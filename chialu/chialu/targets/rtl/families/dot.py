"""The dot-accumulate families of chialu.VecDotAcc (fma_dot_spaces:
dot_acc_space), generated per mode geometry so the seed realizes a
declared core family by construction.

A module computes the finite arithmetic of one output group: the n
operand pairs of the group (and c) come in on the engine's X format
(`xa`, `xb`, `xc`), or as raw operand bits for an integer mode (`a`,
`b`, `c`); it drives `acc`, the exact sum in the seed's fixed-point
frame (AW bits, lsb 2^lo), and `y`, the same sum normalized on X
(magnitude with a sticky). The seed keeps the special values, the
zero-sign rule and the final rounding (`pack_d`, or the library rounder
of the family's `round` component for a float d).

The accumulator families (pairwise_tree, fused_csa, integer_mac,
kulisch_long_accumulator, streaming_accurate_accumulator,
block_fp_accumulation, mx_microscaling_dot, tensor_core_mixed_precision_mac,
bf16_fma_datapath, fp8_training_datapath, multi_term_fused_dot,
fused_two_term_dot, multi_precision_simd_fma) share one construction:
the products of the significands (the `mul` component: a library
multiplier or the `*` operator), an alignment into a window (the seed's
exact frame by a left shift, a window anchored at the largest exponent,
a per-level alignment in a tree, a coarse/fine two-stage shift, the
pairwise exponent differences reused, or a sorting network with
realignment lines), a sign handling (two's complement, or positive and
negative sums reduced apart and the pair selected), a reduction (a
linear chain, a binary tree of library adders, a carry-save tree of 3:2,
4:2 or 7:3 compressors with a library CPA at the root), and the
normalization to X (a leading-zero count or an anticipator on the final
adder's operands). A selected window or accumulator width is built at
that width. A geometry too large for the selected width is rejected; the
pins that round a partial result (a per-level truncation, a faithful or
truncated rounding contract, the tensor core's partial-sum rounding, a
chunked accumulation at a narrower precision) are generated as pinned,
and the comment names the contract the module then meets.

The FMA lineage (classic_fma, reduced_latency_fma, multipath_fma,
bridge_fma, mixed_precision_cascade_fma) realizes d = c + a * b for a
one-element mode: the addend aligned in parallel with the multiplier
over the 2S + Sc + 3 window, the end-around-carry, dual-adder or
complement negation, a leading-zero anticipator or a count after the
add, one normalize; the reduced-latency variant normalizes before the
add and fuses the rounding into a compound adder (the value leaves with
the ROUNDED code, so the seed packs it through the library rounder);
the multipath variant computes close and far paths and selects; the
bridge composes the library's fp multiplier and fp adder (the exact
product crossing the bridge, or rounded first under the cascade style);
the mixed-precision cascade keeps the narrow product exact into the
wider destination.

Exceptions (EXCEPTIONS): a block family declared for a scalar mode, an
FMA family for a mode with several elements under the fused contract.

Component families: a declared multiplier, adder-tree, CPA, shifter or
leading-zero family is the library's module at the actual datapath width;
an undeclared one may use the language's operator. A missing declared
module is an error, irrespective of the cost of building it.
"""
from __future__ import annotations

import argparse

from chialu.targets.rtl.families.fp import (ROUNDED, Geom, Mod as _FPMod, _clog2, _lzc, _mkx, _pin, _shift, _slit,
                                            _x_fields)
from chialu.targets.rtl.families.mul import Netlist
from chialu.targets.rtl.families.mul import reduce as _reduce_cols


class Mod(_FPMod):
    def declared_(self, name):
        return any(f" {name};" in line or f" {name} " in line for line in self.lines)

    def inst(self, kind, family, pins, width, conns, comment, signed=False):
        present = super().inst(kind, family, pins, width, conns, comment, signed)
        if not present and family:
            raise ValueError(f"requested {kind} component {family} has no {width}-bit implementation")
        return present

ACC_FAMILIES = ("pairwise_tree", "fused_csa", "integer_mac", "multi_precision_simd_fma", "fused_two_term_dot",
                "multi_term_fused_dot", "kulisch_long_accumulator", "streaming_accurate_accumulator",
                "block_fp_accumulation", "mx_microscaling_dot", "tensor_core_mixed_precision_mac",
                "bf16_fma_datapath", "fp8_training_datapath")
FMA_FAMILIES = ("classic_fma", "reduced_latency_fma", "multipath_fma", "bridge_fma", "mixed_precision_cascade_fma")
DOT_FAMILIES = {"core": ACC_FAMILIES + FMA_FAMILIES}
BLOCK_FAMILIES = ("block_fp_accumulation", "mx_microscaling_dot")

EXCEPTIONS = {
    "block_fp_accumulation, mx_microscaling_dot on a scalar mode": "the shared exponent is the block format's; a "
                                                                    "scalar mode has none",
    "classic_fma, reduced_latency_fma, multipath_fma, bridge_fma, mixed_precision_cascade_fma on a mode of several "
    "elements under the fused contract": "an FMA sums one product and the addend; several products need the "
                                         "multi-term fused dot (the sequential contract cascades FMAs)",
}


def _sub(pins: dict, prefix: str) -> dict:
    result = {k[len(prefix):]: v for k, v in pins.items() if k.startswith(prefix)}
    owner = getattr(pins, "owner", None)
    if owner:
        from chialu.targets.rtl.families.selection import SelectedPins
        return SelectedPins(owner + "." + prefix.rstrip("."), result)
    return result


def _sh(m: Mod, fam, pins: dict, src: str, width: int, amt: str, opcode: int, out: str, comment: str,
        sticky: str | None = None) -> str:
    """Shift through the declared component at the actual datapath width.

    A wide component may be expensive to simulate, but its cost never
    permits replacing a requested architecture with an operator.
    """
    if fam:
        if fam == "butterfly_network" and (width < 2 or width & (width-1)):
            if opcode not in (0, 1, 2):
                raise ValueError("a padded butterfly adapter supports shifts, not rotations")
            padded = max(2, 1 << (width-1).bit_length())
            sign = src if width == 1 else f"{src}[{width-1}]"
            fill = sign if opcode == 2 else "1'b0"
            operand = m.wire(out+"_butterfly_input", padded, expr=f"{{{{{padded-width}{{{fill}}}}}, {src}}}")
            wide_sticky = out+"_butterfly_sticky" if sticky else None
            wide = _shift(m, str(fam), pins or {}, operand, padded, amt, opcode,
                          out+"_butterfly_result", comment+" (power-of-two butterfly payload adapter)", sticky=wide_sticky)
            m.wire(out, width, expr=f"{wide}[{width-1}:0]")
            if sticky:
                direction = ">>" if opcode == 0 else "<<"
                m.wire(sticky, expr=f"{wide_sticky} | (|({src} & ~({{{width}{{1'b1}}}} {direction} {amt})))")
            return out
        return _shift(m, str(fam), pins or {}, src, width, amt, opcode, out, comment, sticky=sticky)
    expression = f"$signed({src}) >>> {amt}" if opcode == 2 else f"{src} {'<<' if opcode == 0 else '>>'} {amt}"
    m.wire(out, width, expr=expression)
    if sticky:
        m.wire(sticky, expr=f"|({src} & ~({{{width}{{1'b1}}}} {'>>' if opcode == 0 else '<<'} {amt}))")
    return out


def _tz(m: Mod, fam, pins: dict, src: str, width: int, out: str, comment: str) -> str:
    """out = the trailing-zero count of src (width.bit_length() bits) through
    the library counter when a family is declared, else a function with a
    loop."""
    nw = width.bit_length()
    if fam:
        m.wire(out, nw)          # declared before the instance that drives it (slang rejects a use before the declaration)
        if not m.inst("tzc", str(fam), pins or {}, width, f".a({src}), .n({out})", comment):
            raise ValueError(f"requested trailing-zero component {fam} has no {width}-bit implementation")
        return out
    fn = f"tzc_{width}"
    if not any(f"function automatic [{nw-1}:0] {fn}(" in ln for ln in m.lines):
        m.raw(f"  function automatic [{nw-1}:0] {fn}(input [{width-1}:0] v); integer k; begin\n"
              f"    {fn} = {width}; for (k = 0; k < {width}; k = k + 1) if (v[k] && {fn} == {width}) {fn} = k;\n"
              f"  end endfunction")
    m.wire(out, nw, expr=f"{fn}({src})")
    return out


def _lz(m: Mod, fam, pins: dict, src: str, width: int, out: str, comment: str) -> str:
    """out = the leading-zero count of src (width.bit_length() bits) through
    the library counter when a family is declared, else a function with a
    loop (a procedural block with a break re-triggers under a converter). `fam`
    is the family, or (family, its pins) so a caller that has no pins
    argument of its own still reaches the counter's own choices."""
    if isinstance(fam, tuple):
        fam, own = fam
        pins = dict(own or {}, **(pins or {}))
    if fam:
        return _lzc(m, str(fam), pins or {}, src, width, out, comment)
    nw = width.bit_length()
    fn = f"lzc_{width}"
    if not any(f"function automatic [{nw-1}:0] {fn}(" in ln for ln in m.lines):
        m.raw(f"  function automatic [{nw-1}:0] {fn}(input [{width-1}:0] v); integer k; begin\n"
              f"    {fn} = {width}; for (k = {width-1}; k >= 0; k = k - 1) if (v[k] && {fn} == {width}) {fn} = {width-1} - k;\n"
              f"  end endfunction")
    m.wire(out, nw, expr=f"{fn}({src})")
    return out


def _truthy(v) -> bool:
    return str(v).lower() in ("true", "1", "yes")


class DotGeom:
    """The geometry a dot module is generated for: n products per output
    group on the engine geometry g, S and Sc significant bits of an ab
    operand and of c (their values sit in the low bits of the X
    significand), the seed's frame (AW bits, lsb 2^lo), whether c is
    present; `intg` = (W, signed, F, Wc, signed_c, Fc) for an integer or
    fixed-point operand mode (raw operands, a signed or unsigned
    library multiplier), None for the X geometry; `fd` the d format of a
    rounding component (None when the seed packs)."""

    def __init__(self, g: Geom, n: int, S: int, Sc: int, AW: int, lo: int, acc: bool, intg=None, fd=None,
                 tokens: dict | None = None, out: str = "y", band: tuple | None = None, c_range: tuple | None = None):
        self.g, self.n, self.S, self.Sc, self.AW, self.lo, self.acc = g, n, S, Sc, AW, lo, acc
        self.intg, self.fd, self.tokens = intg, fd, tokens or {}
        self.out = out                             # "acc" (an integer, fixed or quire d) or "y" (the rest)
        # the products' exponent band (lsb weight, width): the products' part of the frame, which the bounded
        # alignment keeps the products in (the addend joins through the near window or the far word)
        self.band = band if band else (lo, AW)
        # (lsb exponent of the smallest nonzero addend, exponent of the largest finite addend + 1)
        self.c_range = c_range if c_range else (lo, lo + AW - 2)

    def ports_out(self, m: Mod):
        if self.out == "acc":
            m.port("output", "acc", self.AW, signed=True)
        else:
            m.port("output", "y", self.g.XT)

    def tag(self) -> str:
        t = (f"n{self.n}_s{self.S}c{self.Sc if self.acc else 0}_a{self.AW}l{'m' if self.lo < 0 else ''}{abs(self.lo)}"
             f"_{self.g.tag()}")
        if self.intg:
            W, sg, F, Wc, sgc, Fc = self.intg
            t += f"_i{W}{'s' if sg else 'u'}f{F}" + (f"c{Wc}{'s' if sgc else 'u'}f{Fc}" if self.acc else "")
        return t


def geom_of(fab, fc, fd, n: int, accumulate: bool = True, sr_bits: int = 8, sr: bool = False, conv=None,
            precision_formats=()) -> DotGeom:
    """The DotGeom of a mode as the seed builds it (dot_seed.frame_of)."""
    from chialu.targets.rtl.dot_seed import _sw_of, frame_of
    from chialu.verify.formats import FixedFormat, IntFormat, ScaledIntFormat
    from chialu.targets.rtl.dot_seed import _exp_range
    e, AW, lo = frame_of(fab, fc, fd, n, accumulate, sr_bits, sr, conv, precision_formats=precision_formats)
    S, Sc = _sw_of(fab), (_sw_of(fc) if accumulate else 0)
    lo_ab, hi_ab = _exp_range(fab)
    band_lo, band_hi = 2 * lo_ab, 2 * hi_ab + n.bit_length() + 1
    band = (max(band_lo, lo), min(band_hi - max(band_lo, lo) + 3, AW))
    intg = None
    plain_int = (isinstance(fab, (IntFormat, FixedFormat))
                 and not (isinstance(fab, ScaledIntFormat) and not isinstance(fab, FixedFormat))
                 and fab.encoding in ("twos_complement", "unsigned"))
    c_ok = (not accumulate) or (isinstance(fc, (IntFormat, FixedFormat)) and fc.encoding in ("twos_complement", "unsigned"))
    if plain_int and c_ok:
        intg = (fab.width, fab.encoding == "twos_complement", getattr(fab, "frac_bits", 0),
                fc.width if accumulate else 0, bool(accumulate and fc.encoding == "twos_complement"),
                getattr(fc, "frac_bits", 0) if accumulate else 0)
    out = "acc" if isinstance(fd, (IntFormat, FixedFormat, ScaledIntFormat)) else "y"
    c_range = _exp_range(fc) if accumulate else None
    result = DotGeom(Geom.of_engine(e), n, S, Sc, AW, lo, accumulate, intg, fd, e.tokens, out, band, c_range)
    result.fab = fab
    from fractions import Fraction
    bound = n*_finite_magnitude(fab)**2 + (_finite_magnitude(fc) if accumulate else 0)
    scaled = bound/Fraction(2)**lo
    result.numeric_width = max(2, int(scaled).bit_length()+1)
    return result


def _finite_magnitude(fmt):
    from fractions import Fraction
    from chialu.verify.formats import BlockFormat, FloatFormat, X87Format, PositFormat
    if isinstance(fmt, BlockFormat):
        return _finite_magnitude(fmt.elem)*_finite_magnitude(fmt.scale)
    if isinstance(fmt, X87Format):
        return fmt.core.max_finite()
    if isinstance(fmt, FloatFormat):
        return fmt.max_finite()
    if isinstance(fmt, PositFormat):
        return fmt.decode((1 << (fmt.width-1))-1)
    return max(abs(fmt.min_int), abs(fmt.max_int))*Fraction(2)**(-getattr(fmt, "frac_bits", 0))


# ---- helpers on a Mod -------------------------------------------------------------
def _inst_mul(m: Mod, fam: str | None, pins: dict, W: int, signed: bool, a: str, b: str, p: str, comment: str) -> bool:
    """p = a * b through the library multiplier of a family (False, and
    nothing emitted, for behavioral_star or a family without a module)."""
    from chialu.targets.rtl import families as FAM
    if not fam or fam == "behavioral_star":
        return False
    if fam == "truncated_fixed_width":
        from chialu.targets.rtl.families.fidelity import effective, location
        wanted = pins.get("extra_columns_kept", min(2, W))
        with location(getattr(pins, "owner", ""), fam, {"width": W, "signed": signed}):
            effective(pins, "extra_columns_kept", min(wanted, W), "actual retained columns below the product's high half")
    mod = FAM.mul_module(fam, pins, W, signed)
    if mod is None:
        raise ValueError(f"requested multiplier component {fam} has no {W}-bit implementation")
    if mod.text:
        m.extra.append(mod.text)
    m.n += 1
    ps = ", ".join(f".{k}({v})" for k, v in mod.params.items())
    m.lines.append(f"  // {comment}")
    m.lines.append(f"  {mod.name} " + (f"#({ps}) " if ps else "") + f"u{m.n} (.a({a}), .b({b}), .p({p}));")
    return True


def _multiword_product(m: Mod, tag: str, a: str, b: str, S: int, mul, tree, chunk: int = 8) -> str:
    """Exact significand product from bf16-sized words at their binary weights."""
    words = []
    count = (S + chunk - 1) // chunk
    if count < 2:
        raise ValueError("multi_word_composition requires an operand significand wider than one bf16 word")
    for index, start in enumerate(range(0, S, chunk)):
        size = min(chunk, S-start)
        for prefix, operand in (("a", a), ("b", b)):
            tail = f"{operand}[{start+size-1}:{start}]"
            expr = f"{{{chunk-size}'d0, {tail}}}" if size < chunk else tail
            m.wire(f"{tag}_{prefix}{index}", chunk, expr=expr)
    for i in range(count):
        for j in range(count):
            part = m.wire(f"{tag}_p{i}_{j}", 2*chunk)
            if not _inst_mul(m, mul[0], mul[1], chunk, False, f"{tag}_a{i}", f"{tag}_b{j}", part,
                             f"multiword product {tag}: bf16 word pair {i},{j}"):
                m.assign(part, f"{tag}_a{i} * {tag}_b{j}")
            words.append(m.wire(f"{tag}_v{i}_{j}", 2*S,
                                expr=f"{{{2*S-2*chunk}'d0, {part}}} << {(i+j)*chunk}"))
    return _sum_words(m, tag, words, 2*S, tree, "the exact weighted multiword product")


def _add(m: Mod, fam: str, pins: dict, W: int, a: str, b: str, s: str, comment: str, cin: str = "1'b0",
         cout: str | None = None):
    """s = a + b + cin through the library adder of a family (a behavioral add without one)."""
    co = cout or f"{s}_co"
    m.dot_last_cpa = (fam, dict(pins or {}))
    if cout is None:
        m.wire(co)
    if not m.inst("adder", fam, pins, W, f".a({a}), .b({b}), .cin({cin}), .s({s}), .cout({co})", comment):
        if fam:
            raise ValueError(f"requested adder component {fam} has no {W}-bit implementation")
        m.assign(f"{{{co}, {s}}}", f"{{1'b0, {a}}} + {{1'b0, {b}}} + {cin}")


CPA_DEFAULT = ("parallel_prefix", {"topology": "sklansky"})   # the undeclared CPA: a prefix adder (docs/work-plan.md item 4)


class _LeadingZeroChoice(str):
    def __new__(cls, pins):
        value = str.__new__(cls, str(pins.get("lza.family", "lzc_after_add")))
        value.pins = _sub(pins, "lza.")
        return value


def _complete_lza_normalize(m, tag, W, choice, lza_ops, norm, sum_word, extra_st, magnitude_input,
                            low_carry=None, offset=None):
    """Derive the shift from a full selected adder on the real final operands.

    The original reduction result remains the value being normalized.
    The predictor uses the genuine final operand pair, preserving all
    sign/string/correction choices of the floating-point adder contract.
    A magnitude input names its own `low_carry`, the two-bit value the
    lookahead adds to the operands so that their sum is the magnitude's
    high part exactly: the carry the dropped sticky lsb sends up on a
    sum or a non-negated difference, and one more on a negated
    difference Y - X, whose high part is -(a + b + c0) - 1 (the lsb
    equation of the magnitude recovers the complement of that carry, and
    a shift of the operands before the add makes it unrecoverable). The
    exact operands make the predicted shift exact, so the result leaves
    normalized; the sticky lsb's borrow across a power of two is the case
    the recovered carry mispredicted by one. `offset` (expression, width)
    is a shift the magnitude already took before the add (the
    normalize-before-add path hands the lookahead the unshifted operands,
    whose words do not wrap), subtracted from the predicted count.
    """
    from chialu.targets.rtl.families import fp
    from chialu.targets.rtl.families.fidelity import effective
    a, b = lza_ops
    sw, xw = W+1, W+5
    normal_width = sw
    if norm[0] == "butterfly_network":
        # This topology requires a power of two. Pad its internal operand
        # and X normalizers while keeping the actual final word at W.
        normal_width = 1 << (sw-1).bit_length()
        xw = 1 << (xw-1).bit_length()
    ew = max(8, xw.bit_length()+3)
    geom = Geom(xw, ew, sw)
    cpa, cpa_pins = getattr(m, "dot_last_cpa", CPA_DEFAULT)
    pins = {"sig_adder.family": cpa, "norm.family": "single_barrel",
            "subnormal_representation": "pseudo_normalized_wide_exponent"}
    pins.update({"sig_adder."+key: value for key, value in cpa_pins.items() if key != "family"})
    pins.update({"lz."+key: value for key, value in choice.pins.items()})
    pins["lz.family"] = "lza"
    if choice.pins.get("string_form", "single_indicator") == "dual_pos_neg_strings":
        pins["operand_order"] = "shift_each_operand"
    if norm[0]:
        pins["norm.shifter.family"] = norm[0]
        pins.update({"norm.shifter."+key: value for key, value in norm[1].items() if key != "family"})
    name = f"fam_dot_lza_w{W}{fp._tag(pins)}"
    captured = {}
    token = fp.capture_modules.set(captured)
    try:
        fp.add_sv(geom, "single_path", pins, name=name)
    finally:
        fp.capture_modules.reset(token)
    predictor = captured[name]
    predictor.port("output", "predict_zero")
    predictor.assign("predict_zero", "a_z ? b_z : b_z ? a_z : zero_f")
    m.extra.append(predictor.render())
    # Recover the real final CPA carry-in from its low-bit equation.
    # A negative floor with a sticky uses its ceiling magnitude.
    carry = m.wire(tag+"_look_cin", expr=f"{sum_word}[0] ^ {a}[0] ^ {b}[0]")
    adjust = f"({extra_st}) && {sum_word}[{W-1}]" if not magnitude_input else "1'b0"
    if magnitude_input:
        left = f"{{{a}[{W-1}], {a}}}"
    else:
        overflow = m.wire(tag+"_look_wrap", expr=f"({a}[{W-1}] == {b}[{W-1}]) && ({sum_word}[{W-1}] != {a}[{W-1}])")
        # Carry-save rows name a modular word sum. Remove its redundant
        # high carry before interpreting the two rows as exact X values.
        left = f"{{{a}[{W-1}] ^ {overflow}, {a}}}"
    m.wire(tag+"_look_a", sw, signed=True, expr=left)
    if magnitude_input and low_carry is not None:
        m.wire(tag+"_look_adj", 2, expr=low_carry)
        m.wire(tag+"_look_b", sw, signed=True,
               expr=f"$signed({{{b}[{W-1}], {b}}}) + $signed({{{{({sw}-2){{1'b0}}}}, {tag}_look_adj}})")
    else:
        m.wire(tag+"_look_b", sw, signed=True,
               expr=f"$signed({{{b}[{W-1}], {b}}}) + {carry} + ({adjust})")
    for side in ("a", "b"):
        row = f"{tag}_look_{side}"
        mag = m.wire(row+"m", sw, expr=f"{row}[{sw-1}] ? -{row} : {row}")
        normal_input = mag
        if normal_width > sw:
            normal_input = m.wire(row+"_normal_input", normal_width, expr=f"{{{normal_width-sw}'d0, {mag}}}")
        encoder = choice.pins.get("encoder.family")
        _lz(m, encoder, _sub(choice.pins, "encoder."), normal_input, normal_width, row+"_lz", "normalize a real lookahead operand")
        count = m.wire(row+"_count", _clog2(normal_width), expr=f"({mag} == 0) ? 0 : {row}_lz[{_clog2(normal_width)-1}:0]")
        nm = _sh(m, norm[0], norm[1], normal_input, normal_width, count, 0, row+"_normalized", "the lookahead operand's declared normalizer")
        exponent = m.wire(row+"_exp", ew, signed=True, expr=f"-$signed({{1'b0, {count}}})")
        pad = f"{xw-normal_width}'d0, " if xw > normal_width else ""
        m.wire(row+"x", geom.XT, expr=f"{{2'd0, {row}[{sw-1}], {exponent}, {pad}{nm}, 1'b0}}")
    look = m.wire(tag+"_look_result", geom.XT)
    zero = m.wire(tag+"_look_zero")
    m.n += 1
    m.raw(f"  {name} u{m.n} (.xa({tag}_look_ax), .xb({tag}_look_bx), .sub(1'b0), .y({look}), .predict_zero({zero}));")
    exp = m.wire(tag+"_look_exp", ew, signed=True, expr=f"$signed({look}[{xw+ew}:{xw+1}])")
    bypass = m.wire(tag+"_look_bypass", expr=f"({tag}_look_am == 0) || ({tag}_look_bm == 0)")
    taken = f" - $signed({{{{({ew}-{offset[1]}){{1'b0}}}}, {offset[0]}}})" if offset else ""
    shift = m.wire(tag+"_look_shift", ew, signed=True,
                   expr=f"({bypass} ? {_slit(ew, W-normal_width)} : {_slit(ew, W-xw)}) - {exp}{taken}")
    lw = _clog2(W)
    count = m.wire(tag+"_lzs", lw,
                   expr=f"({tag}_mag == 0 || {shift} < 0) ? 0 : ({shift} >= {W}) ? {lw}'d{W-1} : {shift}[{lw-1}:0]")
    m.wire(tag+"_lz", lw+1, expr=f"{{1'b0, {count}}}")
    nm = _sh(m, norm[0], norm[1], tag+"_mag", W, count, 0, tag+"_nm_shifted", "normalize the actual reduction result by its selected lookahead shift")
    m.wire(tag+"_nm", W, expr=f"{zero} ? {W}'d0 : {nm}")
    for key in ("correction_scheme", "string_form", "split_string_select", "indicator_restriction", "zero_result_detect"):
        if key in choice.pins:
            effective({"lza."+key: choice.pins[key]}, "lza."+key, choice.pins[key], "full selected LZA on the actual final operand pair")


def _cpa_of(pins: dict, *keys: str) -> tuple:
    """(family, sub-pins) of the first CPA component the pins name; the
    default prefix adder when none is declared (a declared prefix family
    expands to its graph)."""
    for k in keys:
        if f"{k}.family" in pins:
            return str(pins[f"{k}.family"]), _sub(pins, f"{k}.")
    return CPA_DEFAULT[0], dict(CPA_DEFAULT[1])


def _render_nl(m: Mod, nl: Netlist, tag: str):
    """The netlist's assigns into the module, its wire names prefixed by
    the tag (several netlists may share a module)."""
    import re
    for line in nl.render():
        m.raw(re.sub(r"\b(t|pp)(\d+)\b", lambda mo: f"{tag}_{mo.group(1)}{mo.group(2)}", line))


def _rows_of(cols: list, W: int, tag: str) -> tuple:
    """The two rows of reduced columns as concatenations (tag-prefixed)."""
    import re
    rs = "{" + ", ".join((c[0] if len(c) > 0 else "1'b0") for c in reversed(cols)) + "}"
    rc = "{" + ", ".join((c[1] if len(c) > 1 else "1'b0") for c in reversed(cols)) + "}"
    fix = lambda s: re.sub(r"\b(t|pp)(\d+)\b", lambda mo: f"{tag}_{mo.group(1)}{mo.group(2)}", s)
    return fix(rs), fix(rc)


def _tree_of(pins: dict, *keys: str) -> tuple:
    """(adder-tree family, compressor, cpa family, cpa pins) of the first
    adder_tree component the pins name (linear_chain by default)."""
    for k in keys:
        fam = pins.get(f"{k}.family")
        if fam:
            fam = str(fam)
            comp = str(_pin(pins, f"{k}.compressor", "3:2"))
            cfam, cpins = _cpa_of(pins, f"{k}.final_cpa", f"{k}.cpa")
            return fam, comp, cfam, cpins
    cfam, cpins = _cpa_of(pins, "final_cpa", "cpa")
    return "linear_chain", "3:2", cfam, cpins


def _reduce_7_3(nl: Netlist, cols: list) -> list:
    """Carry-save reduction with 7:3 counters (four full adders each) down
    to two rows; the tail of a column below seven bits uses 3:2 cells."""
    n = len(cols)
    guard = 0
    while max((len(c) for c in cols), default=0) > 2:
        guard += 1
        if guard > 64:
            raise ValueError("7:3 reduction did not converge")
        new = [[] for _ in range(n)]
        for c in range(n):
            bits = list(cols[c])
            while len(bits) >= 7:
                x = [bits.pop(0) for _ in range(7)]
                s1, c1 = nl.fa(x[0], x[1], x[2])
                s2, c2 = nl.fa(x[3], x[4], x[5])
                s3, c3 = nl.fa(s1, s2, x[6])          # weight 1 sum; c1 c2 c3 at weight 2
                s4, c4 = nl.fa(c1, c2, c3)            # weight 2 sum; carry at weight 4
                new[c].append(s3)
                if c + 1 < n:
                    new[c + 1].append(s4)
                if c + 2 < n:
                    new[c + 2].append(c4)
            while len(bits) >= 3:
                s, co = nl.fa(bits.pop(0), bits.pop(0), bits.pop(0))
                new[c].append(s)
                if c + 1 < n:
                    new[c + 1].append(co)
            new[c] += bits
        cols = new
    return cols


def _sum_words(m: Mod, tag: str, words: list, W: int, tree: tuple, comment: str) -> str:
    """The sum (mod 2^W) of two's complement words through an adder tree:
    a linear chain or a binary tree of library adders, or a carry-save
    tree of compressors with the library CPA at the root. Returns the
    sum's name; `m.last_add` holds the final adder's operands (for an
    anticipator)."""
    fam, comp, cfam, cpins = tree
    m.last_add = None
    if not words:
        return m.wire(f"{tag}_zero", W, expr=f"{W}'d0")
    if len(words) == 1:
        return words[0]
    if fam == "csa_tree" and len(words) >= 3:
        nl = Netlist()
        cols = [[f"{w}[{k}]" for w in words] for k in range(W)]
        if comp == "7:3":
            cols = _reduce_7_3(nl, cols)
        else:
            cols = _reduce_cols(nl, cols, "dadda", "4_2" if comp == "4:2" else "3_2")
        m.raw(f"  // {comment}: carry-save tree of {comp} compressors over {len(words)} words ({nl.fa_count} full adders, "
              f"{nl.ha_count} half adders)")
        _render_nl(m, nl, tag)
        rs, rc = _rows_of(cols, W, tag)
        m.wire(f"{tag}_rs", W, expr=rs)
        m.wire(f"{tag}_rc", W, expr=rc)
        m.wire(f"{tag}_sum", W)
        _add(m, cfam, cpins, W, f"{tag}_rs", f"{tag}_rc", f"{tag}_sum", f"{comment}: the root CPA ({cfam})")
        m.last_add = (f"{tag}_rs", f"{tag}_rc")
        return f"{tag}_sum"
    if fam == "binary_tree":
        level, k = list(words), 0
        while len(level) > 1:
            nxt = []
            for i in range(0, len(level) - 1, 2):
                out = m.wire(f"{tag}_l{k}_{i // 2}", W)
                _add(m, cfam, cpins, W, level[i], level[i + 1], out, f"{comment}: tree level {k} adder ({cfam})")
                m.last_add = (level[i], level[i + 1])
                nxt.append(out)
            if len(level) % 2:
                nxt.append(level[-1])
            level, k = nxt, k + 1
        return level[0]
    cur = words[0]
    for i, w in enumerate(words[1:]):
        out = m.wire(f"{tag}_c{i}", W)
        _add(m, cfam, cpins, W, cur, w, out, f"{comment}: chain adder {i} ({cfam})")
        m.last_add = (cur, w)
        cur = out
    return cur


def _neg(m: Mod, name: str, u: str, s: str, W: int) -> str:
    return m.wire(name, W, expr=f"{s} ? (~{u} + {W}'d1) : {u}")


def _place(m: Mod, name: str, mag: str, width: int, e: str, EWX: int, lo: int, AW: int, shifter: str, spins: dict,
           comment: str, right_ok: bool = True) -> str:
    """{name} = mag * 2^(e - lo) as an AW-bit word of the frame (a left
    shift through the alignment shifter; a right shift when e - lo is
    negative, which only drops zero bits below the value; a zero for an
    amount beyond the frame, which only a zero value has)."""
    aw = _clog2(AW)
    sh = m.wire(f"{name}_sh", EWX, signed=True, expr=f"{e} - {_slit(EWX, lo)}")
    ext = m.wire(f"{name}_x", AW, expr=f"{{{{({AW}-{width}){{1'b0}}}}, {mag}}}" if AW > width else mag)
    amt = m.wire(f"{name}_am", aw, expr=f"({sh} < 0 || {sh} >= {AW}) ? {aw}'d0 : {sh}[{aw-1}:0]")
    _sh(m, shifter, spins, ext, AW, amt, 0, f"{name}_l", comment)
    if right_ok:
        m.wire(f"{name}_ng", EWX, signed=True, expr=f"-{sh}")
        m.wire(f"{name}_ar", aw, expr=f"({sh} >= 0 || {sh} <= -{AW}) ? {aw}'d0 : {name}_ng[{aw-1}:0]")
        _sh(m, shifter, spins, ext, AW, f"{name}_ar", 1, f"{name}_r", f"{comment} (the right shift of a value below the frame)")
        return m.wire(name, AW, expr=f"({sh} >= {AW} || {sh} <= -{AW}) ? {AW}'d0 : ({sh} < 0) ? {name}_r : {name}_l")
    return m.wire(name, AW, expr=f"({sh} >= {AW} || {sh} < 0) ? {AW}'d0 : {name}_l")


def _magnitude(m: Mod, tag: str, word: str, W: int, extra_st: str):
    """{tag}_neg and {tag}_mag of a two's complement word. With a sticky
    (extra_st) the word is the floor of the exact value (the truncation of
    a negative term borrowed one lsb), so the magnitude of a negative word
    with a nonzero fraction is its one's complement: exact in (w, w + 1)
    means |exact| in (-w - 1, -w)."""
    m.wire(f"{tag}_neg", expr=f"{word}[{W-1}]")
    if extra_st == "1'b0":
        m.wire(f"{tag}_mag", W, expr=f"{tag}_neg ? (~{word} + {W}'d1) : {word}")
    else:
        m.wire(f"{tag}_mag", W, expr=f"{tag}_neg ? (~{word} + {{{{({W}-1){{1'b0}}}}, !({extra_st})}}) : {word}")


def _normalize(m: Mod, tag: str, W: int, lz_fam: str, lzc_fam: str, lza_ops: tuple | None, norm: tuple,
               sum_word: str | None = None, extra_st: str = "1'b0", magnitude_input: bool = False,
               low_carry: str | None = None, offset: tuple | None = None):
    """{tag}_nm, the magnitude {tag}_mag with its leading one at bit W-1,
    and {tag}_lz, the shift (clog2(W)+1 bits): the count by a leading-zero
    counter on the magnitude, or by the anticipator on the final adder's
    operands (lza_ops) with a correction after the shift; the shifter of
    the `norm_shifter` slot (norm = (family, pins)). `low_carry` and
    `offset` are a magnitude input's lookahead corrections
    (_complete_lza_normalize)."""
    lw = _clog2(W)
    if lz_fam == "lza" and lza_ops is None:
        raise ValueError("lza requires the final adder's operands; this construction has no final two-operand adder")
    if lz_fam == "lza" and isinstance(lz_fam, _LeadingZeroChoice):
        _complete_lza_normalize(m, tag, W, lz_fam, lza_ops, norm, sum_word, extra_st, magnitude_input, low_carry, offset)
        return
    if lz_fam == "lza" and lza_ops is not None:
        a_src, b_src = lza_ops
        m.wire(f"{tag}_t", W, expr=f"{a_src} ^ {b_src}")
        m.wire(f"{tag}_g", W, expr=f"{a_src} & {b_src}")
        m.wire(f"{tag}_z", W, expr=f"~{a_src} & ~{b_src}")
        m.wire(f"{tag}_f", W)
        m.raw(f"  genvar k_{tag};")
        m.raw(f"  generate for (k_{tag} = 0; k_{tag} < {W}; k_{tag} = k_{tag} + 1) begin : lza_{tag}")
        m.raw(f"    if (k_{tag} == {W-1}) begin : top_\n      assign {tag}_f[k_{tag}] = {tag}_t[k_{tag}] & ({tag}_g[k_{tag}] & ~{tag}_z[k_{tag}-1] | {tag}_z[k_{tag}] & ~{tag}_g[k_{tag}-1]) | ~{tag}_t[k_{tag}] & ({tag}_z[k_{tag}] & ~{tag}_z[k_{tag}-1] | {tag}_g[k_{tag}] & ~{tag}_g[k_{tag}-1]);")
        m.raw(f"    end else if (k_{tag} == 0) begin : bot_\n      assign {tag}_f[k_{tag}] = {tag}_t[k_{tag}+1] & "
              f"({tag}_g[k_{tag}] | {tag}_z[k_{tag}]) | ~{tag}_t[k_{tag}+1] & ({tag}_z[k_{tag}] | {tag}_g[k_{tag}]);")
        m.raw(f"    end else begin : mid_\n      assign {tag}_f[k_{tag}] = {tag}_t[k_{tag}+1] & ({tag}_g[k_{tag}] & "
              f"~{tag}_z[k_{tag}-1] | {tag}_z[k_{tag}] & ~{tag}_g[k_{tag}-1]) | ~{tag}_t[k_{tag}+1] & "
              f"({tag}_z[k_{tag}] & ~{tag}_z[k_{tag}-1] | {tag}_g[k_{tag}] & ~{tag}_g[k_{tag}-1]);")
        m.raw("    end\n  end endgenerate")
        _lz(m, lzc_fam, {}, f"{tag}_f", W, f"{tag}_lzf", f"{tag}: leading zeros of the anticipator's indicator string")
        m.wire(f"{tag}_lzs", lw, expr=f"({tag}_f == 0) ? {lw}'d0 : {tag}_lzf[{lw-1}:0]")
        # the anticipator errs by one position either way on two's complement operands (a negative power of
        # two's leading zero sits one below its magnitude's leading one), the final adder's carry-in and the
        # floor convention's magnitude by one more: the shift stops one short and a correction of up to three
        # positions finishes
        m.wire(f"{tag}_lzm", lw, expr=f"({tag}_lzs == 0) ? {lw}'d0 : ({tag}_lzs - {lw}'d1)")
        _sh(m, norm[0], norm[1], f"{tag}_mag", W, f"{tag}_lzm", 0, f"{tag}_nm0", f"{tag}: the normalize shifter")
        m.wire(f"{tag}_fix", 2, expr=f"{tag}_nm0[{W-1}] ? 2'd0 : {tag}_nm0[{W-2}] ? 2'd1 : {tag}_nm0[{W-3}] ? 2'd2 : 2'd3")
        m.wire(f"{tag}_nm", W, expr=f"{tag}_nm0 << {tag}_fix")
        m.wire(f"{tag}_lz", lw + 1, expr=f"{{1'b0, {tag}_lzm}} + {tag}_fix")
    else:
        _lz(m, lzc_fam, {}, f"{tag}_mag", W, f"{tag}_lzc", f"{tag}: the leading-zero count of the magnitude")
        m.wire(f"{tag}_lzs", lw, expr=f"({tag}_mag == 0) ? {lw}'d0 : {tag}_lzc[{lw-1}:0]")
        m.wire(f"{tag}_lz", lw + 1, expr=f"{{1'b0, {tag}_lzs}}")
        _sh(m, norm[0], norm[1], f"{tag}_mag", W, f"{tag}_lzs", 0, f"{tag}_nm", f"{tag}: the normalize shifter")


def _to_x(m: Mod, tag: str, acc: str, AW: int, lo: int, g: Geom, lz_fam: str, lzc_fam: str, extra_st: str = "1'b0",
          lza_ops: tuple | None = None, norm: tuple = (None, {})) -> str:
    """y_<tag>: the X of a signed frame word (leading one to bit XW-1 of
    the significand, the rest as sticky); the count by a leading-zero
    counter on the magnitude, or by the anticipator on the final adder's
    operands (lza_ops) with the correction."""
    XW, EW, XT = g.XW, g.EW, g.XT
    lw = _clog2(AW)
    _magnitude(m, tag, acc, AW, extra_st)
    _normalize(m, tag, AW, lz_fam, lzc_fam, lza_ops, norm, sum_word=acc, extra_st=extra_st)
    assert AW >= XW
    m.wire(f"{tag}_sig", XW, expr=f"{tag}_nm[{AW-1}:{AW-XW}]")
    m.wire(f"{tag}_st", expr=(f"(|{tag}_nm[{AW-XW-1}:0]) | {extra_st}" if AW > XW else extra_st))
    m.wire(f"{tag}_e", EW, signed=True,
           expr=f"{_slit(EW, lo + AW - XW)} - $signed({{{{({EW}-{lw+1}){{1'b0}}}}, {tag}_lz}})")
    m.wire(f"{tag}_zero", expr=f"({tag}_mag == 0) && !({extra_st})")
    zero_x = _mkx(g, "2'd0", "1'b0", f"{EW}'sd0", f"{XW}'d0", "1'b0")
    return m.wire(f"y_{tag}", XT, expr=f"{tag}_zero ? {zero_x} : "
                                        f"{_mkx(g, '2' + chr(39) + 'd0', tag + '_neg', tag + '_e', tag + '_sig', tag + '_st')}")


def _to_x_w(m: Mod, tag: str, word: str, Wn: int, lo_expr: str, EWX: int, g: Geom, lz_fam: str, lzc_fam: str,
            extra_st: str = "1'b0", lza_ops: tuple | None = None, mag_in: bool = False, sign_expr: str = "1'b0",
            norm: tuple = (None, {}), low_carry: str | None = None, offset: tuple | None = None) -> str:
    """y_<tag> of a signed window word whose lsb exponent is a wire (or of
    a magnitude with its sign when mag_in; `low_carry` and `offset` are
    then the anticipator's corrections, _complete_lza_normalize)."""
    XW, EW, XT = g.XW, g.EW, g.XT
    lw = _clog2(Wn)
    if Wn < XW:
        if isinstance(lz_fam, _LeadingZeroChoice) and lz_fam == "lza" and lza_ops is not None:
            if mag_in:
                m.wire(tag+"_neg", expr=sign_expr)
                m.wire(tag+"_mag", Wn, expr=word)
            else:
                _magnitude(m, tag, word, Wn, extra_st)
            _normalize(m, tag, Wn, lz_fam, lzc_fam, lza_ops, norm, sum_word=word,
                       extra_st=extra_st, magnitude_input=mag_in, low_carry=low_carry, offset=offset)
            m.wire(tag+"_sig", XW, expr=f"{{{tag}_nm, {XW-Wn}'d0}}")
            m.wire(tag+"_wide_exp", EWX, signed=True,
                   expr=f"{lo_expr} - {_slit(EWX, XW-Wn)} - $signed({{1'b0, {tag}_lz}})")
            m.wire(tag+"_e", EW, signed=True, expr=f"{tag}_wide_exp[{EW-1}:0]")
            return m.wire("y_"+tag, XT, expr=_mkx(g, "2'd0", tag+"_neg", tag+"_e", tag+"_sig", extra_st))
        if mag_in:
            m.wire(f"{tag}_wx", XW, expr=f"{{{{({XW}-{Wn}){{1'b0}}}}, {word}}} << {XW - Wn}")
            m.wire(f"{tag}_lox", EWX, signed=True, expr=f"{lo_expr} - {_slit(EWX, XW - Wn)}")
            return _to_x_w(m, tag + "w", f"{tag}_wx", XW, f"{tag}_lox", EWX, g, lz_fam, lzc_fam, extra_st, None, True, sign_expr, norm)
        # A negative window with a fractional tail represents its floor.
        # Convert that floor to magnitude before adding zero padding;
        # subtracting one after padding would borrow a smaller-weight bit.
        _magnitude(m, tag + "p", word, Wn, extra_st)
        m.wire(f"{tag}_wx", XW, expr=f"{{{{({XW}-{Wn}){{1'b0}}}}, {tag}p_mag}} << {XW-Wn}")
        m.wire(f"{tag}_lox", EWX, signed=True, expr=f"{lo_expr} - {_slit(EWX, XW-Wn)}")
        return _to_x_w(m, tag + "w", f"{tag}_wx", XW, f"{tag}_lox", EWX, g, lz_fam, lzc_fam, extra_st, None,
                       mag_in=True, sign_expr=f"{tag}p_neg", norm=norm)
    if mag_in:
        m.wire(f"{tag}_neg", expr=sign_expr)
        m.wire(f"{tag}_mag", Wn, expr=word)
    else:
        _magnitude(m, tag, word, Wn, extra_st)
    _normalize(m, tag, Wn, lz_fam, lzc_fam, lza_ops, norm, sum_word=word, extra_st=extra_st, magnitude_input=mag_in,
               low_carry=low_carry, offset=offset)
    m.wire(f"{tag}_sig", XW, expr=f"{tag}_nm[{Wn-1}:{Wn-XW}]")
    m.wire(f"{tag}_st", expr=(f"(|{tag}_nm[{Wn-XW-1}:0]) | {extra_st}" if Wn > XW else extra_st))
    m.wire(f"{tag}_e0", EWX, signed=True, expr=f"{lo_expr} + {_slit(EWX, Wn - XW)} - $signed({{{{({EWX}-{lw+1}){{1'b0}}}}, {tag}_lz}})")
    m.wire(f"{tag}_e", EW, signed=True, expr=f"{tag}_e0[{EW-1}:0]")
    m.wire(f"{tag}_zero", expr=f"({tag}_mag == 0) && !({extra_st})")
    zero_x = _mkx(g, "2'd0", "1'b0", f"{EW}'sd0", f"{XW}'d0", "1'b0")
    return m.wire(f"y_{tag}", XT, expr=f"{tag}_zero ? {zero_x} : "
                                        f"{_mkx(g, '2' + chr(39) + 'd0', tag + '_neg', tag + '_e', tag + '_sig', tag + '_st')}")


def _frame_of_window(m: Mod, tag: str, word: str, Wn: int, lo_expr: str, EWX: int, AW: int, lo: int) -> str:
    """acc_<tag>: a signed window word moved into the seed's frame (lsb 2^lo)."""
    W2 = max(Wn, AW)
    m.wire(f"{tag}_dl", EWX, signed=True, expr=f"{lo_expr} - {_slit(EWX, lo)}")
    m.wire(f"{tag}_sx", W2, signed=True, expr=f"$signed({word})" if W2 == Wn else f"{{{{({W2}-{Wn}){{{word}[{Wn-1}]}}}}, {word}}}")
    m.wire(f"{tag}_dlp", EWX, signed=True, expr=f"-{tag}_dl")
    m.wire(f"{tag}_fl", W2, signed=True, expr=f"({tag}_dl >= 0) ? ({tag}_sx <<< {tag}_dl[{_clog2(W2)-1}:0]) : ({tag}_sx >>> {tag}_dlp[{_clog2(W2)-1}:0])")
    return m.wire(f"acc_{tag}", AW, signed=True, expr=f"{tag}_fl[{AW-1}:0]")


def _round_trip(m: Mod, tag: str, x: str, fmt, g: Geom, tokens: dict, rnd: str, word: str, ftz: str, comment: str,
                rpins: dict | None = None) -> tuple:
    """(mag, width, exp) of an X value rounded to a float format and read
    back: the library rounder (its rounding structure from the `round`
    slot's pins) and unpacker of the format (a partial sum rounded to a
    narrower accumulate precision)."""
    from chialu.targets.rtl.families import fp
    from chialu.targets.rtl.engine import FW
    from chialu.verify.formats import _mask
    c = fmt
    rn, rt = fp.round_sv(c, g, "dedicated_per_op", dict(rpins or {}), tokens)
    un, ut = fp.unpack_sv(c, g, "per_unit_unpack", {})
    m.extra.append(rt)
    m.extra.append(ut)
    W = c.width
    m.wire(f"{tag}_fl", FW)
    if not hasattr(m, "round_flags"):
        m.round_flags = []
    m.round_flags.append(f"{tag}_fl")
    m.wire(f"{tag}_bits", W)
    m.n += 1
    m.raw(f"  // {comment}: rounded to {c.name} by the library rounder")
    m.raw(f"  {rn} u{m.n} (.x({x}), .rnd({rnd}), .word({word}), .ftz({ftz}), .fl({tag}_fl), .bits({tag}_bits));")
    m.wire(f"{tag}_u", g.VW + 1)
    m.n += 1
    m.raw(f"  {un} u{m.n} (.b({tag}_bits), .daz(1'b0), .u({tag}_u));")
    SW, EW = g.SW, g.EW
    m.wire(f"{tag}_rsig", SW, expr=f"{tag}_u[{SW-1}:0]")
    m.wire(f"{tag}_re", EW, signed=True, expr=f"$signed({tag}_u[{SW+EW-1}:{SW}])")
    m.wire(f"{tag}_rs", expr=f"{tag}_u[{SW+EW}]")
    m.wire(f"{tag}_rsp", 2, expr=f"{tag}_u[{SW+EW+2}:{SW+EW+1}]")
    return f"{tag}_rsig", SW, f"{tag}_re", f"{tag}_rs"


def _rounding_flags(m: Mod) -> bool:
    flags = getattr(m, "round_flags", ())
    if not flags:
        return False
    from chialu.targets.rtl.engine import FW
    m.port("output", "fl", FW)
    m.assign("fl", " | ".join(flags))
    return True


def _window_flags(m: Mod, sticky: str):
    from chialu.targets.rtl.engine import FW, flag_bit
    if not hasattr(m, "round_flags"):
        m.round_flags = []
    m.round_flags.append(f"(({sticky}) ? {FW}'d{1 << flag_bit('inexact')} : {FW}'d0)")


def _expansion_outputs(m: Mod, dg: DotGeom, pins: dict, product: str, result: str):
    """Expose total, addition and multiplication residuals as rounded words."""
    from chialu.targets.rtl.engine import FW
    g, AW, lo = dg.g, dg.AW, dg.lo
    XW, EW, EWX = g.XW, g.EW, g.EW + 3
    fd = dg.fd
    operators = str(pins.get("error_term_ops", "addition"))
    ports = ["d_error"]
    if operators in ("addition", "both"):
        ports.append("d_add_error")
    if operators in ("multiplication", "both"):
        ports.append("d_mul_error")
    preserve = _truthy(pins.get("exact_product_preserved", True))
    cfam, cpins = _cpa_of(pins, "cpa")
    norm = (pins.get("norm_shifter.family"), _sub(pins, "norm_shifter."))
    lzc = pins.get("lza.counter.family") or pins.get("lza.encoder.family")
    if lzc:
        lzc = (lzc, _sub(pins, "lza.counter." if pins.get("lza.counter.family") else "lza.encoder."))
    copy = pins.get("error_term_normalization", "dedicated") == "on_demand_copy"
    lz = _LeadingZeroChoice(dict(pins, **{"lza.family": pins.get("lza.family", "lza")})) if copy else "lzc_after_add"
    rpins = {key: value for key, value in pins.items() if key.startswith("round.")}

    def frame(tag, x):
        _x_fields(m, x, g, tag + "_")
        ex = m.wire(tag + "_ex", EWX, signed=True, expr=f"$signed({{{{3{{{tag}_e[{EW-1}]}}}}, {tag}_e}})")
        raw = _place(m, tag + "_u", tag + "_sig", XW, ex, EWX, lo, AW,
                     pins.get("align.shifter.family"), _sub(pins, "align.shifter."), "an expansion term in the exact frame")
        return _neg(m, tag + "_v", raw, tag + "_s", AW)

    def rounded_frame(tag, x, rounding="rnd", ftz="1'b0"):
        mag, _, exp, sign = _round_trip(m, tag, x, fd, g, dg.tokens, rounding, "word", ftz, "the expansion projection", rpins)
        projection_flags = m.round_flags.pop()
        ex = m.wire(tag + "_ex", EWX, signed=True, expr=f"$signed({{{{3{{{exp}[{EW-1}]}}}}, {exp}}})")
        raw = _place(m, tag + "_placed", mag, g.SW, ex, EWX, lo, AW,
                     pins.get("align.shifter.family"), _sub(pins, "align.shifter."), "the projected value in the exact frame")
        return _neg(m, tag + "_v", raw, sign, AW), projection_flags

    exact_product = frame("xe_p", product)
    addend = frame("xe_c", "xc")
    main, _ = rounded_frame("xe_main", result, ftz="ftz")
    conditions = [f"xa[{g.XT-1}:{g.XT-2}] == 0", f"xb[{g.XT-1}:{g.XT-2}] == 0",
                  f"xc[{g.XT-1}:{g.XT-2}] == 0", "xe_main_rsp == 0"]
    projected = None
    product_flags = None
    if not preserve or "d_mul_error" in ports:
        projected, product_flags = rounded_frame("xe_product", product, "3'd0")
    m.wire("xe_valid", expr=" && ".join(conditions))
    if projected is not None:
        m.wire("xe_project_valid", expr="xe_valid && xe_product_rsp == 0")
    if "d_mul_error" in ports:
        m.round_flags.append(f"(xe_valid ? {product_flags} : {FW}'d0)")
    used = exact_product if preserve else projected
    full = m.wire("xe_full", AW)
    _add(m, cfam, cpins, AW, exact_product, addend, full, "the exact product plus addend")
    used_sum = full
    if not preserve and "d_add_error" in ports:
        used_sum = m.wire("xe_used", AW)
        _add(m, cfam, cpins, AW, used, addend, used_sum, "the projected product plus addend")
    residuals = {"d_error": (full, main), "d_add_error": (used_sum, main), "d_mul_error": (exact_product, projected)}
    for port in ports:
        left, right = residuals[port]
        inverse = m.wire(port + "_subtrahend", AW, expr=f"~{right}")
        difference = m.wire(port + "_frame", AW)
        _add(m, cfam, cpins, AW, left, inverse, difference, "the exact residual subtraction", "1'b1")
        x = _to_x(m, port, difference, AW, lo, g, lz, lzc,
                  lza_ops=(left, inverse) if copy else None, norm=norm)
        _round_trip(m, port + "_pack", x, fd, g, dg.tokens, "rnd", "word", "ftz", "the residual output", rpins)
        flags = m.round_flags.pop()
        valid = "xe_project_valid" if port == "d_mul_error" or (port == "d_add_error" and not preserve) else "xe_valid"
        m.round_flags.append(f"({valid} ? {flags} : {FW}'d0)")
        m.port("output", port, fd.width)
        m.assign(port, f"{valid} ? {port}_pack_bits : {fd.width}'d0")
    from chialu.targets.rtl.families.fidelity import effective
    effective(pins, "two_term_expansion_output", True, "main result and an externally visible rounded residual")
    effective(pins, "error_term_ops", operators, "exposed residual operators")
    effective(pins, "error_term_normalization", "on_demand_copy" if copy else "dedicated",
              "copy of the selected anticipator normalization" if copy else "dedicated magnitude-count normalization")
    return ports


class BandGeom:
    """The windows of the bounded alignment for a geometry: the products'
    band (lsb 2^band_lo, BW bits); the near window (lsb 2^wlo, WN bits),
    which holds the band GNe bits above its lsb and the addend wherever
    its lsb is below EC_FAR (the addend's bits below the window are a
    sticky); the far word (WF bits: two sign bits, the addend, P bits
    below it), which holds the addend with its lsb at or above 2^EC_FAR
    and the products' sum as a sticky and a borrow. `bound` guard
    positions beyond max(Sc, XW) separate the band from the near window's
    lsb and, beyond XW + 1 - Sc, the addend from the far word's lsb; the
    windows are clipped to the frame.

    Exactness: a nonzero products' sum is at least 2^band_lo and below
    2^(band_hi - 1), so an addend entirely below the near window (its msb
    at most band_lo - 2) leaves the sum's leading one at or above
    band_lo - 1 and the window's lsb at least XW + 1 below it; an addend
    with its lsb at or above EC_FAR = band_hi - 1 + P exceeds the
    products' sum by more than the far word's lsb, so the sum only
    decides the sticky and, with the other sign, a borrow of one lsb. A
    zero products' sum bypasses to the addend itself."""

    def __init__(self, dg: DotGeom, bound: int):
        XW, Sc, AW, lo = dg.g.XW, dg.Sc, dg.AW, dg.lo
        self.band_lo, self.BW = dg.band
        self.band_hi = self.band_lo + self.BW - 3
        lo_c, hi_c = dg.c_range
        self.bound = bound
        self.GN = max(Sc, XW) + bound
        P = max(XW + 1 + bound - Sc, 1)
        if lo_c >= self.band_hi - 1 + P:
            P = XW + 1 + bound                        # a stored subnormal addend in the far region keeps its leading zeros
        self.P = P
        self.EC_FAR = self.band_hi - 1 + P
        self.wlo = max(self.band_lo - self.GN, lo)
        self.whi = min(self.EC_FAR + Sc, lo + AW - 1)
        self.WN = self.whi - self.wlo + 1
        self.GNe = self.band_lo - self.wlo
        self.far_possible = hi_c - Sc >= self.EC_FAR
        self.below_possible = lo_c < self.wlo
        self.WF = Sc + 2 + P

    def note(self) -> str:
        return (f"the bounded alignment: the products in their exponent band ({self.BW} bits, lsb 2^{self.band_lo}), the "
                f"addend in the near window ({self.WN} bits, lsb 2^{self.wlo}; {self.bound} guard positions beyond "
                f"max(Sc, XW) below the band" + ("; its bits below the window a sticky" if self.below_possible else "")
                + (f") or, with its lsb at or above 2^{self.EC_FAR}, in the far word ({self.WF} bits) with the products' "
                   f"sum as a sticky and a borrow" if self.far_possible else ")")
                + "; the products' zero sum bypasses to the addend")


def dot_geometry_inactive_parameters(family, pins, dg):
    """Conditional pins with no data-dependent path at this target geometry."""
    if pins.get("align.family") != "bounded_align":
        return {}
    band = BandGeom(dg, int(pins.get("align.bound", 2)))
    result = {}
    if not band.below_possible:
        reason = (f"C's minimum exponent {dg.c_range[0]} is at or above the near window lsb {band.wlo}; "
                  "there is no discarded-C sticky path")
        result.update({"align.sticky_method": reason, "align.tzc": reason})
    if not band.below_possible and not band.far_possible:
        result["align.bound"] = (f"C exponent range {dg.c_range} stays in the product/near window; "
                                 f"no below-window or far-word path uses the requested guard (actual near guard {band.GNe}, "
                                 f"requested minimum {band.GN})")
    return result


def _acc_x_sv(dg: DotGeom, family: str, pins: dict, cfg: dict, name: str) -> tuple:
    """(name, text, info): an accumulator-style family on the X geometry
    (see the module docstring for the construction the cfg selects)."""
    g, n, S, Sc, AW, lo = dg.g, dg.n, dg.S, dg.Sc, dg.AW, dg.lo
    XW, EW, XT = g.XW, g.EW, g.XT
    EWX = EW + 3
    align = cfg.get("align", "frame")
    tree = cfg["tree"]
    sign = cfg.get("sign", "twos")
    mul_fam, mul_pins = cfg.get("mul", (None, {}))
    shifter, spins = cfg.get("shifter", (None, {}))
    lz_fam, lzc_fam = cfg.get("lz", ("lzc_after_add", None))
    norm = cfg.get("norm", (None, {}))
    rpins = cfg.get("round_pins") or {}
    bg = BandGeom(dg, int(cfg.get("bound", 2) or 2)) if align == "band" else None
    window = cfg.get("window")                      # None: the exact frame
    L = max(1, _clog2(n + (1 if dg.acc else 0)))
    Wt = max(2 * S, Sc if dg.acc else 0)
    exact = window is None or window >= AW + L + 2
    Wn = AW + L + 2 if exact else int(window)
    if not exact and int(window) < Wt + L + 2:
        raise ValueError(f"{family}: window_bits={window} is below the {Wt + L + 2}-bit minimum "
                         "for a term and the sum's growth at this geometry")
    needs_rnd = bool(cfg.get("chunks") or cfg.get("pe"))
    notes = list(cfg.get("notes", []))
    if window is not None and exact:
        Wn = int(window)
    dacc = int(cfg.get("declared_acc_width") or 0)
    if dacc:
        # Bounded alignment reduces products in their own exponent band;
        # C joins in the separate near/far addition. The declared width is
        # the actual product reduction word in that architecture.
        required = bg.BW if bg is not None else getattr(dg, "numeric_width", AW)
        if dacc < required:
            raise ValueError(f"{family}: accumulator_width_bits={dacc} is below the {required}-bit "
                             "exact frame required by this geometry")
        Wn = dacc
        from chialu.targets.rtl.families.fidelity import effective
        effective(pins, "accumulator_width_bits", Wn, "width of the actual reduction word")
    if family == "streaming_accurate_accumulator" or (family == "multi_term_fused_dot"
                                                      and int(pins.get("window_bits", 0) or 0)):
        # window_bits 0 asks for the exact frame, which has no width to check against
        from chialu.targets.rtl.families.fidelity import effective
        effective(pins, "window_bits", Wn, "width of each alignment/reduction window")
    if "{acc_w}" in str(cfg.get("comment", "")):    # the header states the word the netlist carries
        cfg = dict(cfg, comment=cfg["comment"].format(acc_w=cfg.get("comment_acc_w") or Wn))
    contract = cfg.get("contract", "the fused contract (one rounding of the exact sum)" if exact else
                       f"a {Wn}-bit window: the bits below it are truncated (a sticky marks them), so the fused "
                       f"contract's single rounding is not met")
    if bg is not None:
        from chialu.targets.rtl.families.fidelity import effective
        effective(pins, "align.bound", bg.GNe-max(Sc, XW),
                  "guard positions physically present below the product band; choose a wider addend exponent range if clipped",
                  geometry={"frame_lsb": lo, "product_band_lsb": bg.band_lo, "near_window_lsb": bg.wlo})
        notes.append(bg.note())
    m = Mod(name, f"dot-accumulate ({family}) for {n} products of {S}-bit significands" + (f" and a {Sc}-bit c" if dg.acc else "")
                  + f" on the engine geometry {g.tag()}: {cfg.get('comment', '')}; meets {contract}"
                  + ("; " + "; ".join(notes) if notes else ""))
    m.port("input", "xa", n * XT)
    m.port("input", "xb", n * XT)
    if dg.acc:
        m.port("input", "xc", XT)
    if needs_rnd:
        m.port("input", "rnd", 3)
        m.port("input", "word", g.sr_bits)
    dg.ports_out(m)

    specials: list = []                             # (special code, sign) of the partial results rounded inside
    tail_lz_fam = lz_fam

    def emit_out(total: str, Wn_: int, lo_e: str, st_all_: str, last_):
        """The frame sum or its X, whichever the seed reads; a partial
        result that overflowed to infinity (or two of opposite signs) at
        its rounding makes the group's result that special."""
        in_frame = Wn_ == AW and lo_e == _slit(EWX, lo)
        if dg.out == "acc":
            m.assign("acc", total if in_frame else _frame_of_window(m, "o", total, Wn_, lo_e, EWX, AW, lo))
            return
        yv = (_to_x(m, "o", total, AW, lo, g, tail_lz_fam, lzc_fam, st_all_, last_, norm) if in_frame else
              _to_x_w(m, "o", total, Wn_, lo_e, EWX, g, tail_lz_fam, lzc_fam, st_all_, last_, norm=norm))
        if not specials:
            m.assign("y", yv)
            return
        m.wire("sp_nan", expr=" | ".join(f"({sp} == 2'd1)" for sp, _s in specials))
        m.wire("sp_inf", expr=" | ".join(f"({sp} == 2'd2)" for sp, _s in specials))
        m.wire("sp_pos", expr=" | ".join(f"({sp} == 2'd2 && !{s})" for sp, s in specials))
        m.wire("sp_neg", expr=" | ".join(f"({sp} == 2'd2 && {s})" for sp, s in specials))
        nan_x = _mkx(g, "2'd1", "1'b0", f"{EW}'sd0", f"{XW}'d0", "1'b0")
        inf_x = _mkx(g, "2'd2", "sp_neg", f"{EW}'sd0", f"{XW}'d0", "1'b0")
        m.assign("y", f"(sp_nan || (sp_pos && sp_neg)) ? {nan_x} : sp_inf ? {inf_x} : {yv}")
    def band_stage(S: str | None, pair: tuple | None, tree_: tuple):
        """y of the bounded alignment from the products' sum S (BW bits;
        or a pair of near-window rows whose sum is it) and the addend."""
        band_lo, BW, WN, GNe, P, WF = bg.band_lo, bg.BW, bg.WN, bg.GNe, bg.P, bg.WF
        method = str(cfg.get("sticky_method", "precomputed_mask"))
        tz_fam, tz_pins = cfg.get("tzc", (None, {}))
        cfam, cpins = tree_[2], tree_[3]
        m.wire("ba_nz", expr="|sc")
        m.wire("ba_dl", EWX, signed=True, expr=f"ec - {_slit(EWX, bg.wlo)}")
        aw = _clog2(WN)
        m.wire("ba_lam", aw, expr=f"(ba_dl >= 0 && ba_dl < {WN}) ? ba_dl[{aw-1}:0] : {aw}'d0")
        m.wire("ba_lx", WN, expr=f"{{{{({WN}-{Sc}){{1'b0}}}}, sc}}")
        _sh(m, shifter, spins, "ba_lx", WN, "ba_lam", 0, "ba_l", "the addend into the near window: a left shift by its distance to the window's lsb")
        if bg.below_possible:
            ra = _clog2(Sc)
            m.wire("ba_ng", EWX, signed=True, expr="-ba_dl")
            m.wire("ba_all", expr=f"(ba_dl < 0) && (ba_ng >= {Sc})")
            m.wire("ba_ram", ra, expr=f"((ba_dl < 0) && !ba_all) ? ba_ng[{ra-1}:0] : {ra}'d0")
            cm = "the addend below the near window: a right shift by the distance, the dropped bits a sticky"
            if method == "or_tree_shifted_out":
                _sh(m, shifter, spins, "sc", Sc, "ba_ram", 1, "ba_r", cm + " (collected by the shifter)", sticky="ba_rst")
            else:
                _sh(m, shifter, spins, "sc", Sc, "ba_ram", 1, "ba_r", cm)
                if method == "trailing_zero_compare":
                    _tz(m, tz_fam, tz_pins, "sc", Sc, "ba_tz", "the sticky by the addend's trailing-zero count against the shift")
                    m.wire("ba_rst", expr=f"ba_nz && (ba_tz < {{{{({Sc.bit_length()}-{ra}){{1'b0}}}}, ba_ram}})")
                else:
                    m.wire("ba_rmk", Sc, expr=f"~({{{Sc}{{1'b1}}}} << ba_ram)")
                    m.wire("ba_rst", expr="|(sc & ba_rmk)")
            m.wire("ba_tr", WN, expr=f"(ba_dl < 0) ? (ba_all ? {WN}'d0 : {{{{({WN}-{Sc}){{1'b0}}}}, ba_r}}) : ba_l")
            m.wire("ba_st", expr="(ba_dl < 0) && (ba_all ? ba_nz : ba_rst)")
        else:
            m.wire("ba_tr", WN, expr="ba_l")
            m.wire("ba_st", expr="1'b0")
        m.wire("ba_far", expr=f"ba_nz && (ec >= {_slit(EWX, bg.EC_FAR)})" if bg.far_possible else "1'b0")
        # the addend's row (inverted when negative) and the carry-in that completes its two's complement unless
        # a truncation borrowed the lsb: the window sum is then the floor of the exact sum
        m.wire("ba_row", WN, expr=f"ba_far ? {WN}'d0 : (c_s ? ~ba_tr : ba_tr)")
        m.wire("ba_cin", expr="!ba_far && c_s && !ba_st")
        if S is not None:
            m.wire("ba_sz", expr=f"({S} == 0)")
            s_neg = f"{S}[{BW-1}]"
            hi_ = WN - BW - GNe
            parts = ([f"{{{hi_}{{{S}[{BW-1}]}}}}"] if hi_ > 0 else []) + [S] + ([f"{GNe}'d0"] if GNe > 0 else [])
            m.wire("ba_sx", WN, expr="{" + ", ".join(parts) + "}")
            m.wire("ba_tn", WN)
            _add(m, cfam, cpins, WN, "ba_sx", "ba_row", "ba_tn", f"the addend stage: the products' sum and the addend's row ({cfam})", cin="ba_cin")
            ops = ("ba_sx", "ba_row")
        else:
            rs, rc = pair
            m.wire("ba_sz", expr=f"(({rs} ^ {rc}) == (({rs} | {rc}) << 1))")      # a carry-save pair sums to zero
            m.wire("ba_qs", WN, expr=f"{rs} ^ {rc} ^ ba_row")
            m.wire("ba_qm", WN, expr=f"({rs} & {rc}) | ({rs} & ba_row) | ({rc} & ba_row)")
            m.wire("ba_qc", WN, expr=f"{{ba_qm[{WN-2}:0], ba_cin}}")
            m.wire("ba_tn", WN)
            _add(m, cfam, cpins, WN, "ba_qs", "ba_qc", "ba_tn", f"the one CPA: the products' carry-save pair and the addend's row ({cfam})")
            s_neg = f"ba_tn[{WN-1}]"                   # the products' sum's sign (the far case zeroes the addend's row)
            ops = ("ba_qs", "ba_qc")
        yn = _to_x_w(m, "on", "ba_tn", WN, _slit(EWX, bg.wlo), EWX, g, lz_fam, lzc_fam, "ba_st",
                     ops if lz_fam == "lza" else None, norm=norm)
        # the far word: the addend less one lsb with ones below when the products' sum has the other sign, the
        # sticky set; a zero products' sum: the addend itself
        m.wire("ba_fopp", expr=f"ba_far && !ba_sz && (c_s ^ {s_neg})")
        m.wire("ba_fhi", Sc, expr=f"sc - {{{{({Sc}-1){{1'b0}}}}, ba_fopp}}")
        m.wire("ba_fmag", WF, expr=f"{{2'b00, ba_fhi, {{{P}{{ba_fopp}}}}}}")
        m.wire("ba_flo", EWX, signed=True, expr=f"ec - {_slit(EWX, P)}")
        yf = _to_x_w(m, "of", "ba_fmag", WF, "ba_flo", EWX, g, "lzc_after_add", lzc_fam, "!ba_sz", None, True, "c_s", norm=norm)
        m.assign("y", f"(ba_sz || ba_far) ? {yf} : {yn}")
        return name, m.render(), {"rnd": False, "product_classification": bool(cfg.get("approximate_product")),
                                  "contract": "architecture" if cfg.get("approximate_product") else "fused"}

    # ---- operands and products
    for t in range(n):
        m.wire(f"xa{t}", XT, expr=f"xa[{t*XT} +: {XT}]")
        m.wire(f"xb{t}", XT, expr=f"xb[{t*XT} +: {XT}]")
        _x_fields(m, f"xa{t}", g, f"a{t}_")
        _x_fields(m, f"xb{t}", g, f"b{t}_")
        m.wire(f"sa{t}", S, expr=f"a{t}_sig[{S-1}:0]")
        m.wire(f"sb{t}", S, expr=f"b{t}_sig[{S-1}:0]")
        m.wire(f"e{t}", EWX, signed=True, expr=f"$signed({{{{3{{a{t}_e[{EW-1}]}}}}, a{t}_e}}) + $signed({{{{3{{b{t}_e[{EW-1}]}}}}, b{t}_e}})")
        m.wire(f"s{t}", expr=f"a{t}_s ^ b{t}_s")
    if dg.acc:
        _x_fields(m, "xc", g, "c_")
        m.wire("sc", Sc, expr=f"c_sig[{Sc-1}:0]")
        m.wire("ec", EWX, signed=True, expr=f"$signed({{{{3{{c_e[{EW-1}]}}}}, c_e}})")
    flatten = cfg.get("flatten", False)
    if not flatten:
        if cfg.get("mul_style") == "twin":
            from chialu.targets.rtl.families import subword
            tn, tt = subword.twin_precision_sv(n * S, [S], [False], mul_pins)
            m.extra.append(tt)
            m.wire("tw_a", n * S, expr="{" + ", ".join(f"sa{t}" for t in reversed(range(n))) + "}")
            m.wire("tw_b", n * S, expr="{" + ", ".join(f"sb{t}" for t in reversed(range(n))) + "}")
            m.wire("tw_p", 2 * n * S)
            m.n += 1
            m.raw(f"  // the products as the {n} lanes of one gated partial-product matrix ({cfg.get('lane_split', '')})")
            m.raw(f"  {tn} u{m.n} (.a(tw_a), .b(tw_b), .sel(1'b0), .p(tw_p));")
            for t in range(n):
                m.wire(f"p{t}", 2 * S, expr=f"tw_p[{2*S*t} +: {2*S}]")
        else:
            for t in range(n):
                if cfg.get("composable"):
                    levels, apart, dimensions = cfg["composable"]
                    _composable_product(m, t, f"sa{t}", f"sb{t}", S, False, levels,
                                        (mul_fam, mul_pins), apart, dimensions)
                elif cfg.get("multiword"):
                    part = _multiword_product(m, f"mw{t}", f"sa{t}", f"sb{t}", S, (mul_fam, mul_pins), tree)
                    m.wire(f"p{t}", 2*S, expr=part)
                else:
                    m.wire(f"p{t}", 2 * S)
                    if not _inst_mul(m, mul_fam, mul_pins, S, False, f"sa{t}", f"sb{t}", f"p{t}", f"product {t}: the significand multiplier ({mul_fam})"):
                        m.assign(f"p{t}", f"sa{t} * sb{t}")
        if cfg.get("pre_norm"):
            # the products normalized before the alignment (leading one to bit 2S-1)
            lw = _clog2(2 * S)
            for t in range(n):
                _lz(m, lzc_fam, {}, f"p{t}", 2 * S, f"plz{t}", f"product {t}: leading zeros for the pre-normalization")
                m.wire(f"plzs{t}", lw, expr=f"(p{t} == 0) ? {lw}'d0 : plz{t}[{lw-1}:0]")
                _sh(m, shifter, spins, f"p{t}", 2 * S, f"plzs{t}", 0, f"pn{t}", f"product {t} normalized")
                m.wire(f"en{t}", EWX, signed=True, expr=f"e{t} - $signed({{{{({EWX}-{lw}){{1'b0}}}}, plzs{t}}})")
            prod = [(f"pn{t}", 2 * S, f"en{t}", f"s{t}") for t in range(n)]
        else:
            prod = [(f"p{t}", 2 * S, f"e{t}", f"s{t}") for t in range(n)]
    else:
        prod = [(f"sa{t}", S, f"e{t}", f"s{t}") for t in range(n)]
    if cfg.get("approximate_product"):
        m.port("output", "product_nonzero")
        m.port("output", "products_negative")
        m.assign("product_nonzero", " | ".join(f"(|{word})" for word, _, _, _ in prod))
        m.assign("products_negative", " & ".join(sign for _, _, _, sign in prod))
    terms = list(prod)
    if dg.acc:
        terms.append(("sc", Sc, "ec", "c_s"))
    T = len(terms)
    st_terms = []                                   # sticky of what an alignment dropped
    # ---- alignment into the window
    if flatten:
        # fused_csa: every product's partial products reduced to a carry-save pair (no CPA per product), the
        # pairs shifted into the frame with c, one final carry-save reduction and one CPA
        comp = tree[1]
        pairs = []
        for t in range(n):
            nl = Netlist()
            cols = [[] for _ in range(2 * S)]
            for i in range(S):
                for j in range(S):
                    # M=0 floating formats have a one-bit significand.
                    # Mod declares one-bit wires as scalars, so indexed
                    # reads would be illegal after a Verilog-2005 conversion.
                    abit = f"sa{t}" if S == 1 else f"sa{t}[{i}]"
                    bbit = f"sb{t}" if S == 1 else f"sb{t}[{j}]"
                    cols[i + j].append(nl.wire(f"{abit} & {bbit}", "pp"))
            cols = _reduce_7_3(nl, cols) if comp == "7:3" else _reduce_cols(nl, cols, "dadda", "4_2" if comp == "4:2" else "3_2")
            m.raw(f"  // product {t}: the partial products reduced to a carry-save pair ({comp}: {nl.fa_count} full adders, "
                  f"{nl.ha_count} half adders)")
            _render_nl(m, nl, f"q{t}")
            rs, rc = _rows_of(cols, 2 * S, f"q{t}")
            m.wire(f"q{t}_rs", 2 * S, expr=rs)
            m.wire(f"q{t}_rc", 2 * S, expr=rc)
            fl, fw = (bg.band_lo, bg.BW) if align == "band" else (lo, AW)
            for part in ("rs", "rc"):
                u = _place(m, f"al{t}{part}", f"q{t}_{part}", 2 * S, f"e{t}", EWX, fl, fw, shifter, spins,
                           f"product {t}: the carry-save {'sum' if part == 'rs' else 'carry'} row into the "
                           f"{'band' if align == 'band' else 'frame'}", right_ok=False)
                pairs.append(_neg(m, f"v{t}{part}", u, f"s{t}", fw))
        if align == "band":
            # the rows in the band, sign-extended into the near window by the constant trick ({~s, s, bits} and one
            # constant row), reduced to a pair; the addend's row joins at the one CPA
            BW, WN, GNe = bg.BW, bg.WN, bg.GNe
            nl = Netlist()
            cols = [[] for _ in range(WN)]
            for w in pairs:
                for k in range(BW - 1):
                    cols[GNe + k].append(f"{w}[{k}]")
                cols[GNe + BW - 1].append(f"{w}[{BW-1}]")
                if GNe + BW < WN:
                    cols[GNe + BW].append(f"~{w}[{BW-1}]")
            K = (-len(pairs) * (1 << (GNe + BW))) % (1 << WN)
            for k in range(WN):
                if (K >> k) & 1:
                    cols[k].append("1'b1")
            cols = _reduce_7_3(nl, cols) if comp == "7:3" else _reduce_cols(nl, cols, "dadda", "4_2" if comp == "4:2" else "3_2")
            m.raw(f"  // the fused reduction of the products' carry-save pairs in the band ({comp}: {nl.fa_count} full adders, "
                  f"{nl.ha_count} half adders)")
            _render_nl(m, nl, "q")
            rs, rc = _rows_of(cols, WN, "q")
            m.wire("q_rs", WN, expr=rs)
            m.wire("q_rc", WN, expr=rc)
            return band_stage(None, ("q_rs", "q_rc"), tree)
        if dg.acc:
            uc = _place(m, "alc", "sc", Sc, "ec", EWX, lo, AW, shifter, spins, "c into the frame", right_ok=False)
            pairs.append(_neg(m, "vc", uc, "c_s", AW))
        total = _sum_words(m, "f", pairs, AW, ("csa_tree", comp, tree[2], tree[3]), "the fused reduction of the carry-save pairs and c")
        emit_out(total, AW, _slit(EWX, lo), "1'b0", m.last_add)
        return name, m.render(), {"rnd": False}
    # a stored-aligned term's lsb exponent is at or above the frame's, so its alignment is a left shift alone; a
    # product normalized before the alignment can have its lsb below the frame (its low bits are zeros then), so
    # its alignment shifts right as well
    right_ok = bool(cfg.get("pre_norm"))
    lines = False                                   # the sorted strategy's realignment lines (the output is selected)
    if align == "band":
        words = []
        reduction_width = dacc or bg.BW
        for k, (mag, w, e, s) in enumerate(prod):
            u = _place(m, f"al{k}", mag, w, e, EWX, bg.band_lo, reduction_width, shifter, spins, f"product {k} into the exponent band",
                       right_ok=right_ok)
            words.append((u, s))
        Wn, lo_expr = reduction_width, _slit(EWX, bg.band_lo)
    elif align in ("frame", "two_stage"):
        frame_width = dacc or AW
        words = []
        for k, (mag, w, e, s) in enumerate(terms):
            if align == "two_stage":
                aw = _clog2(frame_width)
                sh = m.wire(f"al{k}_sh", EWX, signed=True, expr=f"{e} - {_slit(EWX, lo)}")
                ext = m.wire(f"al{k}_x", frame_width, expr=f"{{{{({frame_width}-{w}){{1'b0}}}}, {mag}}}")
                m.wire(f"al{k}_ok", expr=f"({sh} >= 0) && ({sh} < {frame_width})")
                m.wire(f"al{k}_co", aw, expr=f"al{k}_ok ? {{{sh}[{aw-1}:3], 3'd0}} : {aw}'d0")
                m.wire(f"al{k}_fi", aw, expr=f"al{k}_ok ? {{{{({aw}-3){{1'b0}}}}, {sh}[2:0]}} : {aw}'d0")
                _sh(m, shifter, spins, ext, frame_width, f"al{k}_co", 0, f"al{k}_c", f"term {k}: the coarse alignment stage (multiples of 8)")
                _sh(m, shifter, spins, f"al{k}_c", frame_width, f"al{k}_fi", 0, f"al{k}_f", f"term {k}: the fine alignment stage")
                if right_ok:
                    m.wire(f"al{k}_ng", EWX, signed=True, expr=f"-{sh}")
                    m.wire(f"al{k}_ar", aw, expr=f"({sh} >= 0 || {sh} <= -{frame_width}) ? {aw}'d0 : al{k}_ng[{aw-1}:0]")
                    _sh(m, shifter, spins, ext, frame_width, f"al{k}_ar", 1, f"al{k}_r", f"term {k}: the right shift of a value below the frame")
                    u = m.wire(f"al{k}", frame_width, expr=f"al{k}_ok ? al{k}_f : ({sh} < 0 && {sh} > -{frame_width}) ? al{k}_r : {frame_width}'d0")
                else:
                    u = m.wire(f"al{k}", frame_width, expr=f"al{k}_ok ? al{k}_f : {frame_width}'d0")
            else:
                u = _place(m, f"al{k}", mag, w, e, EWX, lo, frame_width, shifter, spins, f"term {k} into the frame", right_ok=right_ok)
            words.append((u, s))
        Wn, lo_expr = frame_width, _slit(EWX, lo)
    elif align == "per_level":
        # Each node aligns its actual inputs, then uses the requested
        # reduction. A linear fold, binary tree and compressor tree keep
        # distinct graphs even when every level uses the same window.
        head = Wn - Wt - L - 1
        nodes = []
        for k, (mag, w, e, s) in enumerate(terms):
            m.wire(f"n{k}_u", Wn, expr=f"{{{{({Wn}-{w}){{1'b0}}}}, {mag}}} << {head}")
            v = _neg(m, f"n{k}_v", f"n{k}_u", s, Wn)
            el = m.wire(f"n{k}_el", EWX, signed=True, expr=f"{e} - {_slit(EWX, head)}")
            nodes.append((v, el, "1'b0"))
        bypass_node = None
        if cfg.get("bypass_min") and len(prod) >= 2:
            exponents = [term[2] for term in prod]
            signs = [term[3] for term in prod]
            pairs = [(i, j) for i in range(len(prod)) for j in range(i+1, len(prod))]
            cancel = m.wire("pl_cancel", expr=" | ".join(f"(({exponents[i]} == {exponents[j]}) && ({signs[i]} != {signs[j]}))" for i, j in pairs))
            selected = []
            for k, exponent in enumerate(exponents):
                minimum = " && ".join(f"({exponent} {'<' if j < k else '<='} {other})" for j, other in enumerate(exponents) if j != k)
                selected.append(m.wire(f"pl_bypass{k}", expr=f"{cancel} && ({minimum})"))
            bv = m.wire("pl_bypass_value", Wn, expr=" : ".join(f"{chosen} ? {nodes[k][0]}" for k, chosen in enumerate(selected)) + f" : {Wn}'d0")
            be = m.wire("pl_bypass_exponent", EWX, signed=True, expr=" : ".join(f"{chosen} ? {nodes[k][1]}" for k, chosen in enumerate(selected)) + f" : {EWX}'sd0")
            bypass_node = (bv, be, "1'b0")
            nodes = [(m.wire(f"pl_main{k}", Wn, expr=f"{selected[k]} ? {Wn}'d0 : {v}"), ex, st)
                     if k < len(prod) else (v, ex, st) for k, (v, ex, st) in enumerate(nodes)]
        def combine(part, tg):
            active = [m.wire(f"{tg}_e{k}", EWX, signed=True,
                             expr=f"({v} == 0 && !({st})) ? {_slit(EWX, -(1 << (EWX-2)))} : {ex}")
                      for k, (v, ex, st) in enumerate(part)]
            anchor = active[0]
            for k, value in enumerate(active[1:]):
                anchor = m.wire(f"{tg}_mx{k}", EWX, signed=True, expr=f"({anchor} > {value}) ? {anchor} : {value}")
            aligned, sticky = [], []
            for side, (v, ex, st) in enumerate(part):
                m.wire(f"{tg}_d{side}", EWX, signed=True, expr=f"{anchor} - {ex}")
                m.wire(f"{tg}_f{side}", expr=f"{tg}_d{side} >= {Wn}")
                dw = _clog2(Wn)
                m.wire(f"{tg}_a{side}", dw, expr=f"{tg}_f{side} ? {dw}'d0 : {tg}_d{side}[{dw-1}:0]")
                _sh(m, shifter, spins, v, Wn, f"{tg}_a{side}", 2, f"{tg}_r{side}", "signed alignment into the node window")
                aligned.append(m.wire(f"{tg}_s{side}", Wn, expr=f"{tg}_f{side} ? {{{Wn}{{{v}[{Wn-1}]}}}} : {tg}_r{side}"))
                m.wire(f"{tg}_m{side}", Wn, expr=f"{tg}_f{side} ? {{{Wn}{{1'b1}}}} : ~({{{Wn}{{1'b1}}}} << {tg}_a{side})")
                sticky.append(m.wire(f"{tg}_k{side}", expr=f"({st}) | (|({v} & {tg}_m{side}))"))
            if sign == "dual":
                positive = [m.wire(f"{tg}_pos{k}", Wn, expr=f"{v}[{Wn-1}] ? {Wn}'d0 : {v}") for k, v in enumerate(aligned)]
                negative = [m.wire(f"{tg}_neg{k}", Wn, expr=f"{v}[{Wn-1}] ? -{v} : {Wn}'d0") for k, v in enumerate(aligned)]
                psum = _sum_words(m, tg+"_positive", positive, Wn, tree, "the node's positive reduction")
                nsum = _sum_words(m, tg+"_negative", negative, Wn, tree, "the node's negative reduction")
                inverse_p = m.wire(tg+"_inverse_p", Wn, expr=f"~{psum}")
                inverse_n = m.wire(tg+"_inverse_n", Wn, expr=f"~{nsum}")
                pn, np = m.wire(tg+"_p_minus_n", Wn), m.wire(tg+"_n_minus_p", Wn)
                _add(m, tree[2], tree[3], Wn, psum, inverse_n, pn, "positive-minus-negative node CPA", "1'b1")
                _add(m, tree[2], tree[3], Wn, nsum, inverse_p, np, "negative-minus-positive node CPA", "1'b1")
                negative_result = m.wire(tg+"_result_negative", expr=f"{psum} < {nsum}")
                magnitude = m.wire(tg+"_positive_difference", Wn, expr=f"{negative_result} ? {np} : {pn}")
                value = m.wire(tg+"_sum", Wn, expr=f"{negative_result} ? -{magnitude} : {magnitude}")
                m.last_add = (psum, inverse_n)
            else:
                value = _sum_words(m, tg, aligned, Wn, tree, "the per-level node reduction")
            st = m.wire(f"{tg}_st", expr=" | ".join(sticky))
            if cfg.get("loop_norm"):
                operands = m.last_add
                nt = tg+"_loop"
                _magnitude(m, nt, value, Wn, st)
                _normalize(m, nt, Wn, lz_fam, lzc_fam, operands, norm, sum_word=value, extra_st=st)
                # A deferred LZA correction is resolved at this window
                # boundary before another partial enters the algorithm.
                fine = m.wire(nt+"_fine", expr=f"!{nt}_nm[{Wn-1}] && (|{nt}_nm)")
                corrected = m.wire(nt+"_corrected", Wn, expr=f"{nt}_nm << {fine}")
                leading = m.wire(nt+"_leading", _clog2(Wn)+1, expr=f"{nt}_lz + {fine}")
                count = m.wire(f"{tg}_norm_count", _clog2(Wn),
                               expr=f"({st} || {corrected} == 0 || {leading} == 0) ? 0 : {leading}-1'b1")
                nm = m.wire(nt+"_magnitude", Wn, expr=f"({leading} == 0) ? {corrected} : ({corrected} >> 1)")
                normalized = m.wire(f"{tg}_norm", Wn, expr=f"{st} ? {value} : {value}[{Wn-1}] ? -{nm} : {nm}")
                anchor = m.wire(f"{tg}_norm_exp", EWX, signed=True, expr=f"{anchor} - $signed({{1'b0, {count}}})")
                value = normalized
                m.last_add = tuple(_sh(m, norm[0], norm[1], operand, Wn, count, 0, f"{tg}_operand{k}",
                                       "the real final operand in the normalized window") for k, operand in enumerate(operands))
            return value, anchor, st
        if tree[0] == "linear_chain":
            cur = nodes[0]
            for index, node in enumerate(nodes[1:]):
                cur = combine((cur, node), f"l{index}_0")
            nodes = [cur]
        else:
            fanin = {"3:2": 3, "4:2": 4, "7:3": 7}[tree[1]] if tree[0] == "csa_tree" else 2
            level = 0
            while len(nodes) > 1:
                nodes = [combine(nodes[i:i+fanin], f"l{level}_{i//fanin}") if len(nodes[i:i+fanin]) > 1 else nodes[i]
                         for i in range(0, len(nodes), fanin)]
                level += 1
        if bypass_node is not None:
            nodes = [combine((nodes[0], bypass_node), "pl_bypass_join")]
        v, el, st = nodes[0]
        if not exact:
            _window_flags(m, st)
        emit_out(v, Wn, el, st if cfg.get("keep_sticky", True) else "1'b0", m.last_add)
        flags_out = _rounding_flags(m)
        return name, m.render(), {"rnd": False, "flags": flags_out, "product_classification": bool(cfg.get("approximate_product")),
                                  "contract": "fused" if (exact or cfg.get("fused_window"))
                                              and not cfg.get("approximate_product") else "architecture"}
    else:
        # a window anchored at the largest exponent: the terms right-shifted by their distance to it
        # Zero terms do not set the window's position. The sentinel leaves
        # room for subtraction from every exponent carried by the X inputs.
        inactive_exp = -(1 << (EWX - 2))
        terms = [(mag, w, m.wire(f"active_e{k}", EWX, signed=True,
                                expr=f"({mag} == 0) ? {_slit(EWX, inactive_exp)} : {e}"), s)
                 for k, (mag, w, e, s) in enumerate(terms)]
        es = [e for (_m, _w, e, _s) in terms]
        if align == "pairwise_diff":
            for i in range(T):
                for j in range(i + 1, T):
                    m.wire(f"d{i}_{j}", EWX, signed=True, expr=f"{es[i]} - {es[j]}")

            def dd(i, j):
                return f"d{i}_{j}" if i < j else (f"(-d{j}_{i})" if i > j else f"{EWX}'sd0")
            for i in range(T):
                conds = [f"({dd(i, j)} >= 0)" if i < j else f"({dd(i, j)} > 0)" for j in range(T) if j != i]
                m.wire(f"ismax{i}", expr=" && ".join(conds) if conds else "1'b1")
            m.wire("emax", EWX, signed=True, expr=" : ".join(f"ismax{i} ? {es[i]}" for i in range(T)) + f" : {es[0]}")
            dist = [m.wire(f"dist{k}", EWX, signed=True,
                           expr=" : ".join(f"ismax{i} ? {dd(i, k)}" for i in range(T)) + f" : {EWX}'sd0") for k in range(T)]
        elif align == "sorted":
            # an odd-even transposition network sorts the terms by exponent (descending); the shifts follow
            # the realignment lines, the running differences down the sorted order
            order = [(mag, w, e, s) for (mag, w, e, s) in terms]
            cur = []
            for k, (mag, w, e, s) in enumerate(order):
                m.wire(f"r0_{k}_m", Wt, expr=f"{{{{({Wt}-{w}){{1'b0}}}}, {mag}}}" if Wt > w else mag)
                cur.append((f"r0_{k}_m", e, s))
            for stage in range(T):
                nxt = list(cur)
                for i in range(stage % 2, T - 1, 2):
                    (ma, ea, sa_), (mb, eb, sb_) = cur[i], cur[i + 1]
                    tg = f"r{stage+1}_{i}"
                    m.wire(f"{tg}_sw", expr=f"{eb} > {ea}")
                    m.wire(f"{tg}_m", Wt, expr=f"{tg}_sw ? {mb} : {ma}")
                    m.wire(f"{tg}_e", EWX, signed=True, expr=f"{tg}_sw ? {eb} : {ea}")
                    m.wire(f"{tg}_s", expr=f"{tg}_sw ? {sb_} : {sa_}")
                    m.wire(f"{tg}b_m", Wt, expr=f"{tg}_sw ? {ma} : {mb}")
                    m.wire(f"{tg}b_e", EWX, signed=True, expr=f"{tg}_sw ? {ea} : {eb}")
                    m.wire(f"{tg}b_s", expr=f"{tg}_sw ? {sa_} : {sb_}")
                    nxt[i] = (f"{tg}_m", f"{tg}_e", f"{tg}_s")
                    nxt[i + 1] = (f"{tg}b_m", f"{tg}b_e", f"{tg}b_s")
                cur = nxt
            terms = [(mg, Wt, e, s) for (mg, e, s) in cur]
            es = [e for (_m, _w, e, _s) in terms]
            if exact and dg.out == "y":
                # the realignment lines (tao_2013): sorted term k has a line of w = Wt + L + XW - 2 bits in an adder of
                # T lines, independent of the exponent range; a term whose gap to its predecessor reaches
                # Wt + L + XW - 1 opens a realignment line and sits at its line's reserved position rather than at
                # its true offset. The clusters so separated are exact within themselves; a lower cluster lies below
                # the X's lsb of the upper cluster's result (the gap exceeds the lower cluster's width and growth by
                # XW - 1), so it enters the result as a sticky and a borrow alone, and the result is the first nonzero
                # cluster, selected after the one add, its exponent from the cluster's first term
                lines = True
                ltau = Wt + L + XW - 1
                lw_ = ltau - 1
                WA = T * lw_
                PW = _clog2(WA)
                tops = [(T - k) * lw_ - L - 1 - Wt for k in range(T)]
                m.comment += (f"; the realignment lines: {T} lines of {lw_} bits, a {WA}-bit adder independent of the exponent "
                              f"range (the exact window at the largest exponent would be {AW + L + 2} bits)")
                m.wire("lp0", PW, expr=f"{PW}'d{tops[0]}")
                m.wire("lflag0", expr="1'b1")
                for k in range(1, T):
                    m.wire(f"lgap{k}", EWX, signed=True, expr=f"{es[k-1]} - {es[k]}")
                    m.wire(f"lflag{k}", expr=f"lgap{k} >= {_slit(EWX, ltau)}")
                    m.wire(f"lp{k}", PW, expr=f"lflag{k} ? {PW}'d{tops[k]} : (lp{k-1} - lgap{k}[{PW-1}:0])")
                words = []
                for k, (mag, w, e, s) in enumerate(terms):
                    m.wire(f"lx{k}", WA, expr=f"{{{{({WA}-{Wt}){{1'b0}}}}, {mag}}}")
                    _sh(m, shifter, spins, f"lx{k}", WA, f"lp{k}", 0, f"lw{k}", f"term {k}: onto its line (a left shift to its position)")
                    words.append((f"lw{k}", s))
                Wn, lo_expr = WA, None
            else:
                m.wire("emax", EWX, signed=True, expr=es[0])
                dist = [m.wire("dist0", EWX, signed=True, expr=f"{EWX}'sd0")]
                for k in range(1, T):
                    m.wire(f"step{k}", EWX, signed=True, expr=f"{es[k-1]} - {es[k]}")
                    dist.append(m.wire(f"dist{k}", EWX, signed=True, expr=f"dist{k-1} + step{k}"))
        else:
            level, lv = list(es), 0
            while len(level) > 1:
                nxt = []
                for i in range(0, len(level) - 1, 2):
                    nxt.append(m.wire(f"mx{lv}_{i//2}", EWX, signed=True, expr=f"({level[i]} > {level[i+1]}) ? {level[i]} : {level[i+1]}"))
                if len(level) % 2:
                    nxt.append(level[-1])
                level, lv = nxt, lv + 1
            m.wire("emax", EWX, signed=True, expr=level[0])
            dist = [m.wire(f"dist{k}", EWX, signed=True, expr=f"emax - {es[k]}") for k in range(T)]
        if lines:
            pass
        else:
          words = []
          dw = _clog2(Wn)
          for k, (mag, w, e, s) in enumerate(terms):
            # the largest term's msb L + 1 bits below the window top (the sum's growth and its sign)
            m.wire(f"w{k}_0", Wn, expr=f"{{{{({Wn}-{w}){{1'b0}}}}, {mag}}} << {Wn - Wt - L - 1}")
            m.wire(f"w{k}_far", expr=f"{dist[k]} >= {Wn}")
            m.wire(f"w{k}_am", dw, expr=f"w{k}_far ? {dw}'d0 : {dist[k]}[{dw-1}:0]")
            if cfg.get("window_two_stage"):
                m.wire(f"w{k}_coarse", dw, expr=f"(w{k}_am >> 3) << 3")
                m.wire(f"w{k}_fine", dw, expr=f"w{k}_am & {dw}'d7")
                _sh(m, shifter, spins, f"w{k}_0", Wn, f"w{k}_coarse", 1, f"w{k}_co", f"term {k}: coarse window alignment")
                _sh(m, shifter, spins, f"w{k}_co", Wn, f"w{k}_fine", 1, f"w{k}_sh", f"term {k}: fine window alignment")
            else:
                _sh(m, shifter, spins, f"w{k}_0", Wn, f"w{k}_am", 1, f"w{k}_sh", f"term {k}: right shift to the window at the largest exponent")
            m.wire(f"w{k}_u", Wn, expr=f"w{k}_far ? {Wn}'d0 : w{k}_sh")
            m.wire(f"w{k}_mk", Wn, expr=f"w{k}_far ? {{{Wn}{{1'b1}}}} : ~({{{Wn}{{1'b1}}}} << w{k}_am)")
            st_terms.append(m.wire(f"w{k}_st", expr=f"|(w{k}_0 & w{k}_mk)"))
            words.append((f"w{k}_u", s))
          lo_expr = m.wire("wlo", EWX, signed=True, expr=f"emax - {_slit(EWX, Wn - Wt - L - 1)}")
    # ---- the sum
    st_all = " | ".join(st_terms) if st_terms else "1'b0"
    if not exact:
        _window_flags(m, st_all)
    if not cfg.get("keep_sticky", True):
        st_all = "1'b0"
    bypass = cfg.get("bypass_min") and len(prod) >= 2
    if bypass:
        # cancellation detected between the two largest products (equal exponents, opposite signs): the
        # smallest product bypasses the reduction and is added after it
        pe = [e for (_m, _w, e, _s) in prod]
        ps = [s for (_m, _w, _e, s) in prod]
        pairs = [(i, j) for i in range(len(prod)) for j in range(i + 1, len(prod))]
        m.wire("cancel", expr=" | ".join(f"(({pe[i]} == {pe[j]}) && ({ps[i]} != {ps[j]}))" for i, j in pairs))
        for k in range(len(prod)):
            m.wire(f"ismin{k}", expr=" && ".join(f"({pe[k]} <= {pe[j]})" for j in range(len(prod)) if j != k) or "1'b1")
    signed_cache = {}
    word_width = Wn
    def signed_words(sel):
        out = []
        for k, (u, s) in enumerate(words):
            if not sel(k, s):
                continue
            if sign == "twos":
                if k not in signed_cache:
                    signed_cache[k] = _neg(m, f"v{k}", u, s, word_width)
                out.append(signed_cache[k])
            else:
                out.append(u)
        return out
    if bypass:
        first = [f"(!(cancel && ismin{k}" + "".join(f" && !ismin{j}" for j in range(k)) + f")) ? {w} : {Wn}'d0"
                 if k < len(prod) else w for k, w in enumerate(signed_words(lambda k, s: True))]
        main = [m.wire(f"vm{k}", Wn, expr=e) for k, e in enumerate(first)]
    if sign == "twos":
        allw = main if bypass else signed_words(lambda k, s: True)
        if cfg.get("apart"):
            split = len(prod)//2
            left = _sum_words(m, "apart_left", allw[:split], Wn, tree, "the first product half's independent reduction")
            right = _sum_words(m, "apart_right", allw[split:len(prod)], Wn, tree, "the second product half's independent reduction")
            total = _sum_words(m, "sum", [left, right] + allw[len(prod):], Wn, tree, "the two independent product sums and C")
        else:
            total = _sum_words(m, "sum", allw, Wn, tree, "the reduction")
        if bypass:
            byp = " : ".join(f"(cancel && ismin{k}) ? v{k}" for k in range(len(prod))) + f" : {Wn}'d0"
            m.wire("vbyp", Wn, expr=byp)
            m.wire("sum_b", Wn)
            _add(m, tree[2], tree[3], Wn, total, "vbyp", "sum_b", "the bypassed smallest product added after the reduction")
            m.last_add = (total, "vbyp")
            total = "sum_b"
        last = m.last_add
    else:
        pos = [m.wire(f"vp{k}", Wn, expr=f"{s} ? {Wn}'d0 : {u}") for k, (u, s) in enumerate(words)]
        neg = [m.wire(f"vn{k}", Wn, expr=f"{s} ? {u} : {Wn}'d0") for k, (u, s) in enumerate(words)]
        P = _sum_words(m, "sump", pos, Wn, tree, "the positive terms' reduction")
        N = _sum_words(m, "sumn", neg, Wn, tree, "the negative terms' reduction")
        m.wire("dual_p", Wn + 1, expr=f"{{1'b0, {P}}}")
        m.wire("dual_n", Wn + 1, expr=f"{{1'b0, {N}}}")
        m.wire("dual_np", Wn + 1, expr="~dual_p")
        m.wire("dual_nn", Wn + 1, expr="~dual_n")
        m.wire("pmn", Wn + 1, signed=True)
        m.wire("nmp", Wn + 1, signed=True)
        _add(m, tree[2], tree[3], Wn+1, "dual_p", "dual_nn", "pmn", "the positive-minus-negative CPA", "1'b1")
        _add(m, tree[2], tree[3], Wn+1, "dual_n", "dual_np", "nmp", "the negative-minus-positive CPA", "1'b1")
        m.wire("negr", expr="pmn[" + str(Wn) + "]")
        m.wire("magr", Wn, expr=f"negr ? nmp[{Wn-1}:0] : pmn[{Wn-1}:0]")
        total = m.wire("sumd", Wn, expr=f"negr ? (~magr + {Wn}'d1) : magr")
        m.wire("dual_lza_n", Wn, expr=f"~{N}")
        last = (P, "dual_lza_n")
    # a negative term truncated at the window's bottom: its true magnitude exceeds the shifted word, so the
    # exact sum lies below the window sum by less than one lsb; one lsb is borrowed and the sticky marks
    # the interval (the engine's convention for a sticky that borrows). The dual reduction needs it as much
    # as the two's-complement one: its `sumd` is a two's-complement word by the time it reaches here, and
    # without the borrow a negative addend below the window rounds one ulp the wrong way.
    if align not in ("frame", "two_stage", "per_level") and st_terms and sign in ("twos", "dual") and cfg.get("keep_sticky", True):
        m.wire("nt_borrow", expr=" | ".join(f"({st} & {s})" for st, (_mg, _w, _e, s) in zip(st_terms, terms)))
        m.wire("nt_addend", Wn, expr=f"{{{{{Wn}{{1'b1}}}}}} ^ {{{{({Wn}-1){{1'b0}}}}, nt_borrow}}")
        m.wire("tot_adj", Wn)
        _add(m, tree[2], tree[3], Wn, total, "nt_addend", "tot_adj", "the sticky borrow correction", "1'b1")
        last = (total, "nt_addend")
        total = "tot_adj"
    # ---- segments of a long accumulator (kulisch): the frame words summed per segment, the carries
    # resolved immediately, kept as a carry word for one final add, or swept once at the end
    if cfg.get("segments"):
        seg = cfg["segments"]
        B = int(seg.get("B", 32))
        org, carry = seg.get("org", "segmented_lazy_carry"), seg.get("carry", "immediate")
        Wk = int(seg.get("width", Wn))
        if Wk < Wn:
            raise ValueError(f"{family}: accumulator_width_bits={Wk} cannot hold the {Wn}-bit exact frame")
        allw = signed_words(lambda k, s: True) if sign == "twos" else [total]
        ext = [m.wire(f"kx{k}", Wk, expr=f"{{{{({Wk}-{Wn}){{{w}[{Wn-1}]}}}}, {w}}}" if Wk > Wn else w) for k, w in enumerate(allw)]
        nseg = -(-Wk // B)
        cw = _clog2(len(ext) + 2)
        sums, couts = [], []
        for j in range(nseg):
            lo_b, hi_b = j * B, min(Wk, (j + 1) * B)
            bw = hi_b - lo_b
            slices = [m.wire(f"ks{j}_{k}", bw + cw, expr=f"{{{{{cw}{{1'b0}}}}, {w}[{hi_b-1}:{lo_b}]}}") for k, w in enumerate(ext)]
            if org == "banked_sub_adders":
                # a bank adds a term only when the term's value reaches it (its aligned word is nonzero there)
                slices = [m.wire(f"kg{j}_{k}", bw + cw, expr=f"(|{w}[{hi_b-1}:{lo_b}]) ? {sl} : {bw+cw}'d0") for k, (w, sl) in enumerate(zip(ext, slices))]
            ssum = _sum_words(m, f"kseg{j}", slices, bw + cw, tree, f"segment {j}: the terms' slices")
            sums.append((ssum, bw))
        out_segs = []
        # the segment sums as one word, the carries out of each segment as a second word (segment j's slice
        # holds the carry of segment j - 1 in its low bits). These real
        # rows also feed the selected anticipator for immediate carry.
        sw_ = m.wire("ksum", Wk, expr="{" + ", ".join(f"{s}[{bw-1}:0]" for s, bw in reversed(sums)) + "}")
        car_slices = []
        for j in range(nseg):
            bw = sums[j][1]
            if j == 0:
                car_slices.append(f"{bw}'d0")
            else:
                ps, pbw = sums[j - 1]
                car_slices.append((f"{{{bw - cw}'d0, {ps}[{pbw + cw - 1}:{pbw}]}}" if bw > cw else f"{ps}[{pbw + bw - 1}:{pbw}]"))
        cwd = m.wire("kcar", Wk, expr="{" + ", ".join(reversed(car_slices)) + "}")
        if carry == "carry_save_deferred":
            m.wire("ktot", Wk)
            _add(m, tree[2], tree[3], Wk, sw_, cwd, "ktot", "the deferred segment carries resolved by one wide adder")
            total_k = "ktot"
        else:
            cin = f"{cw}'d0"
            for j, (s, bw) in enumerate(sums):
                carry_word = m.wire(f"kr{j}_carry", bw+cw, expr=f"{{{bw}'d0, {cin}}}")
                m.wire(f"kr{j}", bw+cw)
                _add(m, tree[2], tree[3], bw+cw, s, carry_word, f"kr{j}", "the immediate segment carry propagation")
                out_segs.append(f"kr{j}[{bw-1}:0]")
                cin = f"kr{j}[{bw+cw-1}:{bw}]"
            total_k = m.wire("ktot", Wk, expr="{" + ", ".join(reversed(out_segs)) + "}")
        total = m.wire("sumk", Wn, expr=f"{total_k}[{Wn-1}:0]")
        last = (sw_, cwd)
    # ---- chunked accumulation (fp8 training datapaths): chunks of products summed, each rounded to the
    # accumulate precision and re-entered into the frame with c
    if cfg.get("chunks"):
        kch, prec = cfg["chunks"]
        vs = signed_words(lambda k, s: True) if sign == "twos" else []
        chunk_terms = []
        if getattr(prec, "man_bits", 0) + 1 > g.SW:
            raise ValueError(f"{family}: engine precision {g.SW} cannot represent the selected {prec.name} chunk rounder; "
                             "derive the geometry with internal_formats(family, pins)")
        for ci in range(0, len(prod), kch):
            tg = f"ch{ci//kch}"
            csum = _sum_words(m, tg, vs[ci:min(ci + kch, len(prod))], Wn, tree, f"chunk {ci//kch}: the products' sum")
            operands = m.last_add
            chunk_lz = lz_fam if operands is not None else "lzc_after_add"
            yx = _to_x_w(m, tg, csum, Wn, lo_expr, EWX, g, chunk_lz, lzc_fam, lza_ops=operands, norm=norm)
            rmag, rw, re_, rs = _round_trip(m, tg + "r", yx, prec, g, dg.tokens, "rnd", "word", "1'b0", f"chunk {ci//kch}", rpins)
            specials.append((f"{tg}r_rsp", rs))
            m.wire(f"{tg}_rex", EWX, signed=True, expr=f"$signed({{{{3{{{re_}[{EW-1}]}}}}, {re_}}})")
            u = _place(m, f"{tg}_u", rmag, rw, f"{tg}_rex", EWX, lo, AW, shifter, spins, f"chunk {ci//kch}: the rounded sum into the frame")
            chunk_terms.append(_neg(m, f"{tg}_v", u, rs, AW))
        rest = [_frame_of_window(m, f"cw{k}", vs[k], Wn, lo_expr, EWX, AW, lo) for k in range(len(prod), len(vs))]
        total = _sum_words(m, "sumc", chunk_terms + rest, AW, tree, "the chunk sums and c")
        Wn, lo_expr, last = AW, _slit(EWX, lo), m.last_add
        if last is None and len(prod) >= 2:
            # A single rounded chunk has no second addition. Its selected
            # anticipator is the one feeding the chunk's actual rounder.
            tail_lz_fam = "lzc_after_add"
    # ---- tensor-core partial sums: PEs of D products, each aligned to its largest exponent, its partial
    # sum rounded to d before the accumulate
    if cfg.get("pe"):
        D, prnd, target = cfg["pe"]
        from chialu.targets.rtl.families.fidelity import effective
        effective(pins, "dot_width_per_pe", D, "products in each instantiated PE")
        effective(pins, "partial_sum_rounding", prnd, "fixed intermediate rounder mode")
        effective(pins, "alignment_target", target, "PE reduction topology")
        vs = signed_words(lambda k, s: True) if sign == "twos" else []
        pe_terms = []
        rsel = "3'd0" if prnd == "rne" else "3'd1"
        for ci in range(0, len(prod), D):
            tg = f"pe{ci//D}"
            if target == "pairwise_sequential":
                cur = vs[ci]
                for k in range(ci + 1, min(ci + D, len(prod))):
                    tgk = f"{tg}_{k}"
                    m.wire(f"{tgk}_s", Wn)
                    _add(m, tree[2], tree[3], Wn, cur, vs[k], f"{tgk}_s", f"PE {ci//D}: pairwise sequential add {k}")
                    yx = _to_x_w(m, tgk, f"{tgk}_s", Wn, lo_expr, EWX, g, lz_fam, lzc_fam,
                                 lza_ops=(cur, vs[k]), norm=norm)
                    rmag, rw, re_, rs = _round_trip(m, tgk + "r", yx, target_fmt(dg), g, dg.tokens, rsel, "word", "1'b0", f"PE {ci//D}: partial sum {k}", rpins)
                    specials.append((f"{tgk}r_rsp", rs))
                    m.wire(f"{tgk}_rex", EWX, signed=True, expr=f"$signed({{{{3{{{re_}[{EW-1}]}}}}, {re_}}})")
                    m.wire(f"{tgk}_wl", EWX, signed=True, expr=lo_expr)
                    # back into the window: mag * 2^(re - lo_expr)
                    m.wire(f"{tgk}_dsh", EWX, signed=True, expr=f"{tgk}_rex - {tgk}_wl")
                    m.wire(f"{tgk}_ux", Wn, expr=f"{{{{({Wn}-{rw}){{1'b0}}}}, {rmag}}}")
                    m.wire(f"{tgk}_ok", expr=f"({tgk}_dsh >= 0) && ({tgk}_dsh < {Wn})")
                    m.wire(f"{tgk}_dn", EWX, signed=True, expr=f"-{tgk}_dsh")
                    m.wire(f"{tgk}_ul", Wn, expr=f"{tgk}_ok ? ({tgk}_ux << {tgk}_dsh[{_clog2(Wn)-1}:0]) : ({tgk}_dsh < 0 && {tgk}_dn < {Wn}) ? ({tgk}_ux >> {tgk}_dn[{_clog2(Wn)-1}:0]) : {Wn}'d0")
                    cur = _neg(m, f"{tgk}_v", f"{tgk}_ul", rs, Wn)
                psum = cur
                operands = None  # cur already passed through the PE rounder.
            else:
                psum = _sum_words(m, tg, vs[ci:min(ci + D, len(prod))], Wn, tree, f"PE {ci//D}: the products aligned to the largest exponent")
                operands = m.last_add
            pe_lz = lz_fam if operands is not None else "lzc_after_add"
            yx = _to_x_w(m, tg + "x", psum, Wn, lo_expr, EWX, g, pe_lz, lzc_fam, lza_ops=operands, norm=norm)
            rmag, rw, re_, rs = _round_trip(m, tg + "r", yx, target_fmt(dg), g, dg.tokens, rsel, "word", "1'b0", f"PE {ci//D}: the partial sum", rpins)
            specials.append((f"{tg}r_rsp", rs))
            m.wire(f"{tg}_rex", EWX, signed=True, expr=f"$signed({{{{3{{{re_}[{EW-1}]}}}}, {re_}}})")
            u = _place(m, f"{tg}_u", rmag, rw, f"{tg}_rex", EWX, lo, AW, shifter, spins, f"PE {ci//D}: the rounded partial sum into the frame")
            pe_terms.append(_neg(m, f"{tg}_v", u, rs, AW))
        rest = [_frame_of_window(m, f"pw{k}", vs[k], Wn, lo_expr, EWX, AW, lo) for k in range(len(prod), len(vs))]
        total = _sum_words(m, "sumt", pe_terms + rest, AW, tree, "the PEs' partial sums and c")
        Wn, lo_expr, last = AW, _slit(EWX, lo), m.last_add
        if last is None:
            tail_lz_fam = "lzc_after_add"
    # ---- outputs
    if align == "band":
        if Wn != bg.BW:
            # All requested-width product adders have already been
            # instantiated. Only redundant sign bits above the proven
            # product bound are removed at the near/far interface.
            total = m.wire("bounded_product_sum", bg.BW, expr=f"{total}[{bg.BW-1}:0]")
        return band_stage(total, None, tree)
    if lines:
        # the clusters' fields of the sum: above a realignment line k the clusters that precede it (a zero field
        # when they cancel or are absent), below it the rest; the first line whose upper field is nonzero selects
        # the result, that field left-aligned, its lsb exponent from the start of the cluster above the line, the
        # field below it as the sticky (the floor convention: a negative lower field borrowed one lsb already)
        # the field is the floor of the cluster's value at the line boundary (a negative lower field borrowed one
        # lsb), so the cluster is zero when the field is zero with a non-negative lower field or all ones with a
        # negative one; the word extends the field by XW bits of the borrow (ones below a borrowed lsb, else
        # zeros), which are the exact bits there, since the lower field lies below the X's lsb
        WA = Wn
        lw_ = WA // T
        WO = WA + XW
        for j in range(T):
            m.wire(f"lbase{j}", EWX, signed=True, expr=f"{es[j]} - {_slit(EWX, tops[j] + XW)}")
        def base_above(k):
            return " : ".join(f"lflag{j} ? lbase{j}" for j in range(k - 1, 0, -1)) + (" : " if k > 1 else "") + "lbase0"
        sels = []
        for k in range(1, T):
            mk = (T - k) * lw_
            fw = WA - mk
            m.wire(f"lbn{k}", expr=f"{total}[{mk-1}]")
            m.wire(f"lnz{k}", expr=f"lbn{k} ? ({total}[{WA-1}:{mk}] != {{{fw}{{1'b1}}}}) : ({total}[{WA-1}:{mk}] != {fw}'d0)")
            m.wire(f"lsel{k}", expr=f"lflag{k} && lnz{k}" + "".join(f" && !lsel{j}" for j in range(1, k)))
            m.wire(f"lword{k}", WO, expr=f"{{{total}[{WA-1}:{mk}], {{{XW}{{lbn{k}}}}}, {mk}'d0}}")
            m.wire(f"llo{k}", EWX, signed=True, expr=base_above(k))
            m.wire(f"lst{k}", expr=f"|{total}[{mk-1}:0]")
            if last is not None and lz_fam == "lza":
                m.wire(f"lopa{k}", WO, expr=f"{{{last[0]}[{WA-1}:{mk}], {mk + XW}'d0}}")
                m.wire(f"lopb{k}", WO, expr=f"{{{last[1]}[{WA-1}:{mk}], {mk + XW}'d0}}")
            sels.append(k)
        m.wire("llo_t", EWX, signed=True, expr=base_above(T))
        m.wire("lword", WO, expr=" : ".join(f"lsel{k} ? lword{k}" for k in sels) + f" : {{{total}, {XW}'d0}}")
        m.wire("llo", EWX, signed=True, expr=" : ".join(f"lsel{k} ? llo{k}" for k in sels) + " : llo_t")
        m.wire("lst", expr=" : ".join(f"lsel{k} ? lst{k}" for k in sels) + " : 1'b0")
        ops = None
        if last is not None and lz_fam == "lza":
            m.wire("lopa", WO, expr=" : ".join(f"lsel{k} ? lopa{k}" for k in sels) + f" : {{{last[0]}, {XW}'d0}}")
            m.wire("lopb", WO, expr=" : ".join(f"lsel{k} ? lopb{k}" for k in sels) + f" : {{{last[1]}, {XW}'d0}}")
            ops = ("lopa", "lopb")
        m.assign("y", _to_x_w(m, "o", "lword", WO, "llo", EWX, g, lz_fam, lzc_fam, "lst", ops, norm=norm))
        return name, m.render(), {"rnd": False}
    emit_out(total, Wn, lo_expr, st_all, last)
    # one product rounded to d and added to c under one more rounding is the sequential contract
    flags_out = _rounding_flags(m)
    return name, m.render(), {"rnd": needs_rnd, "flags": flags_out, "product_classification": bool(cfg.get("approximate_product")),
                              "contract": "architecture" if cfg.get("pe") or cfg.get("chunks")
                              or (not exact and not cfg.get("fused_window")) or cfg.get("approximate_product") else "fused"}


def target_fmt(dg: DotGeom):
    """The float format of d a tensor-core PE rounds its partial sum to."""
    return dg.fd


# ---- the integer geometry ----------------------------------------------------------
def _composable_product(m: Mod, t: int, a: str, b: str, W: int, signed: bool, levels: int, mul: tuple, apart: bool,
                        dimensions: str = "two") -> str:
    """p<t>: the W x W product from 2^(2 levels) sub-multipliers of W / 2^levels
    bits (the Bit Fusion composition): the operands split into a signed top
    part and unsigned lower parts, every pair of parts multiplied by a
    library sub-multiplier (a signed one over the sign-extended parts), the
    partial products shifted and added; `apart` sums the products of each
    row of parts before combining the rows."""
    parts = 1 << levels
    parts_b = parts if dimensions == "two" else 1
    h, hb = W // parts, W // parts_b
    if h * parts != W or h < 2:
        raise ValueError(f"composable submultipliers need at least {2*parts} bits and a width divisible by {parts}")
    mul_fam, mul_pins = mul
    sub_w = max(h, hb) + 1                           # a sign-extended part: the top part keeps its sign
    rows = []
    for i in range(parts):
        row = []
        for j in range(parts_b):
            ai = f"a{t}_p{i}"
            bj = f"b{t}_p{j}"
            if not m.declared_(ai):
                top_i = signed and i == parts - 1
                sg = f"{a}[{(i+1)*h-1}]" if top_i else "1'b0"
                m.wire(ai, sub_w, expr=f"{{{{{sub_w-h}{{{sg}}}}}, {a}[{(i+1)*h-1}:{i*h}]}}")
            if not m.declared_(bj):
                top_j = signed and j == parts_b - 1
                sg = f"{b}[{(j+1)*hb-1}]" if top_j else "1'b0"
                m.wire(bj, sub_w, expr=f"{{{{{sub_w-hb}{{{sg}}}}}, {b}[{(j+1)*hb-1}:{j*hb}]}}")
            pij = m.wire(f"p{t}_{i}_{j}", 2 * sub_w, signed=True)
            if not _inst_mul(m, mul_fam, mul_pins, sub_w, True, ai, bj, pij, f"product {t}: sub-multiplier ({i}, {j}) of {sub_w} bits ({mul_fam})"):
                m.assign(pij, f"$signed({ai}) * $signed({bj})")
            ext = (f"{{{{({2*W}-{2*sub_w}){{{pij}[{2*sub_w-1}]}}}}, {pij}}}" if sub_w < W
                   else f"{pij}[{2*W-1}:0]" if sub_w > W else pij)
            row.append(m.wire(f"p{t}_{i}_{j}s", 2 * W, signed=True, expr=f"$signed({ext}) <<< {i*h + j*hb}"))
        rows.append(row)
    if apart:
        rsums = [m.wire(f"p{t}_r{i}", 2 * W, signed=True, expr=" + ".join(rows[i])) for i in range(parts)]
        return m.wire(f"p{t}", 2 * W, signed=True, expr=" + ".join(rsums))
    return m.wire(f"p{t}", 2 * W, signed=True, expr=" + ".join(x for row in rows for x in row))


def integer_sum_width(dg: DotGeom) -> int:
    """Signed width sufficient for every exact integer-mode sum in its frame."""
    W, signed, F, Wc, signed_c, Fc = dg.intg
    if signed:
        pmin = -(1 << (W - 1)) * ((1 << (W - 1)) - 1)
        pmax = 1 << (2 * W - 2)
    else:
        pmin, pmax = 0, ((1 << W) - 1) ** 2
    low = dg.n * (pmin << (-2 * F - dg.lo))
    high = dg.n * (pmax << (-2 * F - dg.lo))
    if dg.acc:
        cmin = -(1 << (Wc - 1)) if signed_c else 0
        cmax = (1 << (Wc - int(signed_c))) - 1
        low += cmin << (-Fc - dg.lo)
        high += cmax << (-Fc - dg.lo)
    return max(2, high.bit_length() + 1, (~low).bit_length() + 1)


def _integer_segmented_sum(m, words, width, tree, segment):
    """Resolve independently summed slices using the selected carry network."""
    B = int(segment["B"])
    org, carry = segment["org"], segment["carry"]
    cw = _clog2(len(words) + 2)
    sums = []
    for index, start in enumerate(range(0, width, B)):
        bw = min(B, width - start)
        slices = []
        for k, word in enumerate(words):
            source = f"{word}[{start+bw-1}:{start}]"
            if org == "banked_sub_adders":
                source = f"(|{source}) ? {source} : {bw}'d0"
                source = m.wire(f"ik{index}_{k}_gate", bw, expr=source)
            slices.append(m.wire(f"ik{index}_{k}", bw + cw, expr=f"{{{cw}'d0, {source}}}"))
        value = _sum_words(m, f"iksum{index}", slices, bw + cw, tree, f"integer accumulator segment {index}")
        sums.append((value, bw))
    sw = m.wire("ik_sum", width, expr="{" + ", ".join(f"{word}[{bw-1}:0]" for word, bw in reversed(sums)) + "}")
    rows = []
    for index, (_, bw) in enumerate(sums):
        if index == 0:
            rows.append(f"{bw}'d0")
        else:
            prev, pw = sums[index - 1]
            rows.append(f"{{{bw-cw}'d0, {prev}[{pw+cw-1}:{pw}]}}" if bw > cw else f"{prev}[{pw+bw-1}:{pw}]")
    cr = m.wire("ik_carry", width, expr="{" + ", ".join(reversed(rows)) + "}")
    m.last_add = (sw, cr)
    if carry == "carry_save_deferred":
        total = m.wire("ik_total", width)
        _add(m, tree[2], tree[3], width, sw, cr, total, "the integer accumulator's deferred carry word")
        return total
    carry_in = f"{cw}'d0"
    rows = []
    for index, (word, bw) in enumerate(sums):
        carry_word = m.wire(f"ik_cin{index}", bw+cw, expr=f"{{{bw}'d0, {carry_in}}}")
        result = m.wire(f"ik_res{index}", bw+cw)
        _add(m, tree[2], tree[3], bw+cw, word, carry_word, result, "the integer accumulator's immediate segment carry")
        rows.append(f"{result}[{bw-1}:0]")
        carry_in = f"{result}[{bw+cw-1}:{bw}]"
    return m.wire("ik_total", width, expr="{" + ", ".join(reversed(rows)) + "}")


def _acc_int_sv(dg: DotGeom, family: str, pins: dict, cfg: dict, name: str) -> tuple:
    """(name, text, info): an accumulator-style family on raw integer or
    fixed-point operands: the products by a signed or unsigned library
    multiplier (or sub-multipliers), the products and c at their constant
    frame positions, the reduction tree or the flattened carry-save tree."""
    W, signed, F, Wc, signed_c, Fc = dg.intg
    n, AW, lo = dg.n, dg.AW, dg.lo
    g = dg.g
    tree = cfg["tree"]
    mul_fam, mul_pins = cfg.get("mul", (None, {}))
    sp, sc = -2 * F - lo, -Fc - lo
    # the datapath's own width: the exact integer sum (the seed's frame is wider by its normalization margin)
    Wi = min(AW, max(2 * W + sp, (Wc + sc) if dg.acc else 1) + _clog2(n + 2) + 2)
    if cfg.get("declared_acc_width"):
        Wi = int(cfg["declared_acc_width"])
        need = integer_sum_width(dg)
        if Wi < need:
            raise ValueError(f"{family}: accumulator_width_bits={Wi} cannot hold all exact sums "
                             f"of this geometry; at least {need} bits are required")
        from chialu.targets.rtl.families.fidelity import effective
        effective(pins, "accumulator_width_bits", Wi, "width of the integer reduction word")
    notes = list(cfg.get("notes", []))
    m = Mod(name, f"dot-accumulate ({family}) for {n} products of {W}-bit {'signed' if signed else 'unsigned'} operands"
                  + (f" and a {Wc}-bit c" if dg.acc else "") + f" in a {Wi}-bit datapath: {cfg.get('comment', '')}; "
                  f"meets {cfg.get('contract', 'the fused contract (the integer sum is exact)')}" + ("; " + "; ".join(notes) if notes else ""))
    m.port("input", "a", n * W)
    m.port("input", "b", n * W)
    if dg.acc:
        m.port("input", "c", Wc)
    dg.ports_out(m)

    def emit_out(total: str):
        m.wire("acc_i", AW, signed=True, expr=(f"{{{{({AW}-{Wi}){{{total}[{Wi-1}]}}}}, {total}}}" if AW > Wi
                                              else f"{total}[{AW-1}:0]" if Wi > AW else total))
        if dg.out == "acc":
            m.assign("acc", "acc_i")
        else:
            lz_fam, counter = cfg.get("lz", ("lzc_after_add", None))
            m.assign("y", _to_x_w(m, "o", total, Wi, _slit(g.EW+3, lo), g.EW+3, g, lz_fam, counter,
                                  lza_ops=getattr(m, "last_add", None), norm=cfg.get("norm", (None, {}))))
    for t in range(n):
        m.wire(f"a{t}", W, expr=f"a[{t*W} +: {W}]")
        m.wire(f"b{t}", W, expr=f"b[{t*W} +: {W}]")
    if cfg.get("mul_style") == "twin":
        from chialu.targets.rtl.families import subword
        tn, tt = subword.twin_precision_sv(n * W, [W], [signed], mul_pins)
        m.extra.append(tt)
        m.wire("tw_p", 2 * n * W)
        m.n += 1
        m.raw(f"  {tn} u{m.n} (.a(a), .b(b), .sel(1'b0), .p(tw_p));")
    if cfg.get("flatten"):
        # fused_csa: the rows a_i * b of every product (a signed row's sign extension replaced by its
        # inverted sign bit and a constant; the last row of a signed multiplier subtracted: inverted bits,
        # a one and the constant) and c, all at their columns, one carry-save reduction and one CPA
        nl = Netlist()
        cols = [[] for _ in range(Wi)]
        const = 0
        mask = (1 << Wi) - 1
        for t in range(n):
            for i in range(W):
                last = signed and i == W - 1
                off = i + sp
                for k in range(W):
                    if off + k >= Wi:
                        break
                    bit = f"(a{t}[{i}] & b{t}[{k}])"
                    cols[off + k].append(nl.wire(f"~{bit}" if last else bit, "pp"))
                if signed and off + W < Wi:
                    # the row's sign (a_i and b negative), extended: -s 2^(off+W) = ~s 2^(off+W) - 2^(off+W);
                    # the subtracted last row extends the other way
                    srow = nl.wire(f"a{t}[{i}] & b{t}[{W-1}]", "pp")
                    cols[off + W].append(srow if last else nl.wire(f"~{srow}", "pp"))
                    const -= 1 << (off + W)
                if last:
                    const += 1 << off
        if dg.acc:
            for k in range(Wc):
                if sc + k < Wi:
                    cols[sc + k].append(f"c[{k}]")
            if signed_c and sc + Wc < Wi:
                cols[sc + Wc].append(nl.wire(f"~c[{Wc-1}]", "pp"))
                const -= 1 << (sc + Wc)
        const &= mask
        for k in range(Wi):
            if (const >> k) & 1:
                cols[k].append("1'b1")
        comp = tree[1]
        cols = _reduce_7_3(nl, cols) if comp == "7:3" else _reduce_cols(nl, cols, "dadda", "4_2" if comp == "4:2" else "3_2")
        m.raw(f"  // the flattened partial products of every product and c in one carry-save reduction ({comp} compressors: "
              f"{nl.fa_count} full adders, {nl.ha_count} half adders)")
        _render_nl(m, nl, "f")
        rs, rc = _rows_of(cols, Wi, "f")
        m.wire("f_rs", Wi, expr=rs)
        m.wire("f_rc", Wi, expr=rc)
        m.wire("acc_f", Wi, signed=True)
        _add(m, tree[2], tree[3], Wi, "f_rs", "f_rc", "acc_f", f"the root CPA ({tree[2]})")
        emit_out("acc_f")
        return name, m.render(), {"rnd": False}
    words, product_words = [], []
    for t in range(n):
        if cfg.get("composable"):
            levels, apart, dimensions = cfg["composable"]
            p = _composable_product(m, t, f"a{t}", f"b{t}", W, signed, levels, (mul_fam, mul_pins), apart, dimensions)
        elif cfg.get("mul_style") == "twin":
            p = m.wire(f"p{t}", 2 * W, signed=signed, expr=f"tw_p[{2*W*t} +: {2*W}]")
        else:
            p = m.wire(f"p{t}", 2 * W, signed=signed)
            if not _inst_mul(m, mul_fam, mul_pins, W, signed, f"a{t}", f"b{t}", p, f"product {t}: the {W}-bit {'signed' if signed else 'unsigned'} multiplier ({mul_fam})"):
                m.assign(p, f"$signed(a{t}) * $signed(b{t})" if signed else f"a{t} * b{t}")
        ext = f"{{{{({Wi}-{2*W}){{{p}[{2*W-1}]}}}}, {p}}}" if signed else f"{{{{({Wi}-{2*W}){{1'b0}}}}, {p}}}"
        if Wi <= 2 * W:
            ext = f"{p}[{Wi-1}:0]"
        words.append(m.wire(f"v{t}", Wi, expr=f"({ext}) << {sp}" if sp else ext))
        product_words.append(p)
    if cfg.get("approximate_product"):
        m.port("output", "product_nonzero")
        m.port("output", "products_negative")
        m.assign("product_nonzero", " | ".join(f"(|{word})" for word in product_words))
        m.assign("products_negative", " & ".join(f"{word}[{2*W-1}]" for word in product_words) if signed else "1'b0")
    if dg.acc:
        ext = f"{{{{({Wi}-{Wc}){{c[{Wc-1}]}}}}, c}}" if signed_c else f"{{{{({Wi}-{Wc}){{1'b0}}}}, c}}"
        if Wi <= Wc:
            ext = f"c[{Wi-1}:0]"
        words.append(m.wire("vc", Wi, expr=f"({ext}) << {sc}" if sc else ext))
    if cfg.get("segments"):
        total = _integer_segmented_sum(m, words, Wi, tree, cfg["segments"])
    elif cfg.get("apart") and n >= 2:
        # sum apart: the products of each half summed on their own, the halves combined with c
        h = n // 2
        s0 = _sum_words(m, "half0", words[:h], Wi, tree, "the first half's products")
        s1 = _sum_words(m, "half1", words[h:n], Wi, tree, "the second half's products")
        total = _sum_words(m, "sum", [s0, s1] + words[n:], Wi, tree, "the halves and c")
    else:
        total = _sum_words(m, "sum", words, Wi, tree, "the reduction")
    emit_out(total)
    return name, m.render(), {"rnd": False, "product_classification": bool(cfg.get("approximate_product")),
                              "contract": "architecture" if cfg.get("approximate_product") else "fused"}


# ---- the FMA lineage ---------------------------------------------------------------------
def _fma_sv(dg: DotGeom, family: str, pins: dict, name: str) -> tuple:
    """(name, text, info): d = c + a * b for a one-element mode (classic_fma,
    reduced_latency_fma, multipath_fma)."""
    g, S, Sc, AW, lo = dg.g, dg.S, dg.Sc, dg.AW, dg.lo
    XW, EW, XT = g.XW, g.EW, g.XT
    EWX = EW + 3
    if dg.n != 1 or not dg.acc:
        raise ValueError(EXCEPTIONS["classic_fma, reduced_latency_fma, multipath_fma, bridge_fma, mixed_precision_cascade_fma "
                                    "on a mode of several elements under the fused contract"])
    mul_fam = str(_pin(pins, "multiplier.family", "behavioral_star"))
    mul_pins = _sub(pins, "multiplier.")
    shifter, spins = (pins.get("align.shifter.family") or None), _sub(pins, "align.shifter.")
    norm = ((pins.get("norm_shifter.family") or None), _sub(pins, "norm_shifter."))
    cfam, cpins = _cpa_of(pins, "cpa")
    lz_fam = _LeadingZeroChoice(dict(pins, **{"lza.family": pins.get("lza.family", "lza")}))
    lzc_fam = pins.get("lza.counter.family") or pins.get("lza.encoder.family") or None
    if lzc_fam:
        lzc_fam = (lzc_fam, _sub(pins, "lza.counter." if pins.get("lza.counter.family") else "lza.encoder."))
    negation = str(_pin(pins, "negation_handling", "end_around_carry"))
    paths = _pin(pins, "path_count", 2) if family == "multipath_fma" else 1
    criterion = str(_pin(pins, "path_select_criterion", "exponent_difference"))
    if family == "multipath_fma":
        if type(paths) is not int or not 2 <= paths <= 5:
            raise ValueError("multipath_fma path_count must be an integer in 2..5")
        if criterion not in ("exponent_difference", "cancellation_estimate", "both"):
            raise ValueError(f"multipath_fma has no path_select_criterion {criterion!r}")
        from chialu.targets.rtl.families.fidelity import effective
        effective(pins, "path_count", paths, "reachable close/far paths and optional zero-operand bypass")
        effective(pins, "path_select_criterion", criterion, "close-subtraction criterion; close additions use exponent proximity")
    fused_round = family == "reduced_latency_fma" and str(_pin(pins, "rounding_position", "post_cpa")) == "fused_with_cpa_dual_sum"
    pre_norm = family == "reduced_latency_fma" and _truthy(_pin(pins, "normalize_before_add", False))
    if family == "reduced_latency_fma":
        from chialu.targets.rtl.families.fidelity import effective
        effective(pins, "normalize_before_add", pre_norm, "operand normalization before the CPA" if pre_norm else "result normalization after the CPA")
        effective(pins, "rounding_position", "fused_with_cpa_dual_sum" if fused_round else "post_cpa",
                  "compound-CPA rounding candidates" if fused_round else "terminal rounding after the CPA")
    fd = dg.fd
    from chialu.verify.formats import FloatFormat
    M = getattr(fd, "man_bits", None) if isinstance(fd, FloatFormat) else None
    bias = getattr(fd, "bias", 0)
    if fused_round and M is None:
        raise ValueError(f"{family}: fused_with_cpa_dual_sum requires a floating-point destination")
    # G guard bits below the product: the engine's X carries XW significand bits, more than the product's 2S, so
    # the bits of c that fall just below the product stay in the window (the classic 3M + 2 window at the
    # target's precision has none)
    G = max(0, XW - 2 * S) + 3
    Wn = 2 * S + Sc + 3 + G
    notes = []
    if family == "reduced_latency_fma":
        if fused_round:
            if fd.exp_only:
                notes.append("one-bit compound rounding to a power of two, with nearest ties using exponent-field parity; "
                             "field zero is a finite value; the exponent rounder preserves ROUNDED inexact/overflow flags; "
                             "values outside the finite exponent fields before rounding and SR leave unrounded")
            else:
                notes.append(f"the rounding for {M+1} bits is fused into the compound adder for a normal result "
                             f"(it leaves with the ROUNDED code, the seed packs it through the library rounder); a "
                             f"subnormal, an overflow and the stochastic mode leave unrounded")
    m = Mod(name, f"fused multiply-add ({family}): the {Sc}-bit addend aligned against the {2*S}-bit product over a {Wn}-bit "
                  f"window ({G} guard bits below the product for the X's {XW}-bit significand; a sticky lsb holds what leaves "
                  f"it), the significand multiplier {mul_fam}, the window adder {cfam}, "
                  f"negation by {negation}, leading zeros by {lz_fam}, "
                  + (f"{paths} paths selected by {criterion}, " if paths > 1 else "")
                  + ("normalized before the add, " if pre_norm else "") + "one normalize; meets the fused contract"
                  + ("; " + "; ".join(notes) if notes else ""))
    m.port("input", "xa", XT)
    m.port("input", "xb", XT)
    m.port("input", "xc", XT)
    if fused_round:
        m.port("input", "rnd", 3)
    dg.ports_out(m)
    _x_fields(m, "xa", g, "a_")
    _x_fields(m, "xb", g, "b_")
    _x_fields(m, "xc", g, "c_")
    # the multiplier operands normalized at entry (a subnormal operand keeps its leading zeros as unpacked, and
    # a product with leading zeros would put the X's low bits below the window's guard bits)
    # the subnormal operands normalized at entry (the dot's exact contract: a product with leading zeros would put
    # the X's low bits below the window's guard bits) or as stored (the ALU's fp_fma under the IEEE modes: the
    # exponent alignment places them, the one normalize after the sum absorbs the leading zeros)
    as_stored = str(_pin(pins, "subnormal_representation", "pseudo_normalized_wide_exponent")) == "as_stored"
    lwa = _clog2(S)
    for o in ("a", "b"):
        m.wire(f"s{o}0", S, expr=f"{o}_sig[{S-1}:0]")
        if S == 1 or as_stored:
            m.wire(f"{o}_lzs", lwa, expr=f"{lwa}'d0")
            m.wire(f"s{o}", S, expr=f"s{o}0")
        else:
            _lz(m, lzc_fam, {}, f"s{o}0", S, f"{o}_lz", f"operand {o}'s leading zeros")
            m.wire(f"{o}_lzs", lwa, expr=f"(s{o}0 == 0) ? {lwa}'d0 : {o}_lz[{lwa-1}:0]")
            _sh(m, norm[0], norm[1], f"s{o}0", S, f"{o}_lzs", 0, f"s{o}", f"operand {o} normalized")
        m.wire(f"e{o}", EWX, signed=True, expr=f"$signed({{{{3{{{o}_e[{EW-1}]}}}}, {o}_e}}) - $signed({{{{({EWX}-{lwa}){{1'b0}}}}, {o}_lzs}})")
    bypass_add = ((family == "classic_fma" and _truthy(_pin(pins, "subsume_fp_add", False))) or
                  (family == "reduced_latency_fma" and _truthy(_pin(pins, "add_skip_for_pure_addition", False))))
    if family == "reduced_latency_fma":
        effective(pins, "add_skip_for_pure_addition", bypass_add,
                  "a=+1 selects the shifted b significand in place of the multiplier output" if bypass_add else "all finite products use the significand multiplier")
    product = "p_mul" if bypass_add else "p"
    m.wire(product, 2 * S)
    if not _inst_mul(m, mul_fam, mul_pins, S, False, "sa", "sb", product, f"the significand product ({mul_fam})"):
        m.assign(product, "sa * sb")
    if bypass_add:
        m.wire("pure_add", expr=f"!a_s && (ea == -{EWX}'sd{S-1}) && (sa == {S}'d{1 << (S-1)})")
        m.wire("p", 2 * S, expr=f"pure_add ? {{1'b0, sb, {S-1}'d0}} : p_mul")
    m.wire("ep", EWX, signed=True, expr="ea + eb")
    m.wire("sp", expr="a_s ^ b_s")
    # the addend normalized at entry (a subnormal c keeps its leading zeros as unpacked): the product shifts
    # under it only when c's leading one is at the top of its field, else bits the X needs would be lost
    m.wire("sc0", Sc, expr=f"c_sig[{Sc-1}:0]")
    m.wire("ec0", EWX, signed=True, expr=f"$signed({{{{3{{c_e[{EW-1}]}}}}, c_e}})")
    lwc = _clog2(Sc)
    if Sc == 1 or as_stored:
        m.wire("c_lzs", lwc, expr=f"{lwc}'d0")
        m.wire("sc", Sc, expr="sc0")
    else:
        _lz(m, lzc_fam, {}, "sc0", Sc, "c_lz", "the addend's leading zeros")
        m.wire("c_lzs", lwc, expr=f"(sc0 == 0) ? {lwc}'d0 : c_lz[{lwc-1}:0]")
        _sh(m, norm[0], norm[1], "sc0", Sc, "c_lzs", 0, "sc", "the addend normalized")
    m.wire("ec", EWX, signed=True, expr=f"ec0 - $signed({{{{({EWX}-{lwc}){{1'b0}}}}, c_lzs}})")
    m.wire("eff_sub", expr="sp ^ c_s")
    # ---- alignment: the addend sits 2 bits above the product's msb and shifts right by (2S + 2) - (ec - ep);
    # when that is negative the addend is far larger and the product shifts right instead (a zero addend
    # leaves the product in place)
    # a zero product (a zero operand's exponent means nothing): the addend stays in place, unshifted
    m.wire("ep_e", EWX, signed=True, expr=f"(p == 0) ? (ec - {_slit(EWX, 2 * S + 2)}) : ep")
    m.wire("d", EWX, signed=True, expr="ec - ep_e")
    m.wire("shc0", EWX, signed=True, expr=f"{_slit(EWX, 2 * S + 2)} - d")
    m.wire("shc", EWX, signed=True, expr=f"(sc0 == 0) ? {EWX}'sd0 : shc0")
    m.wire("c_case", expr="shc >= 0")
    m.wire("ef", EWX, signed=True, expr=f"(c_case ? ep_e : (ep_e - shc)) - {_slit(EWX, G)}")
    m.wire("w0c", Wn, expr=f"{{1'b0, sc, {2*S+2+G}'d0}}")
    m.wire("w0p", Wn, expr=f"{{{{({Wn}-{2*S}-{G}){{1'b0}}}}, p, {G}'d0}}")
    m.wire("amt0", EWX, signed=True, expr="c_case ? shc : (-shc)")
    m.wire("far", expr=f"amt0 >= {Wn}")
    aw = _clog2(Wn)
    m.wire("amt", aw, expr=f"far ? {aw}'d0 : amt0[{aw-1}:0]")
    m.wire("wsel", Wn, expr="c_case ? w0c : w0p")
    sticky_method = str(pins.get("align.sticky_method", "or_tree_shifted_out"))
    _sh(m, shifter, spins, "wsel", Wn, "amt", 1, "wsh", "the alignment shifter (the addend, or the product when the addend is far larger)",
        sticky="wshift_st" if sticky_method == "or_tree_shifted_out" else None)
    if sticky_method == "or_tree_shifted_out":
        m.wire("wst", expr="far ? (|wsel) : wshift_st")
    elif sticky_method == "trailing_zero_compare":
        _tz(m, pins.get("align.tzc.family"), _sub(pins, "align.tzc."), "wsel", Wn, "wal_tzc", "the alignment's trailing-zero comparator")
        m.wire("wst", expr="(|wsel) && (far || wal_tzc < amt)")
    elif sticky_method == "precomputed_mask":
        m.wire("wmask", Wn, expr=f"far ? {{{Wn}{{1'b1}}}} : ~({{{Wn}{{1'b1}}}} << amt)")
        m.wire("wst", expr="|(wsel & wmask)")
    else:
        raise ValueError(f"unknown alignment sticky method {sticky_method}")
    from chialu.targets.rtl.families.fidelity import effective
    effective(pins, "align.sticky_method", sticky_method, "shifted-out OR, mask, or trailing-zero comparison")
    m.wire("wal", Wn, expr=f"far ? {Wn}'d0 : wsh")
    m.wire("c_al", Wn, expr="c_case ? wal : w0c")
    m.wire("p_al", Wn, expr="c_case ? w0p : wal")
    m.wire("st_c", expr="c_case ? wst : 1'b0")
    m.wire("st_p", expr="c_case ? 1'b0 : wst")
    # the window words with the sticky as an extra lsb, so a subtraction borrows through it
    IW = Wn + 1
    m.wire("X", IW, expr="{p_al, st_p}")
    m.wire("Y", IW, expr="{c_al, st_c}")

    def core(tag: str, X: str, Y: str, big_norm: bool, negative_before_shift=None):
        """(mag, sign, last_add) of |X +/- Y| by the negation style; big_norm
        asks for the full normalizer (a far path needs a 2-bit one)."""
        m.wire(f"{tag}_yop", IW, expr=f"eff_sub ? ~{Y} : {Y}")
        if negation == "dual_adder":
            m.wire(f"{tag}_r1", IW)
            m.wire(f"{tag}_r2", IW)
            m.wire(f"{tag}_c1")
            m.wire(f"{tag}_c2")
            _add(m, cfam, cpins, IW, X, f"{tag}_yop", f"{tag}_r1", f"{tag}: X + Y (or X - Y)", "eff_sub", f"{tag}_c1")
            m.wire(f"{tag}_xop", IW, expr=f"~{X}")
            _add(m, cfam, cpins, IW, f"{tag}_xop", Y, f"{tag}_r2", f"{tag}: the dual adder: Y - X", "1'b1", f"{tag}_c2")
            m.wire(f"{tag}_neg", expr=negative_before_shift or f"eff_sub && !{tag}_c1")
            mag = m.wire(f"{tag}_mag", IW, expr=f"{tag}_neg ? {tag}_r2 : {tag}_r1")
            last = (X, f"{tag}_yop")
        elif negation == "complement_recode":
            m.wire(f"{tag}_r", IW)
            m.wire(f"{tag}_co")
            _add(m, cfam, cpins, IW, X, f"{tag}_yop", f"{tag}_r", f"{tag}: X + Y (or X - Y in two's complement)", "eff_sub", f"{tag}_co")
            m.wire(f"{tag}_neg", expr=negative_before_shift or f"eff_sub && !{tag}_co")
            mag = m.wire(f"{tag}_mag", IW, expr=f"{tag}_neg ? (~{tag}_r + {IW}'d1) : {tag}_r")
            last = (X, f"{tag}_yop")
        else:
            # end-around carry: X + ~Y without the one; a carry out says X > Y and the one is added back,
            # else the result is the ones' complement of the difference
            m.wire(f"{tag}_r", IW)
            m.wire(f"{tag}_co")
            _add(m, cfam, cpins, IW, X, f"{tag}_yop", f"{tag}_r", f"{tag}: X + Y, or X + ~Y (the end-around carry)", "1'b0", f"{tag}_co")
            m.wire(f"{tag}_inc", IW)
            m.wire(f"{tag}_ico")
            # A pre-normalized operand may wrap individually while the
            # difference still fits. Its post-shift CPA carry then cannot
            # determine the original ordering. Correct the modular sum
            # using the sign established before shifting.
            inc_carry = "1'b1" if negative_before_shift else f"{tag}_co"
            if not m.inst("incr", "prefix_and_incrementer", {}, IW, f".a({tag}_r), .cin({inc_carry}), .s({tag}_inc), .cout({tag}_ico)",
                          f"{tag}: the end-around carry added back"):
                m.assign(f"{tag}_inc", f"{tag}_r + {inc_carry}")
            m.wire(f"{tag}_neg", expr=negative_before_shift or f"eff_sub && !{tag}_co")
            magnitude_expr = (f"eff_sub ? ({tag}_neg ? ~{tag}_r : {tag}_inc) : {tag}_r" if negative_before_shift
                              else f"eff_sub ? ({tag}_co ? {tag}_inc : ~{tag}_r) : {tag}_r")
            mag = m.wire(f"{tag}_mag", IW, expr=magnitude_expr)
            last = (X, f"{tag}_yop")
        sign = m.wire(f"{tag}_s", expr=f"{tag}_neg ? c_s : sp")
        return mag, sign, last

    def finish(tag: str, mag: str, sign: str, last, lzf: str, ef: str, offset=None):
        """y_<tag>: the window magnitude (value bits above the sticky lsb)
        normalized to X. `last` is the final adder's operand pair (X and
        Y or ~Y, the sticky lsb included); `offset` is the shift the
        operands took before the add, where `last` is the unshifted pair."""
        m.wire(f"{tag}_v", Wn, expr=f"{mag}[{IW-1}:1]")
        m.wire(f"{tag}_stv", expr=f"{mag}[0]")
        low_carry = None
        if last is not None:
            # the anticipator's operands aligned with the value bits (the sticky lsb dropped) and the carry the
            # dropped lsbs send up: X[0] | Y'[0] on the non-negated difference X - Y = X + ~Y + 1, X[0] & Y'[0] on
            # a sum, and one more than X[0] & Y'[0] on the negated difference Y - X = ~(X + ~Y)
            x0, y0 = f"{last[0]}[0]", f"{last[1]}[0]"
            low_carry = m.wire(f"{tag}_lc", 2, expr=f"{tag}_neg ? (2'd1 + {{1'b0, {x0} & {y0}}}) : "
                                                    f"eff_sub ? {{1'b0, {x0} | {y0}}} : {{1'b0, {x0} & {y0}}}")
            m.wire(f"{tag}_lx", Wn, expr=f"{last[0]}[{IW-1}:1]")
            m.wire(f"{tag}_ly", Wn, expr=f"{last[1]}[{IW-1}:1]")
            last = (f"{tag}_lx", f"{tag}_ly")
        return _to_x_w(m, tag + "x", f"{tag}_v", Wn, ef, EWX, g, lzf, lzc_fam, f"{tag}_stv", last, True, sign, norm=norm,
                       low_carry=low_carry, offset=offset)

    if paths == 1 and not pre_norm:
        mag, sign, last = core("f", "X", "Y", True)
        y = finish("f", mag, sign, last, lz_fam, "ef")
        result, rsign, rmag = y, "f_s", "f_mag"
        if fused_round:
            from .dot_fma_round import post_normalization_dual_sum
            round_lz = "fx_lz"
            if lz_fam == "lza" and lz_fam.pins.get("correction_scheme") == "compensation_in_rounding":
                # The selected LZA may stop one position early. This CPA
                # bank performs the final rounding itself, so it must
                # consume that correction before choosing its P-bit cut.
                round_lz = m.wire("pd_exact_lz", _clog2(Wn)+1,
                                  expr=f"fx_lz + ((|fx_nm) && !fx_nm[{Wn-1}])")
            result = post_normalization_dual_sum(m, dg, Wn, "ef", "f_mag", "f_s", "f_neg",
                "X", "Y", "eff_sub", round_lz, y, topology=str(_pin(cpins, "topology", "kogge_stone")))
    elif paths == 1:
        # normalize before the add: the anticipator on the operands moves the leading one to the top of
        # the window, the add follows, a one-bit correction after it
        m.wire("n_yop", IW, expr="eff_sub ? ~Y : Y")
        m.wire("n_t", IW, expr="X ^ n_yop")
        m.wire("n_g", IW, expr="X & n_yop")
        m.wire("n_z", IW, expr="~X & ~n_yop")
        m.wire("n_f", IW)
        m.raw("  genvar k_n;")
        m.raw(f"  generate for (k_n = 0; k_n < {IW}; k_n = k_n + 1) begin : lza_n")
        m.raw(f"    if (k_n == {IW-1}) begin : top_\n      assign n_f[k_n] = n_t[k_n] & (n_g[k_n] & ~n_z[k_n-1] | n_z[k_n] & ~n_g[k_n-1]) | ~n_t[k_n] & (n_z[k_n] & ~n_z[k_n-1] | n_g[k_n] & ~n_g[k_n-1]);")
        m.raw("    end else if (k_n == 0) begin : bot_\n      assign n_f[k_n] = n_t[k_n+1] & (n_g[k_n] | n_z[k_n]) | ~n_t[k_n+1] & (n_z[k_n] | n_g[k_n]);")
        m.raw("    end else begin : mid_\n      assign n_f[k_n] = n_t[k_n+1] & (n_g[k_n] & ~n_z[k_n-1] | n_z[k_n] & ~n_g[k_n-1]) | ~n_t[k_n+1] & (n_z[k_n] & ~n_z[k_n-1] | n_g[k_n] & ~n_g[k_n-1]);")
        m.raw("    end\n  end endgenerate")
        _lz(m, lzc_fam, {}, "n_f", IW, "n_lzf", "the anticipator's count before the add")
        lw = _clog2(IW)
        m.wire("n_lz", lw, expr=f"(n_f == 0) ? {lw}'d0 : n_lzf[{lw-1}:0]")
        # one short of the prediction (it errs a position either way): the count after the add finishes
        m.wire("n_lzk", lw, expr=f"(n_lz == 0) ? {lw}'d0 : (n_lz > {lw}'d{IW - 1}) ? {lw}'d{IW - 2} : (n_lz - {lw}'d1)")
        _sh(m, norm[0], norm[1], "X", IW, "n_lzk", 0, "Xn", "X normalized before the add")
        _sh(m, norm[0], norm[1], "Y", IW, "n_lzk", 0, "Yn", "Y normalized before the add")
        m.wire("efn", EWX, signed=True, expr=f"ef - $signed({{{{({EWX}-{lw}){{1'b0}}}}, n_lzk}})")
        m.wire("n_negative", expr="eff_sub && (X < Y)")
        mag, sign, last = core("f", "Xn", "Yn", True, "n_negative")
        # the anticipator after the add reads the unshifted operands (the shifted ones wrap when the operands
        # cancel) and takes the shift already made off its count
        y = finish("f", mag, sign, ("X", "n_yop"), lz_fam, "efn", offset=("n_lzk", lw))
        result, rsign, rmag = y, "f_s", "f_mag"
        if fused_round:
            # the dual sum: the window adder split at the rounding position of a normal result whose leading
            # one the pre-normalization put at the top (or one below), the high part from a compound adder
            # (s and s + 1), the round-up decision from the low part; a rare increment when the leading one
            # sits at the top and the guard bit is clear
            k0 = Wn - 1 - M - 1                     # the rounding position for a leading one at bit Wn-2 of the value
            if k0 < 2:
                raise ValueError("the window is too narrow for a fused rounding")
            m.wire("fr_yop", IW, expr="eff_sub ? ~Yn : Yn")
            # the low part (below the split, sticky lsb included) and the compound high part
            LWl = k0 + 1                            # value bits [k0-1:0] and the sticky lsb: IW indices [k0:0]
            m.wire("fr_xl", LWl, expr=f"Xn[{LWl-1}:0]")
            m.wire("fr_yl", LWl, expr=f"fr_yop[{LWl-1}:0]")
            m.wire("fr_sl", LWl)
            m.wire("fr_cl")
            _add(m, cfam, cpins, LWl, "fr_xl", "fr_yl", "fr_sl", "the low part of the fused-rounding adder (X - Y in two's complement on a subtraction)", "eff_sub", "fr_cl")
            HWl = IW - LWl
            m.wire("fr_xh", HWl, expr=f"Xn[{IW-1}:{LWl}]")
            m.wire("fr_yh", HWl, expr=f"fr_yop[{IW-1}:{LWl}]")
            # the compound adder gives S0 = a + b and S1 = S0 + 1 (its flag row is valid with a zero carry-in);
            # the low part's carry and the round-up select among S0, S1 and S2 = S1 + 1 (an incrementer)
            m.wire("fr_s0", HWl)
            m.wire("fr_s1", HWl)
            m.wire("fr_s2", HWl)
            m.wire("fr_c0")
            m.wire("fr_c2")
            if not m.inst("adder", "compound_flagged_prefix", {"topology": str(_pin(cpins, "topology", "kogge_stone"))}, HWl,
                          ".a(fr_xh), .b(fr_yh), .cin(1'b0), .s(fr_s0), .cout(fr_c0), .s1(fr_s1)",
                          "the high part: the sum and the sum plus one from a compound adder"):
                m.assign("{fr_c0, fr_s0}", "{1'b0, fr_xh} + {1'b0, fr_yh}")
                m.assign("fr_s1", "fr_s0 + 1'b1")
            if not m.inst("incr", "prefix_and_incrementer", {}, HWl, ".a(fr_s1), .cin(1'b1), .s(fr_s2), .cout(fr_c2)",
                          "the sum plus two, for a low carry and a round-up together"):
                m.assign("fr_s2", "fr_s1 + 1'b1")
            m.wire("fr_h0", HWl, expr="fr_cl ? fr_s1 : fr_s0")          # the sum with the low part's carry
            m.wire("fr_h1", HWl, expr="fr_cl ? fr_s2 : fr_s1")          # that sum plus one
            m.wire("fr_hc", expr=f"fr_c0 | (fr_cl & (fr_s0 == {{{HWl}{{1'b1}}}}))")
            # a normal-result magnitude in two's complement form (complement_recode) or ones' complement (EAC
            # without the carry back): the fused path serves effective additions and subtractions whose sum
            # is positive (X >= Y); a negative difference leaves unrounded
            # The operand shifts may wrap. Only the original operand
            # ordering, not the high CPA carry, identifies a positive
            # modular difference whose high slices can be used directly.
            m.wire("fr_pos", expr="!f_neg")
            m.wire("fr_top", expr=f"fr_h0[{HWl-1}]")        # the leading one at the window top (else one below)
            # guard and sticky of the two candidate positions: at the top the kept lsb is h0[1], guard h0[0]
            m.wire("fr_stl", expr="|fr_sl")
            m.wire("fr_g_top", expr="fr_h0[0]")
            m.wire("fr_l_top", expr="fr_h0[1]")
            m.wire("fr_st_top", expr="fr_stl")
            m.wire("fr_g_low", expr=f"fr_sl[{LWl-1}]")
            m.wire("fr_l_low", expr="fr_h0[0]")
            m.wire("fr_st_low", expr=f"|fr_sl[{LWl-2}:0]")
            m.wire("fr_g", expr="fr_top ? fr_g_top : fr_g_low")
            m.wire("fr_l", expr="fr_top ? fr_l_top : fr_l_low")
            m.wire("fr_st", expr="fr_top ? fr_st_top : fr_st_low")
            m.wire("fr_inx", expr="fr_g | fr_st")
            # M=0 encodes powers of two. A halfway value chooses the even
            # exponent field, not the (always one) leading significand bit.
            round_lsb = "fr_biased[0]" if fd.exp_only else "fr_l"
            m.wire("fr_up", expr=(f"(rnd == 3'd0) ? (fr_g && (fr_st || {round_lsb})) : (rnd == 3'd1) ? 1'b0 : "
                                  "(rnd == 3'd2) ? (fr_inx && f_s) : (rnd == 3'd3) ? (fr_inx && !f_s) : (rnd == 3'd5) ? fr_inx : 1'b0"))
            # the kept M+1 bits: below the top from (h0 | h1) directly; at the top from the halves shifted
            m.wire("fr_k_low", HWl, expr="fr_up ? fr_h1 : fr_h0")
            m.wire("fr_k_top0", HWl - 1, expr=f"fr_h0[{HWl-1}:1]")
            m.wire("fr_k_top1", HWl - 1, expr=f"fr_h1[{HWl-1}:1]")
            m.wire("fr_k_topi", HWl - 1)
            m.wire("fr_k_topc")
            if not m.inst("incr", "prefix_and_incrementer", {}, HWl - 1, ".a(fr_k_top0), .cin(1'b1), .s(fr_k_topi), .cout(fr_k_topc)",
                          "the rare increment: a round-up at the top position with a clear guard bit"):
                m.assign("fr_k_topi", "fr_k_top0 + 1'b1")
            m.wire("fr_k_top", HWl - 1, expr="!fr_up ? fr_k_top0 : fr_h0[0] ? fr_k_top1 : fr_k_topi")
            # the exponent of the leading one and the normal-range test of the target format
            m.wire("fr_eu", EWX, signed=True, expr=f"efn + {_slit(EWX, Wn - 1)} - (fr_top ? {EWX}'sd0 : {EWX}'sd1)")
            m.wire("fr_biased", EWX, signed=True, expr=f"fr_eu + {_slit(EWX, bias)}")
            m.wire("fr_lead", expr=f"fr_h0[{HWl-1}] | fr_h0[{HWl-2}]")       # the leading one where the pre-normalization put it
            first_code = 0 if fd.exp_only else 1
            last_code = fd._top() if fd.exp_only else (1 << fd.exp_bits)-2
            m.wire("fr_normal", expr=f"fr_pos && fr_lead && (fr_biased >= {first_code}) && (fr_biased <= {_slit(EWX, last_code)}) && (rnd != 3'd4)")
            # the rounded significand (M+1 bits, a carry out of the increment raises the exponent)
            m.wire("fr_kt", HWl, expr="fr_top ? {fr_k_top, 1'b0} : fr_k_low")
            m.wire("fr_carry", expr=f"fr_top ? (fr_up && fr_k_top == {HWl-1}'d0 && (fr_h0[0] ? fr_h1[{HWl-1}:1] == 0 : 1'b1)) : (fr_up && fr_h1 == 0 && fr_h0 == {{{HWl}{{1'b1}}}})")
            # the kept word's leading one sits at its top (the top case, and the low case whose round-up carried
            # into the top bit) or one below (the low case): the X leaves normalized either way, so the mode's
            # rounder packs it without a normalizer
            m.wire("fr_low1", expr=f"!fr_carry && !fr_kt[{HWl-1}]")
            m.wire("fr_sig", XW, expr=f"fr_carry ? ({XW}'d1 << {XW-1}) : fr_low1 ? ({{{{({XW}-{HWl}){{1'b0}}}}, fr_kt}} << {XW - HWl + 1}) : "
                                      f"({{{{({XW}-{HWl}){{1'b0}}}}, fr_kt}} << {XW - HWl})")
            # the kept word's lsb sits at the guard position k0 of the window; a carry out of the top case's
            # increment raises the value by one binade (the low case's carry lands in the word's top bit), and the
            # leading one one below the word's top lowers the exponent of the normalized X by one
            m.wire("fr_e", EWX, signed=True, expr=f"efn + {_slit(EWX, k0 - (XW - HWl))} + ((fr_top && fr_carry) ? {EWX}'sd1 : {EWX}'sd0)"
                                                 f" - (fr_low1 ? {EWX}'sd1 : {EWX}'sd0)")
            m.wire("fr_e_o", EW, signed=True, expr=f"fr_e[{EW-1}:0]")
            m.wire("fr_sp", 2, expr=f"fr_inx ? {ROUNDED} : 2'd0")
            m.wire("fr_y", XT, expr=_mkx(g, "fr_sp", "f_s", "fr_e_o", "fr_sig", "1'b0"))
            m.wire("y_fr", XT, expr=f"fr_normal ? fr_y : {y}")
            result = "y_fr"
    else:
        # the paths: close (a possible massive cancellation: an effective subtraction with the msbs within a
        # bit), far with the addend shifted, far with the product shifted, the close split by the effective
        # operation, and a zero-operand bypass
        m.wire("msb_d", EWX, signed=True, expr=f"(ec + {_slit(EWX, Sc - 1)}) - (ep + {_slit(EWX, 2 * S - 1)})")
        m.wire("close_e", expr="eff_sub && (msb_d <= 1) && (msb_d >= -1)")
        if criterion in ("cancellation_estimate", "both"):
            _lz(m, lzc_fam, {}, "p_al", Wn, "lz_p", "the product's leading position (the cancellation estimate)")
            _lz(m, lzc_fam, {}, "c_al", Wn, "lz_c", "the addend's leading position (the cancellation estimate)")
            m.wire("close_c", expr="eff_sub && ((lz_p > lz_c) ? (lz_p - lz_c <= 1) : (lz_c - lz_p <= 1))")
            close_sub = "close_c" if criterion == "cancellation_estimate" else "close_e && close_c"
        else:
            close_sub = "close_e"
        if paths >= 4:
            # The fourth path handles a near effective addition. The
            # cancellation predicates above deliberately require a
            # subtraction, so using them alone made this path unreachable.
            m.wire("close_add", expr="!eff_sub && (msb_d <= 1) && (msb_d >= -1)")
            m.wire("close", expr=f"({close_sub}) || close_add")
        else:
            m.wire("close", expr=close_sub)
        magc, signc, lastc = core("cl", "X", "Y", True)
        yc = finish("cl", magc, signc, lastc, lz_fam, "ef")
        if paths >= 3:
            magf1, signf1, lastf1 = core("fa", "X", "Y", False)
            yf1 = finish("fa", magf1, signf1, lastf1, "lzc_after_add", "ef")
            magf2, signf2, lastf2 = core("fp", "X", "Y", False)
            yf2 = finish("fp", magf2, signf2, lastf2, "lzc_after_add", "ef")
            m.wire("y_far", XT, expr=f"c_case ? {yf1} : {yf2}")
        else:
            magf, signf, lastf = core("fa", "X", "Y", False)
            yf = finish("fa", magf, signf, lastf, "lzc_after_add", "ef")
            m.wire("y_far", XT, expr=yf)
        if paths >= 4:
            m.wire("ca_yop", IW, expr="Y")
            m.wire("ca_r", IW)
            m.wire("ca_co")
            _add(m, cfam, cpins, IW, "X", "ca_yop", "ca_r", "the close additive path (no anticipator)", "1'b0", "ca_co")
            m.wire("ca_v", Wn, expr=f"ca_r[{IW-1}:1]")
            m.wire("ca_stv", expr="ca_r[0]")
            yca = _to_x_w(m, "ca", "ca_v", Wn, "ef", EWX, g, "lzc_after_add", lzc_fam, "ca_stv", None, True, "sp", norm=norm)
            m.wire("y_close", XT, expr=f"eff_sub ? {yc} : {yca}")
        else:
            m.wire("y_close", XT, expr=yc)
        m.wire("y_sel", XT, expr="close ? y_close : y_far")
        if paths >= 5:
            zero_x = _mkx(g, "2'd0", "1'b0", f"{EW}'sd0", f"{XW}'d0", "1'b0")
            m.wire("p_zero", expr="p == 0")
            m.wire("c_zero", expr="sc == 0 && !c_st")
            # the product alone, normalized like every other result (the tight X is narrower than the product,
            # so nothing places the product in an X field directly)
            ypz = _to_x_w(m, "pz", "p", 2 * S, "ep", EWX, g, "lzc_after_add", lzc_fam, "a_st | b_st", None, True, "sp")
            ycz = _to_x_w(m, "cz", "sc", Sc, "ec", EWX, g, "lzc_after_add", lzc_fam, "c_st", None, True, "c_s")
            m.wire("y_z", XT, expr=f"p_zero ? (c_zero ? {zero_x} : {ycz}) : {ypz}")
            m.wire("y_sel5", XT, expr="(p_zero || c_zero) ? y_z : y_sel")
            result = "y_sel5"
        else:
            result = "y_sel"
        rsign, rmag = "cl_s", "cl_mag"
    if dg.out == "y":
        m.assign("y", result)
    else:
        # the frame value (the window's value bits at the frame's lsb; the sticky is only in y)
        m.wire("acc_v", Wn + 1, signed=True, expr=f"{rsign} ? -$signed({{1'b0, {rmag}[{IW-1}:1]}}) : $signed({{1'b0, {rmag}[{IW-1}:1]}})")
        acc_w = _frame_of_window(m, "o", "acc_v", Wn + 1, "ef", EWX, AW, lo)
        m.assign("acc", acc_w)
    return name, m.render(), {"rnd": fused_round, "rounded": fused_round}


def _bridge_sv(dg: DotGeom, family: str, pins: dict, name: str) -> tuple:
    """(name, text, info): bridge_fma and mixed_precision_cascade_fma from the
    library's fp multiplier and fp adder: the exact product crosses the
    bridge as an X of 2 SW significand bits into an adder generated for
    that width; the cascade rounds the product to d first (the library
    rounder and unpacker), which is the sequential contract."""
    from chialu.targets.rtl.families import fp
    g, AW, lo = dg.g, dg.AW, dg.lo
    expansion = family == "mixed_precision_cascade_fma" and _truthy(pins.get("two_term_expansion_output", False))
    XW, EW, XT, SW = g.XW, g.EW, g.XT, g.SW
    EWX = EW + 3
    if dg.n != 1 or not dg.acc:
        raise ValueError(EXCEPTIONS["classic_fma, reduced_latency_fma, multipath_fma, bridge_fma, mixed_precision_cascade_fma "
                                    "on a mode of several elements under the fused contract"])
    if family == "bridge_fma":
        style = str(_pin(pins, "composition_style", "bridge_reuse"))
        if style == "monolithic_fused":
            return _fma_sv(dg, "classic_fma", pins, name)
        cascade = style == "cascade_mul_then_add"
        prnd = str(_pin(pins, "cascade_product_rounding", "rne"))
    else:
        cascade = not _truthy(_pin(pins, "exact_product_preserved", True))
        prnd = "rne"
    from chialu.verify.formats import FloatFormat
    fd = dg.fd
    if cascade and not (isinstance(fd, FloatFormat) and not getattr(fd, "exp_only", False)):
        raise ValueError("the cascade rounds the product to a float d")
    mul_pins = {"sig_mul.family": str(_pin(pins, "multiplier.family", "behavioral_star")), **{"sig_mul." + k: v for k, v in _sub(pins, "multiplier.").items()}}
    mn, mt = fp.mul_sv(g, "sig_mul_then_round", mul_pins)
    g2 = Geom(XW, EW, 2 * SW, g.sr_bits) if not cascade else g
    add_pins = {"norm.family": "single_barrel"}
    for source, target in (("align.", "align."), ("cpa.", "sig_adder."),
                           ("lza.", "lz."), ("norm_shifter.", "norm.shifter.")):
        for key, value in _sub(pins, source).items():
            add_pins[target + key] = value
    if pins.get("lza.string_form") == "dual_pos_neg_strings":
        add_pins["operand_order"] = "shift_each_operand"
    if pins.get("negation_handling"):
        # the ALU's fp_fma choice: the adder's, which acts on the unswapped datapath (the dual strings) alone
        add_pins["negation_handling"] = str(pins["negation_handling"])
    # the product's significand fills its field while c's is the format's: the adder orders its operands by
    # exponent first, so both are normalized at its entry (the pseudo-normalized representation)
    add_pins["subnormal.internal_representation"] = "pseudo_normalized_wide_exponent"
    # the single-path adder at the bridge's geometry (the two-path adder's far path keeps a narrower window
    # below the larger operand at the widened significand and rounds differently in rare cases)
    an, at = fp.add_sv(g2, "single_path", add_pins)
    notes = []
    if expansion:
        notes.append("the main result and selected operator residuals leave on separate output ports")
    m = Mod(name, f"{family}: the library fp multiplier ({mn}) and fp adder ({an}) composed"
                  + (f"; the product rounded to {fd.name} ({prnd}) before the add, which is the sequential contract"
                     if cascade else f"; the exact {2*SW}-bit product crosses the bridge, one rounding (the fused contract)")
                  + ("; " + "; ".join(notes) if notes else ""))
    m.extra.append(mt)
    m.extra.append(at)
    m.port("input", "xa", XT)
    m.port("input", "xb", XT)
    m.port("input", "xc", XT)
    if cascade or expansion:
        m.port("input", "rnd", 3)
        m.port("input", "word", g.sr_bits)
    if expansion:
        m.port("input", "ftz")
    dg.ports_out(m)
    m.wire("yp", XT)
    m.n += 1
    m.raw(f"  {mn} u{m.n} (.xa(xa), .xb(xb), .y(yp));")
    if cascade:
        rsel = "3'd0" if prnd == "rne" else "3'd1"
        rmag, rw, re_, rs = _round_trip(m, "cp", "yp", fd, g, dg.tokens, rsel, "word", "1'b0", "the product")
        m.wire("yq", XT, expr=f"(cp_rsp != 2'd0) ? {{cp_rsp, cp_rs, cp_re, {XW}'d0, 1'b0}} : "
                              f"{{2'd0, cp_rs, cp_re, {{{{({XW}-{SW}){{1'b0}}}}, cp_rsig}}, 1'b0}}")
        src = "yq"
    else:
        src = "yp"
    m.wire("ysa", XT)
    m.n += 1
    m.raw(f"  {an} u{m.n} (.xa(xc), .xb({src}), .sub(1'b0), .y(ysa));")
    if cascade:
        # a product that overflowed under its rounding is the result (the seed handles c's specials)
        m.wire("ys", XT, expr=f"(cp_rsp == 2'd2) ? {{2'd2, cp_rs, {XW+EW+1}'d0}} : ysa")
    else:
        m.wire("ys", XT, expr="ysa")
    expansion_ports = _expansion_outputs(m, dg, pins, "yp", "ys") if expansion else ()
    if dg.out == "y":
        m.assign("y", "ys")
    else:
        _x_fields(m, "ys", g, "r_")
        m.wire("r_ex", EWX, signed=True, expr=f"$signed({{{{3{{r_e[{EW-1}]}}}}, r_e}})")
        u = _place(m, "ru", "r_sig", XW, "r_ex", EWX, lo, AW, None, {}, "the result into the frame")
        m.wire("acc_u", AW, signed=True, expr=f"r_s ? -$signed({u}) : $signed({u})")
        m.assign("acc", "acc_u")
    flags_out = _rounding_flags(m)
    return name, m.render(), {"rnd": cascade or expansion, "flags": flags_out, "extra_outputs": expansion_ports,
                              "contract": "architecture" if cascade or expansion else "fused"}


# ---- the dispatch --------------------------------------------------------------------
def _fmt_of(name: str):
    from chialu.verify.formats import parse_format
    return parse_format(name)


def internal_formats(family: str, pins: dict) -> tuple:
    """Formats whose intermediate rounded values the engine must represent."""
    formats = []
    if family == "fp8_training_datapath":
        if _truthy(pins.get("chunk_based_accumulation", False)):
            formats.append(_fmt_of(str(pins.get("accumulate_precision", "fp16"))))
        if _truthy(pins.get("unified_internal_format", False)):
            formats.extend((_fmt_of("fp8e4m3"), _fmt_of("fp8e5m2")))
    return tuple(formats)


def validate_unit_binding(spec: dict, mode: dict, family: str, pins: dict) -> None:
    """Check choices implemented by the enclosing unit's ports and packers."""
    from chialu.targets.rtl.families.fidelity import effective, require, unsupported
    from chialu.verify.formats import BlockFormat, FloatFormat
    fab, fc, fd = mode["fab"], mode["fc"], mode["fd"]
    elem = fab.elem if isinstance(fab, BlockFormat) else fab

    def option(pin, name, requested):
        if pin not in pins:
            return
        actual = spec.get(name)
        if isinstance(actual, (list, tuple)):
            require(list(actual) == [requested], pin,
                    f"requires fixed {name}={requested!r}; the unit has {actual!r}")
        else:
            require(actual == requested, pin, f"requires {name}={requested!r}; the unit has {actual!r}")
        effective(pins, pin, pins[pin], f"implemented by the unit's {name}")

    if family == "integer_mac":
        from chialu.verify.formats import IntFormat
        saturating = _truthy(pins.get("saturating_accumulate", False))
        if saturating:
            require(isinstance(fd, IntFormat), "saturating_accumulate", "integer saturation requires an integer/fixed destination")
        if isinstance(fd, IntFormat):
            option("saturating_accumulate", "overflow", "saturate" if saturating else "wrap")
    if family == "bf16_fma_datapath":
        multiword = _truthy(pins.get("multi_word_composition", False))
        if multiword:
            require(isinstance(elem, FloatFormat) and elem.man_bits+1 > 8, "multi_word_composition",
                    "multiword bf16 composition requires an operand significand wider than 8 bits")
        else:
            require(elem.name == "bf16", "format_ab", "the single-word bf16 datapath requires bf16 operands")
        require(fd.name == "fp32" and (not spec.get("accumulate", True) or fc.name == "fp32"),
                "format_d", "the bf16 datapath accumulates in fp32")
        rm = str(pins.get("rounding_mode", "rne"))
        if rm == "round_to_odd":
            require(spec.get("dot_contract") == "architecture", "rounding_mode",
                    "round-to-odd requires the explicit architecture golden contract")
        option("rounding_mode", "rounding", {"rne": "RNE", "rtz": "RTZ", "round_to_odd": "RTZ"}[rm])
        option("flush_subnormals", "daz_in", _truthy(pins.get("flush_subnormals")))
        option("flush_subnormals", "ftz_out", _truthy(pins.get("flush_subnormals")))
        effective(pins, "multi_word_composition", multiword, "exact products composed from 8-bit significand words" if multiword else "one bf16 word per operand")
    if family == "tensor_core_mixed_precision_mac":
        require(isinstance(fd, FloatFormat) and not fd.exp_only, "format_d",
                "tensor PE partial_sum_rounding requires a floating-point destination")
        option("subnormal_support", "daz_in", not _truthy(pins.get("subnormal_support", True)))
    if family == "fp8_training_datapath":
        policy = pins.get("format_policy", "single_e4m3")
        allowed = ({"fp8e4m3", "fp8e5m2"} if policy == "hybrid_forward_e4m3_backward_e5m2" else
                   {"fp8e5m2"} if policy == "single_e5m2" else {"fp8e4m3"})
        require(elem.name in allowed, "format_policy", f"requires operand formats {sorted(allowed)}; got {elem.name}")
        if policy == "hybrid_forward_e4m3_backward_e5m2":
            from chialu.verify.dot_ref import parse_modes
            actual = {m["fab"].elem.name if isinstance(m["fab"], BlockFormat) else m["fab"].name
                      for m in parse_modes(spec["modes"])}
            require(allowed <= actual, "format_policy", "hybrid format policy requires both e4m3 and e5m2 modes")
        effective(pins, "format_policy", policy, f"implemented by operand format {elem.name}")
        precision = str(pins.get("accumulate_precision", "fp16"))
        require(fd.name == precision and (not spec.get("accumulate", True) or fc.name == precision),
                "accumulate_precision", f"requires C and D in {precision}")
        effective(pins, "accumulate_precision", precision, "format of the accumulator and destination")
        if _truthy(pins.get("stochastic_rounding", False)):
            option("stochastic_rounding", "rounding", "SR")
        elif "stochastic_rounding" in pins:
            require("SR" not in spec["rounding"], "stochastic_rounding", "false excludes a stochastic rounding mode")
            effective(pins, "stochastic_rounding", False, "unit excludes stochastic rounding")
        if "per_tensor_scaling" in pins:
            effective(pins, "per_tensor_scaling", isinstance(fab, BlockFormat), "shared scale in the operand format")
    if family == "mixed_precision_cascade_fma" and _truthy(pins.get("two_term_expansion_output", False)):
        require(spec.get("dot_contract") == "architecture", "two_term_expansion_output",
                "the error ports require an explicit architecture contract")
        require(isinstance(fd, FloatFormat), "format_d", "the expansion output requires a floating-point destination")


def dot_active_parameters(family: str, pins: dict) -> dict[str, str]:
    """Inactive own axes and component slots for this architecture choice.

    The full variant product branches on these conditions before expanding
    child domains. Inactive pins are rejected when explicitly supplied.
    """
    off = {}
    if family == "integer_mac" and pins.get("array_style", "systolic_array") != "composable_submultiplier":
        for key in ("scalable_dimensions", "scalability_levels"):
            off[key] = "only composable_submultiplier splits an operand into scalable subproducts"
    if family == "integer_mac":
        if pins.get("array_style", "systolic_array") == "systolic_array":
            off["reduction"] = "systolic MAC cells form a chain using the cpa slot"
        else:
            off["cpa"] = "the selected reduction supplies its own CPA component"
        if _truthy(pins.get("saturating_accumulate", False)):
            off["lza"] = "integer saturation consumes the accumulator word without floating-point normalization"
            off["norm_shifter"] = "integer saturation consumes the accumulator word without floating-point normalization"
    if family == "bridge_fma" and pins.get("composition_style", "bridge_reuse") != "cascade_mul_then_add":
        off["cascade_product_rounding"] = "an exact product crosses the bridge without an intermediate rounding"
    if family == "multi_term_fused_dot":
        if pins.get("rounding_contract", "correctly_rounded") == "correctly_rounded":
            off["guard_bits_per_level"] = ("the correctly-rounded construction takes its width from window_bits "
                                           "rather than a guard per level")
        if pins.get("sign_handling", "post_add_complement") == "dual_reduction_positive_pair_select":
            off["cancellation_handling"] = "positive and negative reductions first meet at the final subtraction"
        if pins.get("normalization_deferral", "per_term") == "per_term":
            off["normalize_before_add"] = "per_term already requests normalization of each product"
    if family == "mixed_precision_cascade_fma" and not _truthy(pins.get("two_term_expansion_output", False)):
        for key in ("error_term_normalization", "error_term_ops"):
            off[key] = "the scalar output has no expansion error term"
    if family == "fp8_training_datapath" and pins.get("format_policy", "single_e4m3") != "hybrid_forward_e4m3_backward_e5m2":
        off["unified_internal_format"] = "a single operand format has no distinct internal representations to unify"
    return off


def dot_family_requirements(family: str, pins: dict) -> dict:
    """Minimum useful dot geometry and unit options for the selected own pins.

    Child widths still need propagation through the generated arithmetic
    geometry. This function never counts an undersized child as exercised.
    """
    from chialu.verify.dot_ref import normalize_dot_spec
    fab, fc, fd, n = "fp4e2m1", "fp4e2m1", "fp4e2m1", 2
    options = {}
    mode_options = {}
    if family in FMA_FAMILIES:
        n = 1
        if family == "bridge_fma" and pins.get("composition_style") == "cascade_mul_then_add":
            options["dot_contract"] = "sequential"
        if family == "mixed_precision_cascade_fma" and not _truthy(pins.get("exact_product_preserved", True)):
            options["dot_contract"] = "sequential"
    elif family == "integer_mac":
        levels = int(pins.get("scalability_levels", 1))
        bits = 2 * (1 << levels) if pins.get("array_style") == "composable_submultiplier" else 2
        fab, fc, fd = f"int{bits}", "int2", "int16"
        if pins.get("array_style") == "composable_submultiplier":
            n = 1
        elif pins.get("accumulation_mode", "sum_apart") == "sum_apart":
            n = 4
        if any(key.startswith("align.") for key in pins):
            significant = bits if pins.get("array_style") == "composable_submultiplier" else 2
            fab, fc, fd = f"fps1e2m{significant-1}", "fp4e2m1", "fp4e2m1"
        elif any(key.startswith(("lza.", "norm_shifter.")) for key in pins):
            fd = "fp4e2m1"
        if _truthy(pins.get("saturating_accumulate", False)):
            fd = "int4"
        options["overflow"] = "saturate" if _truthy(pins.get("saturating_accumulate", False)) else "wrap"
    elif family == "multi_precision_simd_fma":
        lanes, bits = (int(x) for x in str(pins.get("lane_split", "4x16")).split("x"))
        fab = fc = fd = {8: "fp8e4m3", 16: "fp16", 32: "fp32", 64: "fp64"}[bits]
        n = lanes
    elif family in BLOCK_FAMILIES:
        scale = "e8m0" if family == "mx_microscaling_dot" else "fp4e2m1"
        fab, fc, fd, n = f"blks{scale}efp4e2m1s2", "fp4e2m1", "fp4e2m1", 1
    elif family == "tensor_core_mixed_precision_mac":
        n = int(pins.get("dot_width_per_pe", 4))
        options["daz_in"] = [not _truthy(pins.get("subnormal_support", True))]
    elif family == "multi_term_fused_dot" and pins.get("cancellation_handling") == "detect_and_bypass_smallest_operand":
        n = 3
    elif family == "bf16_fma_datapath":
        fab, fc, fd = ("fp32" if _truthy(pins.get("multi_word_composition", False)) else "bf16"), "fp32", "fp32"
        n = {"scalar_fma": 1, "dot2_accumulate": 2, "dot4_accumulate": 4}[pins.get("op_shape", "scalar_fma")]
        rm = pins.get("rounding_mode", "rne")
        options["rounding"] = [{"rne": "RNE", "rtz": "RTZ", "round_to_odd": "RTZ"}[rm]]
        options["daz_in"] = options["ftz_out"] = [_truthy(pins.get("flush_subnormals", False))]
    elif family == "fp8_training_datapath":
        fab = "fp8e5m2" if pins.get("format_policy") == "single_e5m2" else "fp8e4m3"
        fc = fd = str(pins.get("accumulate_precision", "fp16"))
        n = {"scalar_fma": 1, "dot2_accumulate": 2}[pins.get("op_shape", "scalar_fma")]
        options["rounding"] = ["SR" if _truthy(pins.get("stochastic_rounding", False)) else "RNE"]
        if _truthy(pins.get("per_tensor_scaling", False)):
            mode_options["scale_ab"] = "fp8e4m3"
    spec = normalize_dot_spec(dict(unit="vec_dot_acc", dut_name="dot_core", check_en=False,
                                  modes=[dict(elements=n, format_ab=fab, format_c=fc, format_d=fd, **mode_options)], **options))
    architecture = (family == "tensor_core_mixed_precision_mac" or
                    (family == "fp8_training_datapath" and _truthy(pins.get("chunk_based_accumulation", False))) or
                    (family == "bf16_fma_datapath" and pins.get("rounding_mode") == "round_to_odd") or
                    (family == "mixed_precision_cascade_fma" and _truthy(pins.get("two_term_expansion_output", False))) or
                    family == "streaming_accurate_accumulator" or
                    (family == "pairwise_tree" and _truthy(pins.get("per_level_truncation", False))) or
                    (family == "multi_term_fused_dot" and pins.get("rounding_contract", "correctly_rounded") != "correctly_rounded"))
    if architecture:
        spec["dot_contract"] = "architecture"
        spec["dot_architecture"] = {"family": family, "pins": dict(pins)}
    if family == "fp8_training_datapath" and pins.get("format_policy") == "hybrid_forward_e4m3_backward_e5m2":
        other = dict(spec["modes"][0])
        other["format_ab"] = other["format_ab"].replace("efp8e4m3s", "efp8e5m2s") if other["format_ab"].startswith("blks") else "fp8e5m2"
        spec["modes"].append(other)
    if family == "multi_precision_simd_fma" and "shared_rounder" in pins:
        spec["modes"][0]["format_c"] = spec["modes"][0]["format_d"] = "fp4e2m1"
        other = dict(spec["modes"][0], format_c="fp6e3m2", format_d="fp6e3m2")
        spec["modes"].append(other)
    if family == "pairwise_tree" and pins.get("mul.family") == "truncated_fixed_width":
        # Seven significand bits leave at least three omitted columns
        # even at k=4: constant and paired-data correction both act.
        spec["modes"][0].update(format_ab="fps1e2m6", format_c="fp16", format_d="fp16")
        spec["dot_contract"] = "architecture"
        spec["dot_architecture"] = {"family": family, "pins": dict(pins)}
    if pins.get("align.family") == "bounded_align" and family not in ("bf16_fma_datapath", "fp8_training_datapath"):
        from chialu.verify.dot_ref import parse_modes
        from chialu.verify.formats import parse_format
        for mode in spec["modes"]:
            for exponent_bits in range(3, 17):
                candidate = f"fps1e{exponent_bits}m1"
                parsed = parse_modes([dict(mode, format_c=candidate)])[0]
                geometry = geom_of(parsed["fab"], parse_format(candidate), parsed["fd"], parsed["elements"])
                bounded = BandGeom(geometry, int(pins.get("align.bound", 2)))
                if bounded.GNe == bounded.GN and bounded.below_possible and bounded.far_possible:
                    mode["format_c"] = candidate
                    break
            else:
                raise ValueError("no finite test addend format exposes every selected bounded-alignment path")
    return {"spec": spec, "inactive": dot_active_parameters(family, pins),
            "geometry_rule": "all component widths must be checked after deriving the arithmetic geometry"}


def dot_sv(dg: DotGeom, family: str, pins: dict, name: str | None = None, block: bool = False,
           mixed_unit: bool = False) -> tuple:
    """(name, text, info) of a family's module for a geometry; ValueError
    names an incompatible contract or geometry; a requested family never
    selects the seed's behavioral path."""
    from chialu.targets.rtl.families.selection import copy_pins
    pins = copy_pins(pins)
    from chialu.targets.rtl.families.fidelity import effective, inactive
    inactive_choices = {**dot_active_parameters(family, pins), **dot_geometry_inactive_parameters(family, pins, dg)}
    for key_, reason in inactive_choices.items():
        for supplied in pins:
            if supplied == key_ or supplied.startswith(key_ + "."):
                inactive(pins, supplied, reason)
    from chialu.spaces.fma_dot_spaces import UNSUPPORTED_DOT_CHOICES
    for path, exclusion in UNSUPPORTED_DOT_CHOICES.items():
        owner, key_ = path.split(".", 1)
        if owner == family and key_ in pins and ("range" in exclusion or pins[key_] in exclusion["values"]):
            raise ValueError(f"{path}={pins[key_]!r}: {exclusion['reason']}")
    n = dg.n
    if family not in DOT_FAMILIES["core"]:
        raise ValueError(f"{family}: not a dot-accumulate family")
    if (family in ("streaming_accurate_accumulator", "multi_term_fused_dot", "fused_two_term_dot") or
            (family == "pairwise_tree" and _truthy(pins.get("per_level_truncation", False)))):
        # The decoded-X path realizes the selected alignment and window
        # network even for integer inputs. The raw-integer shortcut has
        # no dynamic normalization or per-level window construction.
        dg.intg = None
    if dg.intg:
        # a unit that also serves a float mode declares these pins for that mode's alignment and
        # normalization (the core family is one choice for every mode); the raw-integer mode has neither,
        # so they do not apply to it. A unit of integer modes alone declared them for nothing: an error.
        floating = [k for k in pins if k.startswith("align.") or (dg.out == "acc" and k.startswith(("lza.", "norm_shifter.")))]
        if floating and mixed_unit:
            pins = {k: v for k, v in pins.items() if k not in floating}
        elif any(key.startswith("align.") for key in pins):
            raise ValueError("raw integer/fixed operands use constant frame positions; a declared variable alignment needs decoded-X operands")
        elif dg.out == "acc" and any(key.startswith(("lza.", "norm_shifter.")) for key in pins):
            raise ValueError("a raw integer accumulator result has no final normalization; use a normalized destination for these pins")
    tagp = "_".join(f"{k.replace('.', '_')}{v}" for k, v in sorted(pins.items())
                    if not str(k).endswith(".family") and k.count(".") == 0 and not isinstance(v, (dict, list)))[:60]
    import hashlib
    key = hashlib.blake2b(repr(sorted((str(k), str(v)) for k, v in pins.items())).encode(), digest_size=6).hexdigest()
    name = name or f"fam_dot_{family}_{dg.tag()}_{key}"
    if family in ("classic_fma", "reduced_latency_fma", "multipath_fma"):
        if dg.intg:
            raise ValueError(f"{family}: an FMA datapath aligns floating-point significands; the integer mode keeps its behavioral MAC")
        return _fma_sv(dg, family, pins, name)
    if family in ("bridge_fma", "mixed_precision_cascade_fma"):
        if dg.intg:
            raise ValueError(f"{family}: an FMA datapath aligns floating-point significands; the integer mode keeps its behavioral MAC")
        return _bridge_sv(dg, family, pins, name)
    cfg: dict = {"comment": "", "notes": []}
    mul_key = "multiplier" if family in ("multi_precision_simd_fma", "fused_two_term_dot", "multi_term_fused_dot") else "mul"
    cfg["mul"] = (str(_pin(pins, f"{mul_key}.family", "behavioral_star")), _sub(pins, f"{mul_key}."))
    cfg["shifter"] = ((pins.get("align.shifter.family") or None), _sub(pins, "align.shifter."))
    lzc_fam_ = pins.get("lza.counter.family") or pins.get("lza.encoder.family") or None
    lzc_pins_ = _sub(pins, "lza.counter.") if pins.get("lza.counter.family") else _sub(pins, "lza.encoder.")
    lzc_pins_ = {k: v for k, v in lzc_pins_.items() if k != "family"}
    cfg["lz"] = (_LeadingZeroChoice(pins),
                 (lzc_fam_, lzc_pins_) if lzc_fam_ else None)
    cfg["norm"] = ((pins.get("norm_shifter.family") or None), _sub(pins, "norm_shifter."))
    cfg["round_pins"] = {k: v for k, v in pins.items() if k.startswith("round.")}
    align_fam = str(_pin(pins, "align.family", "full_align"))
    cfg["bound"] = int(_pin(pins, "align.bound", 2) or 2)
    cfg["sticky_method"] = str(_pin(pins, "align.sticky_method", "precomputed_mask"))
    cfg["tzc"] = ((pins.get("align.tzc.family") or None), _sub(pins, "align.tzc."))
    if family == "pairwise_tree":
        cfg["tree"] = _tree_of(pins, "accum")
        cfg["comment"] = "per-element products, then a reduction tree"
        if _truthy(_pin(pins, "per_level_truncation", False)):
            cfg["align"] = "per_level"
            cfg["window"] = 2 * dg.S + max(dg.Sc, 0) + 4 + _clog2(n + 1)
            cfg["comment"] += ", each level truncated to the node window"
        elif dg.intg is None:
            cfg["align"] = "frame"
    elif family == "fused_csa":
        comp = str(_pin(pins, "compressor", "3:2"))
        cfam, cpins = _cpa_of(pins, "final_cpa")
        cfg["tree"] = ("csa_tree", comp, cfam, cpins)
        cfg["flatten"] = True
        cfg["comment"] = f"every partial product of every product and c into one carry-save reduction ({comp}), the final CPA {cfam}"
    elif family == "integer_mac":
        style = str(_pin(pins, "array_style", "systolic_array"))
        tree = _tree_of(pins, "reduction")
        if style == "systolic_array":
            tree = ("linear_chain", "3:2") + _cpa_of(pins, "cpa")
            cfg["comment"] = "a chain of multiply-accumulate cells"
        elif style == "simd_packed_dot":
            cfg["comment"] = "the packed products in parallel, using the selected reduction"
        else:
            levels = int(_pin(pins, "scalability_levels", 1) or 1)
            dimensions = str(_pin(pins, "scalable_dimensions", "one"))
            cfg["composable"] = (levels, str(_pin(pins, "accumulation_mode", "sum_apart")) == "sum_apart", dimensions)
            cfg["comment"] = f"each product from {(4 if dimensions == 'two' else 2) ** levels} composable sub-multipliers"
        cfg["tree"] = tree
        effective(pins, "array_style", style, "multiply/accumulate organization")
        if style == "composable_submultiplier":
            effective(pins, "scalability_levels", levels, "operand splitting depth")
            effective(pins, "scalable_dimensions", dimensions, "one or both operands are split")
        cfg["apart"] = str(_pin(pins, "accumulation_mode", "sum_apart")) == "sum_apart" and style != "composable_submultiplier"
        if n < 4 and cfg["apart"]:
            raise ValueError("integer_mac accumulation_mode=sum_apart requires at least four products so both separate groups contain an actual addition")
        effective(pins, "accumulation_mode", str(_pin(pins, "accumulation_mode", "sum_apart")), "separate or joint reductions")
        wacc = int(_pin(pins, "accumulator_width_bits", 16) or 16)
        cfg["declared_acc_width"] = wacc
        if _truthy(_pin(pins, "saturating_accumulate", False)):
            cfg["notes"].append("the saturation is the unit's overflow option, applied by the seed")
        if dg.intg is None:
            cfg["align"] = "frame"
            cfg["notes"].append("an integer MAC organization over the floating-point products aligned into the frame")
    elif family == "multi_precision_simd_fma":
        cfg["tree"] = ("linear_chain", "3:2") + _cpa_of(pins, "cpa")
        # At a fixed lane split every lane uses its selected multiplier.
        # Substituting a hard-coded gated array here would discard the
        # entire multiplier component family and its recursive pins.
        cfg["lane_split"] = str(_pin(pins, "lane_split", "4x16"))
        lanes, bits = (int(x) for x in cfg["lane_split"].split("x"))
        actual_bits = getattr(getattr(dg, "fab", None), "width", dg.intg[0] if dg.intg else None)
        if n != lanes or actual_bits != bits:
            raise ValueError(f"{family}: lane_split={cfg['lane_split']} requires {lanes} operands of {bits} bits; "
                             f"this geometry has {n} operands of {actual_bits} bits")
        effective(pins, "lane_split", f"{n}x{actual_bits}", "actual lane count and operand widths")
        cfg["align"] = "frame"
        cfg["comment"] = f"{n} packed product lanes using the selected multiplier, one accumulate"
        if _truthy(_pin(pins, "shared_rounder", True)):
            cfg["notes"].append("the shared rounder is the seed's single rounding of the group")
    elif family == "fused_two_term_dot":
        if n != 2:
            raise ValueError(f"fused_two_term_dot sums two products; the mode has {n}")
        cfg["tree"] = ("linear_chain", "3:2") + _cpa_of(pins, "cpa")
        cfg["align"] = "per_level" if _truthy(_pin(pins, "dual_path_add", False)) else "max"
        cfg["comment"] = "a*b + c*d (+ c) aligned to the largest exponent, one normalize"
    elif family == "multi_term_fused_dot":
        strat = str(_pin(pins, "alignment_strategy", "per_level"))
        cfg["align"] = {"per_level": "per_level", "single_wide_window": "frame", "two_stage_coarse_fine": "two_stage",
                        "max_exponent_tree": "max", "pairwise_difference_reuse": "pairwise_diff",
                        "exponent_sorted_realignment_lines": "sorted"}.get(strat, "frame")
        cfg["tree"] = _tree_of(pins, "reduction")
        cfg["sign"] = "dual" if str(_pin(pins, "sign_handling", "post_add_complement")) == "dual_reduction_positive_pair_select" else "twos"
        cfg["bypass_min"] = str(_pin(pins, "cancellation_handling", "none")) == "detect_and_bypass_smallest_operand"
        if cfg["bypass_min"] and n < 3:
            raise ValueError("detect_and_bypass_smallest_operand requires at least three products: two possible cancelling terms and a bypassed smallest term")
        if cfg["bypass_min"] and cfg["sign"] == "dual":
            cfg["notes"].append("the cancellation bypass applies to the two's complement reduction; the dual reduction keeps "
                                "positive and negative sums apart, where a cancellation only meets at the final subtraction")
        cfg["pre_norm"] = _truthy(_pin(pins, "normalize_before_add", False)) or str(_pin(pins, "normalization_deferral", "per_term")) == "per_term"
        contract = str(_pin(pins, "rounding_contract", "correctly_rounded"))
        guard = int(_pin(pins, "guard_bits_per_level", 0) or 0)
        named_window = int(_pin(pins, "window_bits", 0) or 0)
        if contract != "correctly_rounded":
            cfg["keep_sticky"] = contract == "faithful"
            cfg["window"] = named_window or max(2 * dg.S, dg.Sc) + guard + _clog2(n + 1) + 2
            cfg["contract"] = (f"the {contract} contract: a window of {cfg['window']} bits ({guard} guard bits per level), "
                               f"the bits below it truncated" + (" with a sticky" if contract == "faithful" else ""))
        elif named_window:
            # A correctly-rounded reduction does not need the exact frame: a window
            # anchored at the largest exponent, with everything below it reaching the
            # rounding through a sticky, delivers the same single rounding once the
            # width carries the geometry. The width is the declaration's to choose and
            # the conformance gate is what says whether it was wide enough.
            cfg["keep_sticky"] = True
            cfg["window"] = named_window
            cfg["fused_window"] = True
            cfg["contract"] = (f"the fused contract out of a {named_window}-bit window: the bits below it "
                               f"reach the rounding through a sticky")
        if cfg.get("window") is not None:
            if cfg["align"] == "frame":
                cfg["align"] = "max"
            elif cfg["align"] == "two_stage":
                cfg["window_two_stage"] = True
                cfg["align"] = "max"
        cfg["comment"] = f"{n} unrounded products aligned by {strat}, sign handling {cfg['sign']}, one normalize"
    elif family == "kulisch_long_accumulator":
        org = str(_pin(pins, "organization", "monolithic"))
        carry = str(_pin(pins, "carry_resolution", "immediate"))
        width = int(_pin(pins, "accumulator_width_bits", 512) or 512)
        cfg["tree"] = ("linear_chain", "3:2") + _cpa_of(pins, "cpa")
        if org == "monolithic" and carry == "carry_save_deferred":
            cfg["tree"] = ("csa_tree", "3:2") + cfg["tree"][2:]
        cfg["align"] = "frame"
        if org != "monolithic":
            B = 16 if org == "two_speed" else 32
            cfg["segments"] = {"org": org, "B": B, "carry": carry, "width": width}
        elif carry == "periodic_sweep":
            cfg["segments"] = {"org": org, "B": 32, "carry": carry, "width": width}
        cfg["comment"] = ("the long fixed-point word ({acc_w} bits, " + f"{org}, carries {carry}) of one "
                          "operation: the products and c shifted to their weights and added")
        cfg["comment_acc_w"] = width
        cfg["declared_acc_width"] = width
        cfg["notes"].append("the accumulator across operations is the register the unit has no state for; this is its one-operation form")
    elif family == "streaming_accurate_accumulator":
        approach = str(_pin(pins, "approach", "shifted_fixed_point_window"))
        wb = int(_pin(pins, "window_bits", 33) or 33)
        cfg["tree"] = ("linear_chain", "3:2") + _cpa_of(pins, "cpa")
        if approach == "shifted_fixed_point_window":
            cfg["align"] = "per_level"
            cfg["window"] = wb
            cfg["comment"] = f"a linear fold with a {wb}-bit fixed-point window at each partial sum"
        else:
            cfg["align"] = "per_level"
            cfg["window"] = wb
            cfg["tree"] = ("binary_tree",) + cfg["tree"][1:]
            cfg["comment"] = f"a tree reduction over {wb}-bit windows, the dropped bits refined into the sticky"
        cfg["loop_norm"] = _truthy(_pin(pins, "in_loop_normalization", False))
        effective(pins, "in_loop_normalization", cfg["loop_norm"], "normalize exact partials inside the reduction")
        cfg["notes"].append("the accumulator across operations is the register the unit has no state for; this is its one-operation form")
    elif family in BLOCK_FAMILIES:
        if not block:
            raise ValueError(EXCEPTIONS["block_fp_accumulation, mx_microscaling_dot on a scalar mode"])
        cfg["tree"] = _tree_of(pins, "reduction")
        cfg["align"] = "frame"
        cfg["comment"] = "the block's mantissa products under the shared scale (folded in by the unpack) into the wide fixed-point sum"
        acc_prec = str(_pin(pins, "inter_block_accumulate", _pin(pins, "accumulate_precision", "fp32")))
        cfg["notes"].append(f"the inter-block accumulate ({acc_prec}) rounds between blocks; one operation has one block and the seed's single rounding")
    elif family == "tensor_core_mixed_precision_mac":
        D = int(_pin(pins, "dot_width_per_pe", 4) or 4)
        if n < D:
            raise ValueError(f"{family}: dot_width_per_pe={D} requires at least {D} products; this mode has {n}")
        prnd = str(_pin(pins, "partial_sum_rounding", "rne"))
        target = str(_pin(pins, "alignment_target", "largest_exponent"))
        cfg["tree"] = _tree_of(pins, "reduction")
        from chialu.verify.formats import FloatFormat
        if isinstance(dg.fd, FloatFormat) and not getattr(dg.fd, "exp_only", False):
            # Integer operands can still use a floating-point partial-sum
            # format. Route their decoded magnitudes through the X path.
            dg.intg = None
            cfg["align"] = "max"
            cfg["pe"] = (D, prnd, target)
            cfg["contract"] = (f"the partial sum of each PE rounded ({prnd}) to {dg.fd.name} before the accumulate: not the fused "
                               f"contract's single rounding" + ("; with one product per PE and pairwise alignment it is the sequential contract"
                                                                if target == "pairwise_sequential" else ""))
            cfg["comment"] = f"PEs of {D} products aligned to {target}, the partial sums rounded {prnd}"
        else:
            raise ValueError(f"{family}: partial_sum_rounding requires a floating-point destination")
        if not _truthy(_pin(pins, "subnormal_support", True)):
            cfg["notes"].append("subnormal_support false describes flushed inputs, which is the unit's daz option")
    elif family == "bf16_fma_datapath":
        shape = str(_pin(pins, "op_shape", "scalar_fma"))
        cfg["tree"] = ("linear_chain", "3:2") + _cpa_of(pins, "cpa")
        cfg["align"] = "frame"
        cfg["comment"] = f"exact narrow products into the accumulate ({shape})"
        want = {"scalar_fma": 1, "dot2_accumulate": 2, "dot4_accumulate": 4}.get(shape, n)
        if want != n:
            raise ValueError(f"{family}: op_shape={shape} requires {want} products; this mode has {n}")
        effective(pins, "op_shape", shape, f"{n} products in the datapath")
        rm = str(_pin(pins, "rounding_mode", "rne"))
        cfg["notes"].append(f"the datapath's rounding_mode {rm} is applied by the seed's rounding under the run's mode")
        if _truthy(_pin(pins, "flush_subnormals", False)):
            cfg["notes"].append("flush_subnormals describes the unit's daz/ftz options")
        if _truthy(_pin(pins, "multi_word_composition", False)):
            cfg["multiword"] = True
            cfg["comment"] += ", wider significands composed from exact bf16 word products"
    elif family == "fp8_training_datapath":
        shape = str(_pin(pins, "op_shape", "scalar_fma"))
        cfg["tree"] = ("linear_chain", "3:2") + _cpa_of(pins, "cpa")
        cfg["align"] = "frame"
        prec = str(_pin(pins, "accumulate_precision", "fp16"))
        cfg["comment"] = f"exact fp8 products ({shape}) into the accumulate"
        if _truthy(_pin(pins, "chunk_based_accumulation", False)) and dg.intg is None:
            cfg["chunks"] = (4, _fmt_of(prec))
            cfg["contract"] = f"chunks of 4 products summed and rounded to {prec} before the accumulate: not the fused contract's single rounding"
            cfg["comment"] += f", in chunks rounded to {prec}"
        want = {"scalar_fma": 1, "dot2_accumulate": 2}.get(shape, n)
        if want != n:
            raise ValueError(f"{family}: op_shape={shape} requires {want} products; this mode has {n}")
        effective(pins, "op_shape", shape, f"{n} products in the datapath")
        cfg["notes"].append("format_policy and per_tensor_scaling describe the modes and scaling of the unit; unified_internal_format is the X format")
        if _truthy(_pin(pins, "stochastic_rounding", False)):
            cfg["notes"].append("stochastic rounding is the run's SR rounding mode")
    if cfg.get("mul", (None,))[0] == "truncated_fixed_width":
        cfg["approximate_product"] = True
        cfg["contract"] = "the selected truncated product-word algorithm followed by " + (
            f"a {cfg['window']}-bit reduction window and final rounding" if cfg.get("window") is not None else
            "an exact reduction and final rounding")
    if dg.intg is not None and family not in ("fused_csa",):
        return _acc_int_sv(dg, family, pins, cfg, name)
    if dg.intg is not None:
        return _acc_int_sv(dg, family, pins, cfg, name)
    cfg.setdefault("align", "frame")
    if align_fam == "bounded_align":
        if cfg["align"] == "frame" and dg.acc and dg.out == "y" and not cfg.get("chunks") and not cfg.get("pe"):
            cfg["align"] = "band"
        else:
            raise ValueError("bounded_align requires a full-frame floating-point accumulate with an addend; "
                             + ("this mode has no addend" if not dg.acc else
                                "this mode returns an integer frame" if dg.out != "y" else
                                "this architecture rounds partial sums" if cfg.get("chunks") or cfg.get("pe") else
                                "this architecture aligns per window or per level"))
    return _acc_x_sv(dg, family, pins, cfg, name)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="emit a dot-accumulate family module for a mode geometry")
    ap.add_argument("--fab", default="fp16")
    ap.add_argument("--fc", default="fp32")
    ap.add_argument("--fd", default="fp32")
    ap.add_argument("--n", type=int, default=4)
    ap.add_argument("--no-c", action="store_true")
    ap.add_argument("--family", default="pairwise_tree")
    ap.add_argument("--pins", default="", help="k=v,k=v")
    args = ap.parse_args(argv)
    pins = {}
    for kv in [x for x in args.pins.split(",") if x]:
        k, v = kv.split("=", 1)
        pins[k] = int(v) if k == "path_count" else v
    fab, fc, fd = _fmt_of(args.fab), _fmt_of(args.fc), _fmt_of(args.fd)
    from chialu.verify.formats import BlockFormat
    dg = geom_of(fab, fc, fd, args.n, not args.no_c)
    name, text, info = dot_sv(dg, args.family, pins, block=isinstance(fab, BlockFormat))
    print(text)
    return 0


from chialu.targets.rtl.families.selection import track_factory

dot_sv = track_factory(dot_sv)


if __name__ == "__main__":
    raise SystemExit(main())
