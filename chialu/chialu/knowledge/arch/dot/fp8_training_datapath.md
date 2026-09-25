# fp8_training_datapath

Training GEMMs on 8-bit floating-point operands: E4M3 or E5M2 inputs
are multiplied exactly by narrow SIMD multipliers, the product terms
are aligned to the larger product exponent and accumulated in fp16 or
fp32, and a long dot product is split into chunks whose intra-chunk
sums are accumulated first and then folded into the final result, so
the accumulation-error bound falls from O(N) to O(N/CL + CL) and small
products are not swamped. Tensors are scaled per tensor into the fp8
range before conversion, and the fp16 weight update uses stochastic
rounding. Forward tensors take the extra mantissa bit of
E4M3 and gradients take the exponent range of E5M2.

The format policy trades one datapath against two. A single E5M2 path
serves both passes with loss scaling; the hybrid policy adds an FPU
that accepts both formats at about 5% more area than an E5M2-only
FPU, or converts both to a unified 5-exponent 3-fraction internal
form. A per-layer choice from output statistics picks the format and
scale at conversion time. E4M3 buys its range by dropping infinities
and keeping a single NaN pattern, while E5M2 keeps the IEEE specials.

Accumulation precision and chunking are coupled. Nearest-rounded fp16
accumulation stops converging at dot-product length 4096 or more
without chunking, chunk sizes of 64 to 256 give the smallest error in
gradient GEMMs, which are the most accumulation-sensitive operation,
and chunks above 64 cost under 5% energy in 14 nm. Accumulating in
fp32 removes the swamping problem at the cost of the wider adder, and
H100 selects fp16 or fp32 per operation. Stochastic rounding on the
weight update is what keeps fp16 updates at fp32 accuracy; nearest
rounding drops AlexNet top-1 by about four points. Per-tensor scaling
is more flexible than a programmable exponent bias because it is not
restricted to powers of two, and gradients need auto-adjusted loss
scaling.

The accuracy contract is statistical: no ulp bound exists, and the
family is validated by model quality within run-to-run variation of
16-bit training, with the first and last layers and the softmax input
kept at fp16. It wins on training throughput, 2x fp16 at the same
power in 7 nm and on H100, with zero-multiplicand bypass and clock
gating of the unused path adding further savings on sparse
activations; it loses wherever the consumer needs a numerical error
bound rather than a converged model.

The seed instantiates the library's generated module for this family (`chialu/targets/rtl/families/dot.py`: the exact fp8 products into the frame with c; `chunk_based_accumulation` sums chunks of four products, rounds each to `accumulate_precision` through the library rounder and unpacker and re-enters them, which the module comment reports as no longer meeting the fused contract; the format policy and per-tensor scaling are the unit's modes and options, stochastic rounding is the run's SR mode). `python3 -m chialu.targets.rtl.families.dot --fab <format> --fc <format> --fd <format> --n <elements> --family <family> --pins k=v,...` emits it for a rewrite.

## design choices

### accumulate_precision

| member | what it selects |
| --- | --- |
| `fp16` | chunks of products are rounded to fp16 before the accumulate. |
| `bf16` | chunks are rounded to bf16. |
| `fp32` | chunks are rounded to fp32. |

### format_policy

| member | what it selects |
| --- | --- |
| `single_e4m3` | both operand tensors are E4M3. |
| `single_e5m2` | both are E5M2. |
| `hybrid_forward_e4m3_backward_e5m2` | E4M3 forward and E5M2 backward, which is the split the training literature uses. |

### op_shape

| member | what it selects |
| --- | --- |
| `scalar_fma` | one product and the addend. |
| `dot2_accumulate` | two products and the addend. |

## references

wang_2018 -> N. Wang, J. Choi, D. Brand, C.-Y. Chen, K. Gopalakrishnan, "Training Deep Neural Networks with 8-bit Floating Point Numbers", NeurIPS, 2018
sun_2019 -> X. Sun, J. Choi, C.-Y. Chen, N. Wang, S. Venkataramani, et al., "Hybrid 8-bit Floating Point (HFP8) Training and Inference for Deep Neural Networks", NeurIPS, 2019
micikevicius_2022 -> P. Micikevicius, D. Stosic, N. Burgess, M. Cornea, P. Dubey, R. Grisenthwaite, et al., "FP8 Formats for Deep Learning", arXiv:2209.05433, 2022
agrawal_2021 -> A. Agrawal, S. K. Lee, J. Silberman, et al., "A 7nm 4-Core AI Chip with 25.6TFLOPS Hybrid FP8 Training, 102.4TOPS INT4 Inference and Workload-Aware Throttling", IEEE ISSCC, 2021
choquette_2023 -> J. Choquette, "NVIDIA Hopper H100 GPU: Scaling Performance", IEEE Micro, vol. 43, no. 3, pp. 9-17, 2023.
