---
family: cordic
pin: {coordinate_set: unified}
---
# unified

Walther's generalization: the x, y and z recurrences carry a mode
variable m that is 1 for circular, 0 for linear and -1 for hyperbolic
coordinates, so the same shift-and-add datapath with elementary
angles arctan 2^-k, 2^-k or tanh^-1 2^-k computes sine, cosine and
arctangent, multiplication and division, and sinh, cosh, exponential,
logarithm and square root. Hyperbolic convergence requires repeating
the iterations at indices 4, 13, 40, 121 and every later 3k + 1.

The unified set is the pick when one simple shift-and-add unit must
serve many functions, the case the textbooks give for CORDIC, even
though it is not the fastest method for multiplication, logarithm or
exponential: Walther's processor runs three parallel arithmetic units
with 64-bit registers and computes sin or cos in 160 microseconds and
a square root in 100 at 40-bit precision, and FPGA studies find CORDIC
better than polynomials for arctangent but worse for sine and cosine.
The domains and scale factors differ per coordinate set, about
1.74/1.0/1.13 for the angle and 1.65/1.0/0.80 for the radius factor,
and small floating-point arguments need an exponent-scaled recurrence
to keep all L result bits. A circular-only unit fixes K and the
angle table and admits the angle-recoding and prediction schemes
that assume circular rotation mode.

The library's module for cordic realizes this variant by its pin (`chialu/targets/rtl/families/sfu.py`).

## references

walther_1971 -> J. S. Walther, "A Unified Algorithm for Elementary Functions", AFIPS Spring Joint Computer Conference, pp. 379-385, 1971
muller_2016 -> J.-M. Muller, "Elementary Functions: Algorithms and Implementation", 3rd ed., Birkhauser, 2016
muller_2018 -> J.-M. Muller, N. Brunie, F. de Dinechin, C.-P. Jeannerod, M. Joldes, V. Lefevre, G. Melquiond, N. Revol, S. Torres, "Handbook of Floating-Point Arithmetic", 2nd ed., Birkhauser, 2018
meher_2009 -> P. K. Meher, J. Valls, T.-B. Juang, K. Sridharan, K. Maharatna, "50 Years of CORDIC: Algorithms, Architectures, and Applications", IEEE Transactions on Circuits and Systems I, vol. 56, no. 9, pp. 1893-1907, 2009
