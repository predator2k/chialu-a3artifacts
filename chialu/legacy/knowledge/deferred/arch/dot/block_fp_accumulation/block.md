---
family: block_fp_accumulation
pin: {exponent_sharing_granularity: block}
---
# block

One shared exponent per vector block: the significands of a block are
aligned once to the block's largest exponent, the products and their
sum run in fixed point with no intermediate normalization, and one
normalization follows the block sum. In the Stratix 10 NX tensor block
an optional 8-bit exponent is shared by each vector input of a
10-element dot product; in the textbook form a floating-point vector
times a constant vector is one block over a slightly wider fixed-point
accumulator.

The block form fits a dot-product engine whose natural unit is a
vector input: the shared exponent rides with the vector, the
fixed-point dot sums convert to FP32 for cascading or accumulation,
and the block FP16 and FP12 modes reach 143 and 286 TFLOPs at 600 MHz
on the Stratix 10 NX, with no published numerical error contract. The
initial alignment loses information from the small elements, which
the wider accumulator typically recovers over standard operators. It
is the pick when the sharing region is a vector of the dot-product
length or a constant coefficient vector, filters and Fourier
transforms included; the tile form shares one exponent over a
two-dimensional matrix tile converted before each matrix product,
which is what DNN training and MSFP inference use.

The library realizes this choice as a pin of the generated block_fp_accumulation module (`chialu/targets/rtl/families/dot.py`); the family card names the construction.

## references

muller_2018 -> J.-M. Muller, N. Brunie, F. de Dinechin, C.-P. Jeannerod, M. Joldes, V. Lefevre, G. Melquiond, N. Revol, S. Torres, "Handbook of Floating-Point Arithmetic", 2nd ed., Birkhauser, 2018
langhammer_2021 -> M. Langhammer, E. Nurvitadhi, B. Pasca, S. Gribok, "Stratix 10 NX Architecture and Applications", ACM/SIGDA International Symposium on Field-Programmable Gate Arrays (FPGA), 2021
