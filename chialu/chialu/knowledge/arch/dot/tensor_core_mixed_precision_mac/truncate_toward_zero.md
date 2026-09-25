---
family: tensor_core_mixed_precision_mac
pin: {partial_sum_rounding: truncate_toward_zero}
---
# truncate_toward_zero

The shipped low-precision tensor-core accumulator: the exact binary16
products and the addend are aligned to the largest-magnitude operand,
each addition truncates toward zero, partial sums are not normalized
but keep two or three bits of carry headroom above the binary32
significand, and only the final result is normalized, then rounded
toward zero into binary32. V100 keeps no bits below the binary32
significand; T4 and the A100 binary16, bfloat16 and TensorFloat-32
modes keep one extra bit.

Truncation with final-only normalization is what lets a four- or
eight-term dot product plus addend close in one pass with at most
four rounding errors per output element, but it is not IEEE
addition: with no alignment guard digits a cancellation case reaches
relative error 1, and the result is non-monotonic, since raising c11
from 1 - 2^-24 to 1 moves the output from 1 + 2^-23 to 1. The mode
retains full-precision products and supports subnormals, and the
error grows with matrix size and input magnitude, which limits it for
precision-sensitive HPC. It is the pick for training and inference
where an FP32 accumulator absorbs the bias; the A100 binary64 mode
instead rounds to nearest even and normalizes after every addition.

The library realizes this choice as a pin of the generated tensor_core_mixed_precision_mac module (`chialu/targets/rtl/families/dot.py`); the family card names the construction.

## references

fasi_2021 -> M. Fasi, N. J. Higham, M. Mikaitis, S. Pranesh, "Numerical Behavior of NVIDIA Tensor Cores", PeerJ Computer Science, 7:e330, 2021
markidis_2018 -> S. Markidis, S. W. D. Chien, E. Laure, I. B. Peng, J. S. Vetter, "NVIDIA Tensor Core Programmability, Performance & Precision", IEEE IPDPSW, pp. 522-531, 2018
