---
family: tensor_core_mixed_precision_mac
pin: {partial_sum_rounding: rne}
---
# rne

The IEEE-style tensor-core accumulator: in the A100 binary64 mode
each addition of the dot product rounds to nearest with ties to even
and the partial sum is normalized after every addition, so the two
products and the addend are combined as a sequence of binary64
additions rather than aligned once to the largest operand and
truncated. The mode does not always start from the largest addend.

Round-to-nearest-even with per-addition normalization gives the
accumulator the properties of scalar binary64 addition: none of the
alignment guard-digit loss and none of the non-monotonic behaviour
that the low-precision modes show when a partial sum is normalized
only at the end. Its cost is normalization and rounding logic in
every addition stage and a dot width of two terms per element in
place of eight in the binary16, bfloat16 and TensorFloat-32 modes. It
is the pick when tensor cores serve matrix work whose error must not
grow with matrix size and input magnitude, which is what limits the
truncating modes for precision-sensitive HPC; DNN training and
inference keep the low-precision modes and recover accuracy through
FP32 accumulation.

The library realizes this choice as a pin of the generated tensor_core_mixed_precision_mac module (`chialu/targets/rtl/families/dot.py`); the family card names the construction.

## references

fasi_2021 -> M. Fasi, N. J. Higham, M. Mikaitis, S. Pranesh, "Numerical Behavior of NVIDIA Tensor Cores", PeerJ Computer Science, 7:e330, 2021
markidis_2018 -> S. Markidis, S. W. D. Chien, E. Laure, I. B. Peng, J. S. Vetter, "NVIDIA Tensor Core Programmability, Performance & Precision", IEEE IPDPSW, pp. 522-531, 2018
