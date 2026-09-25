---
handle: rouhani_2023b
citation: B. Darvish Rouhani, R. Zhao, A. More, M. Hall, et al., "Microscaling Data Formats for Deep Learning", arXiv:2310.10537, 2023
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_DOT_ACC]
formats: [fp32, bf16, MXFP8_E4M3, MXFP8_E5M2, MXFP6_E2M3, MXFP6_E3M2, MXFP4_E2M1, MXINT8]
authority: incremental
pages_read: 9 / 9
---

## summary
The document evaluates MX formats, which combine one E8M0 scale per 32-element block with FP8/FP6/FP4/INT8 elements for deep-learning dot products. MXINT8 supports direct-cast inference near FP32 results, while MXFP6 supports generative-model training near FP32 loss without changing the training recipe. MXFP4 weights combined with MXFP6 activations/gradients incur a small reported loss increase. (p.1, pp.5–8)

## families
### mx_microscaling_dot  (role: analyzes)
mechanism: An MX block represents k values as XPi, where one shared scale X multiplies k scalar elements Pi. All concrete formats use k=32 and an 8-bit E8M0 scale; element formats are FP8, FP6, FP4, or INT8. Dot-product inputs are converted to MX along the reduction dimension, while vector operations and dot-product outputs remain scalar Bfloat16 or FP32. Training quantizes dot products in forward/backward passes and retains FP32 master weights. (pp.2–4)
choices:
  block_size_k: 32   # p.3
  scale_encoding: e8m0   # p.3
  element_type: fp8_e4m3 / fp8_e5m2 / fp6 / fp4 / int8   # p.3
  accumulate_precision: bf16 / fp32   # p.4
new_choices:
  shared_scale_axis: reduction_dimension / row / column — selects the tensor axis whose k elements share X   # p.3
  conversion_rounding: round_half_to_nearest_even / round_half_away_from_zero — selects rounding during scalar-to-MX conversion   # pp.5, 7
  conversion_recipe: algorithm_1 / implementation_defined — selects the scalar-to-MX conversion semantics permitted by the specification   # p.3
slots:
  mul: UNKNOWN   # p.4
  reduction: UNKNOWN   # p.4
parameters: k=32; E8M0 scale=8 bits; MXFP8 elements=8 bits; MXFP6 elements=6 bits; MXFP4 elements=4 bits; MXINT8 elements=8 bits; pipeline stages/latency/II=UNKNOWN   # p.3
results:
| metric | value | unit | technology / device | baseline | condition | page |
| LM loss | 4.01 | loss | existing GPU emulation, device UNKNOWN / 2023 | FP32 3.98 | GPT-20M training; MXFP6_E3M2 weights/activations/gradients | p.7 |
| LM loss | 3.32 | loss | existing GPU emulation, device UNKNOWN / 2023 | FP32 3.30 | GPT-150M training; MXFP6_E3M2 weights/activations/gradients | p.7 |
| LM loss | 3.12 | loss | existing GPU emulation, device UNKNOWN / 2023 | FP32 3.11 | GPT-300M training; MXFP6_E3M2 weights/activations/gradients | p.7 |
| LM loss | 2.75 | loss | existing GPU emulation, device UNKNOWN / 2023 | FP32 2.74 | GPT-1.5B training; MXFP6_E3M2 weights/activations/gradients | p.7 |
| LM loss | 4.04 | loss | existing GPU emulation, device UNKNOWN / 2023 | FP32 3.98 | GPT-20M training; MXFP4 weights, MXFP6_E3M2 activations/gradients | p.7 |
| LM loss | 3.33 | loss | existing GPU emulation, device UNKNOWN / 2023 | FP32 3.30 | GPT-150M training; MXFP4 weights, MXFP6_E3M2 activations/gradients | p.7 |
| LM loss | 3.14 | loss | existing GPU emulation, device UNKNOWN / 2023 | FP32 3.11 | GPT-300M training; MXFP4 weights, MXFP6_E3M2 activations/gradients | p.7 |
| LM loss | 2.76 | loss | existing GPU emulation, device UNKNOWN / 2023 | FP32 2.74 | GPT-1.5B training; MXFP4 weights, MXFP6_E3M2 activations/gradients | p.7 |
| ARC easy | 0.740 ± 0.009 | score | existing GPU emulation, device UNKNOWN / 2023 | FP32 0.744 ± 0.009 | GPT3-175B direct-cast inference; MXINT8 weights/activations | p.6 |
| ARC challenge | 0.481 ± 0.015 | score | existing GPU emulation, device UNKNOWN / 2023 | FP32 0.480 ± 0.015 | GPT3-175B direct-cast inference; MXINT8 weights/activations | p.6 |
| Lambada | 0.754 ± 0.006 | score | existing GPU emulation, device UNKNOWN / 2023 | FP32 0.755 ± 0.006 | GPT3-175B direct-cast inference; MXINT8 weights/activations | p.6 |
| wikitext | 9.504 | score | existing GPU emulation, device UNKNOWN / 2023 | FP32 9.488 | LLaMA-7B direct-cast inference; MXINT8 weights/activations; lower is better | p.6 |
errors_and_checks: No arithmetic error bound, ulp contract, or hardware checker is reported. Model-level accuracy/loss is evaluated against FP32 across direct-cast/PTQ/finetuned inference and training. (pp.5–7)
conditions: MXINT8 matches FP32 within the reported standard deviation on all GPT3-175B and LLaMA-7B generative-inference tasks. MXFP6_E2M3 approaches FP32 after quantization-aware finetuning. MXFP6_E3M2 trains GPT-like models with 6-bit weights/activations/gradients using FP32-tuned hyperparameters unchanged. Quantization and transpose do not commute, so weights and transposed weights require separate MX tensors. Vector operations remain Bfloat16 or FP32, and conversion semantics may be implementation-defined. (pp.3–8)
evidence: Algorithm 1; Figures 1–4; Tables 1–8; §§2–4.5

## new_families
none

## space_gaps
* `shared_scale_axis` is absent from `mx_microscaling_dot`, although the document makes the row/column/reduction-dimension choice operational and states that it affects transposition and storage. (pp.3–4)
* `conversion_rounding` is absent from `mx_microscaling_dot`, although inference uses round-half-to-nearest-even and generative training uses round-half-away-from-zero. (pp.5, 7)
* `conversion_recipe` is absent from `mx_microscaling_dot`, although the OCP semantics permit implementation-defined recipes beyond Algorithm 1. (p.3)
* The `element_type` domain does not distinguish FP6_E2M3 from FP6_E3M2 or identify FP4_E2M1, although the results compare these encodings separately. (pp.3, 5–7)

## open_questions
* The document delegates the efficient dot-product definition to §6.2 of the OCP Microscaling Specification, so the multiplier/reduction/accumulator microarchitecture is UNKNOWN. (p.4)
* The custom CUDA experiments use existing GPUs, but the GPU model, technology node, circuit area, power, latency, and throughput are not reported. (pp.3–4)
* The accumulation precision inside the delegated MX dot product is not distinguished from its scalar Bfloat16/FP32 output format. (p.4)
