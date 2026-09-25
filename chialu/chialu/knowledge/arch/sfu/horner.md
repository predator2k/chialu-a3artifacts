# horner

Nested multiply-add evaluation of a polynomial, p(y) = a0 + y (a1 +
y (a2 + ... + y ad)): d multiplications and d additions, the minimum
operation count of the evaluation schemes, arranged as one serial
dependency chain of depth d. Each step rounds the product and the sum
separately or once with a fused multiply-add; in a fixed-point
datapath each step's product is truncated a few guard bits beyond
the coefficient's least significant bit, the argument may be
truncated before the multiplication, and the bounds on both
truncations propagate through the following steps.

The scheme trades latency for operation count: it is the advised
form when the coefficients admit no exploitable factorization, it
generally favours throughput, a shallow FMA pipeline favours it and
a deep pipeline favours Estrin's tree. Naive evaluation would cost
n(n+3)/2 operations. In hardware the multiplier sizes grow with the
step index, so truncating the later steps saves the most DSP blocks,
and a degree-2 residual polynomial with three coefficients suffices
for the exponential through double-extended precision.

The error contract is an interval recurrence over the chain: the
bound is about 2 ulp(1) n sum|a(i) x^i|, and a degree-5 exponential
polynomial in double is bounded at 0.508 ulp, or 0.50025 ulp with a
double-extended intermediate; splitting the interval into 64 pieces
recovers the dependency that repeated use of x hides from interval
arithmetic and tightens a degree-4 bound from 3.625 to about 2.64
ulps. Software libraries fix the parenthesization as part of the
analysis and mix precisions along the chain, double for the high
degrees and double-double for the low ones, or fixed precision at
most steps and multiprecision only where the analysis demands it,
and the correctly rounded generators evaluate every polynomial this
way and validate the rounding exhaustively. The family is
feed-forward.

The library realizes this evaluator inside the segmented-polynomial engine (`chialu/targets/rtl/families/sfu.py`: the nested form, one multiply-add per degree).

## references

muller_2016 -> J.-M. Muller, "Elementary Functions: Algorithms and Implementation", 3rd ed., Birkhauser, 2016
muller_2018 -> J.-M. Muller, N. Brunie, F. de Dinechin, C.-P. Jeannerod, M. Joldes, V. Lefevre, G. Melquiond, N. Revol, S. Torres, "Handbook of Floating-Point Arithmetic", 2nd ed., Birkhauser, 2018
pasca_2011 -> B. Pasca, "High-Performance Floating-Point Computing on Reconfigurable Circuits", PhD thesis, ENS Lyon, 2011
tang_1989 -> P. T. P. Tang, "Table-Driven Implementation of the Exponential Function in IEEE Floating-Point Arithmetic", ACM Transactions on Mathematical Software, vol. 15, no. 2, pp. 144-157, 1989
dedinechin_2007 -> F. de Dinechin, C. Q. Lauter, J.-M. Muller, "Fast and Correctly Rounded Logarithms in Double-Precision", RAIRO Theoretical Informatics and Applications, vol. 41, no. 1, pp. 85-102, 2007
lynch_1995 -> T. Lynch, A. Ahmed, M. Schulte, T. Callaway, R. Tisdale, "The K5 Transcendental Functions", Proc. 12th IEEE Symposium on Computer Arithmetic, pp. 163-170, 1995.
lim_2021 -> J. P. Lim, M. Aanjaneya, J. Gustafson, S. Nagarakatte, "An Approach to Generate Correctly Rounded Math Libraries for New Floating Point Variants", Proceedings of the ACM on Programming Languages, vol. 5 (POPL), pp. 1-30, 2021
