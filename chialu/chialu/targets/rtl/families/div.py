"""Divider families as combinational arrays.

Every divider module computes q = floor(a 2^S / b) and r = a 2^S mod b
for an N-bit dividend a, a D-bit divisor b, a Q-bit quotient and a
D-bit remainder (S is the dividend's implied left shift, XW for a float
significand quotient), exact for b != 0 and a 2^S / b < 2^Q:

    module fam_div_<family>_n<N>[s<S>]d<D>q<Q>[_p<pins>] (input [N-1:0] a, input [D-1:0] b, output [Q-1:0] q, output [D-1:0] r);

Every component of a library kind is an instance the family's slots
choose: the divisor normalization's counter and shifter (`norm_lzc`,
`norm_shifter`, the shifter also scaling the dividend and de-scaling
the remainder), the recurrences' adders (`residual_adder`: the trial
subtractions, the assimilations, the divisor's non-shift multiples,
the speculated candidate residuals, the conversions and corrections),
the functional families' multipliers (`iter_mult`, `final_mul`,
`prescaler`) and adders (`iter_add`; direct_polynomial's refinement
step through its polynomial's `sum_adder`), the seed tables'
multipliers (`seed.mul`) and adders (`seed.sum_adder`), the final
rounding's correction adder (`final_round.correction_adder`), the
comparator selection's subtractors (`digit_select.comparator_adder`).
A quotient digit comes from a generated selection table (qds_table,
checked for containment over every cell at generation, emitted as a
case ROM in a module of its own in the digit encoding chosen, folded
on the estimate's sign when asked) or from comparators against its
thresholds. The multiplier slots' default family `behavioral_star` is
the library's module of that name (the language's multiply as a
module); every constant table is a `tab_*` module shared by content.

The digit recurrences (restoring_nonrestoring, srt_radix2,
srt_high_radix as radix-4 and radix-2 sub-stages cascaded or
overlapped, the shared recurrence digit_recurrence_sqrt_combined,
online_msdf) are shift-and-subtract arrays; the functional families
(newton_raphson, goldschmidt, direct_polynomial,
prescaled_very_high_radix, svoboda_tung) refine a reciprocal seed from
a seed table family (each with its error bound evaluated at generation
to size the seed or the iteration count), form the quotient estimate
and correct it by the back-multiplied remainder (final_round
back_multiply_remainder), or carry enough precision that the
estimate rounded at half a quotient step (exclusion_zone_proof) or
biased above the quotient by its error bound and truncated
(extra_precision_quotient) is exact. fam_sqrt_* takes a 2Q-bit radicand to a Q-bit root
by the restoring recurrence, the SRT recurrence in the halved residual
form (its tables generated and checked per stage index), or the
functional rsqrt iteration. The module name carries a tag of the pins
(`_tag`), so two pin sets never share a name.

    python3 -m chialu.targets.rtl.families.div --width 16 --family srt_high_radix --pins radix=4
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from fractions import Fraction

DIV_FAMILIES = ("restoring_nonrestoring", "srt_radix2", "srt_high_radix", "prescaled_very_high_radix", "svoboda_tung",
                "newton_raphson", "goldschmidt", "direct_polynomial", "digit_recurrence_sqrt_combined", "online_msdf")
FUNCTIONAL = ("newton_raphson", "goldschmidt", "direct_polynomial", "prescaled_very_high_radix", "svoboda_tung")
SEED_FAMILIES = ("monolithic_rom", "bipartite_rom", "symmetric_bipartite", "multipartite", "operand_modification_multiply",
                 "poly_seed", "magic_constant_bit_seed")
SPECULATION_CAP = 32          # the most speculative selections one overlapped window builds


def _pin(pins: dict, key: str, default):
    v = pins.get(key, default) if pins else default
    return default if v in (None, "") else v


def _ipin(pins: dict, key: str, default: int) -> int:
    try:
        return int(_pin(pins, key, default))
    except (TypeError, ValueError):
        return default


def _bpin(pins: dict, key: str, default: bool) -> bool:
    v = _pin(pins, key, default)
    return v in (True, "True", "true", 1, "1")


def _sub_pins(pins: dict, prefix: str) -> dict:
    return {k[len(prefix):]: v for k, v in (pins or {}).items() if k.startswith(prefix)}


def _tag(pins: dict) -> str:
    """A tag of a pins dictionary for a module name (empty for none): 48
    bits of the hash of the sorted keys and values, so the tens of
    thousands of pin sets a sweep renders keep distinct names."""
    d = {k: v for k, v in (pins or {}).items() if not str(k).startswith("_")}
    if not d:
        return ""
    return "_p" + hashlib.sha1(json.dumps(d, sort_keys=True, default=str).encode()).hexdigest()[:12]


def _clog2(n: int) -> int:
    return max(1, (n - 1).bit_length())


def _slit(width: int, value: int) -> str:
    return f"-{width}'sd{-value}" if value < 0 else f"{width}'sd{value}"


def _zext(x: str, xw: int, W: int) -> str:
    return x if xw == W else f"{{{{({W}-{xw}){{1'b0}}}}, {x}}}"


class Mod:
    """A module under construction: ports, declarations, body lines,
    the texts of the library modules it instantiates."""

    def __init__(self, name: str, comment: str):
        self.name, self.comment = name, comment
        self.ports: list = []
        self.lines: list = []
        self.extra: list = []
        self.n = 0
        self.k = 0

    def tmp(self, base: str) -> str:
        self.k += 1
        return f"{base}_{self.k}"

    def port(self, direction: str, name: str, width: int = 1, signed: bool = False):
        w = f"[{width-1}:0] " if width > 1 else ""
        self.ports.append(f"{direction} logic {'signed ' if signed else ''}{w}{name}")

    def wire(self, name: str, width: int = 1, signed: bool = False, expr: str | None = None):
        w = f"[{width-1}:0] " if width > 1 else ""
        self.lines.append(f"  logic {'signed ' if signed else ''}{w}{name};" + (f" assign {name} = {expr};" if expr is not None else ""))
        return name

    def assign(self, lhs: str, expr: str):
        self.lines.append(f"  assign {lhs} = {expr};")

    def raw(self, text: str):
        self.lines.append(text)

    def inst(self, m, conns: str, comment: str):
        if m.text:
            self.extra.append(m.text)
        ps = ", ".join(f".{k}({v})" for k, v in m.params.items())
        self.n += 1
        self.lines.append(f"  // {comment}")
        self.lines.append(f"  {m.name} " + (f"#({ps}) " if ps else "") + f"u{self.n} ({conns});")

    def lib(self, kind: str, family: str, pins: dict, width: int, conns: str, comment: str, signed: bool = False) -> bool:
        """Instantiate the selected component or reject it explicitly."""
        from chialu.targets.rtl import families as FAM
        m = None
        if kind == "adder":
            from .binary_cpa import adder_module
            m = adder_module(family, pins, width)
        elif kind == "mul":
            m = FAM.mul_module(family, pins, width, signed)
        elif kind == "lzc":
            m = FAM.lzc_module(family, pins, width)
        elif kind == "cmp":
            m = FAM.comparator_module(family, pins, width, False)
        if m is None:
            raise ValueError(f'divider {kind} component {family!r} rejected width {width} and pins {pins!r}')
        self.inst(m, conns, comment)
        return True

    # ---- the slot-chosen components ------------------------------------------------------
    def add(self, fam, pins: dict, W: int, a: str, b: str, cin: str, s: str, cout: str, comment: str) -> None:
        """Ordinary binary sum/carry through the selected adder contract."""
        from .binary_cpa import adder_module
        family = 'ripple_carry' if fam is None else str(fam)
        m = adder_module(family, {} if pins is None else pins, W)
        if m is None:
            raise ValueError(f'divider adder component {family!r} rejected width {W} and pins {pins!r}')
        self.inst(m, f".a({a}), .b({b}), .cin({cin}), .s({s}), .cout({cout})", comment)

    def sub(self, fam, pins: dict, W: int, a: str, b: str, s: str, ge: str, comment: str) -> None:
        """s = a - b (W bits) and ge = a >= b (the carry-out of a + ~b + 1)."""
        nb = self.wire(self.tmp("nb"), W, expr=f"~({b})")
        self.add(fam, pins, W, a, nb, "1'b1", s, ge, comment)

    def sh(self, fam, pins: dict, src: str, W: int, amt: str, right: bool, out: str, comment: str) -> str:
        """out (W bits) = src shifted by amt (its width clog2(W)) through the
        shifter family; a constant amount is a constant shift."""
        from chialu.targets.rtl import families as FAM
        self.wire(out, W)
        if W < 2:
            self.assign(out, src)
            return out
        f = 'barrel_mux_tree' if fam is None else str(fam)
        m = FAM.shifter_module(f, {} if pins is None else pins, W)
        if m is None:
            raise ValueError(f'divider shifter component {f!r} rejected width {W} and pins {pins!r}')
        self.inst(m, f".a({src}), .amt({amt}), .op(3'd{1 if right else 0}), .y({out}), .sticky()", comment)
        return out

    def lz(self, fam, pins: dict, src: str, W: int, out: str, comment: str) -> str:
        """out (clog2(W+1) bits) = the leading zeros of src through the counter family."""
        from chialu.targets.rtl import families as FAM
        self.wire(out, W.bit_length())
        family = 'lzd_cell_tree' if fam is None else str(fam)
        m = FAM.lzc_module(family, {} if pins is None else pins, W)
        if m is None:
            raise ValueError(f'divider lzc component {family!r} rejected width {W} and pins {pins!r}')
        self.inst(m, f".a({src}), .n({out})", comment)
        return out

    def umul(self, fam, pins: dict, x: str, xw: int, y: str, yw: int, out: str, comment: str, signed: bool = False) -> str:
        """out (xw + yw bits) = x * y through the library multiplier of the
        slot's family at the common width (the narrower operand extended);
        the slot's default behavioral_star is the language's multiply as a
        module."""
        from chialu.targets.rtl import families as FAM
        W = max(xw, yw)
        f = str(fam or "behavioral_star")
        if f == "twin_precision_subword":
            # the subword multiplier serving the one full-width mode
            m = FAM.twin_precision_module([W], [signed], pins or {}, W)
        else:
            m = FAM.mul_module(f, pins or {}, W, signed)
        if m is None:
            raise ValueError(f"the multiplier family {f!r} has no component module at {W} bits")
        if f == "twin_precision_subword":
            self.wire(f"{out}_full", 2 * W, signed=signed)
            xe = x if xw == W else (f"{{{{({W}-{xw}){{{x}[{xw-1}]}}}}, {x}}}" if signed else _zext(x, xw, W))
            ye = y if yw == W else (f"{{{{({W}-{yw}){{{y}[{yw-1}]}}}}, {y}}}" if signed else _zext(y, yw, W))
            self.inst(m, f".a({xe}), .b({ye}), .sel(1'b0), .p({out}_full)", comment)
            self.wire(out, xw + yw, signed=signed, expr=f"{out}_full[{xw+yw-1}:0]")
            return out
        self.wire(f"{out}_full", 2 * W, signed=signed)
        if signed:
            xe = x if xw == W else f"{{{{({W}-{xw}){{{x}[{xw-1}]}}}}, {x}}}"
            ye = y if yw == W else f"{{{{({W}-{yw}){{{y}[{yw-1}]}}}}, {y}}}"
        else:
            xe, ye = _zext(x, xw, W), _zext(y, yw, W)
        self.inst(m, f".a({xe}), .b({ye}), .p({out}_full)", comment)
        self.wire(out, xw + yw, signed=signed, expr=f"{out}_full[{xw+yw-1}:0]")
        return out

    def rom(self, name: str, entries, ew: int, index: str, out: str, comment: str, signed: bool = False,
            default: str | None = None, kbits: int | None = None):
        """out (ew bits) = the constant table entry at index, the table a
        case statement in a module of its own (one module per distinct
        content, shared by every reader). `entries` is a list (entry 0 at
        index 0) or a {index: value} dict; an index outside the entries
        reads `default` (an expression over the module's key `k`, else
        zero)."""
        items = list(enumerate(entries)) if isinstance(entries, list) else sorted(entries.items())
        n = (max(k for k, _v in items) + 1) if items else 1
        KB = kbits or max(1, (n - 1).bit_length())
        mask = (1 << ew) - 1
        dflt = default or f"{ew}'d0"
        body = "\n".join(f"      {KB}'d{k}: v = {ew}'d{v & mask};" for k, v in items)
        key = hashlib.sha1(f"{KB}|{ew}|{dflt}|{body}".encode()).hexdigest()[:10]
        mod = f"tab_{key}"
        self.extra.append(f"// a constant table of {len(items)} entries of {ew} bits over a {KB}-bit key\n"
                          f"module {mod} (input logic [{KB-1}:0] k, output logic [{ew-1}:0] v);\n"
                          f"  always_comb begin\n    case (k)\n{body}\n      default: v = {dflt};\n    endcase\n  end\n"
                          f"endmodule\n")
        self.wire(out, ew, signed=signed)
        self.n += 1
        self.lines.append(f"  // {comment} ({name})")
        self.lines.append(f"  {mod} u{self.n} (.k({index}), .v({out}));")

    def render(self) -> str:
        from chialu.targets.rtl.families.mul import dedupe_modules
        head = [f"// {self.comment}", f"module {self.name} (", ",\n".join("  " + p for p in self.ports), ");"]
        return "\n".join(head + self.lines + ["endmodule", ""]) + dedupe_modules("".join(self.extra))


# ---- shared pieces --------------------------------------------------------------------
def _dividend(m: Mod, N: int, S: int) -> tuple:
    """(name, width) of the dividend with its implied shift applied."""
    if S == 0:
        return "a", N
    m.wire("ax", N + S, expr=f"{{a, {S}'d0}}")
    return "ax", N + S


class Norm:
    """The normalization slots of a family: the counter and the shifter
    (norm_lzc, norm_shifter), the shifter also scaling the dividend and
    de-scaling the remainder."""

    def __init__(self, pins: dict):
        self.lzc = str(_pin(pins, "norm_lzc.family", "lzd_cell_tree"))
        self.lzc_pins = _sub_pins(pins, "norm_lzc.")
        self.shf = str(_pin(pins, "norm_shifter.family", "barrel_mux_tree"))
        self.shf_pins = _sub_pins(pins, "norm_shifter.")

    def normalize(self, m: Mod, D: int, normalized: bool) -> tuple:
        """dn = b << lzs, the divisor with its leading one at bit D-1, and lzs
        (the shift; zero when the divisor arrives normalized)."""
        SW = _clog2(D)
        if normalized:
            m.wire("dn", D, expr="b")
            m.wire("lzs", SW, expr=f"{SW}'d0")
            return "dn", "lzs", SW
        m.lz(self.lzc, self.lzc_pins, "b", D, "lz", "the divisor's leading zeros")
        m.wire("lzs", SW, expr=f"lz[{SW-1}:0]")
        m.sh(self.shf, self.shf_pins, "b", D, "lzs", False, "dn", "the divisor normalized")
        return "dn", "lzs", SW

    def scale(self, m: Mod, src: str, W: int, lzs: str, out: str, comment: str, normalized: bool) -> str:
        if normalized:
            m.wire(out, W, expr=src)
            return out
        return m.sh(self.shf, self.shf_pins, src, W, lzs, False, out, comment)

    def descale(self, m: Mod, src: str, W: int, lzs: str, out: str, comment: str, normalized: bool) -> str:
        if normalized:
            m.wire(out, W, expr=src)
            return out
        return m.sh(self.shf, self.shf_pins, src, W, lzs, True, out, comment)


def _normalize(m: Mod, pins: dict, D: int, normalized: bool) -> tuple:
    """dn = b << lzs and lzs, the divisor normalization with the counter of
    the `norm.lzc` pins (a behavioral count when the family has no
    module) and a behavioral shift: the approximate dividers' form
    (approx.py); the exact families normalize through the Norm slots."""
    LW = D.bit_length()
    SW = _clog2(D)
    if normalized:
        m.wire("dn", D, expr="b")
        m.wire("lzs", SW, expr=f"{SW}'d0")
        return "dn", "lzs", SW
    m.wire("lz", LW)
    fam = str(_pin(pins, "norm.lzc.family", "lzd_cell_tree"))
    if not m.lib("lzc", fam, _sub_pins(pins, "norm.lzc."), D, ".a(b), .n(lz)", "the divisor's leading zeros"):
        m.raw(f"  always_comb begin lz = {LW}'d{D}; for (int k = {D-1}; k >= 0; k = k - 1) if (b[k]) begin lz = {LW}'d{D-1} - k[{LW-1}:0]; break; end end")
    m.wire("lzs", SW, expr=f"lz[{SW-1}:0]")
    m.wire("dn", D, expr="b << lzs")
    return "dn", "lzs", SW


def _initial_residual(m: Mod, name: str, ax: str, NA: int, Q: int, RW: int, signed: bool = False):
    """The partial remainder before the first quotient digit: the dividend
    bits above the Q quotient positions (below 2^RW by the precondition
    a 2^S / b < 2^Q)."""
    top = NA - Q
    if top <= 0:
        m.wire(name, RW, signed=signed, expr=f"{RW}'d0")
    elif top <= RW:
        m.wire(name, RW, signed=signed, expr=f"{{{{({RW}-{top}){{1'b0}}}}, {ax}[{NA-1}:{Q}]}}" if top < RW else f"{ax}[{NA-1}:{Q}]")
    else:
        m.wire(name, RW, signed=signed, expr=f"{ax}[{Q+RW-1}:{Q}]")


def _csa(m: Mod, out_s: str, out_c: str, RW: int, ws: str, wc: str, add: str, cin: str):
    """One carry-save step: (ws, wc, add) -> (out_s, out_c), the carry
    vector taking cin at its low end."""
    m.wire(out_s, RW, expr=f"{ws} ^ {wc} ^ {add}")
    m.wire(out_c, RW, expr=f"{{({ws}[{RW-2}:0] & {wc}[{RW-2}:0]) | ({ws}[{RW-2}:0] & {add}[{RW-2}:0]) | ({wc}[{RW-2}:0] & {add}[{RW-2}:0]), {cin}}}")


def _square_low(m: Mod, src: str, W: int, LOW: int, fam, fpins: dict, out: str, comment: str) -> str:
    """out (LOW bits) = the low LOW bits of src^2: the copies of src shifted
    under its own set bits, reduced by 3:2 rows and assimilated once
    through the adder family. A remainder below 2^LOW is exact from the
    low bits alone, so the rows above them are never formed."""
    rows = [m.wire(f"{out}_r{b}", LOW, expr=f"{src}[{b}] ? ({_zext(src, W, LOW)} << {b}) : {LOW}'d0")
            for b in range(min(W, LOW))]
    lvl = 0
    while len(rows) > 2:
        nxt = []
        for g in range(0, len(rows) - 2, 3):
            _csa(m, f"{out}_s{lvl}_{g}", f"{out}_c{lvl}_{g}", LOW, rows[g], rows[g + 1], rows[g + 2], "1'b0")
            nxt += [f"{out}_s{lvl}_{g}", f"{out}_c{lvl}_{g}"]
        nxt += rows[len(rows) - len(rows) % 3:]
        rows = nxt
        lvl += 1
    if len(rows) == 1:
        m.wire(out, LOW, expr=rows[0])
    else:
        m.wire(out, LOW)
        m.add(fam, fpins, LOW, rows[0], rows[1], "1'b0", out, f"{out}_co", comment)
    return out


# ---- the quotient-digit selection table ---------------------------------------------------
def qds_table(radix: int, a: int, dbits: int, tbits: int, D: int, rho_in=None, rho_out=None,
              unc_ulps: int = 2, d_slack=Fraction(0), y_slack=Fraction(0)) -> tuple:
    """The quotient-digit selection table of a radix-r stage with digits
    -a..a, the divisor truncated to dbits bits (its leading one included,
    d in [1/2, 1)) and the shifted residual estimated from a carry-save
    pair truncated to tbits fraction bits (the estimate errs by up to
    unc_ulps * 2^-tbits below the value). The stage's input residual w
    lies within rho_in d (rho_in = a/(r-1) unless the previous stage's
    digit set says otherwise), and every cell is checked for containment
    of the next residual in [-rho_out d, rho_out d - 2^-D] over the whole
    cell (rho_out = a/(r-1) unless the next stage needs a tighter bound;
    the margin keeps the dividend bits shifting in from leaving the
    bound on either side, so the table is symmetric; d_slack widens
    every divisor cell, y_slack extends the reachable estimate range,
    for an on-line residual's error terms). An unreachable cell holds
    the saturating digit. Returns ({(d_index, y_index): digit or None},
    y_index_min, y_index_max)."""
    rho = Fraction(a, radix - 1)
    rho_in = Fraction(rho_in) if rho_in is not None else rho
    rho_out = Fraction(rho_out) if rho_out is not None else rho
    dstep = Fraction(1, 1 << dbits)
    ystep = Fraction(1, 1 << tbits)
    margin = Fraction(1, 1 << D)
    ybound = radix * rho_in + y_slack
    yi_min = math.floor(-ybound / ystep) - unc_ulps
    yi_max = math.ceil(ybound / ystep)
    table = {}
    for di in range(1 << (dbits - 1), 1 << dbits):
        d_lo, d_hi = di * dstep - d_slack, (di + 1) * dstep + d_slack
        d_lo = max(d_lo, Fraction(1, 2) - d_slack)
        for yi in range(yi_min, yi_max + 1):
            y_lo, y_hi = yi * ystep, (yi + unc_ulps) * ystep
            if y_lo > ybound * d_hi or y_hi < -ybound * d_hi:
                table[(di, yi)] = a if y_lo > 0 else -a
                continue
            chosen = None
            for k in range(-a, a + 1):
                ok = True
                for d in (d_lo, d_hi):
                    if k != -a and y_lo - k * d < -rho_out * d + margin:
                        ok = False
                    if k != a and y_hi - k * d > rho_out * d - margin:
                        ok = False
                if ok:
                    chosen = k
                    break
            table[(di, yi)] = chosen
    return table, yi_min, yi_max


def feasible_table(radix: int, a: int, dbits: int, tbits: int, D: int, **kw) -> tuple:  # noqa: D417
    """The selection table with the truncation widths widened until every
    cell holds a digit: (table, yi_min, yi_max, dbits, tbits)."""
    tmax, dmax = min(10, D), min(8, D)                     # the residual has D fraction bits, the divisor D bits
    tbits, dbits = min(tbits, tmax), min(dbits, dmax)
    while True:
        table, yi_min, yi_max = qds_table(radix, a, dbits, tbits, D, **kw)
        if not any(v is None for v in table.values()):
            return table, yi_min, yi_max, dbits, tbits
        if tbits < tmax:
            tbits += 1
        elif dbits < dmax:
            dbits += 1
        else:
            raise ValueError(f"no feasible radix-{radix} selection table with digits -{a}..{a} below {dmax} divisor and "
                             f"{tmax} residual bits")


def _encode(digit: int, a: int, enc: str) -> tuple:
    """(value, width) of a digit in an encoding: unencoded (signed binary),
    line (one line per digit value, -a first), gray (a Gray code of the
    offset digit + a), choose_highest (a thermometer: line k set when the
    digit is at least -a + 1 + k)."""
    n = 2 * a + 1
    if enc == "unencoded":
        w = (a + 1).bit_length() + 1
        return digit & ((1 << w) - 1), w
    if enc == "line":
        return 1 << (digit + a), n
    if enc == "gray":
        w = _clog2(n) if n > 1 else 1
        v = digit + a
        return v ^ (v >> 1), w
    if enc == "choose_highest":
        return (1 << (digit + a)) - 1, n - 1
    raise ValueError(f"digit encoding {enc!r}")


def _decode_digit(m: Mod, src: str, a: int, enc: str, out: str) -> str:
    """out (signed) = the digit of an encoded selection word."""
    w = (a + 1).bit_length() + 1
    m.wire(out, w, signed=True)
    if enc == "unencoded":
        m.assign(out, f"$signed({src})")
        return out
    if enc == "gray":
        gw = _clog2(2 * a + 1) if 2 * a + 1 > 1 else 1
        # the offset digit from its Gray code: a prefix xor from the top
        m.wire(f"{out}_b", gw)
        m.assign(f"{out}_b[{gw-1}]", f"{src}[{gw-1}]")
        for i in range(gw - 2, -1, -1):
            m.assign(f"{out}_b[{i}]", f"{out}_b[{i+1}] ^ {src}[{i}]")
        m.assign(out, f"$signed({{1'b0, {out}_b}}) - {_slit(w, a)}")
        return out
    n = 2 * a + 1
    if enc == "line":
        terms = " + ".join(f"({src}[{k}] ? {_slit(w, k - a)} : {w}'sd0)" for k in range(n))
        m.assign(out, terms)
        return out
    # choose_highest: the digit is -a plus the count of set thermometer lines
    terms = " + ".join(f"{{{{{w-1}{{1'b0}}}}, {src}[{k}]}}" for k in range(n - 1))
    m.assign(out, f"{_slit(w, -a)} + ({terms})")
    return out


class _CmpPins:
    """The comparator_digit_selection pins: the comparison width, the
    residual input form, the folding, the output encoding, the
    speculative residuals and the comparator adder. `pins` is the pins
    the caller passed and `pre` the slot's prefix, so every key is
    looked up under the name that chose it."""

    def __init__(self, sp: dict, unc: int = 2, pins: dict | None = None, pre: str = ""):
        pins = sp if pins is None else pins
        self.bits = _ipin(pins, pre + "comparison_bits", 8)
        self.residual_input = str(_pin(pins, pre + "residual_input", "assimilated_estimate"))
        self.fold = _bpin(pins, pre + "symmetry_folding", False)
        self.encoding = str(_pin(pins, pre + "output_encoding", "binary"))
        self.speculate = _bpin(pins, pre + "speculative_candidate_residuals", False)
        self.adder = str(_pin(pins, pre + "comparator_adder.family", "ripple_carry"))
        self.adder_pins = _sub_pins(sp, "comparator_adder.")
        self.unc = unc

    def describe(self) -> str:
        return (f"{self.residual_input}, {self.encoding} digit" + (", folded" if self.fold else "")
                + (", speculative residuals" if self.speculate else ""))


def _thresholds_of(row: list, yi_min: int, a: int) -> list:
    """The 2a thresholds of one table row (its digits by estimate index
    from yi_min): the lowest index whose digit is at least k, for
    k = -a+1..a (one past the row when none)."""
    return [next((yi_min + j for j, v in enumerate(row) if v >= k), yi_min + len(row)) for k in range(-a + 1, a + 1)]


def _comparator_digit(m: Mod, i: str, y, YI: int, a: int, thresholds: dict, key: str, key_bits: int,
                      ws, wc, RW: int, cp: _CmpPins) -> str:
    """dsel_i = the digit from comparators of the estimate y (or of the two
    residual words) against the thresholds of the row selected by `key`:
    each comparator is the slot's adder (the sign of y - th is the pass),
    the coder counts the passes into the output encoding; the folded
    form compares |y| alone (the thresholds at or below zero serve a
    negative estimate through the one's complement)."""
    n_th = 2 * a
    w = (a + 1).bit_length() + 1
    ths = []
    for k in range(n_th):
        if key_bits > 0 and len(thresholds) > 1:
            lines = [f"  always_comb begin case ({key})"]
            for rv, th in sorted(thresholds.items()):
                lines.append(f"    {key_bits}'d{rv}: th{k}_{i} = {_slit(YI, th[k])};")
            lines.append(f"    default: th{k}_{i} = {YI}'sd0; endcase end")
            m.wire(f"th{k}_{i}", YI, signed=True)
            m.raw("\n".join(lines))
        else:
            th = next(iter(thresholds.values()))
            m.wire(f"th{k}_{i}", YI, signed=True, expr=_slit(YI, th[k]))
        ths.append(f"th{k}_{i}")
    if cp.fold:
        for th in thresholds.values():
            if any(th[k] > 0 for k in range(a)) or any(th[k] <= 0 for k in range(a, n_th)):
                raise ValueError("comparator folding: the selection thresholds are not symmetric about zero")
    two_word = cp.residual_input == "redundant_two_word" and ws is not None and not cp.fold
    if cp.fold:
        neg = m.wire(f"yneg_{i}", expr=f"{y}[{YI-1}]")
        yabs = m.wire(f"yabs_{i}", YI, signed=True, expr=f"{neg} ? ~{y} : {y}")
    passes = []
    for k in range(n_th):
        thk = ths[k]
        s = m.wire(f"cs{k}_{i}", YI)
        if cp.fold and k < a:
            # a threshold at or below zero: for y < 0, y >= th <=> ~th >= ~y (the sign of ~th - |y|)
            nth = m.wire(f"nth{k}_{i}", YI, signed=True, expr=f"~{thk}")
            m.sub(cp.adder, cp.adder_pins, YI, nth, yabs, s, f"cg{k}_{i}", f"comparator {k}: ~th - |y| for a negative estimate")
            m.wire(f"pass{k}_{i}", expr=f"{neg} ? ~{s}[{YI-1}] : 1'b1")
        elif cp.fold:
            m.sub(cp.adder, cp.adder_pins, YI, yabs, thk, s, f"cg{k}_{i}", f"comparator {k}: |y| - th for a positive estimate")
            m.wire(f"pass{k}_{i}", expr=f"{neg} ? 1'b0 : ~{s}[{YI-1}]")
        elif two_word:
            # the two residual words and the complemented threshold through a 3:2 row, then the adder
            wst = m.wire(f"wst{k}_{i}", YI, expr=f"{ws}[{RW-1}:{RW-YI}]")
            wct = m.wire(f"wct{k}_{i}", YI, expr=f"{wc}[{RW-1}:{RW-YI}]")
            nth = m.wire(f"nth{k}_{i}", YI, expr=f"~{thk}")
            cs3 = m.wire(f"c3s{k}_{i}", YI, expr=f"{wst} ^ {wct} ^ {nth}")
            cc3 = m.wire(f"c3c{k}_{i}", YI, expr=f"{{({wst}[{YI-2}:0] & {wct}[{YI-2}:0]) | ({wst}[{YI-2}:0] & {nth}[{YI-2}:0]) | "
                                                  f"({wct}[{YI-2}:0] & {nth}[{YI-2}:0]), 1'b1}}")
            m.add(cp.adder, cp.adder_pins, YI, cs3, cc3, "1'b0", s, f"cg{k}_{i}", f"comparator {k}: ws + wc - th")
            m.wire(f"pass{k}_{i}", expr=f"~{s}[{YI-1}]")
        else:
            m.sub(cp.adder, cp.adder_pins, YI, y, thk, s, f"cg{k}_{i}", f"comparator {k}: y - th")
            m.wire(f"pass{k}_{i}", expr=f"~{s}[{YI-1}]")
        passes.append(f"pass{k}_{i}")
    # the coder: the digit is -a plus the count of thresholds passed, in the output encoding
    pv = m.wire(f"passes_{i}", n_th, expr="{" + ", ".join(reversed(passes)) + "}")
    if cp.encoding in ("one_hot", "zero_one_hot"):
        # line k (digit -a + k): the pass below it set and its own clear
        n = 2 * a + 1
        lines = []
        for k in range(n):
            lo = f"{pv}[{k-1}]" if k > 0 else "1'b1"
            hi = f"~{pv}[{k}]" if k < n - 1 else "1'b1"
            lines.append((k - a, f"({lo} & {hi})"))
        if cp.encoding == "zero_one_hot":
            lines = [ln for ln in lines if ln[0] != 0]                       # no line for the zero digit
        oh = m.wire(f"oh_{i}", len(lines), expr="{" + ", ".join(ln for _d, ln in reversed(lines)) + "}")
        terms = [f"({oh}[{kk}] ? {_slit(w, dv)} : {w}'sd0)" for kk, (dv, _ln) in enumerate(lines)]
        m.wire(f"dsel_{i}", w, signed=True, expr=" | ".join(terms))
        return f"dsel_{i}"
    if cp.encoding == "sign_magnitude":
        # the sign from the zero threshold, the magnitude the passes beyond it (or the fails below it)
        sgn = m.wire(f"sgn_{i}", expr=f"~{pv}[{a-1}]")
        mag_terms = " + ".join(f"{{{{{w-1}{{1'b0}}}}, {pv}[{k}]}}" for k in range(a, n_th))
        neg_terms = " + ".join(f"{{{{{w-1}{{1'b0}}}}, ~{pv}[{k}]}}" for k in range(0, a))
        mag = m.wire(f"mag_{i}", w, signed=True, expr=f"{sgn} ? ({neg_terms}) : ({mag_terms})")
        m.wire(f"dsel_{i}", w, signed=True, expr=f"{sgn} ? -{mag} : {mag}")
        return f"dsel_{i}"
    terms = " + ".join(f"{{{{{w-1}{{1'b0}}}}, {pv}[{k}]}}" for k in range(n_th))
    m.wire(f"dsel_{i}", w, signed=True, expr=f"{_slit(w, -a)} + ({terms})")
    return f"dsel_{i}"


class Selector:
    """The quotient-digit selection of one recurrence stage: the table
    (qds_table) or the comparators (comparator_digit_selection) of the
    digit_select slot, with its encodings and foldings; every method
    writes into a Mod and returns wires. The estimate's short adder is
    the residual_adder family under the table, the comparator_adder
    family under the comparators."""

    def __init__(self, pins: dict, radix: int, a: int, D: int, rho_in=None, rho_out=None, unc_ulps: int = 2,
                 d_slack=Fraction(0), y_slack=Fraction(0), IB: int | None = None):
        self.family = str(_pin(pins, "digit_select.family", "qds_table"))
        self.radix, self.a, self.D = radix, a, D
        sp = _sub_pins(pins, "digit_select.")
        self.sp = sp
        self.unc = unc_ulps
        # the integer bits of the residual the estimate is cut from (|r w| < r rho d < 2^(IB-1))
        self.IB = IB if IB is not None else (3 if radix == 2 else 4)
        if self.family == "comparator_digit_selection":
            self.cp = _CmpPins(sp, unc_ulps, pins, "digit_select.")
            tb = max(2, min(self.cp.bits - self.IB, D))
            db = 3 if radix > 2 else 1
            self.assim = 0
            self.encoding = self.cp.encoding
            self.fold = self.cp.fold
            self.est_fam, self.est_pins = self.cp.adder, self.cp.adder_pins
        else:
            self.cp = None
            db = max(3, min(_ipin(pins, "digit_select.divisor_truncation_bits", 4), D)) if radix > 2 else 1
            tb = max(2, min(_ipin(pins, "digit_select.residual_truncation_bits", 4), D))
            self.assim = _ipin(pins, "digit_select.assimilator_bits", 0)
            self.encoding = str(_pin(pins, "digit_select.digit_encoding", "unencoded"))
            self.fold = str(_pin(pins, "digit_select.folding", "none")) == "signed_magnitude"
            self.est_fam = str(_pin(pins, "residual_adder.family", "ripple_carry"))
            self.est_pins = _sub_pins(pins, "residual_adder.")
        self.table, self.yi_min, self.yi_max, self.dbits, self.tbits = feasible_table(
            radix, a, db, tb, D, rho_in=rho_in, rho_out=rho_out, unc_ulps=unc_ulps, d_slack=d_slack, y_slack=y_slack)
        self.YI = self.IB + self.tbits
        ND = 1 << (self.dbits - 1)
        self.ND = ND
        # the thresholds per divisor row (its bits below the leading one)
        self.thresholds = {di - ND: _thresholds_of([self.table[(di, yi)] for yi in range(self.yi_min, self.yi_max + 1)],
                                                   self.yi_min, a) for di in range(ND, 2 * ND)}

    def describe(self) -> str:
        if self.cp:
            return f"comparators over {self.YI} estimate bits ({self.cp.describe()})"
        return (f"a table over {self.dbits} divisor bits and {self.tbits} residual fraction bits ({self.encoding} digit"
                f"{', folded' if self.fold else ''}{f', assimilated over {self.assim} bits' if self.assim > self.YI else ''})")

    def estimate(self, m: Mod, i: str, ws: str, wc: str, RW: int, dt: str):
        """y_i, the signed estimate (YI bits) of the shifted residual: the
        top bits of the carry-save pair through the short adder (over
        assimilator_bits when wider); None when the comparators take
        the two words themselves."""
        YI = self.YI
        if self.cp and self.cp.residual_input == "redundant_two_word" and not self.cp.fold:
            return None
        YA = max(YI, min(self.assim, RW)) if self.assim else YI
        m.wire(f"yas_{i}", YA, expr=f"{ws}[{RW-1}:{RW-YA}]")
        m.wire(f"yac_{i}", YA, expr=f"{wc}[{RW-1}:{RW-YA}]")
        m.wire(f"ya_{i}", YA)
        m.add(self.est_fam, self.est_pins, YA, f"yas_{i}", f"yac_{i}", "1'b0", f"ya_{i}", f"yao_{i}",
              f"the residual estimate assimilated over {YA} bits")
        return m.wire(f"y_{i}", YI, signed=True, expr=f"$signed(ya_{i}[{YA-1}:{YA-YI}])")

    def digit_from_estimate(self, m: Mod, i: str, y, dt: str, ws: str = None, wc: str = None, RW: int = 0) -> str:
        """dsel_i (signed) = the digit of estimate y under divisor row dt."""
        YI, a = self.YI, self.a
        w = (a + 1).bit_length() + 1
        rowbits = self.dbits - 1
        if self.cp:
            key = f"{dt}[{rowbits-1}:0]" if rowbits else ""
            return _comparator_digit(m, i, y, YI, a, self.thresholds, key, rowbits, ws, wc, RW, self.cp)
        # the table as a case ROM (a module of its own) over the divisor row and the estimate: the entries
        # outside the table's estimate range saturate by the estimate's sign
        ew = _encode(0, a, self.encoding)[1]
        if self.fold:
            # the table over |y| alone: row e holds the digit of the estimate e - (unc - 1), so a
            # non-negative estimate reads row y + unc - 1 (an increment through the short adder) and a
            # negative one reads row ~y, whose digit negated is its own (the containment is symmetric)
            unc = self.unc
            neg = m.wire(f"yneg_{i}", expr=f"{y}[{YI-1}]")
            m.wire(f"yb_{i}", YI - 1, expr=f"{y}[{YI-2}:0]")
            m.wire(f"yk_{i}", YI - 1, expr=f"{YI-1}'d{unc - 1}")
            m.wire(f"yinc_{i}", YI - 1)
            m.add(self.est_fam, self.est_pins, YI - 1, f"yb_{i}", f"yk_{i}", "1'b0", f"yinc_{i}", f"yincc_{i}",
                  "the folded estimate's offset")
            yabs = m.wire(f"yabs_{i}", YI - 1, expr=f"{neg} ? ~{y}[{YI-2}:0] : yinc_{i}")
            key = f"{{{dt}[{rowbits-1}:0], {yabs}}}" if rowbits else yabs
            ent = {}
            for di in range(self.ND, 2 * self.ND):
                for e in range(0, min(self.yi_max + unc - 1, (1 << (YI - 1)) - 1) + 1):
                    yi = e - (unc - 1)
                    if yi < self.yi_min:
                        continue
                    ent[((di - self.ND) << (YI - 1)) | e] = _encode(self.table[(di, yi)], a, self.encoding)[0]
            m.rom(f"Q_{i}", ent, ew, key, f"drom_{i}", f"the folded selection table ({self.describe()})",
                  default=f"{ew}'d{_encode(a, a, self.encoding)[0]}", kbits=rowbits + YI - 1)
            dpos = _decode_digit(m, f"drom_{i}", a, self.encoding, f"dpos_{i}")
            m.wire(f"dsel_{i}", w, signed=True, expr=f"{neg} ? -{dpos} : {dpos}")
            return f"dsel_{i}"
        yu = m.wire(f"yu_{i}", YI, expr=f"{{~{y}[{YI-1}], {y}[{YI-2}:0]}}")            # the estimate offset to unsigned
        key = f"{{{dt}[{rowbits-1}:0], {yu}}}" if rowbits else yu
        ent = {}
        for di in range(self.ND, 2 * self.ND):
            for yi in range(max(self.yi_min, -(1 << (YI - 1))), min(self.yi_max, (1 << (YI - 1)) - 1) + 1):
                ent[((di - self.ND) << YI) | (yi + (1 << (YI - 1)))] = _encode(self.table[(di, yi)], a, self.encoding)[0]
        m.rom(f"Q_{i}", ent, ew, key, f"drom_{i}", f"the selection table ({self.describe()})",
              default=f"k[{YI-1}] ? {ew}'d{_encode(a, a, self.encoding)[0]} : {ew}'d{_encode(-a, a, self.encoding)[0]}",
              kbits=rowbits + YI)
        return _decode_digit(m, f"drom_{i}", a, self.encoding, f"dsel_{i}")


def _multiples(m: Mod, a: int, dn: str, D: int, RW: int, fam, fpins: dict, tag: str) -> dict:
    """{k: wire} of the divisor multiples k d (k = 1..a) at RW bits, the
    non-shift multiples through the residual adder family."""
    out = {}
    IB = RW - D
    out[1] = m.wire(f"{tag}d1", RW, expr=f"{{{IB}'b0, {dn}}}")
    if a >= 2:
        out[2] = m.wire(f"{tag}d2", RW, expr=f"{{{IB-1}'b0, {dn}, 1'b0}}")
    if a >= 3:
        out[3] = m.wire(f"{tag}d3", RW)
        m.add(fam, fpins, RW, out[1], out[2], "1'b0", out[3], f"{tag}d3c", "the divisor multiple 3d")
    if a >= 4:
        out[4] = m.wire(f"{tag}d4", RW, expr=f"{{{IB-2}'b0, {dn}, 2'b0}}")
    for k in range(5, a + 1):
        if k in out:
            continue
        if k & (k - 1) == 0:
            out[k] = m.wire(f"{tag}d{k}", RW, expr=f"{out[1]} << {k.bit_length() - 1}")
            continue
        p2 = 1 << (k.bit_length() - 1)
        s = m.wire(f"{tag}d{k}", RW)
        m.add(fam, fpins, RW, out[p2], out[k - p2], "1'b0", s, f"{tag}d{k}c", f"the divisor multiple {k}d")
    return out


def _otf_step(m: Mod, i: str, QW: int, kbits: int, digit: str, dw: int, qq: str, qmm: str) -> tuple:
    """One on-the-fly conversion step for a digit of kbits (value in
    -r+1..r-1): (Q', QM') from (Q, QM)."""
    r = 1 << kbits
    dm1 = m.wire(f"dm1_{i}", dw, signed=True, expr=f"{digit} - {dw}'sd1")
    neg = f"{digit}[{dw-1}]"
    pos = f"({digit} > {dw}'sd0)"
    if kbits == 1:
        q_new = m.wire(f"qq_{i}", QW, expr=f"{neg} ? {{{qmm}[{QW-2}:0], {digit}[0]}} : {{{qq}[{QW-2}:0], {digit}[0]}}")
        qm_new = m.wire(f"qmm_{i}", QW, expr=f"{pos} ? {{{qq}[{QW-2}:0], {dm1}[0]}} : {{{qmm}[{QW-2}:0], {dm1}[0]}}")
    else:
        q_new = m.wire(f"qq_{i}", QW, expr=f"{neg} ? {{{qmm}[{QW-1-kbits}:0], {digit}[{kbits-1}:0]}} : {{{qq}[{QW-1-kbits}:0], {digit}[{kbits-1}:0]}}")
        qm_new = m.wire(f"qmm_{i}", QW, expr=f"{pos} ? {{{qq}[{QW-1-kbits}:0], {dm1}[{kbits-1}:0]}} : {{{qmm}[{QW-1-kbits}:0], {dm1}[{kbits-1}:0]}}")
    _ = r
    return q_new, qm_new


# ---- the digit recurrences -------------------------------------------------------------
def restoring_sv(N: int, S: int, D: int, Q: int, pins: dict, name: str) -> tuple:
    """restoring | nonperforming | nonrestoring: one quotient bit per stage
    from the trial subtraction of the divisor from the shifted partial
    remainder through the residual_adder family. Restoring adds the
    divisor back after a failed trial (a second adder per stage),
    nonperforming keeps the old remainder through a multiplexer, and the
    nonrestoring array adds or subtracts by the remainder's sign and
    corrects once at the end."""
    style = str(_pin(pins, "style", "restoring"))
    fam = str(_pin(pins, "residual_adder.family", "ripple_carry"))
    fpins = _sub_pins(pins, "residual_adder.")
    m = Mod(name, f"divider ({style}, residual adder {fam}): the shift-and-subtract array, one quotient bit per stage")
    m.port("input", "a", N)
    m.port("input", "b", D)
    m.port("output", "q", Q)
    m.port("output", "r", D)
    ax, NA = _dividend(m, N, S)
    RW = D + 1
    m.wire("bx", RW, expr="{1'b0, b}")
    _initial_residual(m, "r_0", ax, NA, Q, RW)
    if style == "nonrestoring":
        m.wire("neg_0", expr="1'b0")
        for i in range(Q):
            bit = Q - 1 - i
            m.wire(f"sh_{i+1}", RW, expr=f"{{r_{i}[{RW-2}:0], {ax}[{bit}]}}")
            m.wire(f"opb_{i+1}", RW, expr=f"neg_{i} ? bx : ~bx")
            m.wire(f"t_{i+1}", RW)
            m.wire(f"c_{i+1}")
            m.add(fam, fpins, RW, f"sh_{i+1}", f"opb_{i+1}", f"~neg_{i}", f"t_{i+1}", f"c_{i+1}",
                  f"stage {i+1}: add the divisor to a negative remainder, subtract it from a positive one")
            m.wire(f"r_{i+1}", RW, expr=f"t_{i+1}")
            m.wire(f"neg_{i+1}", expr=f"t_{i+1}[{RW-1}]")
            m.assign(f"q[{bit}]", f"~neg_{i+1}")
        m.wire("rc", RW)
        m.wire("rcc")
        m.add(fam, fpins, RW, f"r_{Q}", "bx", "1'b0", "rc", "rcc", "the final correction: the divisor added back to a negative remainder")
        m.assign("r", f"neg_{Q} ? rc[{D-1}:0] : r_{Q}[{D-1}:0]")
    else:
        for i in range(Q):
            bit = Q - 1 - i
            m.wire(f"sh_{i+1}", RW, expr=f"{{r_{i}[{RW-2}:0], {ax}[{bit}]}}")
            m.wire(f"t_{i+1}", RW)
            m.sub(fam, fpins, RW, f"sh_{i+1}", "bx", f"t_{i+1}", f"ge_{i+1}",
                  f"stage {i+1}: the trial subtraction (its carry-out is the quotient bit)")
            if style == "restoring":
                # the failed trial restored by adding the divisor back
                m.wire(f"rb_{i+1}", RW)
                m.wire(f"rbc_{i+1}")
                m.add(fam, fpins, RW, f"t_{i+1}", "bx", "1'b0", f"rb_{i+1}", f"rbc_{i+1}", f"stage {i+1}: the restoring addition")
                m.wire(f"r_{i+1}", RW, expr=f"ge_{i+1} ? t_{i+1} : rb_{i+1}")
            else:
                m.wire(f"r_{i+1}", RW, expr=f"ge_{i+1} ? t_{i+1} : sh_{i+1}")
            m.assign(f"q[{bit}]", f"ge_{i+1}")
        m.assign("r", f"r_{Q}[{D-1}:0]")
    return name, m.render()


def _plan(radix: int) -> list:
    """The sub-stage digit widths of one iteration at a radix: radix-4 and
    radix-2 sub-stages cascaded or overlapped (the card's staging)."""
    return {2: [1], 4: [2], 8: [2, 1], 16: [2, 2], 32: [2, 2, 1], 64: [2, 2, 2]}[radix]


def _srt_sv(N: int, S: int, D: int, Q: int, family: str, pins: dict, name: str, normalized: bool,
            plan: list | None = None, a4: int | None = None, overlap: int | None = None, form: str | None = None,
            conv: str | None = None) -> tuple:
    """The SRT recurrences: srt_radix2 (digits -1..1 from the estimate,
    the residual carry-save or assimilated by a CPA each stage) and
    srt_high_radix (radix-4 sub-stages with digits -2..2 or -3..3 and
    radix-2 sub-stages, cascaded, or overlapped with the later selections
    speculated per candidate digit of the earlier ones). The digit comes
    from the digit_select slot (a generated table in its encoding, or
    comparators against the table's thresholds through the slot's
    adder), the divisor multiples that are no shifts from the
    residual_adder family, the quotient by on-the-fly conversion or as
    Q+ - Q-; the divisor is normalized through the norm slots and the
    dividend scaled with it."""
    if family == "srt_radix2":
        plan = [1]
        form = form or str(_pin(pins, "residual_form", "carry_save"))
        redundant = form != "twos_complement_cpa"
        overlap = 1
        a4 = 2
    else:
        plan = plan or _plan(_ipin(pins, "radix", 4))
        form = form or str(_pin(pins, "residual_form", "carry_save"))
        redundant = form != "irredundant"
        if a4 is None:
            a4 = 3 if str(_pin(pins, "digit_redundancy", "minimal")) == "maximal" else 2
        if overlap is None:
            overlap = max(1, min(len(plan), _ipin(pins, "overlapped_stages", 1)))
    conv = conv or str(_pin(pins, "quotient_conversion", "on_the_fly"))
    fam = str(_pin(pins, "residual_adder.family", "ripple_carry"))
    fpins = _sub_pins(pins, "residual_adder.")
    norm = Norm(pins)
    bits = sum(plan)
    steps = -(-(Q + 2) // bits)
    QW = steps * bits
    # the sub-stages' digit sets: a radix-4 sub-stage has digits -a4..a4, a radix-2 one -1..1; each stage's
    # selection keeps the residual inside the bound the following sub-stage needs
    radices = [1 << k for k in plan]
    digits = [a4 if k == 2 else 1 for k in plan]
    # the residual bounds: the iteration's composite digit set (a = sum of a_p times the later radices) bounds
    # the residual by a / (r - 1) at the iteration boundary; inside, sub-stage p leaves the residual inside
    # sub-stage p+1's input bound, which is (that sub-stage's output bound + a_{p+1}) / r_{p+1}; the chain
    # closes on the composite bound at the first sub-stage
    a_total = sum(digits[p] << sum(plan[p + 1:]) for p in range(len(plan)))
    rho_total = Fraction(a_total, (1 << bits) - 1)
    rho_in = [Fraction(0)] * len(plan)
    nxt = rho_total
    for p in range(len(plan) - 1, -1, -1):
        rho_in[p] = (nxt + digits[p]) / radices[p]
        nxt = rho_in[p]
    rho_out = [rho_in[p + 1] if p + 1 < len(plan) else rho_total for p in range(len(plan))]
    IB = 4 if 2 in plan else 3
    RW = D + IB
    est_unc = [2] * len(plan)
    # a speculated sub-stage sees an estimate formed arithmetically from the earlier residual: an extra ulp
    windows = []
    p = 0
    while p < len(plan):
        n = min(overlap, len(plan) - p)
        while n > 1 and math.prod(2 * digits[q] + 1 for q in range(p, p + n - 1)) > SPECULATION_CAP:
            n -= 1
        windows.append(list(range(p, p + n)))
        for q in range(p + 1, p + n):
            est_unc[q] = 3
        p += n
    sels = [Selector(pins, radices[p], digits[p], D, rho_in=rho_in[p], rho_out=rho_out[p], unc_ulps=est_unc[p], IB=IB)
            for p in range(len(plan))]
    desc = (f"SRT radix-{2 ** bits} divider: " + " + ".join(f"radix-{r}" for r in radices) + " sub-stage(s) per iteration"
            + (f", selections overlapped in windows of {max(len(w) for w in windows)}" if any(len(w) > 1 for w in windows) else "")
            + f", the residual {'carry-save' if redundant else 'assimilated by a CPA each sub-stage'}, digits by {sels[0].describe()}, "
            f"quotient by {conv}; the divisor normalized to [1/2, 1), the dividend scaled with it")
    m = Mod(name, desc)
    m.port("input", "a", N)
    m.port("input", "b", D)
    m.port("output", "q", Q)
    m.port("output", "r", D)
    ax, NA = _dividend(m, N, S)
    dn, lzs, SW = norm.normalize(m, D, normalized)
    NW = NA + D
    m.wire("axw", NW, expr=f"{{{{{D}{{1'b0}}}}, {ax}}}")
    norm.scale(m, "axw", NW, lzs, "an", "the dividend scaled with the divisor", normalized)
    a_max = max(digits)
    mult = _multiples(m, a_max, dn, D, RW, fam, fpins, "m")
    _initial_residual(m, "ws_0_0", "an", NW, QW, RW)
    m.wire("wc_0_0", RW, expr=f"{RW}'d0")
    for p, s in enumerate(sels):
        m.wire(f"dt_{p}", s.dbits, expr=f"{dn}[{D-1}:{D-s.dbits}]" if s.dbits < D else dn)
    # the conversion state before the first digit (the first step's own wires are the `0_0` ones)
    m.wire("qq_init", QW, expr=f"{QW}'d0")
    m.wire("qmm_init", QW, expr=f"{{{QW}{{1'b1}}}}")
    m.wire("qpos_init", QW, expr=f"{QW}'d0")
    m.wire("qneg_init", QW, expr=f"{QW}'d0")
    # the residual's integer bits above the estimate: the estimate is the top YI bits of the shifted residual
    pos = QW
    ws, wc, qq, qmm, qpos, qneg = "ws_0_0", "wc_0_0", "qq_init", "qmm_init", "qpos_init", "qneg_init"
    YE_MAX = max(s.tbits for s in sels) + 5                    # the speculative estimates' fraction bits
    for st in range(steps):
        for win in windows:
            spec_digits: dict = {}                              # (p, path) -> the speculated digit wire
            for wi, p in enumerate(win):
                k = plan[p]
                r = radices[p]
                a = digits[p]
                sel = sels[p]
                tag = f"{st}_{p}"
                pos -= k
                # the shifted residual: the next k dividend bits enter
                dbits_in = ", ".join(f"an[{pos + k - 1 - t}]" for t in range(k))
                m.wire(f"wsh_{tag}", RW, expr=f"{{{ws}[{RW-1-k}:0], {dbits_in}}}")
                m.wire(f"wch_{tag}", RW, expr=f"{{{wc}[{RW-1-k}:0], {k}'b0}}")
                if wi == 0:
                    y = sel.estimate(m, tag, f"wsh_{tag}", f"wch_{tag}", RW, f"dt_{p}")
                    dsel = sel.digit_from_estimate(m, tag, y, f"dt_{p}", f"wsh_{tag}", f"wch_{tag}", RW)
                    if len(win) > 1:
                        # the estimate of this sub-stage's residual at YE - IB fraction bits (the whole residual
                        # when it is that short), the source of the speculation: the pair's top bits through
                        # the residual adder, the sum modulo 2^YE
                        YE = min(YE_MAX + IB, RW)
                        m.wire(f"yes_{tag}", YE, expr=f"wsh_{tag}[{RW-1}:{RW-YE}]")
                        m.wire(f"yec_{tag}", YE, expr=f"wch_{tag}[{RW-1}:{RW-YE}]")
                        m.wire(f"yeu_{tag}", YE)
                        m.add(fam, fpins, YE, f"yes_{tag}", f"yec_{tag}", "1'b0", f"yeu_{tag}", f"yeuc_{tag}",
                              f"sub-stage {tag}: the residual estimate for the overlapped selections")
                        m.wire(f"ye_{tag}", YE, signed=True, expr=f"$signed(yeu_{tag})")
                        m.wire(f"de_{tag}", YE, signed=True,
                               expr=f"$signed({{{IB}'b0, {dn}[{D-1}:{D-(YE-IB)}]}})" if YE - IB <= D else
                                    f"$signed({{{IB}'b0, {dn}, {YE - IB - D}'b0}})")
                        paths = [((), f"ye_{tag}")]
                        spec_digits[(p, ())] = dsel
                        # the divisor estimate's multiples for the speculation (the odd one by the residual adder)
                        de_m = {1: f"de_{tag}", 2: m.wire(f"de2_{tag}", YE, signed=True, expr=f"de_{tag} <<< 1")}
                        if max(digits) >= 3:
                            m.wire(f"de3_{tag}", YE, signed=True)
                            m.add(fam, fpins, YE, f"de_{tag}", f"de2_{tag}", "1'b0", f"de3_{tag}", f"de3c_{tag}", "the speculation's 3 d")
                            de_m[3] = f"de3_{tag}"
                        for q in win[1:]:
                            kq = plan[q]
                            new_paths = []
                            prev_p = win[win.index(q) - 1]
                            for path, yw in paths:
                                for cand in range(-digits[prev_p], digits[prev_p] + 1):
                                    ptag = f"{tag}_{'_'.join(str(c).replace('-', 'm') for c in path + (cand,))}"
                                    # the residual after the candidate digit, shifted by the next sub-stage's radix,
                                    # through the residual adder family
                                    if cand == 0:
                                        m.wire(f"yn_{ptag}", YE, signed=True, expr=f"{yw} <<< {kq}")
                                    else:
                                        m.wire(f"yc_{ptag}", YE)
                                        if cand > 0:
                                            m.sub(fam, fpins, YE, yw, de_m[cand], f"yc_{ptag}", f"ycc_{ptag}",
                                                  f"speculation {ptag}: the estimate less {cand} d")
                                        else:
                                            m.add(fam, fpins, YE, yw, de_m[-cand], "1'b0", f"yc_{ptag}", f"ycc_{ptag}",
                                                  f"speculation {ptag}: the estimate plus {-cand} d")
                                        m.wire(f"yn_{ptag}", YE, signed=True, expr=f"$signed(yc_{ptag}) <<< {kq}")
                                    # biased one ulp low into the table's estimate convention (a decrement of the
                                    # narrow estimate)
                                    m.wire(f"yt0_{ptag}", sels[q].YI, signed=True, expr=f"$signed(yn_{ptag}[{YE-1}:{YE-sels[q].YI}])")
                                    m.wire(f"ytm_{ptag}", sels[q].YI, expr=f"{{{sels[q].YI}{{1'b1}}}}")
                                    m.wire(f"yt_{ptag}", sels[q].YI, signed=True)
                                    m.add(fam, fpins, sels[q].YI, f"yt0_{ptag}", f"ytm_{ptag}", "1'b0", f"yt_{ptag}", f"ytc_{ptag}",
                                          f"speculation {ptag}: the estimate biased low")
                                    d_spec = sels[q].digit_from_estimate(m, f"s_{ptag}", f"yt_{ptag}", f"dt_{q}")
                                    spec_digits[(q, path + (cand,))] = d_spec
                                    new_paths.append((path + (cand,), f"yn_{ptag}"))
                            paths = new_paths
                else:
                    # the speculated selections resolved by the earlier sub-stages' actual digits
                    prevs = win[:wi]
                    w = (a + 1).bit_length() + 1
                    m.wire(f"dsel_{tag}", w, signed=True)
                    lines = ["  always_comb begin"]
                    lines.append("    case ({" + ", ".join(f"dsel_{st}_{pp}" for pp in prevs) + "})")
                    for (q, path), dw in spec_digits.items():
                        if q != p:
                            continue
                        key = ", ".join(_slit((digits[pp] + 1).bit_length() + 1, c) for pp, c in zip(prevs, path))
                        lines.append(f"      {{{key}}}: dsel_{tag} = {dw};")
                    lines.append(f"      default: dsel_{tag} = {w}'sd0;")
                    lines.append("    endcase end")
                    m.raw("\n".join(lines))
                    dsel = f"dsel_{tag}"
                # the multiple of the digit, subtracted for a positive digit
                w = (a + 1).bit_length() + 1
                mag_terms = " : ".join(f"({dsel} == {_slit(w, s)} || {dsel} == {_slit(w, -s)}) ? {mult[s]}" for s in range(a, 0, -1))
                m.wire(f"mult_{tag}", RW, expr=f"{mag_terms} : {RW}'d0")
                m.wire(f"add_{tag}", RW, expr=f"({dsel} > {w}'sd0) ? ~mult_{tag} : mult_{tag}")
                m.wire(f"cin_{tag}", expr=f"{dsel} > {w}'sd0")
                if redundant:
                    if sel.cp and sel.cp.speculate:
                        # every candidate residual formed, the digit selecting it
                        cs, cc = [], []
                        m.wire(f"zero_{tag}", RW, expr=f"{RW}'d0")
                        for s in range(-a, a + 1):
                            ctag = f"{tag}_c{str(s).replace('-', 'm')}"
                            addc = f"~{mult[s]}" if s > 0 else (mult[-s] if s < 0 else f"zero_{tag}")
                            _csa(m, f"cws_{ctag}", f"cwc_{ctag}", RW, f"wsh_{tag}", f"wch_{tag}", addc, "1'b1" if s > 0 else "1'b0")
                            cs.append((s, f"cws_{ctag}", f"cwc_{ctag}"))
                        sel_s = " : ".join(f"({dsel} == {_slit(w, s)}) ? {x}" for s, x, _ in cs[:-1]) + f" : {cs[-1][1]}"
                        sel_c = " : ".join(f"({dsel} == {_slit(w, s)}) ? {y}" for s, _, y in cs[:-1]) + f" : {cs[-1][2]}"
                        m.wire(f"ws_{tag}n", RW, expr=sel_s)
                        m.wire(f"wc_{tag}n", RW, expr=sel_c)
                    else:
                        _csa(m, f"ws_{tag}n", f"wc_{tag}n", RW, f"wsh_{tag}", f"wch_{tag}", f"add_{tag}", f"cin_{tag}")
                else:
                    m.wire(f"ws_{tag}n", RW)
                    m.wire(f"wco_{tag}")
                    m.add(fam, fpins, RW, f"wsh_{tag}", f"add_{tag}", f"cin_{tag}", f"ws_{tag}n", f"wco_{tag}",
                          f"sub-stage {tag}: the residual assimilated")
                    m.wire(f"wc_{tag}n", RW, expr=f"{RW}'d0")
                ws, wc = f"ws_{tag}n", f"wc_{tag}n"
                # the conversion
                if conv == "on_the_fly":
                    qq, qmm = _otf_step(m, tag, QW, k, dsel, w, qq, qmm)
                else:
                    m.wire(f"qpos_{tag}", QW, expr=f"{{{qpos}[{QW-1-k}:0], ({dsel} > {w}'sd0) ? {dsel}[{k-1}:0] : {k}'d0}}")
                    m.wire(f"qneg_{tag}", QW, expr=f"{{{qneg}[{QW-1-k}:0], ({dsel} < {w}'sd0) ? (-{dsel}) [{k-1}:0] : {k}'d0}}")
                    qpos, qneg = f"qpos_{tag}", f"qneg_{tag}"
    # the final residual: assimilated, its sign correcting the quotient and the remainder
    m.wire("wf", RW)
    m.wire("wfc")
    m.add(fam, fpins, RW, ws, wc, "1'b0", "wf", "wfc", "the final residual assimilated")
    m.wire("wneg", expr=f"wf[{RW-1}]")
    m.wire("wsub", RW)
    m.sub(fam, fpins, RW, "wf", mult[1], "wsub", "wover", "the residual against the divisor")
    m.wire("wadd", RW)
    m.wire("waddc")
    m.add(fam, fpins, RW, "wf", mult[1], "1'b0", "wadd", "waddc", "the divisor added back to a negative residual")
    if conv == "on_the_fly":
        m.wire("qinc", QW)
        m.wire("qincc")
        m.wire("zeroq", QW, expr=f"{QW}'d0")
        m.add(fam, fpins, QW, qq, "zeroq", "1'b1", "qinc", "qincc", "the quotient plus one for a residual at or above the divisor")
        m.wire("q0", QW, expr=f"wneg ? {qmm} : (wover ? qinc : {qq})")
    else:
        m.wire("qd", QW)
        m.sub(fam, fpins, QW, qpos, qneg, "qd", "qdc", "Q+ - Q-")
        m.wire("qadj", QW, expr="wneg ? {%d{1'b1}} : (wover ? %d'd1 : %d'd0)" % (QW, QW, QW))
        m.wire("q0", QW)
        m.wire("q0c")
        m.add(fam, fpins, QW, "qd", "qadj", "1'b0", "q0", "q0c", "the sign correction of the quotient")
    m.wire("rf", RW, expr="wneg ? wadd : (wover ? wsub : wf)")
    m.wire("rfd", D, expr=f"rf[{D-1}:0]")
    norm.descale(m, "rfd", D, lzs, "rds", "the remainder de-scaled", normalized)
    m.assign("q", f"q0[{Q-1}:0]")
    m.assign("r", "rds")
    return name, m.render()


def _online_sv(N: int, S: int, D: int, Q: int, pins: dict, name: str, normalized: bool) -> tuple:
    """On-line (most-significant-digit-first) division unrolled, radix 2 or
    4: the divisor and dividend digits join one per stage after an on-line
    delay of delta digits, stage j adding the new dividend digit and
    subtracting the partial quotient's multiple of the new divisor digit
    at weight r^-delta, then the digit times the divisor known so far
    (the adders from the residual_adder slot); the digit from the
    digit_select slot over the assimilated residual (its table built
    with the on-line terms' bound as extra estimate uncertainty); the
    quotient by on-the-fly conversion. The dividend bits beyond the
    quotient digits enter the residual at the end."""
    radix = 4 if _ipin(pins, "radix", 2) == 4 else 2
    k = 1 if radix == 2 else 2
    # the on-line delay: radix 2 needs 4 digits (at 3 the on-line terms use up the digit set's redundancy)
    delta = max(4 if radix == 2 else 3, min(5, _ipin(pins, "online_delay", 4)))
    fam = str(_pin(pins, "residual_adder.family", "ripple_carry"))
    fpins = _sub_pins(pins, "residual_adder.")
    norm = Norm(pins)
    m = Mod(name, "")
    m.port("input", "a", N)
    m.port("input", "b", D)
    m.port("output", "q", Q)
    m.port("output", "r", D)
    ax, NA = _dividend(m, N, S)
    dn, lzs, SW = norm.normalize(m, D, normalized)
    # the digit count: the Q quotient bits behind at least k leading zero bits, so the fraction x / d over
    # the QD-digit dividend is below r^-1 and the first residual lies inside the bound
    QD = -(-(Q + k) // k) * k
    NX = D + QD
    NW = NA + D
    m.wire("axw", NW, expr=f"{{{{{D}{{1'b0}}}}, {ax}}}")
    norm.scale(m, "axw", NW, lzs, "an", "the dividend scaled with the divisor", normalized)
    m.wire("xb", NX, expr=f"an[{NX-1}:0]" if NW >= NX else _zext("an", NW, NX))
    dd = delta * k                                             # the delay in bits
    LF = max(D, QD) + dd + k
    IBo = 3 if k == 1 else 4
    RW = IBo + LF
    # the residual in carry-save form: every stage's terms enter through 3:2 rows and only the estimate the
    # selection reads is assimilated (the on-line recurrence's point: no carry propagation per digit)
    m.wire("ws_0", RW, expr=f"{{{IBo}'b0, xb[{NX-1}:{NX-dd}], {LF-dd}'d0}}")
    m.wire("wc_0", RW, expr=f"{RW}'d0")
    m.wire("qq_0", QD, expr=f"{QD}'d0")
    m.wire("qmm_0", QD, expr=f"{{{QD}{{1'b1}}}}")
    a_dig = 1 if k == 1 else 2
    w = (a_dig + 1).bit_length() + 1
    # the on-line terms move the shifted residual by up to e = 2 (r - 1) r^-delta: the residual bound is
    # tightened to rho' d with rho' = rho - 2 (e + 2^-D) / (r - 1), which keeps the next residual inside
    # it for every reachable estimate (up to r rho' d + e)
    e_on = Fraction(2 * (radix - 1), radix ** delta)
    rho_on = Fraction(a_dig, radix - 1) - 2 * (e_on + Fraction(1, 1 << D)) / (radix - 1)
    sel = Selector(pins, radix, a_dig, D, rho_in=rho_on, rho_out=rho_on, unc_ulps=2, y_slack=e_on, IB=IBo)
    m.wire("dt_0", sel.dbits, expr=f"{dn}[{D-1}:{D-sel.dbits}]" if sel.dbits < D else dn)
    steps = QD // k
    ws, wc = "ws_0", "wc_0"
    for j in range(steps):
        known = min(D, (j + 1 + delta) * k)                    # divisor bits known at this stage
        m.wire(f"dk_{j}", RW, expr=f"{{{IBo}'b0, {dn}[{D-1}:{D-known}], {LF-known}'d0}}")
        # the new dividend digit at weight r^-delta and the partial quotient times the new divisor digit
        xi = (j + delta + 1) * k
        has_x = xi <= NX
        if has_x:
            m.wire(f"xterm_{j}", RW, expr=f"{{{IBo}'b0, xb[{NX-xi+k-1}:{NX-xi}], {LF-dd}'d0}}")
        di_hi = (j + delta + 1) * k
        has_q = di_hi <= D and j > 0
        if has_q:
            jb = j * k                                         # the partial quotient's bits so far
            sh = LF - dd - jb
            qv = f"{{{{({RW-jb-sh}){{1'b0}}}}, qq_{j}[{jb-1}:0], {sh}'d0}}" if sh > 0 else f"{{{{({RW-jb}){{1'b0}}}}, qq_{j}[{jb-1}:0]}}"
            if k == 1:
                m.wire(f"qd_{j}", RW, expr=f"{dn}[{D-di_hi}] ? {qv} : {RW}'d0")
            else:
                # the 2-bit divisor digit times the partial quotient: 0, Q, 2Q or 3Q (3Q through the adder)
                m.wire(f"q1_{j}", RW, expr=qv)
                m.wire(f"q2_{j}", RW, expr=f"q1_{j} << 1")
                m.wire(f"q3_{j}", RW)
                m.wire(f"q3c_{j}")
                m.add(fam, fpins, RW, f"q1_{j}", f"q2_{j}", "1'b0", f"q3_{j}", f"q3c_{j}", f"stage {j}: 3 Q for the divisor digit 3")
                dg = f"{dn}[{D-di_hi+1}:{D-di_hi}]"
                m.wire(f"qd_{j}", RW, expr=f"({dg} == 2'd3) ? q3_{j} : ({dg} == 2'd2) ? q2_{j} : ({dg} == 2'd1) ? q1_{j} : {RW}'d0")
        # v = r w + xterm - qd: the shifted pair and the two terms through 3:2 rows (the subtraction as the
        # complement with its one riding in the carry word's low end)
        m.wire(f"wsh_{j}", RW, expr=f"{{{ws}[{RW-1-k}:0], {k}'b0}}")
        m.wire(f"wch_{j}", RW, expr=f"{{{wc}[{RW-1-k}:0], {k}'b0}}")
        vs, vc = f"wsh_{j}", f"wch_{j}"
        if has_x:
            _csa(m, f"xs_{j}", f"xc_{j}", RW, vs, vc, f"xterm_{j}", "1'b0")
            vs, vc = f"xs_{j}", f"xc_{j}"
        if has_q:
            m.wire(f"nqd_{j}", RW, expr=f"~qd_{j}")
            _csa(m, f"qs_{j}", f"qc_{j}", RW, vs, vc, f"nqd_{j}", "1'b1")
            vs, vc = f"qs_{j}", f"qc_{j}"
        # the digit from the selection slot over the estimate its own adder assimilates
        y = sel.estimate(m, f"{j}", vs, vc, RW, "dt_0")
        dsel = sel.digit_from_estimate(m, f"{j}", y, "dt_0", vs, vc, RW)
        # w' = v - dsel d[j], the multiple through one more 3:2 row
        if a_dig == 2:
            m.wire(f"dk2_{j}", RW, expr=f"dk_{j} << 1")
            m.wire(f"mult_{j}", RW, expr=f"({dsel} == {w}'sd2 || {dsel} == -{w}'sd2) ? dk2_{j} : ({dsel} == {w}'sd0) ? {RW}'d0 : dk_{j}")
        else:
            m.wire(f"mult_{j}", RW, expr=f"({dsel} == {w}'sd0) ? {RW}'d0 : dk_{j}")
        m.wire(f"addv_{j}", RW, expr=f"({dsel} > {w}'sd0) ? ~mult_{j} : mult_{j}")
        _csa(m, f"ws_{j+1}", f"wc_{j+1}", RW, vs, vc, f"addv_{j}", f"({dsel} > {w}'sd0)")
        ws, wc = f"ws_{j+1}", f"wc_{j+1}"
        _otf_step(m, f"{j+1}", QD, k, dsel, w, f"qq_{j}", f"qmm_{j}")
    # the dividend digits not yet consumed complete the residual, then the pair is assimilated once
    rest = NX - (QD + dd)
    if rest > 0:
        tailw = f"{{{{({RW}-{rest}-{LF-D}){{1'b0}}}}, xb[{rest-1}:0], {LF-D}'d0}}" if LF - D > 0 else f"{{{{({RW}-{rest}){{1'b0}}}}, xb[{rest-1}:0]}}"
        m.wire("tail", RW, expr=tailw)
        _csa(m, "wts", "wtc", RW, ws, wc, "tail", "1'b0")
        ws, wc = "wts", "wtc"
    m.wire("wt", RW)
    m.wire("wtco")
    m.add(fam, fpins, RW, ws, wc, "1'b0", "wt", "wtco", "the final residual assimilated")
    m.wire("dnf", RW, signed=True, expr=f"$signed({{{IBo}'b0, {dn}, {LF-D}'d0}})" if LF > D else f"$signed({{{IBo}'b0, {dn}}})")
    m.wire("wneg", expr=f"wt[{RW-1}]")
    m.wire("wsub", RW)
    m.sub(fam, fpins, RW, "wt", "dnf", "wsub", "wover", "the residual against the divisor")
    m.wire("wadd", RW)
    m.wire("waddc")
    m.add(fam, fpins, RW, "wt", "dnf", "1'b0", "wadd", "waddc", "the divisor added back to a negative residual")
    m.wire("qinc", QD)
    m.wire("qincc")
    m.wire("zeroq", QD, expr=f"{QD}'d0")
    m.add(fam, fpins, QD, f"qq_{steps}", "zeroq", "1'b1", "qinc", "qincc", "the quotient plus one")
    m.wire("qf", QD, expr=f"wneg ? qmm_{steps} : (wover ? qinc : qq_{steps})")
    m.wire("rf", RW, expr="wneg ? wadd : (wover ? wsub : wt)")
    m.wire("rr", D, expr=f"rf[{LF-1}:{LF-D}]")
    norm.descale(m, "rr", D, lzs, "rds", "the remainder de-scaled", normalized)
    m.assign("q", f"qf[{Q-1}:0]")
    m.assign("r", "rds")
    m.comment = (f"on-line MSDF divider (radix {radix}, on-line delay {delta}): the operand digits consumed one per stage, "
                 f"the digit by {sel.describe()}, the quotient converted on the fly")
    return name, m.render()


# ---- the seed tables --------------------------------------------------------------------
class _Fn:
    """The function a seed approximates over the normalized operand x
    (src / 2^W): the reciprocal on [1/2, 1) with one known leading one,
    or the reciprocal square root on [1/4, 1); both range in (1, 2]."""

    def __init__(self, kind: str):
        self.kind = kind
        self.lead = 1 if kind == "reciprocal" else 0
        self.lo = Fraction(1, 2) if kind == "reciprocal" else Fraction(1, 4)

    def val(self, x: Fraction) -> Fraction:
        if self.kind == "reciprocal":
            return 1 / x
        return Fraction(1 / math.sqrt(float(x)))

    def d1(self, x: Fraction) -> Fraction:
        if self.kind == "reciprocal":
            return -1 / (x * x)
        return Fraction(-0.5 * float(x) ** -1.5)

    def d2(self, x: Fraction) -> Fraction:
        if self.kind == "reciprocal":
            return 2 / (x * x * x)
        return Fraction(0.75 * float(x) ** -2.5)

    def rel(self, v: Fraction, x: Fraction) -> float:
        """The relative error of the approximation v at x."""
        return abs(float(v / self.val(x)) - 1.0)


def _fix(v: Fraction, P: int) -> int:
    """v in (0, 2) as a P-bit value with P-1 fraction bits, rounded."""
    return max(0, min((1 << P) - 1, int(round(v * (1 << (P - 1))))))


class Seed:
    """The seed slot's pins: the family, its table widths and its
    component slots (mul, sum_adder)."""

    def __init__(self, pins: dict, prefix: str, default_family: str, default_kin: int = 6):
        # every key is looked up on the pins the caller passed (a slot's family is chosen by the key that
        # names it, which is what the pin log records), the sub-dictionary carries the component's own pins
        self.family = str(_pin(pins, prefix + "family", default_family))
        sp = _sub_pins(pins, prefix)
        self.sp = sp
        self.kin = max(1, _ipin(pins, prefix + "input_bits", default_kin))
        self.out_bits = _ipin(pins, prefix + "output_bits", 0)
        self.guard = max(0, min(3, _ipin(pins, prefix + "guard_bits", 0)))
        self.mul = str(_pin(pins, prefix + "mul.family", "behavioral_star"))
        self.mul_pins = _sub_pins(sp, "mul.")
        self.add = str(_pin(pins, prefix + "sum_adder.family", "ripple_carry"))
        self.add_pins = _sub_pins(sp, "sum_adder.")
        self.pinned_degree = _pin(pins, prefix + "degree", None) is not None
        # the consumer's adder, which sums the Boolean partial-product rows of a seed synthesized inside the
        # multiplier array (that family has no adder slot of its own)
        self.ext_add: tuple | None = None

    def raise_degree(self) -> bool:
        """Raise a polynomial seed's degree by one (up to the space's 2) when
        widening its index is not enough; False when there is no degree
        left to raise. A degree the caller pinned is left alone."""
        if self.family != "poly_seed" or self.pinned_degree:
            return False
        d = max(1, min(2, _ipin(self.sp, "degree", 1)))
        if d >= 2:
            return False
        self.sp["degree"] = d + 1
        return True

    def P_of(self, base: int) -> int:
        """The seed's output precision: the family's natural width, raised to
        output_bits, plus the guard bits."""
        return max(base, min(24, self.out_bits)) + self.guard


def seed_sv(m: Mod, seed, *args) -> tuple:
    """out = fn(x) from the top bits of src as a P-bit value with one
    integer bit; returns (P, the seed's maximum relative error over the
    domain, evaluated at generation: exactly per cell for the table
    families, by a Taylor bound for the polynomial ones). Called as
    seed_sv(m, Seed, src, W, kin, out, fn), or with the family name and
    its pins in place of the Seed (approx.py's form)."""
    if isinstance(seed, str):
        pins, src, W, kin, out, fn = args
        return _seed_sv(m, Seed(pins or {}, "", seed), src, W, kin, out, fn)
    return _seed_sv(m, seed, *args)


def _seed_sv(m: Mod, seed: Seed, src: str, W: int, kin: int, out: str, fn: _Fn) -> tuple:
    family = seed.family
    kin = max(1, min(kin, W - fn.lead))
    lead = fn.lead
    cellw = Fraction(1, 1 << (kin + lead))

    def cell(i: int, bits: int = kin):
        lo = Fraction(lead, 2) + Fraction(i, 1 << (bits + lead))
        return lo, lo + Fraction(1, 1 << (bits + lead))

    def used(i: int, bits: int = kin) -> bool:
        return cell(i, bits)[1] > fn.lo

    if family == "magic_constant_bit_seed":
        # the table-free seed y0 = R - (m >> s) on the operand's significand m (its leading one at the top):
        # slope -1 for the reciprocal, -1/2 for the reciprocal square root, whose radicand of odd exponent
        # (top bit clear) takes m = 2x and the constant of that parity, as the reinterpreted float's exponent
        # halving does; R by a minimax search at generation on the seed's own error (zeroth_error_minimax)
        # or on the error after one Newton step (correction_aware_minimax); the word carries two integer
        # bits during the subtraction and saturates at 2 - ulp
        P = seed.P_of(10)
        s = 0 if fn.kind == "reciprocal" else 1
        aware = str(_pin(seed.sp, "magic_constant_selection", "zeroth_error_minimax")) == "correction_aware_minimax"
        segs = [(Fraction(1, 2), Fraction(1), 0)]
        if fn.kind != "reciprocal":
            segs.append((Fraction(1, 4), Fraction(1, 2), 1))

        def grid_of(lo, hi):
            return [lo + (hi - lo) * Fraction(g, 256) for g in range(257)]

        def err_of(R: Fraction, lo, hi, e: int) -> float:
            worst = 0.0
            for x in grid_of(lo, hi):
                y0 = R - x * (1 << e) / (1 << s)
                if y0 <= 0:
                    return 9.0
                if aware:
                    err = 1 - y0 * x if fn.kind == "reciprocal" else 1 - x * y0 * y0
                    y1 = y0 * (1 + err) if fn.kind == "reciprocal" else y0 * (1 + err / 2)
                    worst = max(worst, fn.rel(y1, x))
                else:
                    worst = max(worst, fn.rel(y0, x))
            return worst

        Rs = []
        eps = 0.0
        for lo_x, hi_x, e in segs:
            lo, hi = Fraction(1), Fraction(3)
            best = None
            for _step in range(3):
                n = 64
                cands = [lo + (hi - lo) * Fraction(g, n) for g in range(n + 1)]
                errs = [(err_of(c, lo_x, hi_x, e), c) for c in cands]
                _e, c = min(errs)
                best = c
                lo, hi = c - (hi - lo) / n, c + (hi - lo) / n
            Rf = int(round(best * (1 << (P - 1))))
            Rs.append(Rf)
            Rq = Fraction(Rf, 1 << (P - 1))
            eps = max(eps, max(fn.rel(min(Rq - x * (1 << e) / (1 << s), 2 - Fraction(1, 1 << (P - 1))), x) for x in grid_of(lo_x, hi_x)))
        if len(segs) == 2:
            m.wire(f"{out}_e", expr=f"~{src}[{W-1}]")
            m.wire(f"{out}_m", W, expr=f"{out}_e ? {{{src}[{W-2}:0], 1'b0}} : {src}")
            msrc = f"{out}_m"
        else:
            msrc = src
        m.wire(f"{out}_x", P + 1, expr=f"{{2'b0, {msrc}[{W-1}:{W-P+1}]}}" if W >= P - 1 else f"{{2'b0, {msrc}, {P-1-W}'d0}}")
        m.wire(f"{out}_sh", P + 1, expr=f"{out}_x >> {s}" if s else f"{out}_x")
        if len(segs) == 2:
            m.wire(f"{out}_r", P + 1, expr=f"{out}_e ? {P+1}'d{Rs[1]} : {P+1}'d{Rs[0]}")
        else:
            m.wire(f"{out}_r", P + 1, expr=f"{P+1}'d{Rs[0]}")
        m.wire(f"{out}_y", P + 1)
        m.sub(seed.add, seed.add_pins, P + 1, f"{out}_r", f"{out}_sh", f"{out}_y", f"{out}_c",
              f"the magic-constant seed R - (m >> {s}) ({'correction-aware' if aware else 'zeroth-error'} minimax R)")
        m.wire(out, P, expr=f"{out}_y[{P}] ? {{{P}{{1'b1}}}} : {out}_y[{P-1}:0]")
        return P, eps * 1.02 + 2.0 ** -(P - 2)
    m.wire(f"{out}_i", kin, expr=f"{src}[{W-1-lead}:{W-lead-kin}]")
    eps = 0.0
    if family == "monolithic_rom" or (family in ("bipartite_rom", "symmetric_bipartite", "multipartite") and kin < 3):
        P = seed.P_of(kin + 4)
        entries = []
        for i in range(1 << kin):
            lo, hi = cell(i)
            v = _fix(fn.val((lo + hi) / 2), P) if used(i) else (1 << (P - 1))
            entries.append(v)
            if used(i):
                vq = Fraction(v, 1 << (P - 1))
                eps = max(eps, fn.rel(vq, max(lo, fn.lo)), fn.rel(vq, hi))
        m.rom(f"T_{out}", entries, P, f"{out}_i", out, f"the {fn.kind} seed table ({family}, {kin} input bits, {P} output bits)")
        return P, eps
    if family in ("bipartite_rom", "symmetric_bipartite", "multipartite"):
        # the index split x0 | x1 | x2 (| x3 ...): T0(x0, x1) holds the value at the centre of the x1 cell,
        # T_k(x0, x_k) the slope at the centre of the x0 cell times the x_k offset; the symmetric table
        # folds the offset's sign, the multipartite one keeps one slope table per finer part; the table
        # outputs are summed through the sum_adder family
        ntab = max(3, min(6, _ipin(seed.sp, "tables", 3))) if family == "multipartite" else 2  # noqa: E501
        n0 = max(1, kin // (ntab + 1))
        rest = kin - n0
        widths = [n0] + [rest // ntab + (1 if k < rest % ntab else 0) for k in range(ntab)]
        widths = [w for w in widths if w > 0]
        nparts = len(widths)
        P = seed.P_of(kin + 4)
        offs = []
        pos = kin
        for w in widths:
            pos -= w
            offs.append(pos)
        for k, w in enumerate(widths):
            m.wire(f"{out}_x{k}", w, expr=f"{out}_i[{offs[k]+w-1}:{offs[k]}]")
        w01 = widths[0] + widths[1]
        t0 = []
        for i in range(1 << w01):
            lo, hi = cell(i, w01)
            t0.append(_fix(fn.val((lo + hi) / 2), P) if used(i, w01) else (1 << (P - 1)))
        m.wire(f"{out}_i01", w01, expr=f"{out}_i[{kin-1}:{kin-w01}]")
        m.rom(f"T0_{out}", t0, P, f"{out}_i01", f"{out}_t0", f"the {fn.kind} seed table of values ({family}, {w01} bits)")
        SW = P + 3
        acc = m.wire(f"{out}_acc0", SW, expr=f"{{3'b0, {out}_t0}}")
        slopes = {}
        for k in range(2, nparts):
            wk = widths[k]
            unit = Fraction(1, 1 << (kin - offs[k] + lead))
            sym = family == "symmetric_bipartite" and wk >= 2
            tk = []
            for i0 in range(1 << widths[0]):
                lo0, hi0 = cell(i0, widths[0])
                slope = fn.d1((lo0 + hi0) / 2)
                for xk in range(1 << wk):
                    off = (Fraction(xk) + Fraction(1, 2) - (1 << (wk - 1))) * unit
                    v = int(round(slope * off * (1 << (P - 1))))
                    slopes[(k, i0, xk)] = v
                    if not sym or xk < (1 << (wk - 1)):
                        tk.append(abs(v) if sym else v)
            if sym:
                m.wire(f"{out}_f{k}", wk - 1, expr=f"{out}_x{k}[{wk-1}] ? ~{out}_x{k}[{wk-2}:0] : {out}_x{k}[{wk-2}:0]")
                m.rom(f"T{k}_{out}", tk, P + 1, f"{{{out}_x0, {out}_f{k}}}", f"{out}_m{k}",
                      f"the folded slope table (symmetric bipartite, part {k})")
                m.wire(f"{out}_t{k}", SW, expr=f"{out}_x{k}[{wk-1}] ? -{{{SW - P - 1}'b0, {out}_m{k}}} : {{{SW - P - 1}'b0, {out}_m{k}}}")
            else:
                m.rom(f"T{k}_{out}", tk, P + 2, f"{{{out}_x0, {out}_x{k}}}", f"{out}_s{k}",
                      f"the slope table (part {k}, {widths[0] + wk} index bits)")
                m.wire(f"{out}_t{k}", SW, expr=f"{{{{{SW - P - 2}{{{out}_s{k}[{P+1}]}}}}, {out}_s{k}}}")
            nacc = m.wire(f"{out}_acc{k-1}", SW)
            m.add(seed.add, seed.add_pins, SW, acc, f"{out}_t{k}", "1'b0", nacc, f"{out}_accc{k-1}", f"the seed's table sum (part {k})")
            acc = nacc
        m.wire(out, P, expr=f"(|{acc}[{SW-1}:{P}]) ? {{{P}{{1'b1}}}} : {acc}[{P-1}:0]")
        for i in range(1 << kin):
            if not used(i):
                continue
            lo, hi = cell(i)
            v = Fraction(t0[i >> (kin - w01)], 1 << (P - 1))
            i0 = i >> (kin - widths[0])
            for k in range(2, nparts):
                xk = (i >> offs[k]) & ((1 << widths[k]) - 1)
                sv = slopes[(k, i0, xk)]
                if family == "symmetric_bipartite" and widths[k] >= 2:
                    mirror = xk if xk < (1 << (widths[k] - 1)) else (1 << widths[k]) - 1 - xk
                    sv = abs(slopes[(k, i0, mirror)]) * (-1 if xk >= (1 << (widths[k] - 1)) else 1)
                v += Fraction(sv, 1 << (P - 1))
            eps = max(eps, fn.rel(v, max(lo, fn.lo)), fn.rel(v, hi))
        return P, eps
    if family == "operand_modification_multiply":
        # x0 = T(x_hi) (2 mid' - x) with the modified operand {x_hi, ~x_lo} (mid' the cell centre less
        # half a unit) and T = 1/mid'^2: the product through the seed's multiplier slot, or as the
        # Boolean partial-product rows of T times the modified operand summed by a carry-save tree
        if fn.kind != "reciprocal":
            raise ValueError("operand_modification_multiply seeds the reciprocal only")
        synth = str(_pin(seed.sp, "seed_synthesis", "modified_operand_product"))
        PT = 2 * kin + 5
        low = W - lead - kin
        tv = []
        for i in range(1 << kin):
            lo, hi = cell(i)
            midp = (lo + hi) / 2 - Fraction(1, 1 << (W + 1))
            tv.append(int(round((1 / (midp * midp)) * (1 << (PT - 3)))))
        m.rom(f"T_{out}", tv, PT, f"{out}_i", f"{out}_t", "the table of 1/mid'^2 (operand modification)")
        m.wire(f"{out}_dm", W, expr=f"{{{src}[{W-1}:{low}], ~{src}[{low-1}:0]}}" if low > 0 else src)
        if synth == "modified_operand_product":
            m.umul(seed.mul, seed.mul_pins, f"{out}_t", PT, f"{out}_dm", W, f"{out}_p", "the seed product T(x_hi) (2 mid' - x)")
        else:
            # the partial-product rows of the table word gated by the operand bits, reduced by 3:2 rows and
            # the datapath's adder (the seed synthesized inside the multiplier array has no adder of its own)
            rows = [m.wire(f"{out}_pp{b}", PT + W, expr=(f"{out}_dm[{b}] ? {{{{{W - b}{{1'b0}}}}, {out}_t, {b}'d0}}" if b else
                                                          f"{out}_dm[{b}] ? {{{{{W}{{1'b0}}}}, {out}_t}}") + f" : {PT + W}'d0")
                    for b in range(W)]
            lvl = 0
            while len(rows) > 2:
                nxt = []
                for g in range(0, len(rows) - 2, 3):
                    x1, x2, x3 = rows[g:g + 3]
                    s_ = m.wire(f"{out}_cs{lvl}_{g}", PT + W, expr=f"{x1} ^ {x2} ^ {x3}")
                    c_ = m.wire(f"{out}_cc{lvl}_{g}", PT + W, expr=f"{{(({x1}[{PT+W-2}:0] & {x2}[{PT+W-2}:0]) | ({x1}[{PT+W-2}:0] & {x3}[{PT+W-2}:0]) | ({x2}[{PT+W-2}:0] & {x3}[{PT+W-2}:0])), 1'b0}}")
                    nxt += [s_, c_]
                nxt += rows[len(rows) - len(rows) % 3:]
                rows = nxt
                lvl += 1
            if len(rows) == 1:
                m.wire(f"{out}_p", PT + W, expr=rows[0])
            else:
                afam, apins = seed.ext_add or (seed.add, seed.add_pins)
                m.wire(f"{out}_p", PT + W)
                m.add(afam, apins, PT + W, rows[0], rows[1], "1'b0", f"{out}_p", f"{out}_pc",
                      "the seed's partial-product rows summed by the datapath's adder")
        P = seed.P_of(2 * kin + 4)
        FB = PT - 3 + W
        m.wire(f"{out}_v", P, expr=f"{out}_p[{FB}:{FB - P + 1}]" if FB - P + 1 >= 0 else f"{{{out}_p[{FB}:0], {P - 1 - FB}'d0}}")
        m.wire(out, P, expr=f"(|{out}_p[{PT + W - 1}:{FB + 1}]) ? {{{P}{{1'b1}}}} : {out}_v")
        for i in range(1 << kin):
            lo, hi = cell(i)
            midp = (lo + hi) / 2 - Fraction(1, 1 << (W + 1))
            T = Fraction(tv[i], 1 << (PT - 3))
            for x in (lo, hi, midp):
                eps = max(eps, fn.rel(T * (2 * midp - x), x))
        return P, eps + 2.0 ** -(P - 1)
    if family == "poly_seed":
        # a Taylor polynomial of degree 1 or 2 at each cell's centre on the offset t = x - centre (its low
        # bits beyond tail_bits dropped); the slope term through the multiplier slot on a signed offset, or
        # from the slope's radix-8 Booth digits pre-decoded in the table (shift-add rows, no recoder)
        deg = max(1, min(2, _ipin(seed.sp, "degree", 1)))
        enc = str(_pin(seed.sp, "slope_encoding", "plain"))
        P = seed.P_of((deg + 1) * (kin + 1) + 4)
        low = W - lead - kin
        tail = max(1, min(_ipin(seed.sp, "tail_bits", 16), low)) if low > 0 else 0
        TW = max(2, tail)                                     # the offset wire (a one-bit offset sign-extended)
        c0, c1, c2 = [], [], []
        for i in range(1 << kin):
            lo, hi = cell(i)
            mid = (lo + hi) / 2
            c0.append(_fix(fn.val(mid), P))
            c1.append(int(round(-fn.d1(mid) * (1 << (P - 1)))))
            c2.append(int(round(fn.d2(mid) / 2 * (1 << (P - 1)))))
        m.rom(f"C0_{out}", c0, P, f"{out}_i", f"{out}_c0", "the polynomial constant table")
        C1W = max(1, max(c1).bit_length())                     # the slope magnitude's width (P - 1 fraction bits)
        C2W = max(1, max(c2).bit_length())                     # the curvature's
        if low > 0:
            # the signed offset: the top tail bits of the low field less the half cell (its top bit flipped)
            m.wire(f"{out}_t", TW, signed=True, expr=f"{{~{src}[{low-1}], {src}[{low-2}:{low-tail}]}}" if tail > 1 else f"{{2{{~{src}[{low-1}]}}}}")
            drop = low - tail                                   # the offset bits dropped
            SW = C1W + 1 + TW
            if enc == "booth_radix8_decoded":
                # the slope's magnitude in radix-8 Booth digits (-4..4) stored per digit: the product is the
                # sum of the digit-weighted offset rows (shifts and negations), no recoder on the path
                nd = (C1W + 3) // 3
                dig_tab = [[] for _ in range(nd)]
                for v in c1:
                    digs = []
                    x = v
                    for _d in range(nd):
                        low3 = x & 7
                        d = low3 if low3 < 4 else low3 - 8
                        digs.append(d)
                        x = (x - d) >> 3
                    for k in range(nd):
                        dig_tab[k].append(digs[k] & 7)
                rows = []
                for k in range(nd):
                    m.rom(f"B{k}_{out}", dig_tab[k], 3, f"{out}_i", f"{out}_b{k}", f"the slope's Booth digit {k}")
                    m.wire(f"{out}_bd{k}", 4, signed=True, expr=f"{{{out}_b{k}[2], {out}_b{k}}}")
                    r = m.wire(f"{out}_row{k}", SW, signed=True,
                               expr=f"(({out}_bd{k} == 4'sd4 || {out}_bd{k} == -4'sd4) ? ($signed({out}_t) <<< 2) : "
                                    f"({out}_bd{k} == 4'sd2 || {out}_bd{k} == -4'sd2) ? ($signed({out}_t) <<< 1) : "
                                    f"({out}_bd{k} == 4'sd3 || {out}_bd{k} == -4'sd3) ? (($signed({out}_t) <<< 1) + $signed({out}_t)) : "
                                    f"({out}_bd{k} == 4'sd0) ? {SW}'sd0 : $signed({out}_t)) <<< {3 * k}")
                    rows.append(m.wire(f"{out}_srow{k}", SW, signed=True, expr=f"{out}_bd{k}[3] ? -{r} : {r}"))
                acc = rows[0]
                for k in range(1, nd):
                    nacc = m.wire(f"{out}_sacc{k}", SW, signed=True)
                    m.add(seed.add, seed.add_pins, SW, acc, rows[k], "1'b0", nacc, f"{out}_saccc{k}", f"the slope rows summed ({k})")
                    acc = nacc
                m.wire(f"{out}_p1", SW, signed=True, expr=acc)
            else:
                m.rom(f"C1_{out}", c1, C1W, f"{out}_i", f"{out}_c1", "the slope magnitude table")
                m.wire(f"{out}_c1s", C1W + 1, signed=True, expr=f"$signed({{1'b0, {out}_c1}})")
                m.umul(seed.mul, seed.mul_pins, f"{out}_c1s", C1W + 1, f"{out}_t", TW, f"{out}_p1", "the slope term c1 t (signed)", signed=True)
            # the slope is negative: the term is subtracted; the offset's weight is 2^-(W - drop) of one
            m.wire(f"{out}_s1", SW + 2, signed=True, expr=f"-$signed({{{{2{{{out}_p1[{SW-1}]}}}}, {out}_p1}})")
            shift1 = W - drop
            m.wire(f"{out}_s1s", SW + 2, signed=True, expr=f"{out}_s1 >>> {shift1}")
            term = f"{out}_s1s"
            sum_w = P + 4
            m.wire(f"{out}_c0s", sum_w, signed=True, expr=f"$signed({{{sum_w - P}'b0, {out}_c0}})")
            m.wire(f"{out}_t1", sum_w, signed=True, expr=f"{term}[{sum_w-1}:0]" if SW + 2 >= sum_w else f"$signed({term})")
            m.wire(f"{out}_sum1", sum_w)
            m.add(seed.add, seed.add_pins, sum_w, f"{out}_c0s", f"{out}_t1", "1'b0", f"{out}_sum1", f"{out}_sum1c", "the constant plus the slope term")
            if deg == 2:
                m.rom(f"C2_{out}", c2, C2W, f"{out}_i", f"{out}_c2", "the curvature table")
                m.umul(seed.mul, seed.mul_pins, f"{out}_t", TW, f"{out}_t", TW, f"{out}_tt", "the offset squared", signed=True)
                m.wire(f"{out}_c2s", C2W + 1, signed=True, expr=f"$signed({{1'b0, {out}_c2}})")
                m.umul(seed.mul, seed.mul_pins, f"{out}_c2s", C2W + 1, f"{out}_tt", 2 * TW, f"{out}_p2", "the curvature term c2 t^2", signed=True)
                m.wire(f"{out}_p2s", C2W + 1 + 2 * TW, signed=True, expr=f"{out}_p2 >>> {2 * shift1}")
                m.wire(f"{out}_t2", sum_w, signed=True, expr=f"{out}_p2s[{sum_w-1}:0]" if C2W + 1 + 2 * TW >= sum_w else f"$signed({out}_p2s)")
                m.wire(f"{out}_sum2", sum_w)
                m.add(seed.add, seed.add_pins, sum_w, f"{out}_sum1", f"{out}_t2", "1'b0", f"{out}_sum2", f"{out}_sum2c", "plus the curvature term")
                m.wire(out, P, expr=f"(|{out}_sum2[{sum_w-1}:{P}]) ? {{{P}{{1'b1}}}} : {out}_sum2[{P-1}:0]")
            else:
                m.wire(out, P, expr=f"(|{out}_sum1[{sum_w-1}:{P}]) ? {{{P}{{1'b1}}}} : {out}_sum1[{P-1}:0]")
        else:
            m.wire(out, P, expr=f"{out}_c0")
            drop = 0
        h = float(cellw / 2)
        x0 = float(max(fn.lo, cell(0)[0]))
        if fn.kind == "reciprocal":
            rem = h ** (deg + 1) / x0 ** (deg + 1)
        else:
            rem = h ** (deg + 1) * (0.75 if deg == 1 else 1.875) / x0 ** (deg + 1)
        # the dropped offset bits shift the point by less than 2^-(W - drop) relative
        eps = rem * 1.1 + 2.0 ** -(P - 1) * 2 + (2.0 ** -(W - drop - 1) * 4 if drop else 0.0)
        return P, eps
    raise ValueError(f"no seed of the family {family}")


# ---- the functional dividers ----------------------------------------------------------
class Rounding:
    """The final_round slot's pins: the family, the candidate count, the
    back-multiply product width and the correction adder."""

    def __init__(self, pins: dict):
        self.family = str(_pin(pins, "final_round.family", "back_multiply_remainder"))
        sp = _sub_pins(pins, "final_round.")
        self.candidates = max(2, min(3, _ipin(pins, "final_round.quotient_candidates", 3)))
        self.low_bits = str(_pin(pins, "final_round.product_bits", "full")) == "low_bits_sufficient"
        self.add = str(_pin(pins, "final_round.correction_adder.family", "ripple_carry"))
        self.add_pins = _sub_pins(sp, "correction_adder.")
        self.exact = self.family in ("exclusion_zone_proof", "extra_precision_quotient")


def _functional_sv(N: int, S: int, D: int, Q: int, family: str, pins: dict, name: str, normalized: bool) -> tuple:
    """newton_raphson | goldschmidt | direct_polynomial | prescaled_very_high_radix | svoboda_tung."""
    prescaled = family in ("prescaled_very_high_radix", "svoboda_tung")
    seed = Seed(pins, "approximator." if family == "direct_polynomial" else "seed.",
                "poly_seed" if family == "direct_polynomial" else "monolithic_rom")
    if seed.family not in SEED_FAMILIES:
        raise ValueError(f"{family}: no seed of the family {seed.family!r}")
    if family == "direct_polynomial" and seed.family != "poly_seed":
        raise ValueError("direct_polynomial: the approximator is a polynomial seed")
    mul_key = "prescaler." if prescaled else ("final_mul." if family == "direct_polynomial" else "iter_mult.")
    mul_fam = str(_pin(pins, mul_key + "family", "behavioral_star"))
    mul_pins = _sub_pins(pins, mul_key)
    if family == "direct_polynomial":
        # the feed-forward divider's one refinement step adds through the polynomial's own adder
        add_fam, add_pins = seed.add, seed.add_pins
    elif family in ("newton_raphson", "goldschmidt"):
        add_fam = str(_pin(pins, "iter_add.family", "ripple_carry"))
        add_pins = _sub_pins(pins, "iter_add.")
    else:
        add_fam = str(_pin(pins, "residual_adder.family", "ripple_carry"))
        add_pins = _sub_pins(pins, "residual_adder.")
    seed.ext_add = (add_fam, add_pins)
    guard = max(0, _ipin(pins, "internal_guard_bits", 4)) if family in ("newton_raphson", "goldschmidt") else 4
    rnd = Rounding(pins) if not prescaled else None
    exact = bool(rnd and rnd.exact)
    order = 3 if family == "newton_raphson" and _ipin(pins, "iteration_order", 2) >= 3 else 2
    round_intermediates = family == "goldschmidt" and not _bpin(pins, "truncated_intermediate_multiplies", True)
    if family == "prescaled_very_high_radix":
        kb = max(2, min(Q, _ipin(pins, "bits_per_iteration", 8)))
        prec = max(6, min(16, _ipin(pins, "prescaling_precision_bits", 8)))
    elif family == "svoboda_tung":
        kb = _clog2(max(4, _ipin(pins, "radix", 4)))
        prec = kb + 2
    else:
        kb, prec = 2, 4
    recode = family == "svoboda_tung" and str(_pin(pins, "msd_recoding", "none")) == "two_digit_recode"
    composition = str(_pin(pins, "composition", "polynomial_only")) if family == "direct_polynomial" else ""
    fn = _Fn("reciprocal")
    norm = Norm(pins)
    m = Mod(name, "")
    m.port("input", "a", N)
    m.port("input", "b", D)
    m.port("output", "q", Q)
    m.port("output", "r", D)
    ax, NA = _dividend(m, N, S)
    dn, lzs, SW = norm.normalize(m, D, normalized)
    NW = NA + D
    m.wire("axw", NW, expr=f"{{{{{D}{{1'b0}}}}, {ax}}}")
    norm.scale(m, "axw", NW, lzs, "an", "the dividend scaled with the divisor", normalized)
    need = Q + D + 3 if exact else Q + 1 + (1 if rnd and rnd.candidates == 2 else 0)
    if exact and rnd.family == "extra_precision_quotient":
        need += 2                                          # the truncated estimate is exact without a rounding step
    kin = max(seed.kin, prec) if prescaled else seed.kin
    # the unrolled step count: the iterations pin when given (the seed then widened until that many steps
    # reach the target), else the fewest steps the seed needs; the feed-forward divider runs its polynomial
    # alone (the seed widened to the target) or one refinement step
    want_steps = None
    if family in ("newton_raphson", "goldschmidt"):
        want_steps = _ipin(pins, "iterations", 0) or None
    elif family == "direct_polynomial":
        want_steps = 0 if composition == "polynomial_only" else 1
    F = None

    def after(eps: float, n: int, F: int) -> float:
        for _s in range(n):
            eps = eps ** order + 3 * 2.0 ** -F
        return eps

    while True:
        P, eps0 = seed_sv(Mod("probe", ""), seed, "dn", D, kin, "x0", fn)
        F = max(need + guard + 2, D, P - 1)
        if prescaled:
            ok = eps0 <= 2.0 ** -(kb + 2)
        elif want_steps is not None:
            ok = after(eps0, want_steps, F) <= 2.0 ** -need
        else:
            ok = True
        if ok:
            break
        if kin < D - 1:
            kin += 1
        elif seed.raise_degree():
            kin = seed.kin                                     # a higher degree reaches further per cell
        elif prescaled and kb > 2:
            kb -= 1
        else:
            raise ValueError(f"{family}: no seed of {seed.family} at up to {D - 1} input bits meets the "
                             f"{'digit set' if prescaled else f'{want_steps} iteration(s)'}")
    P, eps0 = seed_sv(m, seed, "dn", D, kin, "x0", fn)
    XWd = F + 2
    m.wire("x0w", XWd, expr=f"{{2'b0, x0}} << {F - (P - 1)}" if F > P - 1 else (f"{{2'b0, x0}}" if F == P - 1 else f"{{2'b0, x0[{P-1}:{P-1-F}]}}"))
    m.wire("dnw", XWd, expr=f"{{2'b0, dn}} << {F - D}" if F > D else "{2'b0, dn}")
    steps = 0
    target = 2.0 ** -need
    if not prescaled:
        if want_steps is not None:
            steps = want_steps
        else:
            while after(eps0, steps, F) > target and steps < 8:
                steps += 1
        if after(eps0, steps, F) > target:
            raise ValueError(f"{family}: the iteration does not reach 2^-{need} from a seed error of {eps0:.3g}")
    x = "x0w"
    desc = ""
    two = m.wire("two", XWd, expr=f"{{2'b10, {F}'d0}}")

    def trunc_or_round(prod: str, out: str, hi: int, lo: int, comment: str) -> str:
        """The product at F fraction bits: truncated, or rounded to nearest through the iteration adder."""
        if not round_intermediates:
            return m.wire(out, XWd, expr=f"{prod}[{hi}:{lo}]")
        m.wire(f"{out}_t", XWd, expr=f"{prod}[{hi}:{lo}]")
        m.wire(f"{out}_z", XWd, expr=f"{XWd}'d0")
        m.wire(out, XWd)
        m.add(add_fam, add_pins, XWd, f"{out}_t", f"{out}_z", f"{prod}[{lo-1}]", out, f"{out}_c", comment + " (rounded)")
        return out

    if family in ("newton_raphson", "direct_polynomial"):
        for k in range(steps):
            m.umul(mul_fam, mul_pins, x, XWd, "dnw", XWd, f"dx_{k}", f"Newton step {k+1}: d x")
            m.wire(f"dxf_{k}", XWd, expr=f"dx_{k}[{2*F+1}:{F}]")
            m.wire(f"f_{k}", XWd)
            m.sub(add_fam, add_pins, XWd, "two", f"dxf_{k}", f"f_{k}", f"fc_{k}", f"Newton step {k+1}: 2 - d x")
            if order == 3:
                # x (1 + e + e^2) with e = 1 - d x: the cubic step
                m.wire(f"one_{k}", XWd, expr=f"{{2'b01, {F}'d0}}")
                m.wire(f"e_{k}", XWd)
                m.sub(add_fam, add_pins, XWd, f"one_{k}", f"dxf_{k}", f"e_{k}", f"ec_{k}", f"Newton step {k+1}: e = 1 - d x")
                m.wire(f"ea_{k}", XWd, expr=f"e_{k}[{XWd-1}] ? -e_{k} : e_{k}")
                m.umul(mul_fam, mul_pins, f"ea_{k}", XWd, f"ea_{k}", XWd, f"ee_{k}", f"Newton step {k+1}: e^2")
                m.wire(f"eef_{k}", XWd, expr=f"ee_{k}[{2*F+1}:{F}]")
                m.wire(f"g_{k}", XWd)
                m.add(add_fam, add_pins, XWd, f"f_{k}", f"eef_{k}", "1'b0", f"g_{k}", f"gc_{k}", f"Newton step {k+1}: 1 + e + e^2")
                m.umul(mul_fam, mul_pins, x, XWd, f"g_{k}", XWd, f"xg_{k}", f"Newton step {k+1}: x (1 + e + e^2)")
            else:
                m.umul(mul_fam, mul_pins, x, XWd, f"f_{k}", XWd, f"xg_{k}", f"Newton step {k+1}: x (2 - d x)")
            m.wire(f"x_{k+1}", XWd, expr=f"xg_{k}[{2*F+1}:{F}]")
            x = f"x_{k+1}"
        desc = (f"{steps} Newton step(s) of order {order}" if family == "newton_raphson" else
                "a table-indexed polynomial seed" + (f" and {steps} refinement step(s)" if steps else " with no refinement"))
    elif family == "goldschmidt":
        m.umul(mul_fam, mul_pins, "dnw", XWd, "x0w", XWd, "d_0", "Goldschmidt: the divisor scaled by the seed")
        nk = "x0w"
        dk = trunc_or_round("d_0", "df_0", 2 * F + 1, F, "the scaled divisor")
        for k in range(steps):
            m.wire(f"f_{k}", XWd)
            m.sub(add_fam, add_pins, XWd, "two", dk, f"f_{k}", f"fc_{k}", f"Goldschmidt step {k+1}: F = 2 - D")
            m.umul(mul_fam, mul_pins, nk, XWd, f"f_{k}", XWd, f"n_{k+1}", f"Goldschmidt step {k+1}: N F")
            m.umul(mul_fam, mul_pins, dk, XWd, f"f_{k}", XWd, f"d_{k+1}", f"Goldschmidt step {k+1}: D F")
            nk = trunc_or_round(f"n_{k+1}", f"nf_{k+1}", 2 * F + 1, F, f"step {k+1}: N")
            dk = trunc_or_round(f"d_{k+1}", f"df_{k+1}", 2 * F + 1, F, f"step {k+1}: D")
        x = nk
        desc = f"{steps} Goldschmidt step(s)" + (", the intermediates rounded" if round_intermediates else "")
    if prescaled:
        # both operands times the seed: the divisor lands within 2^-(kb+2) of 2^(D+P-1); each stage takes the
        # residual's leading kb bits as a signed digit (rounded for the prescaled recurrence and the
        # recoded Svoboda-Tung form, truncated for Tung's original) and subtracts the digit's multiple of
        # the scaled divisor through the residual adder
        rfam = str(_pin(pins, "residual_adder.family", "ripple_carry"))
        rpins = _sub_pins(pins, "residual_adder.")
        m.umul(mul_fam, mul_pins, "dn", D, "x0", P, "ds", "prescale: the divisor times the seed")
        m.umul(mul_fam, mul_pins, "a", N, "x0", P, "as_", "prescale: the dividend times the seed")
        nsteps = (Q + 1 + kb - 1) // kb
        QW = nsteps * kb
        base = D + P - 1
        WR = NW + P + 2
        m.wire("asw", WR, expr=_zext("as_", N + P, WR))
        m.wire("asx", WR, expr=f"asw << {S}" if S else "asw")
        norm.scale(m, "asx", WR, lzs, "w_0", "the scaled dividend aligned with the divisor", normalized)
        m.wire("dsx", WR, signed=True, expr=f"$signed({_zext('ds', D + P, WR)})")
        m.wire("qacc_0", QW + 2, signed=True, expr=f"{QW+2}'sd0")
        dw = kb + 2
        rounding = family == "prescaled_very_high_radix" or recode
        for j in range(nsteps):
            pos = base + QW - kb * (j + 1)
            m.wire(f"wsh_{j}", WR, signed=True, expr=f"$signed(w_{j}) >>> {pos}")
            if rounding and pos >= 1:
                # the digit rounded: the truncated digit plus the bit below it, through the residual adder
                m.wire(f"digt_{j}", dw, expr=f"wsh_{j}[{dw-1}:0]")
                m.wire(f"digz_{j}", dw, expr=f"{dw}'d0")
                m.wire(f"dig_{j}", dw, signed=True)
                m.add(rfam, rpins, dw, f"digt_{j}", f"digz_{j}", f"w_{j}[{pos-1}]", f"dig_{j}", f"digc_{j}",
                      f"stage {j+1}: the digit rounded")
            else:
                m.wire(f"dig_{j}", dw, signed=True, expr=f"wsh_{j}[{dw-1}:0]")
            m.umul(mul_fam, mul_pins, f"dig_{j}", dw, "dsx", WR, f"qdp_{j}", f"stage {j+1}: the digit times the scaled divisor", signed=True)
            m.wire(f"qd_{j}", WR, signed=True, expr=f"(qdp_{j}[{WR-1}:0]) <<< {pos - base}" if pos > base else f"qdp_{j}[{WR-1}:0]")
            m.wire(f"w_{j+1}", WR)
            m.sub(rfam, rpins, WR, f"w_{j}", f"qd_{j}", f"w_{j+1}", f"wge_{j+1}", f"stage {j+1}: the residual less the digit's multiple")
            m.wire(f"qsh_{j}", QW + 2, signed=True, expr=f"qacc_{j} <<< {kb}")
            m.wire(f"dgx_{j}", QW + 2, signed=True, expr=f"{{{{{QW + 2 - dw}{{dig_{j}[{dw-1}]}}}}, dig_{j}}}")
            m.wire(f"qacc_{j+1}", QW + 2, signed=True)
            m.add(rfam, rpins, QW + 2, f"qsh_{j}", f"dgx_{j}", "1'b0", f"qacc_{j+1}", f"qaccc_{j+1}", f"stage {j+1}: the quotient digits accumulated")
        m.wire("q1", Q + 1, expr=f"qacc_{nsteps}[{QW+1}] ? {Q+1}'d0 : qacc_{nsteps}[{Q}:0]")
        desc = f"{nsteps} stage(s) of {kb} quotient bits on the prescaled operands" + (" (NST two-digit recoding)" if recode else "")
    else:
        # the quotient estimate a 2^S 2^lzs x / 2^(F+D): the product of the dividend's N bits by the reciprocal
        # (F fraction bits of the divisor over 2^D), then the shifts as one right shift by (F + D - S - lzs)
        # through the norm shifter (a constant shift when the divisor arrives normalized)
        m.umul(mul_fam, mul_pins, "a", N, x, XWd, "px", "the quotient estimate a x")
        PW = N + XWd
        if exact:
            # the fraction bits kept below the quotient: two under the exclusion-zone rounding (the half
            # step added), four under the extra precision (the error bound added, so the truncation reads
            # the quotient from an estimate at or above it)
            keep = 2 if rnd.family == "exclusion_zone_proof" else 4
            sh0 = F - keep - S
            m.wire("two_p", PW, expr=f"{PW}'d2")
        else:
            sh0 = F + D - S
        if normalized:
            m.wire("qsh", PW, expr=f"px >> {sh0}")
        else:
            AW = _clog2(PW)
            m.wire("shamt", AW, expr=f"{AW}'d{sh0} - {{{{({AW}-{SW}){{1'b0}}}}, lzs}}")
            m.sh(norm.shf, norm.shf_pins, "px", PW, "shamt", True, "qsh", "the estimate's weight shift")
        if exact:
            m.wire("qe", PW)
            m.add(rnd.add, rnd.add_pins, PW, "qsh", "two_p", "1'b0", "qe", "qec",
                  "the rounding of the exact-width estimate" if rnd.family == "exclusion_zone_proof" else
                  "the estimate biased above the quotient by its error bound")
            m.wire("q1", Q + 1, expr=f"qe[{Q + D + keep}:{D + keep}]")
        else:
            m.wire("q1", Q + 1, expr=f"qsh[{Q}:0]")
    # the correction by the remainder: r = a 2^S - q b; the estimate is within two units of the quotient
    # (within one under two candidates), the back-multiply over the full product or its low bits alone
    RC = max(NA, Q + 1 + D) + 3
    if rnd is None:
        rnd = Rounding({"final_round.correction_adder.family": _pin(pins, "residual_adder.family", "ripple_carry")})
        rnd.low_bits = False
        rnd.add_pins = _sub_pins(pins, "residual_adder.")
    if rnd.low_bits and not exact:
        LB = min(Q + 1 + D, D + 3)
        m.wire("q1l", LB, expr=f"q1[{LB-1}:0]" if LB <= Q + 1 else _zext("q1", Q + 1, LB))
        m.wire("bl", LB, expr=f"b[{LB-1}:0]" if LB <= D else _zext("b", D, LB))
        m.umul(mul_fam, mul_pins, "q1l", LB, "bl", LB, "qbl", "the back-multiplied quotient (low bits)")
        m.wire("qb", Q + 1 + D, expr=_zext("qbl", 2 * LB, Q + 1 + D) if 2 * LB < Q + 1 + D else f"qbl[{Q + D}:0]")
        # the remainder is below 2b in magnitude: its low LB bits sign-extended
        m.wire("rr", RC, signed=True)
        m.wire("axl", LB, expr=f"{ax}[{LB-1}:0]" if LB <= NA else _zext(ax, NA, LB))
        m.wire("rrl", LB)
        m.sub(rnd.add, rnd.add_pins, LB, "axl", f"qbl[{LB-1}:0]", "rrl", "rrlc", "the remainder from the low bits of the product")
        m.assign("rr", f"$signed({{{{({RC}-{LB}){{rrl[{LB-1}]}}}}, rrl}})")
    else:
        m.umul(mul_fam, mul_pins, "q1", Q + 1, "b", D, "qb", "the back-multiplied quotient")
        m.wire("rr", RC, signed=True)
        m.wire("axr", RC, expr=_zext(ax, NA, RC))
        m.wire("qbr", RC, expr=_zext("qb", Q + 1 + D, RC))
        m.sub(rnd.add, rnd.add_pins, RC, "axr", "qbr", "rr", "rrc", "the remainder a - q b")
    m.wire("bs", RC, signed=True, expr=f"$signed({_zext('b', D, RC)})")
    m.wire("bs2", RC, signed=True, expr="bs <<< 1")
    if exact:
        m.wire("qc", Q + 1, expr="q1")
        m.wire("rc", RC, signed=True, expr="rr")
        tail = (f"final rounding {rnd.family}: {F} fraction bits make the "
                f"{'rounded estimate' if rnd.family == 'exclusion_zone_proof' else 'estimate biased by its error bound and truncated'} exact")
    elif prescaled:
        # the prescaled recurrences correct by one unit from the remainder's sign
        rfam = str(_pin(pins, "residual_adder.family", "ripple_carry"))
        rpins = _sub_pins(pins, "residual_adder.")
        m.wire("neg", expr=f"rr[{RC-1}]")
        m.wire("rp1", RC)
        m.wire("rp1c")
        m.add(rfam, rpins, RC, "rr", "bs", "1'b0", "rp1", "rp1c", "the remainder plus b")
        m.wire("rm1", RC)
        m.sub(rfam, rpins, RC, "rr", "bs", "rm1", "over", "the remainder less b")
        m.wire("oneq", Q + 1, expr=f"{Q+1}'d1")
        m.wire("q1p", Q + 1)
        m.wire("q1m", Q + 1)
        m.add(rfam, rpins, Q + 1, "q1", "oneq", "1'b0", "q1p", "q1pc", "the candidate q + 1")
        m.sub(rfam, rpins, Q + 1, "q1", "oneq", "q1m", "q1mc", "the candidate q - 1")
        m.wire("qc", Q + 1, expr="neg ? q1m : over ? q1p : q1")
        m.wire("rc", RC, signed=True, expr="neg ? $signed(rp1) : over ? $signed(rm1) : rr")
        tail = "the quotient corrected by one unit from the back-multiplied remainder"
    else:
        m.wire("neg", expr=f"rr[{RC-1}]")
        m.wire("rp1", RC)
        m.wire("rp1c")
        m.add(rnd.add, rnd.add_pins, RC, "rr", "bs", "1'b0", "rp1", "rp1c", "the remainder plus b")
        m.wire("rm1", RC)
        m.sub(rnd.add, rnd.add_pins, RC, "rr", "bs", "rm1", "over", "the remainder less b")
        m.wire("q1p", Q + 1)
        m.wire("q1m", Q + 1)
        m.wire("oneq", Q + 1, expr=f"{Q+1}'d1")
        m.add(rnd.add, rnd.add_pins, Q + 1, "q1", "oneq", "1'b0", "q1p", "q1pc", "the candidate q + 1")
        m.sub(rnd.add, rnd.add_pins, Q + 1, "q1", "oneq", "q1m", "q1mc", "the candidate q - 1")
        if rnd.candidates == 3:
            m.wire("rp2", RC)
            m.wire("rp2c")
            m.add(rnd.add, rnd.add_pins, RC, "rr", "bs2", "1'b0", "rp2", "rp2c", "the remainder plus 2b")
            m.wire("rm2", RC)
            m.sub(rnd.add, rnd.add_pins, RC, "rr", "bs2", "rm2", "over2", "the remainder less 2b")
            m.wire("neg2", expr=f"neg && rp1[{RC-1}]")
            m.wire("q1p2", Q + 1)
            m.wire("q1m2", Q + 1)
            m.wire("twoq", Q + 1, expr=f"{Q+1}'d2")
            m.add(rnd.add, rnd.add_pins, Q + 1, "q1", "twoq", "1'b0", "q1p2", "q1p2c", "the candidate q + 2")
            m.sub(rnd.add, rnd.add_pins, Q + 1, "q1", "twoq", "q1m2", "q1m2c", "the candidate q - 2")
            m.wire("qc", Q + 1, expr="neg2 ? q1m2 : neg ? q1m : over2 ? q1p2 : over ? q1p : q1")
            m.wire("rc", RC, signed=True, expr="neg2 ? $signed(rp2) : neg ? $signed(rp1) : over2 ? $signed(rm2) : over ? $signed(rm1) : rr")
        else:
            m.wire("qc", Q + 1, expr="neg ? q1m : over ? q1p : q1")
            m.wire("rc", RC, signed=True, expr="neg ? $signed(rp1) : over ? $signed(rm1) : rr")
        tail = (f"the quotient corrected by up to {rnd.candidates - 1} unit(s) from the back-multiplied remainder"
                + (" (its low bits)" if rnd.low_bits else ""))
    m.assign("q", f"qc[{Q-1}:0]")
    m.assign("r", f"rc[{D-1}:0]")
    m.comment = (f"divider ({family}): the divisor normalized, a {seed.family} reciprocal seed of {kin} input bits "
                 f"(error {eps0:.2e}), {desc} with {mul_fam} multipliers at {F} fraction bits; {tail}")
    return name, m.render()


# ---- square root ------------------------------------------------------------------------
def _root_multiples(m: Mod, tag: str, base: str, BW: int, a: int, fam, fpins: dict, RW: int, shift: int) -> dict:
    """{k: wire} of k times a partial root (BW bits) at RW bits, shifted
    left by `shift`; the odd multiples through the adder family."""
    out = {}
    lo = m.wire(f"{tag}x1", RW, expr=f"{{{{({RW}-{BW}-{shift}){{1'b0}}}}, {base}, {shift}'d0}}" if shift else _zext(base, BW, RW))
    out[1] = lo
    for k in range(2, a + 1):
        if k & (k - 1) == 0:
            s = k.bit_length() - 1
            out[k] = m.wire(f"{tag}x{k}", RW, expr=f"{lo} << {s}")
        else:
            p2 = 1 << (k.bit_length() - 1)
            out[k] = m.wire(f"{tag}x{k}", RW)
            m.add(fam, fpins, RW, out[p2], out[k - p2], "1'b0", out[k], f"{tag}x{k}c", f"the partial root times {k}")
    return out


def _trial_sqrt_sv(Q: int, pins: dict, name: str, normalized: bool, family: str) -> tuple:
    """The restoring square root (restoring_nonrestoring): one root bit
    per stage from the trial subtraction of 4 R + 1 (R the partial root)
    from the partial remainder with the next two radicand bits brought
    down, through the residual_adder family; the trial kept when it
    fits. No normalization is needed."""
    fam = str(_pin(pins, "residual_adder.family", "ripple_carry"))
    fpins = _sub_pins(pins, "residual_adder.")
    m = Mod(name, f"square root ({family}, residual adder {fam}): the restoring recurrence, one root bit per stage from the "
                  "trial subtraction of 4 R + 1")
    m.port("input", "x", 2 * Q)
    m.port("output", "root", Q)
    m.port("output", "rem", Q + 2)
    RW = Q + 3
    m.wire("rem_0", RW, expr=f"{RW}'d0")
    m.wire("root_0", Q, expr=f"{Q}'d0")
    for i in range(Q):
        top = 2 * Q - 2 * i
        m.wire(f"in_{i+1}", RW, expr=f"{{rem_{i}[{RW-3}:0], x[{top-1}:{top-2}]}}")
        m.wire(f"T_{i+1}", RW, expr=f"{{1'b0, root_{i}, 2'b01}}")
        m.wire(f"t_{i+1}", RW)
        m.sub(fam, fpins, RW, f"in_{i+1}", f"T_{i+1}", f"t_{i+1}", f"ge_{i+1}", f"stage {i+1}: the trial subtraction of 4 R + 1")
        m.wire(f"rem_{i+1}", RW, expr=f"ge_{i+1} ? t_{i+1} : in_{i+1}")
        m.wire(f"root_{i+1}", Q, expr=f"{{root_{i}[{Q-2}:0], ge_{i+1}}}" if Q > 1 else f"ge_{i+1}")
    m.assign("root", f"root_{Q}")
    m.assign("rem", f"rem_{Q}[{Q+1}:0]")
    return name, m.render()


def _srt_sqrt_sv(Q: int, pins: dict, name: str, normalized: bool, plan: list, a4: int, family: str, conv_otf: bool) -> tuple:
    """The SRT square root with a carry-save residual: radix-4 (digits
    -a4..a4) or radix-2 stages, the root digit from the digit_select
    slot (a table over the residual estimate and the partial root,
    generated and checked for containment per stage index, or the
    comparators against that table's thresholds through the slot's
    adder), the subtrahend formed from the on-the-fly Q and QM words (the
    F formation: the digit's multiple of Q for a positive digit, of QM
    for a negative one, plus the square term's constant) or, without the
    on-the-fly conversion, from the partial root assimilated each stage
    as Q+ - Q- (its multiples plus or minus the constant through the
    residual adder); the residual assimilated at the end, the root taken
    from Q or QM by the final sign. The radicand's leading one must lie
    in its top two bits (`normalized`), else an even shift through the
    norm slots places it there and the remainder is recomputed from the
    de-scaled root (its square by rows of the residual adder)."""
    fam = str(_pin(pins, "residual_adder.family", "ripple_carry"))
    fpins = _sub_pins(pins, "residual_adder.")
    sp = _sub_pins(pins, "digit_select.")
    sel_family = str(_pin(pins, "digit_select.family", "qds_table"))
    IB = 4
    if sel_family == "comparator_digit_selection":
        cp = _CmpPins(sp, 2, pins, "digit_select.")
        tb = max(2, min(cp.bits - IB, 12))
        db = 4
        est_fam, est_pins = cp.adder, cp.adder_pins
    else:
        cp = None
        tb = max(2, min(_ipin(pins, "digit_select.residual_truncation_bits", 4), 10))
        db = max(2, min(_ipin(pins, "digit_select.divisor_truncation_bits", 4), 8))
        est_fam, est_pins = fam, fpins
    if max(plan) == 1:
        db = 1                                                # radix 2 selects from the residual alone (S >= 1/2)
    two_word = bool(cp) and cp.residual_input == "redundant_two_word" and not cp.fold
    norm = Norm(pins)
    XN = 2 * Q
    m = Mod(name, "")
    m.port("input", "x", XN)
    m.port("output", "root", Q)
    m.port("output", "rem", Q + 2)
    AW = _clog2(XN)
    if normalized:
        m.wire("xn", XN, expr="x")
    else:
        # an even normalizing shift: the radicand's leading one lands in its top two bits
        m.lz(norm.lzc, norm.lzc_pins, "x", XN, "lz", "the radicand's leading zeros")
        SH = _clog2(Q)
        m.wire("sh", SH, expr=f"lz[{SH}:1]")
        m.wire("sh2", AW, expr=f"{{lz[{AW-1}:1], 1'b0}}" if AW >= 2 else "1'b0")
        norm.scale(m, "x", XN, "sh2", "xn", "the radicand normalized by an even shift", False)
    # the stages: radix-4 or radix-2 digits, one digit per sub-stage, the plan repeated until the root
    # bits reach Q (the extra low bits are taken out at the end)
    ks = []
    while sum(ks) < Q:
        ks += list(plan)
    QB = sum(ks)
    e = QB - Q
    FR = 2 * Q + 3
    RW = FR + IB
    # w~[0] = (x - 1) / 2 with S[0] = 1: x over 2^XN, the residual with FR fraction bits
    m.wire("xf", RW, expr=f"{{{IB}'b0, xn, {FR-XN}'d0}}" if FR > XN else f"{{{IB}'b0, xn}}")
    m.wire("onef", RW, expr=f"{{{IB-1}'b0, 1'b1, {FR}'d0}}")
    m.wire("xm1", RW)
    m.sub(fam, fpins, RW, "xf", "onef", "xm1", "xm1c", "x - 1")
    m.wire("ws_0", RW, expr="$signed(xm1) >>> 1")
    m.wire("wc_0", RW, expr=f"{RW}'d0")
    # the root words hold S 2^done in their low done+1 bits (the integer bit at position done)
    QWs = 1 + QB
    if conv_otf:
        m.wire("qq_0", QWs, expr=f"{QWs}'d1")
        m.wire("qmm_0", QWs, expr=f"{QWs}'d0")
    else:
        m.wire("qpos_0", QWs, expr=f"{QWs}'d1")
        m.wire("qneg_0", QWs, expr=f"{QWs}'d0")
    ws, wc = "ws_0", "wc_0"
    qq, qmm, qpos, qneg = "qq_0", "qmm_0", "qpos_0", "qneg_0"
    done = 0
    desc_tab = None
    steady = None                                            # the table shared by the stages past db root bits
    for i, k in enumerate(ks):
        r = 1 << k
        a = a4 if k == 2 else 1
        w = (a + 1).bit_length() + 1
        tag = f"{i}"
        eps_bits = done + k                                   # the stage's term r^-(j+1) is 2^-(done + k)
        # the partial root's value word
        if conv_otf:
            sw = qq
        else:
            sw = m.wire(f"s_{tag}", QWs)
            m.sub(fam, fpins, QWs, qpos, qneg, sw, f"sc_{tag}", f"stage {i}: the partial root assimilated (Q+ - Q-)")
        # the cells of the partial root at this stage and the row key that selects them
        if done == 0:
            cells = [(Fraction(1), Fraction(1))]
            rowsel = None
            RWD = 0
            row = ""
            rows = {0: 0}
        elif done <= db:
            # every partial root so far is an exact point: one cell per value
            pts = sorted({Fraction(1) + Fraction(v, 1 << done) for v in range(-(1 << done) + 1, 1)})
            pts = [p for p in pts if p >= Fraction(1, 2)]
            cells = [(p, p) for p in pts]
            rowsel = "exact"
            RWD = done + 1
            row = m.wire(f"row_{tag}", RWD, expr=f"{sw}[{done}:0]")
            rows = {int(p * (1 << done)): ci for ci, p in enumerate(pts)}
        else:
            step = Fraction(1, 1 << db)
            cells = [(Fraction(v, 1 << db), Fraction(v + 1, 1 << db)) for v in range(1 << (db - 1), 1 << db)] + [(Fraction(1), Fraction(1))]
            rowsel = "bits"
            RWD = db
            # {the integer bit, the fraction bits 2..db}: the integer bit set is the cell S = 1, else the
            # fraction bits below the leading one (S >= 1/2) index the cells of [1/2, 1) in order
            row = m.wire(f"row_{tag}", RWD, expr=f"{{{sw}[{done}], {sw}[{done-2}:{done-db}]}}" if db > 1 else f"{sw}[{done}]")
            rows = {rv: (len(cells) - 1 if rv >> (db - 1) else rv) for rv in range(1 << db)}
        if rowsel == "bits" and steady is not None:
            table, yi_min, yi_max, tbits = steady
        else:
            tbits = tb
            while True:
                table, yi_min, yi_max = _sqrt_table_bits(r, a, tbits, cells, eps_bits, rowsel == "bits", FR)
                if not any(v is None for v in table.values()):
                    break
                tbits += 1
                if tbits > 12:
                    raise ValueError(f"{family}: no feasible radix-{r} square-root selection table at stage {i}")
            if rowsel == "bits":
                steady = (table, yi_min, yi_max, tbits)
        YI = IB + tbits
        desc_tab = desc_tab or (f"comparators over {YI} estimate bits ({cp.describe()})" if cp else
                                f"a table over {db} root bits and {tbits} residual fraction bits")
        # the shifted residual (times r) and its estimate
        m.wire(f"wsh_{tag}", RW, expr=f"{{{ws}[{RW-1-k}:0], {k}'d0}}")
        m.wire(f"wch_{tag}", RW, expr=f"{{{wc}[{RW-1-k}:0], {k}'d0}}")
        y = None
        if not two_word:
            m.wire(f"yas_{tag}", YI, expr=f"wsh_{tag}[{RW-1}:{RW-YI}]")
            m.wire(f"yac_{tag}", YI, expr=f"wch_{tag}[{RW-1}:{RW-YI}]")
            m.wire(f"yau_{tag}", YI)
            m.add(est_fam, est_pins, YI, f"yas_{tag}", f"yac_{tag}", "1'b0", f"yau_{tag}", f"yauc_{tag}",
                  f"stage {i}: the residual estimate assimilated")
            y = m.wire(f"y_{tag}", YI, signed=True, expr=f"$signed(yau_{tag})")
        if cp:
            ths = {}
            for rv, ci in rows.items():
                if ci is None:
                    continue
                ths[rv] = _thresholds_of([table[(ci, yi)] for yi in range(yi_min, yi_max + 1)], yi_min, a)
            dsel = _comparator_digit(m, tag, y, YI, a, ths, row, RWD, f"wsh_{tag}", f"wch_{tag}", RW, cp)
        else:
            # the table as a ROM over {row, estimate} (the estimate offset to unsigned by its sign bit),
            # the entries outside the table's estimate range saturating by the sign
            entries = {}
            for rv in range(1 << RWD):
                ci = rows.get(rv)
                if ci is None:
                    continue
                for yi in range(max(yi_min, -(1 << (YI - 1))), min(yi_max, (1 << (YI - 1)) - 1) + 1):
                    entries[(rv << YI) | (yi + (1 << (YI - 1)))] = table[(ci, yi)] & ((1 << w) - 1)
            m.wire(f"yu_{tag}", YI, expr=f"{{~y_{tag}[{YI-1}], y_{tag}[{YI-2}:0]}}")
            idx = f"{{{row}, yu_{tag}}}" if RWD else f"yu_{tag}"
            m.rom(f"SQ_{tag}", entries, w, idx, f"dsel_{tag}", f"the root-digit selection table of stage {i}", signed=True,
                  kbits=RWD + YI, default=f"k[{YI-1}] ? {_slit(w, a)} : {_slit(w, -a)}")
            dsel = f"dsel_{tag}"
        # the F formation at the residual's fixed point: shift the root word's value S 2^done up to FR
        # fraction bits; the square term's constant s^2 r^-(j+1) / 2 has the weight 2^cbit
        shift = FR - done
        cbit = FR - eps_bits - 1
        opts = []
        if conv_otf:
            qf = _root_multiples(m, f"q{tag}_", f"{qq}[{done}:0]", done + 1, a, fam, fpins, RW, shift)
            qmf = _root_multiples(m, f"qm{tag}_", f"{qmm}[{done}:0]", done + 1, a, fam, fpins, RW, shift)
            for s in range(1, a + 1):
                # positive: s (S + s eps/2) = s Q + s^2 2^cbit; negative: |s| (S - |s| eps/2) = |s| QM +
                # (s 2^(eps_bits - done + 1) - s^2) 2^cbit (QM = S - 2^-done); a constant below the words'
                # lsbs is ORed in, a colliding one added
                cpos = s * s
                cneg = s * (1 << (eps_bits - done + 1)) - s * s
                pos_w = m.wire(f"fp{s}_{tag}", RW)
                neg_w = m.wire(f"fn{s}_{tag}", RW)
                m.wire(f"cp{s}_{tag}", RW, expr=f"{RW}'d{cpos << cbit}")
                m.wire(f"cn{s}_{tag}", RW, expr=f"{RW}'d{cneg << cbit}")
                if (cpos << cbit) < (1 << shift):
                    m.assign(pos_w, f"{qf[s]} | cp{s}_{tag}")
                else:
                    m.add(fam, fpins, RW, qf[s], f"cp{s}_{tag}", "1'b0", pos_w, f"fpc{s}_{tag}", f"stage {i}: the subtrahend of the digit {s}")
                if (cneg << cbit) < (1 << shift):
                    m.assign(neg_w, f"{qmf[s]} | cn{s}_{tag}")
                else:
                    m.add(fam, fpins, RW, qmf[s], f"cn{s}_{tag}", "1'b0", neg_w, f"fnc{s}_{tag}", f"stage {i}: the subtrahend of the digit -{s}")
                opts.append((s, pos_w, neg_w))
        else:
            sf = _root_multiples(m, f"s{tag}_", f"{sw}[{done}:0]", done + 1, a, fam, fpins, RW, shift)
            for s in range(1, a + 1):
                cpos = s * s
                pos_w = m.wire(f"fp{s}_{tag}", RW)
                neg_w = m.wire(f"fn{s}_{tag}", RW)
                m.wire(f"cp{s}_{tag}", RW, expr=f"{RW}'d{cpos << cbit}")
                if (cpos << cbit) < (1 << shift):
                    m.assign(pos_w, f"{sf[s]} | cp{s}_{tag}")
                else:
                    m.add(fam, fpins, RW, sf[s], f"cp{s}_{tag}", "1'b0", pos_w, f"fpc{s}_{tag}", f"stage {i}: the subtrahend of the digit {s}")
                m.sub(fam, fpins, RW, sf[s], f"cp{s}_{tag}", neg_w, f"fnc{s}_{tag}", f"stage {i}: the subtrahend of the digit -{s}")
                opts.append((s, pos_w, neg_w))
        sel_p = " : ".join(f"({dsel} == {_slit(w, s)}) ? {p}" for s, p, _n in opts) + f" : {RW}'d0"
        sel_n = " : ".join(f"({dsel} == {_slit(w, -s)}) ? {n_}" for s, _p, n_ in opts) + f" : {RW}'d0"
        m.wire(f"fpos_{tag}", RW, expr=sel_p)
        m.wire(f"fneg_{tag}", RW, expr=sel_n)
        m.wire(f"add_{tag}", RW, expr=f"({dsel} > {w}'sd0) ? ~fpos_{tag} : ({dsel} < {w}'sd0) ? fneg_{tag} : {RW}'d0")
        m.wire(f"cin_{tag}", expr=f"{dsel} > {w}'sd0")
        _csa(m, f"ws_{i+1}", f"wc_{i+1}", RW, f"wsh_{tag}", f"wch_{tag}", f"add_{tag}", f"cin_{tag}")
        # the conversion of the root digit
        if conv_otf:
            qq, qmm = _otf_step(m, f"{i+1}", QWs, k, dsel, w, qq, qmm)
        else:
            m.wire(f"qpos_{i+1}", QWs, expr=f"{{{qpos}[{QWs-1-k}:0], ({dsel} > {w}'sd0) ? {dsel}[{k-1}:0] : {k}'d0}}")
            m.wire(f"qneg_{i+1}", QWs, expr=f"{{{qneg}[{QWs-1-k}:0], ({dsel} < {w}'sd0) ? (-{dsel}) [{k-1}:0] : {k}'d0}}")
            qpos, qneg = f"qpos_{i+1}", f"qneg_{i+1}"
        ws, wc = f"ws_{i+1}", f"wc_{i+1}"
        done += k
    # the final residual: negative selects S - ulp and adds 2 S - ulp back to the remainder
    m.wire("wf", RW)
    m.wire("wfc")
    m.add(fam, fpins, RW, ws, wc, "1'b0", "wf", "wfc", "the final residual assimilated")
    m.wire("wneg", expr=f"wf[{RW-1}]")
    if conv_otf:
        m.wire("sroot", QWs, expr=qq)
        m.wire("rootn", QWs, expr=f"wneg ? {qmm} : {qq}")
    else:
        m.wire("sroot", QWs)
        m.sub(fam, fpins, QWs, qpos, qneg, "sroot", "srootc", "the root assimilated (Q+ - Q-)")
        m.wire("onew", QWs, expr=f"{QWs}'d1")
        m.wire("srootm", QWs)
        m.sub(fam, fpins, QWs, "sroot", "onew", "srootm", "srootmc", "the root less one unit")
        m.wire("rootn", QWs, expr="wneg ? srootm : sroot")
    # rem' = x 4^e - S'^2 in integer units (S' the QB-bit root): w~ = 2^QB (x - S'^2) / 2 at FR fraction bits
    shift_back = FR + QB - XN - 1 - 2 * e
    m.wire("wfs", RW, expr=f"$signed(wf) >>> {shift_back}" if shift_back > 0 else (f"wf << {-shift_back}" if shift_back < 0 else "wf"))
    m.wire("twoS", RW, expr=f"{{{{({RW}-{QWs}-1){{1'b0}}}}, sroot, 1'b0}}")
    m.wire("onef2", RW, expr=f"{RW}'d1")
    m.wire("twoSm1", RW)
    m.sub(fam, fpins, RW, "twoS", "onef2", "twoSm1", "twoSm1c", "2 S - 1")
    m.wire("remn", RW)
    m.wire("remnc")
    m.add(fam, fpins, RW, "wfs", "twoSm1", "1'b0", "remn", "remnc", "the remainder of the decremented root")
    m.wire("remf", RW, expr="wneg ? remn : wfs")
    if e == 0:
        m.wire("rootq", Q, expr=f"rootn[{Q-1}:0]")
        m.wire("remq", RW, expr="remf")
    else:
        # e extra low root bits t: root = floor(root' / 2^e), rem = (rem' + (2^(e+1) root + t) t) / 4^e, the
        # product with the e-bit t as a sum of shifted copies per bit through the residual adder
        m.wire("rootq", Q, expr=f"rootn[{QB-1}:{e}]")
        m.wire("rtl", e, expr=f"rootn[{e-1}:0]")
        terms = [m.wire(f"tb{bpos}", RW, expr=f"rtl[{bpos}] ? ({{{{({RW}-{Q}-{e}-1){{1'b0}}}}, rootq, 1'b0, rtl}} << {bpos}) : {RW}'d0")
                 for bpos in range(e)]
        acc = terms[0]
        for bpos in range(1, e):
            nacc = m.wire(f"tacc{bpos}", RW)
            m.add(fam, fpins, RW, acc, terms[bpos], "1'b0", nacc, f"taccc{bpos}", "the low root bits' correction")
            acc = nacc
        m.wire("remo", RW)
        m.wire("remoc")
        m.add(fam, fpins, RW, "remf", acc, "1'b0", "remo", "remoc", "the remainder before the extra root bits")
        m.wire("remq", RW, expr=f"remo >> {2 * e}")
    if normalized:
        m.assign("root", "rootq")
        m.assign("rem", f"remq[{Q+1}:0]")
    else:
        # the root of the unshifted radicand is the normalized root shifted back; its remainder x - root^2
        # with the square by rows of the residual adder
        # `descale` declares its destination (it shifts into it), so the caller must not
        norm.descale(m, "rootq", Q, "sh", "roots", "the root de-scaled", False)
        # the remainder lies below 2 root + 1, so its low Q + 2 bits are exact from the square's low bits
        LOW = Q + 2
        _square_low(m, "roots", Q, LOW, fam, fpins, "rs2", "the de-scaled root squared for the remainder")
        m.wire("xl", LOW, expr=f"x[{LOW-1}:0]" if XN >= LOW else _zext("x", XN, LOW))
        m.wire("remu", LOW)
        m.sub(fam, fpins, LOW, "xl", "rs2", "remu", "remuc", "the remainder x - root^2 (its low bits)")
        m.assign("root", f"(x == {XN}'d0) ? {Q}'d0 : roots")
        m.assign("rem", f"(x == {XN}'d0) ? {Q+2}'d0 : remu[{Q+1}:0]")
    m.comment = (f"square root ({family}): the SRT recurrence with {' + '.join(f'radix-{1 << k}' for k in plan)} sub-stage(s), a carry-save "
                 f"residual, the root digit from {desc_tab}, the root {'on the fly' if conv_otf else 'as Q+ - Q-'}")
    return name, m.render()


def _sqrt_table_bits(radix: int, a: int, tbits: int, cells: list, eps_bits: int, steady: bool, FR: int) -> tuple:
    """sqrt_table with the stage term r^-(j+1) given as 2^-eps_bits (and,
    for the steady state, every finer one down to the division limit)."""
    rho = Fraction(a, radix - 1)
    ystep = Fraction(1, 1 << tbits)
    margin = Fraction(1, 1 << (FR - 2))
    unc = 2
    eps_list = [Fraction(1, 1 << eps_bits)]
    if steady:
        eps_list += [Fraction(1, 1 << (eps_bits + t)) for t in (1, 2, 4)] + [Fraction(0)]
    ybound = radix * rho * max(hi for _lo, hi in cells)
    yi_min = math.floor(-ybound / ystep) - unc
    yi_max = math.ceil(ybound / ystep)
    table = {}
    for ci, (S_lo, S_hi) in enumerate(cells):
        for yi in range(yi_min, yi_max + 1):
            y_lo, y_hi = yi * ystep, (yi + unc) * ystep
            chosen = None
            for k in range(-a, a + 1):
                ok = True
                for eps in eps_list:
                    for S in (S_lo, S_hi):
                        sub = k * (S + k * eps / 2)
                        bound = rho * (S + k * eps)
                        if k != -a and y_lo - sub < -bound:
                            ok = False
                        if k != a and y_hi - sub > bound - margin:
                            ok = False
                if ok:
                    chosen = k
                    break
            if chosen is None and (y_lo > radix * rho * S_hi or y_hi < -radix * rho * S_hi):
                chosen = a if y_lo > 0 else -a
            table[(ci, yi)] = chosen
    return table, yi_min, yi_max


def _functional_sqrt_sv(Q: int, family: str, pins: dict, name: str, normalized: bool) -> tuple:
    """newton_raphson | goldschmidt | direct_polynomial as square roots:
    a reciprocal-square-root seed refined by y (3 - x y^2) / 2 (Goldschmidt:
    the paired b r^2, y r iteration), the root x y corrected by its
    square; the products through the iter_mult (final_mul) slot, the
    sums through iter_add, the corrections through the final rounding's
    adder, the normalization through the norm slots."""
    seed = Seed(pins, "approximator." if family == "direct_polynomial" else "seed.",
                "poly_seed" if family == "direct_polynomial" else "monolithic_rom")
    if seed.family not in SEED_FAMILIES or seed.family == "operand_modification_multiply":
        raise ValueError(f"{family}: the square root has no seed of the family {seed.family!r}")
    kin = seed.kin
    mul_key = "final_mul." if family == "direct_polynomial" else "iter_mult."
    mul_fam = str(_pin(pins, mul_key + "family", "behavioral_star"))
    mul_pins = _sub_pins(pins, mul_key)
    if family == "direct_polynomial":
        add_fam, add_pins = seed.add, seed.add_pins
        guard = 4
    else:
        add_fam = str(_pin(pins, "iter_add.family", "ripple_carry"))
        add_pins = _sub_pins(pins, "iter_add.")
        guard = max(0, _ipin(pins, "internal_guard_bits", 4))
    rnd = Rounding(pins)
    norm = Norm(pins)
    fn = _Fn("recip_sqrt")
    XN = 2 * Q
    m = Mod(name, "")
    m.port("input", "x", XN)
    m.port("output", "root", Q)
    m.port("output", "rem", Q + 2)
    if normalized:
        m.wire("xn", XN, expr="x")
        m.wire("sh", 1, expr="1'b0")
    else:
        m.lz(norm.lzc, norm.lzc_pins, "x", XN, "lz", "the radicand's leading zeros")
        LW = XN.bit_length()
        SH = max(1, LW - 1)
        m.wire("sh", SH, expr=f"lz[{SH}:1]")
        m.wire("sh2", SH + 1, expr="{sh, 1'b0}")
        norm.scale(m, "x", XN, "sh2", "xn", "the radicand normalized by an even shift", False)
    want = (_ipin(pins, "iterations", 0) or None) if family in ("newton_raphson", "goldschmidt") else (
        0 if str(_pin(pins, "composition", "polynomial_only")) == "polynomial_only" else 1)
    need = Q + 1
    while True:
        P, eps0 = seed_sv(Mod("probe", ""), seed, "xn", XN, kin, "y0", fn)
        F = max(need + guard + 2, P - 1)
        eps = eps0
        for _s in range(want or 0):
            eps = 1.5 * eps * eps + 4 * 2.0 ** -F
        asked = want is not None and (want > 0 or family == "direct_polynomial")
        if not asked or eps <= 2.0 ** -need:
            break
        if kin < XN - 1:
            kin += 1
        elif seed.raise_degree():
            kin = seed.kin
        else:
            raise ValueError(f"{family}: no seed of {seed.family} reaches the target in {want} iteration(s)")
    P, eps0 = seed_sv(m, seed, "xn", XN, kin, "y0", fn)
    XWd = F + 3
    m.wire("y0w", XWd, expr=f"{{3'b0, y0}} << {F - (P - 1)}" if F > P - 1 else (f"{{3'b0, y0}}" if F == P - 1 else f"{{3'b0, y0[{P-1}:{P-1-F}]}}"))
    m.wire("xw", XWd, expr=f"{{3'b0, xn}} << {F - XN}" if F >= XN else f"{{3'b0, xn[{XN-1}:{XN-F}]}}")
    if want is not None and (want > 0 or family == "direct_polynomial"):
        steps = want
    else:
        steps = 0
        eps = eps0
        while eps > 2.0 ** -need and steps < 8:
            eps = 1.5 * eps * eps + 4 * 2.0 ** -F
            steps += 1
        if eps > 2.0 ** -need:
            raise ValueError(f"{family}: the rsqrt iteration does not reach 2^-{need} from a seed error of {eps0:.3g}")
    m.wire("three", XWd, expr=f"{{2'b11, {F}'d0}}")
    y = "y0w"
    if family == "goldschmidt":
        m.umul(mul_fam, mul_pins, "xw", XWd, "y0w", XWd, "gy_0", "Goldschmidt sqrt: x times the seed")
        m.wire("yv_0", XWd, expr=f"gy_0[{2*F+2}:{F}]")
        m.umul(mul_fam, mul_pins, "yv_0", XWd, "y0w", XWd, "gb_0", "Goldschmidt sqrt: x y0^2")
        m.wire("bv_0", XWd, expr=f"gb_0[{2*F+2}:{F}]")
        for k in range(steps):
            m.wire(f"tb_{k}", XWd)
            m.sub(add_fam, add_pins, XWd, "three", f"bv_{k}", f"tb_{k}", f"tbc_{k}", f"Goldschmidt sqrt step {k+1}: 3 - b")
            m.wire(f"rk_{k}", XWd, expr=f"tb_{k} >> 1")
            m.umul(mul_fam, mul_pins, f"yv_{k}", XWd, f"rk_{k}", XWd, f"gy_{k+1}", f"Goldschmidt sqrt step {k+1}: y r")
            m.wire(f"yv_{k+1}", XWd, expr=f"gy_{k+1}[{2*F+2}:{F}]")
            m.umul(mul_fam, mul_pins, f"rk_{k}", XWd, f"rk_{k}", XWd, f"rr_{k}", f"Goldschmidt sqrt step {k+1}: r^2")
            m.wire(f"rrv_{k}", XWd, expr=f"rr_{k}[{2*F+2}:{F}]")
            m.umul(mul_fam, mul_pins, f"bv_{k}", XWd, f"rrv_{k}", XWd, f"gb_{k+1}", f"Goldschmidt sqrt step {k+1}: b r^2")
            m.wire(f"bv_{k+1}", XWd, expr=f"gb_{k+1}[{2*F+2}:{F}]")
        m.wire("rootw", XWd, expr=f"yv_{steps}")
        desc = f"{steps} Goldschmidt step(s)"
    else:
        for k in range(steps):
            m.umul(mul_fam, mul_pins, y, XWd, y, XWd, f"yy_{k}", f"rsqrt step {k+1}: y^2")
            m.wire(f"yyv_{k}", XWd, expr=f"yy_{k}[{2*F+2}:{F}]")
            m.umul(mul_fam, mul_pins, "xw", XWd, f"yyv_{k}", XWd, f"xyy_{k}", f"rsqrt step {k+1}: x y^2")
            m.wire(f"xyyv_{k}", XWd, expr=f"xyy_{k}[{2*F+2}:{F}]")
            m.wire(f"g_{k}", XWd)
            m.sub(add_fam, add_pins, XWd, "three", f"xyyv_{k}", f"g_{k}", f"gc_{k}", f"rsqrt step {k+1}: 3 - x y^2")
            m.umul(mul_fam, mul_pins, y, XWd, f"g_{k}", XWd, f"yg_{k}", f"rsqrt step {k+1}: y (3 - x y^2)")
            m.wire(f"y_{k+1}", XWd, expr=f"yg_{k}[{2*F+3}:{F+1}]")
            y = f"y_{k+1}"
        m.umul(mul_fam, mul_pins, "xw", XWd, y, XWd, "xy", "the root estimate x y")
        m.wire("rootw", XWd, expr=f"xy[{2*F+2}:{F}]")
        desc = (f"{steps} rsqrt Newton step(s)" if family == "newton_raphson" else
                "a table-indexed polynomial seed" + (f" and {steps} refinement step(s)" if steps else ""))
    # the root estimate as an integer, within two units; corrected by its square through the rounding adder
    m.wire("est", Q + 1, expr=f"rootw[{F}:{F-Q}]")
    m.umul(mul_fam, mul_pins, "est", Q + 1, "est", Q + 1, "e2", "the estimate squared")
    EW2 = 2 * Q + 4
    m.wire("xs", EW2, expr="{4'b0, xn}")
    m.wire("e2s", EW2, expr=_zext("e2", 2 * Q + 2, EW2))
    m.wire("ests", EW2, expr=_zext("est", Q + 1, EW2))
    m.wire("d0", EW2)
    m.sub(rnd.add, rnd.add_pins, EW2, "xs", "e2s", "d0", "d0ge", "x - est^2")
    # the candidates est +- 1, est +- 2 and their remainder adjustments 2 est +- 1, 4 est +- 4
    m.wire("e2p1", EW2, expr="{ests[%d:0], 1'b1}" % (EW2 - 2))                 # 2 est + 1
    m.wire("e4p4", EW2)
    m.wire("four", EW2, expr=f"{EW2}'d4")
    m.wire("e4", EW2, expr="{ests[%d:0], 2'b0}" % (EW2 - 3))
    m.add(rnd.add, rnd.add_pins, EW2, "e4", "four", "1'b0", "e4p4", "e4p4c", "4 est + 4")
    m.wire("e2m1", EW2)
    m.wire("onee", EW2, expr=f"{EW2}'d1")
    m.wire("e2w", EW2, expr="{ests[%d:0], 1'b0}" % (EW2 - 2))
    m.sub(rnd.add, rnd.add_pins, EW2, "e2w", "onee", "e2m1", "e2m1c", "2 est - 1")
    m.wire("e4m4", EW2)
    m.sub(rnd.add, rnd.add_pins, EW2, "e4", "four", "e4m4", "e4m4c", "4 est - 4")
    m.wire("dup1", EW2)
    m.sub(rnd.add, rnd.add_pins, EW2, "d0", "e2p1", "dup1", "up1c", "d0 - (2 est + 1): (est + 1)^2 <= x")
    m.wire("up1", expr=f"~dup1[{EW2-1}]")
    m.wire("dup2", EW2)
    m.sub(rnd.add, rnd.add_pins, EW2, "d0", "e4p4", "dup2", "up2c", "d0 - (4 est + 4): (est + 2)^2 <= x")
    m.wire("up2", expr=f"~dup2[{EW2-1}]")
    m.wire("dn1", expr=f"d0[{EW2-1}]")
    m.wire("ddn1", EW2)
    m.wire("ddn1c")
    m.add(rnd.add, rnd.add_pins, EW2, "d0", "e2m1", "1'b0", "ddn1", "ddn1c", "d0 + 2 est - 1: the remainder of est - 1")
    m.wire("dn2", expr=f"ddn1[{EW2-1}]")
    m.wire("ddn2", EW2)
    m.wire("ddn2c")
    m.add(rnd.add, rnd.add_pins, EW2, "d0", "e4m4", "1'b0", "ddn2", "ddn2c", "d0 + 4 est - 4: the remainder of est - 2")
    m.wire("estp1", Q + 1)
    m.wire("estp2", Q + 1)
    m.wire("estm1", Q + 1)
    m.wire("estm2", Q + 1)
    m.wire("oneq", Q + 1, expr=f"{Q+1}'d1")
    m.wire("twoq", Q + 1, expr=f"{Q+1}'d2")
    m.add(rnd.add, rnd.add_pins, Q + 1, "est", "oneq", "1'b0", "estp1", "estp1c", "est + 1")
    m.add(rnd.add, rnd.add_pins, Q + 1, "est", "twoq", "1'b0", "estp2", "estp2c", "est + 2")
    m.sub(rnd.add, rnd.add_pins, Q + 1, "est", "oneq", "estm1", "estm1c", "est - 1")
    m.sub(rnd.add, rnd.add_pins, Q + 1, "est", "twoq", "estm2", "estm2c", "est - 2")
    m.wire("rootn", Q + 1, expr=f"(xn == 0) ? {Q+1}'d0 : up2 ? estp2 : up1 ? estp1 : dn2 ? estm2 : dn1 ? estm1 : est")
    m.wire("remn", EW2, expr="(xn == 0) ? %d'd0 : up2 ? dup2 : up1 ? dup1 : dn2 ? ddn2 : dn1 ? ddn1 : d0" % EW2)
    if normalized:
        m.assign("root", f"rootn[{Q-1}:0]")
        m.assign("rem", f"remn[{Q+1}:0]")
    else:
        m.wire("rootf", Q + 1)
        norm.descale(m, "rootn", Q + 1, "sh", "rootf", "the root de-scaled", False)
        m.umul(mul_fam, mul_pins, "rootf", Q + 1, "rootf", Q + 1, "rf2", "the root squared for the remainder")
        m.wire("xe", EW2, expr="{4'b0, x}")
        m.wire("rf2e", EW2, expr=_zext("rf2", 2 * Q + 2, EW2))
        m.wire("remf", EW2)
        m.sub(rnd.add, rnd.add_pins, EW2, "xe", "rf2e", "remf", "remfc", "the remainder x - root^2")
        m.assign("root", f"rootf[{Q-1}:0]")
        m.assign("rem", f"remf[{Q+1}:0]")
    m.comment = (f"square root ({family}): a {seed.family} reciprocal-square-root seed of {kin} input bits (error {eps0:.2e}), "
                 f"{desc} with {mul_fam} multipliers at {F} fraction bits, the root corrected by its square")
    return name, m.render()


def sqrt_sv(Q: int, family: str, pins: dict, name: str | None = None, normalized: bool = False) -> tuple:
    """(name, text): root = floor(sqrt(x)) and rem = x - root^2 of a 2Q-bit
    radicand. digit_recurrence_sqrt_combined (and restoring_nonrestoring)
    run the trial recurrence under comparator selection or the SRT
    recurrence with a selection table; srt_radix2 and srt_high_radix run
    the SRT recurrence at their radix; the functional families refine a
    reciprocal square-root seed. The functional families and the SRT
    need the radicand normalized (its leading one in the top two bits);
    normalized=True asserts that, else the module normalizes by an even
    shift."""
    pins = pins or {}
    name = name or f"fam_sqrt_{family}_q{Q}{_tag(pins)}"
    if family in FUNCTIONAL:
        if family in ("prescaled_very_high_radix", "svoboda_tung"):
            raise ValueError(f"{family}: no prescaled square root is realized")
        return _functional_sqrt_sv(Q, family, pins, name, normalized)
    if family == "online_msdf":
        raise ValueError("online_msdf: no on-line square root is realized")
    if family == "restoring_nonrestoring":
        return _trial_sqrt_sv(Q, pins, name, normalized, family)
    if family == "digit_recurrence_sqrt_combined":
        radix = _ipin(pins, "radix", 2)
        plan = {2: [1], 4: [2], 16: [2, 2], 64: [2, 2, 2]}.get(radix, [1])
        return _srt_sqrt_sv(Q, pins, name, normalized, plan, 2, family, _bpin(pins, "on_the_fly_conversion", True))
    otf = str(_pin(pins, "quotient_conversion", "on_the_fly")) == "on_the_fly"
    if family == "srt_radix2":
        return _srt_sqrt_sv(Q, pins, name, normalized, [1], 1, family, otf)
    if family == "srt_high_radix":
        a4 = 3 if str(_pin(pins, "digit_redundancy", "minimal")) == "maximal" else 2
        return _srt_sqrt_sv(Q, pins, name, normalized, _plan(_ipin(pins, "radix", 4)), a4, family, otf)
    raise ValueError(f"no square root for the family {family}")




def div_sv(N: int, D: int, Q: int, family: str, pins: dict, name: str | None = None, S: int = 0,
           normalized: bool = False) -> tuple:
    """(name, text) of a divider family: q = floor(a 2^S / b), r = a 2^S mod b."""
    pins = pins or {}
    name = name or f"fam_div_{family}_n{N}{f's{S}' if S else ''}d{D}q{Q}{_tag(pins)}"
    if family == "restoring_nonrestoring":
        return restoring_sv(N, S, D, Q, pins, name)
    if family == "digit_recurrence_sqrt_combined":
        radix = _ipin(pins, "radix", 2)
        plan = {2: [1], 4: [2], 16: [2, 2], 64: [2, 2, 2]}.get(radix, [1])
        spec = _bpin(pins, "speculation_between_subiterations", False)
        conv = "on_the_fly" if _bpin(pins, "on_the_fly_conversion", True) else "separate_positive_negative"
        return _srt_sv(N, S, D, Q, "srt_high_radix", pins, name, normalized, plan=plan, a4=2,
                       overlap=len(plan) if spec else 1, form="carry_save", conv=conv)
    if family in ("srt_radix2", "srt_high_radix"):
        return _srt_sv(N, S, D, Q, family, pins, name, normalized)
    if family in FUNCTIONAL:
        return _functional_sv(N, S, D, Q, family, pins, name, normalized)
    if family == "online_msdf":
        return _online_sv(N, S, D, Q, pins, name, normalized)
    raise ValueError(f"no module for the divider family {family}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--width", type=int, required=True)
    ap.add_argument("--family", default="restoring_nonrestoring")
    ap.add_argument("--pins", default="")
    ap.add_argument("--sqrt", action="store_true")
    ap.add_argument("--sv", default=None)
    args = ap.parse_args(argv)
    pins = dict(kv.split("=", 1) for kv in args.pins.split(",") if "=" in kv)
    try:
        if args.sqrt:
            name, text = sqrt_sv(args.width, args.family, pins)
        else:
            name, text = div_sv(args.width, args.width, args.width, args.family, pins)
    except ValueError as e:
        print(f"div: {e}", file=sys.stderr)
        return 2
    if args.sv:
        open(args.sv, "w").write(text)
        print(name)
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
