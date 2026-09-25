"""The approximate-unit families (the slot spaces of an ALU under
`accuracy: approximate`), on the same interfaces as the exact library:

* adders (a, b, cin -> s, cout): segmented_carry_speculative (sub-adders
  of the sub_adder family with a windowed carry speculation and a
  correction), lower_part_approximate (an exact upper adder, inexact
  low cells: forced constants, OR gates, the AXA / AMA / InXA cell
  styles, a reversed carry) and accuracy_configurable (staged
  correction between sub-adders enabled up to the operating mode, a
  static point of the runtime knob the unit interface lacks);
* multipliers (a, b -> p): truncated_fixed_width with the correction
  ladder, dynamic_segment (the window at the leading one, its
  selection, unbiasing and the small-operand fallback), operand_rounding
  (RoBA: operands rounded to powers of two, the product by shifts),
  logarithmic (Mitchell's line, its unbiased and double-sided variants,
  the correction ladder and the mantissa adder), pp_perforation (rows
  skipped, a correction), approximate_compressor_tree (the inexact
  4:2 cell styles over the low columns, error recovery) and
  approximate_booth (simplified encoders in the low columns, truncated
  hard multiples, rounded digits);
* dividers (a, b -> q, r): approximate_recurrence (the low stages of the
  restoring array with inexact subtractor cells or pruned) and
  approximate_functional (a reciprocal table product, a truncated
  reciprocal multiply, exact small cores on operand windows, the
  logarithmic subtraction, a short Goldschmidt iteration).

A runtime quality control (dual-quality cells, runtime width scaling)
needs a port the unit interface does not carry: those choices are
realized at a static operating point named in the module comment.
"""
from __future__ import annotations

from chialu.targets.rtl.families.mul import Netlist, _add_const, _cols, dedupe_modules, final_add, pp_and_array, reduce
from chialu.targets.rtl.families import mul_ext as MX
from chialu.targets.rtl.families.adder_ext import Mod as AMod

APPROX_ADDERS = ("segmented_carry_speculative", "lower_part_approximate", "accuracy_configurable")
APPROX_MULS = ("truncated_fixed_width", "dynamic_segment", "operand_rounding", "logarithmic", "pp_perforation",
               "approximate_compressor_tree", "approximate_booth")
APPROX_DIVS = ("approximate_recurrence", "approximate_functional")

def _pin(pins: dict, key: str, default):
    v = pins.get(key, default) if pins else default
    return default if v in (None, "") else v


def _ipin(pins: dict, key: str, default: int) -> int:
    try:
        return int(_pin(pins, key, default))
    except (TypeError, ValueError):
        return default


def _bpin(pins: dict, key: str, default: bool = False) -> bool:
    return str(_pin(pins, key, default)).lower() in ("true", "1", "yes")


def _sub(pins: dict, prefix: str) -> dict:
    return {k[len(prefix):]: v for k, v in (pins or {}).items() if k.startswith(prefix)}


def _slot(pins: dict, key: str, default: str) -> tuple:
    """(family, sub-pins) of a slot."""
    return str(_pin(pins, f"{key}.family", default)), _sub(pins, f"{key}.")


def _tag(pins: dict) -> str:
    """A 48-bit tag of the pins for the module name (empty without pins)."""
    if not pins:
        return ""
    import hashlib
    return "_" + hashlib.blake2b(repr(sorted((str(k), str(v)) for k, v in pins.items())).encode(), digest_size=6).hexdigest()


def _clog2(n: int) -> int:
    return max(1, (n - 1).bit_length())


# ---- adders --------------------------------------------------------------------------------
def segmented_speculative_sv(W: int, pins: dict, name: str) -> str:
    k = max(2, min(_ipin(pins, "sub_adder_width", 4), W))
    win = max(0, min(_ipin(pins, "prediction_window", 4), k))
    scheme = str(_pin(pins, "carry_in_scheme", "propagate_window"))
    corr = str(_pin(pins, "correction", "none"))
    fam = _pin(pins, "sub_adder.family", "ripple_carry")
    fpins = _sub(pins, "sub_adder.")
    m = AMod(name, W, f"segmented_carry_speculative: {k}-bit sub-adders ({fam}), carry-in by {scheme} over a {win}-bit window, "
                      f"correction {corr} (the ArithmeticError gate governs)")
    blocks = [(lo, min(lo + k, W)) for lo in range(0, W, k)]
    m.wire("c", len(blocks) + 1)
    m.assign("c[0]", "cin")
    m.wire("cr", len(blocks) + 1)          # the exact carries, for the correction
    m.assign("cr[0]", "cin")
    for bi, (lo, hi) in enumerate(blocks):
        n = hi - lo
        a, b = f"a[{hi-1}:{lo}]", f"b[{hi-1}:{lo}]"
        # the speculated carry into this block
        if bi == 0:
            m.wire(f"sp{bi}", expr="cin")
        elif scheme == "constant_zero" or win == 0:
            m.wire(f"sp{bi}", expr="1'b0")
        else:
            wl = max(0, lo - win)
            m.wire(f"wsum{bi}", lo - wl + 1, expr=f"{{1'b0, a[{lo-1}:{wl}]}} + {{1'b0, b[{lo-1}:{wl}]}}")
            m.wire(f"wsp{bi}", expr=f"wsum{bi}[{lo - wl}]")
            if scheme == "carry_cut_back":
                # the true carry unless the window propagates all the way, when the speculation stands in
                m.wire(f"wp{bi}", expr=f"&(a[{lo-1}:{wl}] ^ b[{lo-1}:{wl}])")
                m.wire(f"sp{bi}", expr=f"wp{bi} ? wsp{bi} : cr[{bi}]")
            else:
                m.wire(f"sp{bi}", expr=f"wsp{bi}")
        if scheme == "carry_select_speculation" and bi > 0:
            m.wire(f"s{bi}_0", n)
            m.wire(f"s{bi}_1", n)
            m.wire(f"co{bi}_0")
            m.wire(f"co{bi}_1")
            m.adder(fam, fpins, n, a, b, "1'b0", f"s{bi}_0", f"co{bi}_0", f"sub-adder {bi}, carry-in 0")
            m.adder(fam, fpins, n, a, b, "1'b1", f"s{bi}_1", f"co{bi}_1", f"sub-adder {bi}, carry-in 1")
            m.wire(f"s{bi}", n, expr=f"sp{bi} ? s{bi}_1 : s{bi}_0")
            m.wire(f"co{bi}", expr=f"sp{bi} ? co{bi}_1 : co{bi}_0")
            m.assign(f"cr[{bi+1}]", f"cr[{bi}] ? co{bi}_1 : co{bi}_0")
        else:
            m.wire(f"s{bi}", n)
            m.wire(f"co{bi}")
            m.adder(fam, fpins, n, a, b, f"sp{bi}", f"s{bi}", f"co{bi}", f"sub-adder {bi}")
            m.wire(f"P{bi}", expr=f"&({a} ^ {b})")
            m.wire(f"G{bi}", expr=f"co{bi} & ~(P{bi} & sp{bi})")   # the block's own generate
            m.assign(f"cr[{bi+1}]", f"G{bi} | (P{bi} & cr[{bi}])")
        m.assign(f"c[{bi+1}]", f"co{bi}")
        if corr in ("sign_repair", "error_reduction_stage") and bi > 0:
            # the miss of the speculation repaired: sign_repair on the top block only, the others on every block
            if corr != "sign_repair" or bi == len(blocks) - 1:
                m.wire(f"miss{bi}", expr=f"cr[{bi}] ^ sp{bi}")
                m.wire(f"sf{bi}", n)
                m.wire(f"cf{bi}")
                m.incr("prefix_and_incrementer", {"structure": "prefix_and_tree"}, n, f"s{bi}", f"miss{bi} & cr[{bi}]", f"sf{bi}", f"cf{bi}",
                       f"sub-adder {bi}: the missed carry added")
                m.wire(f"sd{bi}", n, expr=f"(miss{bi} & ~cr[{bi}]) ? (s{bi} - 1'b1) : sf{bi}")
                m.assign(f"s[{hi-1}:{lo}]", f"sd{bi}")
                continue
        m.assign(f"s[{hi-1}:{lo}]", f"s{bi}")
    m.assign("cout", f"c[{len(blocks)}]" if corr == "none" else f"cr[{len(blocks)}]")
    return m.render()


def lower_part_sv(W: int, pins: dict, name: str) -> str:
    k = max(1, min(_ipin(pins, "lower_width", 4), W - 1))
    cell = str(_pin(pins, "lower_cell", "or_gate"))
    cup = str(_pin(pins, "carry_to_upper", "none"))
    ufam = _pin(pins, "upper_adder.family", "ripple_carry")
    upins = _sub(pins, "upper_adder.")
    U = W - k
    m = AMod(name, W, f"lower_part_approximate: the upper {U} bits exact ({ufam}), the low {k} bits by {cell} cells, "
                      f"carry to the upper part {cup} (the ArithmeticError gate governs)")
    m.wire("al", k, expr=f"a[{k-1}:0]")
    m.wire("bl", k, expr=f"b[{k-1}:0]")
    m.wire("sl", k)
    if cell == "truncate_constant":
        m.assign("sl", f"{{{k}{{1'b1}}}}")
    elif cell == "or_gate":
        m.assign("sl", "al | bl")
    elif cell == "xor_xnor_axa":
        # the AXA style: the sum as the xnor of the inputs, the carry the first operand's bit
        m.assign("sl", "~(al ^ bl)")
    elif cell == "approx_mirror_ama":
        # the AMA style: the carry an exact majority, the sum its complement
        m.wire("cl_c", k + 1)
        m.assign("cl_c[0]", "cin")
        for i in range(k):
            m.assign(f"cl_c[{i+1}]", f"(al[{i}] & bl[{i}]) | (al[{i}] & cl_c[{i}]) | (bl[{i}] & cl_c[{i}])")
            m.assign(f"sl[{i}]", f"~cl_c[{i+1}]")
    elif cell == "inexact_cell_inxa":
        # the InXA style: an exact sum, the carry taken from the first operand's bit
        m.wire("cl_i", k + 1)
        m.assign("cl_i[0]", "cin")
        for i in range(k):
            m.assign(f"cl_i[{i+1}]", f"al[{i}]")
            m.assign(f"sl[{i}]", f"al[{i}] ^ bl[{i}] ^ cl_i[{i}]")
    else:
        # reverse_carry_rcpa: the carries run from the most significant low bit down
        m.wire("cl_r", k + 1)
        m.assign(f"cl_r[{k}]", "1'b0")
        for i in range(k - 1, -1, -1):
            m.assign(f"sl[{i}]", f"al[{i}] ^ bl[{i}] ^ cl_r[{i+1}]")
            m.assign(f"cl_r[{i}]", f"(al[{i}] & bl[{i}]) | ((al[{i}] ^ bl[{i}]) & cl_r[{i+1}])")
    if cup == "msb_and":
        m.wire("cl", expr=f"al[{k-1}] & bl[{k-1}]")
    elif cup == "window_speculation":
        win = max(1, min(_ipin(pins, "window", 3), k))
        m.wire("wsum", win + 1, expr=f"{{1'b0, al[{k-1}:{k-win}]}} + {{1'b0, bl[{k-1}:{k-win}]}}")
        m.wire("cl", expr=f"wsum[{win}]")
    else:
        m.wire("cl", expr="1'b0")
    m.wire("su", U)
    m.wire("cu")
    m.adder(ufam, upins, U, f"a[{W-1}:{k}]", f"b[{W-1}:{k}]", "cl", "su", "cu", "the exact upper adder")
    m.assign("s", "{su, sl}")
    m.assign("cout", "cu")
    return m.render()


def accuracy_configurable_sv(W: int, pins: dict, name: str, amodes: int = 0) -> str:
    """accuracy_configurable (ACA): the word in blocks, the mode deciding
    how many block boundaries carry the exact carry (correction_stage) or
    how many low blocks are dropped (truncation_width).

    With `amodes` zero the mode is the static `operating_mode` pin, which
    is the structure a unit without an accuracy-mode port carries. With
    `amodes` modes the unit drives the `amode` port and each block's
    carry-in is a mux of the exact carry against the speculated zero (the
    runtime ACA of Kahng and Kang 2012), so one structure serves every
    mode. Selections above the family's own top mode take the top mode.
    """
    modes = max(2, min(8, _ipin(pins, "mode_count", 2)))
    grain = str(_pin(pins, "reconfig_grain", "correction_stage"))
    runtime = amodes > 0
    mode = _ipin(pins, "operating_mode", modes // 2)
    mode = max(0, min(modes - 1, mode))
    sfam, spins = _slot(pins, "sub_adder", "ripple_carry")
    k = max(2, (W + modes - 1) // modes)
    aw = _clog2(amodes) if runtime else 0
    m = AMod(name, W,
             f"accuracy_configurable: {modes} modes by {grain}, "
             + (f"the mode on the `amode` port ({amodes} unit modes onto {modes} of its own, a selection above "
                f"the top mode taking it)" if runtime else
                f"frozen at the static operating mode {mode} (a single-cycle unit has one structure; "
                f"`operating_mode` sets it)")
             + f", the sub-adders {sfam} (the ArithmeticError gate governs)",
             ctrl=(("amode", aw),) if runtime else ())
    blocks = [(lo, min(lo + k, W)) for lo in range(0, W, k)]
    m.wire("c", len(blocks) + 1)
    m.assign("c[0]", "cin")
    if runtime:
        # the unit's mode mapped onto the family's own: mode j of the family is selected by
        # every unit mode from j up, and the top family mode takes every selection above it
        mw = _clog2(modes)
        src = "amode" if mw >= aw else f"amode[{mw-1}:0]"      # a 1-bit port takes no part select
        m.wire("amq", mw, expr=f"(amode >= {aw}'d{modes - 1}) ? {mw}'d{modes - 1} : {src}")
    for bi, (lo, hi) in enumerate(blocks):
        n = hi - lo
        a, b = f"a[{hi-1}:{lo}]", f"b[{hi-1}:{lo}]"
        # mode j enables the exact carry into the lowest j block boundaries (correction stages), the rest
        # speculate a zero carry; truncation_width zeroes the low blocks the mode drops instead
        exact_carry = bi == 0 or bi <= mode
        drop = grain == "truncation_width" and bi < (modes - 1 - mode)
        if runtime and grain == "truncation_width":
            # every block adds on the exact carry; block bi is dropped while the mode
            # leaves fewer than bi + 1 blocks standing (no mode drops the top block)
            droppable = bi < modes - 1
            m.wire(f"s{bi}", n)
            m.wire(f"co{bi}")
            if droppable:
                m.wire(f"sx{bi}", n)
            m.adder(sfam, spins, n, a, b, f"c[{bi}]", f"sx{bi}" if droppable else f"s{bi}", f"co{bi}",
                    f"sub-adder {bi}" + (f" (dropped below mode {modes - 1 - bi})" if droppable else ""))
            if droppable:
                m.wire(f"dr{bi}", expr=f"(amq < {_clog2(modes)}'d{modes - 1 - bi})")
                m.assign(f"s{bi}", f"dr{bi} ? {{{n}{{1'b1}}}} : sx{bi}")
                m.assign(f"c[{bi+1}]", f"dr{bi} ? 1'b0 : co{bi}")
            else:
                m.assign(f"c[{bi+1}]", f"co{bi}")
        elif runtime and grain != "truncation_width" and bi > 0:
            # the carry into block bi is exact while the mode reaches that boundary
            m.wire(f"ex{bi}", expr=f"(amq >= {_clog2(modes)}'d{bi})")
            m.wire(f"ci{bi}", expr=f"ex{bi} ? c[{bi}] : 1'b0")
            m.wire(f"s{bi}", n)
            m.wire(f"co{bi}")
            m.adder(sfam, spins, n, a, b, f"ci{bi}", f"s{bi}", f"co{bi}",
                    f"sub-adder {bi} (the carry-in exact from mode {bi} up)")
            m.assign(f"c[{bi+1}]", f"co{bi}")
        elif drop:
            m.wire(f"s{bi}", n, expr=f"{{{n}{{1'b1}}}}")
            m.assign(f"c[{bi+1}]", "1'b0")
        else:
            m.wire(f"s{bi}", n)
            m.wire(f"co{bi}")
            m.adder(sfam, spins, n, a, b, f"c[{bi}]" if exact_carry else "1'b0", f"s{bi}", f"co{bi}",
                    f"sub-adder {bi} ({'exact carry-in' if exact_carry else 'speculated zero carry-in'})")
            m.assign(f"c[{bi+1}]", f"co{bi}")
        m.assign(f"s[{hi-1}:{lo}]", f"s{bi}")
    m.assign("cout", f"c[{len(blocks)}]")
    return m.render()


# ---- multipliers -------------------------------------------------------------------------
def truncated_ladder_sv(w: int, signed: bool, pins: dict, name: str) -> str:
    """truncated_fixed_width of the approximate space is the exact space's
    family itself (its pins: extra_columns_kept, correction_scheme,
    output_rounding, the kept_tree slot)."""
    return MX.truncated_sv(w, signed, pins, name)


def dynamic_segment_sv(w: int, signed: bool, pins: dict, name: str, amodes: int = 0) -> str:
    """dynamic_segment: the product of a `segment_width` window of each
    operand, taken at the leading one.

    With `amodes` modes the unit drives the `amode` port and the window
    scales at runtime: the top mode keeps the whole window and each mode
    below it drops one more low bit of both windows, which is the runtime
    width scaling the family's card offers. The window's position
    arithmetic is unchanged, so only the kept bits differ between modes.
    """
    seg = max(2, min(_ipin(pins, "segment_width", 6), w))
    sel = str(_pin(pins, "segment_select", "dynamic_leading_one"))
    unb = str(_pin(pins, "unbiasing", "lsb_set_to_one"))
    fallback = _bpin(pins, "small_operand_fallback")
    lod, shf, add = _slot(pins, "lod", "lzd_cell_tree"), _slot(pins, "shifter", "barrel_mux_tree"), _slot(pins, "adder", "ripple_carry")
    core = _slot(pins, "core_multiplier", "direct_pp_parallel")
    runtime = amodes > 0
    aw = _clog2(amodes) if runtime else 0
    keep_low = max(2, seg - (amodes - 1)) if runtime else seg      # the bits the coarsest mode keeps
    m = MX.Mod(name, w, f"dynamic_segment: a {seg}-bit window per operand ({sel}; the leading one by {lod[0]}, the window by "
                        f"{shf[0]}), unbiasing {unb}, the window product by {core[0]}, the position arithmetic by {add[0]}"
                        + (", the exact product when both operands fit the window" if fallback else "")
                        + (f", the window scaled by the `amode` port from {keep_low} bits at mode 0 to {seg} at mode "
                           f"{amodes - 1} (runtime width scaling)" if runtime else "")
                        + " (the ArithmeticError gate governs)",
               ctrl=(("amode", aw),) if runtime else ())
    if signed:
        m.wire("am", w, expr=f"a[{w-1}] ? -a : a")
        m.wire("bm", w, expr=f"b[{w-1}] ? -b : b")
    else:
        m.wire("am", w, expr="a")
        m.wire("bm", w, expr="b")
    nw = w.bit_length()
    for s_ in ("a", "b"):
        if sel == "static_msb_or_lsb":
            # the window fixed at the top of the word
            m.wire(f"lz{s_}", nw, expr=f"{nw}'d0")
            m.wire(f"sh{s_}", w, expr=f"{s_}m")
        else:
            m.lzc(lod[0], lod[1], w, f"{s_}m", f"lz{s_}", f"the leading one of {s_} ({lod[0]})")
            m.shift(shf[0], shf[1], w, f"{s_}m", f"lz{s_}", "3'd0", f"sh{s_}", f"{s_} normalized to its leading one ({shf[0]})")
        if seg < w:
            m.wire(f"drop{s_}", expr=f"(lz{s_} < {w - seg}) && (sh{s_}[{w-seg-1}:0] != 0)")
            if sel == "dynamic_leading_one_rounded":
                m.wire(f"wr{s_}", seg + 1, expr=f"{{1'b0, sh{s_}[{w-1}:{w-seg}]}} + sh{s_}[{w-seg-1}]")
                m.wire(f"win{s_}", seg, expr=f"wr{s_}[{seg}] ? {{1'b1, {{{seg-1}{{1'b0}}}}}} : wr{s_}[{seg-1}:0]")
                m.wire(f"ovf{s_}", expr=f"wr{s_}[{seg}]")
            else:
                m.wire(f"ovf{s_}", expr="1'b0")
                if unb == "lsb_set_to_one":
                    m.wire(f"win{s_}", seg, expr=f"{{sh{s_}[{w-1}:{w-seg+1}], sh{s_}[{w-seg}] | drop{s_}}}")
                else:
                    m.wire(f"win{s_}", seg, expr=f"sh{s_}[{w-1}:{w-seg}]")
        else:
            m.wire(f"win{s_}", seg, expr=f"sh{s_}")
            m.wire(f"ovf{s_}", expr="1'b0")
            m.wire(f"drop{s_}", expr="1'b0")
    if runtime:
        # the low bits the mode drops from both windows: mode amodes-1 keeps the whole
        # window, each mode below it drops one more bit (the mask is a constant per mode)
        expr = f"{{{seg}{{1'b1}}}}"
        for md in range(amodes - 2, -1, -1):
            drop = min(seg - 2, amodes - 1 - md)
            mask = f"{{{{{seg - drop}{{1'b1}}}}, {drop}'d0}}" if drop else f"{{{seg}{{1'b1}}}}"
            expr = f"(amode == {aw}'d{md}) ? {mask} : ({expr})"
        m.wire("wmask", seg, expr=expr)
        for s_ in ("a", "b"):
            m.wire(f"winq{s_}", seg, expr=f"win{s_} & wmask")
        m.mul(core[0], core[1], seg, "winqa", "winqb", "pw",
              f"the window product ({core[0]}), the window scaled by the mode")
    else:
        m.mul(core[0], core[1], seg, "wina", "winb", "pw", f"the window product ({core[0]})")
    SW = 2 * w + 2 * seg + 2
    m.wire("pwe", SW, expr=f"{{{{({SW}-{2*seg}){{1'b0}}}}, pw}}")
    # the product's position: 2w - 2seg - (lza + lzb - ovfa - ovfb), in two's complement through the adder slot
    EW = nw + 3
    m.wire("lzae", EW, expr=f"{{{{({EW}-{nw}){{1'b0}}}}, lza}}")
    m.wire("lzbe", EW, expr=f"{{{{({EW}-{nw}){{1'b0}}}}, lzb}}")
    m.wire("ovfe", EW, expr=f"{{{{({EW}-2){{1'b0}}}}, {{1'b0, ovfa}} + {{1'b0, ovfb}}}}")
    m.add(add[0], add[1], EW, "lzae", "lzbe", "lzsum", "the leading positions summed")
    m.wire("lzsl", EW, expr=f"lzsum[{EW-1}:0]")
    m.add(add[0], add[1], EW, "lzsl", "ovfe", "shs", "the rounding overflows taken off", sub=True)
    m.wire("shift", EW, expr=f"shs[{EW-1}:0]")
    m.wire("cst", EW, expr=f"{EW}'d{2 * w - 2 * seg}")
    m.add(add[0], add[1], EW, "cst", "shift", "lfs", "the distance to the product's place", sub=True)
    m.wire("left", EW, expr=f"lfs[{EW-1}:0]")
    m.add(add[0], add[1], EW, "shift", "cst", "lns", "the same distance the other way", sub=True)
    m.wire("leftm", EW, expr=f"left[{EW-1}] ? lns[{EW-1}:0] : left")
    m.wire("lbig", expr=f"leftm >= {SW}")
    m.wire("lam", EW, expr=f"lbig ? {EW}'d0 : leftm")
    m.shift(shf[0], shf[1], SW, "pwe", "lam", "3'd0", "fl", f"the window product to its place, leftwards ({shf[0]})")
    m.shift(shf[0], shf[1], SW, "pwe", "lam", "3'd1", "fr", f"the window product to its place, rightwards ({shf[0]})")
    m.wire("full", SW, expr=f"lbig ? {SW}'d0 : (left[{EW-1}] ? fr : fl)")
    if unb == "poc_cascade_fill" and seg < w:
        # the dropped bits filled with ones below the window's product (the cascade fill of the omitted part)
        m.wire("fill", SW, expr=f"((dropa | dropb) && !left[{EW-1}]) ? (({SW}'d1 << leftm) - 1) : {SW}'d0")
        m.wire("pz0", 2 * w, expr=f"(full | fill)[{2*w-1}:0]")
    elif unb == "round_and_correct" and seg < w:
        m.wire("pz0", 2 * w, expr=f"full[{2*w-1}:0] + (((dropa | dropb) && !left[{EW-1}] && leftm != 0) ? ({2*w}'d1 << (leftm - 1)) : {2*w}'d0)")
    else:
        m.wire("pz0", 2 * w, expr=f"full[{2*w-1}:0]")
    if fallback:
        # both operands inside their windows: the exact product through the core multiplier at the full width
        m.wire("fits", expr=f"(lza >= {w - seg}) && (lzb >= {w - seg})")
        m.mul(core[0], core[1], w, "am", "bm", "pfull", f"the exact product of two operands that fit the window ({core[0]})")
        m.wire("pz", 2 * w, expr=f"(am == 0 || bm == 0) ? {2*w}'d0 : (fits ? pfull : pz0)")
    else:
        m.wire("pz", 2 * w, expr=f"(am == 0 || bm == 0) ? {2*w}'d0 : pz0")
    if signed:
        m.assign("p", f"(a[{w-1}] ^ b[{w-1}]) ? -pz : pz")
    else:
        m.assign("p", "pz")
    return m.render()


def operand_rounding_sv(w: int, signed: bool, pins: dict, name: str) -> str:
    """RoBA: each operand rounded to its nearest power of two; nearest_pow2
    takes the product of the two powers, pow2_plus_residual the RoBA
    form a 2^kb + b 2^ka - 2^(ka+kb) by shifts; bias_correction adds
    the mean residual. The leading ones by the lod slot, the shifts by
    the shifter slot, the sums by the adder slot."""
    rounding = str(_pin(pins, "rounding", "pow2_plus_residual"))
    bias = _bpin(pins, "bias_correction")
    lod, shf, add = _slot(pins, "lod", "lzd_cell_tree"), _slot(pins, "shifter", "barrel_mux_tree"), _slot(pins, "adder", "ripple_carry")
    m = MX.Mod(name, w, f"operand_rounding (RoBA, {rounding}{', bias corrected' if bias else ''}): the operands rounded to powers of two "
                        f"(the leading one by {lod[0]}), the product by shifts ({shf[0]}) and adds ({add[0]}) (the ArithmeticError gate governs)")
    if signed:
        m.wire("am", w, expr=f"a[{w-1}] ? -a : a")
        m.wire("bm", w, expr=f"b[{w-1}] ? -b : b")
    else:
        m.wire("am", w, expr="a")
        m.wire("bm", w, expr="b")
    nw = w.bit_length()
    kw = _clog2(w) + 1
    for s_ in ("a", "b"):
        m.lzc(lod[0], lod[1], w, f"{s_}m", f"lz{s_}", f"the leading one of {s_} ({lod[0]})")
        m.wire(f"k{s_}", kw, expr=f"{w-1} - lz{s_}")
        # round up when the bit below the leading one is set (the nearest power of two)
        m.shift(shf[0], shf[1], w, f"{s_}m", f"lz{s_}", "3'd0", f"sh{s_}", f"{s_} normalized to its leading one ({shf[0]})")
        m.wire(f"up{s_}", expr=f"sh{s_}[{w-2}]" if w >= 2 else "1'b0")
        m.wire(f"kr{s_}", kw, expr=f"k{s_} + up{s_}")
    PW = 2 * w + 2
    m.wire("ksum", kw + 1, expr="kra + krb")
    m.wire("one", PW, expr=f"{PW}'d1")
    m.shift(shf[0], shf[1], PW, "one", "ksum", "3'd0", "t3", f"the product of the two powers ({shf[0]})")
    if rounding == "nearest_pow2":
        m.wire("pz", PW, expr="t3")
    else:
        m.wire("ame", PW, expr=f"{{{{({PW}-{w}){{1'b0}}}}, am}}")
        m.wire("bme", PW, expr=f"{{{{({PW}-{w}){{1'b0}}}}, bm}}")
        m.shift(shf[0], shf[1], PW, "ame", "krb", "3'd0", "t1", f"a times b's power ({shf[0]})")
        m.shift(shf[0], shf[1], PW, "bme", "kra", "3'd0", "t2", f"b times a's power ({shf[0]})")
        m.add(add[0], add[1], PW, "t1", "t2", "t12", f"the two shifted operands added ({add[0]})")
        m.wire("t12l", PW, expr=f"t12[{PW-1}:0]")
        m.add(add[0], add[1], PW, "t12l", "t3", "pzs", f"the powers' product taken off ({add[0]})", sub=True)
        m.wire("pz", PW, expr=f"pzs[{PW-1}:0]")
    if bias:
        # the mean residual of the RoBA form over uniform operands, at the product's scale (about 1/16 of 2^(ka+kb))
        m.wire("t3q", PW, expr="t3 >> 4")
        m.add(add[0], add[1], PW, "pz", "t3q", "pbs", f"the bias correction added ({add[0]})")
        m.wire("pb", PW, expr=f"pbs[{PW-1}:0]")
    else:
        m.wire("pb", PW, expr="pz")
    # a rounded operand at the top of its range takes the product past the width: it saturates
    m.wire("pf", 2 * w, expr=f"(am == 0 || bm == 0) ? {2*w}'d0 : ((pb >> {2*w}) != 0 ? {{{2*w}{{1'b1}}}} : pb[{2*w-1}:0])")
    if signed:
        m.assign("p", f"(a[{w-1}] ^ b[{w-1}]) ? -pf : pf")
    else:
        m.assign("p", "pf")
    return m.render()


def logarithmic_sv(w: int, signed: bool, pins: dict, name: str) -> str:
    """logarithmic of the approximate space on the exact family's module:
    base mitchell / mitchell_unbiased (near-zero-bias constant) /
    double_sided (nearest-one rounding), the correction ladder
    (piecewise_terms as Combet's table, iterative_residual as the
    residual's own Mitchell product added back, operand_decomposition,
    near_zero_bias_coefficients as the unbiased constant), the mantissa
    adder truncated or with the low bits OR-ed."""
    base = str(_pin(pins, "base", "mitchell"))
    corr = str(_pin(pins, "correction", "none"))
    iters = max(1, min(4, _ipin(pins, "iterations", 1)))
    madd = str(_pin(pins, "mantissa_adder", "exact"))
    scheme = {"none": "none", "piecewise_terms": "combet_error_terms", "operand_decomposition": "operand_decomposition",
              "iterative_residual": "none", "near_zero_bias_coefficients": "none"}[corr if corr in ("none", "piecewise_terms", "operand_decomposition", "iterative_residual", "near_zero_bias_coefficients") else "none"]
    if base == "double_sided" and corr != "iterative_residual":
        scheme = "nearest_one_rounding"
    # the core is the exact family's module; its lod, normalize_shifter, log_adder and antilog_shifter slots are
    # this family's slots of the same names
    mpins = {"correction_scheme": scheme, "correction_table_bits": _ipin(pins, "correction_table_bits", 4)}
    for k, v in pins.items():
        if k.split(".")[0] in ("lod", "normalize_shifter", "log_adder", "antilog_shifter"):
            mpins[k] = v
    L = MX._Log(mpins)
    inner = MX.logarithmic_sv(w, False, mpins, name + "_core")            # the core on magnitudes
    m = MX.Mod(name, w, f"logarithmic (approximate space): base {base}, correction {corr}" + (f" x{iters}" if corr == "iterative_residual" else "")
                        + f", mantissa adder {madd}; the core's leading-one detection {L.lod[0]}, adder {L.add[0]}, shifters "
                        f"{L.nsh[0]} and {L.ash[0]} (the ArithmeticError gate governs)")
    m.extra.append(inner)
    if signed:
        m.wire("am", w, expr=f"a[{w-1}] ? -a : a")
        m.wire("bm", w, expr=f"b[{w-1}] ? -b : b")
    else:
        m.wire("am", w, expr="a")
        m.wire("bm", w, expr="b")
    m.wire("pc", 2 * w)
    m.raw(f"  {name}_core u_core (.a(am), .b(bm), .p(pc));")
    unbiased = base == "mitchell_unbiased" or corr == "near_zero_bias_coefficients"
    if corr == "iterative_residual":
        # the residual (the product less the Mitchell estimate is the fractions' product): approximated again
        # by Mitchell on the operands' fractions, added back; iterations beyond the first repeat on the
        # remaining residual with the same structure (the product of the fractions' own fractions)
        nw = w.bit_length()
        m.wire("half", w, expr=f"{w}'d{1 << (w - 1)}")
        m.wire("frmask", w, expr=f"{{1'b0, {{{w-1}{{1'b1}}}}}}")

        def fraction(src: str, tag: str):
            """The fraction bits below the leading one of src (lod and normalize_shifter slots)."""
            m.lzc(L.lod[0], L.lod[1], w, src, f"lz{tag}", f"the leading one of {src} ({L.lod[0]})")
            m.shift(L.nsh[0], L.nsh[1], w, src, f"lz{tag}", "3'd0", f"nm{tag}", f"{src} normalized ({L.nsh[0]})")
            m.wire(f"fr{tag}", w, expr=f"nm{tag} & frmask")

        def complement(src: str, cf: str, out: str):
            """1 - src (at the fraction's scale) under cf, else src (log_adder slot)."""
            m.add(L.add[0], L.add[1], w, "half", src, f"{out}_c", f"the fraction's complement ({L.add[0]})", sub=True)
            m.wire(out, w, expr=f"{cf} ? {out}_c[{w-1}:0] : {src}")

        fraction("am", "a")
        fraction("bm", "b")
        # iteration k adds Mitchell's estimate of the previous fractions' product at their weight: the missing
        # term of each estimate is the product of its operands' fractions
        # after a mantissa carry (fa + fb >= 1) the missing term is (1 - fa)(1 - fb): the complements
        m.add(L.add[0], L.add[1], w, "fra", "frb", "frs0", f"the fractions summed ({L.add[0]})")
        m.wire("cf0", expr=f"frs0[{w-1}]")
        complement("fra", "cf0", "fca")
        complement("frb", "cf0", "fcb")
        cur_a, cur_b = "fca", "fcb"
        m.wire("acc0", 2 * nw, expr="lza + lzb")
        AW2 = _clog2(2 * w)
        for it in range(iters):
            m.wire(f"rp{it}", 2 * w)
            m.raw(f"  {name}_core u_res{it} (.a({cur_a}), .b({cur_b}), .p(rp{it}));")
            m.wire(f"rbig{it}", expr=f"acc{it} >= {2 * w}")
            m.wire(f"ram{it}", AW2, expr=f"rbig{it} ? {AW2}'d0 : acc{it}[{AW2-1}:0]")
            m.shift(L.ash[0], L.ash[1], 2 * w, f"rp{it}", f"ram{it}", "3'd1", f"rsh{it}", f"the residual estimate to its weight ({L.ash[0]})")
            m.wire(f"rs{it}", 2 * w, expr=f"rbig{it} ? {2*w}'d0 : rsh{it}")
            if it + 1 < iters:
                fraction(cur_a, f"a{it}")
                fraction(cur_b, f"b{it}")
                m.add(L.add[0], L.add[1], w, f"fra{it}", f"frb{it}", f"frs{it+1}", f"the residual fractions summed ({L.add[0]})")
                m.wire(f"cf{it+1}", expr=f"frs{it+1}[{w-1}]")
                complement(f"fra{it}", f"cf{it+1}", f"fca{it}")
                complement(f"frb{it}", f"cf{it+1}", f"fcb{it}")
                m.wire(f"acc{it+1}", 2 * nw, expr=f"acc{it} + lza{it} + lzb{it}")
                cur_a, cur_b = f"fca{it}", f"fcb{it}"
        cur = "rs0"
        for it in range(1, iters):
            m.add(L.add[0], L.add[1], 2 * w, cur, f"rs{it}", f"prs{it}", f"the residual estimates summed ({L.add[0]})")
            m.wire(f"pres{it}", 2 * w, expr=f"prs{it}[{2*w-1}:0]")
            cur = f"pres{it}"
        m.add(L.add[0], L.add[1], 2 * w, "pc", cur, "pis", f"the residual added to the estimate ({L.add[0]})")
        m.wire("pi", 2 * w, expr=f"(am == 0 || bm == 0) ? {2*w}'d0 : pis[{2*w-1}:0]")
    else:
        m.wire("pi", 2 * w, expr="pc")
    if unbiased:
        # the near-zero-bias constant: the mean of the missing cross term over uniform fractions (about 1/12 of
        # the estimate's leading power), as shifts of the estimate's own magnitude
        m.wire("pi5", 2 * w, expr="pi >> 5")
        m.wire("pi7", 2 * w, expr="pi >> 7")
        m.add(L.add[0], L.add[1], 2 * w, "pi5", "pi7", "pub", f"the bias terms ({L.add[0]})")
        m.wire("publ", 2 * w, expr=f"pub[{2*w-1}:0]")
        m.add(L.add[0], L.add[1], 2 * w, "pi", "publ", "pu1", f"the bias added ({L.add[0]})")
        m.wire("pu", 2 * w, expr=f"(am == 0 || bm == 0) ? {2*w}'d0 : (pu1[{2*w}] ? {{{2*w}{{1'b1}}}} : pu1[{2*w-1}:0])")
    else:
        m.wire("pu", 2 * w, expr="pi")
    if madd == "truncated":
        m.wire("pm", 2 * w, expr=f"{{pu[{2*w-1}:{w // 2}], {w // 2}'d0}}")
    elif madd == "set_one_soa":
        m.wire("pm", 2 * w, expr=f"{{pu[{2*w-1}:{w // 2}], {{{w // 2}{{1'b1}}}}}}")
    else:
        m.wire("pm", 2 * w, expr="pu")
    if signed:
        m.assign("p", f"(a[{w-1}] ^ b[{w-1}]) ? -pm : pm")
    else:
        m.assign("p", "pm")
    return m.render()


def _block_2x2(nl: Netlist, cols: list, a: str, b: str, i: int, j: int, inexact: bool):
    """The 2x2 block of multiplier bits (i, i+1) and multiplicand bits (j, j+1)
    into the columns: exact as four ANDs, or Kulkarni's inaccurate cell (three
    gates; 3 x 3 gives 7)."""
    if inexact:
        cols[i + j].append(nl.wire(f"{a}[{j}] & {b}[{i}]", "pp"))
        cols[i + j + 1].append(nl.wire(f"({a}[{j+1}] & {b}[{i}]) | ({a}[{j}] & {b}[{i+1}])", "pp"))
        cols[i + j + 2].append(nl.wire(f"{a}[{j+1}] & {b}[{i+1}]", "pp"))
    else:
        for di in (0, 1):
            for dj in (0, 1):
                cols[i + di + j + dj].append(nl.wire(f"{a}[{j+dj}] & {b}[{i+di}]", "pp"))


def perforation_sv(w: int, signed: bool, pins: dict, name: str) -> str:
    """pp_perforation: the low `perforated_rows` rows skipped; the kept rows
    as an AND array (exact_and), as Kulkarni's 2x2 inaccurate blocks
    (kulkarni_2x2_inaccurate), or as the AWTM band (awtm_band_forced_block:
    the multiplicand rounded at `multiplicand_rounding_bit`, the low band's
    blocks inaccurate, the band's carry into the exact upper part predicted
    by `carry_prediction` rather than propagated); a signed multiplier
    forms the block cells on the magnitudes."""
    rows = max(0, min(_ipin(pins, "perforated_rows", 2), w - 1))
    cell = str(_pin(pins, "cell", "exact_and"))
    corr = str(_pin(pins, "correction", "none"))
    pred = str(_pin(pins, "carry_prediction", "two_or_more_threshold"))
    rbit = max(0, min(_ipin(pins, "multiplicand_rounding_bit", 0), w - 2))
    nl = Netlist()
    cols = _cols(2 * w)
    head = []
    blocks = cell in ("kulkarni_2x2_inaccurate", "awtm_band_forced_block")
    a_src, b_src = "a", "b"
    if blocks and signed:
        head.append(f"  logic [{w-1}:0] am, bm; assign am = a[{w-1}] ? -a : a; assign bm = b[{w-1}] ? -b : b;")
        a_src, b_src = "am", "bm"
    if cell == "awtm_band_forced_block" and rbit > 0:
        # the multiplicand rounded at the bit: the bits below it drop, the bit above rounds up
        head.append(f"  logic [{w}:0] ar1; assign ar1 = {{1'b0, {a_src}}} + {{{{{w}{{1'b0}}}}, {a_src}[{rbit-1}]}};")
        head.append(f"  logic [{w-1}:0] ar; assign ar = ar1[{w}] ? {{{w}{{1'b1}}}} : {{ar1[{w-1}:{rbit}], {rbit}'d0}};")
        a_src = "ar"
    if blocks:
        # the kept rows in pairs of 2x2 blocks (an odd last row as exact ANDs); under the band the blocks whose
        # weight lies in the low half are inaccurate, the upper ones exact
        i = rows
        while i < w:
            if i + 1 < w:
                for j in range(0, w, 2):
                    if j + 1 < w:
                        low = cell == "kulkarni_2x2_inaccurate" or (i + j + 2 < w)
                        _block_2x2(nl, cols, a_src, b_src, i, j, low)
                    else:
                        for di in (0, 1):
                            cols[i + di + j].append(nl.wire(f"{a_src}[{j}] & {b_src}[{i+di}]", "pp"))
                i += 2
            else:
                for j in range(w):
                    cols[i + j].append(nl.wire(f"{a_src}[{j}] & {b_src}[{i}]", "pp"))
                i += 1
    else:
        for i in range(w):
            if i < rows:
                continue
            for j in range(w):
                invert = signed and ((i == w - 1) != (j == w - 1))
                cols[i + j].append(nl.wire(f"{'~' if invert else ''}({b_src}[{i}] & {a_src}[{j}])", "pp"))
        if signed:
            _add_const(cols, (1 << w) + (1 << (2 * w - 1)))
    if corr == "constant" and rows > 0:
        # the expected sum of the skipped rows: a quarter of each bit's weight
        exp = sum(0.25 * (1 << (i + j)) for i in range(rows) for j in range(w))
        _add_const(cols, int(round(exp)) % (1 << (2 * w)))
    elif corr == "error_correction_vector" and rows > 0:
        # each skipped row's top bits kept: b_i a[w-1:w-2] at its weight
        for i in range(rows):
            for j in range(max(0, w - 2), w):
                cols[i + j].append(nl.wire(f"{b_src}[{i}] & {a_src}[{j}]", "ec"))
    elif corr == "probabilistic_compensation" and rows > 0:
        # each skipped row's expected value given its multiplier bit: b_i times half the multiplicand's range
        for i in range(rows):
            cols[i + w - 2].append(f"{b_src}[{i}]")
    lines = []
    if cell == "awtm_band_forced_block":
        # the band: the low half's columns reduced and added on their own (no carry out), the carry into the
        # upper half predicted from the bits of the band's top column; the upper half reduced and added with it
        top = cols[w - 1]
        if pred == "simplified_or":
            cpred = nl.wire(" | ".join(top) if top else "1'b0", "t")
        else:
            pairs = [f"({x} & {y})" for k, x in enumerate(top) for y in top[k + 1:]]
            cpred = nl.wire(" | ".join(pairs) if pairs else "1'b0", "t")
        low = cols[:w] + [[] for _ in range(w)]
        high = [[] for _ in range(w)] + cols[w:]
        high[w].append(cpred)
        low_r = reduce(nl, low, "dadda", "3_2")
        high_r = reduce(nl, high, "dadda", "3_2")
        ll, lt = final_add(nl, low_r, pins, "cpa")
        hl, ht = final_add(nl, high_r, pins, "cpa")
        # the two adders' results into the product: the low half's low w bits, the high half's top w bits
        lines = [ln.replace("row_s", "lrow_s").replace("row_c", "lrow_c").replace(".s(p)", ".s(pl)").replace("u_cpa", "u_cpa_l") for ln in ll]
        lines += [ln.replace(".s(p)", ".s(ph)").replace("u_cpa", "u_cpa_h") for ln in hl]
        lines.insert(0, f"  logic [{2*w-1}:0] pl, ph;")
        lines.append(f"  assign p{'z' if signed else ''} = {{ph[{2*w-1}:{w}], pl[{w-1}:0]}};")
        add_text = lt + ht
    else:
        cols = reduce(nl, cols, "dadda", "3_2")
        lines, add_text = final_add(nl, cols, pins, "cpa")
        if blocks and signed:
            lines = [ln.replace(".s(p)", ".s(pz)") for ln in lines]
    text = [f"// pp_perforation: the low {rows} partial-product rows skipped, the kept rows as {cell} cells"
            + (f" (the multiplicand rounded at bit {rbit}, the band's carry by {pred})" if cell == "awtm_band_forced_block" else "")
            + f", correction {corr} (the ArithmeticError gate governs)",
            f"module {name} (input logic [{w-1}:0] a, input logic [{w-1}:0] b, output logic [{2*w-1}:0] p);"]
    text += head
    if blocks and signed:
        text.append(f"  logic [{2*w-1}:0] pz; assign p = (a[{w-1}] ^ b[{w-1}]) ? -pz : pz;")
    text += nl.render()
    text += lines
    text.append("endmodule")
    return "\n".join(text) + "\n" + add_text


def compressor_tree_sv(w: int, signed: bool, pins: dict, name: str) -> str:
    """approximate_compressor_tree: the inexact 4:2 cell styles over the low
    `approximate_columns` columns: the design-1 rule (momeni_d1_d2: sum =
    (x1^x2)|(x3^x4), carry = x1x2|x3x4), the OR rule (yang_inexact: sum =
    x1|x2|x3|x4, carry = x1x2|x3x4) and the unbiased rule
    (esposito_unbiased)."""
    ac = max(0, min(_ipin(pins, "approximate_columns", w), 2 * w - 1))
    cell = str(_pin(pins, "compressor", "momeni_d1_d2"))
    rec = str(_pin(pins, "error_recovery", "none"))
    rule = "or" if cell == "yang_inexact" else ("unbiased" if cell == "esposito_unbiased" else "design1")
    nl = Netlist()
    cols = pp_and_array(nl, w, signed)
    if rule == "or":
        # the OR-style cell: a Dadda pass replacing 4:2 groups in the low columns by an or-sum and an and-carry
        from chialu.targets.rtl.families.mul import _dadda_targets
        n = len(cols)
        h = max(len(c) for c in cols)
        for target in _dadda_targets(h):
            new = [[] for _ in range(n)]
            for c in range(n):
                bits, k = cols[c], 0
                while len(bits) - k + len(new[c]) > target:
                    if c < ac and len(bits) - k >= 4:
                        x1, x2, x3, x4 = bits[k:k + 4]
                        k += 4
                        new[c].append(nl.wire(f"{x1} | {x2} | {x3} | {x4}", "t"))
                        if c + 1 < n:
                            new[c + 1].append(nl.wire(f"({x1} & {x2}) | ({x3} & {x4})", "t"))
                    elif len(bits) - k >= 3 and len(bits) - k + len(new[c]) - target >= 2:
                        s_, cy = nl.fa(bits[k], bits[k + 1], bits[k + 2]); k += 3
                        new[c].append(s_)
                        if c + 1 < n:
                            new[c + 1].append(cy)
                    elif len(bits) - k >= 2:
                        s_, cy = nl.ha(bits[k], bits[k + 1]); k += 2
                        new[c].append(s_)
                        if c + 1 < n:
                            new[c + 1].append(cy)
                    else:
                        break
                new[c].extend(bits[k:])
            cols = new
        errs = None
    else:
        cols, errs = MX._reduce_approx_4_2(nl, cols, ac, rule == "unbiased", 0)
    if rec == "or_based" and errs:
        for c in range(max(0, ac - 2), ac):
            if errs[c] and c + 1 < len(cols):
                cols[c + 1].append(nl.wire(" | ".join(errs[c]), "t"))
    elif rec == "compensation_module":
        _add_const(cols, (1 << max(0, ac - 2)) % (1 << (2 * w)))
    add_lines, add_text = final_add(nl, cols, pins, "cpa")
    text = [f"// approximate_compressor_tree: {cell} realized by the {rule} rule over the low {ac} columns, error recovery {rec}"
            + " (the ArithmeticError gate governs)",
            f"module {name} (input logic [{w-1}:0] a, input logic [{w-1}:0] b, output logic [{2*w-1}:0] p);"]
    text += nl.render()
    text += add_lines
    text.append("endmodule")
    return "\n".join(text) + "\n" + add_text


def approximate_booth_sv(w: int, signed: bool, pins: dict, name: str) -> str:
    """approximate_booth: radix-4 Booth rows whose partial-product bits in
    the low `approx_encoder_columns` columns come from a simplified
    encoder (the digit's +-2 cases folded into +-1: the ABE styles), a
    radix-8 form with the hard multiple 3a truncated in the low
    columns, or digits rounded to powers of two."""
    radix = str(_pin(pins, "radix", 4))
    cols_ap = max(0, min(_ipin(pins, "approx_encoder_columns", w // 2), 2 * w - 1))
    enc = str(_pin(pins, "encoder", "abe1"))
    nl = Netlist()
    from chialu.targets.rtl.families.mul import pp_booth
    r = 8 if radix == "8" else 4
    cols, extra = pp_booth(nl, w, signed, r, "prevention_constant", "ones_complement_plus_neg_bit", "cpa_precompute")
    # the approximation: in the low columns every partial-product bit is replaced by a simplified selection
    # (the multiplicand bit gated by the digit's magnitude, the sign handled by the row's neg bit as usual)
    if enc in ("abe1", "abe2") and cols_ap > 0:
        # the exact bit is ((one & a_j) | (two & a_(j-1))) ^ neg; abe1 drops the doubled term, abe2 reads
        # the doubled term from the same operand bit (the magnitude flag one | two), both keep the negation
        exprs = dict(nl.assigns)
        rewritten = {}
        for c in range(min(cols_ap, len(cols))):
            new_bits = []
            for b_ in cols[c]:
                e = exprs.get(b_, "")
                if b_.startswith("pp") and " | (" in e and e.endswith(")") is False and " ^ " in e:
                    pass
                if b_.startswith("pp") and " ^ " in e and e.startswith("(("):
                    head, negv = e.rsplit(" ^ ", 1)
                    inner = head.strip()[1:-1]                     # (one & a_j) | (two & a_(j-1))
                    t1, t2 = inner.split(" | ", 1)
                    if enc == "abe1":
                        ne = f"{t1} ^ {negv}"
                    else:
                        sel2 = t2.strip()[1:-1].split(" & ")[0]
                        aj = t1.strip()[1:-1].split(" & ")[1]
                        ne = f"({t1} | ({sel2} & {aj})) ^ {negv}"
                    if b_ not in rewritten:
                        rewritten[b_] = nl.wire(ne, "ab")
                    new_bits.append(rewritten[b_])
                else:
                    new_bits.append(b_)
            cols[c] = new_bits
    cols = reduce(nl, cols, "dadda", "3_2")
    add_lines, add_text = final_add(nl, cols, pins, "cpa")
    a3 = ""
    if r == 8:
        # the hard multiple 3a: exact, truncated in the low columns, or rounded to the power of two 4a
        n1 = w + (0 if signed else 1)
        exact3 = "a_ext + {a_ext[" + str(n1) + ":0], 1'b0}"
        if enc == "truncated_hard_multiple":
            m3 = f"({exact3}) & ~((1 << {cols_ap // 2}) - 1)"
        elif enc == "rounded_high_radix_digit":
            m3 = "{a_ext[" + str(n1 - 1) + ":0], 2'b0}"
        else:
            m3 = exact3
        a3 = (f"  logic [{n1+1}:0] a_ext, a3;\n  assign a_ext = " + (f"{{{{2{{a[{w-1}]}}}}, a}}" if signed else "{2'b0, a}") + ";\n"
              f"  assign a3 = {m3};\n")
    text = [f"// approximate_booth: radix-{r} rows, {enc} in the low {cols_ap} columns (the ABE styles fold the digit's +-2 into +-1 "
            f"by an or of the row terms; the truncated hard multiple and the digit rounded to 4a apply to radix 8) (the ArithmeticError gate governs)",
            f"module {name} (input logic [{w-1}:0] a, input logic [{w-1}:0] b, output logic [{2*w-1}:0] p);"]
    if extra:
        text.append(extra)
    if a3:
        text.append(a3.rstrip("\n"))
    text += nl.render()
    text += add_lines
    text.append("endmodule")
    return "\n".join(text) + "\n" + add_text


# ---- dividers ------------------------------------------------------------------------------
def _div_shift(m, fam: str, spins: dict, W: int, src: str, amt: str, aw_in: int, op: int, out: str, comment: str) -> str:
    """out (W bits) = src shifted by amt (aw_in bits) through the shifter
    family's library module, a shift by W or more giving zeros; the
    language's shift when the family has no module."""
    from chialu.targets.rtl import families as FAM
    f = fam
    if f == "butterfly_network" and W & (W - 1):
        f = "barrel_mux_tree"
    mod = FAM.shifter_module(f, spins, W)
    m.wire(out, W)
    if mod is None:
        m.assign(out, f"{src} {'<<' if op == 0 else '>>'} {amt}")
        return out
    aw = _clog2(W)
    big = (1 << aw_in) > W
    if big:
        m.wire(f"{out}_big", expr=f"{amt} >= {W}")
        m.wire(f"{out}_am", aw, expr=f"{out}_big ? {aw}'d0 : {amt}[{aw-1}:0]" if aw_in > aw else f"{out}_big ? {aw}'d0 : {amt}")
    else:
        m.wire(f"{out}_am", aw, expr=f"{{{{({aw}-{aw_in}){{1'b0}}}}, {amt}}}" if aw_in < aw else amt)
    y = f"{out}_y" if big else out
    if big:
        m.wire(y, W)
    if mod.text:
        m.extra.append(mod.text)
    ps = ", ".join(f".{k}({v})" for k, v in mod.params.items())
    m.n += 1
    m.lines.append(f"  // {comment}")
    m.lines.append(f"  {mod.name} " + (f"#({ps}) " if ps else "") + f"u{m.n} (.a({src}), .amt({out}_am), .op(3'd{op}), .y({y}), .sticky());")
    if big:
        m.assign(out, f"{out}_big ? {W}'d0 : {y}")
    return out


def approximate_recurrence_sv(N: int, D: int, Q: int, pins: dict, name: str) -> str:
    """The restoring array of radix 2, 4 or 8 (a stage takes log2(radix)
    quotient bits: the residual against the divisor's multiples, the
    odd multiples from the multiple_adder slot, the largest that fits
    selected) with its low `replaced_depth` stages carrying inexact
    subtractor cells (axsc1: the difference as the xor of the operands
    and no borrow chain; axsc2: the borrow from the operands only; axsc3:
    the difference from the operands only with an exact borrow) or
    pruned (adaptive_pruning: the low quotient bits zero)."""
    depth = max(0, min(_ipin(pins, "replaced_depth", 4), Q))
    cell = str(_pin(pins, "cell", "axsc1"))
    prune = _bpin(pins, "adaptive_pruning")
    r = _ipin(pins, "radix", 2)
    lr = {2: 1, 4: 2, 8: 3}.get(r, 1)
    afam, apins = _slot(pins, "multiple_adder", "ripple_carry")
    from chialu.targets.rtl.families.div import Mod as DMod, _initial_residual
    m = DMod(name, f"approximate_recurrence: the radix-{r} restoring array, the low {depth} quotient bits' stages with {cell} cells"
                   + (" pruned (their quotient bits zero)" if prune else "")
                   + (f", the divisor's odd multiples by {afam}" if r > 2 else "") + " (the ArithmeticError gate governs)")
    m.port("input", "a", N)
    m.port("input", "b", D)
    m.port("output", "q", Q)
    m.port("output", "r", D)
    RW = D + lr
    m.wire("bx", RW, expr=f"{{{{{lr}{{1'b0}}}}, b}}")
    # the divisor's multiples 1..r-1 (the odd ones beyond 1 through the adder slot)
    mult = {1: "bx"}
    for j in range(2, r):
        if j % 2 == 0:
            m.wire(f"bm{j}", RW, expr=f"bx << {j.bit_length() - 1}" if j & (j - 1) == 0 else f"bm{j // 2} << 1")
        else:
            m.wire(f"bm{j}", RW + 1)
            if not m.lib("adder", afam, apins, RW, f".a(bm{j-1}), .b(bx), .cin(1'b0), .s(bm{j}[{RW-1}:0]), .cout(bm{j}[{RW}])",
                         f"the divisor's multiple {j} ({afam})"):
                m.assign(f"bm{j}", f"{{1'b0, bm{j-1}}} + {{1'b0, bx}}")
        mult[j] = f"bm{j}" if j % 2 == 0 else f"bm{j}[{RW-1}:0]"
    _initial_residual(m, "r_0", "a", N, Q, RW)
    # the quotient bits from the top in groups of lr (the last group holds the rest)
    groups = []
    hi = Q
    while hi > 0:
        lo = max(0, hi - lr)
        groups.append((hi - 1, lo))
        hi = lo
    for i, (top, bot) in enumerate(groups):
        nb = top - bot + 1
        approx = bot < depth
        bits = f"a[{top}:{bot}]" if nb > 1 else f"a[{top}]"
        m.wire(f"sh_{i+1}", RW, expr=f"{{r_{i}[{RW-1-nb}:0], {bits}}}")
        if approx and prune:
            m.wire(f"r_{i+1}", RW, expr=f"sh_{i+1}")
            m.assign(f"q[{top}:{bot}]" if nb > 1 else f"q[{top}]", f"{nb}'d0")
            continue
        nm = (1 << nb) - 1                                   # the multiples this group compares against
        for j in range(1, nm + 1):
            y = mult[j]
            if approx and cell in ("axsc1", "axsc2", "axsc3"):
                # a ripple-borrow subtractor row whose low half cells are inexact: axsc1 drops the borrow-in from
                # both outputs, axsc2 keeps the difference and simplifies the borrow, axsc3 keeps the borrow and
                # drops the borrow-in from the difference
                m.wire(f"bo_{i+1}_{j}", RW + 1)
                m.assign(f"bo_{i+1}_{j}[0]", "1'b0")
                m.wire(f"t_{i+1}_{j}", RW)
                half = RW // 2
                for k in range(RW):
                    x, yk, bi = f"sh_{i+1}[{k}]", f"{y}[{k}]", f"bo_{i+1}_{j}[{k}]"
                    if k < half and cell == "axsc1":
                        m.assign(f"t_{i+1}_{j}[{k}]", f"{x} ^ {yk}")
                        m.assign(f"bo_{i+1}_{j}[{k+1}]", f"~{x} & {yk}")
                    elif k < half and cell == "axsc2":
                        m.assign(f"t_{i+1}_{j}[{k}]", f"{x} ^ {yk} ^ {bi}")
                        m.assign(f"bo_{i+1}_{j}[{k+1}]", f"(~{x} & {yk}) | ({yk} & {bi})")
                    elif k < half:
                        m.assign(f"t_{i+1}_{j}[{k}]", f"{x} ^ {yk}")
                        m.assign(f"bo_{i+1}_{j}[{k+1}]", f"(~{x} & {yk}) | (~({x} ^ {yk}) & {bi})")
                    else:
                        m.assign(f"t_{i+1}_{j}[{k}]", f"{x} ^ {yk} ^ {bi}")
                        m.assign(f"bo_{i+1}_{j}[{k+1}]", f"(~{x} & {yk}) | (~({x} ^ {yk}) & {bi})")
                m.wire(f"ge_{i+1}_{j}", expr=f"~bo_{i+1}_{j}[{RW}]")
            else:
                m.wire(f"t_{i+1}_{j}", RW)
                m.wire(f"ge_{i+1}_{j}")
                m.wire(f"nb_{i+1}_{j}", RW, expr=f"~{y}")
                m.assign(f"{{ge_{i+1}_{j}, t_{i+1}_{j}}}", f"{{1'b0, sh_{i+1}}} + {{1'b0, nb_{i+1}_{j}}} + 1'b1")
        # the largest multiple that fits (the comparisons nest: ge_j implies ge_(j-1))
        sel = " : ".join(f"ge_{i+1}_{j} ? t_{i+1}_{j}" for j in range(nm, 0, -1)) + f" : sh_{i+1}"
        m.wire(f"r_{i+1}", RW, expr=sel)
        dig = " : ".join(f"ge_{i+1}_{j} ? {nb}'d{j}" for j in range(nm, 0, -1)) + f" : {nb}'d0"
        m.assign(f"q[{top}:{bot}]" if nb > 1 else f"q[{top}]", dig)
    m.assign("r", f"r_{len(groups)}[{D-1}:0]")
    return m.render()


def approximate_functional_sv(N: int, D: int, Q: int, pins: dict, name: str) -> str:
    method = str(_pin(pins, "method", "truncated_reciprocal_multiply"))
    kin = max(2, min(_ipin(pins, "segment_or_lut_width", 6), D - 1))
    bias = _bpin(pins, "bias_correction")
    lod, shf = _slot(pins, "lod", "lzd_cell_tree"), _slot(pins, "shifter", "barrel_mux_tree")
    mfam, mpins = _slot(pins, "multiplier", "direct_pp_parallel")
    sfam, spins = _slot(pins, "seed_table", "monolithic_rom")
    from chialu.targets.rtl.families import div as DV
    m = DV.Mod(name, f"approximate_functional ({method}, {kin} bits" + (", bias corrected" if bias else "") + "): "
                     f"the quotient estimate without the exact correction; the leading zeros by {lod[0]}, the shifts by "
                     f"{shf[0]}, the products by {mfam}" + (f", the seed table {sfam}" if method not in ("dynamic_segment_exact_core", "log_subtract_corrected") else "")
                     + " (the ArithmeticError gate governs)")
    m.port("input", "a", N)
    m.port("input", "b", D)
    m.port("output", "q", Q)
    m.port("output", "r", D)
    npins = {"norm.lzc.family": lod[0], **{"norm.lzc." + k: v for k, v in lod[1].items()}}
    # the divisor normalized (its leading zeros by the lod slot, the shift by the shifter slot)
    LWD = D.bit_length()
    SW = _clog2(D)
    m.wire("lz", LWD)
    if not m.lib("lzc", lod[0], lod[1], D, ".a(b), .n(lz)", f"the divisor's leading zeros ({lod[0]})"):
        m.raw(f"  always_comb begin lz = {LWD}'d{D}; for (int k = {D-1}; k >= 0; k = k - 1) if (b[k]) begin lz = {LWD}'d{D-1} - k[{LWD-1}:0]; break; end end")
    m.wire("lzs", SW, expr=f"lz[{SW-1}:0]")
    _div_shift(m, shf[0], shf[1], D, "b", "lzs", SW, 0, "dn", f"the divisor normalized ({shf[0]})")
    dn = "dn"
    fn = DV._Fn("reciprocal")
    LW = N.bit_length()

    def dividend_lz():
        m.wire("lza", LW)
        if not m.lib("lzc", lod[0], lod[1], N, ".a(a), .n(lza)", f"the dividend's leading zeros ({lod[0]})"):
            m.raw(f"  always_comb begin lza = {LW}'d{N}; for (int k = {N-1}; k >= 0; k = k - 1) if (a[k]) begin lza = {LW}'d{N-1} - k[{LW-1}:0]; break; end end")
        _div_shift(m, shf[0], shf[1], N, "a", "lza", LW, 0, "an", f"the dividend normalized ({shf[0]})")

    if method == "dynamic_segment_exact_core":
        # AAXD: windows of kin bits at both operands' leading ones through an exact small restoring divider
        dividend_lz()
        wa = min(N, 2 * kin)
        m.wire("wina", wa, expr=f"an[{N-1}:{N-wa}]")
        m.wire("winb", kin, expr=f"dn[{D-1}:{D-kin}]")
        cn, ct = DV.div_sv(wa, kin, wa + kin, "restoring_nonrestoring", {}, name=f"{name}_core", S=kin)
        m.extra.append(ct)
        m.wire("qc", wa + kin)
        m.wire("rc", kin)
        m.raw(f"  {cn} u_core (.a(wina), .b(winb), .q(qc), .r(rc));")
        # q = qc 2^(shift): the windows' scales: a's by (N - wa - lza), b's by (D - kin - lzs)
        PW = N + D + kin + 2
        m.wire("qe", PW, expr=f"{{{{({PW}-{wa+kin}){{1'b0}}}}, qc}}")
        m.wire("sh", LW + 3, signed=True, expr=f"$signed({{3'b0, {LW}'d{N - wa}}}) - $signed({{3'b0, lza}}) - $signed({{3'b0, {LW}'d{D - kin}}}) + $signed({{{{({LW+3}-{SW}){{1'b0}}}}, lzs}}) - {LW+3}'sd{kin}")
        m.wire("shm", LW + 3, expr="sh[%d] ? -sh : sh" % (LW + 2))
        _div_shift(m, shf[0], shf[1], PW, "qe", "shm", LW + 3, 0, "qsl", f"the window quotient to its scale, leftwards ({shf[0]})")
        _div_shift(m, shf[0], shf[1], PW, "qe", "shm", LW + 3, 1, "qsr", f"the window quotient to its scale, rightwards ({shf[0]})")
        m.wire("qs", PW, expr=f"sh[{LW+2}] ? qsr : qsl")
        m.wire("q1", Q + 1, expr=f"qs[{Q}:0]")
    elif method == "log_subtract_corrected":
        # INZeD: the logarithms of both operands by Mitchell's line, subtracted, the antilog by a shift, with a
        # bias constant on the fraction
        dividend_lz()
        F = max(N, D) - 1
        m.wire("fa", F + 1, expr=f"{{1'b0, an}} << {F + 1 - N}" if F + 1 > N else f"{{1'b0, an[{N-2}:0]}}")
        m.wire("fb", F + 1, expr=f"{{1'b0, dn}} << {F + 1 - D}" if F + 1 > D else f"{{1'b0, dn[{D-2}:0]}}")
        m.wire("fd", F + 2, signed=True, expr=f"$signed({{1'b0, fa[{F-1}:0]}}) - $signed({{1'b0, fb[{F-1}:0]}})" + (f" + {F+2}'sd{1 << max(0, F - 4)}" if bias else ""))
        m.wire("neg", expr=f"fd[{F+1}]")
        # the antilog by Mitchell's line: 2^x ~ 1 + x on [0, 1); a negative x is 2^(x + 1) / 2 ~ 1 + x / 2
        m.wire("fdh", F + 2, signed=True, expr="fd >>> 1")
        m.wire("mant", F + 2, expr=f"{{2'b01, {F}'d0}} + (neg ? fdh : fd)")
        # q = 2^((N-1-lza) - (D-1-lzs)) 2^fd = mant 2^(ka - kb) / 2^F
        PW = N + D + F + 4
        m.wire("ka", LW, expr=f"{LW}'d{N-1} - lza")
        m.wire("kb", LW, expr=f"{LW}'d{D-1} - {{{{({LW}-{SW}){{1'b0}}}}, lzs}}")
        m.wire("kdiff", LW + 2, signed=True, expr="$signed({2'b0, ka}) - $signed({2'b0, kb})")
        m.wire("kdm", LW + 2, expr=f"kdiff[{LW+1}] ? -kdiff : kdiff")
        m.wire("me", PW, expr=f"{{{{({PW}-{F+2}){{1'b0}}}}, mant}}")
        _div_shift(m, shf[0], shf[1], PW, "me", "kdm", LW + 2, 0, "qsl", f"the antilog, leftwards ({shf[0]})")
        _div_shift(m, shf[0], shf[1], PW, "me", "kdm", LW + 2, 1, "qsr", f"the antilog, rightwards ({shf[0]})")
        m.wire("qs", PW, expr=f"kdiff[{LW+1}] ? qsr : qsl")
        m.wire("q1", Q + 1, expr=f"qs[{F + Q}:{F}]")
    else:
        # a reciprocal seed of the table width (SEERAD's rounded divisor with a LUT, TruncApp's truncated
        # reciprocal product, SAADI's short Goldschmidt iteration on the seed); the seed_table slot's family
        P, eps0 = DV.seed_sv(m, sfam, spins, dn, D, kin, "x0", fn)
        F = P - 1
        if method == "iterative_quasi_convergence":
            # one or two Goldschmidt steps at the seed's own precision (F fraction bits, two integer bits)
            iters = max(1, min(2, _ipin(pins, "iterations", 1)))
            XW2 = F + 2
            m.wire("xw0", XW2, expr="{1'b0, x0}")
            x = "xw0"
            for k in range(iters):
                m.umul(mfam, mpins, x, XW2, dn, D, f"dx{k}", f"the divisor times the reciprocal estimate ({mfam})")
                m.wire(f"f{k}", XW2, expr=f"{{2'b10, {F}'d0}} - dx{k}[{F + D + 1}:{D}]")
                m.umul(mfam, mpins, x, XW2, f"f{k}", XW2, f"xn{k}", f"the estimate refined ({mfam})")
                m.wire(f"x{k+1}", XW2, expr=f"xn{k}[{2*F+1}:{F}]")
                x = f"x{k+1}"
            P = XW2 + 1                                  # the reciprocal now carries F fraction bits in XW2 bits
        else:
            x = "x0"
        # the truncated dividend: its top kin + 2 bits under truncated_reciprocal_multiply, else the whole
        if method == "truncated_reciprocal_multiply":
            dividend_lz()
            ta = min(N, kin + 2)
            m.wire("atn", N, expr=f"an & {{{{{ta}{{1'b1}}}}, {{{N-ta}{{1'b0}}}}}}" if N > ta else "an")
            _div_shift(m, shf[0], shf[1], N, "atn", "lza", LW, 1, "at", f"the truncated dividend back to its place ({shf[0]})")
            m.umul(mfam, mpins, "at", N, x, P, "ax", f"the dividend times the reciprocal ({mfam})")
        else:
            m.umul(mfam, mpins, "a", N, x, P, "ax", f"the dividend times the reciprocal ({mfam})")
        # q = a x 2^lzs / 2^(F + D)
        PW = N + P + D
        m.wire("axe", PW, expr=f"{{{{({PW}-{N+P}){{1'b0}}}}, ax}}")
        _div_shift(m, shf[0], shf[1], PW, "axe", "lzs", SW, 0, "axs", f"the quotient to the divisor's scale ({shf[0]})")
        m.wire("q1", Q + 1, expr=f"axs[{F + D + Q}:{F + D}]" + (f" + (axs[{F + D - 1}] ? 1'b1 : 1'b0)" if bias else ""))
    m.umul(mfam, mpins, "q1", Q + 1, "b", D, "qb", f"the quotient times the divisor for the remainder ({mfam})")
    m.wire("rr", N + 2, signed=True, expr=f"$signed({{2'b0, a}}) - $signed(qb[{N+1}:0])")
    m.assign("q", f"q1[{Q-1}:0]")
    m.assign("r", f"rr[{D-1}:0]")
    return m.render()


RUNTIME_FAMILIES = {"accuracy_configurable": "the mode selects the correction stages (or the dropped low "
                                                "blocks) of the ACA structure",
                    "dynamic_segment": "the mode scales the window the operands keep (runtime width scaling)"}


def approx_sv(kind: str, family: str, pins: dict, width: int, signed: bool = False, name: str | None = None,
              N=None, D=None, Q=None, amodes: int = 0) -> tuple:
    """(name, text) of an approximate family: kind adder / multiplier /
    divider. `amodes` is the unit's accuracy-mode count under
    `accuracy_ctl: runtime`: a family of RUNTIME_FAMILIES then renders one
    structure whose operating mode the `amode` port selects, and its
    module name carries the mode count, since it is a different netlist
    from the static point's."""
    pins = pins or {}
    tag = _tag(pins)
    rt = f"_rt{amodes}" if amodes and family in RUNTIME_FAMILIES else ""
    if kind == "adder":
        name = name or f"fam_adder_{family}_w{width}{tag}{rt}"
        if family == "segmented_carry_speculative":
            return name, segmented_speculative_sv(width, pins, name)
        if family == "lower_part_approximate":
            return name, lower_part_sv(width, pins, name)
        if family == "accuracy_configurable":
            return name, accuracy_configurable_sv(width, pins, name, amodes)
    elif kind == "multiplier":
        name = name or f"fam_mul_{family}_ax_w{width}_{'s' if signed else 'u'}{tag}{rt}"
        gen = {"truncated_fixed_width": truncated_ladder_sv, "dynamic_segment": dynamic_segment_sv, "operand_rounding": operand_rounding_sv,
               "logarithmic": logarithmic_sv, "pp_perforation": perforation_sv, "approximate_compressor_tree": compressor_tree_sv,
               "approximate_booth": approximate_booth_sv}.get(family)
        if gen:
            if family == "dynamic_segment":
                return name, dynamic_segment_sv(width, signed, pins, name, amodes)
            return name, gen(width, signed, pins, name)
    elif kind == "divider":
        N, D, Q = N or width, D or width, Q or width
        name = name or f"fam_div_{family}_n{N}d{D}q{Q}{tag}"
        if family == "approximate_recurrence":
            return name, approximate_recurrence_sv(N, D, Q, pins, name)
        if family == "approximate_functional":
            return name, approximate_functional_sv(N, D, Q, pins, name)
    raise ValueError(f"no module for the approximate {kind} family {family}")
