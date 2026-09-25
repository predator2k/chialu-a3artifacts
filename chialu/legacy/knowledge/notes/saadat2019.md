---
handle: saadat2019
citation: H. Saadat, H. Javaid, S. Parameswaran, "Approximate Integer and Floating-Point Dividers with Near-Zero Error Bias", 56th Design Automation Conference (DAC), 2019
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [uint8, uint16, uint32, fp16, fp32, fp64]
authority: incremental
pages_read: 6 / 6
---

## summary
The paper proposes INZeD, an approximate logarithmic unsigned integer divider that subtracts an analytically derived correction term to obtain near-zero error bias, and FaNZeD, an FP divider using an optimized INZeD mantissa path. Both designs expose a truncation parameter that trades accuracy for area-delay product and power. The evaluated designs cover 16-by-8/32-by-16 integer division and IEEE single-precision FP division. # p.1, p.3–5

## families
### approximate_functional  (role: extends)
mechanism: INZeD approximates each operand's binary logarithm from its leading-one position and fractional bits, subtracts the logarithms, subtracts a constant correction term before inverse-log scaling, and shifts the result according to the characteristic difference. The correction term approximates the average classical logarithmic-divider error within each power-of-two interval. Input-bit truncation produces the configurable INZeD-t variants. # p.2–4
choices:
  method: log_subtract_corrected   # p.2–3
  bias_correction: true   # p.3
  runtime_quality_scaling: true   # p.3–4
new_choices:
  correction_term: ϵ = 2^-5 + 2^-8 — the 8-bit approximation subtracted in the integer divider before scaling   # p.3
  truncation_bits_t: evaluated as {0, 2, 4, 6, 8, 10, 11, 12, 13} for N=16 and {0, 1, 2, 3, 4, 5} for N=8 — least-significant input bits removed from the main subtracter   # p.3–4
slots:
  none
parameters: unsigned 32-by-16 and 16-by-8 division; single-cycle combinational implementation; 8-bit correction subtracter; INZeD-t configurable truncation   # p.3–4
results:
| metric | value | unit | technology / device | baseline | condition | page |
| error bias | -0.02 | % | TSMC 45nm standard-cell library / 2019 | ALD: 3.91% | 32-by-16 INZeD | p.4 |
| mean error | 2.74 | % | TSMC 45nm standard-cell library / 2019 | ALD: 3.91% | 32-by-16 INZeD | p.4 |
| area-delay product | 728.0 | µm²×ns | TSMC 45nm standard-cell library / 2019 | accurate divider: 18869 µm²×ns | 32-by-16 INZeD | p.4 |
| power | 84.9 | µW | TSMC 45nm standard-cell library / 2019 | accurate divider: 397.9 µW | 32-by-16 INZeD | p.4 |
| error bias | 0.001 | % | TSMC 45nm standard-cell library / 2019 | ALD: 3.93% | 16-by-8 INZeD | p.4 |
| mean error | 2.75 | % | TSMC 45nm standard-cell library / 2019 | ALD: 3.93% | 16-by-8 INZeD | p.4 |
| area-delay product | 294.3 | µm²×ns | TSMC 45nm standard-cell library / 2019 | accurate divider: 1408 µm²×ns | 16-by-8 INZeD | p.4 |
| area-delay-product improvement | 25–95 | × | TSMC 45nm standard-cell library / 2019 | accurate integer divider | INZeD-t, error-bias range 0.01–4.4% | p.5 |
| power improvement | 4.7–15 | × | TSMC 45nm standard-cell library / 2019 | accurate integer divider | INZeD-t, error-bias range 0.01–4.4% | p.5 |
| area-delay-product improvement | 57.6 | × | TSMC 45nm standard-cell library / 2019 | accurate integer divider | 32-by-16 INZeD-t with less than 0.5% error bias | p.5 |
| power improvement | 9.1 | × | TSMC 45nm standard-cell library / 2019 | accurate integer divider | 32-by-16 INZeD-t with less than 0.5% error bias | p.5 |
errors_and_checks: Error bias is the mean relative error, and mean error is the mean absolute relative error. The 32-by-16 analysis uses 67 million uniformly distributed inputs; the 16-by-8 analysis is exhaustive. Inputs causing accurate-divider overflow are excluded. A nonzero approximate result when the accurate result is zero receives a 100% relative-error penalty. # p.4
conditions: The design supports 2N-by-N and N-by-N division. The truncated 2N-by-N design compares the characteristic with N and clamps an overflowing quotient to 2^N−1. Resource use decreases as t increases, while error rises once truncation reaches the correction term. # p.3–5
evidence: §3; §4.1–4.3; Fig. 2–3; Table 1; Fig. 5–6.

## new_families
### approximate_fp_log_divider  (domain: fp: floating-point dividers, closest: sig_div_then_round, why_not: sig_div_then_round requires a correctly rounded final step, while FaNZeD explicitly removes the rounding unit and returns an approximate significand quotient)
mechanism: FaNZeD subtracts FP exponents conventionally and divides normalized mantissas with an INZeD-derived logarithmic datapath. Known mantissa leading-one positions eliminate the input leading-one detectors/barrel shifters, permit a smaller main subtracter, and replace the output barrel shifter with multiplexers. The exponent, normalization, and exception-handling modules remain, while the rounding unit is removed. # p.4
choices:
  mantissa_method: {log_subtract_corrected}   # p.4
  mantissa_truncation_bits: Int[0..20:1]   # p.4–5
  rounding_unit: {removed}   # p.4
  correction_term: {2^-5 + 2^-7}   # p.4
results:
| metric | value | unit | technology / device | baseline | condition | page |
| area-delay-product improvement | 985 | × | TSMC 45nm standard-cell library / 2019 | IEEE single-precision FP divider | FaNZeD-20 | p.5 |
| power improvement | 77 | × | TSMC 45nm standard-cell library / 2019 | IEEE single-precision FP divider | FaNZeD-20 | p.5 |
| error bias | -2.22 | % | TSMC 45nm standard-cell library / 2019 | IEEE single-precision division output | FaNZeD-20 | p.5 |
| mean error | 3.81 | % | TSMC 45nm standard-cell library / 2019 | IEEE single-precision division output | FaNZeD-20 | p.5 |
| area-delay-product improvement | nearly 600 | × | TSMC 45nm standard-cell library / 2019 | IEEE single-precision FP divider | FaNZeD-t with less than 0.1% error bias | p.5 |
| power improvement | 45 | × | TSMC 45nm standard-cell library / 2019 | IEEE single-precision FP divider | FaNZeD-t with less than 0.1% error bias | p.5 |
| AlexNet Top-1 error rate | 43.24 | % | software model / 2019 | IEEE FP: 43.42% | FaNZeD-20, 5,000 ILSVRC 2012 validation images | p.6 |
| AlexNet Top-5 error rate | 20.66 | % | software model / 2019 | IEEE FP: 20.64% | FaNZeD-20, 5,000 ILSVRC 2012 validation images | p.6 |
| maximum JPEG PSNR loss | 0.4 | dB | software model / 2019 | IEEE single-precision FP divider | FaNZeD-20, reported Mandrill/Lena quality settings | p.6 |
evidence: §5; §6.2; §6.4–6.6; Fig. 4 and 7; Tables 2–4.

## space_gaps
* approximate_functional lacks choices for the constant error-correction term and the number of truncated logarithm-fraction bits. # p.3–4
* fp: floating-point dividers lacks a family for approximate significand division with the final rounding unit removed. # p.4
* error_analysis_quality lacks signed mean relative error, called error bias by the paper. # p.4

## open_questions
* The paper states that FaNZeD applies to half- and double-precision formats but reports synthesis/error results only for IEEE single precision. # p.4
* The retained exception-handling behavior is not specified in enough detail to determine subnormal/NaN/infinity semantics after removal of the rounding unit. # p.4
