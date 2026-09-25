---
family: cordic
pin: {scale_compensation: constant_multiplier}
---
# constant_multiplier

Because every step rotates by a nonzero digit, the pseudorotations
stretch the vector by a factor K fixed by the iteration count alone,
1.6467605 for circular after enough iterations and 0.8281 for
hyperbolic with the repeated indices, so the compensation is one
multiplication by the reciprocal of K after the last rotation,
deferred out of the loop and done by a multiplication routine or a
dedicated multiplier.

The constant multiplier is the pick when a multiplier is on hand or
when several results share one correction: Volder's navigation
example spends two multiplications on five trigonometric operations,
and Meher lists postprocessing, interleaved, merged rotation-scaling
and separate-pipeline-stage schedules for placing it. It keeps the
rotation digit set at {+1, -1} and the gain angle-independent, which
the fixed-angle {-1, 0, +1} recoding gives up. Scaling iterations
instead absorb the factor into extra shift-add steps, as merged
(1 + alpha_i 2^-i) factors or altered microangles, and Hu's recoded
rotator counts its modified Booth norm-correction digits as
additional iterations, 9.6 in total against 4.96 rotations on average
for n = 16; Maharatna's scaling-free rotator makes the factor 1 or
1/sqrt 2 by construction.

The library's module for cordic realizes this variant by its pin (`chialu/targets/rtl/families/sfu.py`).

## references

volder_1959 -> J. E. Volder, "The CORDIC Trigonometric Computing Technique", IRE Transactions on Electronic Computers, vol. EC-8, no. 3, pp. 330-334, 1959
meher_2009 -> P. K. Meher, J. Valls, T.-B. Juang, K. Sridharan, K. Maharatna, "50 Years of CORDIC: Algorithms, Architectures, and Applications", IEEE Transactions on Circuits and Systems I, vol. 56, no. 9, pp. 1893-1907, 2009
hu_1993 -> Y. H. Hu, S. Naganathan, "An Angle Recoding Method for CORDIC Algorithm Implementation", IEEE Transactions on Computers, vol. 42, no. 1, pp. 99-102, 1993
muller_2016 -> J.-M. Muller, "Elementary Functions: Algorithms and Implementation", 3rd ed., Birkhauser, 2016
maharatna_2005 -> K. Maharatna, S. Banerjee, E. Grass, M. Krstic, A. Troya, "Modified Virtually Scaling-Free Adaptive CORDIC Rotator Algorithm and Architecture", IEEE Transactions on Circuits and Systems for Video Technology, vol. 15, pp. 1463-1474, 2005
