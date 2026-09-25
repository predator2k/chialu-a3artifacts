---
handle: oklobdzija1995
citation: V. G. Oklobdzija, D. Villeger, "Improving Multiplier Design by Using Improved Column Compression Tree and Optimized Final Adder in CMOS Technology", IEEE Transactions on Very Large Scale Integration (VLSI) Systems, vol. 3, 1995
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [int12, int24, int53]
authority: landmark
pages_read: 292-301 / 10
---

## summary
The paper proposes a parallel multiplier whose partial-product summation tree uses tiled short carry-propagate adders and whose final adder is optimized for nonuniform input arrival times (p.292). A 24 x 24-b tree built from 4-b adders has a critical path of 10 equivalent XOR gate delays, compared with 14, 12, and 11 for 3 : 2, 4 : 2, and 9 : 2 reduction (p.298). The reported delays are simulated rather than measured and are intended primarily for relative comparison (p.293).

## families
### carry_select  (role: extends)
mechanism: The final CPA is divided according to its input-arrival profile. Region 1 follows the positive arrival-time slope and normally uses ripple carry or a variable block adder. Region 2 surrounds the maximum-delay input and uses carry-select addition with a fast carry-lookahead block. Region 3 follows the negative slope and uses carry-select addition whose speculative blocks may use a simpler CLA/VBA combination. Integer positions S1 and S2 delimit the regions (p.299-300).
choices:
new_choices:
  arrival_profile_regioning: three_regions — partitions the CPA into positive-slope, maximum-delay, and negative-slope regions # p.299
  region_boundary_method: iterative_integer_search — selects the integer bit positions S1 and S2 from the arrival profile # p.300
  region_specific_block_style: ripple_or_vba__csla_cla__csla_cla_vba — assigns different adder structures to the three regions # p.299-300
slots:
  block_adder: carry_lookahead # p.299
parameters: three regions; boundary positions S1 and S2; exact block widths UNKNOWN; a 12 x 12-b 2's-complement Booth-encoded example is shown # p.299-300
results:
| metric | value | unit | technology / device | baseline | condition | page |
| final multiplier delay at labeled worst bit | 17.3 | nS | LSI Logic 100K 1 µm CMOS ASIC | UNKNOWN | 12 x 12-b 2's-complement multiplier with Booth encoding; PPST and final-adder profile in Fig. 17(b) | p.300 |
errors_and_checks: none
conditions: Region 1 can use ripple carry when its propagation meets the positive arrival-time slope; otherwise the variable block adder is suggested (p.299). Region 2 favors carry select because its addition delay directly extends the multiplier critical path, while carry select uses less hardware than conditional sum (p.299). Region 3 permits simpler speculative adders because its most-significant inputs arrive before the selecting carry (p.299). The paper concludes that matching the CPA to the arrival profile matters more than applying the fastest uniform addition scheme (p.300).
evidence: §III.A, Figs. 15-17, pp.299-300

## new_families
### tiled_short_cpa_reduction_tree  (domain: mul: integer multipliers, closest: carry_save_array, why_not: carry_save_array describes a regular 2-D CSA array, while this mechanism tiles short carry-propagate adders into a multilevel partial-product reduction tree)
mechanism: Each reduction level uses staggered K-b carry-propagate adders. Horizontal carry propagation replaces part of the vertical counter/compressor path because the carry output can be faster than the sum. The staggered placement groups carry outputs into rows that later adders absorb through available carry inputs. A 24 x 24-b implementation uses four levels of 4-b adders followed by one row of 3 : 2 counters, producing two final rows in 10 equivalent XOR gate delays (p.296-298).
choices: adder_width: Int[1..operand_width]; carry_assimilation: {extra_counter_row, staggered_tiling, terminal_compressor}; terminal_reduction: {3_2_counter, compressor_4_2, compressor_9_2}; carry_sum_delay_relation: {carry_faster, equal, carry_slower}
results:
| metric | value | unit | technology / device | baseline | condition | page |
| compression ratio per equivalent XOR gate | 1.0 | ratio | analytical, technology UNKNOWN | 3 : 2 counter: 0.75; improved 4 : 2 compressor: 0.66 | ideal K-b CPA with carry propagation no slower than sum | p.296 |
| PPST critical-path delay | 10 | equivalent XOR gate delays | LSI Logic 100K 1 µm CMOS ASIC | 3 : 2-counter tree: 14; 4 : 2-compressor tree: 12; 9 : 2-compressor tree: 11 | 24 x 24-b multiplier; four 4-b-adder stages plus one 3 : 2-counter row; assumes carry-out as fast as sum | p.298 |
| PPST critical-path delay | 11 | equivalent XOR gate delays | analytical, technology UNKNOWN | 3 : 2-counter tree: 14 | 24 x 24-b tree using 4-b adders followed by 4 : 2 compressors | p.297 |
| PPST critical-path delay | 10 | equivalent XOR gate delays | analytical, technology UNKNOWN | 3 : 2-counter tree: 14 | 24 x 24-b tree using 4-b adders followed by 9 : 2 compressors | p.297 |
| PPST critical-path delay | 12 | equivalent XOR gate delays | LSI Logic 100K 1 µm CMOS ASIC | UNKNOWN | 53-b multiplier using the proposed PPST design method | p.300 |
errors_and_checks: none
conditions: The 10-delay result requires a 4-b adder whose worst-case carry-out delay equals its sum delay at two equivalent XOR gate delays (p.298). The LSI Logic implementation did not satisfy that assumption because its carry signal was twice as slow as its sum, although its simulated speed remained comparable to the 4 : 2 and 9 : 2 alternatives (p.299). The best adder width depends on multiplier size, Tc/Ts, and technology; longer adders reduce excess carries, while shorter adders are easier to implement (p.297). The results are simulations with modeled cell loads and average wire delay rather than measured silicon delays (p.293).
evidence: §II.D, Table II, Figs. 10-14, pp.296-298; §IV and Table III, p.300

## space_gaps
* The vocabulary names `csa_reduction_tree` and `compressor_4_2_tree` as slot fillers but does not declare their families; the paper compares 3 : 2, 4 : 2, 9 : 2, and short-CPA reduction trees directly (p.293-298).
* The adder vocabulary lacks `variable_block_adder`, which the paper uses for arrival-profile-matched regions of the final CPA (p.299-300).
* `carry_select` lacks choices for nonuniform input-arrival profiles, heterogeneous regional block adders, and profile-derived boundary positions S1/S2 (p.299-300).

## open_questions
* Table III is not legible enough in the supplied text to recover every 24-b and 53-b compressor-tree delay.
* The Booth radix used by the 12 x 12-b examples is not stated.
* The paper does not print the selected S1/S2 boundaries or regional widths for the 24 x 24-b and 53-b designs.
