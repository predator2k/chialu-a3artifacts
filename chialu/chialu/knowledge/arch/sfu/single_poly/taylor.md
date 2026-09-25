---
family: single_poly
pin: {basis: taylor}
---
# taylor

The local expansion: the polynomial is the truncated Taylor series of
the function about a point of the reduced interval, so its coefficients
are the scaled derivatives, its error is smallest at the expansion point
and grows toward the interval ends, and its degree for a target error is
set by the interval width. It pays only when range reduction has made
the interval tiny, so that after reducing |A| below 2^-k a degree-3
series, with terms below 2^-4k discarded, fills an n = 4k bit result.

Taylor is the pick when the reduced argument is small enough that the
local error is the interval error, and when the coefficients must be
known analytically rather than precomputed: after a table-augmented
reduction to |A| < 2^-k the degree-3 series needs only three k by k
multiplications and gives faithful reciprocal, square root and inverse
square root through double precision with a series error below 8.31 x
2^-4k; the Altera exponential uses e^y ~ 1 + y after a three-table
reduction, and LIBMCR evaluates log(r/y) by an odd series through the
13th power at 77-bit accuracy. Over a wide interval it loses badly: at
degree 2 on [-1, 1] the exp error is 0.218 against 0.050 for Chebyshev
and 0.045 for minimax, and at degree 11 for sin on [0, pi/4] minimax is
six orders better.

The library's module for single_poly realizes this variant by its pin (`chialu/targets/rtl/families/sfu.py`).

## references

muller_2016 -> J.-M. Muller, "Elementary Functions: Algorithms and Implementation", 3rd ed., Birkhauser, 2016
muller_2018 -> J.-M. Muller, N. Brunie, F. de Dinechin, C.-P. Jeannerod, M. Joldes, V. Lefevre, G. Melquiond, N. Revol, S. Torres, "Handbook of Floating-Point Arithmetic", 2nd ed., Birkhauser, 2018
ercegovac_2000 -> M. D. Ercegovac, T. Lang, J.-M. Muller, A. Tisserand, "Reciprocation, Square Root, Inverse Square Root, and Some Elementary Functions Using Small Multipliers", IEEE Transactions on Computers, vol. 49, no. 7, pp. 628-637, 2000
pasca_2011 -> B. Pasca, "High-Performance Floating-Point Computing on Reconfigurable Circuits", PhD thesis, ENS Lyon, 2011
