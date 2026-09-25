---
family: fp8_training_datapath
pin: {format_policy: single_e5m2}
---
# single_e5m2

One 8-bit format, (1,5,2) with a 5-bit exponent and a 2-bit mantissa,
serves every GEMM operand in the forward, backward and gradient passes,
and the accumulation rather than the format survives the short
significand: products accumulate in a (1,6,9) FP16, long dot products
are split into chunks whose intra-chunk sums are accumulated first,
and the FP16 AXPY weight updates use floating-point stochastic
rounding whose error magnitude scales with the exponent.

Chunking lowers the theoretical accumulation-error bound from O(N) to
O(N/CL + CL) and limits swamping; nearest-rounded FP16 accumulation
stalls at length 4096 without chunks, chunk sizes of 32 and above
compensate, chunks above 64 cost under 5% energy in 14-nm silicon, and
FP8 multipliers accumulating into FP16 reach 2 to 4 times the
efficiency of pure FP16 (wang_2018). The gradient GEMM is the most
accumulation-sensitive operation, chunking is required for ResNet50
convergence, and the last layer and the ImageNet inputs stay in FP16.
The single format is the pick when the FPU should hold one operand
path and the accumulator carries the accuracy burden;
hybrid_forward_e4m3_backward_e5m2 wins when forward tensors need the
third mantissa bit.

The library realizes this choice as a pin of the generated fp8_training_datapath module (`chialu/targets/rtl/families/dot.py`); the family card names the construction.

## references

wang_2018 -> N. Wang, J. Choi, D. Brand, C.-Y. Chen, K. Gopalakrishnan, "Training Deep Neural Networks with 8-bit Floating Point Numbers", NeurIPS, 2018
