"""The adder families composed around library modules (adder_spaces.py):

* carry_skip, carry_select, carry_increment: blocks sized by the family's
  block_sizing rule (uniform, ramps, doubling, a unit-delay dynamic
  program), every block the library adder of the `block_adder` slot;
  the skip's levels and gate, the select's duplication (a second block or
  the `add_one` incrementer slot) and select source (rippled or a
  lookahead over the block generates and propagates), the increment's
  `increment_stage` slot, intergroup carry and second increment level;
* sparse_prefix_hybrid: a prefix network of the tree_topology at the
  valency over the blocks of 2^log2_sparsity bits (families/prefix.py's
  network), the block sums by the sum_block_style from the `sum_block`
  slot's adder;
* end_around_carry: the carry-out re-entering as the carry-in for
  ones'-complement (modulo 2^W - 1, the double-zero convention the
  integer lane's `_eac` reference uses), modulo 2^W + 1 in
  diminished-one coding, or a generic modulus p (modulus_value; the
  constant 2^W - p added on overflow); recirculation two_pass_prefix (a
  prefix adder of the topology, then a pass through the `incrementer`
  slot), cyclic_prefix_level (the Kogge-Stone cyclic recurrence: every
  level wraps around, the depth stays log2 W) or select_based (both
  candidates, the carry-out selects);
* approximate_truncated: an exact upper adder of the upper_adder family
  over W - k bits and a lower scheme over the k low bits (forced
  complementary constants, OR gates, an isolated sub-adder, or a
  speculative window), with an optional correction stage through the
  `correction_incrementer` slot;
* fpga_carry_chain with prefix_over_chain: ripple segments of
  chain_segment_length bits whose carries come from a prefix overlay.

Every module keeps the adder interface:

    module fam_adder_... (input [W-1:0] a, input [W-1:0] b, input cin, output [W-1:0] s, output cout);
"""
from __future__ import annotations

import hashlib
import json

from chialu.targets.rtl.families.mul import dedupe_modules


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


def _clog2(n: int) -> int:
    return max(1, (n - 1).bit_length())


def _tag(d: dict) -> str:
    """A complete digest of explicit architecture choices (empty for none)."""
    d = {k: v for k, v in (d or {}).items() if not str(k).startswith("_")}
    if not d:
        return ""
    return "_p" + hashlib.sha256(json.dumps(d, sort_keys=True, default=str).encode()).hexdigest()


class Mod:
    def __init__(self, name: str, w: int, comment: str, ctrl: tuple = ()):
        self.name, self.w, self.comment = name, w, comment
        self.lines: list = []
        self.extra: list = []
        self.n = 0
        self.ctrl = tuple(ctrl)          # (port name, width) the unit drives beside the operands

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

    def adder(self, fam, pins: dict, width: int, a: str, b: str, cin: str, s: str, cout: str, comment: str) -> None:
        """s, cout = a + b + cin through the adder family's library module."""
        from chialu.targets.rtl import families as FAM
        m = FAM.adder_module(fam, pins, width) if fam else None
        if m is None:
            raise ValueError(f"the adder family {fam!r} has no library module at {width} bits")
        self.inst(m, f".a({a}), .b({b}), .cin({cin}), .s({s}), .cout({cout})", comment)

    def incr(self, fam, pins: dict, width: int, a: str, cin: str, s: str, cout: str, comment: str) -> None:
        """s, cout = a + cin through the incrementer family's library module."""
        from chialu.targets.rtl import families as FAM
        m = FAM.incrementer_module(fam or "prefix_and_incrementer", pins, width)
        if m is None:
            raise ValueError(f"the incrementer family {fam!r} has no library module")
        self.inst(m, f".a({a}), .cin({cin}), .s({s}), .cout({cout})", comment)

    def slot_adder(self, template, slot, width, a, b, cin, s, cout, comment):
        self.inst(template.module(slot, "adder", width),
                  f".a({a}), .b({b}), .cin({cin}), .s({s}), .cout({cout})", comment)

    def slot_incrementer(self, template, slot, width, a, cin, s, cout, comment):
        self.inst(template.module(slot, "incrementer", width),
                  f".a({a}), .cin({cin}), .s({s}), .cout({cout})", comment)

    def render(self) -> str:
        w = self.w
        ctrl = "".join(f"input logic {f'[{cw-1}:0] ' if cw > 1 else ''}{cn}, " for cn, cw in self.ctrl)
        head = [f"// {self.comment}",
                f"module {self.name} ({ctrl}input logic [{w-1}:0] a, input logic [{w-1}:0] b, input logic cin, "
                f"output logic [{w-1}:0] s, output logic cout);"]
        return "\n".join(head + self.lines + ["endmodule", ""]) + dedupe_modules("".join(self.extra))


# ---- block sizing --------------------------------------------------------------------
RIPPLE_COST, SKIP_COST, MUX_COST = 2, 1, 1        # the unit-delay model: gate levels per rippled bit, per skip, per select


def _fit(sizes: list, W: int) -> list:
    """Clip a size list to W bits, the last block taking the remainder."""
    out, used = [], 0
    for k in sizes:
        if used >= W:
            break
        k = max(1, min(k, W - used))
        out.append(k)
        used += k
    if used < W:
        out.append(W - used)
    return out


def _skip_dp(W: int, bmax: int) -> list:
    """The carry-skip block sizes minimizing the worst path of the unit-delay
    model (a carry generated at the bottom of block i ripples through it,
    skips the blocks between, ripples through block j): a dynamic program
    over the prefix partitions with the state (bits placed, blocks placed,
    the largest RIPPLE k_i - SKIP i so far)."""
    R, S = RIPPLE_COST, SKIP_COST
    best: dict = {(0, 0, -10 ** 6): (0, ())}       # (pos, j, A) -> (worst so far, sizes)
    for pos in range(W):
        for (p, j, A), (worst, sizes) in list(best.items()):
            if p != pos:
                continue
            for k in range(1, min(bmax, W - pos) + 1):
                a_new = max(A, R * k - S * j)
                t = max(worst, R * k, (A + R * k + S * (j - 1)) if j > 0 else 0)
                key = (pos + k, j + 1, a_new)
                cand = (t, sizes + (k,))
                if key not in best or cand < best[key]:
                    best[key] = cand
    finals = [(v[0], len(v[1]), v[1]) for (p, j, A), v in best.items() if p == W]
    return list(min(finals)[2])


def _select_dp(W: int, bmax: int) -> list:
    """The carry-select block sizes minimizing the last select's time under
    the unit-delay model (a block's two sums ready after RIPPLE k, the
    select chain adding MUX per block)."""
    R, M = RIPPLE_COST, MUX_COST
    best: dict = {(0, 0): ()}                        # (pos, t) -> sizes
    for pos in range(W):
        for (p, t), sizes in list(best.items()):
            if p != pos:
                continue
            for k in range(1, min(bmax, W - pos) + 1):
                key = (pos + k, max(R * k, t) + M)
                if key not in best or len(sizes) + 1 < len(best[key]):
                    best[key] = sizes + (k,)
    finals = [(t, len(s), s) for (p, t), s in best.items() if p == W]
    return list(min(finals)[2])


def block_sizes(W: int, rule: str, B: int) -> list:
    """The block widths (lsb first) of a blocked adder under a sizing rule."""
    # Ramp sizing starts at two independently of B. Small nested adders
    # still carry the unused default B=4 after activity projection.
    if B > W and rule not in ("square_root_ramp", "variable_ramp"):
        raise ValueError(f"block_width={B} does not fit the {W}-bit adder")
    B = max(2, B)
    if rule in ("uniform",):
        return _fit([B] * ((W + B - 1) // B), W)
    if rule in ("square_root_ramp", "variable_ramp"):
        sizes, k = [], 2
        while sum(sizes) < W:
            sizes.append(k)
            k += 1
        return _fit(sizes, W)
    if rule == "delay_matched_doubling":
        sizes, k = [], B
        while sum(sizes) < W:
            sizes.append(k)
            k *= 2
        return _fit(sizes, W)
    if rule == "trapezoidal_variable":
        # grow by one per block up to B, then shrink by one: the widest blocks in the middle
        up = list(range(2, B + 1))
        half = (W + 1) // 2
        sizes, used = [], 0
        for k in up:
            if used + k > half:
                break
            sizes.append(k)
            used += k
        mid = W - 2 * used
        seq = sizes + ([mid] if mid > 0 else []) + list(reversed(sizes))
        return _fit(seq, W)
    if rule == "dp_optimized":
        return _skip_dp(W, B)
    if rule == "delay_balanced_dp":
        return _select_dp(W, B)
    raise ValueError(f"block_sizing {rule!r}")


def _spans(sizes: list) -> list:
    out, lo = [], 0
    for k in sizes:
        out.append((lo, lo + k))
        lo += k
    return out


def _lookahead(m: Mod, G: list, P: list, cin: str, tag: str) -> list:
    """The carries c[0..n] into n elements from (G, P) pairs by a flat
    lookahead (one AND-OR chain per element, all from the carry-in)."""
    n = len(G)
    c = [cin]
    for k in range(n):
        t = cin
        for i in range(k + 1):
            t = m.wire(f"{tag}_t{k}_{i}", expr=f"{G[i]} | ({P[i]} & {t})")
        c.append(t)
    return c


# ---- the block-composed adders ---------------------------------------------------------
def carry_skip_template(W: int, pins: dict, name: str):
    """Build the carry-skip parent from its own choices and binary-adder interfaces."""
    from chialu.targets.rtl.families.components import Template
    own = {"block_width", "block_sizing", "skip_levels", "skip_gate"}
    if set(pins) - own:
        raise ValueError("carry_skip_template accepts only the parent's own choices")
    template = Template(name)
    B = _ipin(pins, "block_width", 4)
    rule = str(_pin(pins, "block_sizing", "uniform"))
    levels = max(1, min(3, _ipin(pins, "skip_levels", 1)))
    gate = str(_pin(pins, "skip_gate", "mux"))
    sizes = block_sizes(W, rule, B)
    m = Mod(name, W, f"carry_skip: blocks {sizes} ({rule}), {levels} skip level{'s' if levels > 1 else ''}, {gate}")

    def skip(cin_w: str, prop: str, chain_out: str, out: str) -> None:
        if gate == "mux":
            m.assign(out, f"{prop} ? {cin_w} : {chain_out}")
        else:
            m.assign(out, f"({prop} & {cin_w}) | {chain_out}")

    def chain(entries: list, cin_w: str, tag: str) -> str:
        """Chain the entries (each a callable cin_wire -> (cout_wire, prop_wire)) from cin_w; returns the carry out."""
        c = cin_w
        for e in entries:
            c, _p = e(c)
        return c

    def block_entry(bi: int, lo: int, hi: int):
        n = hi - lo
        a, b = f"a[{hi-1}:{lo}]", f"b[{hi-1}:{lo}]"
        m.wire(f"P{bi}", expr=f"&({a} ^ {b})")

        def build(cin_w: str):
            m.wire(f"s{bi}", n)
            m.wire(f"co{bi}")
            component = template.module("block_adder", "adder", n)
            m.inst(component, f".a({a}), .b({b}), .cin({cin_w}), .s(s{bi}), .cout(co{bi})", f"block {bi} ({n} bits)")
            m.assign(f"s[{hi-1}:{lo}]", f"s{bi}")
            out = m.wire(f"bc{bi}")
            skip(cin_w, f"P{bi}", f"co{bi}", out)
            return out, f"P{bi}"
        return build, f"P{bi}"

    entries = [block_entry(bi, lo, hi) for bi, (lo, hi) in enumerate(_spans(sizes))]

    def group_entry(sub: list, lvl: int, gi: int):
        props = [p for _b, p in sub]
        gp = m.wire(f"GP{lvl}_{gi}", expr=" & ".join(props))

        def build(cin_w: str):
            c = chain([b for b, _p in sub], cin_w, f"l{lvl}g{gi}")
            out = m.wire(f"gc{lvl}_{gi}")
            skip(cin_w, gp, c, out)
            return out, gp
        return build, gp

    for lvl in range(2, levels + 1):
        n = len(entries)
        if n <= 1:
            from chialu.targets.rtl.families.fidelity import effective
            effective(pins, "skip_levels", lvl - 1, "only these skip levels have multiple input groups", {"width": W, "blocks": sizes})
            break
        gsz = max(2, round(n ** 0.5))
        entries = [group_entry(entries[i:i + gsz], lvl, i // gsz) for i in range(0, n, gsz)]
    cout = chain([b for b, _p in entries], "cin", "top")
    m.assign("cout", cout)
    template.text = m.render()
    return template


def carry_skip_sv(W: int, pins: dict, name: str) -> str:
    return render_template("carry_skip", W, pins, name)


def carry_select_template(W: int, pins: dict, name: str):
    template = _new_template("carry_select", pins, name)
    B = _ipin(pins, "block_width", 4)
    rule = str(_pin(pins, "block_sizing", "uniform"))
    dup = str(_pin(pins, "duplication", "full_duplicate"))
    src = str(_pin(pins, "select_source", "rippled_block_carries"))
    sizes = block_sizes(W, rule, B)
    m = Mod(name, W, f"carry_select: blocks {sizes} ({rule}), {dup}, selects {src}")
    spans = _spans(sizes)
    nb = len(spans)
    G, P = [], []
    for bi, (lo, hi) in enumerate(spans):
        n = hi - lo
        a, b = f"a[{hi-1}:{lo}]", f"b[{hi-1}:{lo}]"
        m.wire(f"s{bi}_0", n)
        m.wire(f"s{bi}_1", n)
        m.wire(f"co{bi}_0")
        m.wire(f"co{bi}_1")
        m.slot_adder(template, "block_adder", n, a, b, "1'b0", f"s{bi}_0", f"co{bi}_0", f"block {bi} ({n} bits), carry-in 0")
        if dup == "full_duplicate":
            m.slot_adder(template, "block_adder", n, a, b, "1'b1", f"s{bi}_1", f"co{bi}_1", f"block {bi}, carry-in 1")
        else:
            m.wire(f"ic{bi}")
            m.slot_incrementer(template, "add_one", n, f"s{bi}_0", "1'b1", f"s{bi}_1", f"ic{bi}", f"block {bi}: the carry-in-1 sum by the add-one incrementer")
            m.assign(f"co{bi}_1", f"co{bi}_0 | ic{bi}")
        G.append(f"co{bi}_0")
        P.append(m.wire(f"bp{bi}", expr=f"co{bi}_1 & ~co{bi}_0"))
    if src == "lookahead_tree":
        c = _lookahead(m, G, P, "cin", "la")
    else:
        c = ["cin"]
        for bi in range(nb):
            c.append(m.wire(f"c{bi+1}", expr=f"{c[bi]} ? co{bi}_1 : co{bi}_0"))
    for bi, (lo, hi) in enumerate(spans):
        m.assign(f"s[{hi-1}:{lo}]", f"{c[bi]} ? s{bi}_1 : s{bi}_0")
    m.assign("cout", c[nb])
    template.text = m.render()
    return template


def carry_increment_template(W: int, pins: dict, name: str):
    template = _new_template("carry_increment", pins, name)
    B = _ipin(pins, "block_width", 4)
    rule = str(_pin(pins, "block_sizing", "uniform"))
    inter = str(_pin(pins, "intergroup_carry", "rippled"))
    levels = max(1, min(2, _ipin(pins, "increment_levels", 1)))
    sizes = block_sizes(W, rule, B)
    m = Mod(name, W, f"carry_increment: blocks {sizes} ({rule}), "
                     f"group carries {inter}, {levels} increment level{'s' if levels > 1 else ''}")
    spans = _spans(sizes)
    nb = len(spans)
    # every block once with carry-in 0; its generate is the carry-out, its propagate the AND of the bit propagates
    G, P = [], []
    for bi, (lo, hi) in enumerate(spans):
        n = hi - lo
        a, b = f"a[{hi-1}:{lo}]", f"b[{hi-1}:{lo}]"
        m.wire(f"s{bi}", n)
        m.wire(f"co{bi}")
        m.slot_adder(template, "block_adder", n, a, b, "1'b0", f"s{bi}", f"co{bi}", f"block {bi} ({n} bits), carry-in 0")
        G.append(f"co{bi}")
        P.append(m.wire(f"bp{bi}", expr=f"&({a} ^ {b})"))
    if levels == 1:
        if inter == "lookahead_tree":
            c = _lookahead(m, G, P, "cin", "la")
        else:
            c = ["cin"]
            for bi in range(nb):
                c.append(m.wire(f"c{bi+1}", expr=f"{G[bi]} | ({P[bi]} & {c[bi]})"))
        for bi, (lo, hi) in enumerate(spans):
            n = hi - lo
            m.wire(f"si{bi}", n)
            m.wire(f"ico{bi}")
            m.slot_incrementer(template, "increment_stage", n, f"s{bi}", c[bi], f"si{bi}", f"ico{bi}", f"block {bi}: the carry-in through the increment stage")
            m.assign(f"s[{hi-1}:{lo}]", f"si{bi}")
        m.assign("cout", c[nb])
        template.text = m.render()
        return template
    # two levels: the blocks grouped; inside a group the blocks increment by the group-internal carry (from
    # 0 at the group's start); the group's carry-in then increments the whole group sum once more
    gsz = max(2, round(nb ** 0.5))
    groups = [list(range(i, min(i + gsz, nb))) for i in range(0, nb, gsz)]
    GG, GP, gout = [], [], []
    for gi, blocks in enumerate(groups):
        c = ["1'b0"]
        for bi in blocks:
            c.append(m.wire(f"c{gi}_{bi}", expr=f"{G[bi]} | ({P[bi]} & {c[-1]})"))
        parts = []
        for j, bi in enumerate(blocks):
            lo, hi = spans[bi]
            n = hi - lo
            m.wire(f"si{bi}", n)
            m.wire(f"ico{bi}")
            m.slot_incrementer(template, "increment_stage", n, f"s{bi}", c[j], f"si{bi}", f"ico{bi}", f"group {gi} block {bi}: the group-internal carry")
            parts.append(f"si{bi}")
        lo_g, hi_g = spans[blocks[0]][0], spans[blocks[-1]][1]
        gw = m.wire(f"gs{gi}", hi_g - lo_g, expr="{" + ", ".join(reversed(parts)) + "}")
        GG.append(c[-1])
        GP.append(m.wire(f"gp{gi}", expr=" & ".join(P[bi] for bi in blocks)))
        gout.append((gi, lo_g, hi_g, gw))
    if inter == "lookahead_tree":
        gc = _lookahead(m, GG, GP, "cin", "gla")
    else:
        gc = ["cin"]
        for gi in range(len(groups)):
            gc.append(m.wire(f"gc{gi+1}", expr=f"{GG[gi]} | ({GP[gi]} & {gc[gi]})"))
    for gi, lo_g, hi_g, gw in gout:
        n = hi_g - lo_g
        m.wire(f"gsi{gi}", n)
        m.wire(f"gico{gi}")
        m.slot_incrementer(template, "increment_stage", n, gw, gc[gi], f"gsi{gi}", f"gico{gi}", f"group {gi}: the group carry-in through the second increment level")
        m.assign(f"s[{hi_g-1}:{lo_g}]", f"gsi{gi}")
    m.assign("cout", gc[len(groups)])
    template.text = m.render()
    return template


# ---- sparse_prefix_hybrid and the FPGA chain overlay -----------------------------------------------
def _prefix_network(m: Mod, n: int, spec: str, valency: int, tag: str, G: list, P: list, cin: str) -> list:
    """The carries into n block positions from (G, P) by a prefix network of
    a topology (families/prefix.py), instantiated as a library module."""
    from chialu.targets.rtl import families as FAM
    from chialu.targets.rtl.families import prefix
    if n == 1:
        # one block: the carry into it is the carry-in, the carry out its generate or propagated carry-in
        co = m.wire(f"{tag}_co", expr=f"{G[0]} | ({P[0]} & {cin})")
        return [cin, co]
    name = f"fam_prefix_net_{prefix.module_name(spec, n, False, False)[11:]}" + (f"_v{valency}" if valency > 2 else "")
    text = prefix.network_sv(n, spec, name, valency=valency)
    gv = m.wire(f"{tag}_g", n, expr="{" + ", ".join(reversed(G)) + "}")
    pv = m.wire(f"{tag}_p", n, expr="{" + ", ".join(reversed(P)) + "}")
    cv = m.wire(f"{tag}_c", n)
    co = m.wire(f"{tag}_co")
    m.inst(FAM.Module(name, {}, text), f".g({gv}), .p({pv}), .cin({cin}), .c({cv}), .cout({co})",
           f"the prefix network over the blocks ({spec}" + (f", valency {valency}" if valency > 2 else "") + ")")
    return [f"{cv}[{i}]" for i in range(n)] + [co]


def sparse_prefix_hybrid_template(W: int, pins: dict, name: str):
    template = _new_template("sparse_prefix_hybrid", pins, name)
    sp = max(1, min(3, _ipin(pins, "log2_sparsity", 2)))
    topo = str(_pin(pins, "tree_topology", "sklansky"))
    val = max(2, min(4, _ipin(pins, "valency", 2)))
    style = str(_pin(pins, "sum_block_style", "carry_select"))
    B = 1 << sp
    from chialu.targets.rtl.families.fidelity import effective
    effective(pins, "log2_sparsity", min(sp, max(0, W.bit_length() - 1)), "full sparse block", {"width": W})
    sizes = _fit([B] * ((W + B - 1) // B), W)
    m = Mod(name, W, f"sparse_prefix_hybrid: a {topo} prefix network" + (f" of valency {val}" if val > 2 else "")
                     + f" over blocks of {B} bits, the sums by {style}")
    spans = _spans(sizes)
    m.wire("g", W, expr="a & b")
    m.wire("p", W, expr="a ^ b")
    G, P = [], []
    for bi, (lo, hi) in enumerate(spans):
        # the block generate and propagate from its bits (the tree's pre-processing)
        gg, pp = f"g[{lo}]", f"p[{lo}]"
        for i in range(lo + 1, hi):
            gg = f"(g[{i}] | (p[{i}] & {gg}))"
            pp = f"(p[{i}] & {pp})"
        G.append(m.wire(f"BG{bi}", expr=gg))
        P.append(m.wire(f"BP{bi}", expr=pp))
    c = _prefix_network(m, len(spans), topo, val, "net", G, P, "cin")
    for bi, (lo, hi) in enumerate(spans):
        n = hi - lo
        a, b = f"a[{hi-1}:{lo}]", f"b[{hi-1}:{lo}]"
        if style == "carry_select":
            m.wire(f"s{bi}_0", n)
            m.wire(f"s{bi}_1", n)
            m.wire(f"x{bi}_0")
            m.wire(f"x{bi}_1")
            m.slot_adder(template, "sum_block", n, a, b, "1'b0", f"s{bi}_0", f"x{bi}_0", f"block {bi}: the sum under carry-in 0")
            m.slot_adder(template, "sum_block", n, a, b, "1'b1", f"s{bi}_1", f"x{bi}_1", f"block {bi}: the sum under carry-in 1")
            m.assign(f"s[{hi-1}:{lo}]", f"{c[bi]} ? s{bi}_1 : s{bi}_0")
        elif style == "conditional_sum":
            from chialu.targets.rtl import families as FAM
            m.wire(f"s{bi}", n)
            m.wire(f"x{bi}")
            m.inst(FAM.Module("fam_adder_conditional_sum", {"W": n, "BASE": 1, "RADIX": 2}),
                   f".a({a}), .b({b}), .cin({c[bi]}), .s(s{bi}), .cout(x{bi})", f"block {bi}: a conditional-sum block under the tree's carry")
            m.assign(f"s[{hi-1}:{lo}]", f"s{bi}")
        else:
            m.wire(f"s{bi}", n)
            m.wire(f"x{bi}")
            m.slot_adder(template, "sum_block", n, a, b, c[bi], f"s{bi}", f"x{bi}", f"block {bi}: the block rippled from the tree's carry")
            m.assign(f"s[{hi-1}:{lo}]", f"s{bi}")
    m.assign("cout", c[len(spans)])
    template.text = m.render()
    return template


TEMPLATES = {"carry_skip": carry_skip_template, "carry_select": carry_select_template,
             "carry_increment": carry_increment_template, "sparse_prefix_hybrid": sparse_prefix_hybrid_template}
TEMPLATE_CHOICES = {
    "carry_skip": ("block_width", "block_sizing", "skip_levels", "skip_gate"),
    "carry_select": ("block_width", "block_sizing", "duplication", "select_source"),
    "carry_increment": ("block_width", "block_sizing", "intergroup_carry", "increment_levels"),
    "sparse_prefix_hybrid": ("log2_sparsity", "tree_topology", "valency", "sum_block_style"),
}


def _new_template(family, pins, name):
    from chialu.targets.rtl.families.components import Template
    if set(pins) - set(TEMPLATE_CHOICES[family]):
        raise ValueError(f"{family} template accepts only the parent's own choices")
    return Template(name)


def render_template(family, W, pins, name):
    from chialu.targets.rtl import families as FAM
    own = {k: v for k, v in pins.items() if k in TEMPLATE_CHOICES[family]}
    template = TEMPLATES[family](W, own, name)

    def resolve(component):
        default = "ripple_carry" if component.kind == "adder" else "prefix_and_incrementer"
        chosen = str(_pin(pins, component.slot + ".family", default))
        child = _sub(pins, component.slot + ".")
        factory = FAM.adder_module if component.kind == "adder" else FAM.incrementer_module
        from chialu.targets.rtl.families.fidelity import component_binding
        widths = {item.width for item in template.components.values() if item.slot == component.slot and item.kind == component.kind}
        with component_binding(chosen, child, sorted(widths), component.slot):
            return factory(chosen, child, component.width)

    return template.render(resolve)


def carry_select_sv(W, pins, name):
    return render_template("carry_select", W, pins, name)


def carry_increment_sv(W, pins, name):
    return render_template("carry_increment", W, pins, name)


def sparse_prefix_hybrid_sv(W, pins, name):
    return render_template("sparse_prefix_hybrid", W, pins, name)


def fpga_chain_overlay_sv(W: int, pins: dict, name: str) -> str:
    seg = max(2, min(_ipin(pins, "chain_segment_length", 8), W))
    from chialu.targets.rtl.families.fidelity import effective
    effective(pins, "chain_segment_length", seg, "full carry segment under the prefix overlay", {"width": W})
    if W <= seg:
        raise ValueError("prefix_over_chain requires at least two actual chain segments")
    sizes = _fit([seg] * ((W + seg - 1) // seg), W)
    m = Mod(name, W, f"fpga_carry_chain with a prefix overlay: ripple segments of {seg} bits, the segment carries "
                     f"from a Kogge-Stone network over the segments' generates and propagates")
    spans = _spans(sizes)
    m.wire("g", W, expr="a & b")
    m.wire("p", W, expr="a ^ b")
    G, P = [], []
    for bi, (lo, hi) in enumerate(spans):
        gg, pp = f"g[{lo}]", f"p[{lo}]"
        for i in range(lo + 1, hi):
            gg = f"(g[{i}] | (p[{i}] & {gg}))"
            pp = f"(p[{i}] & {pp})"
        G.append(m.wire(f"SG{bi}", expr=gg))
        P.append(m.wire(f"SP{bi}", expr=pp))
    c = _prefix_network(m, len(spans), "kogge_stone", 2, "net", G, P, "cin")
    for bi, (lo, hi) in enumerate(spans):
        n = hi - lo
        m.wire(f"s{bi}", n)
        m.wire(f"x{bi}")
        m.adder("ripple_carry", {}, n, f"a[{hi-1}:{lo}]", f"b[{hi-1}:{lo}]", c[bi], f"s{bi}", f"x{bi}", f"segment {bi}: the hard ripple chain")
        m.assign(f"s[{hi-1}:{lo}]", f"s{bi}")
    m.assign("cout", c[len(spans)])
    return m.render()


# ---- end_around_carry ----------------------------------------------------------------
def _cyclic_ks(m: Mod, W: int):
    """The cyclic Kogge-Stone recurrence over (g, p): after log2 W levels
    position i holds the group of the W bits ending at i in cyclic
    order, so gc[i] is the carry into bit i+1 mod W with the carry-out
    wrapped around; the all-propagate word (a + b = 2^W - 1) yields no
    carry, the double-zero convention."""
    m.wire("g0", W, expr="a & b")
    m.wire("p0", W, expr="a ^ b")
    bit = lambda name, index: f"{name}[{index}]" if W > 1 else name
    g, p = "g0", "p0"
    L = _clog2(W)
    for lvl in range(L):
        d = 1 << lvl
        gn, pn = f"g{lvl+1}", f"p{lvl+1}"
        m.wire(gn, W)
        m.wire(pn, W)
        for i in range(W):
            j = (i - d) % W
            m.assign(bit(gn, i), f"{bit(g, i)} | ({bit(p, i)} & {bit(g, j)})")
            m.assign(bit(pn, i), f"{bit(p, i)} & {bit(p, j)}")
        g, p = gn, pn
    return g, p


def _diminished_cyclic(m, W, pins, ifam, ipins):
    """One selected GP tree and an inverted end-around carry row.

    For T=a+b, the feedback ~G[W-1:0] produces T+1 below 2**W
    and T-2**W above it. The all-propagate word represents 2**W
    with low code zero; a following cin must map that value to zero,
    rather than incrementing its already truncated code to one.
    """
    from chialu.targets.rtl import families as FAM
    from chialu.targets.rtl.families import prefix
    from chialu.targets.rtl.families.fidelity import effective
    spec = FAM.prefix_spec("end_around_carry", pins, W)
    graph = prefix.build(W, spec)
    graph.validate()
    m.wire("bit_g", W, expr="a & b")
    m.wire("bit_p", W, expr="a ^ b")
    bit = lambda name, i: f"{name}[{i}]" if W > 1 else name
    groups = {(i, i): (bit("bit_g", i), bit("bit_p", i)) for i in range(W)}
    for key in sorted(graph.nodes, key=lambda span: (span[1] - span[0], span)):
        upper, lower = graph.parents_of(key)
        ug, up = groups[upper]
        lg, lp = groups[lower]
        lo, hi = key
        groups[key] = (m.wire(f"cyclic_g_{lo}_{hi}", expr=f"{ug} | ({up} & {lg})"),
                       m.wire(f"cyclic_p_{lo}_{hi}", expr=f"{up} & {lp}"))
    carry, propagate = groups[0, W - 1]
    m.wire("feedback", expr=f"~{carry}")
    m.wire("cyclic_sum", W)
    for i in range(W):
        ci = "feedback"
        if i:
            gi, pi = groups[0, i - 1]
            ci = m.wire(f"cyclic_c{i}", expr=f"{gi} | ({pi} & feedback)")
        m.assign(bit("cyclic_sum", i), f"{bit('bit_p', i)} ^ {ci}")
    m.wire("incremented", W)
    m.wire("increment_carry")
    m.incr(ifam, ipins, W, "cyclic_sum", "cin", "incremented", "increment_carry",
           "the external carry-in after the inverted cyclic carry row")
    m.assign("s", f"(cin && {propagate}) ? {W}'d0 : incremented")
    # Preserve the declared cout=(a+b+cin+1)[W], including the carry
    # past bit W when both operands are all ones and cin is one.
    m.wire("near_carry", expr="&cyclic_sum")
    m.assign("cout", f"cin ? (({carry} | {propagate} | near_carry) & !(&bit_g)) : ({carry} | {propagate})")
    effective(pins, "recirculation", "cyclic_prefix_level", "selected GP graph followed by an inverted feedback row",
              {"width": W, "graph": spec, "nodes": graph.size(), "levels": graph.levels()})
    return m.render()


def end_around_carry_sv(W: int, pins: dict, name: str) -> str:
    modulus = str(_pin(pins, "modulus", "mod_2n_minus_1"))
    recirc = str(_pin(pins, "recirculation", "cyclic_prefix_level"))
    ifam = str(_pin(pins, "incrementer.family", "prefix_and_incrementer"))
    ipins = _sub(pins, "incrementer.")
    # the prefix adder of the passes: the topology and its Harris pins as parallel_prefix reads them
    ppins = {k: v for k, v in (pins or {}).items() if k in ("topology", "log2_sparsity", "fanout_cap")}
    topo = str(_pin(pins, "topology", "kogge_stone"))
    m = Mod(name, W, f"end_around_carry ({modulus}, {recirc}, {topo}, the incrementer {ifam}): the carry-out re-enters as the carry-in")
    ones = f"{{{W}{{1'b1}}}}"
    if modulus == "generic_p_correction":
        # The full binary input domain reaches 2**(W+1)-1. A single
        # correction is sufficient only when both operands are <p.
        # Retain the original selected prefix and its binary carry;
        # aligned conditional subtractions reduce every possible sum.
        from .rns_cpa import generic_modulus
        pmod = generic_modulus(pins, W)
        m.wire("t", W + 1)
        m.adder("parallel_prefix", ppins, W, "a", "b", "cin", "t[%d:0]" % (W - 1), f"t[{W}]", "the sum")
        sw = W + 1
        m.raw(f"  localparam [{W}:0] MODULUS = {sw}'d{pmod};")
        shifts = (((1 << sw) - 1) // pmod).bit_length()
        m.raw(f'  localparam integer REDUCTION_STAGES = {shifts};')
        current = 't'
        for shift in reversed(range(shifts)):
            m.wire(f'difference{shift}', sw)
            m.wire(f'nonnegative{shift}')
            complement = ((1 << sw) - 1) ^ (pmod << shift)
            m.adder('parallel_prefix', ppins, sw, current, f"{sw}'d{complement}", "1'b1",
                    f'difference{shift}', f'nonnegative{shift}', f'complete generic-p reduction, shifted modulus {shift}')
            current = m.wire(f'remainder{shift}', sw,
                             expr=f'nonnegative{shift} ? difference{shift} : {current}')
        m.assign('s', f'{current}[{W-1}:0]')
        m.assign("cout", f"t[{W}]")
        return m.render()
    inv = modulus == "mod_2n_plus_1_diminished_one"      # the complemented carry re-enters
    if recirc == "cyclic_prefix_level":
        if inv:
            return _diminished_cyclic(m, W, pins, ifam, ipins)
        # the cyclic sum of a and b (double zero), then the carry-in through the incrementer with the wrap
        g, p = _cyclic_ks(m, W)
        # the carry into bit i is the cyclic group ending at i-1
        m.wire("cc", W)
        bit = lambda name, index: f"{name}[{index}]" if W > 1 else name
        for i in range(W):
            m.assign(bit("cc", i), bit(g, (i - 1) % W))
        m.wire("t", W, expr="p0 ^ cc")                         # (a + b) mod (2^W - 1), double zero
        m.wire("co1", expr=bit(g, W - 1))
        m.wire("ti", W)
        m.wire("tco")
        m.incr(ifam, ipins, W, "t", "cin", "ti", "tco", "the carry-in entering after the cyclic level")
        # cin=1 at a=b=0 must yield one, including the W=1
        # double-zero ring where that code is also the all-ones word.
        m.assign("s", f"cin ? (tco ? {W}'d1 : ti) : t")
        m.assign("cout", "co1")
        return m.render()
    # two_pass_prefix and select_based: pass 1 is the topology's prefix adder over a + b + cin
    m.wire("r", W)
    m.wire("c1")
    m.adder("parallel_prefix", ppins, W, "a", "b", "cin", "r", "c1", "pass 1: the sum and its carry-out")
    m.wire("back", expr="~c1" if inv else "c1")
    if recirc == "select_based":
        # both candidates (the sum, the sum plus one) and the carry-out selects
        m.wire("r1", W)
        m.wire("c2")
        m.adder("parallel_prefix", ppins, W, "a", "b", "1'b1", "r1", "c2", "the candidate with the re-entering carry (cin = 1)")
        if inv:
            # diminished-one: the complemented carry adds one to the sum with its own carry-in; the candidate
            # under a carry-in of one is the incremented cin = 1 sum (the low W bits stand for the code)
            m.wire("r1i", W)
            m.wire("c3i")
            m.incr(ifam, ipins, W, "r1", "cin", "r1i", "c3i", "the candidate under a carry-in of one")
            m.assign("s", "back ? r1i : r")
        else:
            # with cin already one, the re-entering carry adds a second one: the incrementer of the candidate
            m.wire("r2", W)
            m.wire("c3")
            m.incr(ifam, ipins, W, "r1", "cin", "r2", "c3", "the candidate under a carry-in of one")
            m.wire("sel", W, expr="cin ? r2 : r1")
            m.wire("wrap", expr="cin ? c3 : 1'b0")
            m.assign("s", f"back ? (wrap ? {W}'d1 : sel) : r")
    else:
        m.wire("ri", W)
        m.wire("wrap")
        m.incr(ifam, ipins, W, "r", "back", "ri", "wrap", "pass 2: the re-entering carry through the incrementer")
        # modulo 2^W - 1: an increment that overflows is the double wrap (the sum 2^(W+1) - 1) and stands for 1;
        # diminished-one keeps the low W bits (256 is the code of the modulus, the zero of the ring)
        m.assign("s", "ri" if inv else f"wrap ? {W}'d1 : ri")
    m.assign("cout", "c1")
    return m.render()


# ---- approximate_truncated ---------------------------------------------------------
def approximate_truncated_sv(W: int, pins: dict, name: str) -> str:
    k = _ipin(pins, "lower_part_width", 4)
    if not 1 <= k < W:
        raise ValueError(f"lower_part_width={k} requires an actual lower region and upper region at width {W}")
    scheme = str(_pin(pins, "lower_scheme", "truncate_constant"))
    corr = str(_pin(pins, "correction", "none"))
    ufam = _pin(pins, "upper_adder.family", "ripple_carry")
    upins = _sub(pins, "upper_adder.")
    ifam = str(_pin(pins, "correction_incrementer.family", "prefix_and_incrementer"))
    ipins = _sub(pins, "correction_incrementer.")
    U = W - k
    m = Mod(name, W, f"approximate_truncated: the upper {U} bits exact ({ufam}), the low {k} bits by {scheme}, "
                     f"correction {corr} (the ArithmeticError gate governs)")
    m.wire("al", k, expr=f"a[{k-1}:0]")
    m.wire("bl", k, expr=f"b[{k-1}:0]")
    if scheme == "truncate_constant":
        # forced complementary constants: every lower stage sums to one and carries nothing
        m.wire("sl", k, expr=f"{{{k}{{1'b1}}}}")
        m.wire("cl", expr="1'b0")
    elif scheme == "or_gates":
        m.wire("sl", k, expr="al | bl")
        m.wire("cl", expr=f"al[{k-1}] & bl[{k-1}]")
    elif scheme == "segmented_subadders":
        m.wire("sl", k)
        m.wire("cl_unused")
        m.adder(ufam, upins, k, "al", "bl", "cin", "sl", "cl_unused", "the isolated lower sub-adder (its carry does not cross)")
        m.wire("cl", expr="1'b0")
    else:
        # speculative_segments: the lower sum with the carry into the upper part speculated from a window
        win = _ipin(pins, "speculation_window", 4)
        if not 1 <= win <= k:
            raise ValueError(f"speculation_window={win} does not fit the {k}-bit lower region")
        m.wire("sl", k)
        m.wire("cl_full")
        m.adder(ufam, upins, k, "al", "bl", "cin", "sl", "cl_full", "the lower sub-adder")
        if win >= 8:
            m.wire("wsum", win)
            m.wire("cl")
            m.adder(ufam, upins, win, f"al[{k-1}:{k-win}]", f"bl[{k-1}:{k-win}]", "1'b0", "wsum", "cl", "the speculation window's carry")
        else:
            m.wire("wsum", win + 1, expr=f"{{1'b0, al[{k-1}:{k-win}]}} + {{1'b0, bl[{k-1}:{k-win}]}}")
            m.wire("cl", expr=f"wsum[{win}]")
    m.wire("su", U)
    m.wire("cu")
    m.adder(ufam, upins, U, f"a[{W-1}:{k}]", f"b[{W-1}:{k}]", "cl", "su", "cu", "the exact upper adder")
    if corr == "configurable_stages" and scheme == "speculative_segments":
        # the correction stage: the true lower carry compared with the speculation, the upper sum incremented
        m.wire("miss", expr="cl_full & ~cl")
        m.wire("suc", U)
        m.wire("cuc")
        m.incr(ifam, ipins, U, "su", "miss", "suc", "cuc", "the correction stage through the incrementer")
        m.assign("s", "{suc, sl}")
        m.assign("cout", "cu | cuc")
    else:
        m.assign("s", "{su, sl}")
        m.assign("cout", "cu")
    return m.render()


# ---- the entry -------------------------------------------------------------------------
BLOCKED = ("carry_skip", "carry_select", "carry_increment", "sparse_prefix_hybrid")
EXT_FAMILIES = BLOCKED + ("end_around_carry", "approximate_truncated", "fpga_carry_chain")


def adder_ext_sv(W: int, family: str, pins: dict, name: str | None = None) -> tuple:
    pins = pins or {}
    if family == "end_around_carry":
        name = name or f"fam_adder_eac_{_pin(pins, 'recirculation', 'cyclic_prefix_level')}{_tag(pins)}_w{W}"
        return name, end_around_carry_sv(W, pins, name)
    if family == "approximate_truncated":
        name = name or f"fam_adder_approximate_truncated_{_pin(pins, 'lower_scheme', 'truncate_constant')}{_tag(pins)}_w{W}"
        return name, approximate_truncated_sv(W, pins, name)
    if family == "carry_skip":
        name = name or f"fam_adder_carry_skip{_tag(pins)}_w{W}"
        return name, carry_skip_sv(W, pins, name)
    if family == "carry_select":
        name = name or f"fam_adder_carry_select{_tag(pins)}_w{W}"
        return name, carry_select_sv(W, pins, name)
    if family == "carry_increment":
        name = name or f"fam_adder_carry_increment{_tag(pins)}_w{W}"
        return name, carry_increment_sv(W, pins, name)
    if family == "sparse_prefix_hybrid":
        name = name or f"fam_adder_sparse_prefix_hybrid{_tag(pins)}_w{W}"
        return name, sparse_prefix_hybrid_sv(W, pins, name)
    if family == "fpga_carry_chain":
        name = name or f"fam_adder_fpga_chain_overlay{_tag(pins)}_w{W}"
        return name, fpga_chain_overlay_sv(W, pins, name)
    raise ValueError(f"no module for the adder family {family}")
