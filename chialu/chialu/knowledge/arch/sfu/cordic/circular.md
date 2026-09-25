---
family: cordic
pin: {coordinate_set: circular}
---
# circular

Volder's original: three registers hold X, Y and the angle, each step
cross-adds shifted copies of X and Y while the angle register adds or
subtracts a stored arctangent constant, ROTATION takes the direction
from the angle remainder's sign and VECTORING from the sign of Y. The
first rotation is 90 degrees and the following angles are
alpha_i = tan^-1 2^-(i-2); every step rotates by a nonzero digit in
{+1, -1}, so the scale factor K depends only on the step count,
1.646760255 for n = 24.

Circular alone is the pick when the unit exists for trigonometric
work, since the elementary angles, the convergence bound of about
1.74 radians and the constant K are fixed at design time and the
angle-dependent tricks all assume it: angle recoding with greedy
closest-angle selection cuts rotations to at most n/2, 4.96 on average
for n = 16; Maharatna's scaling-free rotator folds sixteen angular
domains and enables pipeline sections directly from angle bits at
about 8 active rotations instead of 16; Wang's hybrid schemes generate
about two thirds of the directions in parallel and cut latency to about
67 percent; and the on-line CORDIC of Ercegovac and Lang transports the
angle as most-significant-first digits. The unified set adds Walther's
mode variable m, the linear and hyperbolic angle tables and the
repeated hyperbolic indices 4, 13, 40 to reach exp, log, sqrt,
multiply and divide from the same recurrence.

The library's module for cordic realizes this variant by its pin (`chialu/targets/rtl/families/sfu.py`).

## references

volder_1959 -> J. E. Volder, "The CORDIC Trigonometric Computing Technique", IRE Transactions on Electronic Computers, vol. EC-8, no. 3, pp. 330-334, 1959
hu_1993 -> Y. H. Hu, S. Naganathan, "An Angle Recoding Method for CORDIC Algorithm Implementation", IEEE Transactions on Computers, vol. 42, no. 1, pp. 99-102, 1993
maharatna_2005 -> K. Maharatna, S. Banerjee, E. Grass, M. Krstic, A. Troya, "Modified Virtually Scaling-Free Adaptive CORDIC Rotator Algorithm and Architecture", IEEE Transactions on Circuits and Systems for Video Technology, vol. 15, pp. 1463-1474, 2005
wang_1997 -> S. Wang, V. Piuri, E. E. Swartzlander, "Hybrid CORDIC Algorithms", IEEE Transactions on Computers, vol. 46, no. 11, pp. 1202-1207, 1997
walther_1971 -> J. S. Walther, "A Unified Algorithm for Elementary Functions", AFIPS Spring Joint Computer Conference, pp. 379-385, 1971
