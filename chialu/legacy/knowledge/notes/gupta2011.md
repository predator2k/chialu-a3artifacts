---
handle: gupta2011
citation: V. Gupta, D. Mohapatra, S. P. Park, A. Raghunathan, K. Roy, "IMPACT: IMPrecise Adders for Low-Power Approximate Computing", IEEE/ACM International Symposium on Low Power Electronics and Design (ISLPED), pp. 409-414, 2011
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU, VEC_DOT_ACC]
formats: [int8, int16, int20]
authority: incremental
pages_read: 409-414 / 6
---

## summary
The paper simplifies a 24-transistor mirror full-adder into three approximate cells and places those cells in the least-significant positions of multi-bit adders. IBM 90nm layouts and JPEG/MPEG implementations show area/power reductions with application-level quality loss. The same cells also form approximate 4:2/8:2 carry-save compressors.

## families
### lower_part_approximate  (role: proposes)
mechanism: Accurate full-adders implement the most-significant bits, while transistor-reduced mirror-adder cells implement selected least-significant bits. Approximation 1 removes eight transistors and uses buffered Sum = Cout. Approximation 2 uses Cout = A with simplified Sum logic. Approximation 3 uses Sum = B and Cout = A, which eliminates carry propagation inside the approximate portion. The reduced transistor count and node capacitance reduce area/delay and permit lower VDD without timing errors. # pp.410-412
choices:
  lower_width: 7, 8, 9 [outside domain] for JPEG; 1, 2, 3, 4 [outside domain] for MPEG SAD   # pp.412-413
  lower_cell: approx_mirror_ama   # pp.410-411
  carry_to_upper: approximate_FA_Cout [outside domain]   # p.410
new_choices:
  approximation_variant: {approximation_1, approximation_2, approximation_3} — selects the mirror-adder transistor simplification and output equations   # pp.410-411
slots:
  upper_adder: ripple_carry   # pp.410,412
parameters: Conventional cell: 24 transistors; approximation 1: 16 transistors. JPEG arithmetic: 20-bit two’s-complement, with 7/8/9 approximate LSBs. MPEG SAD: 8-bit absolute difference plus 16-bit accumulator, with 1/2/3/4 approximate LSBs. Accurate DCT/IDCT VDD: 1.28 V/1.13 V. Truncation DCT/IDCT VDD for 7/8/9 LSBs: 1.13 V/1.03 V, 1.10 V/1.03 V, 1.1 V/1 V. Approximation 1: 1.18 V/1.05 V, 1.1 V/1.03 V, 1.1 V/1.03 V. Approximation 2: 1.15 V/1.1 V, 1.13 V/1.1 V, 1.1 V/1.1 V. Approximation 3: 1.14 V/1.02 V, 1.11 V/1.01 V, 1.1 V/1 V. # pp.410,412-413
results:
| metric | value | unit | technology / device | baseline | condition | page |
| area | 40.66 | µm² | IBM 90nm; 2011 | none | conventional MA | p.411 |
| area | 22.56 | µm² | IBM 90nm; 2011 | conventional MA | approximation 1 | p.411 |
| area | 23.91 | µm² | IBM 90nm; 2011 | conventional MA | approximation 2 | p.411 |
| area | 13.54 | µm² | IBM 90nm; 2011 | conventional MA | approximation 3 | p.411 |
| PSNR | 31.16 | dB | IBM 90nm; 2011 | none | accurate JPEG DCT-IDCT | p.412 |
| PSNR | 31.08 | dB | IBM 90nm; 2011 | accurate JPEG | truncation; 4 LSBs | p.413 |
| power saving | 24.22 | % | IBM 90nm; 2011 | accurate JPEG | truncation; 4 LSBs | p.413 |
| area saving | 20 | % | IBM 90nm; 2011 | accurate JPEG | truncation; 4 LSBs | p.413 |
| PSNR | 28.9 | dB | IBM 90nm; 2011 | accurate JPEG | approximation 3; 8 LSBs | p.413 |
| quality loss | 0.69 | dB | IBM 90nm; 2011 | accurate | approximation 3; lena; 7 LSBs | p.414 |
| power saving | 44.57 | % | IBM 90nm; 2011 | accurate | approximation 3; lena; 7 LSBs | p.414 |
| quality loss | 2.26 | dB | IBM 90nm; 2011 | accurate | approximation 3; lena; 8 LSBs | p.414 |
| power saving | 53.29 | % | IBM 90nm; 2011 | accurate | approximation 3; lena; 8 LSBs | p.414 |
| quality loss | 5.7 | dB | IBM 90nm; 2011 | accurate | approximation 3; lena; 9 LSBs | p.414 |
| power saving | 59.57 | % | IBM 90nm; 2011 | accurate | approximation 3; lena; 9 LSBs | p.414 |
| quality loss | 0.17 | dB | IBM 90nm; 2011 | accurate | approximation 3; mandril; 7 LSBs | p.414 |
| power saving | 40.48 | % | IBM 90nm; 2011 | accurate | approximation 3; mandril; 7 LSBs | p.414 |
| quality loss | 0.58 | dB | IBM 90nm; 2011 | accurate | approximation 3; mandril; 8 LSBs | p.414 |
| power saving | 49.67 | % | IBM 90nm; 2011 | accurate | approximation 3; mandril; 8 LSBs | p.414 |
| quality loss | 2.05 | dB | IBM 90nm; 2011 | accurate | approximation 3; mandril; 9 LSBs | p.414 |
| power saving | 54.35 | % | IBM 90nm; 2011 | accurate | approximation 3; mandril; 9 LSBs | p.414 |
| quality loss | 0.31 | dB | IBM 90nm; 2011 | accurate | approximation 3; kodim09; 7 LSBs | p.414 |
| power saving | 43.24 | % | IBM 90nm; 2011 | accurate | approximation 3; kodim09; 7 LSBs | p.414 |
| quality loss | 1.14 | dB | IBM 90nm; 2011 | accurate | approximation 3; kodim09; 8 LSBs | p.414 |
| power saving | 52.07 | % | IBM 90nm; 2011 | accurate | approximation 3; kodim09; 8 LSBs | p.414 |
| quality loss | 3.65 | dB | IBM 90nm; 2011 | accurate | approximation 3; kodim09; 9 LSBs | p.414 |
| power saving | 57.07 | % | IBM 90nm; 2011 | accurate | approximation 3; kodim09; 9 LSBs | p.414 |
| quality loss | 0.42 | dB | IBM 90nm; 2011 | accurate | approximation 3; kodim19; 7 LSBs | p.414 |
| power saving | 43.2 | % | IBM 90nm; 2011 | accurate | approximation 3; kodim19; 7 LSBs | p.414 |
| quality loss | 1.34 | dB | IBM 90nm; 2011 | accurate | approximation 3; kodim19; 8 LSBs | p.414 |
| power saving | 52.54 | % | IBM 90nm; 2011 | accurate | approximation 3; kodim19; 8 LSBs | p.414 |
| quality loss | 4.04 | dB | IBM 90nm; 2011 | accurate | approximation 3; kodim19; 9 LSBs | p.414 |
| power saving | 56.94 | % | IBM 90nm; 2011 | accurate | approximation 3; kodim19; 9 LSBs | p.414 |
| quality loss | 0.46 | dB | IBM 90nm; 2011 | accurate | approximation 3; kodim23; 7 LSBs | p.414 |
| power saving | 43.2 | % | IBM 90nm; 2011 | accurate | approximation 3; kodim23; 7 LSBs | p.414 |
| quality loss | 1.35 | dB | IBM 90nm; 2011 | accurate | approximation 3; kodim23; 8 LSBs | p.414 |
| power saving | 52.87 | % | IBM 90nm; 2011 | accurate | approximation 3; kodim23; 8 LSBs | p.414 |
| quality loss | 4.39 | dB | IBM 90nm; 2011 | accurate | approximation 3; kodim23; 9 LSBs | p.414 |
| power saving | 58.39 | % | IBM 90nm; 2011 | accurate | approximation 3; kodim23; 9 LSBs | p.414 |
| area saving | 28.5 | % | IBM 90nm; 2011 | accurate JPEG | approximation 3; 7 LSBs | p.413 |
| area saving | 32.67 | % | IBM 90nm; 2011 | accurate JPEG | approximation 3; 8 LSBs | p.413 |
| area saving | 36.85 | % | IBM 90nm; 2011 | accurate JPEG | approximation 3; 9 LSBs | p.413 |
| power saving | ≈ 42 | % | IBM 90nm; 2011 | accurate MPEG | approximation 3; 4 SAD LSBs | p.413 |
errors_and_checks: Approximation 1 has 3 erroneous Sum outputs and 1 erroneous Cout output among 8 input combinations. Approximation 2 has 3 Sum errors and 2 Cout errors. Approximation 3 has 4 Sum errors and 2 Cout errors. No hardware error detector/correction mechanism is provided. # p.411
conditions: Approximate cells are confined to LSBs so accurate cells preserve the MSBs. # pp.409,412. More than 9 approximate LSBs causes appreciable JPEG quality loss. # p.412. Supply voltages are selected so errors come only from truth-table approximation rather than voltage-overscaling timing faults. # p.412. Approximation 3 gives almost no output-quality loss with 7 or fewer approximate LSBs for the reported image benchmarks. # p.414. Truncation saves more video power but causes greater frame-quality degradation. # p.413.
evidence: §II and Table I define the cells and errors; Table II reports cell area; §III-A, Table III, Figures 7-10, and Table IV report JPEG results; §III-B and Figures 12-13 report MPEG results, pp.410-414.

## new_families
none

## space_gaps
* `lower_width` excludes the demonstrated 1/2/3/7/9-bit approximate regions. # pp.412-413
* `carry_to_upper` lacks a value for the uppermost approximate cell’s generated `Cout`. # p.410
* `approximate_compressor_tree.compressor` lacks FA-based 4:2/8:2 compressors constructed from approximate mirror-adder cells. # pp.409,412

## open_questions
* The paper does not report exact numeric values from Figures 8-10, 12-14 beyond the values stated in prose/Table IV.
* The paper does not specify separate error distributions for the complete RCA/CSA structures.
