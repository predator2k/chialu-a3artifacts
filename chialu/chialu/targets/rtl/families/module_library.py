"""Strict collection of named RTL text, with one shared SV identity rule."""
from __future__ import annotations

import re


_QUOTED = r'"(?:\\.|[^"\\])*"|\\[^\s]+|//[^\n]*|/\*.*?\*/'
_IDENTIFIER = r'[A-Za-z_$][A-Za-z0-9_$]*'
_NUMBER = (r"(?:[0-9][0-9_]*)?'[sS]?[bBoOdDhH][0-9a-fA-F_xXzZ?]+|"
           r"'[01xXzZ]|[0-9][0-9_]*(?:\.[0-9_]+)?(?:[eE][+-]?[0-9_]+)?(?:[munpf]?s)?")
_OPERATORS = (r'<<<=|>>>=|<<=|>>=|<<<|>>>|===|!==|==\?|!=\?|->>|\|->|\|=>|'
              r'\*\*|&&|\|\||<<|>>|<=|>=|==|!=|~&|~\||~\^|\^~|'
              r'\+\+|--|\+=|-=|\*=|/=|%=|&=|\|=|\^=|::|->|=>|\+:|-:|'
              r'\*\>|##|#-#|#=#|``')
_TOKEN = re.compile(_QUOTED + '|' + _NUMBER + '|' + _IDENTIFIER + '|' + _OPERATORS + r'|[^\s]', re.S)
_BOUNDARY = re.compile(_QUOTED + r'|(?<![A-Za-z0-9_$])(?:module|endmodule)(?![A-Za-z0-9_$])', re.S)
_MISSING = object()


def sv_tokens(source):
    """Comments/whitespace are insignificant; strings and compound tokens are not."""
    return tuple(value for value in _TOKEN.findall(source)
                 if not value.startswith(('//', '/*')))


def _same_definition(name, previous, following, identities):
    if '`' in previous or previous != following:
        if name not in identities:
            identities[name] = sv_tokens(previous)
        # Identical text does not imply identical expansion when a macro
        # or compiler directive depends on its preprocessing context.
        # Strings and comments were recognized before backtick tokens.
        if any(token in ('`', '``') for token in identities[name]):
            raise ValueError(f'conflicting definitions for RTL module {name!r}: repeated preprocessor-dependent text requires preprocessing before collection')
        if previous != following and identities[name] != sv_tokens(following):
            raise ValueError(f'conflicting definitions for RTL module {name!r}')


def module_spans(text):
    """Yield every real module boundary, including repeated definitions."""
    start = name = None
    for match in _BOUNDARY.finditer(text):
        value = match.group()
        if value == 'module':
            if start is not None:
                raise ValueError('nested RTL modules cannot be deduplicated')
            header = (m.group() for m in _TOKEN.finditer(text, match.end())
                      if not m.group().startswith(('//', '/*')))
            name = next(header, '')
            if name in ('automatic', 'static'):
                name = next(header, '')
            if not (re.fullmatch(_IDENTIFIER, name) or name.startswith('\\')):
                raise ValueError('RTL module has no concrete identifier')
            start = match.start()
        elif value == 'endmodule':
            if start is None:
                raise ValueError('RTL endmodule has no matching module')
            end = match.end()
            following = (m for m in _TOKEN.finditer(text, end)
                         if not m.group().startswith(('//', '/*')))
            separator = next(following, None)
            if separator is not None and separator.group() == ':':
                label = next(following, None)
                if label is None or label.group() != name:
                    raise ValueError('RTL endmodule label differs from its module name')
                end = label.end()
            yield name, start, end
            start = name = None
    if start is not None:
        raise ValueError(f'unterminated RTL module {name!r}')


class ModuleLibrary(dict):
    """A dict-compatible collector whose mutation APIs cannot discard conflicts.

    Entries are named SV text; this also supports the named package texts
    in a seed's module map. The first spelling is retained when tokens agree.
    """
    def __init__(self, initial=(), **kwargs):
        super().__init__()
        self._identities = {}
        self.update(initial, **kwargs)

    @staticmethod
    def _valid(name, text):
        if not isinstance(name, str) or not name or not isinstance(text, str):
            raise TypeError('RTL libraries require nonempty string names and SV text values')

    def __setitem__(self, name, text):
        self._valid(name, text)
        if name in self:
            _same_definition(name, self[name], text, self._identities)
            return
        dict.__setitem__(self, name, text)

    def update(self, source=(), **kwargs):
        entries = source.items() if hasattr(source, 'items') else source
        pending, identities = dict(self), dict(getattr(self, '_identities', {}))
        for name, text in (*entries, *kwargs.items()):
            self._valid(name, text)
            if name in pending:
                _same_definition(name, pending[name], text, identities)
            else:
                pending[name] = text
        # Validate the entire update before mutating a caller's library.
        for name, text in pending.items():
            if name not in self:
                dict.__setitem__(self, name, text)
        self._identities = identities

    def setdefault(self, name, default=None):
        if default is None and name in self:
            return self[name]
        self[name] = default
        return self[name]

    def __delitem__(self, name):
        dict.__delitem__(self, name)
        self._identities.pop(name, None)

    def pop(self, name, default=_MISSING):
        if name not in self:
            if default is _MISSING:
                raise KeyError(name)
            return default
        value = self[name]
        del self[name]
        return value

    def popitem(self):
        name, value = dict.popitem(self)
        self._identities.pop(name, None)
        return name, value

    def clear(self):
        dict.clear(self)
        self._identities.clear()

    def copy(self):
        return type(self)(self)

    def __ior__(self, other):
        self.update(other)
        return self

    def __or__(self, other):
        result = self.copy()
        result.update(other)
        return result

    def __ror__(self, other):
        result = type(self)(other)
        result.update(self)
        return result

    def __reduce__(self):
        return type(self), (list(self.items()),)


def collect_modules(target, source):
    """Strict merge, including legacy callers that supply an ordinary dict."""
    if isinstance(target, ModuleLibrary):
        target.update(source)
    else:
        validated = ModuleLibrary(target)
        validated.update(source)
        for name, text in validated.items():
            if name not in target:
                target[name] = text
    return target


def dedupe_modules(text):
    out, seen, cursor = [], ModuleLibrary(), 0
    for name, start, end in module_spans(text):
        out.append(text[cursor:start])
        fresh = name not in seen
        seen[name] = text[start:end]
        if fresh:
            out.append(text[start:end])
        cursor = end
    out.append(text[cursor:])
    return ''.join(out)


def split_modules(text):
    """Split without letting a dict silently erase a repeated definition."""
    result, cursor = ModuleLibrary(), 0
    spans = list(module_spans(text))
    for index, (name, start, end) in enumerate(spans):
        # Include the final suffix before validating, so semantic footer
        # tokens cannot be attached later through an unchecked dict write.
        stop = len(text) if index == len(spans) - 1 else end
        result[name] = text[cursor:stop] + '\n'
        cursor = end
    return result
