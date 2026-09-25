---
family: range_reduction
pin: {method: table_augmented}
---
# table_augmented

A table indexed by leading argument bits performs a second, function-
specific reduction after or instead of the constant subtraction, so
the polynomial's argument is small enough for a low degree: an
exponential splits into an integer part, a table-indexed part A and a
residual Z; a logarithm multiplies the significand by a tabulated
reciprocal r_i so that z = y r_i - 1 stays below 2^-7; a trigonometric
reduction tabulates the remainders modulo pi/2 of chunks of the
rounded integer.

It is the middle regime, for arguments of reasonable size between the
cody_waite and payne_hanek ranges, and its cost is table storage: 2^12
entries for a binary64 exponential with a 12-bit index, 64 to 256 for
logarithms, 128 reciprocals with at most 10 nonzero bits so that y r_i
and the subtraction are exact in double-extended, and 24 KB of three
tables for eight signed 7-bit chunks with a 2^-86 worst-case relative
bound at p = 14. That last design runs about 4 to 5 times faster than
a Payne-Hanek implementation over 8 < |x| < 2^63 and reverts to it
beyond. Ercegovac's small-multiplier scheme reduces with a k-bit
reciprocal table rounded down to |A| < 2^-k and one M table per
function. Smaller reduced intervals cut the polynomial degree at the
price of tables or repeated reduction.

The library's module for range_reduction realizes this variant by its pin (`chialu/targets/rtl/families/sfu.py`).

## references

muller_2016 -> J.-M. Muller, "Elementary Functions: Algorithms and Implementation", 3rd ed., Birkhauser, 2016
muller_2018 -> J.-M. Muller, N. Brunie, F. de Dinechin, C.-P. Jeannerod, M. Joldes, V. Lefevre, G. Melquiond, N. Revol, S. Torres, "Handbook of Floating-Point Arithmetic", 2nd ed., Birkhauser, 2018
dedinechin_2007 -> F. de Dinechin, C. Q. Lauter, J.-M. Muller, "Fast and Correctly Rounded Logarithms in Double-Precision", RAIRO Theoretical Informatics and Applications, vol. 41, no. 1, pp. 85-102, 2007
brisebarre_2005 -> N. Brisebarre, D. Defour, P. Kornerup, J.-M. Muller, N. Revol, "A New Range-Reduction Algorithm", IEEE Transactions on Computers, vol. 54, no. 3, pp. 331-339, 2005
ercegovac_2000 -> M. D. Ercegovac, T. Lang, J.-M. Muller, A. Tisserand, "Reciprocation, Square Root, Inverse Square Root, and Some Elementary Functions Using Small Multipliers", IEEE Transactions on Computers, vol. 49, no. 7, pp. 628-637, 2000
