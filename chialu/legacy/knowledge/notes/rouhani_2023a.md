---
handle: rouhani_2023a
citation: B. Darvish Rouhani, R. Zhao, V. Elango, et al., "With Shared Microexponents, A Little Shifting Goes a Long Way", ISCA, 2023
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_DOT_ACC]
formats: [MX4, MX6, MX9, FP8, BF16, FP32, INT4, INT6, INT8, MSFP12, MSFP16]
authority: landmark
pages_read: 1-13 / 13
---

## summary
The document introduces Block Data Representations and proposes MX formats that use hardware-managed shared microexponents for fine-grained two-level scaling in dot-product units. MX4/MX6/MX9 define 4-bit/6-bit/9-bit representations that trade numerical fidelity against dot-product area and memory efficiency.

## families
### mx_microscaling_dot  (role: proposes)
mechanism: MX partitions values into first-level blocks of 16 and two-element sub-blocks. An 8-bit power-of-two exponent scales each first-level block, while a shared 1-bit microexponent conditionally right-shifts each two-element sub-block during reduction. The dot-product pipeline multiplies mantissas, applies sub-block shifts within the adder tree, reduces each block, normalizes block results to the largest exponent, accumulates them in fixed point, converts the result to FP32, and performs FP32 accumulation. # pp.4-5
choices:
  block_size_k: 16   # p.7
  scale_encoding: two_level_microexponent   # pp.4,7
  element_type: MX4, MX6, MX9 [outside domain]   # p.7
  accumulate_precision: fp32   # p.5
new_choices:
  sub_block_size_k2: 2 — number of elements sharing each microexponent   # p.7
  global_scale_bits_d1: 8 — width of the first-level power-of-two exponent   # p.7
  microexponent_bits_d2: 1 — width of each second-level exponent   # p.7
  mantissa_bits_m: {2, 4, 7} — explicit mantissa widths for MX4/MX6/MX9   # p.7
  quantization_axis: reduction_dimension — tensor dimension along which MX blocks are formed   # p.7
  reduction_precision_f: min(25, maximum possible dynamic range) — fixed-point precision used after block reduction   # p.5
slots:
  none
parameters: MX4: k1=16, k2=2, d1=8, d2=1, m=2, 4 average bits/element; MX6: k1=16, k2=2, d1=8, d2=1, m=4, 6 average bits/element; MX9: k1=16, k2=2, d1=8, d2=1, m=7, 9 average bits/element; dot length r is configurable; pipeline stages/latency/II are UNKNOWN.   # pp.5,7
results:
| metric | value | unit | technology / device | baseline | condition | page |
| area-memory cost | approximately 2× lower | normalized area-memory efficiency product | leading-edge process node; 2023 | configurable FP8 dot product supporting E4M3 and E5M2 | MX6; symmetric 64-element dot product; 256-element tile packed into a 64B interface | p.7 |
| area-memory cost | 4× lower | normalized area-memory efficiency product | leading-edge process node; 2023 | configurable FP8 dot product supporting E4M3 and E5M2 | MX4; Gaussian distribution with variable variance | p.7 |
| QSNR difference | about 16dB higher | dB | UNKNOWN; 2023 | FP8 E4M3 | MX9; Gaussian distribution with variable variance | p.7 |
| QSNR difference | approximately 3.6dB higher | dB | UNKNOWN; 2023 | MSFP16 | MX9 | p.7 |
| QSNR change | 0.5dB higher | dB | UNKNOWN; 2023 | d2=1 | increasing d2 from 1-bit to 2-bit; normalized cost rises 30 − 50% | p.7 |
| QSNR change | approximately 2dB higher | dB | UNKNOWN; 2023 | k2=8 | reducing k2 to 2 with d2=1; normalized cost rises 3% | p.7 |
| QSNR change | 0.7dB higher | dB | UNKNOWN; 2023 | k2=2 | reducing k2 to 1; normalized cost rises 30 − 40% | p.7 |
| GPT-XL language-model loss | 2.74 | LM loss | UNKNOWN; 2023 | FP32: 2.74 | MX9 training; 1.5B-parameter model | p.10 |
| MoE language-model loss | 2.21 | LM loss | UNKNOWN; 2023 | FP32: 2.22 | MX9 training; 1.9B-parameter model | p.10 |
errors_and_checks: QSNR is the numerical-fidelity metric. For β=2^d2−1, the paper proves QSNR ≥ 6.02m + 10 log(2^(2β)/(min(N,k1)+(2^(2β)−1)k2)) for an arbitrary FP32 input distribution. The empirical QSNR study averages more than 10K independent vectors. No fault-detection mechanism is reported.   # pp.6,11
conditions: MX tensors must be quantized along the reduction dimension, so quantization and transpose do not commute.   # p.7
  Tensor reductions use MX, while Layernorm/Softmax/GELU/residual addition normally use BF16 or FP32.   # p.7
  MX6 may require quantization-aware fine-tuning for inference and more iterations for training, while MX9 is evaluated as a direct replacement for FP32/BF16/FP16.   # pp.8-10
  Hardware area estimates use a 10ns timing constraint with only input/output registers and target minimum area rather than optimal pipelining.   # p.5
evidence: Fig. 4 and Table I p.4; Fig. 6 pp.5-6; Fig. 7 and Table II pp.6-7; Tables III-VII pp.8-10; Theorem 1 pp.6,11.

## new_families
none

## space_gaps
* `mx_microscaling_dot.element_type` lacks MX4/MX6/MX9 values, which are the paper's three selected formats. # p.7
* `mx_microscaling_dot` lacks first-level exponent width, microexponent width, microexponent sharing granularity, and mantissa-width choices. # p.7
* `mx_microscaling_dot` lacks a slot or choice for the fixed-point reduction/FP32 accumulation pipeline. # p.5

## open_questions
* The leading-edge process node is not identified. # p.6
* The multiplier/reduction-tree/adder circuit families are not disclosed. # p.5
* Optimal register placement, pipeline depth, latency, and initiation interval are not reported. # p.5
* Proprietary generative-inference accuracy measurements are explicitly not reported. # p.7
