---
handle: micikevicius_2022
citation: P. Micikevicius, D. Stosic, N. Burgess, M. Cornea, P. Dubey, R. Grisenthwaite, et al., "FP8 Formats for Deep Learning", arXiv:2209.05433, 2022
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_DOT_ACC]
formats: [fp8_e4m3, fp8_e5m2, fp16, bf16, fp32, int8]
authority: landmark
pages_read: 9 / 9
---

## summary
The paper proposes E4M3/E5M2 FP8 binary interchange encodings for deep-learning training and inference (p.1-3). Simulated FP8 training generally matches FP16/bfloat16 model quality, while E4M3 post-training quantization retains more model quality than int8 for the evaluated language models (p.4-6). The paper specifies formats and usage rather than an arithmetic microarchitecture (p.4).

## families
### fp8_training_datapath  (role: analyzes)
mechanism: Tensors are scaled, clipped or saturated, converted to E4M3/E5M2, and supplied to GEMM operations; arithmetic and outputs remain wider precision (p.2, p.4). E4M3 is recommended for weights/activations and E5M2 for gradients (p.3). Training experiments emulate FP8 by converting operands to FP8 and back to FP16/bfloat16 before wider-precision arithmetic, so no FP8 multiplier/accumulator circuit is instantiated (p.4).
choices:
  format_policy: hybrid_forward_e4m3_backward_e5m2   # p.3
  per_tensor_scaling: true   # p.2, p.4, p.6
new_choices:
  special_value_policy: E4M3_no_infinity_single_nan_pattern; E5M2_ieee_specials — E4M3 reallocates most special-value encodings to extend range, while E5M2 retains IEEE-style infinities/NaNs/zeros   # p.3
  scaling_granularity: per_tensor_activations_per_channel_weights — scaling granularity used for post-training quantization   # p.6
  conversion_overflow: saturate_or_optional_nonsaturating — saturation is used normally, with an optional strict non-saturating conversion mode   # p.2
  conversion_rounding: implementation_selected — round-to-nearest-even/stochastic and other modes are left to software or hardware   # p.2
slots:
  none
parameters: 8-bit S.E.M encodings; E4M3 has exponent bias 7, maximum normal 448, minimum normal 2^-6, and minimum subnormal 2^-9; E5M2 has exponent bias 15, maximum normal 57,344, minimum normal 2^-14, and minimum subnormal 2^-16 (p.3). Evaluated models reach 175B parameters (p.5).
results:
| metric | value | unit | technology / device | baseline | condition | page |
| VGG-16 | 71.11 | top-1 accuracy | UNKNOWN / 2022 | FP16/bfloat16 71.27 | FP8 training, ILSVRC12 validation | p.4 |
| VGG-16 BN | 73.69 | top-1 accuracy | UNKNOWN / 2022 | FP16/bfloat16 73.95 | FP8 training, ILSVRC12 validation | p.4 |
| Inception v3 | 77.06 | top-1 accuracy | UNKNOWN / 2022 | FP16/bfloat16 77.23 | FP8 training, ILSVRC12 validation | p.4 |
| DenseNet 121 | 75.33 | top-1 accuracy | UNKNOWN / 2022 | FP16/bfloat16 75.59 | FP8 training, ILSVRC12 validation | p.4 |
| DenseNet 169 | 76.83 | top-1 accuracy | UNKNOWN / 2022 | FP16/bfloat16 76.97 | FP8 training, ILSVRC12 validation | p.4 |
| Resnet18 | 70.12 | top-1 accuracy | UNKNOWN / 2022 | FP16/bfloat16 70.58 | FP8 training, ILSVRC12 validation | p.4 |
| Resnet34 | 73.72 | top-1 accuracy | UNKNOWN / 2022 | FP16/bfloat16 73.84 | FP8 training, ILSVRC12 validation | p.4 |
| Resnet50 v1.5 | 76.76 | top-1 accuracy | UNKNOWN / 2022 | FP16/bfloat16 76.71 | FP8 training, ILSVRC12 validation | p.4 |
| Resnet101 v1.5 | 77.48 | top-1 accuracy | UNKNOWN / 2022 | FP16/bfloat16 77.51 | FP8 training, ILSVRC12 validation | p.4 |
| ResNeXt50 | 77.62 | top-1 accuracy | UNKNOWN / 2022 | FP16/bfloat16 77.68 | FP8 training, ILSVRC12 validation | p.4 |
| Xception | 79.17 | top-1 accuracy | UNKNOWN / 2022 | FP16/bfloat16 79.46 | FP8 training, ILSVRC12 validation | p.4 |
| MobileNet v2 | 71.04 | top-1 accuracy | UNKNOWN / 2022 | FP16/bfloat16 71.65 | FP8 training, ILSVRC12 validation | p.4 |
| DeiT small | 80.02 | top-1 accuracy | UNKNOWN / 2022 | FP16/bfloat16 80.08 | FP8 training, ILSVRC12 validation | p.4 |
| GNMT | 24.65 | BLEU score | UNKNOWN / 2022 | FP16/bfloat16 24.83 | FP8 training, WMT 2016 English-to-German | p.5 |
| Transformer Base | 26.83 | BLEU score | UNKNOWN / 2022 | FP16/bfloat16 26.87 | FP8 training, WMT 2016 English-to-German | p.5 |
| Transformer Large | 28.35 | BLEU score | UNKNOWN / 2022 | FP16/bfloat16 28.43 | FP8 training, WMT 2016 English-to-German | p.5 |
| Transformer-XL Base | 22.99 | perplexity | UNKNOWN / 2022 | FP16/bfloat16 22.98 | FP8 training | p.5 |
| Transformer-XL Large | 17.75 | perplexity | UNKNOWN / 2022 | FP16/bfloat16 17.80 | FP8 training | p.5 |
| GPT 126M | 19.24 | perplexity | UNKNOWN / 2022 | FP16/bfloat16 19.14 | FP8 training | p.5 |
| GPT 1.3B | 10.66 | perplexity | UNKNOWN / 2022 | FP16/bfloat16 10.62 | FP8 training | p.5 |
| GPT 5B | 8.98 | perplexity | UNKNOWN / 2022 | FP16/bfloat16 8.94 | FP8 training | p.5 |
| GPT 22B | 7.24 | perplexity | UNKNOWN / 2022 | FP16/bfloat16 7.21 | FP8 training | p.5 |
| GPT 175B | 6.68 | perplexity | UNKNOWN / 2022 | bfloat16 6.65 | Reported at 75% training because baseline was incomplete | p.5 |
| BERT Base | 88.09 | F1 | UNKNOWN / 2022 | 16-bit FP 88.19; int8 76.89 | E4M3 post-training quantization, SQuAD v1.1 | p.6 |
| BERT Large | 90.94 | F1 | UNKNOWN / 2022 | 16-bit FP 90.87; int8 89.65 | E4M3 post-training quantization, SQuAD v1.1 | p.6 |
| GPT3 126M | 19.43 | perplexity | UNKNOWN / 2022 | 16-bit FP 19.01; int8 28.37 | E4M3 post-training quantization, wikitext103 | p.6 |
| GPT3 1.3B | 10.29 | perplexity | UNKNOWN / 2022 | 16-bit FP 10.19; int8 12.74 | E4M3 post-training quantization, wikitext103 | p.6 |
| GPT3 6.7B | 8.41 | perplexity | UNKNOWN / 2022 | 16-bit FP 8.51; int8 10.29 | E4M3 post-training quantization, wikitext103 | p.6 |
| GPT3 1.3B GEMM+residuals | 10.44 | perplexity | UNKNOWN / 2022 | bfloat16 10.19; fixed bias 7 gives 12.59 | Per-tensor-scaled E4M3 inference | p.6-7 |
errors_and_checks: No arithmetic-error/ulp bound or hardware fault model is reported. Validation uses downstream model quality against FP16/bfloat16; most training results are described as within run-to-run variation, with MobileNet v2 identified as an exception (p.4-5).
conditions: FP8 values require scaling because one format's range may not cover every tensor; per-tensor scaling is more flexible than programmable exponent bias because it is not restricted to powers of two (p.2, p.4). The experiments quantize primarily GEMM inputs and retain higher-precision outputs, while quantizing residual connections increases the need for per-tensor scaling (p.4, p.6-7). The study reports no hardware area/latency/power measurements because FP8 arithmetic is simulated with wider arithmetic (p.4).
evidence: Table 1 and Sections 2-3 define the formats and usage (p.2-4); Tables 2-4 and Figure 1 report training quality (p.4-5); Table 5 and Figure 2 report post-training quantization/scaling results (p.6-7).

## new_families
none

## space_gaps
* The fp8_training_datapath vocabulary lacks choices for exponent/mantissa allocation and format-specific infinity/NaN encoding, which are the paper's primary design decisions (p.3).
* The fp8_training_datapath vocabulary lacks activation/weight scaling granularity and overflow-conversion policy (p.2, p.6).

## open_questions
* The paper leaves rounding mode, including stochastic rounding, to the implementation (p.2).
* The paper does not specify an FP8 multiplier, reduction tree, accumulator precision, pipeline, latency, or initiation interval (p.4).
* The GPT 175B baseline comparison is measured at 75% training because the bfloat16 baseline was incomplete (p.5).
