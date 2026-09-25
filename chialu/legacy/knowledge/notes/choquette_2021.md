---
handle: choquette_2021
citation: J. Choquette, W. Gandhi, O. Giroux, N. Stam, R. Krashinsky, "NVIDIA A100 Tensor Core GPU: Performance and Innovation", IEEE Micro, vol. 41, no. 2, pp. 29-35, 2021
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_DOT_ACC]
formats: [fp16, bf16, tf32, fp32, fp64]
authority: incremental
pages_read: 29-35 / 7
---

## summary
The document describes the A100 GPU and its third-generation Tensor Cores for HPC/AI matrix operations, including BF16/TF32/FP64 support and fine-grain sparsity. The Tensor Cores use 32-thread granularity and provide higher dense/sparse throughput than V100. # pp.29,31

## families
### tensor_core_mixed_precision_mac  (role: extends)
mechanism: A deep-learning layer performs an operation similar to matrix multiplication on activation/weight tensors. A layer tile is divided into four smaller tiles, each processed by a 32-thread warp. A100 reorganizes Tensor Cores from V100's 8-thread operating granularity to 32-thread granularity, which prevents each warp tile from requiring four separate shared-memory loads. Fine-grain sparsity doubles throughput when sparse data are processed. # pp.29,31
choices:
new_choices:
  thread_granularity: {8_thread, 32_thread} — the number of warp threads at which a Tensor Core operates # p.31
  structured_sparsity_support: Bool — whether fine-grain sparsity increases Tensor Core throughput # pp.29,31
slots:
  mul: UNKNOWN # pp.29-31
  reduction: UNKNOWN # pp.29-31
parameters: 32-thread Tensor Core granularity; four smaller tiles, each processed by one 32-thread warp; pipeline stages/latency/II UNKNOWN # p.31
results:
| metric | value | unit | technology / device | baseline | condition | page |
| dense FP16 math throughput per SM | 2x | relative throughput | TSMC 7-nm NVIDIA A100, 2021 | NVIDIA V100 | dense FP16 data | p.31 |
| dense FP16 Tensor Core throughput per GPU | 2.5 times | relative throughput | TSMC 7-nm NVIDIA A100, 2021 | NVIDIA V100 | dense FP16 data | pp.29,31 |
| FP32-data processing per GPU with TF32 | 10x | relative throughput | TSMC 7-nm NVIDIA A100, 2021 | NVIDIA V100 | TensorFloat-32 operation on FP32 data | p.31 |
| sparse-data throughput | 2x | relative throughput | TSMC 7-nm NVIDIA A100, 2021 | A100 dense-data throughput | fine-grain sparse data | p.31 |
errors_and_checks: none
conditions: The 2x dense FP16 throughput per SM requires 2x more data bandwidth, while the effective 4x sparse-data increase requires 3x more data bandwidth. The 32-thread organization reduces repeated shared-memory loading, and combined organization/data-movement changes reduce six L1+SMEM accesses to two SMEM reads. The document does not report product exactness, partial-sum rounding, alignment order, subnormal handling, accumulator precision, or arithmetic-array dimensions. # p.31
evidence: SM Core section and Figures 4-5, pp.31-32.

## new_families
none

## space_gaps
* `tensor_core_mixed_precision_mac` lacks a choice for Tensor Core thread granularity, which changes tile data delivery between V100's 8-thread organization and A100's 32-thread organization. # p.31
* `tensor_core_mixed_precision_mac` lacks a choice for hardware-supported fine-grain sparsity, which doubles A100 throughput on sparse data. # pp.29,31
* `tensor_core_mixed_precision_mac` lacks TF32/BF16/FP64 format choices, although A100 explicitly adds these Tensor Core datatypes. # pp.29,31

## open_questions
* The document does not state the Tensor Core dot width, multiplier/reduction microarchitecture, product exactness, FP32 accumulation behavior, partial-sum rounding, or subnormal support. # pp.29-31
* The document does not define the fine-grain sparsity pattern or its encoding. # pp.29,31
