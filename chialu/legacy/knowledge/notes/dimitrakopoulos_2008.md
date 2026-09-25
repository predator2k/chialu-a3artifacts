---
handle: dimitrakopoulos_2008
citation: G. Dimitrakopoulos et al., "Low-Power Leading-Zero Counting and Anticipation Logic for High-Speed Floating Point Units", IEEE Transactions on VLSI Systems, vol. 16, no. 7, 2008
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU, other]
formats: [binary]
authority: incremental
pages_read: 837-850 / 14 pages
---

## summary
The paper derives leading-zero-count bits with carry-lookahead relations and presents two modular LZC organizations for static/dynamic CMOS. The paper also integrates the LZC with leading-zero anticipation and proposes a one-bit anticipation-error correction method.

## families
### lzd_cell_tree  (role: extends)
mechanism: A binary OR tree forms progressively reduced input strings and the all-zero flag. Independent single-output carry-lookahead trees apply the Z operator to those strings to compute each weighted count bit. The straightforward organization limits gate fanout to 2, while the shared-carry-propagate organization reuses intermediate OR-tree signals and reduces gate count. Dynamic implementations duplicate only the input/OR-tree signals needed in both polarities, while the count trees remain single rail. # pp.839-842
choices:
  block_primitive: carry_merge [outside domain]   # p.840
  formulation: carry_lookahead_flags   # pp.839-840
new_choices:
  organization: {independent_count_trees, shared_carry_propagate} — selects shorter critical paths or fewer gates   # pp.841-842
  circuit_style: {static_cmos, dynamic_cmos} — selects the implementation logic   # pp.841-842
  dynamic_rail_style: {full_dual_rail, hybrid_single_dual_rail} — selects full signal duplication or duplication limited to polarity-critical nodes   # p.842
slots: none
parameters: Arbitrary wordlength; an n-bit unit uses log2(n) count bits and an all-zero flag; reported implementations use 64-bit inputs. # pp.838-840, 845-846
results:
| metric | value | unit | technology / device | baseline | condition | page |
| minimum delay | 6.6 | FO4 | UMC 130-nm CMOS / 2008 | none | 64-bit, static CMOS, straightforward organization | p.846 |
| minimum-delay reduction | 4% | delay | UMC 130-nm CMOS / 2008 | Oklobdzija [16] | 64-bit, static CMOS | p.845 |
| energy reduction | 10% to 49% | energy/operation | UMC 130-nm CMOS / 2008 | prior LZC architectures | equal-delay static CMOS comparisons | p.845 |
| minimum delay | around 11 | FO4 | UMC 130-nm CMOS / 2008 | none | encoder-based LZC and Bruguera-Lang [19], static CMOS | p.845 |
| significant-bit delay | 8.5 | FO4 | UMC 130-nm CMOS / 2008 | proposed LZC | Bruguera-Lang [19], 22% worse | p.845 |
| energy | less than 2 | pJ/operation | UMC 130-nm CMOS / 2008 | Bruguera-Lang [19] | proposed LZC sized to 8.5 FO4 | p.845 |
| speed improvement | 12% | delay | UMC 130-nm CMOS / 2008 | Lee-Nowka [10] | 64-bit dynamic single-rail implementation | p.846 |
| speed improvement | 40% | delay | UMC 130-nm CMOS / 2008 | encoder-based LZC | 64-bit dynamic single-rail implementation | p.846 |
| energy reduction | 55% | energy/operation | UMC 130-nm CMOS / 2008 | Lee-Nowka [10] | dynamic single-rail implementation | p.846 |
| energy reduction | exceeds 80% | energy/operation | UMC 130-nm CMOS / 2008 | encoder-based LZC | dynamic single-rail implementation | p.846 |
| energy reduction | more than 45% | energy/operation | UMC 130-nm CMOS / 2008 | proposed full-dual-rail LZC | proposed hybrid single/dual-rail implementation | p.846 |
errors_and_checks: The all-zero flag is computed by the binary OR tree. Count bits are treated as don’t-care values for an all-zero input. # pp.839-840
conditions: The straightforward organization is faster because fanout is limited to 2. The shared-carry-propagate organization is most energy-efficient above 8.5 FO4 in static CMOS and above 5 FO4 in dynamic CMOS. Dynamic gates require dual-polarity signals at polarity-critical inputs to preserve monotonic evaluation. # pp.841-842, 845-846
evidence: Sections III-IV and VI-A; Figs. 2-8, pp.839-846

## new_families
### leading_zero_anticipation  (domain: fp, closest: lzd_cell_tree, why_not: lzd_cell_tree encodes a supplied word but does not predict the normalization count from adder operands or correct prediction errors)
mechanism: Combined-indicator or split-indicator logic predicts a pseudo-result whose leading-zero/one count differs from the true add/subtract result by at most one. The proposed integration sends indicators directly into carry-lookahead LZC units. The proposed correction computes the true result’s count LSB with one carry tree, compares that bit with the predicted count LSB, and controls a final shifter stage capable of shifting by zero, one, or two positions. # pp.843-845
choices: indicator_structure: {combined, split}; split_selection: {true_sign, maximum_count}; error_handling: {shifter_msb_check, adder_one_hot_check, input_pattern_detect, true_count_lsb_compare}
results:
| metric | value | unit | technology / device | baseline | condition | page |
| energy reduction | more than 40% | energy/operation | UMC 130-nm CMOS / 2008 | prediction circuit using Oklobdzija LZC [16] | proposed LZC, small-delay static targets | p.846 |
| LZC delay contribution | 2/3 | total delay | UMC 130-nm CMOS / 2008 | complete prediction circuit | combined-indicator LZA | p.846 |
| LZC energy contribution | more than 60% | total energy/operation | UMC 130-nm CMOS / 2008 | complete prediction circuit | combined-indicator LZA | p.846 |
| LZA energy contribution | roughly 32% | total energy/operation | UMC 130-nm CMOS / 2008 | complete prediction circuit | optimized to 10 FO4 | p.846 |
| LZC energy reduction | 39% | energy/operation | UMC 130-nm CMOS / 2008 | Oklobdzija LZC [16] | prediction circuit optimized to 10 FO4 | p.846 |
| LZA energy reduction | 23% | energy/operation | UMC 130-nm CMOS / 2008 | LZA driving Oklobdzija LZC [16] | reduced driven capacitance at 10 FO4 | p.846 |
| speed improvement | 3% | delay | UMC 130-nm CMOS / 2008 | combined-indicator LZA | split LZA, static CMOS | p.847 |
| energy increase | 18% | energy/operation | UMC 130-nm CMOS / 2008 | combined-indicator LZA | split LZA, static CMOS average | p.847 |
| energy reduction | over 55% | energy/operation | UMC 130-nm CMOS / 2008 | Lee-Nowka [10] split LZA | combined-indicator dynamic LZA with proposed LZC, small delays | p.848 |
| standalone shifter minimum delay | 9.5 | FO4 | UMC 130-nm CMOS / 2008 | none | normalization shifter | p.848 |
| standalone shifter energy | roughly 32 | pJ | UMC 130-nm CMOS / 2008 | none | at 9.5 FO4 | p.848 |
| LZE I delay overhead | over 18% | delay | UMC 130-nm CMOS / 2008 | standalone shifter | output-MSB error detection | p.848 |
| LZE I energy | 27 | pJ | UMC 130-nm CMOS / 2008 | standalone shifter | unequal-delay comparison; standalone shifter uses 18 pJ at the same delay | p.848 |
| minimum delay | 9.9 | FO4 | UMC 130-nm CMOS / 2008 | standalone shifter | proposed method and LZE II | pp.848-849 |
| delay overhead | 4% | delay | UMC 130-nm CMOS / 2008 | standalone shifter | proposed method and LZE II | p.849 |
| energy overhead | around 20% | energy/operation | UMC 130-nm CMOS / 2008 | standalone shifter | proposed method and LZE II | p.849 |
evidence: Section V, Section VI-B-C, Figs. 7 and 9-11, pp.843-849

## space_gaps
* `lzd_cell_tree.block_primitive` lacks the proposed `carry_merge` cell value. # p.840
* `lzd_cell_tree` lacks organization/circuit-style/dynamic-rail choices that distinguish the reported energy-delay points. # pp.841-842
* The vocabulary lacks a leading-zero-anticipation family with indicator organization, sign/count selection, and one-bit error handling choices. # pp.843-845

## open_questions
* The 64-bit LZC experiments do not identify a corresponding IEEE floating-point format or significand width. # pp.845-849
