"""Parallel-prefix carry networks as graphs: the data structure, the
named topologies and the Harris (l, f, t) taxonomy, the PrefixRL node
edits with legalization, the compact index-sequence notation of Roy et
al., a greedy construction for non-uniform arrival, the cost metrics,
and the emission of an unrolled SystemVerilog adder from any graph.

Representation. A prefix graph over n positions (position i is bit i
of the operands; the carry-in is absorbed into position 0's generate)
has one implicit leaf per position and a set of nodes, each a span [lo, hi] computed from an
upper parent [k, hi] and a lower parent [lo, q] with lo < k <= q+1 and
q < hi. Exact splits (q = k-1) are the legality condition of PrefixRL
(Roy et al. 2021, arXiv 2205.07000) and of the bottom-up enumeration of
Roy, Choudhury, Puri and Pan (DAC 2013); an overlap (q >= k) is legal
for the prefix operator, which is idempotent, and is what the fanout-
sharing Knowles networks build. A node with lo = 0 is a carry output
(a gray cell in the usual figures); the others are black cells. The
adder is complete when every position i >= 1 has the node [0, i]
(the carry into bit i+1).

Taxonomy. Harris (2003) indexes the regular networks by (l, f, t) with
l + f + t = L - 1, L = log2 n: l extra logic levels, fanout 2^f + 1,
2^t wire tracks. harris(n, l, f, t) builds the point: l levels of
pairwise combining, a Knowles (0, f, t) network on every 2^l-th
position, l levels filling the rest. sklansky = (0, L-1, 0),
kogge_stone = (0, 0, L-1), brent_kung = (L-1, 0, 0), han_carlson =
(1, 0, L-2), ladner_fischer(l) = (l, L-1-l, 0), knowles(f) = (0, f,
L-1-f).

Edits. add(hi, lo) and remove(hi, lo) follow PrefixRL's grid rules:
a node's upper parent is the nearest node of its row above it (the
smallest existing span [k, hi] with k > lo, the leaf when none), and
the lower parent [lo, k-1] is added when missing; removing a node
re-legalizes its children. The tree-generation game of Lai et al.
(arXiv 2405.06758) and the backbone-plus-refinement of PrefixAgent
(arXiv 2507.06127) operate on the same moves; the search itself is
chiALU's (the variables expose the taxonomy, the coding agent edits
through the command line, the numeric backends walk the points).

Cost. levels(), size(), fanout() and tracks() are the technology-
independent metrics of those papers; synthesis (chialu.eda) gives the
delay and area.

    python3 -m chialu.targets.rtl.families.prefix --width 32 --graph harris:l1f1t2 --report
    python3 -m chialu.targets.rtl.families.prefix --width 32 --graph kogge_stone --edit "remove 20 0; add 20 0" --sv out.sv
    python3 -m chialu.targets.rtl.families.prefix --width 16 --arrival 0,0,0,1,2,3,4,4,4,3,2,1,0,0,0,0 --report
"""
from __future__ import annotations

import argparse
from functools import lru_cache
import re
import sys

NAMED = ("kogge_stone", "sklansky", "brent_kung", "ladner_fischer", "han_carlson", "knowles_mixed", "ripple")


class PrefixGraph:
    """A prefix graph over n positions: nodes {(lo, hi): (k, q)}."""

    def __init__(self, n: int):
        if n < 1:
            raise ValueError("a prefix graph needs at least one position")
        self.n = n
        self.nodes: dict[tuple[int, int], tuple[int, int]] = {}
        # a node of valency above 2: its parents as spans, the most significant first (the binary
        # entry in `nodes` holds the top split so the metrics and the pruning see it)
        self.multi: dict[tuple[int, int], list] = {}

    def add_multi(self, parents: list) -> tuple[int, int]:
        """Add the node over contiguous parent spans (most significant first)."""
        parents = list(parents)
        for (plo, phi), (nlo, nhi) in zip(parents, parents[1:]):
            if nhi != plo - 1:
                raise ValueError(f"parents {parents} are not contiguous")
        for (plo, phi) in parents:
            if not self.has(plo, phi):
                raise ValueError(f"parent [{plo}, {phi}] is missing")
        lo, hi = parents[-1][0], parents[0][1]
        if len(parents) == 2:
            self.nodes[(lo, hi)] = (parents[0][0], parents[1][1])
            return (lo, hi)
        self.nodes[(lo, hi)] = (parents[0][0], parents[0][0] - 1)
        self.multi[(lo, hi)] = parents
        return (lo, hi)

    def parents_of(self, key: tuple) -> list:
        if key in self.multi:
            return list(self.multi[key])
        lo, hi = key
        k, q = self.nodes[key]
        return [(k, hi), (lo, q)]

    # ---- construction -------------------------------------------------
    def has(self, lo: int, hi: int) -> bool:
        return lo == hi or (lo, hi) in self.nodes

    def add(self, hi: int, lo: int, k: int | None = None, q: int | None = None) -> tuple[int, int]:
        """Add the node [lo, hi]. With k (and q) given, the parents are
        [k, hi] and [lo, q] and must exist. Without them, the PrefixRL
        rule applies: the upper parent is the nearest existing span of
        row hi above lo (the leaf when none), and the lower parent
        [lo, k-1] is added recursively when missing."""
        if not (0 <= lo < hi < self.n):
            raise ValueError(f"span [{lo}, {hi}] outside 0..{self.n - 1}")
        if k is None:
            # the nearest node of the row: the smallest lo above ours (the leaf when none)
            k = min([ll for (ll, hh) in self.nodes if hh == hi and ll > lo], default=hi)
            q = k - 1
            if not self.has(lo, q):
                self.add(q, lo)
        if q is None:
            q = k - 1
        if not (lo < k <= q + 1 <= hi and q < hi):
            raise ValueError(f"node [{lo}, {hi}]: parents [{k}, {hi}] and [{lo}, {q}] do not split it")
        if not self.has(k, hi) or not self.has(lo, q):
            raise ValueError(f"node [{lo}, {hi}]: a parent [{k}, {hi}] or [{lo}, {q}] is missing")
        self.nodes[(lo, hi)] = (k, q)
        return (lo, hi)

    def remove(self, hi: int, lo: int) -> None:
        """Remove the node [lo, hi] (a carry output [0, hi] is rebuilt
        from the next node of its row, as PrefixRL keeps the outputs),
        then re-legalize every child on the exact-split rule."""
        if (lo, hi) not in self.nodes:
            return
        del self.nodes[(lo, hi)]
        if lo == 0:
            self.add(hi, 0)          # the output stays; its upper parent moves up the row
            return
        for (ll, hh), (k, q) in list(self.nodes.items()):
            if (k == lo and hh == hi) or (ll == lo and q == hi):
                del self.nodes[(ll, hh)]
                self.add(hh, ll)

    def complete(self) -> bool:
        return all((0, i) in self.nodes for i in range(1, self.n))

    def validate(self) -> None:
        for (lo, hi), (k, q) in self.nodes.items():
            if (lo, hi) in self.multi:
                for plo, phi in self.multi[(lo, hi)]:
                    if not self.has(plo, phi):
                        raise ValueError(f"node [{lo}, {hi}]: missing parent [{plo}, {phi}]")
                continue
            if not (lo < k <= q + 1 <= hi and q < hi):
                raise ValueError(f"node [{lo}, {hi}]: bad split k={k} q={q}")
            if not self.has(k, hi) or not self.has(lo, q):
                raise ValueError(f"node [{lo}, {hi}]: missing parent")
        if not self.complete():
            missing = [i for i in range(1, self.n) if (0, i) not in self.nodes]
            raise ValueError(f"incomplete: no carry node for positions {missing[:8]}")
        self.levels()               # raises on a cycle

    # ---- metrics ------------------------------------------------------
    def level_of(self) -> dict[tuple[int, int], int]:
        memo: dict[tuple[int, int], int] = {}
        visiting: set = set()

        def lv(lo, hi):
            if lo == hi:
                return 0
            key = (lo, hi)
            if key in memo:
                return memo[key]
            if key in visiting:
                raise ValueError(f"cycle through [{lo}, {hi}]")
            visiting.add(key)
            memo[key] = 1 + max(lv(plo, phi) for plo, phi in self.parents_of(key))
            visiting.discard(key)
            return memo[key]

        for key in self.nodes:
            lv(*key)
        return memo

    def levels(self) -> int:
        lv = self.level_of()
        return max(lv.values(), default=0)

    def size(self) -> int:
        return len(self.nodes)

    def children(self) -> dict[tuple[int, int], list]:
        out: dict[tuple[int, int], list] = {}
        for key in self.nodes:
            for par in self.parents_of(key):
                out.setdefault(par, []).append(key)
        return out

    def fanout(self) -> int:
        """The largest number of nodes any node or leaf feeds (PrefixRL's
        fanout; Harris' 2^f + 1 adds the sum XOR of an output node)."""
        return max((len(v) for v in self.children().values()), default=0)

    def tracks(self) -> int:
        """The wire tracks of Harris: per level, the number of distinct
        lower-parent nets crossing a channel between two columns (a net
        fanning out to several nodes is one track); the maximum over
        channels and levels. Kogge-Stone gives n/2, Sklansky 1."""
        lv = self.level_of()
        best = 0
        by_level: dict[int, set] = {}
        for (lo, hi), (k, q) in self.nodes.items():
            by_level.setdefault(lv[(lo, hi)], set()).add(((lo, q), hi))
        for nets in by_level.values():
            cross: dict[int, set] = {}
            for src, hi in nets:
                for c in range(src[1], hi):          # channel c+0.5 for src.hi <= c < hi
                    cross.setdefault(c, set()).add(src)
            best = max(best, max((len(v) for v in cross.values()), default=0))
        return best

    def exact_split(self) -> bool:
        """True when no node overlaps its parents (q = k-1 everywhere):
        the PrefixRL grid and the compact notation cover such graphs."""
        return all(q == k - 1 for (k, q) in self.nodes.values()) and not self.multi

    def valency(self) -> int:
        return max([len(v) for v in self.multi.values()] + [2 if self.nodes else 1])

    def summary(self) -> dict:
        return {"n": self.n, "levels": self.levels(), "size": self.size(), "fanout": self.fanout(),
                "tracks": self.tracks(), "exact_split": self.exact_split(), "valency": self.valency()}

    # ---- notation -----------------------------------------------------
    def sequence(self) -> list[int]:
        """Roy et al.'s compact notation: the MSB (hi) of every node in
        topological order, the higher bits first within a level. A graph
        round-trips through from_sequence when every node's upper parent
        is its row's longest span so far and its lower parent the longest
        span of row k-1 (the exact-split graphs the generators build)."""
        if self.multi:
            raise ValueError("the compact notation covers binary graphs")
        lv = self.level_of()
        return [hi for (lo, hi) in sorted(self.nodes, key=lambda s: (lv[s], -s[1]))]

    @classmethod
    def from_sequence(cls, n: int, seq: list[int]) -> "PrefixGraph":
        """Rebuild from the compact notation: each index hi makes the node
        whose upper parent is the most recent node of row hi (or the leaf)
        and whose lower parent is the node just below that parent's lo."""
        g = cls(n)
        recent: dict[int, tuple[int, int]] = {}
        for hi in seq:
            up = recent.get(hi, (hi, hi))
            k = up[0]
            if k == 0:
                raise ValueError(f"row {hi} is already complete")
            low = recent.get(k - 1, (k - 1, k - 1))
            g.nodes[(low[0], hi)] = (k, k - 1)
            recent[hi] = (low[0], hi)
        return g

    def grid(self) -> str:
        """The n x n picture PrefixRL uses: row hi, column lo, one
        character per cell (# node, . none, o leaf)."""
        rows = []
        for hi in range(self.n - 1, -1, -1):
            cells = []
            for lo in range(self.n):
                cells.append("o" if lo == hi else ("#" if (lo, hi) in self.nodes else ("." if lo < hi else " ")))
            rows.append(f"{hi:3d} " + "".join(cells))
        return "\n".join(rows)

    # ---- emission -----------------------------------------------------
    def _emit_nodes(self, flagged_p: bool) -> tuple:
        """([wires], [assigns]) of every node's G (and P where a node is not
        a carry output, or always under flagged_p) from g0 / p0."""
        lv = self.level_of()
        order = sorted(self.nodes, key=lambda s: (lv[s], s[1]))
        wires, assigns = [], []

        def gp(plo, phi):
            return (f"g0[{phi}]", f"p0[{phi}]") if plo == phi else (f"G_{plo}_{phi}", f"P_{plo}_{phi}")

        for (lo, hi) in order:
            pars = self.parents_of((lo, hi))
            # G = G_1 | P_1 (G_2 | P_2 (... G_v)); P = P_1 & ... & P_v, the most significant parent first
            gs, ps = zip(*(gp(plo, phi) for plo, phi in pars))
            expr = gs[-1]
            for gk, pk in reversed(list(zip(gs[:-1], ps[:-1]))):
                expr = f"{gk} | ({pk} & ({expr}))" if "|" in expr else f"{gk} | ({pk} & {expr})"
            wires.append(f"G_{lo}_{hi}")
            assigns.append(f"  assign G_{lo}_{hi} = {expr};")
            if lo != 0 or flagged_p:
                wires.append(f"P_{lo}_{hi}")
                assigns.append(f"  assign P_{lo}_{hi} = {' & '.join(ps)};")
        return wires, assigns

    def to_sv(self, name: str, ling: bool = False, flagged: bool = False, flag_from_p: bool = True,
              ling_group: int = 1, sum_recovery: str = "xor_correction", flag_outputs: str = "sum_sum1",
              flag_impl: str = "flag_row", late_cin: bool = False, width: int | None = None) -> str:
        """An adder module over the graph: W = n data bits (n = W for a plain
        graph; n = the block count under a Ling group above 1), the
        carry-in absorbed into position 0's generate (g_0 | p_0 cin), or
        entering at the output row under `late_cin` (c_i = G | P cin).
        LING feeds the pseudo-carry pre-signals (Ling 1981): per bit
        (ling_group 1) the pairs (g_i, t_{i-1}) with c_{i+1} = t_i H_i;
        per block of ling_group bits the block pseudo-generate H_b (the
        top transfer factored out) and the shifted block transfer, the
        block's carries then by a ripple from the block carry-in
        (sum_recovery xor_correction) or by conditional sums selected by
        it (late_select_mux). FLAGGED adds s1 = s + 1 (flag_outputs
        sum_sum1) and sm1 = s - 1 (sum_sum1_summinus1) from the flag row
        f_i = p_0 ... p_{i-1}, which the tree's P outputs provide
        (Burgess 2002), or from a second carry tree with the carry-in
        forced (flag_impl dual_carry_tree)."""
        n = self.n
        W = width if width else (n * ling_group if (ling and ling_group > 1) else n)
        out = [f"module {name} (input logic [{W-1}:0] a, input logic [{W-1}:0] b, input logic cin,",
               f"  output logic [{W-1}:0] s, output logic cout"
               + (f", output logic [{W-1}:0] s1" if flagged else "")
               + (f", output logic [{W-1}:0] sm1" if flagged and flag_outputs == "sum_sum1_summinus1" else "") + ");",
               f"  // prefix graph: {self.summary()}",
               f"  logic [{W-1}:0] gi, pi_, ti;",
               "  assign gi = a & b;", "  assign pi_ = a ^ b;", "  assign ti = a | b;"]
        if ling and ling_group > 1:
            return self._to_sv_ling_blocks(name, out, W, ling_group, sum_recovery)
        out.append(f"  logic [{W-1}:0] g0, p0;")
        if ling:
            out += ["  assign g0 = {gi[%d:1], gi[0] | cin};" % (W - 1) if W >= 2 else "  assign g0 = gi | cin;",
                    "  assign p0 = " + ("{ti[%d:0], 1'b0};" % (W - 2) if W >= 2 else "1'b0;")]
        elif late_cin:
            out += ["  assign g0 = gi;", "  assign p0 = pi_;"]
        else:
            out += ["  assign g0 = {gi[%d:1], gi[0] | (pi_[0] & cin)};" % (W - 1) if W >= 2
                    else "  assign g0 = gi | (pi_ & cin);",
                    "  assign p0 = pi_;"]
        wires, assigns = self._emit_nodes(flagged or late_cin)
        if wires:
            out.append("  logic " + ", ".join(wires) + ";")
        out += assigns
        # the carries: c[i+1] into bit i+1 is the node [0, i] (position 0 alone holds the absorbed carry-in)
        out.append(f"  logic [{W}:0] c;")
        out.append("  assign c[0] = cin;")

        def G(i):
            return "g0[0]" if i == 0 else f"G_0_{i}"

        def P(i):
            return "p0[0]" if i == 0 else f"P_0_{i}"

        for i in range(0, W):
            if ling:
                out.append(f"  assign c[{i+1}] = ti[{i}] & {G(i)};")
            elif late_cin:
                out.append(f"  assign c[{i+1}] = {G(i)} | ({P(i)} & cin);")
            else:
                out.append(f"  assign c[{i+1}] = {G(i)};")
        if ling and sum_recovery == "late_select_mux":
            # the conditional sums per bit, selected by the pseudo-carry (the AND with t moved before the select)
            out.append("  assign s[0] = pi_[0] ^ cin;")
            for i in range(1, W):
                out.append(f"  assign s[{i}] = {G(i-1)} ? (pi_[{i}] ^ ti[{i-1}]) : pi_[{i}];")
        else:
            out.append(f"  assign s = pi_ ^ c[{W-1}:0];")
        out.append(f"  assign cout = c[{W}];")
        if flagged:
            if flag_impl == "dual_carry_tree" and not ling:
                # a second carry network with the carry-in forced to one; under late_cin it is the P path
                if late_cin:
                    out.append(f"  logic [{W}:0] c1;")
                    out.append("  assign c1[0] = 1'b1;")
                    for i in range(0, W):
                        out.append(f"  assign c1[{i+1}] = {G(i)} | {P(i)};")
                else:
                    out.append(f"  logic [{W-1}:0] g1, p1;")
                    out.append("  assign g1 = {gi[%d:1], gi[0] | pi_[0]};" % (W - 1) if W >= 2 else "  assign g1 = gi | pi_;")
                    out.append("  assign p1 = pi_;")
                    w1, a1 = self._emit_nodes(False)
                    ren = [(w, w.replace("G_", "H_", 1).replace("P_", "Q_", 1)) for w in w1]
                    if ren:
                        out.append("  logic " + ", ".join(new for _o, new in ren) + ";")
                    for a in a1:
                        for old, new in ren:
                            a = re.sub(r"\b" + old + r"\b", new, a)
                        out.append(a.replace("g0[", "g1[").replace("p0[", "p1["))
                    out.append(f"  logic [{W}:0] c1;")
                    out.append("  assign c1[0] = 1'b1;")
                    for i in range(0, W):
                        out.append(f"  assign c1[{i+1}] = " + ("g1[0]" if i == 0 else f"H_0_{i}") + ";")
                out.append(f"  assign s1 = pi_ ^ c1[{W-1}:0];")
            else:
                if flag_from_p and not ling:      # the Ling tree's P is over t, not p
                    # f_i = p_0 & ... & p_{i-1}: the tree's P[0, i-1] when the node exists, else a plain AND
                    fl = ["1'b1", "pi_[0]"] + [(f"P_0_{i-1}" if (0, i - 1) in self.nodes else f"(&pi_[{i-1}:0])")
                                                for i in range(2, W)]
                    out.append("  logic [%d:0] f;" % (W - 1))
                    for i, e in enumerate(fl[:W]):
                        out.append(f"  assign f[{i}] = {e};")
                else:
                    out.append("  logic [%d:0] f;" % (W - 1))
                    out.append("  assign f[0] = 1'b1;")
                    for i in range(1, W):
                        out.append(f"  assign f[{i}] = f[{i-1}] & s[{i-1}];")
                out.append("  assign s1 = s ^ f;")
            if flag_outputs == "sum_sum1_summinus1":
                # s - 1 flips the bits up to and including the lowest one of s: the not-kill flag row over s
                out.append("  logic [%d:0] fm;" % (W - 1))
                out.append("  assign fm[0] = 1'b1;")
                for i in range(1, W):
                    out.append(f"  assign fm[{i}] = fm[{i-1}] & ~s[{i-1}];")
                out.append("  assign sm1 = s ^ fm;")
        out.append("endmodule")
        return "\n".join(out) + "\n"

    def _to_sv_ling_blocks(self, name: str, out: list, W: int, k: int, sum_recovery: str) -> str:
        """The Ling adder over blocks of k bits: the graph spans the block
        positions; block b's pre-signals are H_b (its generate with the
        top transfer factored out, the carry-in absorbed in bit 0) and
        T'_b t_top(b-1) (its transfer without the top bit, times the
        previous block's top transfer), the tree's output the block
        pseudo-carry Hc_b with the block carry-out t_top(b) Hc_b; inside
        a block the carries ripple from the block carry-in (xor_correction)
        or select precomputed conditional sums (late_select_mux)."""
        n = self.n
        blocks = [(b * k, min(b * k + k, W)) for b in range(n)]
        out.append(f"  logic [{W-1}:0] gc;")
        out.append("  assign gc = {gi[%d:1], gi[0] | (pi_[0] & cin)};" % (W - 1) if W >= 2 else "  assign gc = gi | (pi_ & cin);")
        out.append(f"  logic [{n-1}:0] g0, p0;")
        for b, (lo, hi) in enumerate(blocks):
            top = hi - 1
            # H_b = g_top | g_{top-1} | t_{top-1} g_{top-2} | ... (the block generate less the top transfer)
            terms = [f"gc[{top}]"]
            pre = ""
            for i in range(top - 1, lo - 1, -1):
                terms.append((pre + f"gc[{i}]") if pre else f"gc[{i}]")
                pre += f"ti[{i}] & "
            out.append(f"  assign g0[{b}] = " + " | ".join(f"({t})" if "&" in t else t for t in terms) + ";")
            tr = " & ".join([f"ti[{i}]" for i in range(lo, top)] + ([f"ti[{blocks[b-1][1]-1}]"] if b > 0 else []))
            out.append(f"  assign p0[{b}] = " + (tr if b > 0 else "1'b0") + ";")
        wires, assigns = self._emit_nodes(False)
        if wires:
            out.append("  logic " + ", ".join(wires) + ";")
        out += assigns
        # the block carries: into block b, the carry-out of block b-1 = t_top(b-1) & Hc_{b-1}
        out.append(f"  logic [{n}:0] bc;")
        out.append("  assign bc[0] = cin;")
        for b, (lo, hi) in enumerate(blocks):
            hc = "g0[0]" if b == 0 else f"G_0_{b}"
            out.append(f"  assign bc[{b+1}] = ti[{hi-1}] & {hc};")
        for b, (lo, hi) in enumerate(blocks):
            nb = hi - lo
            if sum_recovery == "late_select_mux":
                # the block's conditional sums for a carry-in of 0 and 1, selected by the block carry
                for cv in (0, 1):
                    out.append(f"  logic [{nb}:0] r{cv}_{b};")
                    out.append(f"  assign r{cv}_{b}[0] = 1'b{cv};")
                    for i in range(nb):
                        out.append(f"  assign r{cv}_{b}[{i+1}] = gc[{lo+i}] | (pi_[{lo+i}] & r{cv}_{b}[{i}]);")
                for i in range(nb):
                    out.append(f"  assign s[{lo+i}] = pi_[{lo+i}] ^ (bc[{b}] ? r1_{b}[{i}] : r0_{b}[{i}]);")
            else:
                out.append(f"  logic [{nb}:0] r_{b};")
                out.append(f"  assign r_{b}[0] = bc[{b}];")
                for i in range(nb):
                    out.append(f"  assign r_{b}[{i+1}] = gc[{lo+i}] | (pi_[{lo+i}] & r_{b}[{i}]);")
                    out.append(f"  assign s[{lo+i}] = pi_[{lo+i}] ^ r_{b}[{i}];")
        out.append(f"  assign cout = bc[{n}];")
        out.append("endmodule")
        return "\n".join(out) + "\n"

    def to_network_sv(self, name: str) -> str:
        """A carry network over the graph's positions from generate and
        propagate pairs: (input [n-1:0] g, p, input cin, output [n-1:0] c,
        output cout), c[i] the carry into position i."""
        n = self.n
        out = [f"module {name} (input logic [{n-1}:0] g, input logic [{n-1}:0] p, input logic cin,",
               f"  output logic [{n-1}:0] c, output logic cout);",
               f"  // prefix graph: {self.summary()}",
               f"  logic [{n-1}:0] g0, p0;",
               "  assign g0 = {g[%d:1], g[0] | (p[0] & cin)};" % (n - 1) if n >= 2 else "  assign g0 = g | (p & cin);",
               "  assign p0 = p;"]
        wires, assigns = self._emit_nodes(False)
        if wires:
            out.append("  logic " + ", ".join(wires) + ";")
        out += assigns
        out.append("  assign c[0] = cin;")
        for i in range(1, n):
            out.append(f"  assign c[{i}] = " + ("g0[0]" if i == 1 else f"G_0_{i-1}") + ";")
        out.append("  assign cout = " + ("g0[0]" if n == 1 else f"G_0_{n-1}") + ";")
        out.append("endmodule")
        return "\n".join(out) + "\n"


# ---- the regular networks -------------------------------------------------
def _L(n: int) -> int:
    return max(1, (n - 1).bit_length())


def ripple(n: int) -> PrefixGraph:
    g = PrefixGraph(n)
    for i in range(1, n):
        g.add(i, 0, k=i, q=i - 1)
    return g


def kogge_stone(n: int) -> PrefixGraph:
    return knowles(n, 0)


def sklansky(n: int) -> PrefixGraph:
    return knowles(n, _L(n) - 1)


def knowles(n: int, f: int, fanouts: list[int] | None = None) -> PrefixGraph:
    """The Knowles network [k_L .. k_1]: level j combines position i with
    the level j-1 node at (i - 2^(j-1)) | (k_j - 1); k_j = 2^f at the top
    halving per level down to 1 gives Harris' (0, f, t)."""
    L = _L(n)
    if fanouts is None:
        fanouts = [max(1, 2 ** (f - (L - j))) for j in range(1, L + 1)]     # index j-1 = level j
    fanouts = (list(fanouts) + [1] * L)[:L]
    g = PrefixGraph(n)
    span = {i: (i, i) for i in range(n)}                                     # the current node per position
    for j in range(1, L + 1):
        d = 2 ** (j - 1)
        k = min(fanouts[j - 1], d)
        new = dict(span)
        for i in range(n):
            lo, hi = span[i]
            if lo == 0:
                continue
            p = (i - d) | (k - 1)
            p = min(p, i - 1)
            if p < 0:
                continue
            plo, phi = span[p]
            # contiguity: the lower parent reaches up to the upper parent's lo - 1 at least
            if phi < lo - 1:
                p = lo - 1
                plo, phi = span[p]
            _join(g, i, lo, plo, phi)
            new[i] = (plo, i)
        span = new
    for i in range(1, n):
        if span[i][0] != 0:
            raise ValueError(f"knowles({n}, {f}): position {i} incomplete")
    _prune(g)
    return g


def _join(g: PrefixGraph, i: int, lo: int, plo: int, phi: int) -> None:
    """The node [plo, i] from the lower parent [plo, phi] and the upper
    parent of row i that splits exactly at phi+1 when one exists (a
    shorter span of the same row), else the row's current node [lo, i]."""
    up = phi + 1 if phi + 1 > lo and g.has(phi + 1, i) else lo
    if (plo, i) in g.nodes:
        return
    g.add(i, plo, k=up, q=phi)


def harris(n: int, l: int, f: int, t: int | None = None) -> PrefixGraph:
    """Harris' (l, f, t) point: l pairwise levels, Knowles (0, f, t) on
    every 2^l-th position, l levels filling the rest. l and f are
    clipped to the width's L = log2 n (l <= L-1, f <= L-1-l) and t
    follows, so one (l, f) names a point at every width; a given t is
    checked against that."""
    L = _L(n)
    l = max(0, min(l, L - 1))
    f = max(0, min(f, L - 1 - l))
    if t is not None and t != L - 1 - l - f:
        raise ValueError(f"harris: l + f + t must be {L - 1} for n = {n} (got l={l} f={f} t={t})")
    t = L - 1 - l - f
    if l == 0:
        return knowles(n, f)
    g = PrefixGraph(n)
    span = {i: (i, i) for i in range(n)}
    # up-sweep: l levels; at level j the positions i with (i + 1) % 2^j == 0 take the node 2^(j-1) below
    for j in range(1, l + 1):
        d = 2 ** (j - 1)
        new = dict(span)
        for i in range(n):
            if (i + 1) % (2 * d) == 0 and i - d >= 0 and span[i][0] != 0:
                lo, hi = span[i]
                plo, phi = span[i - d]
                if phi >= lo - 1:
                    _join(g, i, lo, plo, phi)
                    new[i] = (plo, i)
        span = new
    # the sparse Knowles network on positions i = m * 2^l - 1 (m >= 1): after the up-sweep each holds
    # [(m-1) * 2^l, i], the first one [0, 2^l - 1] complete
    step = 2 ** l
    pos = [i for i in range(n) if (i + 1) % step == 0]
    sub_n = len(pos)
    Ls = _L(sub_n)
    fanouts = [max(1, 2 ** (f - (Ls - j))) for j in range(1, Ls + 1)]
    cur = {m: span[pos[m]] for m in range(sub_n)}
    for j in range(1, Ls + 1):
        d = 2 ** (j - 1)
        k = min(fanouts[j - 1], d)
        new = dict(cur)
        for m in range(1, sub_n):
            lo, hi = cur[m]
            if lo == 0:
                continue
            pm = (m - d) | (k - 1)
            pm = min(pm, m - 1)
            if pm < 0:
                continue
            plo, phi = cur[pm]
            if phi < lo - 1:
                # walk down to the sparse node just below our span
                cands = [mm for mm in range(m) if cur[mm][1] >= lo - 1 and cur[mm][1] < hi]
                pm = max(cands)
                plo, phi = cur[pm]
            _join(g, hi, lo, plo, phi)
            new[m] = (plo, hi)
        cur = new
    for m in range(1, sub_n):
        span[pos[m]] = cur[m]
    # down-sweep: l levels; at level j (from the top), the positions at odd multiples of 2^(l-j) take the sparse node below
    for j in range(l, 0, -1):
        d = 2 ** (j - 1)
        new = dict(span)
        for i in range(n):
            lo, hi = span[i]
            if lo == 0 or (i + 1) % (2 * d) != d or (i + 1) % (2 * d) == 0:
                continue
            p = i - d
            if p < 0:
                continue
            plo, phi = span[p]
            if phi >= lo - 1:
                _join(g, i, lo, plo, phi)
                new[i] = (plo, i)
        span = new
    for i in range(1, n):
        if span[i][0] != 0:
            raise ValueError(f"harris({n}, {l}, {f}, {t}): position {i} incomplete")
    _prune(g)
    return g


def brent_kung(n: int) -> PrefixGraph:
    return harris(n, _L(n) - 1, 0, 0)


def han_carlson(n: int) -> PrefixGraph:
    L = _L(n)
    return harris(n, 1, 0, L - 2) if L >= 2 else kogge_stone(n)


def ladner_fischer(n: int, l: int = 1) -> PrefixGraph:
    L = _L(n)
    l = max(0, min(l, L - 1))
    return harris(n, l, L - 1 - l, 0)


def knowles_mixed(n: int) -> PrefixGraph:
    """The midpoint of the Knowles row: f = (L-1) // 2."""
    return knowles(n, (_L(n) - 1) // 2)


def nonuniform_arrival(n: int, arrival: list[int], target: int | None = None) -> PrefixGraph:
    """A greedy prefix graph for per-position arrival times (in levels):
    at each time step every position whose current node and whose
    lower neighbour's node are ready combines them (Kogge-Stone among
    the ready positions, which ripples the early bits while the late
    ones arrive); then a size-decreasing pass reuses a neighbour's
    lower parent wherever the output time stays within the target,
    which is the depth-decreasing / size-decreasing pair of Zimmermann
    (1996) in greedy form. arrival[i] is the time of bit i in levels."""
    if len(arrival) != n:
        raise ValueError(f"arrival needs {n} entries")
    g = PrefixGraph(n)
    span = {i: (i, i) for i in range(n)}
    ready = {i: arrival[i] for i in range(n)}
    t = min(arrival)
    guard = 0
    while any(span[i][0] != 0 for i in range(1, n)):
        guard += 1
        if guard > 4 * n + 64:
            raise ValueError("nonuniform_arrival did not converge")
        new = dict(span)
        newr = dict(ready)
        for i in range(1, n):
            lo, hi = span[i]
            if lo == 0 or ready[i] > t:
                continue
            p = lo - 1
            plo, phi = span[p]
            if ready[p] > t:
                continue
            _join(g, i, lo, plo, phi)
            new[i] = (plo, i)
            newr[i] = t + 1
        span, ready = new, newr
        t += 1
    depth = max(ready.values())
    if target is not None and target > depth:
        depth = target
    # size-decreasing pass: a node [lo, hi] with slack whose lower neighbour's node [lo', hi-1] shares lo
    # can take that neighbour's upper parent chain: replace lower parent by the largest node [lo, q] with q < hi
    # that a lower row already computes, when the level stays within the depth
    changed = True
    while changed:
        changed = False
        lv = g.level_of()
        # times: level + arrival offsets are folded in the greedy build; here re-time from the graph
        for (lo, hi), (k, q) in sorted(g.nodes.items(), key=lambda kv: (-kv[0][1], kv[0][0])):
            if lo != 0:
                continue
            # candidates: nodes [0, q'] with q' < q whose upper span [q'+1, hi] exists
            for q2 in range(q - 1, -1, -1):
                if (0, q2) in g.nodes or q2 == 0:
                    if g.has(q2 + 1, hi):
                        old = g.nodes[(0, hi)]
                        g.nodes[(0, hi)] = (q2 + 1, q2)
                        try:
                            new_lv = g.level_of()
                        except ValueError:
                            g.nodes[(0, hi)] = old
                            continue
                        if new_lv[(0, hi)] + 0 <= lv[(0, hi)] and _timed_depth(g, arrival) <= depth:
                            changed = True
                            break
                        g.nodes[(0, hi)] = old
    _prune(g)
    return g


def _timed_depth(g: PrefixGraph, arrival: list[int]) -> int:
    memo: dict = {}

    def tm(lo, hi):
        if lo == hi:
            return arrival[lo]
        if (lo, hi) in memo:
            return memo[(lo, hi)]
        k, q = g.nodes[(lo, hi)]
        memo[(lo, hi)] = 1 + max(tm(k, hi), tm(lo, q))
        return memo[(lo, hi)]

    return max(tm(0, i) for i in range(1, g.n))


def _prune(g: PrefixGraph) -> None:
    """Drop nodes no output depends on."""
    live: set = set()
    stack = [(0, i) for i in range(1, g.n) if (0, i) in g.nodes]
    while stack:
        key = stack.pop()
        if key in live or key not in g.nodes:
            continue
        live.add(key)
        stack += g.parents_of(key)
    for key in list(g.nodes):
        if key not in live:
            del g.nodes[key]
            g.multi.pop(key, None)


def _radix_sklansky(n: int, v: int) -> PrefixGraph:
    """Sklansky at valency v: level l merges v blocks of v^l positions;
    the positions of the upper blocks take the ends of every lower block
    of the group (a node of up to v parents)."""
    g = PrefixGraph(n)
    span = {i: (i, i) for i in range(n)}
    d = 1
    while d < n:
        new = dict(span)
        for i in range(n):
            lo, hi = span[i]
            if lo == 0:
                continue
            j = (i // d) % v                     # the block of position i inside its group of v blocks
            if j == 0:
                continue
            base = (i // (d * v)) * (d * v)      # the group's first position
            pars = [span[i]]
            for m in range(j - 1, -1, -1):
                end = base + m * d + d - 1
                pars.append(span[end])
                if span[end][0] == 0:
                    break
            # the parents must chain: each next parent ends where the previous begins minus one
            chain = [pars[0]]
            for pr in pars[1:]:
                if pr[1] == chain[-1][0] - 1:
                    chain.append(pr)
                else:
                    break
            if len(chain) < 2:
                continue
            new[i] = g.add_multi(chain)
        span = new
        d *= v
    for i in range(1, n):
        if span[i][0] != 0:
            raise ValueError(f"radix-{v} sklansky({n}): position {i} incomplete")
    _prune(g)
    return g


def _radix_kogge_stone(n: int, v: int) -> PrefixGraph:
    """Kogge-Stone at valency v: at level l every position combines its span
    with the spans of the positions d, 2d, ... (v-1)d below it (d = v^l)."""
    g = PrefixGraph(n)
    span = {i: (i, i) for i in range(n)}
    d = 1
    while d < n:
        new = dict(span)
        for i in range(n):
            lo, hi = span[i]
            if lo == 0:
                continue
            chain = [span[i]]
            for m in range(1, v):
                pos = i - m * d
                if pos < 0:
                    break
                pr = span[pos]
                if pr[1] != chain[-1][0] - 1:
                    break
                chain.append(pr)
                if pr[0] == 0:
                    break
            if len(chain) >= 2:
                new[i] = g.add_multi(chain)
        span = new
        d *= v
    for i in range(1, n):
        if span[i][0] != 0:
            raise ValueError(f"radix-{v} kogge_stone({n}): position {i} incomplete")
    _prune(g)
    return g


def _radix_brent_kung(n: int, v: int) -> PrefixGraph:
    """Brent-Kung at valency v: an up-sweep whose level l merges the v
    spans of v^l positions ending at positions (i+1) % v^(l+1) == 0, then a
    down-sweep filling the other positions from the complete node below."""
    g = PrefixGraph(n)
    span = {i: (i, i) for i in range(n)}
    d = 1
    while d < n:
        new = dict(span)
        for i in range(n):
            if (i + 1) % (d * v) != 0 or span[i][0] == 0:
                continue
            chain = [span[i]]
            for m in range(1, v):
                pos = i - m * d
                if pos < 0:
                    break
                pr = span[pos]
                if pr[1] != chain[-1][0] - 1:
                    break
                chain.append(pr)
                if pr[0] == 0:
                    break
            if len(chain) >= 2:
                new[i] = g.add_multi(chain)
        span = new
        d *= v
    # the down-sweep: from the coarsest level down, an incomplete position takes the complete node below its span
    levels = []
    dd = 1
    while dd < n:
        levels.append(dd)
        dd *= v
    for d in reversed(levels):
        new = dict(span)
        for i in range(n):
            lo, hi = span[i]
            if lo == 0:
                continue
            below = lo - 1
            if below >= 0 and span[below][0] == 0 and (hi - lo + 1) == d:
                new[i] = g.add_multi([span[i], span[below]])
        span = new
    # the positions still open (spans shorter than a level width) take the node below
    changed = True
    while changed:
        changed = False
        for i in range(1, n):
            lo, hi = span[i]
            if lo != 0 and span[lo - 1][0] == 0:
                span[i] = g.add_multi([span[i], span[lo - 1]])
                changed = True
    for i in range(1, n):
        if span[i][0] != 0:
            raise ValueError(f"radix-{v} brent_kung({n}): position {i} incomplete")
    _prune(g)
    return g


RADIX_TOPOLOGIES = {"sklansky": _radix_sklansky, "kogge_stone": _radix_kogge_stone, "brent_kung": _radix_brent_kung}


def build(n: int, spec: str, valency: int = 2) -> PrefixGraph:
    """A graph from a spec string: a named topology (kogge_stone,
    sklansky, brent_kung, ladner_fischer[:l], han_carlson,
    knowles_mixed, ripple), harris:l<l>f<f>t<t>, knowles:<f> or
    knowles:k_L,...,k_1, seq:<indices> (Roy et al.), or
    arrival:<t0>,<t1>,...[:target]."""
    kind, _, arg = spec.partition(":")
    if valency > 2:
        if kind not in RADIX_TOPOLOGIES:
            raise ValueError(f"valency {valency} is built for {', '.join(RADIX_TOPOLOGIES)}; {kind} is binary")
        return RADIX_TOPOLOGIES[kind](n, valency)
    if kind == "kogge_stone":
        return kogge_stone(n)
    if kind == "sklansky":
        return sklansky(n)
    if kind == "brent_kung":
        return brent_kung(n)
    if kind == "han_carlson":
        return han_carlson(n)
    if kind == "knowles_mixed":
        return knowles_mixed(n)
    if kind == "ripple":
        return ripple(n)
    if kind == "ladner_fischer":
        return ladner_fischer(n, int(arg) if arg else 1)
    if kind == "harris":
        vals = {}
        for key in "lft":
            i = arg.find(key)
            if i >= 0:
                j = i + 1
                while j < len(arg) and arg[j].isdigit():
                    j += 1
                vals[key] = int(arg[i + 1:j])
        return harris(n, vals.get("l", 0), vals.get("f", 0), vals.get("t"))
    if kind == "knowles":
        if "," in arg:
            ks = [int(x) for x in arg.split(",")]
            return knowles(n, 0, fanouts=list(reversed(ks)))
        return knowles(n, int(arg or 0))
    if kind == "seq":
        return PrefixGraph.from_sequence(n, [int(x) for x in arg.replace(",", " ").split()])
    if kind == "arrival":
        parts = arg.split(":")
        arr = [int(x) for x in parts[0].split(",")]
        target = int(parts[1]) if len(parts) > 1 else None
        return nonuniform_arrival(n, arr, target)
    raise ValueError(f"unknown prefix graph spec {spec!r}")


def apply_edits(g: PrefixGraph, edits: str) -> PrefixGraph:
    """'add <hi> <lo>; remove <hi> <lo>; ...' in PrefixRL's moves."""
    for e in edits.split(";"):
        e = e.strip()
        if not e:
            continue
        op, *args = e.split()
        hi, lo = int(args[0]), int(args[1])
        if op == "add":
            g.add(hi, lo)
        elif op == "remove":
            g.remove(hi, lo)
        else:
            raise ValueError(f"unknown edit {op!r}")
    return g


def module_name(spec: str, width: int, ling: bool, flagged: bool, valency: int = 2, ling_group: int = 1,
                sum_recovery: str = "xor_correction", flag_outputs: str = "sum_sum1", flag_impl: str = "flag_row",
                late_cin: bool = False) -> str:
    tag = "".join(ch if ch.isalnum() else "_" for ch in spec)
    name = f"fam_prefix_{tag}_w{width}" + (f"_v{valency}" if valency > 2 else "")
    if ling:
        name += "_ling" + (f"{ling_group}" if ling_group > 1 else "") + ("_sel" if sum_recovery == "late_select_mux" else "")
    if flagged:
        name += "_flag" + ("m" if flag_outputs == "sum_sum1_summinus1" else "") + ("_dual" if flag_impl == "dual_carry_tree" else "") \
                + ("_late" if late_cin else "")
    return name


def adder_sv(width: int, spec: str, ling: bool = False, flagged: bool = False, edits: str = "",
             name: str | None = None, valency: int = 2, ling_group: int = 1, sum_recovery: str = "xor_correction",
             flag_outputs: str = "sum_sum1", flag_impl: str = "flag_row", late_cin: bool = False) -> tuple[str, str, dict]:
    """(module name, SystemVerilog, summary) for an adder of `width` data
    bits whose carry network is the graph `spec` (plus edits) at the
    valency; a Ling adder groups ling_group bits per graph position."""
    module, text, metrics = _adder_sv_cached(width, spec, ling, flagged, edits, name, valency, ling_group,
                                            sum_recovery, flag_outputs, flag_impl, late_cin)
    return module, text, dict(metrics)


@lru_cache(maxsize=64, typed=True)
def _adder_sv_cached(width: int, spec: str, ling: bool, flagged: bool, edits: str, name: str | None,
                     valency: int, ling_group: int, sum_recovery: str, flag_outputs: str,
                     flag_impl: str, late_cin: bool) -> tuple:
    """Only immutable generated data is cached; family selection stays outside."""
    n = width
    if ling and ling_group > 1:
        n = (width + ling_group - 1) // ling_group
    g = build(n, spec, valency)
    if edits:
        apply_edits(g, edits)
    g.validate()
    name = name or module_name(spec, width, ling, flagged, valency, ling_group, sum_recovery, flag_outputs, flag_impl, late_cin)
    return name, g.to_sv(name, ling=ling, flagged=flagged, ling_group=ling_group if ling else 1, sum_recovery=sum_recovery,
                         flag_outputs=flag_outputs, flag_impl=flag_impl, late_cin=late_cin, width=width), tuple(g.summary().items())


def network_sv(n: int, spec: str, name: str, valency: int = 2) -> str:
    """The carry network module over n generate/propagate positions."""
    g = build(n, spec, valency)
    g.validate()
    return g.to_network_sv(name)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--width", type=int, required=True, help="data bits (one graph position per bit)")
    ap.add_argument("--graph", default="kogge_stone", help="see build(): kogge_stone, harris:l1f1t2, seq:..., arrival:...")
    ap.add_argument("--arrival", default=None, help="per-bit arrival times in levels, bit 0 first")
    ap.add_argument("--target", type=int, default=None, help="with --arrival: the output time to fit")
    ap.add_argument("--edit", default="", help='"add <hi> <lo>; remove <hi> <lo>; ..."')
    ap.add_argument("--ling", action="store_true")
    ap.add_argument("--flagged", action="store_true")
    ap.add_argument("--name", default=None)
    ap.add_argument("--sv", default=None, help="write the module here (default: stdout without --report)")
    ap.add_argument("--report", action="store_true", help="print the metrics, the grid and the compact sequence")
    args = ap.parse_args(argv)
    spec = args.graph
    if args.arrival:
        spec = f"arrival:{args.arrival}" + (f":{args.target}" if args.target is not None else "")
    try:
        name, sv, summ = adder_sv(args.width, spec, args.ling, args.flagged, args.edit, args.name)
    except ValueError as e:
        print(f"prefix: {e}", file=sys.stderr)
        return 2
    if args.sv:
        with open(args.sv, "w") as fh:
            fh.write(sv)
    if args.report or args.sv:
        g = build(args.width, spec)
        if args.edit:
            apply_edits(g, args.edit)
        print(f"{name}: " + ", ".join(f"{k}={v}" for k, v in summ.items()))
        if args.report:
            print(g.grid())
            print("seq: " + " ".join(str(x) for x in g.sequence()))
    if not args.sv and not args.report:
        sys.stdout.write(sv)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
