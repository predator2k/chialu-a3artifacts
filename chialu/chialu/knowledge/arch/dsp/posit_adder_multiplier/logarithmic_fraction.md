---
family: posit_adder_multiplier
pin: {approximation: logarithmic_fraction}
---
# logarithmic_fraction

The posit logarithm-approximate multiplier (PLAM): after decoding,
the sign is the XOR of the operand signs, the regimes add, the
exponents add, and the fractions add instead of multiply, with the
concatenated regime and exponent fields letting an exponent overflow
carry straight into the regime sum. A fraction overflow selects F or
F-1 and bumps the exponent, so the fixed-point fraction multiplier
disappears; the result is encoded and correctly rounded.

The approximation is the pick for inference datapaths that tolerate
a bounded relative error: the error depends only on the two
fractions, peaks at 11.1 percent when both are one half, and is
independent of regime and exponent, and top-1 accuracy on five
classification sets stays within about half a percent of exact
posit<16,1>. In TSMC 45 nm the 16-bit and 32-bit units cut area by
69 and 73 percent and power by 64 and 82 percent against the exact
FloPoCo posit multiplier, and the 32-bit unit is half the area of an
FP32 multiplier, at 185 LUTs and no DSP for 16 bits on a Zynq. Its
delay stays above the equal-width float multiplier because the
variable-length fields still need detection, and it is unusable
where the exact-rounding contract of the standard applies.

The library's PLAM module (`posit.plam_sv`) realizes this variant on X: the fractions added instead of multiplied, the sum's carry raising the exponent, a relative error of at most 1/9; the seed uses it under an approximate contract only, since an exact contract keeps the exact multiplier.

## references

murillo_2022 -> R. Murillo, A. A. Del Barrio, G. Botella, M. S. Kim, H. Kim, N. Bagherzadeh, "PLAM: A Posit Logarithm-Approximate Multiplier", IEEE Transactions on Emerging Topics in Computing, 2022
