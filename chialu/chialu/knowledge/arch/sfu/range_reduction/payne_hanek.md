---
family: range_reduction
pin: {method: payne_hanek}
---
# payne_hanek

The significand f of x = 2^k f is multiplied by only the exponent-
selected middle bits of a long stored multiple of 1/pi: the constant
bits whose product with f is a whole number of periods are dropped on
the left, bits below the required accuracy on the right, so a p-bit
significand times a window of j + m - n bits yields the quadrant or
octant selector and the reduced fraction, with the discarded right-
hand bits bounded by 2^(-n-p). The ordinary-case cost barely depends
on argument size.

It stays accurate and efficient for large arguments and can cover the
whole floating-point range, but the window must cover the worst-case
cancellation: the smallest binary64 reduced argument for C = pi/2 is
2^-60.89, so a 20-bit window leaves the cosine of the worst-case
double correct to three digits while a 60-bit window gives sixteen.
The stored constant is EMAX - EMIN + p + i + K bits, about ten 32-bit
words for a 24-bit format and 32000 bits for VAX H-format; the VAX
routine adds reciprocal digits on demand after a leading-zero test,
for a sine/cosine error just above 3/4 ulp. Detrey's FPGA
trigonometric operator multiplies the mantissa by a 3 w_F bit portion
of 4/pi. It is the pick above the cody_waite range where tables are
unaffordable; a 24 KB table method is 4 to 5 times faster over [8,
2^63).

The library's module for range_reduction realizes this variant by its pin (`chialu/targets/rtl/families/sfu.py`).

## references

muller_2016 -> J.-M. Muller, "Elementary Functions: Algorithms and Implementation", 3rd ed., Birkhauser, 2016
muller_2018 -> J.-M. Muller, N. Brunie, F. de Dinechin, C.-P. Jeannerod, M. Joldes, V. Lefevre, G. Melquiond, N. Revol, S. Torres, "Handbook of Floating-Point Arithmetic", 2nd ed., Birkhauser, 2018
payne_1983 -> M. H. Payne, R. N. Hanek, "Radian Reduction for Trigonometric Functions", ACM SIGNUM Newsletter, vol. 18, no. 1, pp. 19-24, 1983
detrey_2007b -> J. Detrey, F. de Dinechin, "Floating-Point Trigonometric Functions for FPGAs", International Conference on Field Programmable Logic and Applications (FPL), pp. 29-34, 2007
brisebarre_2005 -> N. Brisebarre, D. Defour, P. Kornerup, J.-M. Muller, N. Revol, "A New Range-Reduction Algorithm", IEEE Transactions on Computers, vol. 54, no. 3, pp. 331-339, 2005
