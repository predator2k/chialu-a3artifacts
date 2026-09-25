"""Execute integer Python references over bounded symbolic inputs and emit their expressions."""
from __future__ import annotations

from dataclasses import dataclass
from itertools import count


class Unsupported(ValueError):
    pass


class Branch(Exception):
    def __init__(self, condition):
        self.condition = condition


class Execution:
    def __init__(self, choices, bits):
        self.choices = iter(choices)
        self.bits = bits
        self.nodes = []
        self.conditions = []

    def literal(self, value):
        if not isinstance(value, int):
            raise Unsupported(f"noninteger symbolic operand {value!r}")
        value = int(value)
        if not -(1 << (self.bits - 1)) <= value < 1 << (self.bits - 1):
            raise Unsupported(f"symbolic constant exceeds {self.bits} signed bits")
        return f"-{self.bits}'sd{-value}" if value < 0 else f"{self.bits}'sd{value}"

    def word(self, expression, lo, hi):
        if lo < -(1 << (self.bits - 1)) or hi >= 1 << (self.bits - 1):
            raise Unsupported(f"symbolic intermediate exceeds {self.bits} signed bits")
        name = f"n{len(self.nodes)}"
        self.nodes.append(f"wire signed [{self.bits-1}:0] {name} = {expression};")
        return Word(self, name, lo, hi)

    def branch(self, condition):
        try:
            choice = next(self.choices)
        except StopIteration:
            raise Branch(condition)
        self.conditions.append(condition if choice else f"!({condition})")
        return choice


@dataclass(eq=False)
class Word:
    execution: Execution
    name: str
    lo: int
    hi: int

    def other(self, value):
        if isinstance(value, Word):
            if value.execution is not self.execution:
                raise Unsupported("symbolic operands belong to different executions")
            return value
        return Word(self.execution, self.execution.literal(value), value, value)

    def binary(self, op, other, lo, hi):
        return self.execution.word(f"({self.name}) {op} ({other.name})", lo, hi)

    def __add__(self, value):
        b = self.other(value)
        return self.binary("+", b, self.lo + b.lo, self.hi + b.hi)

    __radd__ = __add__

    def __sub__(self, value):
        b = self.other(value)
        return self.binary("-", b, self.lo - b.hi, self.hi - b.lo)

    def __rsub__(self, value):
        return self.other(value) - self

    def __neg__(self):
        return self.execution.word(f"-({self.name})", -self.hi, -self.lo)

    def __invert__(self):
        return self.execution.word(f"~({self.name})", ~self.hi, ~self.lo)

    def __mul__(self, value):
        b = self.other(value)
        bounds = [x*y for x in (self.lo, self.hi) for y in (b.lo, b.hi)]
        return self.binary("*", b, min(bounds), max(bounds))

    __rmul__ = __mul__

    def bitwise(self, op, value):
        b = self.other(value)
        if op == "&" and (self.lo >= 0 or b.lo >= 0):
            hi = min(x.hi for x in (self, b) if x.lo >= 0)
            lo = 0
        elif self.lo >= 0 and b.lo >= 0:
            lo, hi = 0, (1 << max(self.hi, b.hi).bit_length()) - 1
        else:
            n = max(abs(self.lo), abs(self.hi), abs(b.lo), abs(b.hi)).bit_length() + 1
            lo, hi = -(1 << n), (1 << n) - 1
        return self.binary(op, b, lo, hi)

    def __and__(self, value):
        return self.bitwise("&", value)

    __rand__ = __and__

    def __or__(self, value):
        return self.bitwise("|", value)

    __ror__ = __or__

    def __xor__(self, value):
        return self.bitwise("^", value)

    __rxor__ = __xor__

    def __lshift__(self, value):
        b = self.other(value)
        if b.lo < 0 or b.hi > self.execution.bits:
            raise Unsupported("symbolic shift amount exceeds the bounded integer representation")
        bounds = [a << n for a in (self.lo, self.hi) for n in (b.lo, b.hi)]
        return self.binary("<<<", b, min(bounds), max(bounds))

    def __rlshift__(self, value):
        return self.other(value) << self

    def __rshift__(self, value):
        b = self.other(value)
        if b.lo < 0:
            raise Unsupported("negative symbolic shift amount")
        bounds = [a >> n for a in (self.lo, self.hi) for n in (b.lo, b.hi)]
        return self.binary(">>>", b, min(bounds), max(bounds))

    def __mod__(self, value):
        b = self.other(value)
        if b.lo <= 0:
            raise Unsupported("symbolic modulo requires a positive divisor")
        if self.lo >= 0:
            return self.binary("%", b, 0, b.hi - 1)
        return self.execution.word(f"((({self.name}) % ({b.name})) + ({b.name})) % ({b.name})", 0, b.hi - 1)

    def __floordiv__(self, value):
        b = self.other(value)
        if b.lo <= 0:
            raise Unsupported("symbolic division requires a positive divisor")
        bounds = [a // n for a in (self.lo, self.hi) for n in (b.lo, b.hi)]
        if self.lo >= 0:
            return self.binary("/", b, min(bounds), max(bounds))
        rem = self % b
        return self.execution.word(f"(({self.name}) - ({rem.name})) / ({b.name})", min(bounds), max(bounds))

    def compare(self, op, value):
        b = self.other(value)
        if op == "==" and (self.hi < b.lo or b.hi < self.lo):
            return False
        if op == "==" and self.lo == self.hi == b.lo == b.hi:
            return True
        if op == "<":
            if self.hi < b.lo:
                return True
            if self.lo >= b.hi:
                return False
        if op == "<=":
            if self.hi <= b.lo:
                return True
            if self.lo > b.hi:
                return False
        return self.execution.word(f"({self.name}) {op} ({b.name})", 0, 1)

    def __lt__(self, value):
        return self.compare("<", value)

    def __le__(self, value):
        return self.compare("<=", value)

    def __gt__(self, value):
        return self.other(value) < self

    def __ge__(self, value):
        return self.other(value) <= self

    def __eq__(self, value):
        return self.compare("==", value)

    def __ne__(self, value):
        equal = self == value
        return not equal if isinstance(equal, bool) else equal.execution.word(f"!({equal.name})", 0, 1)

    def __bool__(self):
        if self.lo == self.hi == 0:
            return False
        if self.hi < 0 or self.lo > 0:
            return True
        return self.execution.branch(f"({self.name}) != 0")

    def __abs__(self):
        return self.execution.word(f"({self.name}) < 0 ? -({self.name}) : ({self.name})", 0, max(abs(self.lo), abs(self.hi)))

    def bit_length(self):
        if self.lo < 0:
            return abs(self).bit_length()
        expr = "0"
        for bit in range(self.hi.bit_length()):
            expr = f"{self.name}[{bit}] ? {bit+1} : ({expr})"
        return self.execution.word(expr, 0, self.hi.bit_length())


def compile_reference(adapter, name="python_golden", max_paths=512):
    """Compile the adapter's Python callable; unsupported execution makes no proof claim.

    Every conditional path contributes its guard. Failed Python assertions leave
    that path undefined, and the formal miter must prove the reference is defined
    on every admitted input. Intermediate intervals prevent integer overflow in
    the emitted expressions.
    """
    if adapter.tolerance is not None:
        raise Unsupported("approximate contracts require an error-bound proof")
    if adapter.normalize or adapter.decimal:
        raise Unsupported("this input normalization has no symbolic domain contract")
    inputs = [p for p in adapter.ports if p.direction == "input"]
    outputs = [p for p in adapter.ports if p.direction == "output"]
    bits = 4 * max(p.width for p in adapter.ports) + 32
    declarations = [f"{p.direction} wire [{p.width-1}:0] {p.name}" for p in adapter.ports]
    declarations += ["output wire defined", "output wire admitted"]
    lines = [f"module {name}({', '.join(declarations)});"]
    domain = []
    for p in inputs:
        limit = adapter.domains.get(p.name, 1 << p.width)
        if not 0 < limit <= 1 << p.width:
            raise Unsupported(f"{p.name}: invalid input domain")
        if limit < 1 << p.width:
            domain.append(f"{p.name} < {p.width}'d{limit}")
        if p.name in adapter.constants:
            value = adapter.constants[p.name]
            if not 0 <= value < limit:
                raise Unsupported(f"{p.name}: constant is outside its input domain")
            domain.append(f"{p.name} == {p.width}'d{value}")
    if adapter.nonzero_divisor:
        domain.append("b != 0")
    if adapter.equal_operands:
        domain.append("a == b")
    lines.append("assign admitted = " + " && ".join(f"({d})" for d in domain or ["1'b1"]) + ";")
    pending, guards, results = [()], [], {p.name: [] for p in outputs}
    for index in count():
        if not pending:
            break
        if index >= max_paths:
            raise Unsupported(f"reference exceeds {max_paths} conditional paths")
        choices = pending.pop()
        execution = Execution(choices, bits)
        values = {}
        for p in inputs:
            lo, hi = 0, adapter.domains.get(p.name, 1 << p.width) - 1
            if p.name == "b" and adapter.nonzero_divisor:
                lo = 1
            values[p.name] = (adapter.constants[p.name] if p.name in adapter.constants else
                              execution.word(f"$signed({{1'b0, {p.name}}})", lo, hi))
        if adapter.equal_operands:
            values["b"] = values["a"]
        try:
            result = adapter.reference(values)
        except Branch:
            pending.extend((choices + (False,), choices + (True,)))
            continue
        except AssertionError:
            continue
        except (TypeError, AttributeError) as error:
            raise Unsupported(f"Python reference operation cannot be compiled: {error}") from error
        if not isinstance(result, dict) or result.keys() != results.keys():
            raise Unsupported("Python reference omits an output")
        scope = f"path{index}"
        lines += [f"if (1) begin : {scope}"] + execution.nodes
        lines.append("wire active = " + " && ".join(f"({x})" for x in execution.conditions or ["1'b1"]) + ";")
        guards.append(scope + ".active")
        for p in outputs:
            value = result[p.name]
            if isinstance(value, Word):
                expr = value.name
                lo, hi = value.lo, value.hi
            else:
                expr = execution.literal(value)
                lo = hi = value
            # The miter checks these bounds as well as the reference's assertions.
            lines.append(f"wire [{p.width-1}:0] out_{p.name} = {expr};")
            lines.append(f"wire fits_{p.name} = ({expr}) >= 0 && ({expr}) < {bits}'sd{1 << p.width};")
            results[p.name].append(f"({scope}.active ? {scope}.out_{p.name} : {p.width}'d0)")
        lines.append("wire fits = " + " && ".join(f"fits_{p.name}" for p in outputs) + ";")
        guards[-1] = f"({scope}.active && {scope}.fits)"
        lines.append("end")
    lines.append("assign defined = " + " | ".join(guards or ["1'b0"]) + ";")
    for p in outputs:
        lines.append(f"assign {p.name} = " + " | ".join(results[p.name] or [f"{p.width}'d0"]) + ";")
    lines += ["endmodule", ""]
    return "\n".join(lines)
