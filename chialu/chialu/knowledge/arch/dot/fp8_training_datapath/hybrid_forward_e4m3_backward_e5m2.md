---
family: fp8_training_datapath
pin: {format_policy: hybrid_forward_e4m3_backward_e5m2}
---
# hybrid_forward_e4m3_backward_e5m2

Two 8-bit formats share the datapath: weights and activations in the
forward pass use E4M3 (1-4-3), which trades one exponent bit for a
third mantissa bit, and errors and gradients in the backward pass use
E5M2 (1-5-2) for its wider range. Tensors are scaled, clipped or
saturated and converted to the chosen format before the GEMM, while
arithmetic and outputs stay wider; the forward format may carry a
shifted exponent bias and the gradients an auto-adjusted loss scale.

Forward tensors need the extra mantissa bit and backward gradients the
larger exponent range; an FPU supporting both HFP8 formats is
estimated 5% larger than a 1-5-2-only FPU, and training lands within
0.5% of full precision on the tested models (sun_2019). E4M3
reallocates most special-value encodings to reach a maximum normal of
448 while E5M2 keeps IEEE-style infinities and NaNs, and per-tensor
scaling is required because one format's range does not cover every
tensor (micikevicius_2022). A 7-nm training engine converts both hfp8
formats into a unified fp9 operand with a 5-bit exponent and 3-bit
fraction and accumulates in fp16 (agrawal_2021). The hybrid policy is
the pick when training must match 16-bit accuracy; single_e5m2 keeps
one operand path and wins when chunked accumulation and stochastic
rounding alone carry the accuracy.

The library realizes this choice as a pin of the generated fp8_training_datapath module (`chialu/targets/rtl/families/dot.py`); the family card names the construction.

## references

sun_2019 -> X. Sun, J. Choi, C.-Y. Chen, N. Wang, S. Venkataramani, et al., "Hybrid 8-bit Floating Point (HFP8) Training and Inference for Deep Neural Networks", NeurIPS, 2019
micikevicius_2022 -> P. Micikevicius, D. Stosic, N. Burgess, M. Cornea, P. Dubey, R. Grisenthwaite, et al., "FP8 Formats for Deep Learning", arXiv:2209.05433, 2022
agrawal_2021 -> A. Agrawal, S. K. Lee, J. Silberman, et al., "A 7nm 4-Core AI Chip with 25.6TFLOPS Hybrid FP8 Training, 102.4TOPS INT4 Inference and Workload-Aware Throttling", IEEE ISSCC, 2021
