---
family: block_fp_accumulation
pin: {inter_block_accumulate: wide_fixed_point}
---
# wide_fixed_point

Block floating point with a single fixed-point accumulator: all
vector significands are aligned once to the largest exponent of the
block, the constant multiplication and the accumulation then run in
fixed-point arithmetic in an accumulator slightly wider than the
input significands, and one normalization at the end returns the
result to floating point, with no intermediate normalization shift
anywhere in the chain.

The wide fixed-point accumulator removes every intermediate
normalization of a standard floating-point chain, and the extra
accumulator width typically improves accuracy over standard operators
even though the initial alignment loses information from the small
elements. It is the textbook form for multiplying a floating-point
vector by a constant vector, filters and Fourier transforms included,
and it is the pick when the whole reduction fits one block whose
dynamic range is known. The FP32 alternative converts each block sum
back to floating point and accumulates across blocks in FP32 ALUs,
which is what the DNN training and FPGA tensor-block designs use when
dot products span many tiles or the shared exponent changes per
vector input.

The library realizes this choice as a pin of the generated block_fp_accumulation module (`chialu/targets/rtl/families/dot.py`); the family card names the construction.

## references

muller_2018 -> J.-M. Muller, N. Brunie, F. de Dinechin, C.-P. Jeannerod, M. Joldes, V. Lefevre, G. Melquiond, N. Revol, S. Torres, "Handbook of Floating-Point Arithmetic", 2nd ed., Birkhauser, 2018
langhammer_2021 -> M. Langhammer, E. Nurvitadhi, B. Pasca, S. Gribok, "Stratix 10 NX Architecture and Applications", ACM/SIGDA International Symposium on Field-Programmable Gate Arrays (FPGA), 2021
