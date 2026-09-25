---
family: range_reduction
pin: {reduction_type: multiplicative}
---
# multiplicative

The reduced argument is x* = x / C^k, recovered through identities
such as ln(x 2^k) = ln x + k ln 2, so with C a power of the radix the
reduction is an exponent/significand split that is exact and free: a
logarithm takes the mantissa in [1, 2) and the exponent separately,
and an exponential writes x = E log 2 + Y and reconstructs e^Y 2^E. A
second multiplicative stage multiplies the significand by a tabulated
reciprocal so that y r_i - 1 is small.

It has no cancellation problem while C is a radix power, so the error
analysis moves to the second stage: a reciprocal table entry rounded
down to k + 1 bits bounds the reduced argument by |A| < 2^-k, and 128
reciprocals with at most 10 nonzero bits make y r_i and the
subtraction exact in double-extended. The exponential's E may be a
relaxed estimate: the FloPoCo unit accepts an E off by one as long as
Y stays in [-1/2, 1/2), which is cheaper than guaranteeing Y in [0,
1), with at most 1 ulp of error in Y. The Payne-Hanek product with
4/pi is the multiplicative form of a trigonometric reduction, its
selector bits coming from the integer part. The additive sibling is
required when C is not a radix power and no reciprocal table applies,
as for trigonometric arguments of moderate size.

The library's module for range_reduction realizes this variant by its pin (`chialu/targets/rtl/families/sfu.py`).

## references

muller_2016 -> J.-M. Muller, "Elementary Functions: Algorithms and Implementation", 3rd ed., Birkhauser, 2016
muller_2018 -> J.-M. Muller, N. Brunie, F. de Dinechin, C.-P. Jeannerod, M. Joldes, V. Lefevre, G. Melquiond, N. Revol, S. Torres, "Handbook of Floating-Point Arithmetic", 2nd ed., Birkhauser, 2018
dedinechin_2007 -> F. de Dinechin, C. Q. Lauter, J.-M. Muller, "Fast and Correctly Rounded Logarithms in Double-Precision", RAIRO Theoretical Informatics and Applications, vol. 41, no. 1, pp. 85-102, 2007
ercegovac_2000 -> M. D. Ercegovac, T. Lang, J.-M. Muller, A. Tisserand, "Reciprocation, Square Root, Inverse Square Root, and Some Elementary Functions Using Small Multipliers", IEEE Transactions on Computers, vol. 49, no. 7, pp. 628-637, 2000
pasca_2011 -> B. Pasca, "High-Performance Floating-Point Computing on Reconfigurable Circuits", PhD thesis, ENS Lyon, 2011
