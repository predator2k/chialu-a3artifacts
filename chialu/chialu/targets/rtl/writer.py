"""SystemVerilog emission: a module builder that owns the ports, the
declarations, the function library, the continuous assignments and the
always_comb blocks of one module, renders the indentation, and
deduplicates declarations and functions by name.

    m = SvModule("alu_core", header=["behavioral reference ..."])
    m.port("a", "in", 32)
    m.logic("y_m0", 32)
    m.function(text)                     # a `function automatic ...` text
    blk = m.comb()                       # an always_comb block
    blk.stmt("y_m0 = '0;")
    with blk.case("op"):
        with blk.arm("3'd0"):
            blk.stmt("y_m0[15:0] = m0_a0 + m0_b0;")
    text = m.render()

Expression helpers (`flag`, `is_nan`, `sel`, ...) build the recurring SV
fragments of the arithmetic generators so no emitter concatenates
quote characters or replaces Python's `True` in a string.
"""
from __future__ import annotations

import re
from contextlib import contextmanager

_FUNC_NAME_RE = re.compile(r"function\s+(?:automatic\s+)?(?:signed\s+)?"
                           r"(?:\[[^\]]*\]\s*)?(\w+)\s*\(")


class CombBlock:
    """One always_comb block: statements with nesting-driven indentation."""

    def __init__(self, indent: str = "  "):
        self._indent = indent
        self._depth = 2                    # inside `always_comb begin`
        self.lines: list[str] = []

    def stmt(self, text: str):
        self.lines.append(self._indent * self._depth + text)

    def stmts(self, texts):
        for t in texts:
            self.stmt(t)

    def open(self, text: str):
        """A line that opens a nesting level (`case (op)`, `if (x) begin`)."""
        self.stmt(text)
        self._depth += 1

    def close(self, text: str = "end"):
        self._depth -= 1
        self.stmt(text)

    @contextmanager
    def case(self, selector: str, default: str | None = "default: ;"):
        self.open(f"case ({selector})")
        yield
        if default is not None:
            self.stmt(default)
        self.close("endcase")

    @contextmanager
    def arm(self, label: str):
        self.open(f"{label}: begin")
        yield
        self.close("end")

    @contextmanager
    def block(self, head: str):
        """`<head> begin` ... `end`."""
        self.open(f"{head} begin")
        yield
        self.close("end")

    def render(self) -> list[str]:
        return [self._indent + "always_comb begin"] + self.lines + [self._indent + "end"]


class SvModule:
    """A module under construction. Declarations are deduplicated by
    signal name (a second `logic()` of the same name is a no-op when the
    declaration text agrees, an error otherwise); functions by function
    name."""

    def __init__(self, name: str, header: list[str] | tuple = ()):
        self.name = name
        self.header = list(header)
        self.ports: list[tuple[str, str, int]] = []
        self.parameters: list[tuple[str, str]] = []   # (declaration, default)
        self.imports: list[str] = []                  # package names
        self._decls: dict[str, str] = {}
        self._decl_order: list[str] = []
        self._funcs: dict[str, str] = {}
        self._func_order: list[str] = []
        self._body: list[str] = []          # assigns, raw lines, blocks in order
        self._blocks: list[CombBlock] = []

    # ---- interface
    def parameter(self, decl: str, default):
        """A module parameter, e.g. parameter("int LANE", 0)."""
        self.parameters.append((decl, str(default)))

    def import_package(self, name: str):
        if name not in self.imports:
            self.imports.append(name)

    def port(self, name: str, direction: str, width: int):
        if any(n == name for n, _d, _w in self.ports):
            return
        self.ports.append((name, direction, width))

    def ports_from(self, ports):
        """adir Port objects (name, direction, width)."""
        for p in ports:
            self.port(p.name, p.direction, p.width)

    # ---- declarations
    def logic(self, name: str, width: int = 1, signed: bool = False,
              dims: str = "") -> str:
        if any(n == name for n, _d, _w in self.ports):
            return name                      # a port: declared by the interface
        rng = f" [{width - 1}:0]" if width > 1 else ""
        text = f"  logic{' signed' if signed else ''}{rng} {name}{dims};"
        return self.declare(name, text)

    def declare(self, name: str, text: str) -> str:
        prev = self._decls.get(name)
        if prev is None:
            self._decls[name] = text
            self._decl_order.append(name)
        elif prev != text:
            raise ValueError(f"{self.name}: {name} declared twice with different "
                             f"text:\n  {prev}\n  {text}")
        return name

    def declared(self, name: str) -> bool:
        return name in self._decls

    def localparam(self, name: str, value) -> str:
        return self.declare(name, f"  localparam int {name} = {value};")

    # ---- functions
    def function(self, text: str) -> str:
        """A function text (possibly several functions); each is kept once."""
        for chunk in _split_functions(text):
            m = _FUNC_NAME_RE.search(chunk)
            key = m.group(1) if m else chunk
            if key not in self._funcs:
                self._funcs[key] = chunk
                self._func_order.append(key)
        return text

    def has_function(self, name: str) -> bool:
        return name in self._funcs

    # ---- body
    def assign(self, lhs: str, rhs: str):
        self._body.append(f"  assign {lhs} = {rhs};")

    def raw(self, text: str):
        """Verbatim module-scope text (indented by the caller)."""
        self._body.append(text)

    def comb(self) -> CombBlock:
        blk = CombBlock()
        self._blocks.append(blk)
        self._body.append(blk)
        return blk

    def instance(self, module: str, inst: str, conns: dict):
        c = ", ".join(f".{k}({v})" for k, v in conns.items())
        self._body.append(f"  {module} {inst} ({c});")

    # ---- render
    def render(self) -> str:
        # every port is a vector, [0:0] included: the datapath indexes
        # one-bit selects and words (`daz_in_sel[0]`, `sr_rnd[0 +: 1]`)
        decl_ports = [f"  {'input ' if d == 'in' else 'output'} logic [{w - 1}:0] {n}"
                      for n, d, w in self.ports]
        params = ""
        if self.parameters:
            params = " #(" + ", ".join(f"parameter {d} = {v}" for d, v in self.parameters) + ")"
        L = [f"module {self.name}{params} (", ",\n".join(decl_ports), ");"]
        # the header comments sit inside the module, so a module that is a mutable
        # region carries them: a sharing plan rewrites them with the region
        L += [f"  // {h}" for h in self.header]
        for pkg in self.imports:
            L.append(f"  import {pkg}::*;")
        for k in self._func_order:
            L.append(self._funcs[k].rstrip("\n"))
        for k in self._decl_order:
            L.append(self._decls[k])
        for item in self._body:
            if isinstance(item, CombBlock):
                L += item.render()
            else:
                L.append(item)
        L.append("endmodule")
        return "\n".join(L) + "\n"


class SvPackage(SvModule):
    """A package: the functions (and localparams) of one mode, defined
    once and imported by every module of the mode."""

    def render(self) -> str:
        L = [f"// {h}" for h in self.header] + [f"package {self.name};"]
        for k in self._func_order:
            L.append(self._funcs[k].rstrip("\n"))
        for k in self._decl_order:
            L.append(self._decls[k])
        L.append("endpackage")
        return "\n".join(L) + "\n"


def _split_functions(text: str) -> list[str]:
    """Split a text holding several `function ... endfunction` items (with
    the comments and localparams that precede each) into one chunk per
    function; text without a function is one chunk."""
    parts = re.split(r"(?<=endfunction)\n", text)
    out = [p for p in parts if p.strip()]
    return out or [text]


# ------------------------------------------------------- SV expressions --

def bits(width: int, value: int) -> str:
    """A sized decimal literal."""
    return f"{width}'d{value}"


def onehot(width: int, bit: int) -> str:
    return f"({width}'d1 << {bit})"


def ones(width: int) -> str:
    return f"{{{width}{{1'b1}}}}"


def zeros(width: int) -> str:
    return f"{{{width}{{1'b0}}}}"


def sel(cond: str, a: str, b: str) -> str:
    return f"({cond} ? {a} : {b})"


def cat(*parts: str) -> str:
    return "{" + ", ".join(parts) + "}"


def slice_(sig: str, hi: int, lo: int) -> str:
    return f"{sig}[{hi}:{lo}]" if hi != lo else f"{sig}[{hi}]"


def part(sig: str, base, width: int) -> str:
    """An indexed part-select `sig[base +: width]`."""
    return f"{sig}[{base} +: {width}]"


def bool_(v) -> str:
    """A Python truth value as a 1-bit literal."""
    return "1'b1" if v else "1'b0"


def cmp_flags(width: int, gt: str, eq: str, lt: str) -> str:
    """The three compare flags as a result word of `width` bits, with the
    greater-than flag in bit 2, the equal flag in bit 1 and the less-than
    flag in bit 0. The word is zero-padded above three bits, and below
    three bits it carries the low `width` flags, which is the same
    truncation the reference applies when it masks the compare code to the
    result width. A padding replication is emitted only where its count is
    positive, because a negative count stops the simulator."""
    if width < 1:
        raise ValueError(f"a compare result needs at least one bit, got {width}")
    if width > 3:
        return cat(zeros(width - 3), gt, eq, lt)
    kept = [gt, eq, lt][3 - width:]
    return kept[0] if width == 1 else cat(*kept)
