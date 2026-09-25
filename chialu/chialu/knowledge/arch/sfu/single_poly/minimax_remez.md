---
family: single_poly
pin: {basis: minimax_remez}
---
# minimax_remez

The equioscillating polynomial: the degree-n polynomial that minimizes
the maximum weighted error over the reduced interval, characterized by
an error curve that reaches its extreme value with alternating sign at n
+ 2 points. Remez's algorithm finds it by solving for an equioscillating
polynomial on a set of reference points and replacing those points with
the current error extrema until they coincide, with quadratic
convergence.

Minimax is the default pick for a hardware or library polynomial because
it gives the fewest terms for a target worst-case error: on [0, 1] a
degree-3 minimax exp reaches 5.4 x 10^-4, and for elementary functions
it beats Chebyshev by at most one bit and Taylor by orders of magnitude.
The degree is set by the interval, 19 for arctan on [0, 10] at 10^-5
against 1 on [0, 0.01], so the range reducer rather than the basis
controls cost. Coefficient constraints must enter the synthesis:
rounding an unconstrained Remez polynomial to binary32 or to a 2^-m
lattice can lose much accuracy, and constrained or lattice-searched
coefficients recover up to 1.5 bits, with certified supremum-norm bounds
available from Sollya. A Remez-derived logarithm correction proves to
0.5116 ulp overall.

The library's module for single_poly realizes this variant by its pin (`chialu/targets/rtl/families/sfu.py`).

## references

muller_2016 -> J.-M. Muller, "Elementary Functions: Algorithms and Implementation", 3rd ed., Birkhauser, 2016
muller_2018 -> J.-M. Muller, N. Brunie, F. de Dinechin, C.-P. Jeannerod, M. Joldes, V. Lefevre, G. Melquiond, N. Revol, S. Torres, "Handbook of Floating-Point Arithmetic", 2nd ed., Birkhauser, 2018
tang_1990 -> P. T. P. Tang, "Table-Driven Implementation of the Logarithm Function in IEEE Floating-Point Arithmetic", ACM Transactions on Mathematical Software, vol. 16, no. 4, pp. 378-400, 1990
brisebarre_2006 -> N. Brisebarre, J.-M. Muller, A. Tisserand, "Computing Machine-Efficient Polynomial Approximations", ACM Transactions on Mathematical Software, vol. 32, no. 2, pp. 236-256, 2006
