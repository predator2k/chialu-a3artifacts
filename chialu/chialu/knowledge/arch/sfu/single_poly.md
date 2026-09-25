# single_poly

One polynomial over the whole reduced interval: a range reducer maps
the argument into a bounded interval, a polynomial is fitted there in
a Taylor, orthogonal (least-squares) or minimax basis, where Remez's
algorithm iterates to the equioscillating polynomial with quadratic
convergence, the coefficients are constrained during synthesis to
machine numbers or per-coefficient widths rather than rounded
afterwards, and an evaluator (Horner, Estrin, FMA-based, a shared
multiplier, or a factored form) computes it. The final error is the
approximation error plus the finite-precision evaluation error, and
the two are bounded separately.

Degree and interval move together and the range reducer sets the
exchange rate: on [0,1] a minimax polynomial gives sin 7.8 bits at
degree 2 and 41.9 at degree 9, but sqrt only 3.9 to 6.0 because it is
not smooth at 0; arctan on [0,10] needs degree 19 for 1e-5 while
[0,0.01] needs degree 1. Very high degrees (47 for arctan on Itanium)
simplify range reduction and cut memory where Estrin parallelism and
extended precision hide the latency, at 52 to 70 cycles and 0.51 ulp.
The basis fixes the constant: Taylor is local and poor interval-wide
(degree-2 exp on [-1,1]: 0.218 against 0.045 minimax), minimax beats
Chebyshev by at most one bit, and odd or even symmetry halves the
coefficient count.

Coefficient encoding is where hardware polynomials are won. Rounding
an unconstrained minimax polynomial can raise the error by orders of
magnitude (8e-32 rounded against 8e-37 constrained at degree 21), so
constraints belong in the synthesis: a lattice search over the
polytope of candidate integer coefficients gains about 1.5 bits over
rounded coefficients for low-degree small-width polynomials near
24-bit precision, and linear programming against per-input rounding
intervals accepts a larger approximation error while keeping the
final result correctly rounded. Guard bits are the internal width
beyond the target; decomposing the reduced argument into k-bit blocks
turns a degree-3 Taylor evaluation into three k by k multiplications
with a proven error of a few units of 2^-4k, faithfully rather than
correctly rounded. A shared multiplier and adder evaluate a degree-4
minimax over several cycles when area matters more than latency.

The family wins when a function is needed over a limited range with no
table, and it is the local approximation inside table-driven and
piecewise schemes. It loses once the interval is wide enough that the
degree explodes; splitting the interval or adding a table buys degree
with memory. The contract is faithful or correctly rounded as the
error budget dictates; certified supremum-norm bounds and exhaustive
validation are how a 0.5116 ulp near-one logarithm or a bfloat16
library is proven.

The seed instantiates the library's generated module for this family (`chialu/targets/rtl/families/sfu.py`: one polynomial of `degree` over the reduced domain in the `basis`, through the evaluator slot's family). `python3 -m chialu.targets.rtl.families.sfu --function <fn> --format <format> --family single_poly --pins k=v,...` emits the module with its modeled error for a rewrite.

## design choices

### coeff_encoding

| member | what it selects |
| --- | --- |
| `plain` | each coefficient multiplies through a multiplier. |
| `csd` | each coefficient is its canonical signed-digit terms, summed as shifted copies. |
| `power_of_two` | each coefficient is rounded to a power of two, so the multiply is a shift. |
| `per_coeff_width` | each coefficient is narrowed from the top degree down while the sampled error stays inside the target. |
| `shared` | one coefficient value is shared, which a single polynomial over one domain leaves equal to plain. |

## references

muller_2016 -> J.-M. Muller, "Elementary Functions: Algorithms and Implementation", 3rd ed., Birkhauser, 2016
muller_2018 -> J.-M. Muller, N. Brunie, F. de Dinechin, C.-P. Jeannerod, M. Joldes, V. Lefevre, G. Melquiond, N. Revol, S. Torres, "Handbook of Floating-Point Arithmetic", 2nd ed., Birkhauser, 2018
brisebarre_2006 -> N. Brisebarre, J.-M. Muller, A. Tisserand, "Computing Machine-Efficient Polynomial Approximations", ACM Transactions on Mathematical Software, vol. 32, no. 2, pp. 236-256, 2006
tang_1990 -> P. T. P. Tang, "Table-Driven Implementation of the Logarithm Function in IEEE Floating-Point Arithmetic", ACM Transactions on Mathematical Software, vol. 16, no. 4, pp. 378-400, 1990
ercegovac_2000 -> M. D. Ercegovac, T. Lang, J.-M. Muller, A. Tisserand, "Reciprocation, Square Root, Inverse Square Root, and Some Elementary Functions Using Small Multipliers", IEEE Transactions on Computers, vol. 49, no. 7, pp. 628-637, 2000
lim_2021 -> J. P. Lim, M. Aanjaneya, J. Gustafson, S. Nagarakatte, "An Approach to Generate Correctly Rounded Math Libraries for New Floating Point Variants", Proceedings of the ACM on Programming Languages, vol. 5 (POPL), pp. 1-30, 2021
richards_1955 -> Richards, "Arithmetic Operations in Digital Computers", Van Nostrand, 1955
