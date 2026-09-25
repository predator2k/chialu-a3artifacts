---
handle: jaberipur_2009
citation: Jaberipur, Kaivani, "Improving the Speed of Parallel Decimal Multiplication", IEEE Transactions on Computers, 2009
actual_citation: same
status: ok
kind: paper
unit_classes: [other]
formats: [bcd]
authority: incremental
pages_read: 1539-1552 / 14
---

## summary
The paper proposes a parallel BCD multiplier with direct unsigned double-BCD partial-product generation, a six-level BCD carry-save reduction tree, and a 26-digit final BCD adder. The synthesized 16-by-16-digit implementation reports 3.71 ns latency and 445,725 μm² area in TSMC 0.13 μm standard CMOS.

## families
### parallel_decimal_multiplication  (role: proposes)
mechanism: Each multiplier digit selects two equally weighted components formed from X, 2X, 5X, 8X, and 9X. Dedicated logic directly generates 8X and 9X as unsigned double-BCD values, which removes negative partial products/sign digits/10s-complement carry-in bits. A BCD carry-save tree reduces 32 operands, and a 26-digit BCD adder converts the remaining double-BCD portion. # p.1541-p.1550
choices:
  pp_generation: precomputed_multiples_mux   # p.1541-p.1542
new_choices:
  partial_product_representation: unsigned_double_bcd — every selected multiple consists of two equally weighted nonnegative BCD components   # p.1542
  precomputed_multiple_set: {X, 2X, 5X, 8X, 9X} — the custom selectors form every multiplier-digit multiple from this set and zero   # p.1542-p.1543
slots:
  reduction_tree: csa_tree   # p.1544-p.1547
  final_adder: parallel_prefix [topology=kogge_stone]   # p.1547-p.1549
parameters: 16-by-16 BCD digits; 32 decimal partial-product operands; 26-digit final BCD addition; PPR structure also shown for 34-by-34 digits/68 operands   # p.1545-p.1549
results:
| metric | value | unit | technology / device | baseline | condition | page |
| latency | 3.71 | ns | TSMC 0.13 μm standard CMOS (2009) | [18] scaled to 0.13 μm: 4.30 ns | synthesized 16-by-16-digit multiplier | p.1550 |
| area | 445,725 | μm² | TSMC 0.13 μm standard CMOS (2009) | UNKNOWN | synthesized 16-by-16-digit multiplier | p.1550 |
| speed advantage | 16 | percent | TSMC 0.13 μm standard CMOS (2009) | [18] scaled to 0.13 μm | synthesized 16-by-16-digit multiplier | p.1550 |
| latency advantage | 14 | percent | static CMOS Logical Effort (2009) | [18] | 16-by-16-digit multiplier | p.1550 |
| latency advantage | 20 | percent | static CMOS Logical Effort (2009) | [20] | 16-by-16-digit multiplier | p.1550 |
| latency advantage | 13 | percent | static CMOS Logical Effort (2009) | [20] with PPR from [19] | 16-by-16-digit multiplier | p.1550 |
| area overhead | 15 | percent | static CMOS Logical Effort (2009) | [18] | 16-by-16-digit multiplier | p.1550 |
| area overhead | 36 | percent | static CMOS Logical Effort (2009) | [20] | 16-by-16-digit multiplier | p.1550 |
| area overhead | 33 | percent | static CMOS Logical Effort (2009) | [20] with PPR from [19] | 16-by-16-digit multiplier | p.1550 |
errors_and_checks: none
conditions: The design trades area for latency, with the additional area attributed mainly to the more complex PPG logic. The Logical Effort model excludes wiring delay/gate sizing and assumes equal input/output loads, so the comparative percentages are estimates. # p.1548, p.1550
evidence: Fig. 3, Fig. 4, Tables 6-8, §§3.1, 4.2, 5, 6

### decimal_multioperand_addition  (role: extends)
mechanism: The PPR tree uses BCD full adders as 3-to-2 reduction cells. Simplified first-level cells omit carry-in because every partial product is positive. Later unused decimal carries are collected with (9:4)/(6:3) binary-to-BCD counters placed off the critical path. A Wallace-like organization emits one low BCD product digit after each level, leaving six BCD digits resolved and 26 double-BCD digits after six levels. # p.1544-p.1547
choices:
  reduction_style: bcd_csa_per_level_correction   # p.1543-p.1547
  compressor_arity: 3_to_2   # p.1543-p.1546
  correction_placement: per_level   # p.1544-p.1546
new_choices:
  carry_collection: binary_to_bcd_counters_off_critical_path — unused decimal carries are grouped by (9:4)/(6:3) counters during reduction   # p.1545-p.1546
slots:
  reduction_tree: csa_tree   # p.1544-p.1547
  root_adder: parallel_prefix [topology=kogge_stone]   # p.1547-p.1549
parameters: six reduction levels for 32-to-2 reduction; 16 simplified and 16 regular BCD-FAs; 68-to-2 organization also described   # p.1545-p.1547
results:
| metric | value | unit | technology / device | baseline | condition | page |
| PPR latency | 32.35 | FO4 | static CMOS Logical Effort (2009) | [18]: 42.02 FO4; [20]: 40.93 FO4; [19]: 36.98 FO4 | 32-to-2 reduction for 16-by-16-digit multiplication | p.1549 |
| BCD-FA sum latency | 6.05 | FO4 | static CMOS Logical Effort (2009) | cell from [6]: 6.88 FO4 | modified regular BCD-FA | p.1546 |
| simplified BCD-FA latency | 5.89 | FO4 | static CMOS Logical Effort (2009) | unmodified simplified cell: 6.49 FO4 | first reduction level without carry-in | p.1546 |
errors_and_checks: none
conditions: Wallace-like early digit production applies to the BCD-FA tree because each cell emits an in-place BCD digit and a carry to the next decimal position. The technique does not apply to the in-place 4-2-2-1 reduction methods of [19]/[20]. # p.1544-p.1545
evidence: Figs. 7-9, Tables 4-5 and 7, §§4.1-4.2, 6.2

### bcd_direct_addition  (role: instantiates)
mechanism: The final converter speculatively adds 6 to digits of one operand in parallel, overlapping preprocessing with the end of PPR. A wordwide carry network then completes a 26-digit double-BCD-to-BCD addition. # p.1547-p.1549
choices:
  digit_code: bcd8421   # p.1547-p.1549
  correction_placement: presum_plus6   # p.1547
  carry_scheme: full_lookahead   # p.1547-p.1548
new_choices:
  prefix_network: 104_bit_kogge_stone — the binary carry network spans 26 BCD digits   # p.1548-p.1549
slots:
  digit_adder: parallel_prefix [topology=kogge_stone]   # p.1548-p.1549
parameters: 26 BCD digits/104 carry-network bits   # p.1548-p.1549
results:
| metric | value | unit | technology / device | baseline | condition | page |
| converter latency | 16.00 | FO4 | static CMOS Logical Effort (2009) | [18] 32-digit BCD-CS converter: 12.50 FO4; [20] 32-digit double-BCD converter: 18.02 FO4 | proposed 26-digit double-BCD-to-BCD converter | p.1549 |
errors_and_checks: none
conditions: The 26-digit width follows from resolving six low product digits during PPR. The Kogge-Stone network is selected because the combined binary/decimal operand-setup logic that favored a quaternary tree in [20] is unnecessary here. # p.1547-p.1548
evidence: Fig. 10, §§5.1-5.2, 6.3

### parallel_prefix  (role: instantiates)
mechanism: A 104-bit Kogge-Stone carry network supplies wordwide carry generation for the final 26-digit BCD addition after speculative per-digit +6 preprocessing. # p.1547-p.1549
choices:
  topology: kogge_stone   # p.1548-p.1549
new_choices:
  none
slots:
  none
parameters: 104 bits; 26 BCD digits   # p.1548-p.1549
results:
| metric | value | unit | technology / device | baseline | condition | page |
| final-converter latency | 16.00 | FO4 | static CMOS Logical Effort (2009) | [20] 32-digit quaternary-tree converter: 18.02 FO4 | complete proposed converter, including BCD logic | p.1549 |
errors_and_checks: none
conditions: The reported 16.00 FO4 measures the complete converter rather than the prefix network alone. # p.1549
evidence: §§5.2, 6.3.3

## new_families
none

## space_gaps
* `parallel_decimal_multiplication.pp_generation` does not distinguish direct generation of an unsigned double-BCD basis `{X, 2X, 5X, 8X, 9X}` from generic precomputed-multiple selection. # p.1541-p.1543
* `decimal_multioperand_addition` lacks a choice for off-critical-path binary-to-BCD collection of unused decimal carries. # p.1544-p.1546

## open_questions
* The paper reports the full 34-by-34-digit PPR organization but does not report synthesis area/latency for a complete 34-by-34-digit multiplier.
* The synthesis comparison with [18] depends on technology scaling and unknown library/optimization differences, which the paper says may change the reported comparison.
