"""Lossless spelling repairs at the declaration/plan boundary."""
from __future__ import annotations


NOTE_PREFIX = "// chiALU declaration: "


def canonical_value(domain, value):
    """Read bool spellings and quoted enum members only in their own domain.

    Never use Python truthiness (``'False'`` is truthy), broaden a domain,
    or coerce numbers. A narrowed boolean domain still checks membership.
    """
    if not isinstance(value, str):
        return value
    text = value
    if len(text) >= 2 and text[0] == text[-1] and text[0] in "\"'":
        text = text[1:-1]
    boolean = domain.kind == "bool" or (domain.finite() and domain.kind in ("enum", "categorical")
                                        and domain.members() and all(type(v) is bool for v in domain.members()))
    if boolean and text in ("True", "False", "true", "false"):
        return text in ("True", "true")
    if text != value and not domain.contains(value) and domain.contains(text):
        return text
    return value


def canonical_vars(ctx, values):
    result = {}
    for name, value in values.items():
        binding = ctx.bindings.get(name)
        result[name] = canonical_value(binding.domain, value) if binding is not None else value
    return result


class RenderResult(tuple):
    """Compatible with ADIR's seed/replan tuple protocol, with repair notes."""

    def __new__(cls, *parts, notes=()):
        result = super().__new__(cls, parts)
        result.notes = list(notes)
        return result

    def __getnewargs__(self):
        return tuple(self)
