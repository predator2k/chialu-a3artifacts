---
handle: zeydel2010
citation: B. R. Zeydel, D. Baran, V. G. Oklobdzija, "Energy-Efficient Design Methodologies: High-Performance VLSI Adders", IEEE Journal of Solid-State Circuits, vol. 45, no. 6, pp. 1220-1233, 2010.
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [int64]
authority: incremental
pages_read: 1220-1233 / 14
---

## summary
The paper develops energy-efficient design methods for 64-bit parallel-prefix adders implemented in static CMOS, CMOS domino, and CMOS compound domino logic. It proposes KS2-S2-(L), FZO-S2, and EZO-S2 adders that combine Ling pseudo-carry recurrence, minimum-depth prefix structures, merged first-stage operations, and conditional sums. Modeled comparisons cover 65 nm, 45 nm, 32 nm, and 22 nm CMOS technologies.

## families
### parallel_prefix  (role: compares)
mechanism: The paper compares Kogge-Stone and Han-Carlson carry structures using Weinberger carry recurrence and Ling pseudo-carry recurrence. Logic depth, prefix, fan-out, and wiring complexity define the topology space. Minimum-depth Kogge-Stone structures favor maximum performance, while structures with additional stages can reduce gate count and energy when delay is relaxed. Bitwise operations can be merged into the first recurrence stage when transistor-stack limits permit. (pp.1221, 1225-1227)
choices:
  topology: kogge_stone; han_carlson   # pp.1221, 1230-1231
  valency: 2; 4; 8 [outside domain]   # pp.1223, 1228-1229
  node_style: dynamic_domino   # pp.1222-1223, 1228
new_choices:
  logic_family: {static_cmos, cmos_domino, cmos_compound_domino} — selects the circuit family used for prefix stages   # pp.1222-1223
  first_stage_bitwise_merge: Bool — controls whether bitwise generate/propagate operations share the first recurrence stage   # pp.1226-1227
  output_load_buffering: Bool — controls addition of inverter stages for output-load driving   # p.1227
slots: none
parameters: 64-bit adders; prefix-2/prefix-4 gates; compound prefix-8 stage; output load 100*Min-Inv; input load swept from 20*Min-Inv to 100*Min-Inv   # pp.1228-1230
results:
| metric | value | unit | technology / device | baseline | condition | page |
| performance improvement | 5 | % | 65 nm CMOS / 2010 | existing designs | static CMOS adders | p.1232 |
| energy saving | 1.7 | energy saving | 65 nm CMOS / 2010 | existing designs | static CMOS adders | p.1232 |
errors_and_checks: Arithmetic accuracy/fault checking is not addressed. Energy-delay estimation differs from H-Spice by less than 6% for delay and less than 15% for energy.   # p.1230
conditions: Minimum-depth structures are most efficient at the highest performance, while additional stages can save energy when delay is relaxed.   # pp.1225-1226
evidence: §§II, IV.D-IV.E, VI-VII; Figs. 3-8 and 11-17 (pp.1221, 1224-1231)

### ling_prefix  (role: extends)
mechanism: Ling recurrence factors propagate from the carry expression and recursively computes pseudo-carry H. The pseudo-carry reduces first-stage fan-in and transistor-stack height, while the true carry is recovered during conditional sum computation. The recurrence supports arbitrary group sizes and levels and can use the same parallel-prefix structures as Weinberger recurrence. (pp.1221-1223)
choices:
  pseudo_carry_group: 2; 4   # pp.1227-1229
  topology: kogge_stone   # pp.1227-1229
  sum_recovery: late_select_mux   # pp.1222, 1228-1229
new_choices:
  bitwise_merge: Bool — controls integration of bitwise operations into the first pseudo-carry stage   # pp.1226-1228
slots: none
parameters: KS2-(L) uses six static stages or three compound-domino stages for 64-bit carry; FZO-S1/FZO-S2 use four stages; EZO-S1/EZO-S2 use three stages   # pp.1228-1229
results:
| metric | value | unit | technology / device | baseline | condition | page |
| performance improvement | 5 | % | 65 nm CMOS / 2010 | existing designs | Ling recurrence with merging and conditional sum in static adders | pp.1230, 1232 |
conditions: Ling is advantageous when carry and sum computation are separate. Ling is impractical for full-adder-based carry-skip, variable-block, and carry-select adders because it cannot reuse XOR propagate and must recover true carry before a block.   # p.1227
evidence: §III.B, §§IV.E-IV.F, §V (pp.1221-1229)

### sparse_prefix_hybrid  (role: proposes)
mechanism: KS2-S2-(L), FZO-S2, and EZO-S2 compute every other pseudo-carry with a minimum-depth Kogge-Stone Ling tree. A static 2-bit conditional-sum block selects each pair of sums from the pseudo-carry. Sparsity halves the carry-structure gate count and reduces wiring while preserving the respective four-stage or three-stage organization. (pp.1227-1229)
choices:
  log2_sparsity: 1   # pp.1227-1229
  tree_topology: kogge_stone   # pp.1227-1229
  valency: 2; 4   # pp.1227-1229
  sum_block_style: conditional_sum   # pp.1227-1229
new_choices:
  logic_family: {static_cmos, cmos_domino, cmos_compound_domino} — selects KS2-S2-(L), FZO-S2, or EZO-S2 realization style   # pp.1227-1229
slots: none
parameters: 64-bit; 2-bit conditional-sum blocks; KS2-S2-(L) has seven domino stages or four compound-domino stages; FZO-S2 has four domino stages; EZO-S2 has three compound-domino stages   # pp.1228-1229
results:
| metric | value | unit | technology / device | baseline | condition | page |
| speed improvement | 20 | % faster | 65 nm CMOS / 2010 | existing domino adders | FZO-S2/high-performance domino design | p.1232 |
| energy reduction | 4.5 | energy reduction | 65 nm CMOS / 2010 | existing domino adders | domino adders | p.1232 |
| energy reduction | 2.4 | energy reduction | 65 nm CMOS / 2010 | existing compound-domino adders | best-performance range | p.1232 |
| energy consumption | up to four times less | energy | UNKNOWN / 2010 | leading CMOS implementations, e.g. Kao [23] | EZO-S2 at highest achievable speed | p.1232 |
errors_and_checks: none
conditions: Conditional-sum depth should not exceed carry-path depth; static prefix-2 designs up to 64 bits should use at most 4-bit blocks, while dynamic prefix-4 designs should use 2-bit or 4-bit blocks.   # pp.1224-1225
evidence: §IV.C, §V, §VII; Figs. 4-6 and 8-17 (pp.1224-1232)

## new_families
none

## space_gaps
* `parallel_prefix.node_style` lacks `static_cmos` and `cmos_compound_domino`, which are primary implementation alternatives in the paper.   # pp.1222-1223
* `sparse_prefix_hybrid` lacks a circuit-family choice for static CMOS/domino/compound-domino realizations.   # pp.1227-1229
* `sparse_prefix_hybrid.sum_block` cannot name the document's 2-bit conditional-sum block because `conditional_sum` is absent from the slot domain.   # pp.1224-1225, 1228-1229
* `parallel_prefix.valency` stops at 4, while the paper defines a compound-domino stage containing prefix-4 dynamic and prefix-2 static gates as prefix-8.   # p.1228

## open_questions
* The prose does not state whether “1.7,” “4.5,” and “2.4 energy reduction” are multiplicative factors, so the merge pass must preserve the printed wording.   # p.1232
* Figs. 12-17 contain energy-delay curves, but the supplied text gives no absolute curve coordinates.   # pp.1230-1231
