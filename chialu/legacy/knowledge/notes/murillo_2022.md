---
handle: murillo_2022
citation: R. Murillo, A. A. Del Barrio, G. Botella, M. S. Kim, H. Kim, N. Bagherzadeh, "PLAM: A Posit Logarithm-Approximate Multiplier", IEEE Transactions on Emerging Topics in Computing, 2022
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [posit16_1, posit16_2, posit32_2, fp16, bf16, fp32]
authority: incremental
pages_read: 1-7 / 7
---

## summary
PLAM replaces the posit fraction multiplication with fixed-point fraction addition using the approximation log2(1+x) ≈ x, while retaining posit sign/regime/exponent processing. The parameterized FloPoCo implementation targets DNN inference and reports lower FPGA/ASIC resource use than exact posit multipliers with similar inference accuracy.

## families
### posit_adder_multiplier  (role: proposes)
mechanism: PLAM decodes each posit into sign/regime/exponent/fraction fields and computes S = SA ⊕ SB, K = KA + KB, E = EA + EB, and F = FA + FB. Concatenating regime/exponent fields lets the exponent-add overflow feed the regime addition directly. Fraction overflow selects F or F−1 and adjusts the exponent, so the conventional fixed-point fraction multiplier is removed. The result is encoded and correctly rounded. # pp.3-5
choices:
  es_bits: 1, 2   # pp.5-6
  approximation: logarithmic_fraction   # pp.3-4
new_choices:
  rounding: round_to_nearest_even — the generated PLAM supports correct posit rounding rather than fraction truncation   # pp.3,5
slots:
  none
parameters: parameterized Posit<n,es>; fraction width n-es-3; DNN evaluation Posit<16,1>; ASIC evaluation Posit<n,2> for n=8,12,16,20,24,28,32; FPGA evaluation 16-bit and 32-bit; unpipelined hardware models   # pp.3,5-6
results:
| metric | value | unit | technology / device | baseline | condition | page |
| FPGA LUT use | 185 | LUTs | Zedboard/Zynq-7000, Vivado 2020.1 (2022) | FloPoCo-Posit [16]: 237 LUTs | 16-bit PLAM | p.5 |
| FPGA DSP use | 0 | DSPs | Zedboard/Zynq-7000, Vivado 2020.1 (2022) | FloPoCo-Posit [16]: 1 DSP | 16-bit PLAM | p.5 |
| FPGA LUT use | 435 | LUTs | Zedboard/Zynq-7000, Vivado 2020.1 (2022) | FloPoCo-Posit [16]: 604 LUTs | 32-bit PLAM | p.5 |
| FPGA DSP use | 0 | DSPs | Zedboard/Zynq-7000, Vivado 2020.1 (2022) | FloPoCo-Posit [16]: 4 DSPs | 32-bit PLAM | p.5 |
| area reduction | 69.06% | percent | TSMC 45 nm (2022) | FloPoCo-Posit [16] | 16-bit, es=2 | p.5 |
| power reduction | 63.63% | percent | TSMC 45 nm (2022) | FloPoCo-Posit [16] | 16-bit, es=2 | p.5 |
| area reduction | 72.86% | percent | TSMC 45 nm (2022) | FloPoCo-Posit [16] | 32-bit, es=2 | p.5 |
| power reduction | 81.79% | percent | TSMC 45 nm (2022) | FloPoCo-Posit [16] | 32-bit, es=2 | p.5 |
| area reduction | 50.40% | percent | TSMC 45 nm (2022) | FloPoCo FP32 | 32-bit PLAM, es=2 | p.5 |
| power reduction | 66.86% | percent | TSMC 45 nm (2022) | FloPoCo FP32 | 32-bit PLAM, es=2 | p.5 |
| delay reduction | 17.01% | percent | TSMC 45 nm (2022) | 32-bit Posit-HDL | maximum reported reduction | p.5 |
| ISOLET Top-1 accuracy | 0.9051 | accuracy fraction | Deep PeNSieve/SoftPosit emulation (2022) | exact Posit<16,1>: 0.9093 | PLAM inference | p.5 |
| UCI HAR Top-1 accuracy | 0.9282 | accuracy fraction | Deep PeNSieve/SoftPosit emulation (2022) | exact Posit<16,1>: 0.9307 | PLAM inference | p.5 |
| MNIST Top-1 accuracy | 0.9898 | accuracy fraction | Deep PeNSieve/SoftPosit emulation (2022) | exact Posit<16,1>: 0.9903 | PLAM inference | p.5 |
| SVHN Top-1 accuracy | 0.8489 | accuracy fraction | Deep PeNSieve/SoftPosit emulation (2022) | exact Posit<16,1>: 0.8513 | PLAM inference | p.5 |
| CIFAR-10 Top-1 accuracy | 0.7251 | accuracy fraction | Deep PeNSieve/SoftPosit emulation (2022) | exact Posit<16,1>: 0.7247 | PLAM inference | p.5 |
| ISOLET Top-5 accuracy | 0.9585 | accuracy fraction | Deep PeNSieve/SoftPosit emulation (2022) | exact Posit<16,1>: 0.9585 | PLAM inference | p.5 |
| UCI HAR Top-5 accuracy | 0.9841 | accuracy fraction | Deep PeNSieve/SoftPosit emulation (2022) | exact Posit<16,1>: 0.9841 | PLAM inference | p.5 |
| MNIST Top-5 accuracy | 1.0 | accuracy fraction | Deep PeNSieve/SoftPosit emulation (2022) | exact Posit<16,1>: 1.0 | PLAM inference | p.5 |
| SVHN Top-5 accuracy | 0.9761 | accuracy fraction | Deep PeNSieve/SoftPosit emulation (2022) | exact Posit<16,1>: 0.9766 | PLAM inference | p.5 |
| CIFAR-10 Top-5 accuracy | 0.9743 | accuracy fraction | Deep PeNSieve/SoftPosit emulation (2022) | exact Posit<16,1>: 0.9744 | PLAM inference | p.5 |
errors_and_checks: The relative error depends only on fA and fB and has a maximum of 11.1% when fA=fB=0.5; exponent/regime values do not affect the relative error. The implementation supports correct rounding and was checked using extensive vectors generated through an extended SoftPosit library, but no formal coverage is reported.   # pp.4-5
conditions: PLAM is evaluated by replacing exact posit multiplication only during inference after model training. The inference study covers ISOLET/UCI HAR/MNIST/SVHN/CIFAR-10, and larger networks remain unevaluated because software posit emulation makes training slow. The ASIC baselines use FloPoCo floating-point units without denormal/full-exception support. PLAM delay remains higher than the equal-width floating-point operator because posit variable-length fields require detection. The 16-bit PLAM has resource use similar to floating-point multipliers, while the FloPoCo bfloat16 implementation reports better figures.   # pp.4-6
evidence: §III, equations (12)-(24), Figs. 3-4, Tables II-III, §V, Figs. 5-6, pp.3-6

## new_families
none

## space_gaps
* posit_adder_multiplier lacks a rounding choice even though correct round-to-nearest-even support distinguishes PLAM and newer exact posit implementations from fraction-truncating designs. # pp.2,5

## open_questions
* Table III does not state the exponent-size parameter used for its 16-bit and 32-bit FPGA results.
* Figs. 5-6 plot absolute ASIC area/delay/power/energy values without tabulating the numerical points, so only textual reductions can be recorded exactly.
* The number/distribution of the “extensive testing vectors” and the resulting verification coverage are unspecified.
