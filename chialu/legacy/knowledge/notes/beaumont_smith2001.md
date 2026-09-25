---
handle: beaumont_smith2001
citation: A. Beaumont-Smith, C.-C. Lim, "Parallel Prefix Adder Design", 15th IEEE Symposium on Computer Arithmetic (ARITH-15), pp. 218-225, 2001.
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [binary8, binary16, binary32, binary64]
authority: incremental
pages_read: 218-225 / 8
---

## summary
The paper introduces algorithm-generated parallel-prefix carry trees with high-valency cells and repeated carry chains, then maps their area-delay design space in 0.25μm CMOS. The paper also extends the construction to end-around-carry adders that distribute cyclic carry assimilation without a single high-fanout carry-out signal. # p.218, p.222

## families
### parallel_prefix  (role: extends)
mechanism: The synthesis algorithm constructs a stride-width carry-tree slice and copies it from least-significant to most-significant positions. Each row uses prefix cells with a selected maximum valency, and each row maximizes its carry-assimilation span. Repeated carry chains overlap and share subadders, which supplies more carry signals to the final-stage load. Black cells become grey cells where only group generate is required. # p.219-p.221
choices:
  valency: 2 / 3 / 4   # p.219-p.220
  topology: high_valency_generated [outside domain]   # p.220-p.221
new_choices:
  row_valencies: sequence of q_i values from {2, 3, 4} — selects the maximum prefix-cell input count independently for each row   # p.220
  carry_tree_stride: d — sets the spacing of repeated carry chains   # p.219-p.220
slots:
  none
parameters: widths 8/32/64 bit; q_i ∈ {2,3,4}; carry-tree stride d; pipeline stages/latency cycles/II: UNKNOWN   # p.220
results:
| metric | value | unit | technology / device | baseline | condition | page |
| design-space size | around 120 | generated carry trees | commercial 0.25μm CMOS / 2001 | none | nominal 8-/32-/64-bit studies | p.221 |
| area-delay and area-delay² candidate | 32,4,[4 2 4 2],[1 2 1 0] | carry-tree specification | commercial 0.25μm CMOS / 2001 | generated 32-bit trees | notation gives w,d,[q_i],[inverters per row] | p.221 |
| area-delay and area-delay² candidate | 64,4,[4 4 4 4],[2 2 1 0] | carry-tree specification | commercial 0.25μm CMOS / 2001 | generated 64-bit trees | notation gives w,d,[q_i],[inverters per row] | p.222 |
| minimum-delay specification in study | 64,1,[4 4 4] | carry-tree specification | commercial 0.25μm CMOS / 2001 | around 120 generated carry trees | three valency-4 rows with low fanout | p.222 |
errors_and_checks: The generator functionally verifies each constructed tree with associativity/idempotency/increasing-significance operator rules and checks each output's G range; no runtime fault model or checker is reported. # p.221
conditions: Higher valency reduces the number of prefix cells or interconnect length, but prefix-cell delay increases with fan-in. # p.219-p.220 The study models relative carry-tree delay rather than absolute adder delay and excludes bitwise propagate/generate and sum cells. # p.220-p.221 The simulations use typical process parameters at 105C, simultaneous operand arrival, RC wire delay, and a good ground-return assumption; time-of-flight delay is treated as negligible for distances up to 0.5mm. # p.220-p.221 The minimum-delay 64,1,[4 4 4] tree probably has too many wires for practical implementation. # p.222
evidence: §1.1-§1.3, §2-§2.2, Figs. 1-9, pp.219-224

### end_around_carry  (role: proposes)
mechanism: The end-around-carry construction extends group generate/kill expressions so a carry may assimilate cyclically across at most one adder width. Repeated shifted carry trees are aligned by making the stride a factor of the width, making q_1 a common factor of stride and width, enforcing the row-product rule, and placing cells modulo the width. This distributes the cyclic carry computation instead of reducing it to one carry-out that drives flags or result multiplexers. # p.220, p.222
choices:
  recirculation: cyclic_prefix_level   # p.220, p.222
  topology: han_carlson / kogge_stone / high_valency_generated [outside domain]   # p.224
new_choices:
  row_valencies: sequence of q_i values from {2, 3, 4} — selects the valency of each cyclic-prefix row   # p.220, p.224
  carry_tree_stride: d — controls repeated cyclic carry-chain spacing and alignment   # p.220
slots:
  none
parameters: 16-bit examples 16,4,[4 4 2], 16,2,[2 2 2 2 2], and 16,1,[2 2 2 2]; pipeline stages/latency cycles/II: UNKNOWN   # p.224
results: none
errors_and_checks: The generator verifies that each end-around-carry output covers the cyclic propagate/generate range from the output bit through the preceding bit; no runtime fault model or checker is reported. # p.221
conditions: The proposed use is the near path of a floating-point adder that produces result magnitude without rounding. # p.222 The construction is potentially faster than flagged-prefix and carry-select structures because it avoids a single carry-out reduction followed by a large flag/multiplexer fanout, but it requires more long wires. # p.222
evidence: §2.1, §3, Figs. 10-13, pp.220-224

## new_families
none

## space_gaps
* `parallel_prefix.topology` and `end_around_carry.topology` lack a value for algorithm-generated trees whose per-row valencies and repeated-chain stride define the structure rather than a named topology. # p.220-p.224
* `parallel_prefix.valency` cannot represent the paper's independently selected per-row sequence q_i. # p.220

## open_questions
* Exact area/delay coordinates for individual generated trees appear only graphically in Figs. 7-9, so the merge pass must not infer unprinted point values. # p.223-p.224
