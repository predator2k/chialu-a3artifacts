---
handle: kalamkar_2019
citation: D. Kalamkar, D. Mudigere, N. Mellempudi, D. Das, K. Banerjee, et al., "A Study of BFLOAT16 for Deep Learning Training", arXiv:1905.12322, 2019
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_DOT_ACC]
formats: [bfloat16, fp32, fp16, int16]
authority: landmark
pages_read: 1-10 / 10
---

## summary
The paper establishes a mixed-precision training flow with BFLOAT16 inputs, FP32 accumulation, and FP32 master weights across vision/speech/language/generative/recommendation workloads (p.4). BFLOAT16 training matches the reported FP32 baselines without loss scaling or hyperparameter changes, subject to workload-specific tensor placement (pp.5-8).

## families
### bf16_fma_datapath  (role: analyzes)
mechanism: Core GEMM operations consume BFLOAT16 weights/activations and accumulate into FP32 tensors. The paper states that an FMA can use 8-bit multipliers because BFLOAT16 retains the FP32 exponent range with a smaller significand. Quantlib emulates BFLOAT16 by modifying FP32 operands before GEMM, while AVX512BF16 dot-product instructions with FP32 accumulation are exercised through bit-accurate emulation (pp.2-4, 8).
choices:
  rounding_mode: rne   # pp.2, 8
new_choices:
  conversion_rounding: {round_to_nearest_even, direct_truncation} — rounding applied when FP32 tensors are reduced to BFLOAT16 precision   # pp.2, 7-8
slots:
  mul: none
parameters: BFLOAT16 bit format (s,e,m) = (1,8,7); 16-bit inputs; FP32 accumulator; FMA uses 8-bit multipliers; native-memory experiment stores activations/weights as 16bit data   # pp.3-4, 8
results:
| metric | value | unit | technology / device | baseline | condition | page |
| AlexNet top-1 accuracy | 57.2% | % | UNKNOWN; result year 2019 | FP32: 57.4% | ImageNet-1K, 88 epochs, global minibatch 1024, 16 nodes | p.5 |
| AlexNet top-5 accuracy | 80.1% | % | UNKNOWN; result year 2019 | FP32: 80.7% | ImageNet-1K, 88 epochs, global minibatch 1024, 16 nodes | p.5 |
| ResNet-50 top-1 accuracy | 74.7% | % | UNKNOWN; result year 2019 | FP32: 74.7% | ImageNet-1K, 90 epochs, 32 nodes | p.5 |
| ResNet-50 top-5 accuracy | 92.0% | % | UNKNOWN; result year 2019 | FP32: 92.0% | ImageNet-1K, 90 epochs, 32 nodes | p.5 |
| GNMT BLEU | 29.3 | BLEU | UNKNOWN; result year 2019 | FP32: 29.3 | De→En, WMT’16 | p.6 |
| GNMT BLEU | 18.3 | BLEU | UNKNOWN; result year 2019 | FP32: 17.1 | Vi→En, IWSLT’15 + attention | p.6 |
| DC-GAN Inception Score | 2.06 ± 0.055 | score | UNKNOWN; result year 2019 | FP32: 1.97 ± 0.054 | face dataset | p.6 |
| DC-GAN MS-SSIM | 0.217 | MS-SSIM | UNKNOWN; result year 2019 | FP32: 0.262 | face dataset | p.6 |
| SR-GAN PSNR | 26.1415 | PSNR | UNKNOWN; result year 2019 | FP32: 26.1749 | DIV2K | p.7 |
| SR-GAN SSIM | 0.74079 | SSIM | UNKNOWN; result year 2019 | FP32: 0.73753 | DIV2K | p.7 |
| SR-GAN MS-SSIM | 0.99999 | MS-SSIM | UNKNOWN; result year 2019 | FP32: 0.99999 | DIV2K | p.7 |
| Deep & Cross Network log loss | 0.44372 | log loss | UNKNOWN; result year 2019 | FP32: 0.44372 | BFLOAT16 round-to-nearest, Kaggle Criteo | p.8 |
| DNN recommender log loss | 0.12520 | log loss | UNKNOWN; result year 2019 | FP32: 0.12520 | BFLOAT16 round-to-nearest, TeraByte Criteo | p.8 |
| ResNet-50 top-1 accuracy | 75.62% | % | current AVX512 silicon, bit-accurate AVX512BF16 emulation; result year 2019 | current state-of-the-art performance | ImageNet, 16bit memory operands, BFLOAT16 dot product with FP32 accumulation | p.8 |
errors_and_checks: The paper gives no arithmetic-error/ULP bound. End-to-end validation compares convergence and task accuracy with FP32; direct truncation produces about 0.02% recommendation-accuracy degradation, while round-to-nearest matches the FP32 log-loss baselines (pp.5-8).
conditions: BFLOAT16 retains the FP32 exponent range, which avoids the loss scaling required by FP16 (pp.3-4). GEMM inputs use BFLOAT16 and outputs accumulate in FP32; biases/weight updates/master weights remain FP32 (p.4). Most results use FP32 execution after BFLOAT16 operand emulation, so the paper reports no silicon area/power/latency result (pp.2, 8).
evidence: §3; Table 1; Figure 1; Figure 2; Tables 2-5; §4.5 (pp.3-8)

## new_families
### fp32_bfloat16_tensor_conversion  (domain: fp format converters, closest: shift_round_convert, why_not: shift_round_convert covers fp↔int conversion rather than reduction between floating-point formats)
mechanism: Quantlib retains each value in an FP32 container while zeroing the lower 16 bits and applying round-to-nearest-even, which gives FP32 hardware the precision/rounding behavior expected from BFLOAT16 operands. Direct truncation is also evaluated for recommendation workloads. Native AVX512BF16 execution instead keeps activation/weight data as 16bit values in memory (pp.2, 7-8).
choices: source_format: {fp32}; target_format: {bfloat16}; rounding: {round_to_nearest_even, direct_truncation}; storage_form: {fp32_container, native_16bit}
results:
| metric | value | unit | technology / device | baseline | condition | page |
| Deep & Cross Network log loss | 0.44393 | log loss | UNKNOWN; result year 2019 | round-to-nearest: 0.44372; FP32: 0.44372 | direct truncation, Kaggle Criteo | p.8 |
| DNN recommender log loss | 0.12537 | log loss | UNKNOWN; result year 2019 | round-to-nearest: 0.12520; FP32: 0.12520 | direct truncation, TeraByte Criteo | p.8 |
evidence: Quantlib description (p.2); Table 5 and §4.5 (p.8)

## space_gaps
* `bf16_fma_datapath.rounding_mode` lacks the document’s `direct_truncation` conversion mode (p.8).
* The fp format-converter vocabulary lacks FP32-to-BFLOAT16 precision reduction with FP32-container/native-16bit storage forms (pp.2, 8).

## open_questions
* Table 1 reports BFLOAT16 minimum subnormal as `N/A`, but the paper does not state whether hardware flushes subnormal inputs/results, so `flush_subnormals` remains UNKNOWN (p.4).
* The AVX512BF16 dot-product instruction’s product count/shape is not given, so `op_shape` remains UNKNOWN (p.8).
