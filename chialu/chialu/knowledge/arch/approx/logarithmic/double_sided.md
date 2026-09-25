---
family: logarithmic
pin: {base: double_sided}
---
# double_sided

A nearest-one detector replaces the leading-one detector: each
magnitude maps to a one-hot nearest power of two, rounded up or down
and capped at 128 for 8-bit operands, and a priority encoder gives its
exponent, so an operand is A=2^k1+q1 with a residual q1 of either
sign. The product 2^(k1+k2)+q2*2^k1+q1*2^k2 is formed with shifts and
addition while q1q2 is omitted; because the residuals carry sign the
error is double-sided rather than one-sided.

Against the mitchell base, whose error is one-sided, the double_sided
base has a signed error that cancels across accumulation: ILM-0 has
the lowest MRED among the compared logarithmic multipliers and a
maximum error magnitude of 3844 output units against 4026 for
Mitchell at 8 bits. ILM-k replaces the k low-order bits of one adder
with alternating 1/0 outputs to keep the double-sided distribution
while cutting area, at 255.3 um2 for ILM-5 against 287.4 um2 for
ILM-0 in ST 28-nm. The costs are sign-magnitude operation, which may
be less efficient than two's complement for MAC, an error rate above
98 per cent, and no fault detection. It is the pick for neural
inference where accumulated error rather than per-product error sets
output quality.

## references

ansari2021 -> M. S. Ansari, B. F. Cockburn, J. Han, "An Improved Logarithmic Multiplier for Energy-Efficient Neural Computing", IEEE Transactions on Computers, vol. 70, no. 4, pp. 614-625, 2021
