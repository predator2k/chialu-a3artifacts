"""Floating-point structures on the engine's X representation: the
unpacker (pattern -> V), the significand adder families (single_path,
two_path, delay_optimized_unified, low_power_gated) with their align,
exponent, leading-zero and normalize slots, the significand multiplier
families (sig_mul_then_round, round_fused_in_reduction), the comparators
(integer_compare_on_bits, dedicated_magnitude_comparator), the rounder
(X -> pattern and flags) with the rounding families of its `round` slot
(increment_adder, compound_adder_select, injection, flagged_prefix) and
the divider and square-root wrappers.

Every module is generated for one engine geometry (XW, EW; the format
for the unpacker and the rounder) and is value-exact against the
engine's functions: an X of the same value and the same sticky packs
to the same pattern and flags under every rounding mode, which
families/fptest.py checks through the engine's own pack.

X = {special[1:0], sign, exp[EW] (signed, of bit 0 of sig), sig[XW],
sticky}; V = {special, sign, exp, sig[SW]}. The unpacker's V carries
the stored significand (the hidden one at bit M, a subnormal below
it), so the exponent of bit 0 orders magnitudes lexicographically
with the significand; the adder aligns on that without normalizing
its inputs, which is the as_stored subnormal representation, or
normalizes them first (pseudo_normalized_wide_exponent).

Every component of a library kind inside a module is an instance of a
slot's family (fp_spaces.py, misc_spaces.py): the adders of the
exponent path (`exp.adder`, `exp_adder`), the shifters, the
leading-zero counters, the trailing-zero counters of the sticky, the
rounder's incrementers and injection adder. A mask over a variable
position is a thermometer or one-hot decode (per-bit compares) rather
than a variable shift. A module's name carries a tag of its pins, so
two pin sets never share a name.
"""
from __future__ import annotations
from contextvars import ContextVar

import hashlib
import json
import math

from chialu.targets.rtl.engine import FW, flag_bit
from chialu.verify.formats import FloatFormat, X87Format, _mask  # noqa: F401 - the format classes of a geometry


class Geom:
    """The engine geometry a module is generated for."""

    def __init__(self, XW: int, EW: int, SW: int, sr_bits: int = 8, tight: bool = False, sr: bool = False):
        self.XW, self.EW, self.SW, self.sr_bits = XW, EW, SW, sr_bits
        self.XT = 3 + EW + XW + 1
        self.VW = 3 + EW + SW
        self.tight = bool(tight)      # the guard-round-sticky X (the unit option x_form)
        self.sr = bool(sr)            # the stochastic mode provisioned: the dropped bits are compared exactly

    @classmethod
    def of_engine(cls, e) -> "Geom":
        return cls(e.XW, e.EW, e.SW, e.sr_bits, getattr(e, "tight", False), getattr(e, "sr", False))

    def tag(self) -> str:
        return f"x{self.XW}e{self.EW}s{self.SW}"


def _pin(pins: dict, key: str, default):
    v = pins.get(key, default) if pins else default
    return default if v in (None, "") else v


def _clog2(n: int) -> int:
    return max(1, (n - 1).bit_length())


def _slit(width: int, value: int) -> str:
    """A signed SystemVerilog literal (a negative value as a negated magnitude)."""
    return f"-{width}'sd{-value}" if value < 0 else f"{width}'sd{value}"


def _sub(pins: dict, prefix: str) -> dict:
    return {k[len(prefix):]: v for k, v in (pins or {}).items() if k.startswith(prefix)}


def _tag(pins: dict) -> str:
    """A tag of a pins dictionary for a module name (empty for none): 48
    bits of the hash of the sorted keys and values, so the tens of
    thousands of pin sets a sweep renders keep distinct names."""
    d = {k: v for k, v in (pins or {}).items() if not str(k).startswith("_")}
    if not d:
        return ""
    return "_p" + hashlib.sha1(json.dumps(d, sort_keys=True, default=str).encode()).hexdigest()[:12]


# ---- helper module texts --------------------------------------------------------
def _lib(kind: str, family: str, pins: dict, width: int, signed: bool = False):
    """(instance head, text) of a library module of a kind."""
    from chialu.targets.rtl import families as FAM
    if kind == "adder":
        from .binary_cpa import adder_module
        m = adder_module(family, pins, width)
    elif kind == "shifter":
        m = FAM.shifter_module(family, pins, width)
    elif kind == "lzc":
        m = FAM.lzc_module(family, pins, width)
    elif kind == "incr":
        m = FAM.incrementer_module(family, pins, width)
    elif kind == "mul":
        # Component multipliers use the binary wrapper, which fixes the
        # matrix packing selector for twin_precision_subword's one lane.
        m = FAM.mul_module(family, pins, width, signed)
    elif kind == "cmp":
        m = FAM.comparator_module(family, pins, width, signed)
    elif kind == "tzc":
        m = FAM.tzc_module(family, pins, width)
    else:
        m = None
    if m is None:
        raise ValueError(f"{kind} family {family!r} rejected its pins at width {width}: {dict(pins or {})!r}")
    ps = ", ".join(f".{k}({v})" for k, v in m.params.items())
    head = f"{m.name} " + (f"#({ps}) " if ps else "")
    return head, (m.text or "")


capture_modules = ContextVar("fp_capture_modules", default=None)


class Mod:
    """A module under construction: ports, declarations, body lines."""

    def __init__(self, name: str, comment: str):
        self.name = name
        self.comment = comment
        self.ports: list = []
        self.lines: list = []
        self.extra: list = []           # texts of generated modules this one instantiates
        self.n = 0
        self.instances = []
        capture = capture_modules.get()
        if capture is not None:
            capture[name] = self

    def port(self, direction: str, name: str, width: int = 1, signed: bool = False):
        w = f"[{width-1}:0] " if width > 1 else ""
        sg = "signed " if signed else ""
        self.ports.append(f"{direction} logic {sg}{w}{name}")

    def wire(self, name: str, width: int = 1, signed: bool = False, expr: str | None = None):
        w = f"[{width-1}:0] " if width > 1 else ""
        sg = "signed " if signed else ""
        self.lines.append(f"  logic {sg}{w}{name};" + (f" assign {name} = {expr};" if expr is not None else ""))
        return name

    def assign(self, lhs: str, expr: str):
        self.lines.append(f"  assign {lhs} = {expr};")

    def raw(self, text: str):
        self.lines.append(text)

    def inst(self, kind: str, family: str, pins: dict, width: int, conns: str, comment: str, signed: bool = False) -> bool:
        """Instantiate the requested family, rejecting an unavailable implementation."""
        head, text = _lib(kind, family, pins, width, signed)
        if head is None:
            raise ValueError(f"{kind} family {family!r} did not generate a module at width {width}")
        if text:
            self.extra.append(text)
        self.n += 1
        self.instances.append((self.n, kind, family, dict(pins), width, conns, signed, head))
        self.lines.append(f"  // {comment}")
        self.lines.append(f"  {head}u{self.n} ({conns});")
        return True

    def render(self) -> str:
        from chialu.targets.rtl.families.mul import dedupe_modules
        head = [f"// {self.comment}", f"module {self.name} (", ",\n".join("  " + p for p in self.ports), ");"]
        return "\n".join(head + self.lines + ["endmodule", ""]) + dedupe_modules("".join(self.extra))


def _x_fields(m: Mod, x: str, g: Geom, pre: str):
    """Declare the fields of an X input."""
    XT, XW, EW = g.XT, g.XW, g.EW
    m.wire(f"{pre}sp", 2, expr=f"{x}[{XT-1}:{XT-2}]")
    m.wire(f"{pre}s", expr=f"{x}[{XT-3}]")
    m.wire(f"{pre}e", EW, signed=True, expr=f"$signed({x}[{XW+EW}:{XW+1}])")
    m.wire(f"{pre}sig", XW, expr=f"{x}[{XW}:1]")
    m.wire(f"{pre}st", expr=f"{x}[0]")
    m.wire(f"{pre}z", expr=f"({pre}sp == 2'd0) && ({pre}sig == 0) && !{pre}st")


def _mkx(g: Geom, sp: str, s: str, e: str, sig: str, st: str) -> str:
    return f"{{{sp}, {s}, {e}, {sig}, {st}}}"


def _mkx_special(g: Geom, sp: str, s: str = "1'b0") -> str:
    return f"{{{sp}, {s}, {g.EW}'sd0, {g.XW}'d0, 1'b0}}"


def _lzc(m: Mod, family: str, pins: dict, src: str, width: int, out: str, comment: str) -> str:
    """The leading-zero count of `src` (width bits) into `out` (clog2(width+1)
    bits) through the lzc family module; a behavioral count when the family
    has no module."""
    nw = width.bit_length()
    m.wire(out, nw)
    if not m.inst("lzc", family, pins, width, f".a({src}), .n({out})", comment):
        m.raw(f"  always_comb begin {out} = {width}; for (int k = {width-1}; k >= 0; k = k - 1) if ({src}[k]) begin {out} = {width-1} - k; break; end end")
    return out


def _shift(m: Mod, family: str, pins: dict, src: str, width: int, amt: str, opcode, out: str, comment: str,
           sticky: str | None = None, allowed_ops=None) -> str:
    """out = src shifted by amt through the shifter family module (opcode: 0
    shl, 1 shr as an integer, or an expression of 3 bits selecting the op
    at run time), a behavioral shift without one. `sticky` names a wire to
    receive the OR of the bits shifted out (the module collects it). The
    butterfly network needs a power-of-two width."""
    m.wire(out, width)
    if sticky:
        m.wire(sticky)
        # A caller may need a sticky result while selecting a shifter without
        # an internal collector. Keep that selection and collect the discarded
        # bits outside the shifter instead of overriding the requested pin.
        from chialu.targets.rtl.families.selection import copy_pins
        pins = copy_pins(pins)
        pins.setdefault("sticky_collect", True)
    collect_outside = bool(sticky) and pins.get("sticky_collect") is False
    op = f"3'd{opcode}" if isinstance(opcode, int) else opcode
    if family == "butterfly_network" and width & (width - 1):
        operations = {opcode} if isinstance(opcode, int) else set(allowed_ops or ())
        if not operations or not operations <= {0, 1, 2}:
            raise ValueError(f"{width}-bit butterfly adaptation requires a shift-only contract; rotations cannot be padded")
        network_width = 1 << (width - 1).bit_length()
        pad = f"{network_width-width}'d0"
        if 2 in operations:
            extension = f"{{{network_width-width}{{{src}[{width-1}]}}}}"
            pad = extension if operations == {2} else f"(({op} == 3'd2) ? {extension} : {pad})"
        padded_input = m.wire(out + "_network_a", network_width, expr=f"{{{pad}, {src}}}")
        padded_output = m.wire(out + "_network_y", network_width)
        native_sticky = m.wire(out + "_network_sticky") if sticky else ""
        m.inst("shifter", family, pins, network_width,
               f".a({padded_input}), .amt({amt}), .op({op}), .y({padded_output}), .sticky({native_sticky})",
               comment + f"; {width}-bit payload in a {network_width}-bit butterfly network")
        m.assign(out, f"{padded_output}[{width-1}:0]")
        if sticky:
            if collect_outside:
                mask = f"(({op} == 3'd0) ? ~({{{width}{{1'b1}}}} >> {amt}) : ~({{{width}{{1'b1}}}} << {amt}))"
                m.assign(sticky, f"|({src} & {mask})")
            else:
                m.assign(sticky, f"{native_sticky} | (({op} == 3'd0) && (|{padded_output}[{network_width-1}:{width}]))")
        return out
    if not m.inst("shifter", family, pins, width, f".a({src}), .amt({amt}), .op({op}), .y({out}), .sticky({'' if collect_outside else sticky or ''})", comment):
        if isinstance(opcode, int):
            m.assign(out, f"{src} {'<<' if opcode == 0 else '>>'} {amt}")
            if sticky:
                m.assign(sticky, f"|({src} & ~({{{width}{{1'b1}}}} {'>>' if opcode == 0 else '<<'} {amt}))")
        else:
            m.assign(out, f"({op} == 3'd0) ? ({src} << {amt}) : ({src} >> {amt})")
            if sticky:
                m.assign(sticky, "1'b0")
    if collect_outside:
        right_mask = f"~({{{width}{{1'b1}}}} << {amt})"
        left_mask = f"~({{{width}{{1'b1}}}} >> {amt})"
        m.assign(sticky, f"|({src} & (({op} == 3'd0) ? {left_mask} : {right_mask}))")
    return out


def _thermo(m: Mod, name: str, width: int, amt: str, comment: str) -> str:
    """name[i] = (amt > i): the thermometer of an amount (the mask of the
    positions below it), a compare per bit rather than a variable shift."""
    m.raw(f"  // {comment}")
    m.wire(name, width)
    for i in range(width):
        m.assign(f"{name}[{i}]", f"({amt} > {i})")
    return name


def _onehot(m: Mod, name: str, width: int, val: str, comment: str, offset: int = 0) -> str:
    """name[i] = (val == i + offset): the one-hot decode of a position."""
    m.raw(f"  // {comment}")
    m.wire(name, width)
    for i in range(width):
        m.assign(f"{name}[{i}]", f"({val} == {i + offset})")
    return name


def _adder(m: Mod, fam: str, pins: dict, width: int, a: str, b: str, out: str, comment: str,
           cin: str = "1'b0", cout: str = "", signed: bool = False, declare: bool = True) -> str:
    """out (width bits) = a + b + cin through the adder family's library
    module; the operator when the family has none."""
    if declare:
        m.wire(out, width, signed=signed)
    if not m.inst("adder", fam, pins, width, f".a({a}), .b({b}), .cin({cin}), .s({out}), .cout({cout})", comment):
        m.assign(out, f"{a} + {b} + {cin}")
    return out


def _exp_sub(m: Mod, fam: str, pins: dict, width: int, a: str, b: str, out: str, comment: str) -> str:
    """out = a - b (two's complement, width bits) through the adder family:
    a + ~b + 1."""
    nb = m.wire(f"{out}_nb", width, expr=f"~({b})")
    return _adder(m, fam, pins, width, a, nb, out, comment, cin="1'b1", signed=True)


def _exp_add(m: Mod, fam: str, pins: dict, width: int, a: str, b: str, out: str, comment: str) -> str:
    return _adder(m, fam, pins, width, a, b, out, comment, signed=True)


def _exp_const(m: Mod, fam: str, pins: dict, width: int, a: str, const: int, out: str, comment: str) -> str:
    """out = a + const (a signed constant) through the adder family."""
    c = m.wire(f"{out}_c", width, signed=True, expr=_slit(width, const))
    return _adder(m, fam, pins, width, a, c, out, comment, signed=True)


def _incr(m: Mod, fam: str, pins: dict, width: int, a: str, cin: str, out: str, cout: str, comment: str) -> str:
    """out, cout = a + cin through the incrementer family's library module."""
    m.wire(out, width)
    if cout:
        m.wire(cout)
    if not m.inst("incr", fam, pins, width, f".a({a}), .cin({cin}), .s({out}), .cout({cout})", comment):
        m.assign(f"{{{cout or 'unused_cout'}, {out}}}" if cout else out, f"{a} + {cin}")
    return out


# ---- the unpacker ------------------------------------------------------------
def unpack_sv(c, g: Geom, family: str, pins: dict, name: str | None = None) -> tuple:
    """(name, text): pattern -> {den, V} of a float format. per_unit_unpack,
    shared_per_lane and shared_across_formats are sharing patterns of the
    same decoder; denormal_handling in_unpack normalizes a subnormal here
    (the lzc slot's count and the shifter slot's left shift), in_datapath
    leaves it stored."""
    pins = pins or {}
    M, E, bias, W = c.man_bits, c.exp_bits, c.bias, c.width
    signed = c.signed
    tag = c.name.replace(".", "_")
    norm = str(_pin(pins, "denormal_handling", "in_unpack")) == "in_unpack"
    lzc_fam, lzc_pins = str(_pin(pins, "lzc.family", "lzd_cell_tree")), _sub(pins, "lzc.")
    sh_fam, sh_pins = str(_pin(pins, "shifter.family", "barrel_mux_tree")), _sub(pins, "shifter.")
    name = name or f"fam_fp_unpack_{family}_{tag}_{g.tag()}{_tag(pins)}"
    m = Mod(name, f"fp unpacker ({family}): {c.name} pattern -> V; the fields split, the specials decoded, "
                  f"the hidden one restored{', a subnormal normalized in the unpacker' if norm else ', a subnormal left as stored'}")
    m.port("input", "b", W)
    m.port("input", "daz")
    m.port("output", "u", g.VW + 1)
    m.wire("e", E, expr=f"b[{M+E-1}:{M}]")
    if M > 0:
        m.wire("mant", M, expr=f"b[{M-1}:0]")
    m.wire("s", expr=f"b[{W-1}]" if signed else "1'b0")
    emax = c.emax_code
    if c.exp_only:
        is_nan = f"(e == {E}'d{emax})" if c.has_nan else "1'b0"
        is_inf = f"(e == {E}'d{emax})" if (c.has_inf and not c.has_nan) else "1'b0"
    elif c.has_inf and c.has_nan:
        is_inf = f"(e == {E}'d{emax} && mant == 0)"
        is_nan = f"(e == {E}'d{emax} && mant != 0)"
    elif c.has_inf:
        is_inf = f"(e == {E}'d{emax} && mant == 0)"
        is_nan = "1'b0"
    elif c.has_nan:
        is_inf = "1'b0"
        is_nan = f"(e == {E}'d{emax} && mant == {{{M}{{1'b1}}}})"
    else:
        is_inf = is_nan = "1'b0"
    m.wire("nan", expr=is_nan)
    m.wire("inf", expr=is_inf)
    SW, EW = g.SW, g.EW
    if M > 0:
        m.wire("sub_", expr="(e == 0)")
        m.wire("den", expr="sub_ && (mant != 0)")
        m.wire("sig0", SW, expr=f"sub_ ? {{{{({SW}-{M}){{1'b0}}}}, mant}} : {{{{({SW}-{M}-1){{1'b0}}}}, 1'b1, mant}}")
        m.wire("sig1", SW, expr="(sub_ && daz) ? {SW}'d0" .replace("{SW}", str(SW)) + " : sig0")
        m.wire("ex0", EW, signed=True, expr=f"sub_ ? {_slit(EW, 1 - bias - M)} : $signed({{{{({EW}-{E}){{1'b0}}}}, e}}) - {_slit(EW, bias + M)}")
        if norm:
            _lzc(m, lzc_fam, lzc_pins, "sig1", SW, "lz", "the subnormal's leading-zero count")
            m.wire("lzs", _clog2(SW) if SW > 1 else 1, expr=f"(sig1 == 0) ? {_clog2(SW)}'d0 : lz[{_clog2(SW)-1}:0]")
            _shift(m, sh_fam, sh_pins, "sig1", SW, "lzs", 0, "sign", "the subnormal normalized")
            m.wire("exn", EW, signed=True, expr=f"ex0 - $signed({{{{({EW}-{SW.bit_length()}){{1'b0}}}}, lz}})")
            sig_final, ex_final = "sign", "exn"
        else:
            sig_final, ex_final = "sig1", "ex0"
    else:
        m.wire("den", expr="1'b0")
        m.wire("sig1", SW, expr=f"{SW}'d1")
        m.wire("ex0", EW, signed=True, expr=f"$signed({{{{({EW}-{E}){{1'b0}}}}, e}}) - {_slit(EW, bias)}")
        sig_final, ex_final = "sig1", "ex0"
    m.wire("v_nan", g.VW, expr=f"{{2'd1, 1'b0, {EW}'sd0, {SW}'d0}}")
    m.wire("v_inf", g.VW, expr=f"{{2'd2, s, {EW}'sd0, {SW}'d0}}")
    m.wire("v_fin", g.VW, expr=f"{{2'd0, s, {ex_final}, {sig_final}}}")
    m.assign("u", "nan ? {1'b0, v_nan} : inf ? {1'b0, v_inf} : {den, v_fin}")
    return name, m.render()


# ---- the leading-zero anticipator strings ------------------------------------------
def _lza_string(m: Mod, tag: str, a_src: str, b_src: str, IW: int, restriction: str) -> str:
    """f_<tag>: the indicator string of the difference a_src + b_src + 1
    (b_src the complemented operand) over the window: Schmookler and
    Nowka's general string (either sign), or the positive-result string
    (a non-negative difference: T_{i+1} G_i ~Z_{i-1} + ~T_{i+1} Z_i
    ~Z_{i-1}); the string's leading one is at the difference's leading
    one or one position above it (T above the window is 0)."""
    m.wire(f"t_{tag}", IW, expr=f"{a_src} ^ {b_src}")
    m.wire(f"g_{tag}", IW, expr=f"{a_src} & {b_src}")
    m.wire(f"z_{tag}", IW, expr=f"~{a_src} & ~{b_src}")
    f = m.wire(f"f_{tag}", IW)
    for k in range(IW):
        t1 = f"t_{tag}[{k+1}]" if k + 1 < IW else "1'b0"
        gm = f"g_{tag}[{k-1}]" if k >= 1 else "1'b0"
        zm = f"z_{tag}[{k-1}]" if k >= 1 else "1'b0"
        gk, zk = f"g_{tag}[{k}]", f"z_{tag}[{k}]"
        if restriction == "positive_result_only":
            expr = f"({t1} & {gk} & ~{zm}) | (~{t1} & {zk} & ~{zm})"
        else:
            expr = f"({t1} & (({gk} & ~{zm}) | ({zk} & ~{gm}))) | (~{t1} & (({zk} & ~{zm}) | ({gk} & ~{gm})))"
        m.assign(f"{f}[{k}]", expr)
    return f


# ---- the significand adder ---------------------------------------------------------
NEGATIONS = ("end_around_carry", "dual_adder", "complement_recode")


def add_sv(g: Geom, family: str, pins: dict, name: str | None = None, external: bool = False) -> tuple:
    """(name, text): xa (+/-) xb -> X through the family's datapath. The
    slots are the family's: align / far_align (the shifter and the sticky
    method), norm / close_norm (the normalize shifter, coarse/fine or one
    barrel), lz / near_lz (the anticipator or the counter after the add
    with its counter or encoder family), sig_adder, exp (the exponent
    adder), eac_incrementer (the ones' complement end-around carry).
    negation_handling is the unswapped datapath's (operand_order
    shift_each_operand): the swapped datapath's difference is non-negative."""
    pins = pins or {}
    XW, EW, XT, SW = g.XW, g.EW, g.XT, g.SW
    G = XW - SW
    IW = XW + 1
    AW = _clog2(IW)
    if family == "single_path":
        AK, NK, LK, npaths = "align", "norm", "lz", 1
    elif family == "two_path":
        AK, NK, LK, npaths = "far_align", "close_norm", "near_lz", 2
    elif family == "delay_optimized_unified":
        AK, NK, LK, npaths = "far_align", "norm", "near_lz", 2
    elif family == "low_power_gated":
        AK, NK, LK = "align", "norm", "lz"
        # one partition is no gating, and it renders single_path's text: the family's own default is two
        npaths = max(1, min(3, int(_pin(pins, "datapath_partitions", 2))))
    else:
        raise ValueError(f"fp adder family {family!r}: no module")
    order = str(_pin(pins, "operand_order", "swap_before_shift"))
    swap = order == "swap_before_shift"
    negation = str(_pin(pins, "negation_handling", "end_around_carry"))
    if negation not in NEGATIONS:
        raise ValueError(f"fp adder negation_handling {negation!r}: one of {', '.join(NEGATIONS)}")
    # the keys a caller forwarded before the float spaces' Rev 8 (dot.py's fused multiply-add composes this adder
    # with `subnormal.internal_representation` and `near_lz.*` on single_path): they stand in for the defaults
    legacy_sub = _sub(pins, "subnormal.")
    legacy_lz = _sub(pins, "near_lz.") if LK == "lz" else {}
    pre_norm = str(_pin(pins, "subnormal_representation",
                        legacy_sub.get("internal_representation", "as_stored"))) == "pseudo_normalized_wide_exponent"
    sig_fam, sig_pins = str(_pin(pins, "sig_adder.family", "ripple_carry")), _sub(pins, "sig_adder.")
    # sig_adder.external: the significand adder is not instantiated; its operands, carry-in, sum and carry-out are
    # ports (sa_a, sa_b, sa_cin, sa_s, sa_cout) the unit connects to a carry-propagate adder shared with the
    # integer adders. The datapath must have one significand adder: a single path, the operands ordered before
    # one shifter (one adder serves add and subtract) and two's complement subtraction.
    external = bool(external) or sig_pins.pop("external", False) in (True, "True", 1)
    exp_dual = _pin(pins, "exp.dual_direction_subtract", False) in (True, "True", 1)
    exp_fam, exp_pins = str(_pin(pins, "exp.adder.family", "ripple_carry")), _sub(pins, "exp.adder.")
    align_fam = str(_pin(pins, f"{AK}.family", "full_align"))
    sticky_method = str(_pin(pins, f"{AK}.sticky_method", "or_tree_shifted_out"))
    al_sh_fam, al_sh_pins = str(_pin(pins, f"{AK}.shifter.family", "barrel_mux_tree")), _sub(pins, f"{AK}.shifter.")
    tzc_fam, tzc_pins = str(_pin(pins, f"{AK}.tzc.family", "trailing_zero")), _sub(pins, f"{AK}.tzc.")
    norm_fam = str(_pin(pins, f"{NK}.family", "coarse_fine"))
    coarse = int(_pin(pins, f"{NK}.coarse_granularity", 4))
    nm_sh_fam, nm_sh_pins = str(_pin(pins, f"{NK}.shifter.family", "barrel_mux_tree")), _sub(pins, f"{NK}.shifter.")
    lz_fam = str(_pin(pins, f"{LK}.family", legacy_lz.get("family", "lza")))
    if lz_fam == "lza":
        lzc_fam = str(_pin(pins, f"{LK}.encoder.family", legacy_lz.get("encoder.family", "lzd_cell_tree")))
        lzc_pins = _sub(pins, f"{LK}.encoder.")
        correction = str(_pin(pins, f"{LK}.correction_scheme", "post_norm_fine_shift"))
        string_form = str(_pin(pins, f"{LK}.string_form", "single_indicator"))
        split_sel = str(_pin(pins, f"{LK}.split_string_select", "true_sign"))
        restriction = str(_pin(pins, f"{LK}.indicator_restriction", "general"))
        zero_detect = str(_pin(pins, f"{LK}.zero_result_detect", "indicator_or"))
    else:
        lzc_fam = str(_pin(pins, f"{LK}.counter.family", legacy_lz.get("counter.family", "lzd_cell_tree")))
        lzc_pins = _sub(pins, f"{LK}.counter.")
        correction, string_form, split_sel, restriction, zero_detect = "none", "single_indicator", "true_sign", "general", "sum"
    threshold, trigger, select_point, sub_style = 1, "exp_diff_and_effective_sub", "late_result_mux", "twos_complement"
    eac_fam, eac_pins = "prefix_and_incrementer", {}
    if family == "two_path":
        threshold = max(1, int(_pin(pins, "path_threshold", 1)))
        trigger = str(_pin(pins, "close_path_trigger", "exp_diff_only"))
        select_point = str(_pin(pins, "path_select_point", "early_exponent_compare"))
    if family == "delay_optimized_unified":
        if str(_pin(pins, "path_separation", "standard_close_far")) == "nonstandard_unified_rounding":
            threshold = 2
        sub_style = str(_pin(pins, "subtraction_style", "twos_complement"))
        eac_fam, eac_pins = str(_pin(pins, "eac_incrementer.family", "prefix_and_incrementer")), _sub(pins, "eac_incrementer.")
    if family == "low_power_gated":
        select_point = "early_exponent_compare"          # operand isolation of the inactive partition
    if external and not (npaths == 1 and swap and sub_style == "twos_complement"):
        raise ValueError("an external significand adder (a CPA shared with the integer adders) needs a single-path float "
                         "adder with operand_order swap_before_shift and two's complement subtraction")
    dual = string_form == "dual_pos_neg_strings"
    if dual and swap:
        raise ValueError("lza dual_pos_neg_strings serve the unswapped datapath (operand_order shift_each_operand): "
                         "the swapped datapath's difference is non-negative and its single string suffices")
    if restriction == "positive_result_only" and not swap and not dual:
        raise ValueError("a single indicator string of the unswapped datapath must be the general one: "
                         "the difference's sign is the add's (indicator_restriction=positive_result_only with "
                         "operand_order=shift_each_operand and string_form=single_indicator)")
    name = name or f"fam_fp_add_{family}_{g.tag()}{_tag(pins)}" + ("_xsa" if external else "")
    m = Mod(name, f"fp significand adder ({family}): {npaths} path{'s' if npaths > 1 else ''}; operands "
                  f"{'ordered by magnitude before one shifter' if swap else 'each shifted by its own amount, the magnitude of the difference by ' + negation}; "
                  f"align {align_fam} on a {al_sh_fam} shifter, sticky by {sticky_method}; significand adder {sig_fam}; "
                  f"leading zeros by {lz_fam} ({lzc_fam}{', ' + string_form if lz_fam == 'lza' else ''}); normalize {norm_fam} on a "
                  f"{nm_sh_fam} shifter; exponent path on {exp_fam} adders; subnormals as "
                  f"{'normalized into the wide exponent' if pre_norm else 'stored'}; window of {G} guard bits below the larger "
                  f"operand's lsb (the significands are the unpacker's: {SW} stored bits)")
    m.port("input", "xa", XT)
    m.port("input", "xb", XT)
    m.port("input", "sub")
    m.port("output", "y", XT)
    if external:
        m.port("output", "sa_a", IW)
        m.port("output", "sa_b", IW)
        m.port("output", "sa_cin")
        m.port("input", "sa_s", IW)
        m.port("input", "sa_cout")
    _x_fields(m, "xa", g, "a_")
    m.raw(f"  logic [{XT-1}:0] xbs; assign xbs = {{xb[{XT-1}:{XT-2}], xb[{XT-3}] ^ sub, xb[{XT-4}:0]}};")
    _x_fields(m, "xbs", g, "b_")
    # operands, normalized first under the pseudo-normalized representation
    if pre_norm:
        for pre in ("a_", "b_"):
            _lzc(m, lzc_fam, lzc_pins, f"{pre}sig", XW, f"{pre}lz", f"operand {pre[0]}: leading zeros (pseudo-normalized representation)")
            m.wire(f"{pre}lzs", _clog2(XW), expr=f"({pre}sig == 0) ? {_clog2(XW)}'d0 : {pre}lz[{_clog2(XW)-1}:0]")
            _shift(m, nm_sh_fam, nm_sh_pins, f"{pre}sig", XW, f"{pre}lzs", 0, f"{pre}nsig", f"operand {pre[0]} normalized")
            m.wire(f"{pre}lzx", EW, signed=True, expr=f"$signed({{{{({EW}-{XW.bit_length()}){{1'b0}}}}, {pre}lz}})")
            _exp_sub(m, exp_fam, exp_pins, EW, f"{pre}e", f"{pre}lzx", f"{pre}ne", f"operand {pre[0]}: the exponent lowered by the count")
        siga, sigb, ea, eb = "a_nsig", "b_nsig", "a_ne", "b_ne"
    else:
        siga, sigb, ea, eb = "a_sig", "b_sig", "a_e", "b_e"
    # ---- exponent path
    m.wire("eax", EW + 1, signed=True, expr=f"$signed({{{ea}[{EW-1}], {ea}}})")
    m.wire("ebx", EW + 1, signed=True, expr=f"$signed({{{eb}[{EW-1}], {eb}}})")
    _exp_sub(m, exp_fam, exp_pins, EW + 1, "eax", "ebx", "d", "the exponent difference")
    if exp_dual:
        _exp_sub(m, exp_fam, exp_pins, EW + 1, "ebx", "eax", "dn", "the exponent difference the other way, in parallel")
    else:
        m.wire("zero_x", EW + 1, signed=True, expr=f"{EW+1}'sd0")
        _exp_sub(m, exp_fam, exp_pins, EW + 1, "zero_x", "d", "dn", "the difference negated")
    # the operand order: under the swap the larger magnitude leads (the significands compared at equal exponents);
    # unswapped, the exponent order alone decides who shifts, and the significand adder's carry decides the sign
    m.wire("a_big", expr=f"(d > 0) || (d == 0 && {siga} >= {sigb})" if swap else "d >= 0")
    m.wire("dabs", EW + 1, expr="a_big ? d : dn")
    m.wire("e_big", EW, signed=True, expr=f"a_big ? {ea} : {eb}")
    m.wire("s_big", expr="a_big ? a_s : b_s")
    m.wire("eff_sub", expr="a_s ^ b_s")
    GS = 0 if pre_norm else G           # the guard shift: none when the operands were normalized to bit XW-1

    def window(sig: str) -> str:
        return f"{{1'b0, {sig}}}" if (pre_norm or G == 0) else f"{{1'b0, {sig}[{SW-1}:0], {G}'d0}}"

    if swap:
        m.wire("big_sig", XW, expr=f"a_big ? {siga} : {sigb}")
        m.wire("sml_sig", XW, expr=f"a_big ? {sigb} : {siga}")
        m.wire("big_st", expr="a_big ? a_st : b_st")
        m.wire("sml_st", expr="a_big ? b_st : a_st")
        m.wire("mb", IW, expr=window("big_sig"))
        m.wire("ms0", IW, expr=window("sml_sig"))
    else:
        m.wire("ma0", IW, expr=window(siga))
        m.wire("mb0", IW, expr=window(sigb))

    def lim_of(max_shift):
        # the full window: the engine keeps every bit of it (a shift bound below the window changes the
        # packed result under the stochastic mode, which compares the dropped bits exactly)
        return IW - 1 if max_shift is None else max_shift

    def align_one(pre: str, src: str, src_sig: str, src_st: str, sel: str, lim: int, comment: str):
        """m_<pre>, stb_<pre>: `src` (IW bits) shifted right by dabs when `sel`
        (else unshifted), the sticky of what left the window (by the
        sticky method) and the operand's own sticky."""
        aw = _clog2(lim + 1) if lim >= 1 else 1
        m.wire(f"far_{pre}", expr=f"{sel} && (dabs > {lim})")
        m.wire(f"amt_{pre}", aw, expr=f"(!({sel}) || far_{pre}) ? {aw}'d0 : dabs[{aw-1}:0]")
        if aw < AW:
            m.wire(f"amtw_{pre}", AW, expr=f"{{{{({AW}-{aw}){{1'b0}}}}, amt_{pre}}}")
            amt = f"amtw_{pre}"
        else:
            amt = f"amt_{pre}"
        if lim >= 1:
            _shift(m, al_sh_fam, al_sh_pins, src, IW, amt, 1, f"mssh_{pre}",
                   f"{comment}: the operand shifted right by the exponent difference",
                   sticky=f"stk0_{pre}" if sticky_method == "or_tree_shifted_out" else None)
        else:
            m.wire(f"mssh_{pre}", IW, expr=src)
            if sticky_method == "or_tree_shifted_out":
                m.wire(f"stk0_{pre}", expr="1'b0")
        m.wire(f"m_{pre}", IW, expr=f"far_{pre} ? {IW}'d0 : mssh_{pre}")
        if sticky_method == "or_tree_shifted_out":
            m.wire(f"stk_{pre}", expr=f"far_{pre} ? ({src_sig} != 0) : stk0_{pre}")
        elif sticky_method == "trailing_zero_compare":
            m.wire(f"tz_{pre}", IW.bit_length())
            if not m.inst("tzc", tzc_fam, tzc_pins, IW, f".a({src}), .n(tz_{pre})", f"{comment}: trailing zeros of the operand"):
                m.raw(f"  always_comb begin tz_{pre} = {IW}; for (int k = 0; k < {IW}; k = k + 1) if ({src}[k]) begin tz_{pre} = k; break; end end")
            m.wire(f"stk_{pre}", expr=f"far_{pre} ? ({src_sig} != 0) : (({src} != 0) && (tz_{pre} < amt_{pre}))")
        else:
            _thermo(m, f"mask_{pre}", IW, f"amt_{pre}", f"{comment}: the mask of the positions the shift drops")
            m.wire(f"stk_{pre}", expr=f"far_{pre} ? ({src_sig} != 0) : (|({src} & mask_{pre}))")
        m.wire(f"stb_{pre}", expr=f"{src_st} | stk_{pre}")

    def align(pre: str, max_shift, comment: str):
        """The aligned operands of a path: under the swap, mb and ms_<pre>
        with the smaller's sticky stb_<pre>; unswapped, ma_<pre> and mb_<pre>
        with sta_<pre> and stb_<pre>."""
        lim = lim_of(max_shift)
        if swap:
            align_one(pre, "ms0", "sml_sig", "sml_st", "1'b1", lim, comment)
            m.wire(f"ms_{pre}", IW, expr=f"m_{pre}")
        else:
            align_one(pre + "a", "ma0", siga, "a_st", "~a_big", lim, comment + " (operand a)")
            align_one(pre + "b", "mb0", sigb, "b_st", "a_big", lim, comment + " (operand b)")
            m.wire(f"ma_{pre}", IW, expr=f"m_{pre}a")
            m.wire(f"mb_{pre}", IW, expr=f"m_{pre}b")
            m.wire(f"sta_{pre}", expr=f"stb_{pre}a")
            m.wire(f"stb_{pre}", expr=f"stb_{pre}b")

    def gate(pre: str, x: str, iso, width: int):
        return x if iso is None else m.wire(f"{x}_i{pre}", width, expr=f"{iso} ? {x} : {width}'d0")

    def sig_add(pre: str, iso, comment: str):
        """r_<pre>, the window sum or difference of the path's aligned operands."""
        if swap:
            # one adder serves the add and the subtract: b complemented and the sticky borrow as the carry-in
            mbi = gate(pre, "mb", iso, IW)
            m.wire(f"bop_{pre}", IW, expr=f"eff_sub ? ~ms_{pre} : ms_{pre}")
            bopi = gate(pre, f"bop_{pre}", iso, IW)
            if sub_style == "ones_complement_end_around":
                r0 = _adder(m, sig_fam, sig_pins, IW, mbi, bopi, f"r0_{pre}", f"{comment}: the significand adder ({sig_fam})", cout=f"co0_{pre}")
                _incr(m, eac_fam, eac_pins, IW, r0, "1'b1", f"r1_{pre}", f"co1_{pre}", f"{comment}: the end-around carry through the incrementer ({eac_fam})")
                m.wire(f"r_{pre}", IW, expr=f"(eff_sub && !stb_{pre}) ? r1_{pre} : r0_{pre}")
                m.wire(f"co_{pre}", expr=f"(eff_sub && !stb_{pre}) ? (co0_{pre} | co1_{pre}) : co0_{pre}")
            else:
                m.wire(f"cin_{pre}", expr=f"eff_sub ? ~stb_{pre} : 1'b0")
                m.wire(f"co_{pre}")
                if external:
                    m.raw(f"  // {comment}: the significand adder is the unit's carry-propagate adder shared with the integer "
                          f"adders (ports sa_*)")
                    m.assign("sa_a", mbi)
                    m.assign("sa_b", bopi)
                    m.assign("sa_cin", f"cin_{pre}")
                    m.wire(f"r_{pre}", IW, expr="sa_s")
                    m.assign(f"co_{pre}", "sa_cout")
                else:
                    _adder(m, sig_fam, sig_pins, IW, mbi, bopi, f"r_{pre}", f"{comment}: the significand adder ({sig_fam})", cin=f"cin_{pre}", cout=f"co_{pre}")
            return f"r_{pre}", f"stb_{pre}"
        # unswapped: X (operand a's window, sticky sta) and Y (operand b's, sticky stb), one of them shifted; the
        # sum, or the magnitude of the difference by the negation scheme. A subtraction borrows the shifted
        # operand's sticky: the exact difference is X + sta.e - (Y + stb.e) with 0 < e < 1, so its integer part
        # is X - Y - stb when non-negative and Y - X - sta when negative (the shifted operand is the smaller)
        mai = gate(pre, f"ma_{pre}", iso, IW)
        m.wire(f"yop_{pre}", IW, expr=f"eff_sub ? ~mb_{pre} : mb_{pre}")
        yopi = gate(pre, f"yop_{pre}", iso, IW)
        m.wire(f"nma_{pre}", IW, expr=f"~ma_{pre}")
        m.wire(f"stall_{pre}", expr=f"sta_{pre} | stb_{pre}")
        m.wire(f"cop_{pre}")
        if negation == "dual_adder":
            # X + Y, or X - Y - stb, and Y - X - sta in parallel; no carry out of the subtraction says X < Y + stb
            m.wire(f"cinp_{pre}", expr=f"eff_sub ? ~stb_{pre} : 1'b0")
            _adder(m, sig_fam, sig_pins, IW, mai, yopi, f"rp_{pre}", f"{comment}: the significand adder, X + Y or X - Y ({sig_fam})", cin=f"cinp_{pre}", cout=f"cop_{pre}")
            mbi = gate(pre, f"mb_{pre}", iso, IW)
            nmai = gate(pre, f"nma_{pre}", iso, IW)
            m.wire(f"cinn_{pre}", expr=f"~sta_{pre}")
            m.wire(f"con_{pre}")
            _adder(m, sig_fam, sig_pins, IW, mbi, nmai, f"rn_{pre}", f"{comment}: the dual adder, Y - X ({sig_fam})", cin=f"cinn_{pre}", cout=f"con_{pre}")
            m.wire(f"neg_{pre}", expr=f"eff_sub && !cop_{pre}")
            m.wire(f"r_{pre}", IW, expr=f"neg_{pre} ? rn_{pre} : rp_{pre}")
        elif negation == "complement_recode":
            # one two's complement adder: X + Y, or X - Y - stb; a negative difference is complemented after the
            # fact, the one of the two's complement withheld when a sticky borrowed (the integer part is then
            # Y - X - sta, and ~r = -r - 1)
            m.wire(f"cinp_{pre}", expr=f"eff_sub ? ~stb_{pre} : 1'b0")
            _adder(m, sig_fam, sig_pins, IW, mai, yopi, f"rp_{pre}", f"{comment}: the significand adder, X + Y or X - Y ({sig_fam})", cin=f"cinp_{pre}", cout=f"cop_{pre}")
            m.wire(f"neg_{pre}", expr=f"eff_sub && !cop_{pre}")
            m.wire(f"nrp_{pre}", IW, expr=f"~rp_{pre}")
            _incr(m, eac_fam, eac_pins, IW, f"nrp_{pre}", "1'b1", f"nrpi_{pre}", f"nrpc_{pre}", f"{comment}: the two's complement of a negative difference ({eac_fam})")
            m.wire(f"r_{pre}", IW, expr=f"!neg_{pre} ? rp_{pre} : stall_{pre} ? nrp_{pre} : nrpi_{pre}")
        else:
            # ones' complement: X + ~Y without the one; a carry out (X > Y) adds it back through the incrementer,
            # else the difference is the ones' complement of the sum; a sticky borrow withholds the one either way
            _adder(m, sig_fam, sig_pins, IW, mai, yopi, f"rp_{pre}", f"{comment}: the significand adder, X + Y or X + ~Y ({sig_fam})", cin="1'b0", cout=f"cop_{pre}")
            _incr(m, eac_fam, eac_pins, IW, f"rp_{pre}", "1'b1", f"rpi_{pre}", f"rpic_{pre}", f"{comment}: the end-around carry through the incrementer ({eac_fam})")
            m.wire(f"neg_{pre}", expr=f"eff_sub && !cop_{pre}")
            m.wire(f"r_{pre}", IW, expr=f"!eff_sub ? rp_{pre} : cop_{pre} ? (stb_{pre} ? rp_{pre} : rpi_{pre}) : (sta_{pre} ? ~rpi_{pre} : ~rp_{pre})")
        return f"r_{pre}", f"stall_{pre}"

    def sign_of(pre: str) -> str:
        """The result sign of a path: the larger operand's under the swap, else the adder's decision."""
        return "s_big" if swap else f"(neg_{pre} ? b_s : a_s)"

    def pos_of(pre: str) -> str:
        """Whether a - b is the non-negative direction of a path (the dual strings' true-sign select)."""
        return "a_big" if swap else f"(!neg_{pre})"

    def pack_window(pre: str, r: str, st_in: str, e_base: str, comment: str, normalize: bool, lza_pairs, zero_src):
        """y_<pre>: the X of the window result r (IW bits, lsb exponent e_base - GS),
        normalized when asked (leading one to bit XW-1). lza_pairs: the
        adder operand pairs the anticipator strings read ((a, b) with b the
        complemented operand; two pairs for the dual strings); zero_src:
        (x, y, st) the operand-function zero test compares."""
        sign, pos = sign_of(pre), pos_of(pre)
        m.wire(f"ovf_{pre}", expr=f"{r}[{IW-1}]")
        m.wire(f"sig0_{pre}", XW, expr=f"ovf_{pre} ? {r}[{IW-1}:1] : {r}[{XW-1}:0]")
        m.wire(f"st0_{pre}", expr=f"{st_in} | (ovf_{pre} & {r}[0])")
        _exp_const(m, exp_fam, exp_pins, EW, e_base, -GS, f"e0n_{pre}", f"{comment}: the window's exponent origin")
        _exp_const(m, exp_fam, exp_pins, EW, e_base, 1 - GS, f"e0o_{pre}", f"{comment}: the window's exponent origin after a carry out")
        m.wire(f"e0_{pre}", EW, signed=True, expr=f"ovf_{pre} ? e0o_{pre} : e0n_{pre}")
        if not normalize:
            m.wire(f"zero_{pre}", expr=f"(sig0_{pre} == 0) && !st0_{pre}")
            m.wire(f"sr_{pre}", expr=f"zero_{pre} ? 1'b0 : {sign}")
            m.wire(f"y_{pre}", XT, expr=_mkx(g, "2'd0", f"sr_{pre}", f"e0_{pre}", f"sig0_{pre}", f"st0_{pre}"))
            return
        lw = _clog2(XW)
        if lz_fam == "lza" and lza_pairs:
            counts = []
            for k, (a_src, b_src) in enumerate(lza_pairs):
                tg = f"{pre}{k}"
                f = _lza_string(m, tg, a_src, b_src, IW, restriction)
                m.wire(f"fw_{tg}", XW, expr=f"ovf_{pre} ? {f}[{IW-1}:1] : {f}[{XW-1}:0]")
                counts.append(tg)
            if len(counts) == 1 or split_sel == "true_sign":
                if len(counts) == 1:
                    m.wire(f"fws_{pre}", XW, expr=f"fw_{counts[0]}")
                else:
                    # the string of the non-negative direction (a - b when a is the larger)
                    m.wire(f"fws_{pre}", XW, expr=f"{pos} ? fw_{counts[0]} : fw_{counts[1]}")
                _lzc(m, lzc_fam, lzc_pins, f"fws_{pre}", XW, f"lzp_{pre}", f"{comment}: leading zeros of the indicator string")
                m.wire(f"lzs_{pre}", lw, expr=f"(!eff_sub || fws_{pre} == 0) ? {lw}'d0 : lzp_{pre}[{lw-1}:0]")
                m.wire(f"fz_{pre}", expr=f"fws_{pre} == 0")
            else:
                # both strings counted; the higher leading one (the smaller count) is the difference's
                for tg in counts:
                    _lzc(m, lzc_fam, lzc_pins, f"fw_{tg}", XW, f"lzp_{tg}", f"{comment}: leading zeros of the indicator string ({tg})")
                m.wire(f"lzm_{pre}", XW.bit_length(), expr=f"(lzp_{counts[0]} < lzp_{counts[1]}) ? lzp_{counts[0]} : lzp_{counts[1]}")
                m.wire(f"fz_{pre}", expr=f"(fw_{counts[0]} == 0) && (fw_{counts[1]} == 0)")
                m.wire(f"lzs_{pre}", lw, expr=f"(!eff_sub || fz_{pre}) ? {lw}'d0 : lzm_{pre}[{lw-1}:0]")
            src_lz = f"lzs_{pre}"
        else:
            _lzc(m, lzc_fam, lzc_pins, f"sig0_{pre}", XW, f"lz_{pre}", f"{comment}: leading zeros of the result")
            m.wire(f"lzs_{pre}", lw, expr=f"(sig0_{pre} == 0) ? {lw}'d0 : lz_{pre}[{lw-1}:0]")
            src_lz = f"lzs_{pre}"
        if norm_fam == "coarse_fine":
            cg = max(2, coarse)
            cb = _clog2(cg)
            # the count split into its coarse and fine fields (the granularity is a power of two)
            m.wire(f"cshift_{pre}", lw, expr=f"{{{src_lz}[{lw-1}:{cb}], {cb}'d0}}" if lw > cb else f"{lw}'d0")
            m.wire(f"fshift_{pre}", lw, expr=f"{{{{({lw}-{cb}){{1'b0}}}}, {src_lz}[{cb-1}:0]}}" if lw > cb else src_lz)
            _shift(m, nm_sh_fam, nm_sh_pins, f"sig0_{pre}", XW, f"cshift_{pre}", 0, f"sigc_{pre}", f"{comment}: the coarse normalize stage (multiples of {cg})")
            _shift(m, nm_sh_fam, nm_sh_pins, f"sigc_{pre}", XW, f"fshift_{pre}", 0, f"sign_{pre}", f"{comment}: the fine normalize stage")
        else:
            _shift(m, nm_sh_fam, nm_sh_pins, f"sig0_{pre}", XW, src_lz, 0, f"sign_{pre}", f"{comment}: the normalize shifter")
        m.wire(f"lzx_{pre}", EW, signed=True, expr=f"$signed({{{{({EW}-{lw}){{1'b0}}}}, {src_lz}}})")
        _exp_sub(m, exp_fam, exp_pins, EW, f"e0_{pre}", f"lzx_{pre}", f"en_{pre}", f"{comment}: the exponent lowered by the normalize count")
        if lz_fam == "lza" and lza_pairs and correction == "post_norm_fine_shift":
            # the anticipator errs by at most one position: one more shift when the top bit is still clear
            m.wire(f"fix_{pre}", expr=f"~sign_{pre}[{XW-1}] && (sign_{pre} != 0)")
            m.wire(f"sigf_{pre}", XW, expr=f"fix_{pre} ? {{sign_{pre}[{XW-2}:0], 1'b0}} : sign_{pre}")
            _exp_const(m, exp_fam, exp_pins, EW, f"en_{pre}", -1, f"enm_{pre}", f"{comment}: the exponent of the corrected position")
            m.wire(f"ef_{pre}", EW, signed=True, expr=f"fix_{pre} ? enm_{pre} : en_{pre}")
            sigf, ef = f"sigf_{pre}", f"ef_{pre}"
        else:
            # compensation_in_rounding: the value leaves normalized within one position; the rounder's own
            # normalization absorbs it
            sigf, ef = f"sign_{pre}", f"en_{pre}"
        if lz_fam == "lza" and lza_pairs and zero_detect == "operand_function_or":
            x_, y_, st_ = zero_src
            m.wire(f"zero_{pre}", expr=f"eff_sub && ({x_} == {y_}) && !{st_}")
        else:
            m.wire(f"zero_{pre}", expr=f"({sigf} == 0) && !st0_{pre}")
        m.wire(f"sr_{pre}", expr=f"zero_{pre} ? 1'b0 : {sign}")
        m.wire(f"y_{pre}", XT, expr=_mkx(g, "2'd0", f"sr_{pre}", ef, sigf, f"st0_{pre}"))

    def pairs_of(pre: str):
        """The anticipator's operand pairs of a path: (larger, complemented smaller) under the swap;
        both directions unswapped (the dual strings, or the a - b string alone)."""
        if swap:
            return [("mb", f"bop_{pre}")]
        if dual:
            return [(f"ma_{pre}", f"yop_{pre}"), (f"mb_{pre}", f"nma_{pre}")]
        return [(f"ma_{pre}", f"yop_{pre}")]

    def zero_src_of(pre: str):
        if swap:
            return ("mb", f"ms_{pre}", f"stb_{pre}")
        return (f"ma_{pre}", f"mb_{pre}", f"stall_{pre}")

    if npaths == 1:
        align("f", None, "align")
        r, stb = sig_add("f", None, "add")
        m.wire("st_f", expr=f"{'big_st' if swap else '1' + chr(39) + 'b0'} | {stb}")
        pack_window("f", r, "st_f", "e_big", "normalize", True, pairs_of("f"), zero_src_of("f"))
        result = "y_f"
    else:
        if trigger == "exp_diff_only":
            m.wire("close", expr=f"dabs <= {threshold}")
        else:
            m.wire("close", expr=f"(dabs <= {threshold}) && eff_sub")
        early = select_point == "early_exponent_compare"
        big_st = "big_st" if swap else "1'b0"
        # the far path: the full aligner, one adder, no big normalizer (a 1-bit carry at most)
        if npaths == 3:
            m.wire("far_add", expr="~eff_sub")
            m.wire("far_sub", expr="eff_sub && !close")
            align("f", None, "far path align")
            for tag_, iso, cm in (("fad", "far_add" if early else None, "far add path"), ("fsb", "far_sub" if early else None, "far subtract path")):
                # the far paths share the alignment (f); each has its own adder
                if swap:
                    m.wire(f"ms_{tag_}", IW, expr="ms_f")
                else:
                    m.wire(f"ma_{tag_}", IW, expr="ma_f")
                    m.wire(f"mb_{tag_}", IW, expr="mb_f")
                    m.wire(f"sta_{tag_}", expr="sta_f")
                m.wire(f"stb_{tag_}", expr="stb_f")
                r, stb = sig_add(tag_, iso, cm)
                m.wire(f"st_{tag_}", expr=f"{big_st} | {stb}")
                pack_window(tag_, r, f"st_{tag_}", "e_big", cm, False, None, None)
            far_result = "eff_sub ? y_fsb : y_fad"
        else:
            align("f", None, "far path align")
            r, stb = sig_add("f", "~close" if early else None, "far path")
            m.wire("st_f", expr=f"{big_st} | {stb}")
            pack_window("f", r, "st_f", "e_big", "far path", False, None, None)
            far_result = "y_f"
        # the close path: a shift of at most the threshold, the subtractor, the anticipator and the normalizer
        align("c", threshold, "close path align")
        r, stb = sig_add("c", "close" if early else None, "close path")
        m.wire("st_c", expr=f"{big_st} | {stb}")
        pack_window("c", r, "st_c", "e_big", "close path", True, pairs_of("c"), zero_src_of("c"))
        m.wire("y_sel", XT, expr=f"close ? y_c : ({far_result})")
        result = "y_sel"
    # ---- the specials, as the engine orders them
    nan_x = _mkx_special(g, "2'd1")
    inf_a = _mkx_special(g, "2'd2", "a_s")
    inf_b = _mkx_special(g, "2'd2", "b_s")
    m.wire("both_inf", expr="(a_sp == 2'd2) && (b_sp == 2'd2)")
    m.wire("y_sp", XT, expr=(f"(a_sp == 2'd1 || b_sp == 2'd1) ? {nan_x} : "
                              f"both_inf ? ((a_s == b_s) ? {inf_a} : {nan_x}) : "
                              f"(a_sp == 2'd2) ? {inf_a} : "
                              f"(b_sp == 2'd2) ? {inf_b} : "
                              f"a_z ? xbs : b_z ? xa : {result}"))
    m.assign("y", "y_sp")
    return name, m.render()


FMA_FAMILIES = ("classic_fma", "reduced_latency_fma", "multipath_fma", "bridge_fma")


def fma_normalization(family: str, pins: dict) -> str | None:
    """What a fused multiply-add of the fp_fma slot promises about its
    finite results' form: `exact` (the leading one at the top of the X,
    or an exact zero, or a lone sticky), `within_one` (the leading one at
    the top or one position below it: the anticipator under
    `lza.correction_scheme: compensation_in_rounding` leaves its
    one-position error to the rounder's own normalization, as the fp
    adder families do under that member), or None (no promise: a
    separate multiplier and adder, and bridge_fma's bridge_reuse, whose
    adder returns the other operand as it came when one operand is
    zero)."""
    if family not in FMA_FAMILIES:
        return None
    pins = pins or {}
    if family == "bridge_fma" and str(_pin(pins, "composition_style", "bridge_reuse")) != "monolithic_fused":
        return None
    if str(_pin(pins, "lza.family", "lza")) == "lza" \
            and str(_pin(pins, "lza.correction_scheme", "post_norm_fine_shift")) == "compensation_in_rounding":
        return "within_one"
    return "exact"


def fma_normalizes(family: str, pins: dict) -> bool:
    """Whether a fused multiply-add of the fp_fma slot delivers every finite
    result normalized (fma_normalization `exact`), which lets the mode's
    rounder take normalized_input."""
    return fma_normalization(family, pins) == "exact"


def fma_takes_rnd(family: str, pins: dict) -> bool:
    """Whether the fp_fma slot's module takes the rounding mode (`rnd`) and
    delivers a normal result already rounded (the ROUNDED code):
    reduced_latency_fma under `rounding_position: fused_with_cpa_dual_sum`.
    The mode's rounder then packs it without a second increment, so the
    seed instantiates the library rounder for such a mode."""
    return family == "reduced_latency_fma" and \
        str(_pin(pins or {}, "rounding_position", "post_cpa")) == "fused_with_cpa_dual_sum"


FMA_OP_CODES = {"fadd": 0, "fsub": 1, "fmul": 2, "fmadd": 3, "fmsub": 4, "fnmsub": 5, "fnmadd": 6}
"""The `fop` code of the fused multiply-add module: the op it computes on
xa, xb and xc (fadd is xa + xb, fsub xa - xb, fmul xa * xb; fmadd
xa * xb + xc, fmsub xa * xb - xc, fnmsub -(xa * xb) + xc, fnmadd
-(xa * xb) - xc, the RISC-V F extension's four)."""


def fma_sv(g: Geom, family: str, pins: dict, name: str | None = None, fmt=None) -> tuple:
    """(name, text): the op `fop` (FMA_OP_CODES) on xa, xb and xc through
    one fused multiply-add of the fp_fma slot's family (dot.py's _fma_sv,
    d = c + a * b under the fused contract): fadd is 1 * xa + xb, fmul is
    xa * xb + (a zero of the product's sign), and the four fused ops are
    (-1)^np * xa * xb + (-1)^nc * xc with the negations folded into the
    signs of xa and xc. The slots are the family's: multiplier, align,
    lza, cpa, norm_shifter; negation_handling is the window sum's;
    `sharing` is the seed's (one instance per mode, or one over the modes
    that select it) and leaves the module alone. The specials as the
    engine orders them for each op. `fmt` is the mode's float format,
    which the fused rounding of reduced_latency_fma rounds for (the
    module then takes `rnd`, fma_takes_rnd)."""
    from chialu.targets.rtl.families import dot as DOT
    pins = pins or {}
    XW, EW, XT, SW = g.XW, g.EW, g.XT, g.SW
    if family not in FMA_FAMILIES:
        raise ValueError(f"fp_fma family {family!r}: no module (separate_multiplier_and_adder is the fp_adder's and "
                         f"the fp_multiplier's own structures)")
    negation = str(_pin(pins, "negation_handling", "end_around_carry"))
    if negation not in NEGATIONS:
        raise ValueError(f"{family} negation_handling {negation!r}: one of {', '.join(NEGATIONS)}")
    fused_round = fma_takes_rnd(family, pins)
    if fused_round:
        # the rules: the rounding position is the mode's format's, so the module needs the format, one datapath
        # shared across formats cannot round for each, and the rounding within the window needs the exact X (the
        # kept bits and the guard of the format lie inside the product's frame, as under round_fused_in_reduction).
        # chialu/behavior_rules.py states the three on the member (x_form_exact and significand_in_mode over the
        # contract, sharing_dedicated_per_mode as a member condition on the sibling); the raises are the last defense
        if str(_pin(pins, "sharing", "dedicated_per_mode")) == "shared_across_formats":
            raise ValueError("fp_fma reduced_latency_fma rounding_position fused_with_cpa_dual_sum rounds for the mode's "
                             "format inside the window adder; one datapath shared across formats (sharing "
                             "shared_across_formats) has no one format to round for, so the fused rounding takes "
                             "sharing dedicated_per_mode (a member condition of chialu.behavior_rules)")
        if g.tight:
            raise ValueError("fp_fma reduced_latency_fma rounding_position fused_with_cpa_dual_sum rounds within the "
                             "product's frame, as round_fused_in_reduction does, and needs the exact X (the unit option "
                             "x_form exact; chialu.behavior_rules removes the member under guard_round_sticky): this "
                             "mode's guard-round-sticky X is narrower than the product")
        if fmt is None or not isinstance(fmt, FloatFormat) or getattr(fmt, "exp_only", False):
            raise ValueError("fp_fma reduced_latency_fma rounding_position fused_with_cpa_dual_sum needs the mode's "
                             "float format with a significand (the rounding position is the format's precision; "
                             "significand_in_mode of chialu.behavior_rules)")
    # the subnormal operands as stored (FPnew: the window's exponent alignment places them, the one normalize
    # after the sum absorbs their leading zeros) or normalized at entry; the stochastic mode compares the dropped
    # bits exactly and needs the normalized operands' full window
    style = str(_pin(pins, "composition_style", "bridge_reuse")) if family == "bridge_fma" else None
    if style is not None and style not in ("bridge_reuse", "cascade_mul_then_add", "monolithic_fused"):
        raise ValueError(f"bridge_fma composition_style {style!r}")
    if style == "cascade_mul_then_add":
        # the rule: a cascade rounds the product before the add, so fadd, fsub and fmul through it are not the
        # result of one rounding of the exact value, and its product rounding (cascade_product_rounding, one
        # fixed mode) is not the mode's `rounding`, which the ALU's fma_contract sequential rounds the product
        # under; the separate multiplier and adder realize that contract. chialu/behavior_rules.py removes the
        # member from the ALU's slot under every contract (fma_contract_cascade_product_rounding); the last defense
        raise ValueError("fp_fma bridge_fma composition_style cascade_mul_then_add rounds the product before the add "
                         "under its own fixed cascade_product_rounding, which is neither the one rounding the mode's "
                         "fadd, fsub and fmul promise nor the mode's rounding that fma_contract sequential rounds the "
                         "product under; the sequential contract's fused ops go through separate_multiplier_and_adder")
    if style == "bridge_reuse" and g.tight:
        # the rule: the bridge carries the exact 2 SW-bit product into an adder generated for that width;
        # chialu/behavior_rules.py removes the member under x_form guard_round_sticky, this raise is the last defense
        raise ValueError("fp_fma bridge_fma composition_style bridge_reuse carries the exact 2 SW-bit product across the "
                         "bridge into an adder generated for that width; the guard-round-sticky X (the unit option "
                         "x_form guard_round_sticky) is narrower than the product, so the bridge needs the exact X")
    subnormal = str(_pin(pins, "subnormal_representation", "as_stored"))
    if subnormal not in ("as_stored", "pseudo_normalized_wide_exponent"):
        raise ValueError(f"{family} subnormal_representation {subnormal!r}")
    if subnormal == "as_stored" and g.sr and style != "bridge_reuse":
        # the last defense behind the no_sr rule of chialu/behavior_rules.py on the fp_fma slot; the bridge's
        # adder normalizes both addends at its entry, so the choice is inactive under bridge_reuse
        raise ValueError(f"{family}: subnormal_representation as_stored serves the IEEE rounding modes; the stochastic "
                         f"mode compares the dropped bits exactly and needs pseudo_normalized_wide_exponent")
    fpins = {k: v for k, v in pins.items() if k != "sharing"}
    fpins["negation_handling"] = negation
    fpins["subnormal_representation"] = subnormal
    if family == "classic_fma" or style == "monolithic_fused":
        fpins["subsume_fp_add"] = True
    dg = DOT.DotGeom(g, 1, SW, SW, XW, 0, True, None, fmt if fused_round else None, out="y")
    core_name = f"fam_fp_fma_core_{family}_{g.tag()}" + (f"_{fmt.name}" if fused_round else "") + _tag(fpins)
    if style is None:
        inner_name, inner_text, _info = DOT._fma_sv(dg, family, fpins, core_name)
        organization = f"the window sum's negation by {negation}" + (
            f"; the rounding for {fmt.name} fused into the window adder's compound sum (a normal result leaves "
            f"rounded, with the ROUNDED code; a subnormal, an overflow and the stochastic mode leave unrounded)"
            if fused_round else "")
    else:
        # the bridge: the library's fp multiplier and fp adder composed (monolithic_fused is classic_fma's text and
        # keeps classic_fma's subnormal_representation); the bridge's adder normalizes both addends at its entry, so
        # under bridge_reuse subnormal_representation is not its choice (alu_contracts names it inactive there, and a
        # deferred rule of chialu/behavior_rules.py records it)
        if style == "bridge_reuse":
            fpins.pop("subnormal_representation", None)
        inner_name, inner_text, _info = DOT._bridge_sv(dg, family, fpins, core_name)
        organization = (f"the bridge {style}: the significand product crosses into the adder of the family's own "
                        f"align, lza, cpa and norm_shifter slots" if style == "bridge_reuse"
                        else f"monolithic_fused (classic_fma's datapath), the window sum's negation by {negation}")
    name = name or f"fam_fp_fma_{family}_{g.tag()}{_tag(pins)}"
    m = Mod(name, f"fp fused multiply-add ({family}): the mode's adder, its multiplier and the fused ops fmadd, "
                  f"fmsub, fnmsub, fnmadd through one datapath {inner_name} under the op code fop (0 fadd, 1 fsub, "
                  f"2 fmul, 3 fmadd, 4 fmsub, 5 fnmsub, 6 fnmadd): fadd is 1 * xa + xb, fmul is xa * xb + (a zero of "
                  f"the product's sign), a fused op negates xa for the negated product and xc for the negated addend; "
                  f"{organization}; the significand multiplier "
                  f"{_pin(pins, 'multiplier.family', 'behavioral_star')}; the specials as the engine orders them for each op")
    m.port("input", "xa", XT)
    m.port("input", "xb", XT)
    m.port("input", "xc", XT)
    m.port("input", "fop", 3)
    if fused_round:
        m.port("input", "rnd", 3)
    m.port("output", "y", XT)
    m.extra.append(inner_text)
    _x_fields(m, "xa", g, "a_")
    _x_fields(m, "xb", g, "b_")
    # the op code: the two-operand ops, and the negations of the product and of the addend
    m.wire("is_add", expr="fop[2:1] == 2'b00")
    m.wire("is_mul", expr="fop == 3'd2")
    m.wire("neg_p", expr="(fop == 3'd5) || (fop == 3'd6)")
    m.wire("neg_c", expr="(fop == 3'd1) || (fop == 3'd4) || (fop == 3'd6)")
    m.wire("xan", XT, expr=f"{{xa[{XT-1}:{XT-2}], xa[{XT-3}] ^ neg_p, xa[{XT-4}:0]}}")
    m.wire("addend", XT, expr="is_add ? xb : xc")
    m.wire("xcn", XT, expr=f"{{addend[{XT-1}:{XT-2}], addend[{XT-3}] ^ neg_c, addend[{XT-4}:0]}}")
    # the operand roles: the product's factors and the addend
    one_x = _mkx(g, "2'd0", "1'b0", _slit(EW, -(SW - 1)), f"{XW}'d{1 << (SW - 1)}", "1'b0")
    m.wire("ps", expr="a_s ^ b_s")
    zero_p = _mkx(g, "2'd0", "ps", f"{EW}'sd0", f"{XW}'d0", "1'b0")
    m.wire("fa", XT, expr=f"is_add ? {one_x} : xan")
    m.wire("fb", XT, expr="is_add ? xa : xb")
    m.wire("fc", XT, expr=f"is_mul ? {zero_p} : xcn")
    m.wire("yf", XT)
    m.raw("  // the fused datapath: fc + fa * fb")
    m.raw(f"  {inner_name} u_fma (.xa(fa), .xb(fb), .xc(fc){', .rnd(rnd)' if fused_round else ''}, .y(yf));")
    # the specials as the engine orders them: a NaN operand, an invalid product (inf * 0), infinities of opposite
    # sign, an infinite product, an infinite addend; every finite case, a zero factor or a zero addend included,
    # is the datapath's, so a finite result leaves normalized (the leading one at the top of the X, or an exact
    # zero, or a lone sticky), which the rounder relies on
    for src, pre in (("fa", "fa_"), ("fb", "fb_"), ("fc", "fc_")):
        _x_fields(m, src, g, pre)
    nan_x = _mkx_special(g, "2'd1")
    m.wire("p_nan", expr="(fa_sp == 2'd1) || (fb_sp == 2'd1)")
    m.wire("p_inf", expr="(fa_sp == 2'd2) || (fb_sp == 2'd2)")
    m.wire("p_inv", expr="p_inf && ((fa_sp == 2'd0 && fa_z) || (fb_sp == 2'd0 && fb_z))")
    m.wire("fps", expr="fa_s ^ fb_s")
    m.wire("c_nan", expr="fc_sp == 2'd1")
    m.wire("c_inf", expr="fc_sp == 2'd2")
    inf_p = _mkx_special(g, "2'd2", "fps")
    inf_c = _mkx_special(g, "2'd2", "fc_s")
    m.wire("y_sp", XT, expr=(f"(p_nan || c_nan || p_inv) ? {nan_x} : "
                             f"(p_inf && c_inf && (fps != fc_s)) ? {nan_x} : "
                             f"p_inf ? {inf_p} : c_inf ? {inf_c} : yf"))
    m.assign("y", "y_sp")
    return name, m.render()


# ---- the significand multiplier ------------------------------------------------------
ROUNDED = "2'd3"            # the X special code of a value a producer already rounded: the rounder adds no
                            # increment, reports inexact, and reads the tininess decision from the sticky bit


def mul_sv(g: Geom, family: str, pins: dict, M: int | None = None, name: str | None = None, bias: int | None = None,
           scale_feedback: bool = False, scale_format=None, target_format=None, tokens=None) -> tuple:
    """(name, text): xa * xb -> X. The significand multiplier is the library
    multiplier of the sig_mul family over the SW-bit stored significands
    (their product fits the X field, so the sticky is the operands'), the
    exponent sum through the exp_adder slot; round_fused_in_reduction adds
    the rounding injection for the target precision M through the
    injection_adder slot and truncates, so the value the rounder receives
    is already at M+1 bits under the IEEE modes (the stochastic mode keeps
    the exact product); sticky_method names the sticky's source (the
    dropped product bits, or the operands' trailing-zero counts through
    the tzc slot); the lzc slot counts the product's leading zeros for the
    rounding position."""
    pins = pins or {}
    XW, EW, XT, SW = g.XW, g.EW, g.XT, g.SW
    fused = family == "round_fused_in_reduction"
    if scale_feedback and scale_format is not None and (not scale_format.exp_only or not isinstance(target_format, FloatFormat)):
        from chialu.targets.rtl.families.fp_block_fused import mul_sv as block_mul_sv
        return block_mul_sv(g, pins, scale_format, target_format, name, tokens)
    name = name or f"fam_fp_mul_{family}_{g.tag()}" + (f"_m{M}" if fused and M is not None else "") + _tag(pins)
    if scale_feedback:
        if not fused:
            raise ValueError("scale feedback is a fused-rounding interface")
        name += "_scale"
    mul_fam, mul_pins = str(_pin(pins, "sig_mul.family", "direct_pp_parallel")), _sub(pins, "sig_mul.")
    exp_fam, exp_pins = str(_pin(pins, "exp_adder.family", "ripple_carry")), _sub(pins, "exp_adder.")
    sticky = str(_pin(pins, "sticky_method", "post_cpa_or_tree")) if fused else "post_cpa_or_tree"
    m = Mod(name, f"fp significand multiplier ({family}): {mul_fam} over the {SW}-bit significands, the exact product in the "
                  f"X field, the exponent sum on a {exp_fam} adder" + (f"; the rounding for {M+1} bits injected into the product, "
                                                                    f"sticky by {sticky}" if fused else ""))
    m.port("input", "xa", XT)
    m.port("input", "xb", XT)
    if fused:
        m.port("input", "rnd", 3)
    if scale_feedback:
        m.port("input", "scale_exp", EW, signed=True)
        m.port("output", "raw_y", XT)
    m.port("output", "y", XT)
    _x_fields(m, "xa", g, "a_")
    _x_fields(m, "xb", g, "b_")
    m.wire("s", expr="a_s ^ b_s")
    m.wire("sa", SW, expr=f"a_sig[{SW-1}:0]")
    m.wire("sb", SW, expr=f"b_sig[{SW-1}:0]")
    m.wire("p", 2 * SW)
    if not m.inst("mul", mul_fam, mul_pins, SW, ".a(sa), .b(sb), .p(p)", f"the significand product ({mul_fam})"):
        m.assign("p", "sa * sb")
    _exp_add(m, exp_fam, exp_pins, EW, "a_e", "b_e", "e", "the exponent sum")
    cut = max(0, 2 * SW - XW)                   # the product bits below the X field (the guard-round-sticky X)
    if fused and cut:
        raise ValueError("round_fused_in_reduction rounds within the product's frame and needs the exact X "
                         "(the unit option x_form exact; chialu.behavior_rules prunes the family under guard_round_sticky): this mode's guard-round-sticky X is narrower than the product")
    if cut:
        # Stored subnormal significands need not reach the top of the product.
        # Normalize the *exact* product before discarding any bits. Otherwise
        # a tiny product can disappear into sticky before the rounder sees it.
        _lzc(m, "lzd_cell_tree", {}, "p", 2 * SW, "product_lz", "normalize the exact product before compact X")
        m.wire("product_normal", 2 * SW, expr="p << product_lz")
        m.wire("product_lzx", EW, expr="product_lz")
        _exp_sub(m, exp_fam, exp_pins, EW, "e", "product_lzx", "product_e", "exponent of the normalized exact product")
        m.wire("st", expr=f"a_st | b_st | (|product_normal[{cut-1}:0])")
        _exp_const(m, exp_fam, exp_pins, EW, "product_e", cut, "ek", "the exponent of the kept product bits")
    else:
        m.wire("st", expr="a_st | b_st")            # the product is exact: no bits below the field
    if fused and M is not None:
        # the rounding position from the result's exponent: M+1 bits below the product's leading one for
        # a normal result, fewer for a subnormal one (the format's bias sets it); inject half an lsb
        # (nearest, a tie made even), all ones (toward the sign's infinity, away from zero) or nothing
        # (toward zero), then truncate; the value leaves with the ROUNDED code so the rounder adds no
        # increment and reports the inexact flag; the stochastic mode keeps the exact product
        PW = 2 * SW
        nw = PW.bit_length()
        b0 = bias if bias is not None else 0
        minimum_exponent = -b0 if getattr(target_format, "exp_only", False) else 1 - b0
        lzc_fam, lzc_pins = str(_pin(pins, "lzc.family", "lzd_cell_tree")), _sub(pins, "lzc.")
        inj_fam, inj_pins = str(_pin(pins, "injection_adder.family", "ripple_carry")), _sub(pins, "injection_adder.")
        _lzc(m, lzc_fam, lzc_pins, "p", PW, "plz", "the product's leading zeros (the rounding position)")
        m.wire("sigm1", nw + 1, signed=True, expr=f"$signed({{1'b0, {nw}'d{PW - 1}}}) - $signed({{1'b0, plz}})")   # sigbits - 1
        m.wire("sigm1x", EW, signed=True, expr=f"$signed({{{{({EW}-{nw+1}){{sigm1[{nw}]}}}}, sigm1}})")
        _exp_add(m, exp_fam, exp_pins, EW, "e", "sigm1x", "eu", "the leading one's exponent")
        # biased = eu + bias; the subnormal deficit 1 - biased = (1 - bias) - eu when positive
        if scale_feedback:
            _exp_const(m, exp_fam, exp_pins, EW, "scale_exp", minimum_exponent, "onemb", "minimum normal exponent at the selected block scale")
            _exp_const(m, exp_fam, exp_pins, EW, "scale_exp", minimum_exponent - 1, "minimum_below", "one exponent below the block's normal range")
            m.wire("subn", expr="eu < $signed(onemb)")
        else:
            m.wire("subn", expr=f"eu < {_slit(EW, minimum_exponent)}")
            m.wire("onemb", EW, signed=True, expr=_slit(EW, minimum_exponent))
        _exp_sub(m, exp_fam, exp_pins, EW, "onemb", "eu", "deficit", "the subnormal result's missing positions")
        m.wire("adj", EW, signed=True, expr=f"subn ? deficit : {EW}'sd0")
        m.wire("dropn0", nw + 1, signed=True, expr=f"sigm1 - {nw+1}'sd{M}")                    # sigbits - (M + 1)
        m.wire("dropn0x", EW, signed=True, expr=f"$signed({{{{({EW}-{nw+1}){{dropn0[{nw}]}}}}, dropn0}})")
        _exp_add(m, exp_fam, exp_pins, EW, "dropn0x", "adj", "drop0", "the dropped positions of the result")
        m.wire("below", expr=f"drop0 > {EW}'sd{PW}")        # the whole product lies below the rounding position
        m.wire("dropc", EW, signed=True, expr=f"(drop0 < 0) ? {EW}'sd0 : below ? {EW}'sd{PW} : drop0")
        m.wire("drop", nw + 1, expr=f"dropc[{nw}:0]")
        _thermo(m, "ones", PW + 1, "drop", "the mask of the dropped positions")
        _onehot(m, "half", PW + 1, "drop", "the half position (one below the kept lsb)", offset=1)
        _onehot(m, "lsb1", PW + 1, "drop", "the kept lsb")
        m.wire("inj", PW + 1, expr="(rnd == 3'd0) ? half : (rnd == 3'd2) ? (s ? ones : 0) : (rnd == 3'd3) ? (s ? 0 : ones) : (rnd == 3'd5) ? ones : 0")
        m.wire("px", PW + 1, expr="{1'b0, p}")
        m.wire("pi", PW + 1)
        m.wire("pico")
        _adder(m, inj_fam, inj_pins, PW + 1, "px", "inj", "pi", f"the injection added to the product ({inj_fam})", cout="pico", declare=False)
        m.wire("pr0", PW + 1, expr="pi & ~ones")
        if sticky == "input_trailing_zero_count":
            # the product's trailing zeros are the operands' summed: the dropped part is nonzero when they
            # fall short of the dropped positions, a tie when they reach the half position exactly
            tz_fam, tz_pins = str(_pin(pins, "tzc.family", "trailing_zero")), _sub(pins, "tzc.")
            for pre, src in (("a", "sa"), ("b", "sb")):
                m.wire(f"tz{pre}", SW.bit_length())
                if not m.inst("tzc", tz_fam, tz_pins, SW, f".a({src}), .n(tz{pre})", f"operand {pre}: trailing zeros"):
                    m.raw(f"  always_comb begin tz{pre} = {SW}; for (int k = 0; k < {SW}; k = k + 1) if ({src}[k]) begin tz{pre} = k; break; end end")
            m.wire("tzp", nw + 1, expr="tza + tzb")
            m.wire("inexact", expr="(p != 0) && (tzp < drop)")
            m.wire("tie", expr="(rnd == 3'd0) && (drop != 0) && (p != 0) && (tzp == drop - 1)")
        else:
            m.wire("rest", PW + 1, expr="px & ones")
            m.wire("tie", expr="(rnd == 3'd0) && (rest == half) && (drop != 0)")
            m.wire("inexact", expr="rest != 0")
        m.wire("pr", PW + 1, expr="(tie && (pr0 & lsb1) != 0 && (px & lsb1) == 0) ? (pr0 & ~lsb1) : pr0")
        injection_condition = "rnd != 3'd4"
        if isinstance(target_format, FloatFormat) and target_format.has_inf and not target_format.has_nan and target_format.man_bits:
            _onehot(m, "hole_unit", PW + 1, "sigm1", "the reserved infinity value at the product's current exponent")
            _onehot(m, "hole_carried_unit", PW + 1, "sigm1", "a carry into the reserved infinity value", offset=-1)
            exponent = "eu"
            if scale_feedback:
                _exp_sub(m, exp_fam, exp_pins, EW, "eu", "scale_exp", "hole_element_exponent", "the product exponent relative to the block scale")
                exponent = "hole_element_exponent"
            boundary = target_format.emax_code - target_format.bias
            m.wire("hole_product", expr=f"({exponent} == {_slit(EW,boundary)} && pr == hole_unit) || "
                                        f"({exponent} == {_slit(EW,boundary-1)} && pr == hole_carried_unit)")
            injection_condition += " && !hole_product"
        m.wire("use_inj", expr=injection_condition)
        m.wire("pf", PW + 1, expr="use_inj ? pr : px")
        m.wire("sp_fin", 2, expr=f"(use_inj && inexact) ? {ROUNDED} : 2'd0")
        # tininess after rounding, as the packer decides it: the pre-rounding exponent against the format's
        # minimum, unless the value rounded at the normal precision carries into the next binade at it
        emin = minimum_exponent
        m.wire("dropnc", nw + 1, expr=f"(dropn0 < 0) ? {nw+1}'d0 : (dropn0 > {nw+1}'sd{PW}) ? {nw+1}'d{PW} : dropn0[{nw}:0]")
        _thermo(m, "onesn", PW + 1, "dropnc", "the mask of the positions below the normal rounding position")
        _onehot(m, "halfn", PW + 1, "dropnc", "the half position at the normal rounding position", offset=1)
        _onehot(m, "lsbn", PW + 1, "dropnc", "the kept lsb at the normal rounding position")
        m.wire("wtop", nw + 2, expr=f"{{1'b0, dropnc}} + {nw+2}'d{M + 1}")
        _thermo(m, "wtopm", PW + 1, "wtop", "the mask below the top of the kept field at the normal position")
        m.wire("wmask", PW + 1, expr="wtopm & ~onesn")       # the kept M+1 bits at the normal position
        m.wire("restn", PW + 1, expr="px & onesn")
        m.wire("upn", expr=("(rnd == 3'd0) ? ((restn > halfn) || (restn == halfn && halfn != 0 && (px & lsbn) != 0)) : (rnd == 3'd1) ? 1'b0 : "
                             "(rnd == 3'd2) ? ((restn != 0) && s) : (rnd == 3'd3) ? ((restn != 0) && !s) : (restn != 0)"))
        m.wire("carry_n", expr="upn && ((px & wmask) == wmask)")
        if scale_feedback:
            m.wire("tiny", expr="(eu < $signed(onemb)) && !(eu == $signed(minimum_below) && carry_n)")
        else:
            m.wire("tiny", expr=f"(eu < {_slit(EW, emin)}) && !(eu == {_slit(EW, emin - 1)} && carry_n) && !(eu == {_slit(EW, -b0)} && carry_n)")
        m.wire("stf", expr="(use_inj && inexact) ? tiny : st")
        # below the rounding position: the product rounds to nothing or to one unit at that position
        m.wire("unit_up", expr="(p != 0) && ((rnd == 3'd2 && s) || (rnd == 3'd3 && !s) || rnd == 3'd5)")
        _exp_add(m, exp_fam, exp_pins, EW, "e", "drop0", "e_below", "the exponent of the unit below the rounding position")
        m.wire("y_norm", XT, expr=_mkx(g, "sp_fin", "s", "e", f"{{{{({XW}-{PW+1}){{1'b0}}}}, pf}}" if XW > PW + 1 else f"pf[{XW-1}:0]", "stf"))
        m.wire("y_below", XT, expr=_mkx(g, ROUNDED, "s", "e_below", f"{{{{({XW}-1){{1'b0}}}}, unit_up}}", "tiny"))
        m.wire("y_fin", XT, expr="(use_inj && below && (p != 0)) ? y_below : y_norm")
    elif cut:
        m.wire("y_fin", XT, expr=_mkx(g, "2'd0", "s", "ek", f"product_normal[{2*SW-1}:{cut}]", "st"))
    else:
        m.wire("y_fin", XT, expr=_mkx(g, "2'd0", "s", "e", f"{{{{({XW}-{2*SW}){{1'b0}}}}, p}}" if XW > 2 * SW else "p", "st"))
    nan_x = _mkx_special(g, "2'd1")
    inf_s = _mkx_special(g, "2'd2", "s")
    m.wire("y_sp", XT, expr=(f"(a_sp == 2'd1 || b_sp == 2'd1) ? {nan_x} : "
                              f"(a_sp == 2'd2 || b_sp == 2'd2) ? (((a_sp == 2'd0 && a_z) || (b_sp == 2'd0 && b_z)) ? {nan_x} : {inf_s}) : "
                              f"y_fin"))
    m.assign("y", "y_sp")
    if scale_feedback:
        raw = _mkx(g, "2'd0", "s", "e", f"{{{{({XW}-{2*SW}){{1'b0}}}}, p}}" if XW > 2 * SW else "p", "st")
        m.assign("raw_y", f"(a_sp == 2'd1 || b_sp == 2'd1) ? {nan_x} : "
                 f"(a_sp == 2'd2 || b_sp == 2'd2) ? (((a_sp == 2'd0 && a_z) || (b_sp == 2'd0 && b_z)) ? {nan_x} : {inf_s}) : {raw}")
    return name, m.render()


# ---- the comparator ----------------------------------------------------------------
def cmp_sv(g: Geom, family: str, pins: dict, name: str | None = None) -> tuple:
    """(name, text): lt and eq of two finite-or-infinite X values as the
    engine orders them (sign, then magnitude; both zeros equal).
    integer_compare_on_bits compares {exp, sig, sticky} as one magnitude
    word through one comparator of the `comparator` slot;
    dedicated_magnitude_comparator compares the exponents, then the
    significands, each through a comparator of the slot."""
    pins = pins or {}
    XW, EW, XT = g.XW, g.EW, g.XT
    cmp_fam, cmp_pins = str(_pin(pins, "comparator.family", "prefix_comparator")), _sub(pins, "comparator.")
    name = name or f"fam_fp_cmp_{family}_{g.tag()}{_tag(pins)}"
    m = Mod(name, f"fp comparator ({family}, {cmp_fam})")
    m.port("input", "xa", XT)
    m.port("input", "xb", XT)
    m.port("output", "lt")
    m.port("output", "eq")
    _x_fields(m, "xa", g, "a_")
    _x_fields(m, "xb", g, "b_")
    m.wire("sa", expr="a_s && !a_z")
    m.wire("sb", expr="b_s && !b_z")
    # magnitude order of two nonzero finite values with stored significands: the exponent of bit 0
    # then the significand (both normalized or both stored); the engine's order includes the sticky.
    # The signed exponent orders as an unsigned word with its sign bit inverted.
    m.wire("aeu", EW, expr=f"{{~a_e[{EW-1}], a_e[{EW-2}:0]}}")
    m.wire("beu", EW, expr=f"{{~b_e[{EW-1}], b_e[{EW-2}:0]}}")
    if family == "integer_compare_on_bits":
        cw = EW + XW + 1
        m.wire("ma", cw, expr="{aeu, a_sig, a_st}")
        m.wire("mb", cw, expr="{beu, b_sig, b_st}")
        m.wire("mlt")
        m.wire("meq")
        if not m.inst("cmp", cmp_fam, cmp_pins, cw, ".a(ma), .b(mb), .lt(mlt), .eq(meq)", f"the magnitude words compared as integers ({cmp_fam})"):
            m.assign("mlt", "ma < mb")
            m.assign("meq", "ma == mb")
    else:
        m.wire("elt")
        m.wire("eeq")
        if not m.inst("cmp", cmp_fam, cmp_pins, EW, ".a(aeu), .b(beu), .lt(elt), .eq(eeq)", f"the exponents compared ({cmp_fam})"):
            m.assign("elt", "aeu < beu")
            m.assign("eeq", "aeu == beu")
        m.wire("slt")
        m.wire("seq")
        if not m.inst("cmp", cmp_fam, cmp_pins, XW + 1, ".a({a_sig, a_st}), .b({b_sig, b_st}), .lt(slt), .eq(seq)", f"the significands compared ({cmp_fam})"):
            m.assign("slt", "{a_sig, a_st} < {b_sig, b_st}")
            m.assign("seq", "{a_sig, a_st} == {b_sig, b_st}")
        m.wire("mlt", expr="elt || (eeq && slt)")
        m.wire("meq", expr="eeq && seq")
    m.wire("mag_lt", expr="a_z ? 1'b1 : b_z ? 1'b0 : mlt")
    m.wire("fin_eq", expr="(a_z || b_z) ? (a_z && b_z) : ((a_s == b_s) && meq)")
    m.wire("fin_lt", expr="(a_z && b_z) ? 1'b0 : (sa != sb) ? sa : (sa ? (!mag_lt && !fin_eq) : mag_lt)")
    m.wire("inf_lt", expr="(a_sp == 2'd2 && b_sp == 2'd2) ? (a_s && !b_s) : (a_sp == 2'd2) ? a_s : !b_s")
    m.wire("inf_eq", expr="(a_sp == b_sp) && (a_s == b_s)")
    m.wire("any_inf", expr="(a_sp == 2'd2) || (b_sp == 2'd2)")
    m.wire("nan_any", expr="(a_sp == 2'd1) || (b_sp == 2'd1)")
    m.assign("lt", "!nan_any && (any_inf ? inf_lt : fin_lt)")
    m.assign("eq", "!nan_any && (any_inf ? inf_eq : fin_eq)")
    return name, m.render()


# ---- the rounder --------------------------------------------------------------------
def round_sv(c, g: Geom, family: str, pins: dict, tokens: dict, name: str | None = None,
             normalized_input: bool = False) -> tuple:
    """(name, text): X -> {flags, pattern} of a float format, the engine's
    pack as a datapath: the normalizer (the lzc slot's count and the
    shifter slot's left shift), the exponent lowered by the count through
    the exp_adder slot, the right shift to the kept bits (the shifter
    slot) with the sticky of the dropped ones (a thermometer mask), the
    rounding decision, the increment by the `round` slot's family
    (increment_adder: the decision in an incrementer's carry-in;
    compound_adder_select: the kept bits plus one from an incrementer,
    selected; injection: the constant added through an adder before
    truncation; flagged_prefix: the flagged prefix adder's sum plus one),
    the exponent field's increment on a rounding carry-out (the
    exp_incrementer slot), overflow and ftz. `family` is the rounder's
    sharing pattern (or the converter's family), a label. `normalized_input`:
    every producer of the mode delivers its leading one at bit XW-1 (or an
    exact zero, or a lone sticky), as the fused multiply-add does, so the
    normalizer's count and shift are not built."""
    pins = pins or {}
    M, E, bias, W = c.man_bits, c.exp_bits, c.bias, c.width
    if c.exp_only:
        from chialu.targets.rtl.families.fp_exp import round_sv as round_exp_sv
        return round_exp_sv(c, g, family, pins, tokens, name)
    XW, EW, XT, sb = g.XW, g.EW, g.XT, g.sr_bits
    tag = c.name.replace(".", "_")
    round_fam = str(_pin(pins, "round.family", "increment_adder"))
    lzc_fam, lzc_pins = str(_pin(pins, "lzc.family", "lzd_cell_tree")), _sub(pins, "lzc.")
    sh_fam, sh_pins = str(_pin(pins, "shifter.family", "barrel_mux_tree")), _sub(pins, "shifter.")
    exp_fam, exp_pins = str(_pin(pins, "exp_adder.family", "ripple_carry")), _sub(pins, "exp_adder.")
    inc_fam, inc_pins = str(_pin(pins, "exp_incrementer.family", "prefix_and_incrementer")), _sub(pins, "exp_incrementer.")
    name = name or f"fam_fp_round_{family}_{round_fam}_{tag}_{g.tag()}{_tag(pins)}" + ("_nin" if normalized_input else "")
    signed = 1 if c.signed else 0
    MW = W - signed
    top = c._top()
    maxf = c._max_finite_bits()
    emax_code = c.emax_code
    nan_bits = c.encode_special(__import__("chialu.verify.formats", fromlist=["NAN"]).NAN) if c.has_nan else 0
    inf_bits = (emax_code << M) if c.has_inf else maxf
    tin_before = tokens.get("TININESS_BEFORE", "0")
    srge = tokens.get("SRGE", "0")
    m = Mod(name, f"fp rounder ({family}, rounding {round_fam}, leading zeros {lzc_fam}, shifts {sh_fam}, exponent {exp_fam} / {inc_fam}): "
                  f"X -> {c.name} pattern and flags")
    m.port("input", "x", XT)
    m.port("input", "rnd", 3)
    m.port("input", "word", sb)
    m.port("input", "ftz")
    m.port("output", "fl", FW)
    m.port("output", "bits", W)
    _x_fields(m, "x", g, "x_")
    m.wire("s", expr=f"x_s & {signed}'d{signed}" if signed else "1'b0")
    # normalize: the leading one to bit XW-1 (a lone sticky becomes the smallest value)
    m.wire("lone", expr="(x_sig == 0) && x_st")
    if normalized_input:
        # the producer normalized: the leading one is at bit XW-1 already; a lone sticky is the smallest value,
        # moved to the top with its exponent lowered by the whole field
        m.wire("sig", XW, expr=f"lone ? ({XW}'d1 << {XW-1}) : x_sig")
        _exp_const(m, exp_fam, exp_pins, EW, "x_e", -(2 * XW - 1), "e_lone", "the exponent of a lone sticky's unit at the top")
        m.wire("e", EW, signed=True, expr="lone ? e_lone : x_e")
    else:
        m.wire("sig_in", XW, expr=f"lone ? {XW}'d1 : x_sig")
        _exp_const(m, exp_fam, exp_pins, EW, "x_e", -XW, "e_lone", "the exponent of a lone sticky's unit")
        m.wire("e_in", EW, signed=True, expr="lone ? e_lone : x_e")
        _lzc(m, lzc_fam, lzc_pins, "sig_in", XW, "lz", "the normalizer's leading-zero count")
        lw = _clog2(XW)
        m.wire("lzs", lw, expr=f"(sig_in == 0) ? {lw}'d0 : lz[{lw-1}:0]")
        _shift(m, sh_fam, sh_pins, "sig_in", XW, "lzs", 0, "sig", "the normalizer's left shift")
        m.wire("lzx", EW, signed=True, expr=f"$signed({{{{({EW}-{lw}){{1'b0}}}}, lzs}})")
        _exp_sub(m, exp_fam, exp_pins, EW, "e_in", "lzx", "e", "the exponent lowered by the normalize count")
    # eu = e + XW - 1 is the leading one's exponent; biased = eu + bias the format's field; both enter
    # through compares against constants and one adder for the field
    EUOFF = XW - 1
    BOFF = XW - 1 + bias
    m.wire("normal", expr=f"e >= {_slit(EW, 1 - BOFF)}")                                  # biased >= 1
    shn = XW - 1 - M
    SHW = EW + 1
    # sh0 = shn + 1 - biased for a subnormal result: (shn + 1 - BOFF) - e
    m.wire("shc", SHW, signed=True, expr=_slit(SHW, shn + 1 - BOFF))
    m.wire("ex", SHW, signed=True, expr=f"$signed({{e[{EW-1}], e}})")
    _exp_sub(m, exp_fam, exp_pins, SHW, "shc", "ex", "shsub", "the subnormal result's extra right shift")
    m.wire("sht", SHW, signed=True, expr=f"normal ? {SHW}'sd{shn} : shsub")
    m.wire("sh", SHW, signed=True, expr=f"(sht > {SHW}'sd{XW+1}) ? {SHW}'sd{XW+1} : sht")
    aw = _clog2(XW + 2)
    m.wire("sha", aw, expr=f"sh[{aw-1}:0]")
    # keep = sig >> sh (XW+1 bits), rest = the dropped bits. The masks take the full amount, XW + 1 included
    # (the half position then sits at bit XW, the word's zero top bit, so nothing rounds up); the shifter takes
    # at most XW, which already clears the word, since a barrel shifter of W bits has no stage for a shift of W
    # (at the guard-round-sticky X of fp8e4m3, XW + 1 = 8, the amount 8 left the word unshifted)
    m.wire("sigw", XW + 1, expr="{1'b0, sig}")
    m.wire("shk", aw, expr=f"(sh > {SHW}'sd{XW}) ? {aw}'d{XW} : sha")
    _shift(m, sh_fam, sh_pins, "sigw", XW + 1, "shk", 1, "keep", "the right shift to the kept bits")
    _thermo(m, "restmask", XW + 1, "sha", "the mask of the dropped positions")
    m.wire("rest", XW + 1, expr="sigw & restmask")
    _onehot(m, "halfv", XW + 1, "sha", "the half position (one below the kept lsb)", offset=1)
    m.wire("keepn", XW + 1, expr=f"sigw >> {shn}")
    m.wire("restn", XW + 1, expr=f"sigw & ({{1'b0, {{{XW}{{1'b1}}}}}} >> {XW - shn})")
    m.wire("halfn", XW + 1, expr=(f"{XW+1}'d0" if shn == 0 else f"{{{XW}'d0, 1'b1}} << {shn - 1}"))
    m.wire("inexact", expr="(rest != 0) | x_st")
    # the dropped bits as a fraction word for the stochastic compare: rest below the kept lsb, aligned to
    # sb bits: (rest << sb) >> sht through the shifter (zero past the window)
    FW_ = XW + sb + 1
    m.wire("restw", FW_, expr=f"{{rest, {sb}'d0}}")
    faw = _clog2(FW_)
    m.wire("fsh", faw, expr=f"sht[{faw-1}:0]")
    _shift(m, sh_fam, sh_pins, "restw", FW_, "fsh", 1, "fint0", "the dropped bits aligned to the stochastic word")
    m.wire("fint", FW_, expr=f"(sht > {SHW}'sd{XW + sb}) ? {FW_}'d0 : fint0")
    m.wire("fintn", FW_, expr=(f"restn >> {shn - sb}" if shn >= sb else f"restn << {sb - shn}"))
    # the rounding decision, as the engine's rup
    for pre, rest_, halfv_, inex_, lsb_, fint_ in (("", "rest", "halfv", "inexact", "keep[0]", "fint"),
                                                 ("n", "restn", "halfn", "((restn != 0) | x_st)", "keepn[0]", "fintn")):
        m.wire(f"gt_half{pre}", expr=f"{rest_} > {halfv_}")
        m.wire(f"half_eq{pre}", expr=f"({rest_} == {halfv_}) && ({halfv_} != 0)")
        m.wire(f"up{pre}", expr=(f"(rnd == 3'd0) ? (gt_half{pre} || (half_eq{pre} && (x_st || {lsb_}))) : "
                                 f"(rnd == 3'd1) ? 1'b0 : (rnd == 3'd2) ? ({inex_} && s) : (rnd == 3'd3) ? ({inex_} && !s) : "
                                 f"(rnd == 3'd4) ? ({inex_} && ({srge} ? ({fint_} >= word) : ({fint_} > word))) : {inex_}"))
    m.wire("rounded", expr=f"x_sp == {ROUNDED}")
    m.wire("upr", expr="rounded ? 1'b0 : up")
    m.wire("inexact_r", expr="rounded | inexact")
    # the carry into the next binade of the value rounded at the normal precision: its kept bits all ones
    m.wire("carry_n", expr=f"upn && (&keepn[{M}:0])")
    # the increment by the rounding family
    m.wire("mag", XW + 1)
    if round_fam == "compound_adder_select":
        rinc_fam, rinc_pins = str(_pin(pins, "round.incrementer.family", "prefix_and_incrementer")), _sub(pins, "round.incrementer.")
        _incr(m, rinc_fam, rinc_pins, XW + 1, "keep", "1'b1", "k1", "", f"the kept bits plus one, in parallel with the decision ({rinc_fam})")
        m.assign("mag", "upr ? k1 : keep")
    elif round_fam == "flagged_prefix":
        cfam, cpins = str(_pin(pins, "round.compound_adder.family", "compound_flagged_prefix")), _sub(pins, "round.compound_adder.")
        m.wire("k1", XW + 1)
        m.wire("kco")
        if m.inst("adder", cfam, cpins, XW + 1, f".a(keep), .b({XW+1}'d0), .cin(1'b0), .s(), .cout(kco), .s1(k1)",
                  f"the sum and the sum plus one of the kept bits from the flagged prefix adder ({cfam})"):
            m.assign("mag", "upr ? k1 : keep")
        else:
            m.assign("mag", "keep + upr")
    elif round_fam == "injection":
        inj_fam, inj_pins = str(_pin(pins, "round.injection_adder.family", "ripple_carry")), _sub(pins, "round.injection_adder.")
        # the mode-dependent constant added below the kept lsb, then truncation; a nearest tie made even
        m.wire("ones", XW + 1, expr="restmask")
        m.wire("inj", XW + 1, expr="(rnd == 3'd0) ? halfv : (rnd == 3'd2) ? (s ? ones : 0) : (rnd == 3'd3) ? (s ? 0 : ones) : (rnd == 3'd5) ? ones : 0")
        # the sticky joins the lowest dropped bit, so a value inexact by the sticky alone rounds as one
        m.wire("sigw_i", XW + 1, expr=f"(sha != 0) ? (sigw | {{{XW}'d0, x_st}}) : sigw")
        m.wire("sum_i", XW + 1)
        m.wire("sum_ico")
        _adder(m, inj_fam, inj_pins, XW + 1, "sigw_i", "inj", "sum_i", f"the injection added ({inj_fam})", cout="sum_ico", declare=False)
        m.wire("sum_iw", XW + 2, expr="{sum_ico, sum_i}")
        _shift(m, sh_fam, sh_pins, "sum_iw", XW + 2, "sha", 1, "magiw", "the injected sum shifted to the kept bits")
        m.wire("magi", XW + 1, expr=f"magiw[{XW}:0]")
        m.wire("tie", expr="(rnd == 3'd0) && half_eq && !x_st")
        m.wire("magt", XW + 1, expr="tie ? {magi[XW:1], 1'b0}".replace("XW", str(XW)) + " : magi")
        # the stochastic mode keeps the decision path: the increment through the adder with the decision
        m.wire("uprw", XW + 1, expr=f"{{{XW}'d0, upr}}")
        m.wire("mags", XW + 1)
        _adder(m, inj_fam, inj_pins, XW + 1, "keep", "uprw", "mags", f"the stochastic mode's increment ({inj_fam})", declare=False)
        m.assign("mag", "rounded ? keep : (rnd == 3'd4 || sha == 0) ? mags : magt")
    else:
        rinc_fam, rinc_pins = str(_pin(pins, "round.incrementer.family", "prefix_and_incrementer")), _sub(pins, "round.incrementer.")
        _incr(m, rinc_fam, rinc_pins, XW + 1, "keep", "upr", "mag0", "", f"the rounding increment ({rinc_fam})")
        m.assign("mag", "mag0")
    # the exponent field: e + (XW - 1 + bias) for a normal result, incremented when the increment carried
    # into the next binade; a subnormal result's field is zero and the significand is the mantissa itself
    _exp_const(m, exp_fam, exp_pins, EW, "e", BOFF, "bfield", "the biased exponent field")
    m.wire("bfu", EW, expr="bfield")
    _incr(m, inc_fam, inc_pins, EW, "bfu", f"mag[{M+1}]", "efield", "", f"the exponent field incremented on a rounding carry ({inc_fam})")
    CW = max(W + EW + 1, XW + 2)
    m.wire("code", CW, expr=f"normal ? {{{{({CW}-{EW}-{M}){{1'b0}}}}, efield, mag[{M-1}:0]}} : {{{{({CW}-{XW+1}){{1'b0}}}}, mag}}"
           if M > 0 else f"normal ? {{{{({CW}-{EW}){{1'b0}}}}, efield}} : {{{{({CW}-{XW+1}){{1'b0}}}}, mag}}")
    emin = 1 - bias
    if tin_before == "1":
        m.wire("tiny", expr=f"e < {_slit(EW, emin - EUOFF)}")
    else:
        m.wire("tiny", expr=f"(e < {_slit(EW, emin - EUOFF)}) && !(e == {_slit(EW, emin - 1 - EUOFF)} && carry_n) && !(e == {_slit(EW, -bias - EUOFF)} && carry_n)")
    m.wire("ovf", expr=f"code > {CW}'d{maxf}")
    m.wire("to_inf", expr=f"{1 if c.has_inf else 0} && (rnd == 3'd0 || (rnd == 3'd3 && !s) || (rnd == 3'd2 && s) || rnd == 3'd5 || (rnd == 3'd4 && (e > {_slit(EW, top - bias - EUOFF)} || up)))")
    out_inf = f"{{s, {MW}'d{inf_bits}}}" if signed else f"{MW}'d{inf_bits}"
    out_max = f"{{s, {MW}'d{maxf}}}" if signed else f"{MW}'d{maxf}"
    out_zero = f"{{s, {MW}'d0}}" if signed else f"{MW}'d0"
    out_code = f"{{s, code[{MW-1}:0]}}" if signed else f"code[{MW-1}:0]"
    F_NAN, F_INEX, F_OVF, F_UNF = flag_bit("nan"), flag_bit("inexact"), flag_bit("overflow"), flag_bit("underflow")
    subnz = f"code[{M-1}:0] != 0" if M > 0 else "1'b0"
    m.wire("ftz_hit", expr=f"ftz && code[{MW-1}:{M}] == 0 && ({subnz})")
    m.wire("is_zero", expr="(x_sig == 0) && (!x_st || rounded)")
    m.wire("tiny_r", expr="rounded ? x_st : tiny")
    inexact_expression = "inexact_r"
    finite_bits = f"ovf ? (to_inf ? {out_inf} : {out_max}) : (ftz_hit ? {out_zero} : {out_code})"
    if c.has_inf and not c.has_nan:
        from chialu.targets.rtl.families.fp_hole import correction
        gap, gap_bits = correction(m, c, g, srge, CW)
        inexact_expression = f"(inexact_r || {gap})"
        finite_bits = f"ovf ? (to_inf ? {out_inf} : {out_max}) : {gap} ? {gap_bits} : (ftz_hit ? {out_zero} : {out_code})"
    m.wire("fl_fin", FW, expr=(f"ovf ? ((1 << {F_OVF}) | (1 << {F_INEX})) : "
                                f"(({inexact_expression} ? (1 << {F_INEX}) : 0) | ((tiny_r && inexact_r) ? (1 << {F_UNF}) : 0) | (ftz_hit ? ((1 << {F_INEX}) | (1 << {F_UNF})) : 0))"))
    m.wire("bits_fin", W, expr=finite_bits)
    m.wire("fl_zero", FW, expr=f"rounded ? ((1 << {F_INEX}) | (1 << {F_UNF})) : {FW}'d0")
    if c.has_inf:
        inf_fl, inf_bits_o = "0", out_inf
    else:
        inf_fl, inf_bits_o = f"((1 << {F_INEX}) | (1 << {F_OVF}))", out_inf
    m.assign("fl", f"(x_sp == 2'd1) ? (1 << {F_NAN}) : (x_sp == 2'd2) ? {inf_fl} : is_zero ? fl_zero : fl_fin")
    exact_zero = f"(rounded ? {out_zero} : {W}'d0)" if tokens.get("ZERO_POSITIVE", "1") == "1" else out_zero
    m.assign("bits", f"(x_sp == 2'd1) ? {W}'d{nan_bits} : (x_sp == 2'd2) ? {inf_bits_o} : is_zero ? {exact_zero} : bits_fin")
    return name, m.render()


# ---- the divider and the square root --------------------------------------------------
def round_int_sv(c, g: Geom, family: str, pins: dict, tokens: dict, name: str | None = None) -> tuple:
    """Normalize, align and round X to an integer, fixed or decimal target."""
    if family != "shift_round_convert":
        raise ValueError(f"integer conversion requires shift_round_convert, got {family!r}")
    XW, EW, XT, sb = g.XW, g.EW, g.XT, g.sr_bits
    W, F = c.width, getattr(c, "frac_bits", 0)
    TW, SW = XW + W + 3, EW + 1
    name = name or f"fam_int_round_{c.name}_{g.tag()}{_tag(pins)}"
    m = Mod(name, f"{family}: X to {c.name}, selected normalizer, shifters and rounding datapath")
    for direction, port, width in (("input", "x", XT), ("input", "rnd", 3), ("input", "word", sb),
                                   ("input", "ftz", 1), ("output", "fl", FW), ("output", "bits", W)):
        m.port(direction, port, width)
    _x_fields(m, "x", g, "x_")
    lf, lp = str(_pin(pins, "lzc.family", "lzd_cell_tree")), _sub(pins, "lzc.")
    sf, sp = str(_pin(pins, "shifter.family", "barrel_mux_tree")), _sub(pins, "shifter.")
    ef, ep = str(_pin(pins, "exp_adder.family", "ripple_carry")), _sub(pins, "exp_adder.")
    xf, xp = str(_pin(pins, "exp_incrementer.family", "prefix_and_incrementer")), _sub(pins, "exp_incrementer.")
    rf = str(_pin(pins, "round.family", "increment_adder"))
    m.wire("lone", expr="x_sig == 0 && x_st")
    m.wire("sig_in", XW, expr=f"lone ? {XW}'d1 : x_sig")
    _lzc(m, lf, lp, "sig_in", XW, "lz", "normalize the source significand")
    lw = _clog2(XW)
    m.wire("lzs", lw, expr=f"sig_in == 0 ? {lw}'d0 : lz[{lw-1}:0]")
    _shift(m, sf, sp, "sig_in", XW, "lzs", 0, "sig", "place the leading one at the normalizer output")
    m.wire("xe", SW, signed=True, expr=f"{{x_e[{EW-1}], x_e}}")
    m.wire("lzx", SW, expr=f"{{{{{SW-lw}{{1'b0}}}}, lzs}}")
    _exp_sub(m, ef, ep, SW, "xe", "lzx", "enorm", "normalization exponent adjustment")
    m.wire("offset", SW, signed=True, expr=f"lone ? {_slit(SW, F-XW)} : {_slit(SW, F)}")
    _exp_add(m, ef, ep, SW, "enorm", "offset", "pe", "target fractional-bit scale")
    m.wire("pen", SW, expr="~pe")
    _incr(m, xf, xp, SW, "pen", "1'b1", "negpe", "", "two's-complement right-shift distance")
    aw = _clog2(TW)
    m.wire("right", expr=f"pe[{SW-1}]")
    m.wire("distance", SW, expr="right ? negpe : pe")
    m.wire("amount", aw, expr=f"distance >= {SW}'d{TW} ? {aw}'d{TW-1} : distance[{aw-1}:0]")
    m.wire("sigw", TW, expr=f"{{{{{TW-XW}{{1'b0}}}}, sig}}")
    _shift(m, sf, sp, "sigw", TW, "amount", "{2'd0, right}", "aligned", "align to the target's fixed least-significant bit", allowed_ops=(0, 1))
    m.wire("keep", TW, expr=f"right && distance >= {SW}'d{TW} ? {TW}'d0 : aligned")
    m.wire("big", expr=f"!right && distance > {SW}'d{W+2}")
    _thermo(m, "restmask0", TW, "amount", "positions discarded by the right shift")
    m.wire("restmask", TW, expr=f"!right ? {TW}'d0 : distance >= {SW}'d{TW} ? {{{TW}{{1'b1}}}} : restmask0")
    m.wire("rest", TW, expr="sigw & restmask")
    _onehot(m, "half0", TW, "amount", "half of the target least-significant bit", offset=1)
    m.wire("halfv", TW, expr=f"!right ? {TW}'d0 : distance >= {SW}'d{TW} ? ({TW}'d1 << {TW-1}) : half0")
    fw = TW + sb
    m.wire("restw", fw, expr=f"{{rest, {sb}'d0}}")
    faw = _clog2(fw)
    m.wire("famt", faw, expr=f"distance >= {SW}'d{fw} ? {faw}'d{fw-1} : distance[{faw-1}:0]")
    _shift(m, sf, sp, "restw", fw, "famt", 1, "fint0", "align discarded bits with the stochastic word")
    m.wire("fint", fw, expr=f"!right || distance >= {SW}'d{fw} ? {fw}'d0 : fint0")
    m.wire("inexact", expr="rest != 0 || x_st")
    m.wire("tie", expr="rest == halfv && halfv != 0")
    srge = tokens.get("SRGE", "0")
    m.wire("up", expr=f"rnd == 0 ? (rest > halfv || (tie && (x_st || keep[0]))) : rnd == 1 ? 1'b0 : "
                      f"rnd == 2 ? (inexact && x_s) : rnd == 3 ? (inexact && !x_s) : "
                      f"rnd == 4 ? (inexact && ({srge} ? fint >= word : fint > word)) : inexact")
    if rf in ("increment_adder", "compound_adder_select"):
        af, ap = str(_pin(pins, "round.incrementer.family", "prefix_and_incrementer")), _sub(pins, "round.incrementer.")
        _incr(m, af, ap, TW, "keep", "up" if rf == "increment_adder" else "1'b1", "incremented", "", "rounding increment")
        m.wire("mag", TW, expr="incremented" if rf == "increment_adder" else "up ? incremented : keep")
    elif rf == "flagged_prefix":
        af, ap = str(_pin(pins, "round.compound_adder.family", "compound_flagged_prefix")), _sub(pins, "round.compound_adder.")
        m.wire("incremented", TW)
        m.inst("adder", af, ap, TW, f".a(keep), .b({TW}'d0), .cin(1'b0), .s(), .cout(), .s1(incremented)", "parallel rounded candidate")
        m.wire("mag", TW, expr="up ? incremented : keep")
    elif rf == "injection":
        af, ap = str(_pin(pins, "round.injection_adder.family", "ripple_carry")), _sub(pins, "round.injection_adder.")
        m.wire("inject", TW, expr="rnd == 0 ? halfv : (rnd == 2 && x_s) || (rnd == 3 && !x_s) || rnd == 5 ? restmask : 0")
        m.wire("sig_st", TW, expr="sigw | (right && x_st ? 1 : 0)")
        _adder(m, af, ap, TW, "sig_st", "inject", "injected", "injection below the target least-significant bit")
        _shift(m, sf, sp, "injected", TW, "amount", 1, "truncated", "discard the injected rounding positions")
        m.wire("upw", TW, expr=f"{{{TW-1}'d0, up}}")
        _adder(m, af, ap, TW, "keep", "upw", "stochastic", "stochastic rounding and nonfractional sticky increment")
        m.wire("nearest", TW, expr=f"rnd == 0 && tie && !x_st ? {{truncated[{TW-1}:1], 1'b0}} : truncated")
        m.wire("mag", TW, expr=f"!right || rnd == 4 || distance >= {SW}'d{TW} ? stochastic : nearest")
    else:
        raise ValueError(f"unknown integer rounding family {rf!r}")
    mx, mn = c.max_int, c.min_int
    m.wire("negative", expr="x_s && (mag != 0 || big)")
    m.wire("overflow", expr=f"big || (negative ? mag > {TW}'d{abs(mn)} : mag > {TW}'d{mx})")
    m.wire("finite", TW, expr=f"overflow ? (negative ? {TW}'d{abs(mn)} : {TW}'d{mx}) : mag")
    ni = int(tokens.get("NANTOINT", 0))
    nanval, nanneg = (mx, 0) if ni == 1 else (abs(mn), int(mn < 0)) if ni == 2 else (0, 0)
    m.wire("t", TW, expr=f"x_sp == 1 ? {TW}'d{nanval} : x_sp == 2 ? (x_s ? {TW}'d{abs(mn)} : {TW}'d{mx}) : finite")
    m.wire("neg", expr=f"x_sp == 1 ? 1'b{nanneg} : x_sp == 2 ? x_s : negative")
    if c.encoding == "bcd":
        m.raw(f"  always_comb begin\n    automatic logic [{TW-1}:0] value = t;\n    for (int i=0; i<{c.digits}; i=i+1) begin bits[4*i +: 4] = value % 10; value = value / 10; end\n  end")
    elif c.encoding == "unsigned":
        m.assign("bits", f"neg ? {W}'d0 : t[{W-1}:0]")
    elif c.encoding == "twos_complement":
        m.assign("bits", f"neg ? (~t[{W-1}:0] + 1'b1) : t[{W-1}:0]")
    elif c.encoding == "ones_complement":
        m.assign("bits", f"neg ? ~t[{W-1}:0] : t[{W-1}:0]")
    else:
        m.assign("bits", f"{{neg, t[{W-2}:0]}}")
    fi, fo, fn = flag_bit("invalid"), flag_bit("overflow"), flag_bit("inexact")
    m.assign("fl", f"x_sp != 0 ? (1 << {fi}) : overflow ? ((1 << {fi}) | (1 << {fo}) | (1 << {fn})) : inexact ? (1 << {fn}) : 0")
    return name, m.render()

def _norm_x(m: Mod, pins: dict, g: Geom, pre: str):
    """{pre}sn, {pre}en: the significand normalized (its leading one at bit
    XW-1) and the exponent lowered by the count, through the norm_lzc,
    norm_shifter and exp_adder slots; a zero significand leaves the
    special-case path to its own result."""
    XW, EW = g.XW, g.EW
    nw = XW.bit_length()
    aw = _clog2(XW)
    exp_fam, exp_pins = str(_pin(pins, "exp_adder.family", "ripple_carry")), _sub(pins, "exp_adder.")
    _lzc(m, str(_pin(pins, "norm_lzc.family", "lzd_cell_tree")), _sub(pins, "norm_lzc."), f"{pre}sig", XW, f"{pre}lz",
         f"operand {pre[0]}: the significand's leading zeros")
    m.wire(f"{pre}lzs", aw, expr=f"{pre}lz[{aw-1}:0]")
    _shift(m, str(_pin(pins, "norm_shifter.family", "barrel_mux_tree")), _sub(pins, "norm_shifter."), f"{pre}sig", XW, f"{pre}lzs", 0,
           f"{pre}sn", f"operand {pre[0]}: the significand normalized")
    m.wire(f"{pre}lzx", EW, signed=True, expr=f"$signed({{{{({EW}-{nw}){{1'b0}}}}, {pre}lz}})")
    _exp_sub(m, exp_fam, exp_pins, EW, f"{pre}e", f"{pre}lzx", f"{pre}en", f"operand {pre[0]}: the exponent lowered by the count")


def div_sv(g: Geom, family: str, pins: dict, name: str | None = None) -> tuple:
    """(name, text): xa / xb -> X as the engine divides: both significands
    normalized, the quotient (a << XW) / b of XW+1 bits from the library
    divider of the sig_div component's family (an XW-bit dividend with
    the implied shift XW, a normalized XW-bit divisor), its top bit
    dropped into the sticky when it carries, the sticky from the
    remainder and the operands' sticky bits, the exponent the difference
    less XW through the exp_adder slot; NaN, infinity and zero operands
    as the engine."""
    pins = pins or {}
    XW, EW, XT = g.XW, g.EW, g.XT
    dfam = str(_pin(pins, "sig_div.family", "restoring_nonrestoring"))
    dpins = _sub(pins, "sig_div.")
    exp_fam, exp_pins = str(_pin(pins, "exp_adder.family", "ripple_carry")), _sub(pins, "exp_adder.")
    name = name or f"fam_fp_div_{family}_{dfam}_{g.tag()}{_tag(pins)}"
    from chialu.targets.rtl.families import div as DIV
    dname, dtext = DIV.div_sv(XW, XW, XW + 1, dfam, dpins, name=f"{name}_sig", S=XW, normalized=True)
    m = Mod(name, f"fp significand divider ({family}): the operands normalized, the {XW+1}-bit quotient from the {dfam} "
                  f"divider over the significands, the sticky from the remainder, the exponents through {exp_fam} adders")
    m.port("input", "xa", XT)
    m.port("input", "xb", XT)
    m.port("output", "y", XT)
    _x_fields(m, "xa", g, "a_")
    _x_fields(m, "xb", g, "b_")
    _norm_x(m, pins, g, "a_")
    _norm_x(m, pins, g, "b_")
    m.wire("q", XW + 1)
    m.wire("r", XW)
    m.extra.append(dtext)
    m.raw(f"  // structure sig_div: family {dfam} realized by the library divider {dname}")
    m.raw(f"  {dname} u_div (.a(a_sn), .b(b_sn), .q(q), .r(r));")
    m.wire("s", expr="a_s ^ b_s")
    m.wire("rnz", expr="r != 0")
    _exp_sub(m, exp_fam, exp_pins, EW, "a_en", "b_en", "ed", "the exponent difference")
    _exp_const(m, exp_fam, exp_pins, EW, "ed", -(XW - 1), "e_hi", "the quotient's exponent when its top bit carries")
    _exp_const(m, exp_fam, exp_pins, EW, "ed", -XW, "e_lo", "the quotient's exponent")
    m.wire("y_fin", XT, expr=f"q[{XW}] ? {_mkx(g, chr(50) + chr(39) + 'd0', 's', 'e_hi', f'q[{XW}:1]', 'rnz | q[0] | a_st | b_st')} : "
                              f"{_mkx(g, chr(50) + chr(39) + 'd0', 's', 'e_lo', f'q[{XW-1}:0]', 'rnz | a_st | b_st')}")
    nan_x = _mkx_special(g, "2'd1")
    inf_s = _mkx_special(g, "2'd2", "s")
    zero_s = _mkx_special(g, "2'd0", "s")
    m.wire("y_sp", XT, expr=(f"(a_sp == 2'd1 || b_sp == 2'd1) ? {nan_x} : "
                              f"(a_sp == 2'd2 && b_sp == 2'd2) ? {nan_x} : "
                              f"(a_sp == 2'd2) ? {inf_s} : (b_sp == 2'd2) ? {zero_s} : "
                              f"b_z ? (a_z ? {nan_x} : {inf_s}) : a_z ? {zero_s} : y_fin"))
    m.assign("y", "y_sp")
    return name, m.render()


def sqrt_sv(g: Geom, family: str, pins: dict, name: str | None = None) -> tuple:
    """(name, text): sqrt(xa) -> X as the engine does: the significand
    normalized, the exponent made even (the significand doubled when it
    is odd), the radicand m 2^(2K) with K = (XW+1)/2 to the library
    square root of the sig_sqrt component's family (XW+1 root bits; a
    functional family takes the radicand at an even width, so an odd
    XW+1 shifts it by two and halves the root), the sticky from the
    remainder and the dropped root bit, the exponent through the
    exp_adder slot; NaN, infinity, zero and negative operands as the
    engine."""
    pins = pins or {}
    XW, EW, XT = g.XW, g.EW, g.XT
    sfam = str(_pin(pins, "sig_sqrt.family", "digit_recurrence_sqrt_combined"))
    spins = _sub(pins, "sig_sqrt.")
    exp_fam, exp_pins = str(_pin(pins, "exp_adder.family", "ripple_carry")), _sub(pins, "exp_adder.")
    name = name or f"fam_fp_sqrt_{family}_{sfam}_{g.tag()}{_tag(pins)}"
    from chialu.targets.rtl.families import div as DIV
    Q = XW + 1
    K = Q // 2
    functional = sfam in DIV.FUNCTIONAL
    Qs = Q + 1 if (functional and Q % 2 == 1) else Q
    sname, stext = DIV.sqrt_sv(Qs, sfam, spins, name=f"{name}_sig", normalized=functional)
    m = Mod(name, f"fp square root ({family}): the operand normalized and its exponent made even, the {Q}-bit root from "
                  f"the {sfam} square root over the radicand, the sticky from the remainder, the exponent through {exp_fam} adders")
    m.port("input", "xa", XT)
    m.port("output", "y", XT)
    _x_fields(m, "xa", g, "a_")
    _norm_x(m, pins, g, "a_")
    m.wire("eodd", expr="a_en[0]")
    m.wire("mm", XW + 1, expr="eodd ? {a_sn, 1'b0} : {1'b0, a_sn}")
    _exp_const(m, exp_fam, exp_pins, EW, "a_en", -1, "eem", "the exponent made even")
    m.wire("ee", EW, signed=True, expr="eodd ? eem : a_en")
    m.wire("rad", 2 * Q, expr=f"{{{{({2*Q}-{XW+1}){{1'b0}}}}, mm}} << {2 * K}")
    m.wire("root_s", Qs)
    m.wire("rem_s", Qs + 2)
    m.extra.append(stext)
    m.raw(f"  // structure sig_sqrt: family {sfam} realized by the library square root {sname}")
    if Qs != Q:
        # an odd root width leaves the radicand's leading one two or three bits below the top of the wider
        # word: the odd exponent's radicand shifts by two, the even one's by four, so the leading one lands
        # in the top two bits; the root halves (or quarters) back, exact since the shifts are even
        m.wire("rad_s", 2 * Qs, expr=f"eodd ? {{rad, 2'b00}} : {{rad[{2*Q-3}:0], 4'b0000}}")
        m.raw(f"  {sname} u_sqrt (.x(rad_s), .root(root_s), .rem(rem_s));")
        m.wire("root", Q, expr=f"eodd ? root_s[{Qs-1}:1] : root_s[{Qs-1}:2]")
        m.wire("st_rem", expr="(rem_s != 0) | (eodd ? root_s[0] : (root_s[1:0] != 2'b00))")
    else:
        m.raw(f"  {sname} u_sqrt (.x(rad), .root(root_s), .rem(rem_s));")
        m.wire("root", Q, expr="root_s")
        m.wire("st_rem", expr="rem_s != 0")
    m.wire("eh", EW, signed=True, expr="ee >>> 1")
    _exp_const(m, exp_fam, exp_pins, EW, "eh", -(K - 1), "er", "the root's exponent")
    m.wire("y_fin", XT, expr=_mkx(g, "2'd0", "1'b0", "er", f"root[{XW}:1]", "st_rem | root[0] | a_st"))
    nan_x = _mkx_special(g, "2'd1")
    m.wire("y_sp", XT, expr=(f"(a_sp == 2'd1) ? {nan_x} : (a_sp == 2'd2) ? (a_s ? {nan_x} : xa) : "
                              f"a_z ? xa : a_s ? {nan_x} : y_fin"))
    m.assign("y", "y_sp")
    return name, m.render()
