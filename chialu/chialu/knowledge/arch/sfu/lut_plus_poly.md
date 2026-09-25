# lut_plus_poly

Table-driven function evaluation: the argument is reduced to a
residual near a breakpoint x_i, the leading bits of the reduced
argument index a table of function values or local polynomial
coefficients, a low-degree polynomial in h = x - x_i (minimax,
Taylor, or economized series) computes the local correction, and
reconstruction combines table value, correction, and reduction
constants, then normalizes and rounds. Table
spacing and degree trade against each other: more index bits shrink
the interval and the degree needed for a given error at exponential
table cost, and table entries can be stored as lead/trail
pairs so working-precision arithmetic reaches about twice working
precision.

The software instances fix the scale: 32 entries with a degree-3
single or degree-6 double polynomial for the exponential, 128 entries
for the logarithm, and a proved bound below 0.54 ulp using only
working-precision operations. Hardware instances move the other way,
6 to 7 index bits with a degree-2 polynomial, per-coefficient widths
that leave the highest-order path narrowest, rectangular or truncated
multipliers, and a per-function bias that centers the truncation
error, so one small coefficient ROM serves several functions at one
result per cycle; on FPGAs the index width is chosen around block-RAM
and DSP thresholds rather than at its arithmetic minimum, and degree
2 carries the exponential residual through double-extended precision.
Guard bits set the rounding contract: three suffice for a faithful
result when the evaluation error before rounding is a few ulps, and
each added bit raises the fraction of correctly rounded outputs.

Breakpoint placement is the distinctive lever. Uniform breakpoints
need a working precision above the target or lead/trail entries,
whereas Gal's accurate points perturb each breakpoint until the table
value carries a run of zeros or ones after bit 53, which removes the
table's representation error at target precision and yields correct
rounding on more than 99.7 percent of arguments in a single pass at a
bound of 1 ulp, at the cost of an expensive search per function.
Basis follows the coefficient store: minimax minimizes degree, and
Taylor is chosen when coefficients must be generated on the fly under
a small constant memory. Correct rounding for every argument comes
from a quick phase and an accurate phase that share the reduction
tables. The family wins for a fixed function at fixed accuracy and
initiation interval one, replaced CORDIC in x86 units at two to three
times the speed, and loses to plain computation when memory latency
exceeds the polynomial, to CORDIC when no multiplier is affordable,
and to digit recurrence at double precision on FPGAs, where it halves
pipeline depth but spends more logic. Execution is feed-forward.

The seed instantiates the library's generated module for this family (`chialu/targets/rtl/families/sfu.py`: 2^`index_bits` segments with a coefficient table and a local polynomial of `degree`, `multiplier_shape` truncated dropping the low bits of the local variable). `python3 -m chialu.targets.rtl.families.sfu --function <fn> --format <format> --family lut_plus_poly --pins k=v,...` emits the module with its modeled error for a rewrite.

## design choices

### basis

| member | what it selects |
| --- | --- |
| `taylor` | the coefficients come from a Taylor expansion about the segment's midpoint. |
| `chebyshev` | they come from a Chebyshev fit over the segment. |
| `minimax_remez` | they come from a Remez minimax fit. |

### coeff_encoding

| member | what it selects |
| --- | --- |
| `plain` | each coefficient multiplies through a multiplier. |
| `csd` | each coefficient is its canonical signed-digit terms, summed as shifted copies. |
| `power_of_two` | each coefficient is rounded to a power of two, so the multiply is a shift. |
| `per_coeff_width` | each coefficient is narrowed from the top degree down while the sampled error stays inside the target. |
| `shared` | the top coefficient is one value for every segment and the lower ones are refitted per segment. |

## references

muller_2016 -> J.-M. Muller, "Elementary Functions: Algorithms and Implementation", 3rd ed., Birkhauser, 2016
tang_1989 -> P. T. P. Tang, "Table-Driven Implementation of the Exponential Function in IEEE Floating-Point Arithmetic", ACM Transactions on Mathematical Software, vol. 15, no. 2, pp. 144-157, 1989
tang_1990 -> P. T. P. Tang, "Table-Driven Implementation of the Logarithm Function in IEEE Floating-Point Arithmetic", ACM Transactions on Mathematical Software, vol. 16, no. 4, pp. 378-400, 1990
gal_1991 -> S. Gal, B. Bachelis, "An Accurate Elementary Mathematical Library for the IEEE Floating Point Standard", ACM Transactions on Mathematical Software, vol. 17, no. 1, pp. 26-45, 1991
pasca_2011 -> B. Pasca, "High-Performance Floating-Point Computing on Reconfigurable Circuits", PhD thesis, ENS Lyon, 2011
oberman_2005 -> S. F. Oberman, M. Y. Siu, "A High-Performance Area-Efficient Multifunction Interpolator", 17th IEEE Symposium on Computer Arithmetic (ARITH-17), pp. 272-279, 2005
dedinechin_2007 -> F. de Dinechin, C. Q. Lauter, J.-M. Muller, "Fast and Correctly Rounded Logarithms in Double-Precision", RAIRO Theoretical Informatics and Applications, vol. 41, no. 1, pp. 85-102, 2007
lynch_1995 -> T. Lynch, A. Ahmed, M. Schulte, T. Callaway, R. Tisdale, "The K5 Transcendental Functions", Proc. 12th IEEE Symposium on Computer Arithmetic, pp. 163-170, 1995.
