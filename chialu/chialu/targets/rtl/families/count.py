"""The bit-count families as generated modules: popcount_counter_tree,
lzd_cell_tree, prefix_lzc, priority_encoder and trailing_zero
(shift_simd_spaces.bitcount_space, fp_spaces.lzc_space). Every choice of
a family changes the text, and the component slots are library
instances: the popcount's `final_adder` (its node adders and the root
adder), the prefix counter's `counter` (a popcount over the positions
above the leading one), the trailing-zero unit's `lzd` (the detector the
reversed word feeds) and `negation_incrementer` (the ~a + 1 of the
two's-complement isolate).

Interfaces (the lane's and the float datapath's):

    popcount:  (input [W-1:0] a, output [clog2(W+1)-1:0] n)
    lzc, tzc:  (input [W-1:0] a, output [clog2(W+1)-1:0] n), n = W for a zero word

    python3 -m chialu.targets.rtl.families.count --family lzd_cell_tree --width 16 --pins block_primitive=nibble_cell
"""
from __future__ import annotations

import argparse
import sys

from chialu.targets.rtl.families.mul import dedupe_modules

POPCOUNT_FAMILIES = ("popcount_counter_tree",)
LZC_FAMILIES = ("lzd_cell_tree", "prefix_lzc", "priority_encoder")
TZC_FAMILIES = ("trailing_zero",)


def _pin(pins: dict, key: str, default):
    v = pins.get(key, default) if pins else default
    return default if v in (None, "") else v


def _ipin(pins: dict, key: str, default: int) -> int:
    try:
        return int(_pin(pins, key, default))
    except (TypeError, ValueError):
        return default


def _sub(pins: dict, prefix: str) -> dict:
    return {k[len(prefix):]: v for k, v in (pins or {}).items() if k.startswith(prefix)}


def _tag(sub_pins: dict) -> str:
    """A short tag of a component's pins for a module name (empty for none)."""
    if not sub_pins:
        return ""
    import hashlib
    import json
    return "_p" + hashlib.sha1(json.dumps(sub_pins, sort_keys=True, default=str).encode()).hexdigest()[:5]


def _cw(W: int) -> int:
    """The count width: clog2(W + 1)."""
    return max(1, W.bit_length())


def _clog2(n: int) -> int:
    return max(1, (n - 1).bit_length())


class Mod:
    """A module under construction with explicit ports; the library
    instances it holds are appended to `extra`."""

    def __init__(self, name: str, ports: str, comment: str):
        self.name, self.ports, self.comment = name, ports, comment
        self.lines: list = []
        self.extra: list = []
        self.n = 0
        self.k = 0

    def tmp(self, base: str) -> str:
        self.k += 1
        return f"{base}{self.k}"

    def wire(self, name: str, width: int = 1, expr: str | None = None) -> str:
        wd = f"[{width-1}:0] " if width > 1 else ""
        self.lines.append(f"  logic {wd}{name};" + (f" assign {name} = {expr};" if expr is not None else ""))
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

    def adder(self, fam: str, pins: dict, width: int, a: str, b: str, s: str, comment: str, cin: str = "1'b0", cout: str = "") -> None:
        """s (width bits), cout = a + b + cin through the adder family; the
        family is a library one (the caller's slot domain guarantees it).
        An end_around_carry family's native module sums modulo 2^W - 1 (or
        2^W + 1), so it enters through binary_cpa's decode wrapper, which
        restores the binary sum and carry the count tree adds up."""
        from chialu.targets.rtl.families.binary_cpa import adder_module
        m = adder_module(fam, pins, width)
        if m is None:
            raise ValueError(f"the adder family {fam!r} has no library module at {width} bits")
        self.inst(m, f".a({a}), .b({b}), .cin({cin}), .s({s}), .cout({cout})", comment)

    def render(self) -> str:
        head = [f"// {self.comment}", f"module {self.name} ({self.ports});"]
        return "\n".join(head + self.lines + ["endmodule", ""]) + dedupe_modules("".join(self.extra))


def _fa(m: Mod, x: str, y: str, z: str, tag: str) -> tuple:
    """(sum, carry) of a full adder."""
    s = m.wire(m.tmp(f"{tag}_s"), expr=f"{x} ^ {y} ^ {z}")
    c = m.wire(m.tmp(f"{tag}_c"), expr=f"({x} & {y}) | ({x} & {z}) | ({y} & {z})")
    return s, c


def _ha(m: Mod, x: str, y: str, tag: str) -> tuple:
    s = m.wire(m.tmp(f"{tag}_s"), expr=f"{x} ^ {y}")
    c = m.wire(m.tmp(f"{tag}_c"), expr=f"{x} & {y}")
    return s, c


def _or_encode(m: Mod, onehot: list, values: list, width: int, out: str, comment: str) -> str:
    """out (width bits) = the value of the one asserted line: bit b is the OR
    of the lines whose value has bit b set (the one-hot encoder)."""
    m.raw(f"  // {comment}")
    for b in range(width):
        terms = [ln for ln, v in zip(onehot, values) if (v >> b) & 1]
        m.assign(f"{out}[{b}]", " | ".join(terms) if terms else "1'b0")
    return out


# ---- popcount_counter_tree -----------------------------------------------------------------------
PRIMITIVE_BITS = {"full_adder_3_2": 3, "compressor_4_2": 4, "counter_7_3": 7, "lut_rom": 6}


def _count_group(m: Mod, prim: str, bits: list, tag: str) -> list:
    """The count of a group of equal-weight bits by one primitive cell:
    [bit of weight 1, 2, 4, ...] (the list shortens for a short group)."""
    k = len(bits)
    if k == 1:
        return [bits[0]]
    if k == 2:
        s, c = _ha(m, bits[0], bits[1], tag)
        return [s, c]
    if prim == "lut_rom":
        # a value table over the group's bits (a ROM cell), the classic ROM counter stage
        cw = k.bit_length()
        out = m.wire(m.tmp(f"{tag}_rom"), cw)
        m.raw(f"  always_comb begin case ({{{', '.join(reversed(bits))}}})")
        for v in range(1 << k):
            m.raw(f"    {k}'d{v}: {out} = {cw}'d{bin(v).count('1')};")
        m.raw(f"    default: {out} = {cw}'d0;")
        m.raw("  endcase end")
        return [f"{out}[{b}]" for b in range(cw)]
    if prim == "counter_7_3" and k >= 5:
        # the 7:3 counter as four full adders; a short group fills the missing inputs with zeros
        x = list(bits) + ["1'b0"] * (7 - k)
        s1, c1 = _fa(m, x[0], x[1], x[2], tag)
        s2, c2 = _fa(m, x[3], x[4], x[5], tag)
        s3, c3 = _fa(m, s1, s2, x[6], tag)
        s4, c4 = _fa(m, c1, c2, c3, tag)
        return [s3, s4, c4]
    if prim == "compressor_4_2" and k == 4:
        # a 4:2 compressor cell counting four bits: a full adder, then two half adders
        s1, c1 = _fa(m, bits[0], bits[1], bits[2], tag)
        s0, c0 = _ha(m, s1, bits[3], tag)
        s2, c2 = _ha(m, c1, c0, tag)
        return [s0, s2, c2]
    # full adders: three bits at a time, the leftovers by half adders, summed by weight
    cols = _reduce_columns(m, [list(bits)], "full_adder_3_2", tag, final=True)
    return [(c[0] if c else "1'b0") for c in cols][:k.bit_length()]


def _reduce_columns(m: Mod, cols: list, prim: str, tag: str, final: bool = False) -> list:
    """Wallace-style reduction of weight columns (cols[w] is the list of
    lines of weight 2^w) by the primitive's cell until every column holds
    at most two lines (at most one when `final`, by half adders); returns
    the columns."""
    cols = [list(c) for c in cols]
    limit = 1 if final else 2
    guard = 0
    while any(len(c) > limit for c in cols) and guard < 64:
        guard += 1
        nxt: list = [[] for _ in range(len(cols) + 3)]
        for w, col in enumerate(cols):
            col = list(col)
            while len(col) >= 3 and (len(col) > limit or len(col) >= 3):
                if prim == "counter_7_3" and len(col) >= 7:
                    x = [col.pop(0) for _ in range(7)]
                    s1, c1 = _fa(m, x[0], x[1], x[2], tag)
                    s2, c2 = _fa(m, x[3], x[4], x[5], tag)
                    s3, c3 = _fa(m, s1, s2, x[6], tag)
                    s4, c4 = _fa(m, c1, c2, c3, tag)
                    nxt[w].append(s3); nxt[w + 1].append(s4); nxt[w + 2].append(c4)
                elif prim == "compressor_4_2" and len(col) >= 4:
                    # the 4:2 compressor cell: two full adders in series; the first's carry (cout) and the
                    # second's (carry) are lines of the next weight
                    x = [col.pop(0) for _ in range(4)]
                    s1, cout = _fa(m, x[0], x[1], x[2], tag)
                    s, c = _fa(m, s1, x[3], "1'b0", tag)
                    nxt[w].append(s); nxt[w + 1].append(c); nxt[w + 1].append(cout)
                elif prim == "lut_rom" and len(col) >= 4:
                    x = [col.pop(0) for _ in range(min(6, len(col)))]
                    k = len(x)
                    cw = k.bit_length()
                    out = m.wire(m.tmp(f"{tag}_rom"), cw)
                    m.raw(f"  always_comb begin case ({{{', '.join(reversed(x))}}})")
                    for v in range(1 << k):
                        m.raw(f"    {k}'d{v}: {out} = {cw}'d{bin(v).count('1')};")
                    m.raw(f"    default: {out} = {cw}'d0;")
                    m.raw("  endcase end")
                    for b in range(cw):
                        nxt[w + b].append(f"{out}[{b}]")
                else:
                    x = [col.pop(0) for _ in range(3)]
                    s, c = _fa(m, x[0], x[1], x[2], tag)
                    nxt[w].append(s); nxt[w + 1].append(c)
            if final and len(col) == 2:
                s, c = _ha(m, col.pop(0), col.pop(0), tag)
                nxt[w].append(s); nxt[w + 1].append(c)
            nxt[w] = col + nxt[w]
        while len(nxt) > 1 and not nxt[-1]:
            nxt.pop()
        cols = nxt
    return cols


def popcount_sv(W: int, pins: dict, name: str | None = None) -> tuple:
    """(name, text) of the population count of a W-bit word: the bits
    grouped and counted by the counter primitive, the group counts joined
    by tree_shape (a balanced tree of adders, a chain of adders, or a
    Wallace-style column reduction by the primitive's cells into two rows),
    the adders being the `final_adder` slot's family."""
    pins = pins or {}
    shape = str(_pin(pins, "tree_shape", "balanced_tree"))
    prim = str(_pin(pins, "counter_primitive", "full_adder_3_2"))
    fa_fam = str(_pin(pins, "final_adder.family", "ripple_carry"))
    fa_pins = _sub(pins, "final_adder.")
    if prim not in PRIMITIVE_BITS:
        raise ValueError(f"popcount_counter_tree: counter_primitive {prim!r}")
    if shape not in ("balanced_tree", "wallace_style", "linear_chain"):
        raise ValueError(f"popcount_counter_tree: tree_shape {shape!r}")
    CW = _cw(W)
    name = name or f"fam_count_popcount_{shape}_{prim}_{fa_fam}{_tag(fa_pins)}_w{W}"
    m = Mod(name, f"input logic [{W-1}:0] a, output logic [{CW-1}:0] n",
            f"popcount_counter_tree ({shape}, {prim}, adders {fa_fam}): the count of the ones of a {W}-bit word")
    bits = [f"a[{i}]" for i in range(W)]
    if shape == "wallace_style":
        # the columns of equal weight reduced by the primitive's cells until two rows remain, the final adder
        cols = _reduce_columns(m, [bits], prim, "w")
        cols = cols[:CW] + [[] for _ in range(CW - len(cols))]
        ra = m.wire("row_a", CW, expr="{" + ", ".join((c[0] if len(c) > 0 else "1'b0") for c in reversed(cols)) + "}")
        rb = m.wire("row_b", CW, expr="{" + ", ".join((c[1] if len(c) > 1 else "1'b0") for c in reversed(cols)) + "}")
        m.adder(fa_fam, fa_pins, CW, ra, rb, "n", f"the final adder ({fa_fam}) over the two rows")
        return name, m.render()
    # the group counts by the primitive, then adders in a tree or a chain
    K = PRIMITIVE_BITS[prim]
    counts = []
    for g, i in enumerate(range(0, W, K)):
        outs = _count_group(m, prim, bits[i:i + K], f"g{g}")
        cw = len(outs)
        v = m.wire(f"gc{g}", cw, expr="{" + ", ".join(reversed(outs)) + "}" if cw > 1 else outs[0])
        counts.append((v, cw))
    k = 0

    def add(x, y):
        nonlocal k
        (xa, wa), (ya, wb) = x, y
        w = max(wa, wb)
        k += 1
        xe = xa if wa == w else f"{{{w - wa}'d0, {xa}}}"
        ye = ya if wb == w else f"{{{w - wb}'d0, {ya}}}"
        s = m.wire(f"s{k}", w)
        co = m.wire(f"co{k}")
        m.adder(fa_fam, fa_pins, w, xe, ye, s, f"count adder {k} ({fa_fam}, {w} bits)", cout=co)
        v = m.wire(f"t{k}", w + 1, expr=f"{{{co}, {s}}}")
        return v, w + 1

    if shape == "linear_chain":
        acc = counts[0]
        for c in counts[1:]:
            acc = add(acc, c)
    else:
        level = counts
        while len(level) > 1:
            nxt = [add(level[i], level[i + 1]) for i in range(0, len(level) - 1, 2)]
            if len(level) % 2:
                nxt.append(level[-1])
            level = nxt
        acc = level[0]
    v, w = acc
    m.assign("n", f"{v}[{CW-1}:0]" if w >= CW else f"{{{CW - w}'d0, {v}}}")
    return name, m.render()


# ---- lzd_cell_tree -------------------------------------------------------------------------------
def lzd_cell_tree_sv(W: int, pins: dict, name: str | None = None) -> tuple:
    """(name, text) of the leading-zero count as a tree of cells: pair or
    nibble leaves emit (valid, position), every level merges two children
    into (v_hi | v_lo, v_hi ? {0, p_hi} : {1, p_lo}); the valid flags
    propagate up the tree or come from a flat OR per node; the count is
    the root's position, or (one_hot_shift_controls) a one-hot leading-one
    vector encoded to the count; W for a zero word."""
    pins = pins or {}
    prim = str(_pin(pins, "block_primitive", "pair_cell"))
    form = str(_pin(pins, "output_form", "binary_count"))
    vprop = bool(_pin(pins, "valid_flag_propagation", True))
    if prim not in ("pair_cell", "nibble_cell"):
        raise ValueError(f"lzd_cell_tree: block_primitive {prim!r}")
    if form not in ("binary_count", "one_hot_shift_controls"):
        raise ValueError(f"lzd_cell_tree: output_form {form!r}")
    CW = _cw(W)
    name = name or f"fam_count_lzd_{prim}_{form}_{'vprop' if vprop else 'vflat'}_w{W}"
    m = Mod(name, f"input logic [{W-1}:0] a, output logic [{CW-1}:0] n",
            f"lzd_cell_tree ({prim}, {form}, valid flags {'propagated' if vprop else 'flat'}): the leading zeros of a {W}-bit word")
    # msb-first order: leaf bit j is a[W-1-j]
    if form == "one_hot_shift_controls":
        # the one-hot leading-one vector (the shift controls a one-hot shifter takes), then the encoder
        m.wire("f", W)
        for j in range(W):
            above = " | ".join(f"a[{W-1-i}]" for i in range(j)) if j else "1'b0"
            m.assign(f"f[{j}]", f"a[{W-1-j}] & ~({above})")
        m.wire("v", expr=f"|a")
        enc = m.wire("enc", CW)
        _or_encode(m, [f"f[{j}]" for j in range(W)], list(range(W)), CW, enc, "the one-hot vector encoded to the count")
        m.assign("n", f"v ? {enc} : {CW}'d{W}")
        return name, m.render()
    leaf = 2 if prim == "pair_cell" else 4
    lb = 1 if leaf == 2 else 2
    L = 0
    while leaf << L < W:
        L += 1
    WP = leaf << L
    nleaf = WP // leaf

    def bit(j):
        return f"a[{W-1-j}]" if j < W else "1'b0"

    V = [[None] * (nleaf >> l) for l in range(L + 1)]
    P = [[None] * (nleaf >> l) for l in range(L + 1)]
    # the leaves
    for i in range(nleaf):
        bs = [bit(i * leaf + t) for t in range(leaf)]
        V[0][i] = m.wire(f"v0_{i}", expr=" | ".join(bs))
        if leaf == 2:
            P[0][i] = m.wire(f"p0_{i}", expr=f"~{bs[0]}")
        else:
            # the nibble's leading-one position by priority
            P[0][i] = m.wire(f"p0_{i}", 2, expr=f"{bs[0]} ? 2'd0 : {bs[1]} ? 2'd1 : {bs[2]} ? 2'd2 : 2'd3")
    for l in range(1, L + 1):
        pw = lb + l
        span = leaf << l
        for i in range(nleaf >> l):
            hi, lo = V[l - 1][2 * i], V[l - 1][2 * i + 1]
            if vprop:
                V[l][i] = m.wire(f"v{l}_{i}", expr=f"{hi} | {lo}")
            else:
                V[l][i] = m.wire(f"v{l}_{i}", expr=" | ".join(bit(i * span + t) for t in range(span)))
            P[l][i] = m.wire(f"p{l}_{i}", pw, expr=f"{hi} ? {{1'b0, {P[l-1][2*i]}}} : {{1'b1, {P[l-1][2*i+1]}}}")
    root_v, root_p, pw = V[L][0], P[L][0], lb + L
    pe = root_p if pw >= CW else f"{{{CW - pw}'d0, {root_p}}}"
    if pw > CW:
        pe = f"{root_p}[{CW-1}:0]"
    m.assign("n", f"{root_v} ? {pe} : {CW}'d{W}")
    return name, m.render()


# ---- prefix_lzc ----------------------------------------------------------------------------------
def _prefix_or(m: Mod, x: list, topo: str, tag: str) -> list:
    """The inclusive prefix OR of a list of lines (index 0 first) by a
    prefix network topology."""
    n = len(x)
    if topo == "kogge_stone":
        cur = list(x)
        d = 1
        lvl = 0
        while d < n:
            nxt = list(cur)
            for i in range(d, n):
                nxt[i] = m.wire(f"{tag}_ks{lvl}_{i}", expr=f"{cur[i]} | {cur[i-d]}")
            cur, d, lvl = nxt, d * 2, lvl + 1
        return cur
    if topo == "sklansky":
        cur = list(x)
        d = 1
        lvl = 0
        while d < n:
            nxt = list(cur)
            for i in range(n):
                if (i // d) % 2 == 1:
                    src = (i // d) * d - 1
                    nxt[i] = m.wire(f"{tag}_sk{lvl}_{i}", expr=f"{cur[i]} | {cur[src]}")
            cur, d, lvl = nxt, d * 2, lvl + 1
        return cur
    if topo == "brent_kung":
        cur = list(x)
        d = 1
        lvl = 0
        while d < n:                                     # the up-sweep
            nxt = list(cur)
            for i in range(2 * d - 1, n, 2 * d):
                nxt[i] = m.wire(f"{tag}_bu{lvl}_{i}", expr=f"{cur[i]} | {cur[i-d]}")
            cur, d, lvl = nxt, d * 2, lvl + 1
        d //= 2
        while d >= 1:                                    # the down-sweep
            nxt = list(cur)
            for i in range(3 * d - 1, n, 2 * d):
                nxt[i] = m.wire(f"{tag}_bd{lvl}_{i}", expr=f"{cur[i]} | {cur[i-d]}")
            cur, d, lvl = nxt, d // 2, lvl + 1
        return cur
    raise ValueError(f"prefix_lzc: prefix_topology {topo!r}")


def prefix_lzc_sv(W: int, pins: dict, name: str | None = None) -> tuple:
    """(name, text) of the leading-zero count as a prefix computation: a
    prefix OR from the msb marks every position at or below the leading
    one; the count is the population count of the unmarked positions
    (through the `counter` slot's popcount family) or, under
    lookahead_flags, the encoding of the leading-one flags (marked and
    the position above unmarked) by one OR tree per count bit."""
    pins = pins or {}
    topo = str(_pin(pins, "prefix_topology", "kogge_stone"))
    cform = str(_pin(pins, "count_form", "popcount_of_complement"))
    if cform not in ("popcount_of_complement", "lookahead_flags"):
        raise ValueError(f"prefix_lzc: count_form {cform!r}")
    CW = _cw(W)
    cnt_fam = str(_pin(pins, "counter.family", "popcount_counter_tree"))
    cnt_pins = _sub(pins, "counter.")
    ctag = "".join(w[0] for w in cnt_fam.split("_")) + _tag(cnt_pins)
    name = name or f"fam_count_prefix_lzc_{topo}_{'pcomp_' + ctag if cform == 'popcount_of_complement' else 'flags'}_w{W}"
    m = Mod(name, f"input logic [{W-1}:0] a, output logic [{CW-1}:0] n",
            f"prefix_lzc ({topo} prefix OR, {cform}): the leading zeros of a {W}-bit word")
    x = [m.wire(f"x{j}", expr=f"a[{W-1-j}]") for j in range(W)]      # msb first
    pre = _prefix_or(m, x, topo, "p")                                   # pre[j]: a one at msb-first index <= j
    if cform == "popcount_of_complement":
        from chialu.targets.rtl import families as FAM
        z = m.wire("zeros", W, expr="{" + ", ".join(f"~{pre[j]}" for j in range(W)) + "}")
        cm = FAM.popcount_module(cnt_fam, cnt_pins, W)
        if cm is None:
            raise ValueError(f"prefix_lzc: the counter family {cnt_fam!r} has no popcount module")
        m.inst(cm, f".a({z}), .n(n)", f"the count of the positions above the leading one ({cnt_fam})")
        return name, m.render()
    f = [m.wire(f"f{j}", expr=f"{pre[j]}" + (f" & ~{pre[j-1]}" if j else "")) for j in range(W)]
    enc = m.wire("enc", CW)
    _or_encode(m, f, list(range(W)), CW, enc, "the leading-one flags encoded by one OR tree per count bit")
    m.assign("n", f"{pre[W-1]} ? {enc} : {CW}'d{W}")
    return name, m.render()


# ---- priority_encoder ----------------------------------------------------------------------------
def priority_encoder_sv(W: int, pins: dict, name: str | None = None) -> tuple:
    """(name, text) of the leading-one position by a priority kill chain
    with lookahead: the bits in groups of G, a kill chain inside every
    group, a lookahead line per group, and `levels` levels of grouping over
    the lookahead lines (the chain among groups is broken by a macro
    lookahead at every level above the first); the output is the binary
    position resolved directly, or a one-hot vector encoded after."""
    pins = pins or {}
    G = max(2, _ipin(pins, "lookahead_group", 4))
    levels = max(1, min(3, _ipin(pins, "levels", 1)))
    form = str(_pin(pins, "output_form", "direct_binary"))
    if form not in ("one_hot_then_encode", "direct_binary"):
        raise ValueError(f"priority_encoder: output_form {form!r}")
    CW = _cw(W)
    name = name or f"fam_count_priority_encoder_g{G}_l{levels}_{form}_w{W}"
    m = Mod(name, f"input logic [{W-1}:0] a, output logic [{CW-1}:0] n",
            f"priority_encoder (groups of {G}, {levels} lookahead level{'s' if levels > 1 else ''}, {form}): the leading zeros of a {W}-bit word")
    # msb-first index j = W-1-i; x[j] is the bit
    x = [f"a[{W-1-j}]" for j in range(W)]
    # level 1: groups of G with a kill chain inside and a lookahead line (any) per group
    groups = [list(range(g, min(g + G, W))) for g in range(0, W, G)]
    anyg = [m.wire(f"any{gi}", expr=" | ".join(x[j] for j in grp)) for gi, grp in enumerate(groups)]
    # the higher levels: the group lines grouped by G, a lookahead line per macro
    lines = [anyg]
    members = [[[gi] for gi in range(len(groups))]]
    for lv in range(2, levels + 1):
        prev = lines[-1]
        mac = [list(range(g, min(g + G, len(prev)))) for g in range(0, len(prev), G)]
        lines.append([m.wire(f"any{lv}_{k}", expr=" | ".join(prev[i] for i in mk)) for k, mk in enumerate(mac)])
        members.append(mac)
    # the kill of a group: a one in an earlier group. Within a macro the earlier groups are killed by a
    # ripple over the group lines; across macros by the macro lookahead lines (the same recursively).
    def killed_before(level_idx: int, k: int) -> str:
        """The lines that kill entry k of level `level_idx` (msb first): the earlier entries of its macro,
        and the earlier macros through the level above."""
        if level_idx + 1 >= len(lines):
            return " | ".join(lines[level_idx][:k]) if k else "1'b0"
        mac = members[level_idx + 1]
        mk = next(mi for mi, ms in enumerate(mac) if k in ms)
        inner = [lines[level_idx][i] for i in mac[mk] if i < k]
        outer = killed_before(level_idx + 1, mk)
        parts = ([outer] if outer != "1'b0" else []) + inner
        return " | ".join(parts) if parts else "1'b0"

    kill_g = [m.wire(f"kg{gi}", expr=killed_before(0, gi)) for gi in range(len(groups))]
    first_g = [m.wire(f"fg{gi}", expr=f"{anyg[gi]} & ~{kill_g[gi]}") for gi in range(len(groups))]
    # inside a group: the kill chain over its bits
    onehot = []
    for gi, grp in enumerate(groups):
        chain = "1'b0"
        for t, j in enumerate(grp):
            kb = m.wire(f"kb{j}", expr=chain)
            onehot.append(m.wire(f"oh{j}", expr=f"{x[j]} & ~{kb} & {first_g[gi]}"))
            chain = m.wire(f"kc{j}", expr=f"{kb} | {x[j]}")
    v = m.wire("v", expr=" | ".join(anyg))
    if form == "one_hot_then_encode":
        enc = m.wire("enc", CW)
        _or_encode(m, onehot, list(range(W)), CW, enc, "the one-hot leading-one vector encoded to the count")
        m.assign("n", f"v ? {enc} : {CW}'d{W}")
    else:
        # the position resolved directly: the first group's base plus its local offset (a select per group)
        pos = f"{CW}'d{W}"
        for gi in reversed(range(len(groups))):
            grp = groups[gi]
            lw = _clog2(len(grp) + 1)
            local = f"{lw}'d{len(grp) - 1}"
            for t, j in reversed(list(enumerate(grp))):
                local = f"({x[j]} ? {lw}'d{t} : {local})" if t < len(grp) - 1 else local
            lc = m.wire(f"loc{gi}", lw, expr=local)
            pos = f"({first_g[gi]} ? ({CW}'d{grp[0]} + {{{CW - lw}'d0, {lc}}}) : {pos})" if CW > lw else f"({first_g[gi]} ? ({CW}'d{grp[0]} + {lc}) : {pos})"
        m.assign("n", pos)
    return name, m.render()


# ---- trailing_zero -------------------------------------------------------------------------------
def _debruijn(L: int) -> int:
    """A de Bruijn constant of 2^L bits: (low * DB) >> (2^L - L) is distinct
    for every one-hot low (the prefer-one greedy sequence, checked)."""
    n = 1 << L
    seq = [0] * L
    seen = {tuple(seq)}
    while len(seq) < n:
        for b in (1, 0):
            cand = tuple(seq[-(L - 1):] + [b]) if L > 1 else (b,)
            if cand not in seen:
                seen.add(cand)
                seq.append(b)
                break
        else:
            break
    db = int("".join(map(str, seq)), 2)
    idx = {((db << i) & (n - 1 << 0 if False else (1 << n) - 1)) >> (n - L) for i in range(n)}
    if len(idx) != n:
        raise ValueError(f"trailing_zero: no de Bruijn constant for {L} bits")
    return db


def trailing_zero_sv(W: int, pins: dict, name: str | None = None) -> tuple:
    """(name, text) of the trailing-zero count: the word reversed into the
    `lzd` slot's leading-zero detector; or the lowest one isolated (a & -a
    through the `negation_incrementer` slot, or a ripple kill chain) and
    encoded, directly or by a de Bruijn multiply and a table."""
    pins = pins or {}
    strat = str(_pin(pins, "strategy", "reverse_then_lzd"))
    iso = str(_pin(pins, "isolate_circuit", "twos_complement_and"))
    if strat not in ("reverse_then_lzd", "isolate_then_encode", "debruijn_multiply_index"):
        raise ValueError(f"trailing_zero: strategy {strat!r}")
    if iso not in ("twos_complement_and", "ripple_kill_chain"):
        raise ValueError(f"trailing_zero: isolate_circuit {iso!r}")
    CW = _cw(W)
    from chialu.targets.rtl import families as FAM
    if strat == "reverse_then_lzd":
        lzd_fam = str(_pin(pins, "lzd.family", "lzd_cell_tree"))
        lzd_pins = _sub(pins, "lzd.")
        lm = FAM.lzc_module(lzd_fam, lzd_pins, W)
        if lm is None:
            raise ValueError(f"trailing_zero: the lzd family {lzd_fam!r} has no module")
        name = name or f"fam_count_tzc_reverse_{lzd_fam}{_tag(lzd_pins)}_w{W}"
        m = Mod(name, f"input logic [{W-1}:0] a, output logic [{CW-1}:0] n",
                f"trailing_zero (reverse_then_lzd over {lzd_fam}): the word reversed into the leading-zero detector")
        r = m.wire("r", W, expr="{" + ", ".join(f"a[{i}]" for i in range(W)) + "}")
        m.inst(lm, f".a({r}), .n(n)", f"the leading-zero detector ({lzd_fam}) on the reversed word")
        return name, m.render()
    name = name or f"fam_count_tzc_{strat}_{iso}{_tag(_sub(pins, 'negation_incrementer.')) if iso == 'twos_complement_and' else ''}_w{W}"
    m = Mod(name, f"input logic [{W-1}:0] a, output logic [{CW-1}:0] n",
            f"trailing_zero ({strat}, {iso}): the lowest one isolated and encoded")
    low = m.wire("low", W)
    if iso == "twos_complement_and":
        inc_fam = str(_pin(pins, "negation_incrementer.family", "prefix_and_incrementer"))
        inc_pins = _sub(pins, "negation_incrementer.")
        im = FAM.incrementer_module(inc_fam, inc_pins, W)
        if im is None:
            raise ValueError(f"trailing_zero: the incrementer family {inc_fam!r} has no module")
        na = m.wire("na", W, expr="~a")
        neg = m.wire("neg", W)
        m.inst(im, f".a({na}), .cin(1'b1), .s({neg}), .cout()", f"-a = ~a + 1 through the incrementer ({inc_fam})")
        m.assign(low, f"a & {neg}")
    else:
        m.wire("kill", W)
        m.assign("kill[0]", "1'b0")
        for i in range(1, W):
            m.assign(f"kill[{i}]", f"kill[{i-1}] | a[{i-1}]")
        m.assign(low, "a & ~kill")
    if strat == "isolate_then_encode":
        enc = m.wire("enc", CW)
        _or_encode(m, [f"low[{i}]" for i in range(W)], list(range(W)), CW, enc, "the isolated one encoded to its index")
    else:
        L = _clog2(W) if W > 1 else 1
        WP = 1 << L
        db = _debruijn(L)
        lowp = low if WP == W else m.wire("lowp", WP, expr=f"{{{WP - W}'d0, low}}")
        prod = m.wire("prod", WP, expr=f"{lowp} * {WP}'d{db}")
        idx = m.wire("idx", L, expr=f"prod[{WP-1}:{WP-L}]")
        enc = m.wire("enc", CW)
        table = {}
        for i in range(WP):
            table[((db << i) & ((1 << WP) - 1)) >> (WP - L)] = i
        m.raw(f"  // the de Bruijn index table ({L} bits, constant {WP}'d{db})")
        m.raw(f"  always_comb begin case ({idx})")
        for k in sorted(table):
            m.raw(f"    {L}'d{k}: {enc} = {CW}'d{min(table[k], W)};")
        m.raw(f"    default: {enc} = {CW}'d0;")
        m.raw("  endcase end")
    m.assign("n", f"(low == {W}'d0) ? {CW}'d{W} : enc")
    return name, m.render()


# ---- the CLI ------------------------------------------------------------------------------------
def count_sv(family: str, W: int, pins: dict, name: str | None = None) -> tuple:
    if family in POPCOUNT_FAMILIES:
        return popcount_sv(W, pins, name)
    if family == "lzd_cell_tree":
        return lzd_cell_tree_sv(W, pins, name)
    if family == "prefix_lzc":
        return prefix_lzc_sv(W, pins, name)
    if family == "priority_encoder":
        return priority_encoder_sv(W, pins, name)
    if family in TZC_FAMILIES:
        return trailing_zero_sv(W, pins, name)
    raise ValueError(f"no bit-count module for the family {family!r}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="emit a bit-count family module")
    ap.add_argument("--family", required=True)
    ap.add_argument("--width", type=int, default=16)
    ap.add_argument("--pins", default="")
    a = ap.parse_args(argv)
    pins = {}
    for kv in filter(None, a.pins.split(",")):
        k, v = kv.split("=", 1)
        pins[k] = {"True": True, "False": False}.get(v, v)
    _, text = count_sv(a.family, a.width, pins)
    sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
