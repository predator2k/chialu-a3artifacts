---
family: softmax_layernorm
pin: {exp_evaluation: base2_shift_add}
---
# base2_shift_add

The exponential by shifts and additions in base 2: after online maximum
subtraction the input lies in (-inf, 0], the Log2Exp unit forms the
exponential with shift and add operations and emits it as a 4-bit log2
code rather than a linear value, the codes are reduced by online
normalization, and the division is a Mitchell-style leading-one detect,
subtraction, multiplexing and shift. The unit is a two-stage pipeline
with ping-pong buffers and 8-bit inputs and outputs.

Base-2 shift-add is the pick when memory traffic and energy dominate:
the 4-bit exponent codes shrink the softmax intermediate buffers from 16
bits to 4, and in 28 nm the SOLE softmax unit is 3.04x more
energy-efficient and 2.82x more area-efficient than Softermax and
averages 36.2x the throughput of a 2080Ti GPU at token length 785. The
accuracy contract is empirical: without retraining the worst drop is
under 0.9% against FP32 and 0.8% against INT8 over ImageNet-1K, GLUE and
SQuAD, with an average near 0.38% and 0.2%. The unit assumes
maximum-shifted inputs and 8-bit activations, and its logarithmic codes
trade the linear precision that the polynomial sibling keeps; it pairs
with the log-domain normalization rather than a reciprocal multiply.

The library's module for softmax_layernorm realizes this variant by its pin (`chialu/targets/rtl/families/sfu.py`).

## references

wang_2023 -> W. Wang, S. Zhou, W. Sun, P. Sun, Y. Liu, "SOLE: Hardware-Software Co-Design of Softmax and LayerNorm for Efficient Transformer Inference", IEEE/ACM International Conference on Computer-Aided Design (ICCAD), pp. 1-9, 2023
