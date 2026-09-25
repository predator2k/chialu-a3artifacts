---
handle: oklobdzija2005
citation: V. G. Oklobdzija, B. R. Zeydel, H. Q. Dao, S. Mathew, R. Krishnamurthy, "Comparison of High-Performance VLSI Adders in the Energy-Delay Space", IEEE Transactions on VLSI Systems, 2005.
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [int32, int64]
authority: incremental
pages_read: 754-758 / 5
---

## summary
The document presents an energy-delay estimation method based on logical effort, characterized gate energy, wiring, branching, and transistor sizing. The method compares 32- and 64-b Kogge–Stone, Han–Carlson, Quaternary-Tree, and KS4-IBM adders implemented in static/domino/compound-domino CMOS. The comparisons show that the preferred topology and circuit style depend on the target energy-delay region.

## families
### parallel_prefix  (role: compares)
mechanism: The Kogge–Stone carry network uses domino carry-merge blocks followed by static inverters. Compound-domino replaces each inverter with an AOI gate, which allows two domino carry-merge stages to be merged. The KS4-IBM variant reduces the number of stages at the cost of increased gate complexity and branching. # p.756-757
choices:
  topology: kogge_stone   # p.756-757
  node_style: {dynamic_domino, compound_domino [outside domain], static_cmos [outside domain]}   # p.756-757
new_choices:
  none
slots:
  none
parameters: 32-b and 64-b adders; 100-nm and 130-nm CMOS; path gain H from 2 to the maximum H where minimum input size occurs; 1 mm output wire in the 64-b comparison   # p.754-757
results:
| metric | value | unit | technology / device | baseline | condition | page |
|---|---:|---|---|---|---|---|
| delay improvement | 20% | % | 130-nm CMOS / 2005 | 64-b domino Kogge–Stone at the same 200 pJ energy budget | compound-domino Kogge–Stone | p.757 |
errors_and_checks: none
conditions: A single-delay comparison can misidentify the preferred topology because energy and delay trade against each other. # p.755; KS4-IBM achieves lower delay with less energy penalty than the other evaluated designs at high-performance targets. # p.757; KS4-IBM gate-complexity overhead is too large at lower-performance targets, where QT and HC consume less energy. # p.757; EDE assumes 15% gate switching activity for static adders and 50% for dynamic adders. # p.756
evidence: §II, §IV, §V.A-B; Table I; Figs. 1-4, p.754-757

### sparse_prefix_hybrid  (role: compares)
mechanism: The paper classifies Han–Carlson and Intel’s Quaternary-Tree adder as sparse designs. The 32-b compound-domino QT implementation has the same stage count as the compared Kogge–Stone implementation. The 64-b QT implementation has one additional stage, which reduces its benefit relative to Kogge–Stone. # p.757
choices:
  tree_topology: {han_carlson, quaternary_tree [outside domain]}   # p.756-757
new_choices:
  circuit_family: {static_cmos, domino_cmos, compound_domino_cmos} — selects the gate family used to implement the sparse carry network   # p.756-757
slots:
  sum_block: UNKNOWN   # p.756-757
parameters: 32-b and 64-b adders; 100-nm and 130-nm CMOS; 1 mm output wire in the 64-b comparison   # p.754-757
results: none with extractable numeric values
errors_and_checks: none
conditions: The 32-b EDE comparison reproduces the energy-delay tradeoff observed in optimized H-SPICE simulations and supports QT as an energy-reducing option without sacrificed performance. # p.757; the 32-b H-SPICE data were scaled from 130 nm to 100 nm using 50% energy and 30% delay scaling. # p.757; QT provides less benefit at 64 b because its implementation has one more stage than Kogge–Stone. # p.757; HC and QT consume less energy than KS4-IBM at lower-performance targets. # p.757
evidence: §V.A-B; Figs. 2-4, p.756-757

## new_families
none

## space_gaps
* `parallel_prefix.node_style` lacks the paper’s `compound_domino` and `static_cmos` implementation values. # p.756-757
* `sparse_prefix_hybrid.tree_topology` lacks the Intel `quaternary_tree` value. # p.756-757
* `sparse_prefix_hybrid` lacks a circuit-family choice for static/domino/compound-domino implementations. # p.756-757

## open_questions
* Table I values and most coordinates in Figs. 2-4 are not legible in the supplied document text, so only numbers stated explicitly in prose are recorded.
* The QT sparsity and sum-block implementation are not specified.
* The paper names `KS4-IBM` as a prefix-4 adder but does not define whether “prefix-4” maps exactly to the vocabulary’s `valency` choice.
