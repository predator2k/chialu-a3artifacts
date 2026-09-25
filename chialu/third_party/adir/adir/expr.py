"""The expression language (design section 4.5): metric names, numeric
literals, `+ - * /`, `log exp sqrt abs max min`, the aggregates
`geomean mean sum min max quantile wmean` over list- or mapping-valued
values, member-wise arithmetic on mappings, interval records, and the
conditions of `when` and constraint rows (`le ge eq lt gt ne`, or their
symbols). UNDECIDED propagates through everything."""
from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Any, Callable

from .errors import UNDECIDED, BindError

_TOKEN = re.compile(r"""
    (?P<num>0x[0-9a-fA-F]+|\d+\.\d*(?:[eE][+-]?\d+)?|\.\d+(?:[eE][+-]?\d+)?|\d+(?:[eE][+-]?\d+)?)
  | (?P<name>[A-Za-z_$][A-Za-z0-9_$]*(?:\.[A-Za-z0-9_*$-]+)*)
  | (?P<cmp><=|>=|==|!=|<|>)
  | (?P<op>[-+*/(),])
  | (?P<ws>\s+)
""", re.X)
_WORD_CMP = {"le": "le", "ge": "ge", "eq": "eq", "lt": "lt", "gt": "gt", "ne": "ne"}
_SYM_CMP = {"<=": "le", ">=": "ge", "==": "eq", "!=": "ne", "<": "lt", ">": "gt"}
FUNCTIONS = ("log", "exp", "sqrt", "abs", "max", "min", "geomean", "mean",
             "sum", "quantile", "wmean")


class ParseError(ValueError):
    pass


def tokenize(text: str):
    pos, out = 0, []
    while pos < len(text):
        m = _TOKEN.match(text, pos)
        if not m:
            raise ParseError(f"cannot read {text[pos:pos + 12]!r} in {text!r}")
        pos = m.end()
        kind = m.lastgroup
        val = m.group(kind)
        if kind == "ws":
            continue
        if kind == "name" and val in _WORD_CMP:
            out.append(("cmp", _WORD_CMP[val]))
        elif kind == "cmp":
            out.append(("cmp", _SYM_CMP[val]))
        elif kind == "num":
            out.append(("num", int(val, 16) if val.startswith("0x")
                        else (float(val) if any(c in val for c in ".eE") else int(val))))
        else:
            out.append((kind, val))
    return out


class _Parser:
    def __init__(self, tokens):
        self.t = tokens
        self.i = 0

    def peek(self):
        return self.t[self.i] if self.i < len(self.t) else (None, None)

    def take(self, kind=None, val=None):
        k, v = self.peek()
        if k is None or (kind and k != kind) or (val is not None and v != val):
            raise ParseError(f"expected {val or kind}, got {v!r}")
        self.i += 1
        return v

    def condition(self):
        left = self.expr()
        k, v = self.peek()
        if k == "cmp":
            self.i += 1
            right = self.expr()
            node = ("cmp", v, left, right)
        else:
            node = left
        if self.peek()[0] is not None:
            raise ParseError(f"trailing {self.peek()[1]!r}")
        return node

    def expr(self):
        node = self.term()
        while self.peek() in (("op", "+"), ("op", "-")):
            op = self.take()
            node = ("bin", op, node, self.term())
        return node

    def term(self):
        node = self.unary()
        while self.peek() in (("op", "*"), ("op", "/")):
            op = self.take()
            node = ("bin", op, node, self.unary())
        return node

    def unary(self):
        if self.peek() == ("op", "-"):
            self.take()
            return ("neg", self.unary())
        return self.atom()

    def atom(self):
        k, v = self.peek()
        if k == "num":
            self.take()
            return ("num", v)
        if k == "name":
            self.take()
            if self.peek() == ("op", "("):
                if v not in FUNCTIONS:
                    raise ParseError(f"unknown function {v!r} (known: {', '.join(FUNCTIONS)})")
                self.take()
                args = []
                if self.peek() != ("op", ")"):
                    args.append(self.expr())
                    while self.peek() == ("op", ","):
                        self.take()
                        args.append(self.expr())
                self.take("op", ")")
                return ("call", v, args)
            return ("ref", v)
        if k == "op" and v == "(":
            self.take()
            node = self.expr()
            self.take("op", ")")
            return node
        raise ParseError(f"unexpected {v!r}")


def parse(text: str):
    """An expression or a condition, as an AST."""
    if not isinstance(text, str):
        return ("num", text)
    try:
        return _Parser(tokenize(text)).condition()
    except ParseError as e:
        raise ParseError(f"{text!r}: {e}") from None


def references(ast) -> list:
    out = []

    def walk(n):
        if n[0] == "ref":
            out.append(n[1])
        elif n[0] in ("bin", "cmp"):
            walk(n[2])
            walk(n[3])
        elif n[0] == "neg":
            walk(n[1])
        elif n[0] == "call":
            for a in n[2]:
                walk(a)
    walk(ast)
    return out


def is_bare_reference(ast) -> bool:
    return ast[0] == "ref"


def is_condition(ast) -> bool:
    return ast[0] == "cmp"


# ------------------------------------------------------------------ values

@dataclass(frozen=True)
class Interval:
    mean: float
    lo: float
    hi: float
    n: int = 0

    def to_json(self):
        return {"mean": self.mean, "lo": self.lo, "hi": self.hi, "n": self.n}


def as_value(v):
    """Interval records arrive as dicts from a node; everything else is
    itself."""
    if isinstance(v, dict) and {"mean", "lo", "hi"} <= set(v):
        return Interval(float(v["mean"]), float(v["lo"]), float(v["hi"]), int(v.get("n", 0)))
    return v


def _num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _apply(op: str, a, b):
    if a is UNDECIDED or b is UNDECIDED:
        return UNDECIDED
    a, b = as_value(a), as_value(b)
    if isinstance(a, dict) and isinstance(b, dict):
        if set(a) != set(b):
            raise ValueError(f"mappings with different keys: {sorted(a)[:4]} vs {sorted(b)[:4]}")
        return {k: _apply(op, a[k], b[k]) for k in a}
    if isinstance(a, dict):
        return {k: _apply(op, x, b) for k, x in a.items()}
    if isinstance(b, dict):
        return {k: _apply(op, a, x) for k, x in b.items()}
    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            raise ValueError("lists of different length")
        return [_apply(op, x, y) for x, y in zip(a, b)]
    if isinstance(a, list):
        return [_apply(op, x, b) for x in a]
    if isinstance(b, list):
        return [_apply(op, a, x) for x in b]
    if isinstance(a, bool):
        a = int(a)
    if isinstance(b, bool):
        b = int(b)
    ia, ib = isinstance(a, Interval), isinstance(b, Interval)
    if not ia and not ib:
        if not (_num(a) and _num(b)):
            raise ValueError(f"arithmetic on {a!r} and {b!r}")
        return _scalar(op, a, b)
    A = a if ia else Interval(a, a, a)
    B = b if ib else Interval(b, b, b)
    mean = _scalar(op, A.mean, B.mean)
    if op == "+":
        lo, hi = A.lo + B.lo, A.hi + B.hi
    elif op == "-":
        lo, hi = A.lo - B.hi, A.hi - B.lo
    else:
        ext = [_scalar(op, x, y) for x in (A.lo, A.hi) for y in (B.lo, B.hi)]
        lo, hi = min(ext), max(ext)
    return Interval(mean, lo, hi, max(A.n, B.n))


def _scalar(op, a, b):
    if op == "+":
        return a + b
    if op == "-":
        return a - b
    if op == "*":
        return a * b
    if b == 0:
        return math.inf if a > 0 else (-math.inf if a < 0 else math.nan)
    return a / b


def _flatten(v, out):
    v = as_value(v)
    if v is UNDECIDED:
        out.append(UNDECIDED)
    elif isinstance(v, dict):
        for x in v.values():
            _flatten(x, out)
    elif isinstance(v, (list, tuple)):
        for x in v:
            _flatten(x, out)
    elif isinstance(v, Interval):
        out.append(v.mean)
    elif isinstance(v, bool):
        out.append(int(v))
    elif _num(v):
        out.append(v)
    else:
        raise ValueError(f"cannot aggregate {v!r}")
    return out


def _numbers(v):
    xs = _flatten(v, [])
    if any(x is UNDECIDED for x in xs) or not xs:
        return None
    return xs


def _unary_math(name, v):
    v = as_value(v)
    if v is UNDECIDED:
        return UNDECIDED
    if isinstance(v, dict):
        return {k: _unary_math(name, x) for k, x in v.items()}
    if isinstance(v, list):
        return [_unary_math(name, x) for x in v]
    f = {"log": math.log, "exp": math.exp, "sqrt": math.sqrt, "abs": abs}[name]
    if isinstance(v, Interval):
        vals = sorted(f(x) for x in (v.lo, v.hi))
        return Interval(f(v.mean), vals[0], vals[1], v.n)
    return f(v)


def _call(name, args):
    if any(a is UNDECIDED for a in args):
        return UNDECIDED
    if name in ("log", "exp", "sqrt", "abs"):
        if len(args) != 1:
            raise ValueError(f"{name} takes one argument")
        return _unary_math(name, args[0])
    if name in ("max", "min") and len(args) >= 2:
        vals = []
        for a in args:
            a = as_value(a)
            vals.append(a.mean if isinstance(a, Interval) else a)
        return max(vals) if name == "max" else min(vals)
    if name in ("max", "min", "mean", "sum", "geomean"):
        if len(args) != 1:
            raise ValueError(f"{name} takes one list or mapping")
        xs = _numbers(args[0])
        if xs is None:
            return UNDECIDED
        if name == "max":
            return max(xs)
        if name == "min":
            return min(xs)
        if name == "sum":
            return sum(xs)
        if name == "mean":
            return sum(xs) / len(xs)
        if any(x <= 0 for x in xs):
            raise ValueError("geomean needs positive values")
        return math.exp(sum(math.log(x) for x in xs) / len(xs))
    if name == "quantile":
        if len(args) != 2:
            raise ValueError("quantile(list, q)")
        xs = _numbers(args[0])
        q = args[1]
        if xs is None:
            return UNDECIDED
        xs = sorted(xs)
        pos = (len(xs) - 1) * float(q)
        lo, hi = int(math.floor(pos)), int(math.ceil(pos))
        return xs[lo] + (xs[hi] - xs[lo]) * (pos - lo)
    if name == "wmean":
        if len(args) != 2:
            raise ValueError("wmean(values, weights)")
        vals, weights = as_value(args[0]), as_value(args[1])
        if isinstance(vals, dict) and isinstance(weights, dict):
            keys = [k for k in vals if k in weights]
            pairs = [(vals[k], weights[k]) for k in keys]
        elif isinstance(vals, (list, tuple)) and isinstance(weights, (list, tuple)):
            pairs = list(zip(vals, weights))
        else:
            raise ValueError("wmean needs two mappings or two lists")
        num = den = 0.0
        for v, w in pairs:
            v = as_value(v)
            if v is UNDECIDED:
                return UNDECIDED
            if isinstance(v, Interval):
                v = v.mean
            num += float(v) * float(w)
            den += float(w)
        return num / den if den else UNDECIDED
    raise ValueError(f"unknown function {name}")


def _compare(op, a, b):
    if a is UNDECIDED or b is UNDECIDED:
        return UNDECIDED
    a, b = as_value(a), as_value(b)
    if isinstance(a, dict):
        rs = [_compare(op, x, b[k] if isinstance(b, dict) else b) for k, x in a.items()]
        if any(r is UNDECIDED for r in rs):
            return UNDECIDED
        return all(rs)
    if isinstance(a, list):
        rs = [_compare(op, x, b) for x in a]
        if any(r is UNDECIDED for r in rs):
            return UNDECIDED
        return all(rs)
    if op in ("eq", "ne") and not (_num(a) or isinstance(a, Interval)):
        eq = (a == b)
        return eq if op == "eq" else not eq
    if isinstance(a, Interval) or isinstance(b, Interval):
        A = a if isinstance(a, Interval) else Interval(a, a, a)
        B = b if isinstance(b, Interval) else Interval(b, b, b)
        if op in ("le", "lt"):
            return A.hi <= B.lo if op == "le" else A.hi < B.lo
        if op in ("ge", "gt"):
            return A.lo >= B.hi if op == "ge" else A.lo > B.hi
        return (A.mean == B.mean) if op == "eq" else (A.mean != B.mean)
    if isinstance(a, bool):
        a = int(a)
    if isinstance(b, bool):
        b = int(b)
    return {"le": a <= b, "ge": a >= b, "lt": a < b, "gt": a > b,
            "eq": a == b, "ne": a != b}[op]


def evaluate(ast, resolve: Callable[[str], Any]):
    """The value of an AST under `resolve(name)`. A condition yields a
    bool or UNDECIDED; an expression yields a number, an Interval, a
    mapping, a list, a string, a bool or UNDECIDED."""
    k = ast[0]
    if k == "num":
        return ast[1]
    if k == "ref":
        return as_value(resolve(ast[1]))
    if k == "neg":
        return _apply("-", 0, evaluate(ast[1], resolve))
    if k == "bin":
        return _apply(ast[1], evaluate(ast[2], resolve), evaluate(ast[3], resolve))
    if k == "call":
        return _call(ast[1], [evaluate(a, resolve) for a in ast[2]])
    if k == "cmp":
        return _compare(ast[1], evaluate(ast[2], resolve), evaluate(ast[3], resolve))
    raise ValueError(f"bad node {ast!r}")


def condition_slack(ast, resolve) -> float:
    """The normalized distance to satisfaction of a failed condition, in
    [0, 1]: 0 at the boundary, 1 far away. A bare boolean condition is 1
    when false."""
    if ast[0] != "cmp":
        return 1.0
    op, a, b = ast[1], evaluate(ast[2], resolve), evaluate(ast[3], resolve)
    a, b = as_value(a), as_value(b)
    if a is UNDECIDED or b is UNDECIDED:
        return 1.0
    if isinstance(a, Interval):
        a = a.mean
    if isinstance(b, Interval):
        b = b.mean
    if not (_num(a) and _num(b)):
        return 1.0
    scale = max(abs(b), abs(a), 1e-12)
    if op in ("le", "lt"):
        d = (a - b) / scale
    elif op in ("ge", "gt"):
        d = (b - a) / scale
    else:
        d = abs(a - b) / scale
    return max(0.0, min(1.0, d))


def condition_text(op: str) -> str:
    return {"le": "<=", "ge": ">=", "eq": "==", "lt": "<", "gt": ">", "ne": "!="}[op]


class Expr:
    """A parsed expression with its text and its references."""

    def __init__(self, text):
        self.text = text if isinstance(text, str) else repr(text)
        self.ast = parse(text)
        self.refs = references(self.ast)

    def __repr__(self):
        return f"Expr({self.text!r})"

    def value(self, resolve):
        return evaluate(self.ast, resolve)

    @property
    def is_condition(self):
        return is_condition(self.ast)

    @property
    def is_bare(self):
        return is_bare_reference(self.ast)


def to_json(v):
    """A value as JSON-serializable data."""
    v = as_value(v)
    if v is UNDECIDED:
        return None
    if isinstance(v, Interval):
        return v.to_json()
    if isinstance(v, dict):
        return {str(k): to_json(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [to_json(x) for x in v]
    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
        return str(v)
    return v
