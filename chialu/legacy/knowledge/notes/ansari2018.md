---
handle: ansari2018
citation: M. S. Ansari, H. Jiang, B. F. Cockburn, J. Han, "Low-Power Approximate Multipliers Using Encoded Partial Products and Approximate Compressors", IEEE Journal on Emerging and Selected Topics in Circuits and Systems, vol. 8, no. 3, pp. 404-416, 2018
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [int8, int16, int32]
authority: incremental
pages_read: 12 / 12
---

## summary
The paper proposes an approximate 4:2 compressor whose partial-product inputs are encoded as generate/propagate signals to reduce the probability of erroneous compressor states. Two 4×4 unsigned multipliers are recursively composed into 8×8/16×16/32×32 designs, and the compressor is also applied to an 8×8 signed radix-4 Booth multiplier. The designs trade MRED/ER/NMED against delay/power/area/PDP in ST’s 28-nm CMOS process.

## families
### approximate_compressor_tree  (role: proposes)
mechanism: The approximate 4:2 compressor omits 𝐶𝑜𝑢𝑡 and replaces XOR-heavy exact logic with AND/OR equations. Symmetric partial products are encoded as 𝑃𝑖,𝑗 = 𝑝𝑝𝑖,𝑗 + 𝑝𝑝𝑗,𝑖 and 𝐺𝑖,𝑗 = 𝑝𝑝𝑖,𝑗·𝑝𝑝𝑗,𝑖, which makes several faulty truth-table rows unreachable and reduces the faulty Carry/Sum cases from 5/7 to 2/4 in Stage 2. M1 retains carry 𝑐4 with an exact full adder, while M2 omits 𝑐4 to break the longest carry-propagation path. Larger multipliers recursively combine four smaller multipliers and sum the shifted products with a Wallace tree. # pp.2-5
choices:
  compressor: ansari_encoded   # p.2
new_choices:
  input_encoding: generate_propagate — encodes symmetric partial products as 𝑃𝑖,𝑗/𝐺𝑖,𝑗 before approximate compression   # pp.2-3
  terminal_carry_handling: {retain_c4, omit_c4} — distinguishes M1 from M2   # p.4
  recursive_exactness_placement: {all_approximate, exact_P1, approximate_P4_only} — selects which subproducts use exact multipliers   # p.4
slots:
  none
parameters: 4×4 M1/M2 building blocks; six 8×8 designs; six evaluated 16×16 designs; M32-5/M32-6; unsigned operands; exhaustive 8×8 accuracy evaluation over 65536 cases; 10 million uniformly distributed samples for 16×16 accuracy evaluation   # pp.4-6
results:
| metric | value | unit | technology / device | baseline | condition | page |
| M16-1 MRED | 0.0644 | dimensionless | UNKNOWN / 2018 | exact multiplication | 16×16 unsigned | p.6 |
| M16-1 ER | 96.71 | % | UNKNOWN / 2018 | exact multiplication | 16×16 unsigned | p.6 |
| M16-1 NMED | 5.7×10-2 | dimensionless | UNKNOWN / 2018 | exact multiplication | 16×16 unsigned | p.6 |
| M16-2 MRED | 0.0839 | dimensionless | UNKNOWN / 2018 | exact multiplication | 16×16 unsigned | p.6 |
| M16-2 ER | 96.67 | % | UNKNOWN / 2018 | exact multiplication | 16×16 unsigned | p.6 |
| M16-2 NMED | 7.2×10-2 | dimensionless | UNKNOWN / 2018 | exact multiplication | 16×16 unsigned | p.6 |
| M16-3 MRED | 0.0168 | dimensionless | UNKNOWN / 2018 | exact multiplication | 16×16 unsigned | p.6 |
| M16-3 ER | 94.74 | % | UNKNOWN / 2018 | exact multiplication | 16×16 unsigned | p.6 |
| M16-3 NMED | 1.2×10-3 | dimensionless | UNKNOWN / 2018 | exact multiplication | 16×16 unsigned | p.6 |
| M16-4 MRED | 0.0224 | dimensionless | UNKNOWN / 2018 | exact multiplication | 16×16 unsigned | p.6 |
| M16-4 ER | 94.65 | % | UNKNOWN / 2018 | exact multiplication | 16×16 unsigned | p.6 |
| M16-4 NMED | 1.9×10-3 | dimensionless | UNKNOWN / 2018 | exact multiplication | 16×16 unsigned | p.6 |
| M16-5 MRED | 0.0013 | dimensionless | UNKNOWN / 2018 | exact multiplication | 16×16 unsigned | p.6 |
| M16-5 ER | 72.49 | % | UNKNOWN / 2018 | exact multiplication | 16×16 unsigned | p.6 |
| M16-5 NMED | 5.1×10-6 | dimensionless | UNKNOWN / 2018 | exact multiplication | 16×16 unsigned | p.6 |
| M16-6 MRED | 0.0017 | dimensionless | UNKNOWN / 2018 | exact multiplication | 16×16 unsigned | p.6 |
| M16-6 ER | 72.33 | % | UNKNOWN / 2018 | exact multiplication | 16×16 unsigned | p.6 |
| M16-6 NMED | 5.7×10-6 | dimensionless | UNKNOWN / 2018 | exact multiplication | 16×16 unsigned | p.6 |
| M16-1 delay | 1.65 | nS | ST 28-nm CMOS / 2018 | Wallace-16 | 1V, 25°C | p.6 |
| M16-1 power | 302.4 | µW | ST 28-nm CMOS / 2018 | Wallace-16 | 1V, 25°C | p.6 |
| M16-1 area | 627.5 | µm² | ST 28-nm CMOS / 2018 | Wallace-16 | 1V, 25°C | p.6 |
| M16-1 PDP | 498.9 | fJ | ST 28-nm CMOS / 2018 | Wallace-16 | 1V, 25°C | p.6 |
| M16-2 delay | 1.62 | nS | ST 28-nm CMOS / 2018 | Wallace-16 | 1V, 25°C | p.6 |
| M16-2 power | 268.4 | µW | ST 28-nm CMOS / 2018 | Wallace-16 | 1V, 25°C | p.6 |
| M16-2 area | 588.6 | µm² | ST 28-nm CMOS / 2018 | Wallace-16 | 1V, 25°C | p.6 |
| M16-2 PDP | 434.8 | fJ | ST 28-nm CMOS / 2018 | Wallace-16 | 1V, 25°C | p.6 |
| M16-3 delay | 1.66 | nS | ST 28-nm CMOS / 2018 | Wallace-16 | 1V, 25°C | p.6 |
| M16-3 power | 338.8 | µW | ST 28-nm CMOS / 2018 | Wallace-16 | 1V, 25°C | p.6 |
| M16-3 area | 702.3 | µm² | ST 28-nm CMOS / 2018 | Wallace-16 | 1V, 25°C | p.6 |
| M16-3 PDP | 562.4 | fJ | ST 28-nm CMOS / 2018 | Wallace-16 | 1V, 25°C | p.6 |
| M16-4 delay | 1.64 | nS | ST 28-nm CMOS / 2018 | Wallace-16 | 1V, 25°C | p.6 |
| M16-4 power | 315.2 | µW | ST 28-nm CMOS / 2018 | Wallace-16 | 1V, 25°C | p.6 |
| M16-4 area | 673.5 | µm² | ST 28-nm CMOS / 2018 | Wallace-16 | 1V, 25°C | p.6 |
| M16-4 PDP | 516.9 | fJ | ST 28-nm CMOS / 2018 | Wallace-16 | 1V, 25°C | p.6 |
| M16-5 delay | 1.82 | nS | ST 28-nm CMOS / 2018 | Wallace-16 | 1V, 25°C | p.6 |
| M16-5 power | 408.7 | µW | ST 28-nm CMOS / 2018 | Wallace-16 | 1V, 25°C | p.6 |
| M16-5 area | 852.8 | µm² | ST 28-nm CMOS / 2018 | Wallace-16 | 1V, 25°C | p.6 |
| M16-5 PDP | 743.8 | fJ | ST 28-nm CMOS / 2018 | Wallace-16 | 1V, 25°C | p.6 |
| M16-6 delay | 1.82 | nS | ST 28-nm CMOS / 2018 | Wallace-16 | 1V, 25°C | p.6 |
| M16-6 power | 402.2 | µW | ST 28-nm CMOS / 2018 | Wallace-16 | 1V, 25°C | p.6 |
| M16-6 area | 843.5 | µm² | ST 28-nm CMOS / 2018 | Wallace-16 | 1V, 25°C | p.6 |
| M16-6 PDP | 732.0 | fJ | ST 28-nm CMOS / 2018 | Wallace-16 | 1V, 25°C | p.6 |
| M32-5 delay | 3.35 | nS | ST 28-nm CMOS / 2018 | comparison set in Table 11 | 32×32 unsigned, 1V, 25°C | p.6 |
| M32-5 power | 841.1 | µW | ST 28-nm CMOS / 2018 | comparison set in Table 11 | 32×32 unsigned, 1V, 25°C | p.6 |
| M32-5 area | 1723.4 | µm² | ST 28-nm CMOS / 2018 | comparison set in Table 11 | 32×32 unsigned, 1V, 25°C | p.6 |
| M32-5 PDP | 2817.68 | fJ | ST 28-nm CMOS / 2018 | comparison set in Table 11 | 32×32 unsigned, 1V, 25°C | p.6 |
| M32-6 delay | 3.35 | nS | ST 28-nm CMOS / 2018 | comparison set in Table 11 | 32×32 unsigned, 1V, 25°C | p.6 |
| M32-6 power | 839.7 | µW | ST 28-nm CMOS / 2018 | comparison set in Table 11 | 32×32 unsigned, 1V, 25°C | p.6 |
| M32-6 area | 1718.9 | µm² | ST 28-nm CMOS / 2018 | comparison set in Table 11 | 32×32 unsigned, 1V, 25°C | p.6 |
| M32-6 PDP | 2812.99 | fJ | ST 28-nm CMOS / 2018 | comparison set in Table 11 | 32×32 unsigned, 1V, 25°C | p.6 |
errors_and_checks: Accuracy is reported as MRED, ER, and NMED; ER is the percentage of operations whose result differs from exact multiplication. No runtime error detection or correction is included. # p.6
conditions: M2 reduces latency by omitting 𝑐4 but is less accurate than M1. # p.4 M16-2 has the lowest PDP among the compared unsigned designs. # p.6 M16-5 has 44% smaller PDP than AM2-16 at the same reported MRED. # p.11 M16-5/M16-6 have 59.25%/59.89% smaller PDP than Wallace-16. # p.11 Approximation is intended for error-tolerant applications; JPEG/image-sharpening quality and coded-MIMO BER depend on the selected multiplier variant. # pp.7-11
evidence: §III.A-D, Tables 3-7; §IV.A-B, Tables 9 and 11; §V, Figs. 6-13 and Tables 14-15.

### approximate_booth  (role: extends)
mechanism: CABM uses an exact radix-4 Booth encoder and exact sign-extension handling, while approximate compressors reduce the eight least-significant partial-product columns. The eight most-significant columns use exact compressors. Approximate compression is not applied to sign-extension bits. # p.5
choices:
  radix: 4   # p.5
  approx_encoder_columns: 0   # p.5
  encoder: exact   # p.5
new_choices:
  approximate_reduction_columns: 8 — counts LSB columns using approximate compressors independently of encoder approximation   # p.5
slots:
  none
parameters: 8×8 signed radix-4 Booth multiplier; exact Booth encoders; approximate compressors in 8 LSB columns; exact compressors in 8 MSB columns   # p.5
results:
| metric | value | unit | technology / device | baseline | condition | page |
| MRED | 0.014 | dimensionless | UNKNOWN / 2018 | exact multiplication | CABM | p.6 |
| ER | 84.72 | % | UNKNOWN / 2018 | exact multiplication | CABM | p.6 |
| NED | 0.18 | dimensionless | UNKNOWN / 2018 | exact multiplication | CABM | p.6 |
| delay | 1.63 | nS | ST 28-nm CMOS / 2018 | Exact Booth | CABM, 1V, 25°C | p.7 |
| power | 69.678 | µW | ST 28-nm CMOS / 2018 | Exact Booth | CABM, 1V, 25°C | p.7 |
| area | 284.32 | µm² | ST 28-nm CMOS / 2018 | Exact Booth | CABM, 1V, 25°C | p.7 |
| PDP | 113.575 | fJ | ST 28-nm CMOS / 2018 | Exact Booth | CABM, Table 12 | p.7 |
| PDP × MRED | 1.788 | fJ | ST 28-nm CMOS / 2018 | AWBM1/AWBM2 | CABM; Table 13 uses PDP 127.699 fJ | p.7 |
errors_and_checks: CABM reports MRED 0.014, ER 84.72%, and NED 0.18; no error detector or correction stage is included. # p.6
conditions: CABM has lower MRED than AWBM1/AWBM2. # p.6 AWBM2 has slightly lower power, while CABM has lower delay/area and more than twice the accuracy by MRED. # p.7 Approximate compressors cannot be applied to the sign-extension bits. # p.5
evidence: §III.D, Fig. 4 and Table 8; §IV.A-B, Tables 10, 12, and 13.

## new_families
none

## space_gaps
* approximate_compressor_tree lacks a choice for generate/propagate encoding of correlated partial-product inputs. # pp.2-3
* approximate_compressor_tree lacks choices for recursive block scaling and significance-based placement of exact/approximate submultipliers. # p.4
* approximate_booth lacks a choice for approximate reduction columns distinct from approximate encoder columns. # p.5
* approximate_booth lacks a reduction slot that can be filled by approximate_compressor_tree. # p.5
* error_analysis_quality lacks NMED/NED values used alongside MRED and ER. # p.6

## open_questions
* Table 12 reports CABM PDP as 113.575 fJ, while Table 13 uses 127.699 fJ to calculate PDP × MRED; the document does not reconcile the values.
* The text says six 32×32 designs were formed, but Table 7 and Table 11 report only M32-5 and M32-6.
