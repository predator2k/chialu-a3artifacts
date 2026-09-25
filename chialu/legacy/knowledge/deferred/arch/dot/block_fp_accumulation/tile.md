---
family: block_fp_accumulation
pin: {exponent_sharing_granularity: tile}
---
# tile

One shared exponent per two-dimensional tile: a matrix tile, or a
bounding box along the channel depth of a convolution tensor, takes
the maximum element exponent, each mantissa is right-shifted by its
exponent difference with the low bits truncated, and a dot product
multiplies the sign-magnitude mantissas in fixed point, reduces the
products with fixed-point additions and adds the two shared exponents
once; longer dot products sum several bounding-box-sized units inside
a systolic tensor core.

Tile sharing is chosen where tensors are converted just before each
matrix product, so the exponent is selected per tile from the largest
value and the tile is the unit the tensor core consumes. Tile size
trades error against exponent-handling cost: each doubling of the
bounding box adds about 0.52 dB of quantization noise in MSFP15,
sizes 16 to 128 were effective for inference, and 24 by 24 and 64 by
64 tiles keep training within 0.5 percent of FP32; MSFP16 to MSFP11
reach 8.8 to 50.9 times the MAC density of Float32 in 16 nm at size
16. Per-tile accumulation adds one floating-point operation per 2N
fixed-point operations for an N by N tile, and inputs tolerate the
alignment loss only while large terms dominate the reduction. The
block form shares an exponent per vector input instead, which suits
an FPGA dot-product block whose unit is a vector.

The library realizes this choice as a pin of the generated block_fp_accumulation module (`chialu/targets/rtl/families/dot.py`); the family card names the construction.

## references

rouhani_2020 -> B. Darvish Rouhani, D. Lo, R. Zhao, et al., "Pushing the Limits of Narrow Precision Inferencing at Cloud Scale with Microsoft Floating Point", NeurIPS, 2020
drumond_2018 -> M. Drumond, T. Lin, M. Jaggi, B. Falsafi, "Training DNNs with Hybrid Block Floating Point", NeurIPS, pp. 451-461, 2018
