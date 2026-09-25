---
handle: carmichael_2019
citation: Z. Carmichael, H. F. Langroudi, C. Khazanov, J. Lillie, J. L. Gustafson, D. Kudithipudi, "Deep Positron: A Deep Neural Network Using the Posit Number System", Design, Automation and Test in Europe (DATE), 2019
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_DOT_ACC]
formats: [fixed5-8, fp5-8, posit5-8, fp32]
authority: incremental
pages_read: 7 / 7
---

## summary
Deep Positron uses parameterized exact multiply-and-accumulate units for low-precision posit DNN inference, with fixed-point and floating-point units implemented for equal-width comparison (pp.1, 3-5). The posit EMAC accumulates exact products in a quire and performs one convergent rounding after the complete sum (p.4). On three low-dimensional datasets, the 8-bit posit implementation matches or exceeds the tested 8-bit floating-point/fixed-point accuracies (p.5).

## families
### posit_quire_mac  (role: proposes)
mechanism: Each posit operand is decoded into sign/regime/exponent/fraction fields. Exact fraction products are converted to a signed fixed-point position using a biased combined scale factor, then accumulated in a quire. The quire holds the complete sum of k products without intermediate truncation or rounding. A leading-zero detector extracts the magnitude and scale after accumulation, and convergent round-to-nearest/ties-to-even precedes posit encoding. A D flip-flop separates multiplication and accumulation for pipelining. (pp.3-4)
choices:
  quire_width_bits: qsize = 2^(es+2) × (n − 2) + 2 + ⌈log2(k)⌉, n ≥ 3 [outside domain]   # p.4
  organization: monolithic_register   # pp.3-4
  op_set: fused_dot_product   # pp.3-4
new_choices:
  rounding_mode: round_to_nearest_ties_to_even — selects the single post-accumulation rounding rule   # pp.3-4
  input_exception_policy: real_inputs_only — excludes Not a Real inputs from the implementation   # p.4
slots:
  none
parameters: posit width n; exponent-size parameter es; k input pairs; qsize = 2^(es+2) × (n − 2) + 2 + ⌈log2(k)⌉; tested widths n = 5 through 8; one register boundary between multiplication and accumulation; II UNKNOWN   # pp.3-5
results:
| metric | value | unit | technology / device | baseline | condition | page |
| classification accuracy | 85.89 | % | Xilinx Virtex-7 xc7vx485t-2ffg1761c / 2019 | 8-bit floating-point 77.4%; 8-bit fixed-point 57.8%; 32-bit float 90.1% | 8-bit EMAC, Wisconsin Breast Cancer dataset, inference size 190 | p.5 |
| classification accuracy | 98 | % | Xilinx Virtex-7 xc7vx485t-2ffg1761c / 2019 | 8-bit floating-point 96%; 8-bit fixed-point 92%; 32-bit float 98% | 8-bit EMAC, Iris dataset, inference size 50 | p.5 |
| classification accuracy | 96.4 | % | Xilinx Virtex-7 xc7vx485t-2ffg1761c / 2019 | 8-bit floating-point 96.4%; 8-bit fixed-point 95.9%; 32-bit float 96.8% | 8-bit EMAC, Mushroom dataset, inference size 2708 | p.5 |
| best accuracy degradation below 8 bits | 0-4.21 | % | Xilinx Virtex-7 xc7vx485t-2ffg1761c / 2019 | 32-bit floating-point | best tested posit configurations have es ∈ {0, 2} | p.5 |
errors_and_checks: Products and their sum are retained exactly in the fixed-point quire; truncation and rounding occur only after all products have accumulated. The output uses round-to-nearest/ties-to-even. NaR inputs are excluded, and no fault-detection mechanism or coverage result is reported.   # pp.3-4
conditions: The design targets DNN inference at widths of 8 bits or less. Posit has higher dynamic range for n ≤ 7 and can operate at a higher frequency than floating point for a given dynamic range, while fixed-point has the lowest datapath latency and EDP. Posit generally uses more LUTs because decoding and encoding are more involved. The reported application results cover three low-dimensional datasets rather than full-scale DNN accelerators.   # pp.5-6
evidence: §III.A, §III.D, Algorithms 1-2, Fig. 5, §IV.A-B, Figs. 6-9, Table II (pp.3-5)

## new_families
none

## space_gaps
* `posit_quire_mac.quire_width_bits` does not represent the paper's parameterized qsize formula or its low-precision quire widths (p.4).
* `posit_quire_mac` lacks choices for post-accumulation rounding and NaR input handling, both of which the implementation fixes (pp.3-4).
* `posit_quire_mac` lacks component slots for the posit LZD/shift decoder and the exact fixed-point accumulator datapath (p.4).

## open_questions
* Table II does not identify the selected es value for each dataset's 8-bit posit result (p.5).
* Figs. 6-9 plot frequency/EDP/LUT results without tabulating exact coordinates, so the merge pass must not derive exact values from the supplied text (p.5).
* The tested values of k and the resulting instantiated qsize values are not reported (pp.3-5).
