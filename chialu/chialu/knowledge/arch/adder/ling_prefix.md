# ling_prefix

Prefix addition on a pseudo-carry instead of the carry: Ling factors
the propagate of the least significant bit out of the group generate,
so the network propagates H_i = G_i + G_{i+1}, which is true when a
carry either enters or leaves bit i, under the recurrence H_i = g_i +
t_{i+1} H_{i+1} with the inclusive-OR transfer t_i = a_i + b_i. The
first-level function loses one term or one stack level, so a 4-bit H
is one INVERT-AND-OR stage plus a wire-OR where the group generate
needs 5-input gates, while every later prefix combination has the
same complexity as the ordinary group generate. The true carry is
recovered locally as H AND propagate and hidden in the sum stage.

In RTL the family shows as a prefix network whose leaves are the pair
(g_i, t_{i-1}) in place of (g_i, p_i), that is a generate vector with
the carry-in folded into g_0 and a transfer vector shifted by one
position (`p0 = {t[W-2:0], 1'b0}`), over any prefix topology (Sklansky,
Kogge-Stone, Brent-Kung); the true carry is recovered as `c[i+1] = t[i]
& H[i]`, and the sum either selects between the two conditional sums on
H (`s[i] = H[i-1] ? (p[i] ^ t[i-1]) : p[i]`, the sum-select form) or
corrects a preliminary sum with an XOR. A module of the library is
named `fam_prefix_<topology>_w<W>_ling_sel` for the sum-select form;
inside a lane-partitioned adder it appears as the segment module of
each lane, under the partitioned wrapper.

The pseudo-carry group sets where the saved stage lands: a 2-bit
pseudo-carry lets even- and odd-indexed pairs be associated in
separate prefix trees of log2 n - 1 levels, while a 4-bit group
matches ECL and dynamic gates of fan-in four and drives the
hierarchical lookahead like a G/P pair. The topology is any prefix
tree, because the change is confined to preprocessing; the pins on
record are Sklansky, Kogge-Stone and sparse Kogge-Stone. The sum
recovery choice decides where the extra AND of H and propagate goes:
a late select multiplexer picks between precomputed conditional sums
after H arrives, keeping the recovery off the critical path, at the
cost of sum precomputation whose complexity grows faster than the
carry tree's; the alternative corrects a preliminary sum with an XOR.
The order choice raises the factoring beyond one bit position.

The family is the high-speed pick for wide adders when the carry tree
is critical, because the shorter first-stage stack permits a larger
first gate under the same input capacitance: the HP 64-bit adder in
0.5-µm dual-rail dynamic CMOS reaches 0.93 ns on a 4-gate critical
path against 8 gates for a group-of-2 lookahead, and the parity-tree
form saves about 13 percent of delay over Ladner-Fischer and
Kogge-Stone in 0.18-µm static CMOS. A group of 16 also needs 8 terms
where the conventional G needs 15. It loses on energy in the
long-delay, minimum-size region where sum precomputation is critical,
gains less as sparseness grows, and does not fit carry-skip,
variable-block or carry-select adders, which reuse an XOR propagate
and need the true carry before each block.

## the library's module

The seed instantiates the library's prefix module for the declared
`topology` (see the parallel_prefix card: `chialu.targets.rtl.families.prefix`
emits any graph; `--ling` selects the Ling pre- and post-processing on any topology); a rewrite pastes an edited graph's module in
its place.

## design choices

### sum_recovery

| member | what it selects |
| --- | --- |
| `late_select_mux` | the two conditional sums are computed and the Ling pseudo-carry selects between them. |
| `xor_correction` | the sum is recovered by an XOR correction on the pseudo-carry. |

### topology

| member | what it selects |
| --- | --- |
| `sklansky` | the minimum-depth prefix graph with doubling fanout. |
| `kogge_stone` | the minimum-depth graph at unit fanout and maximal wiring. |
| `han_carlson` | a Brent-Kung skeleton over a Kogge-Stone core. |
| `knowles_mixed` | the Knowles continuum, whose fanout vector names the point. |

## references

ling1966 -> H. Ling, "High Speed Binary Parallel Adder", IEEE Transactions on Electronic Computers, vol. EC-15, pp. 799-802, 1966.
ling1981 -> H. Ling, "High-Speed Binary Adder", IBM Journal of Research and Development, vol. 25, no. 2-3, pp. 156-166, 1981.
doran1988 -> R. W. Doran, "Variants of an Improved Carry Look-Ahead Adder", IEEE Transactions on Computers, vol. 37, no. 9, pp. 1110-1113, 1988.
bewick1994 -> G. W. Bewick, "Fast Multiplication: Algorithms and Implementation", PhD dissertation, Stanford University, CSL-TR-94-617, 1994
naffziger1996 -> S. Naffziger, "A Sub-Nanosecond 0.5 um 64 b Adder Design", IEEE International Solid-State Circuits Conference (ISSCC), pp. 362-363, 1996.
dimitrakopoulos2005 -> G. Dimitrakopoulos, D. Nikolos, "High-Speed Parallel-Prefix VLSI Ling Adders", IEEE Transactions on Computers, 2005.
zlatanovici2009 -> R. Zlatanovici, S. Kao, B. Nikolic, "Energy-Delay Optimization of 64-Bit Carry-Lookahead Adders With a 240 ps 90 nm CMOS Design Example", IEEE Journal of Solid-State Circuits, 2009.
zeydel2010 -> B. R. Zeydel, D. Baran, V. G. Oklobdzija, "Energy-Efficient Design Methodologies: High-Performance VLSI Adders", IEEE Journal of Solid-State Circuits, vol. 45, no. 6, pp. 1220-1233, 2010.
