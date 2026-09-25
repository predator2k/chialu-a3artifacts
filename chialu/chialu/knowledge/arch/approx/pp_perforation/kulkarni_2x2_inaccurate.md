---
family: pp_perforation
pin: {cell: kulkarni_2x2_inaccurate}
---
# kulkarni_2x2_inaccurate

The underdesigned multiplier: the 2x2 building block returns 7 instead
of 9 for the input 3x3 and is correct on the other fifteen inputs,
which halves the cell's area; both operands are cut into 2-bit groups,
every group pair is multiplied by such a block, the shifted block
products are accumulated by an accurate adder network, and selected
blocks can be swapped back to exact cells to tune the error/power
point. Wider recursive tilings use 4x4 blocks built from approximate
compressors.

It is the pick when a low error rate matters more than error
magnitude: the cell errs on one input in sixteen with a maximum
relative error of 22.22 percent, the multiplier-level error
probability grows with width to 0.81 at 16 bits while the mean error
stays small, dynamic power falls by about a third at 16 bits in 45 nm,
and placing the inaccuracy in the partial products beats inexact
adders in the tree. Because the accumulation stays accurate the
partial-product errors add and the tree does not change the
statistics, but the overhead is high against exact_and perforation and
NMED and MRED are large for the error rate; precise blocks at the most
significant positions cut ER and maximum error, and
error_correction_vector recovers the exact product.

## references

kulkarni2011 -> P. Kulkarni, P. Gupta, M. Ercegovac, "Trading Accuracy for Power with an Underdesigned Multiplier Architecture", 24th International Conference on VLSI Design, pp. 346-351, 2011
mittal2016 -> S. Mittal, "A Survey of Techniques for Approximate Computing", ACM Computing Surveys, vol. 48, no. 4, 2016
jiang2017 -> H. Jiang, C. Liu, L. Liu, F. Lombardi, J. Han, "A Review, Classification, and Comparative Evaluation of Approximate Arithmetic Circuits", ACM Journal on Emerging Technologies in Computing Systems, vol. 13, no. 4, 2017
mazahir2017b -> S. Mazahir, O. Hasan, R. Hafiz, M. Shafique, "Probabilistic Error Analysis of Approximate Recursive Multipliers", IEEE Transactions on Computers, vol. 66, no. 11, pp. 1982-1990, 2017
