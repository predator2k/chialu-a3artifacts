---
handle: mathew2003
citation: S. Mathew, M. Anders, R. K. Krishnamurthy, S. Borkar, "A 4-GHz 130-nm Address Generation Unit with 32-bit Sparse-Tree Adder Core", IEEE Journal of Solid-State Circuits, 2003.
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [int32]
authority: incremental
pages_read: 689-695 / 7
---

## summary
The paper proposes a 32-bit sparse-tree adder core for a 4-GHz address generation unit in 1.2-V 130-nm CMOS. The adder generates every fourth carry through a pruned dynamic tree and generates intervening conditional sums through static ripple sidepaths, which reduces delay/energy relative to a Kogge–Stone adder. A dual-\(V_T\) semidynamic implementation reduces average energy and active leakage.

## families
### sparse_prefix_hybrid  (role: proposes)
mechanism: The adder generates every fourth carry with an irregular radix-2 sparse carry-merge tree. Each 4-bit static conditional-sum generator computes sums for input carries 0 and 1 with ripple carry-merge logic, and a transmission-gate multiplexer selects the result using the corresponding 1-in-4 tree carry. The critical path contains a dynamic PG stage and five alternating static/dynamic carry-merge stages; the noncritical conditional-sum path is reduced from five stages to four and implemented mainly in static CMOS. A set-domino latch suppresses precharge activity at the sum-generator input. # pp.690-693
choices:
  log2_sparsity: 2   # p.690
  valency: 2   # p.690
  sum_block_style: conditional_sum   # pp.691-692
new_choices:
  tree_shape: irregular_sparse — two carry-merge gates accept increased fanout while the other 121 generate/propagate gates retain fanouts of 1 and 2   # p.691
  logic_partition: dynamic_critical_static_noncritical — critical sparse-tree gates use single-rail dynamic logic and conditional-sum generators use static CMOS   # p.692
  threshold_voltage_partition: low-V_T_critical_high-V_T_noncritical — remaining sidepath slack permits high-\(V_T\) devices in the noncritical sum generators   # p.694
slots:
  sum_block: ripple_carry   # p.691
parameters: 32-bit operands; every fourth carry; 4-bit conditional-sum blocks; six critical-path stages; five noncritical-path stages before optimization and four after optimization; 152-ps adder target; 6.6-GHz adder core target   # pp.690-692
results:
| metric | value | unit | technology / device | baseline | condition | page |
| adder-core delay | 152 | ps | 1.2-V 130-nm technology, 2003 | none | AGU second phase | p.690 |
| AGU operating frequency | 4 | GHz | 1.2-V 130-nm CMOS, 2003 | none | single-cycle address generation | p.694 |
| delay reduction | 20 | % | 1.2-V 130-nm technology, 2003 | Kogge–Stone adder | energy-delay comparison | p.693 |
| generate/propagate fanout reduction | 33%–50% | % | 1.2-V 130-nm technology, 2003 | Kogge–Stone adder | sparse carry-merge tree | p.693 |
| maximum interconnect span | 12 versus 16 | bitslices | 1.2-V 130-nm technology, 2003 | Kogge–Stone adder | critical inter-stage wiring | p.690 |
| wiring-complexity reduction | 80 | % | 1.2-V 130-nm technology, 2003 | Kogge–Stone adder | carry-merge network | pp.690,693 |
| worst-case energy reduction | 56 | % | 1.2-V 130-nm technology, 2003 | Kogge–Stone adder | both adders at the 152-ps target | p.693 |
| Kogge–Stone average energy | 41 | pJ | 1.2-V 130-nm technology, 2003 | none | single-rail dynamic design with activity factor 0.5 | p.693 |
| average energy reduction | 71 | % | 1.2-V 130-nm technology, 2003 | dynamic Kogge–Stone implementation | adder input data activity of 10% | p.694 |
| leakage energy reduction | 56 | % | 1.2-V 130-nm CMOS, 2003 | initial all-low-\(V_T\) design | high-\(V_T\) allocation without transistor resizing | p.694 |
| active leakage energy component | 1 | % | 1.2-V 130-nm CMOS, 2003 | none | dual-\(V_T\) sparse-tree design | p.694 |
| projected delay improvement | 33 | % | 100-nm technology projection, 2003 | Kogge–Stone adder | scaling projection | p.694 |
| projected energy reduction | 50 | % | 100-nm technology projection, 2003 | Kogge–Stone adder | scaling projection | p.694 |
| projected leakage energy component | 4 | % | 100-nm technology projection, 2003 | none | device leakage assumed to increase by 3–5× | p.694 |
errors_and_checks: none
conditions: The sparse tree retains the Kogge–Stone logic depth while reducing fanout and wiring, and the noncritical ripple sidepath must complete before the final carry-controlled multiplexer selection. # pp.690-692 The bulk-CMOS static-stage stack height is limited to 2P because of body-effect stack penalty. # p.691 The 71% average-energy result assumes 10% adder input data activity, described as typical for datapath circuits. # pp.693-694 High-\(V_T\) allocation consumes the remaining sidepath slack until the main-path and sidepath delays are balanced. # p.694
evidence: Sections II–VI; Figs. 2–16; Tables I–II; pp.689-694

## new_families
none

## space_gaps
* `sparse_prefix_hybrid.tree_topology` lacks an `irregular_sparse` value for the explicitly irregular tree used by the design. # p.691
* `sparse_prefix_hybrid` lacks choices for critical/noncritical logic-style partitioning and dual-\(V_T\) assignment. # pp.692-694
* `sparse_prefix_hybrid.sum_block` permits `ripple_carry`, but the document specifically uses a dual-rail conditional-sum generator whose conditional carries ripple within each 4-bit block. # pp.691-692

## open_questions
* The supplied rendering does not expose the numeric cells of Tables I and II, so the exact absolute sparse-tree energy/leakage values and detailed 100-nm projections remain UNKNOWN.
* Section IV reports a 25% maximum interconnect-length reduction from 16 to 12 bitslices, while Section VI describes the maximum-span reduction as 30%; the merge pass must preserve this discrepancy. # pp.690,693
