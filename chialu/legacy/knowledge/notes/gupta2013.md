---
handle: gupta2013
citation: V. Gupta, D. Mohapatra, A. Raghunathan, K. Roy, "Low-Power Digital Signal Processing Using Approximate Adders", IEEE Transactions on Computer-Aided Design, vol. 32, no. 1, pp. 124-137, 2013
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU, VEC_DOT_ACC]
formats: [int8, int16, int20, fixed_point]
authority: landmark
pages_read: 124-137 / 14
---

## summary
The paper proposes five transistor-simplified mirror-adder cells and uses them in the LSBs of ripple/carry-save adders for error-resilient DSP systems. Reduced transistor count/load capacitance permits voltage scaling, with reported power/quality tradeoffs for image compression, video compression, DCT, FIR filtering, and an 8 × 8 multiplier. Mathematical models estimate mean error and switched-capacitance power as functions of the number of approximate LSBs. # p.124–p.136

## families
### lower_part_approximate  (role: proposes)
mechanism: Five approximate full-adder cells are derived by removing transistors from the 24-transistor conventional mirror adder while avoiding open/short circuits and limiting truth-table errors. Multi-bit RCAs and CSAs use these cells only in the LSBs and accurate mirror-adder cells in the MSBs. Approximation 5 replaces the approximate region with buffered Sum=B and Cout=A signals, eliminating internal carry propagation there. Reduced input/internal capacitance shortens multilevel-adder critical paths and permits a lower VDD. # p.125–p.128
choices:
  lower_width: application-set 1–10 [outside domain]   # p.128, p.130, p.133, p.135
  lower_cell: approx_mirror_ama   # p.125–p.128
  carry_to_upper: approximate_cell_carry [outside domain]   # p.127
new_choices:
  approximation_variant: {approximation_1, approximation_2, approximation_3, approximation_4, approximation_5} — five distinct transistor-removal/buffer simplifications of the mirror-adder cell   # p.126–p.128
  significance_weighted_allocation: Bool — assigns different approximate-LSB counts to output groups according to output significance   # p.132–p.135
slots:
  upper_adder: ripple_carry [full_adder_cell=static_cmos_mirror]   # p.125, p.128
parameters: conventional cell 24 transistors; image DCT/IDCT 7–9 approximate LSBs; video hardware 1–4 approximate LSBs; optimized DCT/FIR groups 2–10 approximate LSBs; at most three supply voltages; DCT 333.33 MHz; FIR 300 MHz   # p.126, p.128, p.130, p.132–p.135
results:
| metric | value | unit | technology / device | baseline | condition | page |
| cell area | 29.31 | μm2 | IBM 90-nm / 2013 | conventional MA, 40.66 μm2 | approximation 1 | p.127 |
| cell area | 25.5 | μm2 | IBM 90-nm / 2013 | conventional MA, 40.66 μm2 | approximation 2 | p.127 |
| cell area | 22.56 | μm2 | IBM 90-nm / 2013 | conventional MA, 40.66 μm2 | approximation 3 | p.127 |
| cell area | 23.91 | μm2 | IBM 90-nm / 2013 | conventional MA, 40.66 μm2 | approximation 4 | p.127 |
| buffer area | 6.77 | μm2 | IBM 90-nm / 2013 | none | single buffer used by approximation 5 | p.127 |
| PSNR | 29.30 | dB | IBM 90-nm / 2013 | accurate DCT, 31.16 dB | approximation 4, Q=[−6, 0], [l1,l2,l3]=[8,8,8] | p.134 |
| power savings | 62.9 | % | IBM 90-nm / 2013 | accurate DCT | approximation 4, Q=[−6, 0], [8,8,8] | p.134 |
| PSNR | 22.06 | dB | IBM 90-nm / 2013 | accurate DCT, 31.16 dB | truncation, Q=[−6, 0], [8,8,8] | p.134 |
| power savings | 65.9 | % | IBM 90-nm / 2013 | accurate DCT | truncation, Q=[−6, 0], [8,8,8] | p.134 |
| PSNR | 25.30 | dB | IBM 90-nm / 2013 | accurate DCT, 31.16 dB | approximation 5, Q=0.021, [10,10,10] | p.134 |
| power savings | 69.32 | % | IBM 90-nm / 2013 | accurate DCT | approximation 5, Q=0.021, [10,10,10] | p.134 |
| power savings | ≈42 | % | UNKNOWN / 2013 | accurate video adders | approximation 5, 4 approximate LSBs, Akiyo 50 frames | p.130 |
| ΔMPBR | 0.27 | % | UNKNOWN / 2013 | accurate FIR | approximation 5, Q=3.24, [10,10,10] | p.135 |
| ΔMSBR | 1.92 | % | UNKNOWN / 2013 | accurate FIR | approximation 5, Q=3.24, [10,10,10] | p.135 |
| power savings | 61.77 | % | UNKNOWN / 2013 | accurate FIR | approximation 5, Q=3.24, [10,10,10] | p.135 |
errors_and_checks: Truth-table Sum/Cout error counts are 2/1, 2/0, 3/1, 3/2, and 4/2 for approximations 1–5. For y approximate RCA bits, mean errors are 0, y/4, 1−2^−y, (1−2^(y−1))/4, and 1/2, respectively; truncation has mean error 1−2^y. No fault-detection mechanism is provided. # p.127–p.128, p.130–p.131, p.136
conditions: Approximate cells are restricted to LSBs because MSB errors severely reduce application quality. Image quality degrades appreciably beyond the ninth approximate LSB. The method targets application-specific error-resilient DSP rather than general-purpose processors, where arithmetic is reported as only 6% of energy. Approximation 4 suits negative Q constraints; approximations 1/5/3/2 suit progressively larger positive Q cases. The method applies to arithmetic circuits constructed from full adders. # p.124–p.125, p.128, p.134
evidence: §II, Tables I–V, Figs. 1–10; §IV-A–B and Appendix; §V, Tables VII–IX and Figs. 17–19.

### approximate_compressor_tree  (role: instantiates)
mechanism: An 8 × 8 multiplier forms accurate partial products and reduces them with an approximate carry-save tree containing an 8:2 compressor, followed by an approximate RCA. Both the compressor and RCA are built from the proposed approximate mirror-adder cells, with 5–9 LSBs made approximate. # p.132
choices:
  approximate_columns: 5–9 [outside domain]   # p.132
  compressor: approximate_mirror_adder_8_2 [outside domain]   # p.132
new_choices:
  approximate_cell_basis: mirror_adder_transistor_simplification — identifies the approximate full-adder implementation used inside the compressor   # p.132
slots:
  cpa: lower_part_approximate [outside slot domain]   # p.132
parameters: 8 × 8 multiplier; 8:2 carry-save compressor; 5–9 approximate LSBs; exhaustive Nanosim input simulation; mean error calculated with MATLAB   # p.132
results: none; Fig. 16 plots percentage power reduction against mean error without tabulated coordinates.
errors_and_checks: Mean error is evaluated, but exact plotted values are not printed. No error detection/correction is provided. # p.132
conditions: Approximation 4 outperforms the cited inaccurate-partial-product approach at larger mean errors, while the partial-product approach reaches saturation sooner than approximations 4 and 5. # p.132
evidence: §IV-C, Fig. 16.

## new_families
none

## space_gaps
* `lower_part_approximate.lower_width` excludes the reported 1–10-bit configurations because its domain permits only multiples of four. # p.128, p.130, p.133, p.135
* `lower_part_approximate.lower_cell` does not distinguish the five proposed mirror-adder transistor simplifications. # p.126–p.128
* `lower_part_approximate.carry_to_upper` lacks an approximate full-adder-generated boundary carry. # p.127
* `approximate_compressor_tree.compressor` lacks a full-adder-based approximate 8:2 compressor value. # p.132
* `approximate_compressor_tree.cpa` excludes `lower_part_approximate`, although the demonstrated multiplier uses an approximate lower-part RCA. # p.132

## open_questions
* Fig. 16 does not print the numerical power/error coordinates for the approximate multiplier.
* The video-compression and FIR result passages do not explicitly state a fabrication technology.
