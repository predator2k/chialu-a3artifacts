---
family: logarithmic
pin: {base: mitchell}
---
# mitchell

The base logarithmic multiplier: each operand 2^k(1+x) is replaced by
its piecewise-linear binary logarithm k+x, where a leading-one detector
supplies the characteristic k and the bits below the leading one stand
in for the fraction, so log2(1+x) is approximated by x. The two
representations are added, and the product is reconstructed by
shifting the summed fraction by the summed characteristic, with a
piecewise antilogarithm that distinguishes the x1+x2<1 and x1+x2>=1
cases.

The uncorrected operation is one-sided and reaches -11.1 per cent
error at worst and about 3.8 per cent on average, which is the
accuracy floor every correction line in the family starts from. The
mitchell base is the pick when speed and power matter more than
per-product accuracy; the truncated lines (Mitch-w, DR-ALM) keep only
a few bits below the leading one and reach 88 per cent energy savings
against an exact 32-bit fixed-point multiplier in 32 nm. Against the
double_sided base, whose nearest-power-of-two detector gives a signed
error, mitchell loses on accumulated error but keeps the simpler
leading-one detector; against mitchell_unbiased it keeps the negative
bias that set-one adders or a constant shift would otherwise remove.

## references

mitchell1962 -> J. N. Mitchell, "Computer Multiplication and Division Using Binary Logarithms", IRE Transactions on Electronic Computers, vol. EC-11, no. 4, pp. 512-517, 1962
jiang2020 -> H. Jiang, F. J. H. Santiago, H. Mo, L. Liu, J. Han, "Approximate Arithmetic Circuits: A Survey, Characterization, and Recent Applications", Proceedings of the IEEE, vol. 108, no. 12, pp. 2108-2135, 2020
mahalingam2006 -> V. Mahalingam, N. Ranganathan, "Improving Accuracy in Mitchell's Logarithmic Multiplication Using Operand Decomposition", IEEE Transactions on Computers, vol. 55, no. 12, pp. 1523-1535, 2006
kim2019 -> M. S. Kim, A. A. Del Barrio, L. T. Oliveira, R. Hermida, N. Bagherzadeh, "Efficient Mitchell's Approximate Log Multipliers for Convolutional Neural Networks", IEEE Transactions on Computers, vol. 68, no. 5, pp. 660-675, 2019
yin2021 -> P. Yin, C. Wang, H. Waris, W. Liu, Y. Han, F. Lombardi, "Design and Analysis of Energy-Efficient Dynamic Range Approximate Logarithmic Multipliers for Machine Learning", IEEE Transactions on Sustainable Computing, vol. 6, no. 4, pp. 612-625, 2021
