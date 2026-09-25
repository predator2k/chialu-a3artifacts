---
handle: burgess_2019
citation: N. Burgess, J. Milanovic, N. Stephens, K. Monachopoulos, D. Mansell, "Bfloat16 Processing for Neural Networks", ARITH-26, pp. 88-91, 2019
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_DOT_ACC]
formats: [bf16, fp25, fp32]
authority: incremental
pages_read: 88-91 / 4
---

## summary
The paper proposes BFDOT2, a SIMD operation that sums two exact BF16 products before adding the FP25 pair sum to an FP32 accumulator. Round-Odd/flush-to-zero/default-NaN behavior reduces area while the reported neural-network tests retain approximately the same accuracy as BF16 Round-to-Nearest and FP32.

## families
### bf16_fma_datapath  (role: proposes)
mechanism: Each 32-bit SIMD lane computes two BF16 products, adds the products with a reduced-area FP25 adder that rounds to FP32, and adds the pair sum to an FP32 accumulator. The BF16 multipliers use 8-bit integer multipliers to produce exact 16-bit significand products. The operation uses chained rather than fused multiply-add, Round-Odd rounding, flush-to-zero subnormal handling, default NaNs, and no IEEE exception flags. # p.88-90
choices:
  op_shape: dot2_accumulate   # p.88
  rounding_mode: round_to_odd   # p.89
  flush_subnormals: true   # p.89
new_choices:
  accumulation_structure: chained_pair_sum_then_accumulate — Two products are added in FP25 before the rounded pair sum is accumulated into FP32.   # p.89
  exception_reporting: none — Trapped and cumulative IEEE exceptions are not reported.   # p.89-90
  nan_handling: default_nan — Input NaNs are not propagated, and only one default NaN is returned.   # p.89-90
slots:
  none
parameters: BF16 inputs; FP32 accumulator/result; example 128-bit vector unit with 32-bit lanes; two BF16 products per lane; 8-bit integer multiplier; 16-bit product significand; 25-bit unpacked product; FP25 pair adder.   # p.88-89
results:
| metric | value | unit | technology / device | baseline | condition | page |
| area | approximately 25 | % reduction | UNKNOWN; 2019 | implementation supporting all 4 IEEE-mandated rounding modes | RO-only BFDOT2 RTL synthesis | p.89 |
| area | approximately 15 | % reduction | UNKNOWN; 2019 | RO-only implementation with hardware subnormal processing | RO-only BFDOT2 with subnormal operands/results flushed to zero | p.89 |
| area | 65 | % reduction | UNKNOWN; 2019 | fully IEEE-standard-compliant block | BFDOT2 with all stated simplifications | p.90 |
| roundoff error | approximately 1 | ulp more | UNKNOWN; 2019 | Round-to-Nearest | Round-Odd over 1,000 trials accumulating 18,432 FP25 numbers into FP32 | p.89 |
| average roundoff error mitigation | 0.1 | ulp | UNKNOWN; 2019 | direct accumulation using Round-Odd | FP25 numbers added in pairs before accumulation | p.89 |
| identical final BF16 results | 99.9676 | % | UNKNOWN; 2019 | BF16 Round-to-Nearest forward order | Round-Odd on extracted DeepSpeech data | p.90-91 |
| Inception Top-1 accuracy | 0.77984 | score | UNKNOWN; 2019 | BF16 RN 0.77984; FP32 RN 0.77980 | BF16 Round-Odd inference | p.90 |
| Inception Top-1 recall | 0.93942 | score | UNKNOWN; 2019 | BF16 RN 0.93942; FP32 RN 0.93942 | BF16 Round-Odd inference | p.90 |
| ResNet Top-1 accuracy | 0.75198 | score | UNKNOWN; 2019 | BF16 RN 0.75200; FP32 RN 0.75202 | BF16 Round-Odd inference | p.90 |
| ResNet Top-1 recall | 0.92186 | score | UNKNOWN; 2019 | BF16 RN 0.92186; FP32 RN 0.92194 | BF16 Round-Odd inference | p.90 |
| DeepSpeech Word Error Rate | 0.06396 | rate | UNKNOWN; 2019 | BF16 RN 0.06396; FP32 RN 0.06396 | BF16 Round-Odd inference | p.90 |
| DeepSpeech Letter Error Rate | 0.02822 | rate | UNKNOWN; 2019 | BF16 RN 0.02822; FP32 RN 0.02820 | BF16 Round-Odd inference | p.90 |
errors_and_checks: A BF16 product significand is exactly representable in FP32 unless its exponent is out of range. Round-Odd is unbiased but introduces approximately twice the rounding error of Round-to-Nearest. Extracted DeepSpeech data produced 0-bit/1-bit/2-bit RN-versus-RO differences in 99.9676%/0.0309%/0.0009% of results. The design provides no hardware fault-detection contract.   # p.88-90
conditions: BF16 multiplication avoids product rounding while the unrounded exponent remains in range.   # p.88-89; Flush-to-zero is intended for neural networks whose values fit BF16's 8-bit exponent range.   # p.89; Pairing products reduces accumulator latency and accumulated rounding error.   # p.89; Rare late cancellation can expose a larger relative error in the final BF16 result.   # p.90-91; Some neural-network models do not tolerate quantization without capability loss.   # p.88
evidence: §II; Fig. 1; Fig. 2; §III; Table I; Table II; Fig. 3; §IV, p.88-91

## new_families
none

## space_gaps
* `bf16_fma_datapath` lacks a choice for chained/fused accumulation structure, which distinguishes BFDOT2 from a fused dot product.   # p.89
* `bf16_fma_datapath` lacks choices for IEEE exception reporting and default-NaN handling.   # p.89-90

## open_questions
* The RTL synthesis technology node/device, absolute area, absolute power, timing, pipeline depth, latency, and initiation interval are not reported.
* The paper does not identify the integer-multiplier or FP25-adder microarchitecture families.
