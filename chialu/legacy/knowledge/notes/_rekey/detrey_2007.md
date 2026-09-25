---
handle: detrey_2007
citation: J. Detrey, F. de Dinechin, "Parameterized Floating-Point Logarithm and Exponential Functions for FPGAs", Microprocessors and Microsystems, vol. 31, no. 8, pp. 537-545, 2007
actual_citation: Jérémie Detrey, Florent de Dinechin, "Floating-Point Trigonometric Functions for FPGAs", IEEE conference proceedings, 2007
status: mismatch
kind: paper
unit_classes: [other]
formats: [custom_float, fp32]
authority: incremental
pages_read: 29-34 / 6
---

## summary
The document proposes parameterized FPGA sine/cosine operators that combine Payne-Hanek argument reduction with HOTBM minimax-polynomial evaluation and guarantee faithful rounding for the reference floating-point design (pp.29-32). The document compares radian/π-scaled, floating-point/fixed-point-output, and dual/single-function variants on a Virtex-II XC2V1000-4 (pp.32-34).

## families
### range_reduction  (role: instantiates)
mechanism: The radian operator multiplies the input mantissa by a left-selected portion of 4/π, retains the three integer low bits for octant/sign reconstruction, and produces a reduced argument for evaluating sin((π/4)y) and cos((π/4)y). A close path derives the reduced argument exponent/mantissa directly from small x, while a far path normalizes the fixed-point reduced argument with an LZC and shifter. The sin(πx)/cos(πx) variant replaces this multiplication with an exact split into integer/fractional parts. (pp.30-33)
choices:
  method: payne_hanek   # p.30
  reduction_type: multiplicative   # p.30
  worst_case_bound_proven: true   # p.30
new_choices:
  path_structure: dual_close_far — Selects whether fixed-point Y is derived from (Ey, My) or (Ey, My) is normalized from Y.   # p.31
slots: none
parameters: 4/π storage roughly 2^(wE-1) + 3wF bits; extracted portion roughly 3wF bits; multiplier roughly wF × 3wF bits; gK determined from the smallest reduced argument; g at most 2 for faithful rounding.   # pp.30-32
results: none
errors_and_checks: The Kahan-Douglas analysis determines the smallest possible reduced argument and the required gK for a specified floating-point domain. Argument-reduction error is carried through g-bit-extended HOTBM inputs; the complete reference design guarantees relative error below 2^-wF.   # pp.30-32
conditions: Cody-Waite reduction is useful only for small arguments because it relies on floating-point operators. Iterative modular reductions are considered poorly suited to a pipelined implementation. The sin(πx)/cos(πx) interface makes reduction exact and removes one subsequent guard bit.   # pp.30, 32-33
evidence: §2; Figures 2-4; §3 dual-path argument reduction; §4 functions of πx, pp.30-33

### single_poly  (role: instantiates)
mechanism: Two HOTBM evaluators approximate transformed sine/cosine functions over the reduced domain. HOTBM starts from a minimax polynomial and constructs an optimized parallel datapath from lookup tables, powering units, and small multipliers. The cosine evaluator computes 1-cos((π/4)y), omitting the constant leading bit. The sine path factors out y, evaluates the remaining fixed-point function, and multiplies it by the floating-point reduced argument mantissa. (p.32)
choices:
  basis: minimax_remez   # p.32
new_choices:
  output_transform: sine_factor_and_cosine_residual — Removes known leading behavior before HOTBM evaluation.   # p.32
slots:
  range_reducer: range_reduction [method=payne_hanek]   # pp.30-32
parameters: input/output datapaths carry wF+g fractional bits; g is at most 2; polynomial degree/table sizes are UNKNOWN.   # p.32
results: none
errors_and_checks: HOTBM produces faithful results; the complete reference datapath targets faithful rounding, defined as relative error below 2^-wF.   # p.32
conditions: A fully pipelined CORDIC is rejected because its hardware becomes large. HOTBM is compact through single precision but grows exponentially with precision and is considered poorly suited beyond 32 bits.   # pp.32-33
evidence: §3 table-based evaluation and error analysis, p.32; §6, p.33

## new_families
### dual_sine_cosine  (domain: sfu: elementary-function units, closest: single_poly, why_not: single_poly covers the approximation kernel rather than the complete argument-reduction/evaluation/reconstruction/exception datapath)
mechanism: The operator shares one argument reducer between simultaneous sine and cosine outputs, evaluates both reduced functions, reconstructs signs/functions from the octant and input sign, and handles zero/infinity/NaN cases. Variants accept radians or π-scaled inputs, return floating-point or fixed-point outputs, compute both functions or sine alone, and optionally map multiplications to embedded FPGA multipliers. (pp.30-33)
choices: input_scaling: {radian, pi_scaled}; outputs: {sin_cos, sine_only}; output_format: {floating_point, fixed_point}; multiplier_mapping: {logic_slices, embedded_multipliers}
results:
| metric | value | unit | technology / device | baseline | condition | page |
| area / latency | 803 / 69 | slices / ns | Virtex-II XC2V1000-4 / 2007 | UNKNOWN | dual sin/cos, (wE,wF)=(5,10), logic | p.34 |
| area / latency | 424 + 7 / 61 | slices + multipliers / ns | Virtex-II XC2V1000-4 / 2007 | UNKNOWN | dual sin/cos, (5,10), embedded | p.34 |
| area / latency | 363 / 58 | slices / ns | Virtex-II XC2V1000-4 / 2007 | UNKNOWN | dual sin/cos πx, (5,10), logic | p.34 |
| area / latency | 244 + 3 / 46 | slices + multipliers / ns | Virtex-II XC2V1000-4 / 2007 | UNKNOWN | dual sin/cos πx, (5,10), embedded | p.34 |
| area / latency | 376 / 57 | slices / ns | Virtex-II XC2V1000-4 / 2007 | UNKNOWN | fixed-point out, (5,10) | p.34 |
| area / latency | 709 / 70 | slices / ns | Virtex-II XC2V1000-4 / 2007 | UNKNOWN | sine alone, (5,10) | p.34 |
| area / latency | 1159 / 86 | slices / ns | Virtex-II XC2V1000-4 / 2007 | UNKNOWN | dual sin/cos, (6,13), logic | p.34 |
| area / latency | 537 + 7 / 76 | slices + multipliers / ns | Virtex-II XC2V1000-4 / 2007 | UNKNOWN | dual sin/cos, (6,13), embedded | p.34 |
| area / latency | 641 / 61 | slices / ns | Virtex-II XC2V1000-4 / 2007 | UNKNOWN | dual sin/cos πx, (6,13), logic | p.34 |
| area / latency | 462 + 3 / 61 | slices + multipliers / ns | Virtex-II XC2V1000-4 / 2007 | UNKNOWN | dual sin/cos πx, (6,13), embedded | p.34 |
| area / latency | 642 / 63 | slices / ns | Virtex-II XC2V1000-4 / 2007 | UNKNOWN | fixed-point out, (6,13) | p.34 |
| area / latency | 1027 / 86 | slices / ns | Virtex-II XC2V1000-4 / 2007 | UNKNOWN | sine alone, (6,13) | p.34 |
| area / latency | 1652 / 91 | slices / ns | Virtex-II XC2V1000-4 / 2007 | UNKNOWN | dual sin/cos, (7,16), logic | p.34 |
| area / latency | 816 + 10 / 87 | slices + multipliers / ns | Virtex-II XC2V1000-4 / 2007 | UNKNOWN | dual sin/cos, (7,16), embedded | p.34 |
| area / latency | 865 / 73 | slices / ns | Virtex-II XC2V1000-4 / 2007 | UNKNOWN | dual sin/cos πx, (7,16), logic | p.34 |
| area / latency | 559 + 4 / 69 | slices + multipliers / ns | Virtex-II XC2V1000-4 / 2007 | UNKNOWN | dual sin/cos πx, (7,16), embedded | p.34 |
| area / latency | 923 / 72 | slices / ns | Virtex-II XC2V1000-4 / 2007 | UNKNOWN | fixed-point out, (7,16) | p.34 |
| area / latency | 1428 / 92 | slices / ns | Virtex-II XC2V1000-4 / 2007 | UNKNOWN | sine alone, (7,16) | p.34 |
| area / latency | 2549 / 99 | slices / ns | Virtex-II XC2V1000-4 / 2007 | UNKNOWN | dual sin/cos, (7,20), logic | p.34 |
| area / latency | 1372 + 17 / 96 | slices + multipliers / ns | Virtex-II XC2V1000-4 / 2007 | UNKNOWN | dual sin/cos, (7,20), embedded | p.34 |
| area / latency | 1531 / 84 | slices / ns | Virtex-II XC2V1000-4 / 2007 | UNKNOWN | dual sin/cos πx, (7,20), logic | p.34 |
| area / latency | 1005 + 8 / 76 | slices + multipliers / ns | Virtex-II XC2V1000-4 / 2007 | UNKNOWN | dual sin/cos πx, (7,20), embedded | p.34 |
| area / latency | 1620 / 82 | slices / ns | Virtex-II XC2V1000-4 / 2007 | UNKNOWN | fixed-point out, (7,20) | p.34 |
| area / latency | 2050 / 101 | slices / ns | Virtex-II XC2V1000-4 / 2007 | UNKNOWN | sine alone, (7,20) | p.34 |
| area / latency | 3320 / 109 | slices / ns | Virtex-II XC2V1000-4 / 2007 | UNKNOWN | dual sin/cos, fp32, logic | p.34 |
| area / latency | 1700 + 19 / 99 | slices + multipliers / ns | Virtex-II XC2V1000-4 / 2007 | UNKNOWN | dual sin/cos, fp32, embedded | p.34 |
| area / latency | 2081 / 89 | slices / ns | Virtex-II XC2V1000-4 / 2007 | UNKNOWN | dual sin/cos πx, fp32, logic | p.34 |
| area / latency | 1365 + 10 / 85 | slices + multipliers / ns | Virtex-II XC2V1000-4 / 2007 | UNKNOWN | dual sin/cos πx, fp32, embedded | p.34 |
| area / latency | 2203 / 88 | slices / ns | Virtex-II XC2V1000-4 / 2007 | UNKNOWN | fixed-point out, fp32 | p.34 |
| area / latency | 2659 / 105 | slices / ns | Virtex-II XC2V1000-4 / 2007 | UNKNOWN | sine alone, fp32 | p.34 |
| pipeline depth | 18 | cycles | Virtex-II -4 / 2007 | UNKNOWN | preliminary fp32 result at 100MHz | p.33 |
| initiation interval | 10 | ns | Virtex-II -4 / 2007 | libm sine: roughly 80ns/result on 2.4 GHz Pentium 4 | preliminary fp32 dual output | p.33 |
evidence: Figures 3-5, pp.31-32; §§4-5, pp.32-34; Table 1, p.34

## space_gaps
* The vocabulary lacks a complete trigonometric-operator family that composes argument reduction, simultaneous sine/cosine evaluation, octant reconstruction, and exceptional-case handling.   # pp.30-33
* The vocabulary lacks HOTBM as a polynomial-evaluator family built from lookup tables, powering units, and small multipliers.   # p.32
* range_reduction lacks the document's dual close/far path choice.   # p.31

## open_questions
* The document excerpt does not identify the conference venue of the mismatched paper.
* The document omits the HOTBM polynomial degrees, table dimensions, and detailed error derivation.   # p.32
* The fixed-point-output variant is called less accurate, but no numerical error bound is reported.   # p.33
