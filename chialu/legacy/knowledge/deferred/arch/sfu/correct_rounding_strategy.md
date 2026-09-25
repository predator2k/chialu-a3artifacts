# correct_rounding_strategy

The exactly rounded contract for an elementary function: the result
must equal the rounding of the exact value, and an approximation
with error 2^-m cannot decide the last bit when its interval crosses
a breakpoint, a midpoint for round-to-nearest or a number for directed
modes, the Table Maker's Dilemma. Ziv's retry evaluates at
about n+10 to n+20 bits with a rounding test and re-evaluates at
higher precision only for the rare hard cases; a single pass runs
once at a precision set by the published worst-case distance of any
input from a breakpoint; RLIBM synthesis fits the polynomial to each
input's rounding interval by linear programming so that one
fixed-precision pass rounds correctly.

The strategy trades average cost, worst-case latency and proof
effort. The two-phase retry runs a quick phase of 60 to 80 bits and
an accurate phase of 120 to 150 bits sized from the known hard cases,
taken in under 1% of calls at about ten times the quick phase's time,
so the correctly rounded logarithm averages 339 cycles against 323
for the default libm on a Pentium 4, worst case 4824 against 8424; without worst-case knowledge the fallback must assume hundreds
of bits and the worst case runs to hundreds of thousands of cycles.
The accurate-table variants test a discriminant within 1/1024 ulp of
the boundary, or nine trailing bits, and retry about once in a
thousand calls at double length. The single pass needs the worst-case
precision up front; in hardware at 16 and 24 bits it is found by
exhaustive simulation and lowered by adjusting stored coefficients
per subinterval, and it does not extend to double or to functions
whose argument reduction blocks exact rounding. Interval synthesis
takes an MPFR oracle, one rounding interval per input, an invertible
output compensation and an exact LP with counterexample-guided
refinement, and runs 1.3x to 2x faster than the float libraries and
CR-LIBM, which mis-round millions of fp32 log2 inputs.

Worst-case knowledge is the enabling asset: exhaustive search is
feasible for binary32 and below, binary64 needs the L or SLZ
algorithms with years of workstation time and yields full-range
bounds only for exp, ln, 2^x and log2 (binary64 exp needs 2^-113 for
|x| at least 2^-30 and ln 2^-118), trigonometric functions are
covered on intervals, and binary128 is out of reach. Directed modes
move the breakpoints to the numbers themselves, so nearest-only
designs use the midpoint distance alone; inputs near zero and exact
breakpoints such as log(1) are handled analytically.

The family is the contract layer above the evaluator families; the
retry form is variable-latency, the single pass fixed. It wins
wherever bit-reproducible results are required and loses to the 1-ulp
class families whenever the contract allows the loose profiles of
graphics, and wherever the format is wider than the searches.

The family is a methodology over another evaluator (single_pass_worst_case_precision is the precision choice of the evaluator it wraps, ziv_two_phase_retry recomputes at a higher precision when the first result is undecided, rlibm_interval_synthesis is a coefficient-synthesis method), so the library has no module for it and lists it as an exception (`sfu.SEQUENTIAL_SFU`).

## references

muller_2016 -> J.-M. Muller, "Elementary Functions: Algorithms and Implementation", 3rd ed., Birkhauser, 2016
muller_2018 -> J.-M. Muller, N. Brunie, F. de Dinechin, C.-P. Jeannerod, M. Joldes, V. Lefevre, G. Melquiond, N. Revol, S. Torres, "Handbook of Floating-Point Arithmetic", 2nd ed., Birkhauser, 2018
lefevre_2001 -> V. Lefevre, J.-M. Muller, "Worst Cases for Correct Rounding of the Elementary Functions in Double Precision", 15th IEEE Symposium on Computer Arithmetic (ARITH-15), pp. 111-118, 2001
dedinechin_2007 -> F. de Dinechin, C. Q. Lauter, J.-M. Muller, "Fast and Correctly Rounded Logarithms in Double-Precision", RAIRO Theoretical Informatics and Applications, vol. 41, no. 1, pp. 85-102, 2007
markstein_1990 -> Markstein, "Computation of Elementary Functions on the IBM RISC System/6000 Processor", IBM Journal of Research and Development, 1990
gal_1991 -> S. Gal, B. Bachelis, "An Accurate Elementary Mathematical Library for the IEEE Floating Point Standard", ACM Transactions on Mathematical Software, vol. 17, no. 1, pp. 26-45, 1991
schulte_1994 -> M. J. Schulte, E. E. Swartzlander, "Hardware Designs for Exactly Rounded Elementary Functions", IEEE Transactions on Computers, vol. 43, no. 8, pp. 964-973, 1994
lim_2021 -> J. P. Lim, M. Aanjaneya, J. Gustafson, S. Nagarakatte, "An Approach to Generate Correctly Rounded Math Libraries for New Floating Point Variants", Proceedings of the ACM on Programming Languages, vol. 5 (POPL), pp. 1-30, 2021
