# parallel_prefix

Carry-propagate addition as a prefix computation: per-bit
generate/propagate pairs are combined through an associative operator
in a log-depth network, and the sum is one XOR behind the carries. The
topology choice fixes the depth / wiring / fanout trade: Sklansky is
minimum depth with doubling fanout, Kogge-Stone is minimum depth and
unit fanout at maximal wire cost, Brent-Kung spends +log depth for a
regular constant-track layout, Han-Carlson and Ladner-Fischer sit
between, and the Knowles family parameterizes the whole continuum.

The family wins whenever delay matters at width >= 16 and wiring is
affordable; below ~8 bits ripple or Manchester chains beat it on area,
and at extreme wire cost sparse hybrids (one prefix node per k bits
plus small sum blocks) recover most of the delay at a fraction of the
tracks. Valency (radix of the prefix operator) trades stage count
against stage load; fanout caps insert buffers the topology pretends
not to need.

## the library's prefix graphs

The family library builds any prefix graph and emits it as an unrolled
adder module (`chialu/targets/rtl/families/prefix.py`); the seed
instantiates the module of the declared `topology` (the (l, f) point of
`log2_sparsity` and `fanout_cap` under `harris`), so a declaration is
realized by construction. The command line serves a rewrite:

    python3 -m chialu.targets.rtl.families.prefix --width 32 --graph harris:l1f1 --report
    python3 -m chialu.targets.rtl.families.prefix --width 32 --graph kogge_stone --edit "remove 20 4; add 20 0" --sv prefix32.sv
    python3 -m chialu.targets.rtl.families.prefix --width 32 --arrival 0,0,1,2,3,4,5,5,5,4,3,2,1,0,0,0,... --target 6 --sv final_adder.sv

* `--graph` names a topology (kogge_stone, sklansky, brent_kung,
  ladner_fischer[:l], han_carlson, knowles_mixed, ripple), a Harris
  point `harris:l<l>f<f>` (l extra levels, fanout 2^f + 1, the wire
  tracks 2^(L-1-l-f) following), a Knowles fanout vector
  `knowles:k_L,...,k_1`, or a Roy et al. index sequence `seq:...`.
* `--edit "add <hi> <lo>; remove <hi> <lo>"` applies PrefixRL's node
  moves with legalization (a node's upper parent is the nearest node of
  its row, the missing lower parent is added; a removed node's children
  are re-legalized); `--report` prints levels, size, fanout, wire tracks,
  the grid and the sequence, which is the graph's cost before synthesis.
* `--arrival` builds the graph for per-bit arrival times (the
  multiplier's final adder): the ready bits combine while the late ones
  arrive, then the size-decreasing pass shares parents within the target
  depth (Zimmermann's depth- and size-decreasing transforms, greedy).
* `--ling` feeds (g_i, t_{i-1}) into the tree and recovers c = t & H
  (ling_prefix); `--flagged` adds s1 = s + 1 from the tree's group
  propagates (compound_flagged_prefix, valid with cin = 0).

The emitted module is pasted into the program in place of the seed's
instance; the review checks the structure, synthesis the delay and area.

## references

kogge_stone1973 -> P. M. Kogge, H. S. Stone, "A Parallel Algorithm for the Efficient Solution of a General Class of Recurrence Equations", IEEE Trans. Computers, 1973
sklansky1960 -> J. Sklansky, "Conditional-Sum Addition Logic", IRE Trans. Electronic Computers, 1960
brent_kung1982 -> R. P. Brent, H. T. Kung, "A Regular Layout for Parallel Adders", IEEE Trans. Computers, 1982
han_carlson1987 -> T. Han, D. A. Carlson, "Fast Area-Efficient VLSI Adders", ARITH-8, 1987
knowles2001 -> S. Knowles, "A Family of Adders", ARITH-15, 2001
harris2003 -> D. Harris, "A Taxonomy of Parallel Prefix Networks", Asilomar, 2003 (the (l, f, t) cube)
roy2013 -> S. Roy, M. Choudhury, R. Puri, D. Z. Pan, "Towards Optimal Performance-Area Trade-off in Adders by Synthesis of Parallel Prefix Structures", DAC, 2013 (the index-sequence notation, bottom-up enumeration under level/fanout constraints)
roy2021 -> R. Roy et al., "PrefixRL: Optimization of Parallel Prefix Circuits using Deep Reinforcement Learning", DAC, 2021 (arXiv 2205.07000; the node grid, add/remove moves with legalization)
lai2024 -> Y. Lai, J. Liu, D. Z. Pan, P. Luo, "Scalable and Effective Arithmetic Tree Generation for Adder and Multiplier Designs", NeurIPS, 2024 (arXiv 2405.06758; tree generation as a game, Pareto delay/area)
zuo2025 -> D. Zuo, J. Zhu, Y. Luo, Y. Ma, "PrefixAgent: An LLM-Powered Design Framework for Efficient Prefix Adder Optimization", 2025 (arXiv 2507.06127; a backbone from the taxonomy, then structural refinement)
