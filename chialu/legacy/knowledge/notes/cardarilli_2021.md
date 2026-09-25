---
handle: cardarilli_2021
citation: G. C. Cardarilli, L. Di Nunzio, R. Fazzolari, D. Giardino, A. Nannarelli, M. Re, S. Spano, "A Pseudo-Softmax Function for Hardware-Based High Speed Image Classification", Scientific Reports, vol. 11, 2021
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_SFU]
formats: [int3, int8, int10, fp17_custom]
authority: incremental
pages_read: 10 / 10
---

## summary
The document proposes pseudo-softmax, which replaces base e with base 2 so quantized integer inputs become floating-point exponents and exponential hardware is avoided. A parallel floating-point adder tree, one shared two-segment PWL reciprocal, and an exponent-subtractor array produce positive probability outputs for image classification and Boltzmann action selection. # p.2–5

## families
### softmax_layernorm  (role: extends)
mechanism: Pseudo-softmax computes 2^xi/Σ2^xk for quantized integer inputs. A binary tree adds floating-point values whose mantissas initially equal 1.0. One PWL block approximates the reciprocal of the normalized sum mantissa, while parallel integer subtractors form each output exponent xi−expsum. All outputs share the reciprocal mantissa, remain positive, and sum to one. # p.2–4
choices:
  exp_evaluation: approximate_substitute   # p.2–3
  max_subtraction: false   # p.2–3
  normalization_division: reciprocal_multiply   # p.3–4
new_choices:
  exponential_base: 2 — replaces e so each integer input directly represents a floating-point exponent   # p.2–3
slots:
  none
parameters: INT8 inputs in [−128,127]; N<128 for the stated overflow guarantee; unsigned 17-bit outputs with 9-bit unbiased exponent and 8-bit fractional mantissa; evaluated with N from 2 to 1000; unpipelined N=10 implementations; pseudo-Boltzmann temperature τ=2^T   # p.3, p.5–8
results:
| metric | value | unit | technology / device | baseline | condition | page |
| MSE | 2.7082 × 10−4 | MSE | UNKNOWN / 2021 | 0.8502 for architecture in ref. 23 | corner test 1, 10-bit inputs, N=30 | p.6 |
| MSE | 0.0019 | MSE | UNKNOWN / 2021 | 0.0018 for architecture in ref. 23 | corner test 2, 10-bit inputs, N=30 | p.6 |
| CNN approximation error | [0, 10 × 10−4] | MSE | UNKNOWN / 2021 | ref. 23; pseudo-softmax reported one order of magnitude lower | 10-bit ResNet-50/VGG-16/VGG-19/InceptionV3/MobileNetV2, 10,000 inferences | p.6–7 |
| input-to-output delay | 3.22 | ns | 90 nm 1.0 V CMOS standard-cell / 2021 | none | unpipelined INT8, N=10 | p.8 |
| maximum operating frequency | 310 | MHz | 90 nm 1.0 V CMOS standard-cell / 2021 | none | unpipelined INT8, N=10 | p.8 |
| area difference | about 30% larger | % | 90 nm 1.0 V CMOS standard-cell / 2021 | fastest architecture in ref. 23 | INT3, N=10, similar MSE ∝ 10−3 | p.8 |
errors_and_checks: The outputs sum to one and retain probability-distribution behavior. Accuracy is evaluated empirically by MSE rather than a worst-case final-output bound. INT8 and INT10 VGG-16 MSE distributions are similar, while INT3 reaches the approximately 10−3 MSE reported for the 10-bit baseline. # p.2, p.6–7
conditions: The design assumes integer-quantized network outputs, typically INT8. The 9-bit exponent avoids overflow for xi≤127 and N<128, but zero has no encoding and requires threshold comparison. The adder tree can be pipelined after each adder when throughput timing requires it. Area and power scale with input count/quantization except for the shared reciprocal block. Serial or mixed parallel-serial input support is left as future work. # p.2–4, p.8
evidence: Eq. (2), Eqs. (4)–(8), Figs. 2–3, “Hardware architecture,” “Approximation error analysis,” Figs. 5–8, and “Implementation results,” p.2–8.

### pwl  (role: instantiates)
mechanism: The normalized denominator mantissa lies in [1,2). The reciprocal block selects one of two linear polynomials at x=1.5 using the most-significant fractional mantissa bit. Each slope is the negative sum of two powers of two, so shifts and subtractors replace multiplication. Incremental refinement selects coefficients close to powers of two. # p.4–5
choices:
  segments: 2 [outside domain]   # p.4–5
  segmentation: uniform   # p.5
  x_frac_bits: 8   # p.3–5
  slope_encoding: signed_po2_pair   # p.5
new_choices:
  none
slots:
  segmenter: uniform_high_bit_decode   # p.5
parameters: domain [1.0,2.0); breakpoint 1.5; ỹ=1.59375−0.625x for x<1.5 and ỹ=1.125−0.3125x for x≥1.5; 8-bit reciprocal output   # p.4–5
results:
| metric | value | unit | technology / device | baseline | condition | page |
| maximum absolute error | 0.03125 < 2−5 | absolute reciprocal error | UNKNOWN / 2021 | exact y=1/x | exhaustive fixed-point simulation over [1.0,2.0) | p.5 |
| average error | 0.011151 < 2−7 | reciprocal error | UNKNOWN / 2021 | exact y=1/x | exhaustive fixed-point simulation over [1.0,2.0) | p.5 |
errors_and_checks: Exhaustive fixed-point simulation reports maximum absolute and average reciprocal errors; the document gives no final-output worst-case error bound. # p.5
conditions: Normalization confines the reciprocal input to [1,2), and one reciprocal result serves every pseudo-softmax output. # p.3–5
evidence: Eq. (9), Eq. (10), Fig. 4, and “Piece-wise linear reciprocal block,” p.4–5.

## new_families
none

## space_gaps
* `softmax_layernorm.exp_evaluation` identifies approximation substitution but does not record the substituted exponential base 2, which is the defining pseudo-softmax choice. # p.2–3
* `pwl.segments` excludes the two-segment reciprocal implementation reported by the document. # p.4–5

## open_questions
* Figure 8 contains area/power values that are not present as readable numbers in the supplied document text, so those absolute implementation results remain unrecorded.
* The document states that the adder tree can be pipelined but does not report a selected pipeline depth or initiation interval. # p.4
* The document does not specify a numerical threshold for mapping small positive outputs to zero. # p.3
