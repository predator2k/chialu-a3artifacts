"""The posit unit families (dsp_posit_spaces: posit_unit_space) as
generated SystemVerilog on the engine's V/X formats.

posit_adder_multiplier
    The decoder (pattern -> V, the shape of the float unpacker: `.b`,
    `.daz`, `.u` = {den, V}) and the encoder (X -> pattern and flags, the
    shape of the float rounder: `.x`, `.rnd`, `.word`, `.ftz`, `.fl`,
    `.bits`) of a posit format, bit-exact with the engine's unpack_posit
    and pack_posit. Pins:
      regime_decode           lzc_plus_shifter: the regime run from a library
                              leading-zero counter over the body xored with
                              its first bit, then a library shifter that
                              exposes the exponent and fraction fields;
                              two_stage_masked_decode: a prefix-or thermometer
                              of the run, its one-hot terminator, the run
                              length as an or of constants and the fields as
                              an and-or matrix keyed by the one-hot (no counter,
                              no shifter)
      internal_representation sign_magnitude: the pattern negated first (an
                              incrementer over the inverted pattern), the
                              magnitude decoded, the sign carried separately;
                              the encoder rounds the magnitude and negates the
                              pattern last. twos_complement: the raw two's
                              complement pattern decoded without a negation
                              stage (the scale of a negative posit is the
                              bitwise complement of the raw scale, the
                              significand the two's complement {s, ~s, f}),
                              the significand negated narrow into X at the
                              end; the encoder negates the field word first
                              (with the sticky's borrow), builds the regime of
                              the complemented scale and rounds in the two's
                              complement domain, so no final negation exists
      es_bits                 the format's es; a pin that differs from the mode's
                              format is noted in the module header
      operator_set            add_mul: the unit's X adder and multiplier;
                              add_mul_div: also its divider and square root
                              (fp.div_sv / fp.sqrt_sv under the sig_div slot)
      approximation           logarithmic_fraction (PLAM): the fraction multiply
                              as a Mitchell add of the fractions (plam_sv), used
                              by the seed only under `accuracy: approximate`;
                              an exact contract keeps the exact multiplier
    The X adder of the unit is fp.add_sv (single_path) with the sig_datapath
    slot's adder as its significand adder.

posit_ieee_interop
    boundary_converters: a dedicated converter module per direction
    (cvt_sv: the posit lane's decoded value into a float target through
    the float rounder datapath, into a posit target through the posit
    encoder; a float lane's decoded value into a posit target through the
    posit encoder), one per lane and target;
    unified_dual_format_datapath and isa_posit_replaces_float: the decoder
    and encoder modules alone, the conversions through the lane's shared X
    datapath and pack functions (the ISA style presumes a mode set without
    float modes; the module header says whether the unit's has any).
"""
from __future__ import annotations

from chialu.targets.rtl.engine import FW, flag_bit
from chialu.targets.rtl.families.fp import (Geom, Mod, _clog2, _lzc, _pin,
                                            _shift, _x_fields)
from chialu.verify.formats import FloatFormat, PositFormat, X87Format

POSIT_FAMILIES = {"posit_unit": ("posit_adder_multiplier", "posit_ieee_interop")}


def _slots(pins: dict) -> tuple:
    """((lzc family, pins), (shifter family, pins)) of the unit's `lzc` and
    `shifter` slots: the regime run's leading-zero count and the decoder's,
    encoder's and PLAM's shifts."""
    pins = pins or {}
    return ((str(_pin(pins, "lzc.family", "lzd_cell_tree")), {k[4:]: v for k, v in pins.items() if k.startswith("lzc.") and k != "lzc.family"}),
            (str(_pin(pins, "shifter.family", "barrel_mux_tree")), {k[8:]: v for k, v in pins.items() if k.startswith("shifter.") and k != "shifter.family"}))


def _ptag(pins: dict) -> str:
    """A 48-bit tag of the pins for a module name (empty without pins)."""
    if not pins:
        return ""
    import hashlib
    return "_" + hashlib.blake2b(repr(sorted((str(k), str(v)) for k, v in pins.items())).encode(), digest_size=6).hexdigest()


def _fmt_tag(fmt) -> str:
    return fmt.name.replace(".", "_")


def _check_family(family: str):
    if family not in POSIT_FAMILIES["posit_unit"]:
        raise ValueError(f"{family}: not a posit unit family")


def _incr(m: Mod, out: str, a_expr: str, cin: str, width: int, comment: str, cout: str | None = None):
    """out = a + cin through the library incrementer (a behavioral add
    without one); cout names the carry-out wire when wanted."""
    m.wire(out, width)
    if cout:
        m.wire(cout)
    conns = f".a({a_expr}), .cin({cin}), .s({out}), .cout({cout or ''})"
    if not m.inst("incr", "prefix_and_incrementer", {}, width, conns, comment):
        if cout:
            m.raw(f"  assign {{{cout}, {out}}} = {{1'b0, {a_expr}}} + {cin};")
        else:
            m.assign(out, f"{a_expr} + {cin}")


def _pins_note(fmt: PositFormat, pins: dict, family: str = "posit_adder_multiplier") -> str:
    """The note of the pins the seed realizes around this module (the
    adder/multiplier family's alone: the interop family has no operator
    set of its own)."""
    notes = []
    if family != "posit_adder_multiplier":
        return ""
    op_set = pins.get("operator_set")
    if op_set:
        notes.append(f"operator_set {op_set}")
    ap = pins.get("approximation")
    if ap and ap != "none":
        notes.append(f"approximation {ap}: the fraction multiply uses the selected PLAM module; the target budget is checked separately")
    return ("; " + "; ".join(notes)) if notes else ""


# ---- the decoder -----------------------------------------------------------------
def decode_sv(fmt: PositFormat, g: Geom, family: str, pins: dict, name: str | None = None) -> tuple:
    """(name, text): posit pattern -> {den (0), V}."""
    pins = pins or {}
    _check_family(family)
    n, es = fmt.width, fmt.es
    LZ, SH = _slots(pins)
    regime = str(_pin(pins, "regime_decode", "lzc_plus_shifter"))
    rep = str(_pin(pins, "internal_representation", "sign_magnitude"))
    if regime not in ("lzc_plus_shifter", "two_stage_masked_decode"):
        raise ValueError(f"regime_decode {regime!r}")
    if rep not in ("sign_magnitude", "twos_complement"):
        raise ValueError(f"internal_representation {rep!r}")
    SW, EW, VW = g.SW, g.EW, g.VW
    if SW < n:
        raise ValueError(f"the geometry's significand ({SW} bits) is narrower than the posit ({n})")
    BW = n - 1                      # the body: regime, exponent and fraction
    FB = BW - es                    # the widest fraction
    RUNW = BW.bit_length()          # the run length 0..BW
    KW = RUNW + 1                   # k signed
    SCW = KW + es                   # the scale k * 2^es + e, signed
    tag = _fmt_tag(fmt)
    name = name or f"fam_posit_decode_{family}_{regime}_{rep}_{tag}_{g.tag()}{_ptag(pins)}"
    m = Mod(name, f"posit decoder ({family}): {fmt.name} pattern -> V; regime by {regime}, internal representation "
                  f"{rep}{_pins_note(fmt, pins, family)}; daz has no effect (posits have no subnormals)")
    m.port("input", "b", n)
    m.port("input", "daz")
    m.port("output", "u", VW + 1)
    m.wire("s", expr=f"b[{n-1}]")
    m.wire("zero", expr=f"b == {n}'d0")
    m.wire("nar", expr=f"b == {{1'b1, {{{n-1}{{1'b0}}}}}}")
    if rep == "sign_magnitude":
        m.wire("bx", n, expr=f"b ^ {{{n}{{s}}}}")
        _incr(m, "mag", "bx", "s", n, "the magnitude: a negative pattern two's-complemented (the sign carried separately)")
        m.wire("body", BW, expr=f"mag[{BW-1}:0]")
    else:
        m.wire("body", BW, expr=f"b[{BW-1}:0]")
    m.wire("first", expr=f"body[{BW-1}]")
    m.wire("t", BW, expr=f"body ^ {{{BW}{{first}}}}")
    m.wire("run", RUNW)
    m.wire("rest", BW)
    if regime == "lzc_plus_shifter":
        _lzc(m, LZ[0], LZ[1], "t", BW, "lz", "the regime run: the leading zeros of the body xored with its first bit")
        m.assign("run", f"lz[{RUNW-1}:0]")
        AW = _clog2(BW)
        m.wire("sha", AW, expr=f"run[{AW-1}:0] + {AW}'d1")
        _shift(m, SH[0], SH[1], "body", BW, "sha", 0, "rest0", "the body shifted past the run and its terminator")
        m.assign("rest", f"(({{1'b0, run}} + {RUNW+1}'d1) >= {RUNW+1}'d{BW}) ? {BW}'d0 : rest0")
    else:
        m.raw("  // stage 1: the thermometer of the run (a prefix or of the xored body) and its one-hot terminator")
        prev = "t"
        step = 1
        while step < BW:
            m.wire(f"por{step}", BW, expr=f"{prev} | ({prev} >> {step})")
            prev = f"por{step}"
            step *= 2
        m.wire("seen", BW, expr=prev)
        m.wire("term", BW, expr=f"seen & ~{{1'b0, seen[{BW-1}:1]}}")
        m.wire("none", expr="!seen[0]")
        m.assign("run", f"none ? {RUNW}'d{BW} : (" + " | ".join(f"({{{RUNW}{{term[{i}]}}}} & {RUNW}'d{BW-1-i})" for i in range(BW - 1)) + ")")
        m.raw("  // stage 2: the fields below the terminator selected by the one-hot (an and-or matrix, no shifter)")
        terms = [f"({{{BW}{{term[{i}]}}}} & (body << {BW-i}))" for i in range(1, BW)]
        m.assign("rest", " | ".join(terms) if terms else f"{BW}'d0")
    if es:
        m.wire("ef", es, expr=f"rest[{BW-1}:{BW-es}]")
    m.wire("fw", BW, expr=(f"{{rest[{FB-1}:0], {{{es}{{1'b0}}}}}}" if es and FB else (f"rest[{FB-1}:0]" if FB else f"{BW}'d0")))
    m.wire("k", KW, signed=True, expr=f"first ? ($signed({{1'b0, run}}) - {KW}'sd1) : -$signed({{1'b0, run}})")
    if es:
        m.wire("sc", SCW, signed=True, expr=f"($signed({{{{{es}{{k[{KW-1}]}}}}, k}}) <<< {es}) + $signed({{{{{SCW-es}{{1'b0}}}}, ef}})")
    else:
        m.wire("sc", SCW, signed=True, expr="k")
    m.wire("sig_n", n)
    m.wire("ex", EW, signed=True)
    if rep == "sign_magnitude":
        m.assign("sig_n", "{1'b1, fw}")
        m.assign("ex", f"$signed({{{{{EW-SCW}{{sc[{SCW-1}]}}}}, sc}}) - {EW}'sd{n-1}")
    else:
        m.raw("  // a negative pattern's scale is the complement of the raw scale; its significand {1, 0, f} negated narrow")
        m.wire("scx", SCW, signed=True, expr=f"sc ^ {{{SCW}{{s}}}}")
        m.wire("fz", expr=f"fw == {BW}'d0")
        _incr(m, "negw", "~{1'b0, fw}", "1'b1", n, "the two's complement significand converted to a magnitude")
        m.assign("sig_n", f"s ? (fz ? {{1'b1, {{{BW}{{1'b0}}}}}} : negw) : {{1'b1, fw}}")
        m.assign("ex", f"$signed({{{{{EW-SCW}{{scx[{SCW-1}]}}}}, scx}}) - {EW}'sd{n-1} + $signed({{{{{EW-1}{{1'b0}}}}, (s & fz)}})")
    m.wire("sig", SW, expr=(f"{{{{{SW-n}{{1'b0}}}}, sig_n}}" if SW > n else "sig_n"))
    m.wire("v_zero", VW, expr=f"{{2'd0, 1'b0, {EW}'sd0, {SW}'d0}}")
    m.wire("v_nar", VW, expr=f"{{2'd1, 1'b0, {EW}'sd0, {SW}'d0}}")
    m.wire("v_fin", VW, expr="{2'd0, s, ex, sig}")
    m.assign("u", "zero ? {1'b0, v_zero} : nar ? {1'b0, v_nar} : {1'b0, v_fin}")
    return name, m.render()


# ---- the encoder -----------------------------------------------------------------
def encode_sv(fmt: PositFormat, g: Geom, family: str, pins: dict, tokens: dict | None = None,
              name: str | None = None) -> tuple:
    """(name, text): X -> {flags, posit pattern}, the engine's pack_posit as
    a datapath: the normalizer (leading-zero counter and shifter), the
    regime and exponent split of the scale, the regime word, the fields
    shifted below it, nearest-even rounding on the guard and sticky, the
    increment and the clamps to maxpos and minpos. Directed modes follow
    the frozen Python pattern rules. Other modes use nearest even.
    The word and ftz inputs have no effect."""
    pins = pins or {}
    _check_family(family)
    n, es = fmt.width, fmt.es
    LZ, SH = _slots(pins)
    rep = str(_pin(pins, "internal_representation", "sign_magnitude"))
    if rep not in ("sign_magnitude", "twos_complement"):
        raise ValueError(f"internal_representation {rep!r}")
    XW, EW, XT, sb = g.XW, g.EW, g.XT, g.sr_bits
    tag = _fmt_tag(fmt)
    name = name or f"fam_posit_encode_{family}_{rep}_{tag}_{g.tag()}{_ptag(pins)}"
    tc = rep == "twos_complement"
    m = Mod(name, f"posit encoder ({family}): X -> {fmt.name} pattern and flags; internal representation {rep}: "
                  + ("the magnitude rounded to nearest even, the pattern negated last"
                     if not tc else
                     "the field word negated first (the sticky as its borrow), the regime of the complemented scale, "
                     "nearest-even rounding in the two's complement domain, no final negation")
                  + f"{_pins_note(fmt, pins, family)}; rounding follows the frozen Python pattern rules")
    m.port("input", "x", XT)
    m.port("input", "rnd", 3)
    m.port("input", "word", sb)
    m.port("input", "ftz")
    m.port("output", "fl", FW)
    m.port("output", "bits", n)
    _x_fields(m, "x", g, "x_")
    m.wire("s", expr="x_s")
    m.wire("nar_in", expr="x_sp != 2'd0")
    m.wire("is_zero", expr=f"(x_sig == {XW}'d0) && !x_st")
    m.wire("lone", expr=f"(x_sig == {XW}'d0) && x_st")
    m.wire("sig_in", XW, expr=f"lone ? {XW}'d1 : x_sig")
    m.wire("e_in", EW, signed=True, expr=f"lone ? (x_e - {EW}'sd1) : x_e")
    _lzc(m, LZ[0], LZ[1], "sig_in", XW, "lz", "the normalizer's leading-zero count")
    lw = _clog2(XW)
    m.wire("lzs", lw, expr=f"(sig_in == {XW}'d0) ? {lw}'d0 : lz[{lw-1}:0]")
    _shift(m, SH[0], SH[1], "sig_in", XW, "lzs", 0, "sig", "the normalizer's left shift")
    m.wire("e", EW, signed=True, expr=f"e_in - $signed({{{{({EW}-{lw}){{1'b0}}}}, lzs}})")
    m.wire("eu", EW, signed=True, expr=f"e + {EW}'sd{XW-1}")
    m.wire("k", EW, signed=True, expr=f"eu >>> {es}" if es else "eu")
    if es:
        m.wire("elow", es, expr=f"eu[{es-1}:0]")
    m.wire("clamp_hi", expr=f"k > {EW}'sd{n-2}")
    m.wire("clamp_lo", expr=f"k < -{EW}'sd{n-2}")
    m.wire("clamp", expr="clamp_hi | clamp_lo")
    m.wire("ovf_k", expr=f"k == {EW}'sd{n-2}")
    FLW = es + XW - 1
    RW = n + es + XW + 2
    m.wire("fldm", FLW, expr=f"{{elow, sig[{XW-2}:0]}}" if es else f"sig[{XW-2}:0]")
    if tc:
        m.raw("  // the negative result's fields: the two's complement of the field word, the sticky as its borrow;")
        m.raw("  // the carry out complements the scale once more (an exact power of two)")
        m.wire("fldi", FLW, expr="~fldm")
        m.wire("nst", expr="!x_st")
        _incr(m, "fldn", "fldi", "nst", FLW, "the field word negated (narrow, before the regime is built)", cout="cneg")
        m.wire("fld", FLW, expr="s ? fldn : fldm")
        m.wire("kp", EW, signed=True, expr=f"s ? (~k + $signed({{{{{EW-1}{{1'b0}}}}, cneg}})) : k")
        padbit = "(s & x_st)"
        top = "s"
    else:
        m.wire("fld", FLW, expr="fldm")
        m.wire("kp", EW, signed=True, expr="k")
        padbit = "1'b0"
        top = "1'b0"
    RLW = _clog2(RW)
    m.wire("kabs", EW, expr="(kp < 0) ? -kp : kp")
    m.wire("rl", RLW, expr=f"(kp >= 0) ? (kabs[{RLW-1}:0] + {RLW}'d2) : (kabs[{RLW-1}:0] + {RLW}'d1)")
    m.wire("reg_hi", RW, expr=f"(kp >= 0) ? ~({{{RW}{{1'b1}}}} >> (kabs + 1)) : ({{{{{RW-1}{{1'b0}}}}, 1'b1}} << ({RW-1} - kabs))")
    m.wire("fld_top", RW, expr=f"{{fld, {{{RW-FLW}{{{padbit}}}}}}}")
    _shift(m, SH[0], SH[1], "fld_top", RW, "rl", 1, "fld_sh", "the exponent and fraction fields shifted below the regime")
    m.wire("r", RW, expr=f"reg_hi | fld_sh | {{{{{RW-1}{{1'b0}}}}, x_st}}")
    m.wire("topb", n - 1, expr=f"r[{RW-1}:{RW-n+1}]")
    m.wire("guard", expr=f"r[{RW-n}]")
    m.wire("rest_nz", expr=f"r[{RW-n-1}:0] != {RW-n}'d0")
    m.wire("inexact", expr="guard | rest_nz")
    m.wire("nearest_up", expr="guard & (rest_nz | topb[0])")
    down = "1'b0" if tc else "(inexact & s)"
    up = "inexact" if tc else "(inexact & !s)"
    m.wire("up", expr=f"(rnd == 3'd1 || rnd == 3'd2) ? {down} : (rnd == 3'd3) ? {up} : nearest_up")
    m.wire("pt0", n, expr=f"{{{top}, topb}}")
    _incr(m, "pt", "pt0", "up", n, "the rounding increment")
    maxpos = (1 << (n - 1)) - 1
    neg_maxpos = (1 << (n - 1)) + 1
    ones = (1 << n) - 1
    if tc:
        m.wire("ovf1", expr=f"pt == {n}'d{1 << (n - 1)}")
        m.wire("unf1", expr=f"pt == {n}'d0")
        m.wire("res", n, expr=(f"clamp_hi ? (s ? {n}'d{neg_maxpos} : {n}'d{maxpos}) : clamp_lo ? (s ? {n}'d{ones} : {n}'d1) : "
                               f"ovf1 ? (s ? {n}'d{neg_maxpos} : {n}'d{maxpos}) : unf1 ? (s ? {n}'d{ones} : {n}'d1) : pt"))
    else:
        m.wire("ovf1", expr=f"pt[{n-1}]")
        m.wire("unf1", expr=f"pt == {n}'d0")
        m.wire("mag", n, expr=f"clamp_hi ? {n}'d{maxpos} : clamp_lo ? {n}'d1 : ovf1 ? {n}'d{maxpos} : unf1 ? {n}'d1 : pt")
        m.wire("magx", n, expr=f"mag ^ {{{n}{{s}}}}")
        _incr(m, "res", "magx", "s", n, "the sign applied last: a negative result's pattern negated")
    F_NAN, F_INEX, F_OVF, F_UNF = flag_bit("nan"), flag_bit("inexact"), flag_bit("overflow"), flag_bit("underflow")
    m.wire("inex_f", expr="clamp | inexact")
    m.wire("ovf_f", expr="clamp_hi | (!clamp & (ovf1 | (ovf_k & inexact)))")
    m.wire("unf_f", expr="clamp_lo | (!clamp & unf1)")
    m.wire("fl_fin", FW, expr=f"(inex_f ? ({FW}'d1 << {F_INEX}) : {FW}'d0) | (ovf_f ? ({FW}'d1 << {F_OVF}) : {FW}'d0) | (unf_f ? ({FW}'d1 << {F_UNF}) : {FW}'d0)")
    m.assign("fl", f"nar_in ? ({FW}'d1 << {F_NAN}) : is_zero ? {FW}'d0 : fl_fin")
    m.assign("bits", f"nar_in ? {{1'b1, {{{n-1}{{1'b0}}}}}} : is_zero ? {n}'d0 : res")
    return name, m.render()


# ---- the PLAM multiplier ---------------------------------------------------------------
def plam_sv(g: Geom, name: str | None = None, pins: dict | None = None) -> tuple:
    """(name, text): xa * xb -> X with the fraction product replaced by
    Mitchell's addition of the fractions (PLAM): 1.fa * 1.fb ~ 1.(fa + fb),
    the carry of the fraction sum raising the exponent; the maximum
    relative error is 1/9 (fa = fb = 1/2). Specials as the engine's mul."""
    XW, EW, XT = g.XW, g.EW, g.XT
    LZ, SH = _slots(pins or {})
    name = name or f"fam_posit_mul_plam_{g.tag()}{_ptag(pins or {})}"
    m = Mod(name, "posit logarithm-approximate multiplier (PLAM): the significands normalized, the fractions added "
                  "instead of multiplied, the sum's carry into the exponent; error at most 1/9 relative")
    m.port("input", "xa", XT)
    m.port("input", "xb", XT)
    m.port("output", "y", XT)
    _x_fields(m, "xa", g, "a_")
    _x_fields(m, "xb", g, "b_")
    lw = _clog2(XW)
    for pre in ("a_", "b_"):
        _lzc(m, LZ[0], LZ[1], f"{pre}sig", XW, f"{pre}lz", f"operand {pre[0]}: leading zeros")
        m.wire(f"{pre}lzs", lw, expr=f"({pre}sig == {XW}'d0) ? {lw}'d0 : {pre}lz[{lw-1}:0]")
        _shift(m, SH[0], SH[1], f"{pre}sig", XW, f"{pre}lzs", 0, f"{pre}n", f"operand {pre[0]} normalized")
        m.wire(f"{pre}en", EW, signed=True, expr=f"{pre}e - $signed({{{{({EW}-{lw}){{1'b0}}}}, {pre}lzs}})")
        m.wire(f"{pre}f", XW - 1, expr=f"{pre}n[{XW-2}:0]")
    m.wire("s", expr="a_s ^ b_s")
    m.wire("sum", XW, expr="{1'b0, a_f} + {1'b0, b_f}")
    m.wire("carry", expr=f"sum[{XW-1}]")
    m.wire("sig", XW, expr=f"{{1'b1, sum[{XW-2}:0]}}")
    m.wire("e", EW, signed=True, expr=f"a_en + b_en + {EW}'sd{XW-1} + $signed({{{{{EW-1}{{1'b0}}}}, carry}})")
    m.wire("st", expr=f"a_st | b_st | ((a_f != 0) && (b_f != 0))")
    m.wire("nan", expr="(a_sp == 2'd1) || (b_sp == 2'd1)")
    m.wire("inf", expr="(a_sp == 2'd2) || (b_sp == 2'd2)")
    m.wire("zero", expr="a_z || b_z")
    m.wire("x_nan", XT, expr=f"{{2'd1, 1'b0, {EW}'sd0, {XW}'d0, 1'b0}}")
    m.wire("x_inf", XT, expr=f"{{2'd2, s, {EW}'sd0, {XW}'d0, 1'b0}}")
    m.wire("x_zero", XT, expr=f"{{2'd0, s, {EW}'sd0, {XW}'d0, 1'b0}}")
    m.assign("y", "nan ? x_nan : inf ? (zero ? x_nan : x_inf) : zero ? x_zero : {2'd0, s, e, sig, st}")
    return name, m.render()


# ---- the boundary converters and the characterization unit ------------------------------------
def cvt_sv(src, tgt, g: Geom, family: str, pins: dict, tokens: dict | None = None, name: str | None = None) -> tuple:
    """(name, text): the boundary converter of one direction on the lane's
    X: a decoded `src` value into the `tgt` pattern with flags (the shape
    of the rounder). A posit target goes through the posit encoder, a
    float target through the float rounder datapath (fp.round_sv)."""
    from chialu.targets.rtl.families import fp
    pins = pins or {}
    _check_family(family)
    tokens = tokens or {}
    name = name or f"fam_posit_cvt_{_fmt_tag(src)}_to_{_fmt_tag(tgt)}_{g.tag()}{_ptag(pins)}"
    if isinstance(tgt, PositFormat):
        inner, text = encode_sv(tgt, g, family, pins, tokens, name=f"{name}_enc")
        how = f"the posit encoder of {tgt.name}"
    else:
        core = tgt.core if isinstance(tgt, X87Format) else tgt
        if not isinstance(core, FloatFormat) or core.exp_only:
            raise ValueError(f"no boundary converter into {tgt.name}")
        inner, text = fp.round_sv(core, g, "dedicated_per_op", {}, tokens, name=f"{name}_round")
        how = f"the float rounder datapath of {tgt.name}"
    XT, sb = g.XT, g.sr_bits
    m = Mod(name, f"posit boundary converter ({family}): a decoded {src.name} value (X) into the {tgt.name} pattern "
                  f"through {how}; one dedicated module per direction")
    m.port("input", "x", XT)
    m.port("input", "rnd", 3)
    m.port("input", "word", sb)
    m.port("input", "ftz")
    m.port("output", "fl", FW)
    m.port("output", "bits", tgt.width)
    m.raw(f"  {inner} u_cvt (.x(x), .rnd(rnd), .word(word), .ftz(ftz), .fl(fl), .bits(bits));")
    m.extra.append(text)
    return name, m.render()


def unit_sv(fmt: PositFormat, g: Geom, family: str, pins: dict, tokens: dict | None = None,
            name: str | None = None) -> tuple:
    """(name, text): the decoder and the encoder of a format in one module
    (the characterization's unit): b, daz -> u and x, rnd, word, ftz -> fl,
    bits."""
    dn, dt = decode_sv(fmt, g, family, pins)
    en, et = encode_sv(fmt, g, family, pins, tokens)
    n, XT, VW, sb = fmt.width, g.XT, g.VW, g.sr_bits
    name = name or f"fam_posit_unit_{dn.split('_decode_')[1]}"
    m = Mod(name, f"posit unit ({family}): the decoder {dn} and the encoder {en} of {fmt.name}")
    m.port("input", "b", n)
    m.port("input", "daz")
    m.port("output", "u", VW + 1)
    m.port("input", "x", XT)
    m.port("input", "rnd", 3)
    m.port("input", "word", sb)
    m.port("input", "ftz")
    m.port("output", "fl", FW)
    m.port("output", "bits", n)
    m.raw(f"  {dn} u_dec (.b(b), .daz(daz), .u(u));")
    m.raw(f"  {en} u_enc (.x(x), .rnd(rnd), .word(word), .ftz(ftz), .fl(fl), .bits(bits));")
    m.extra.append(dt)
    m.extra.append(et)
    return name, m.render()


# ---- command line -----------------------------------------------------------------------
def main(argv=None) -> int:
    import argparse
    from chialu.targets.rtl.engine import Conventions, Engine
    from chialu.verify.formats import parse_format
    ap = argparse.ArgumentParser(description="emit a posit unit module of the family library")
    ap.add_argument("--format", default="posit16_1")
    ap.add_argument("--family", default="posit_adder_multiplier")
    ap.add_argument("--pins", default="", help="k=v,... (regime_decode, internal_representation, ...)")
    ap.add_argument("--kind", default="unit", choices=("decode", "encode", "unit", "plam", "cvt"))
    ap.add_argument("--target", default="fp16", help="the target format of --kind cvt")
    ap.add_argument("--sv", default=None, help="write the text here (stdout otherwise)")
    args = ap.parse_args(argv)
    fmt = parse_format(args.format)
    pins = dict(kv.split("=", 1) for kv in args.pins.split(",") if kv)
    targets = [fmt] + ([parse_format(args.target)] if args.kind == "cvt" else [])
    e = Engine("t", fmt, 8, False, targets=targets, conv=Conventions())
    g = Geom.of_engine(e)
    if args.kind == "decode":
        n, t = decode_sv(fmt, g, args.family, pins)
    elif args.kind == "encode":
        n, t = encode_sv(fmt, g, args.family, pins, e.tokens)
    elif args.kind == "plam":
        n, t = plam_sv(g)
    elif args.kind == "cvt":
        n, t = cvt_sv(fmt, parse_format(args.target), g, args.family, pins, e.tokens)
    else:
        n, t = unit_sv(fmt, g, args.family, pins, e.tokens)
    from chialu.targets.rtl.families import module_texts
    text = "\n".join(module_texts(n, t).values())
    if args.sv:
        open(args.sv, "w").write(text)
        print(f"{n}: {len(text)} chars -> {args.sv}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
