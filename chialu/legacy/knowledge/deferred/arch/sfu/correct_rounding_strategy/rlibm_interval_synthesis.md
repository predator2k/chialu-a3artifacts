---
family: correct_rounding_strategy
pin: {strategy: rlibm_interval_synthesis}
---
# rlibm_interval_synthesis

Polynomial synthesis from rounding intervals: an MPFR oracle gives
the correctly rounded result for every target input, each result
defines the interval of double values that round to it, range
reduction and the inverse of a monotonic output compensation map
those intervals to the reduced domain, and an exact rational LP
solver finds coefficients that satisfy every interval, with violating
inputs added as counterexamples until the evaluation in double
passes them all.

It is the pick when the target format is small enough to enumerate,
bfloat16, posit16, fp32 or posit32, and one fixed-precision
polynomial in double must be correct for every input without a
retry: the generated functions match the oracle on all inputs, run
about 1.3x to 2x faster than the float libraries and CR-LIBM, and
found glibc's float log2 wrong on about fourteen million inputs.
The degree, the range reduction and the compensation are developer
inputs, an infeasible LP means a higher degree or a different
reduction, and exhaustive validation of double remains open, so the
retry and worst-case-precision strategies keep the wide formats.

The library's module for correct_rounding_strategy realizes this variant by its pin (`chialu/targets/rtl/families/sfu.py`).

## references

lim_2021 -> J. P. Lim, M. Aanjaneya, J. Gustafson, S. Nagarakatte, "An Approach to Generate Correctly Rounded Math Libraries for New Floating Point Variants", Proceedings of the ACM on Programming Languages, vol. 5 (POPL), pp. 1-30, 2021
lim_2021b -> J. P. Lim, S. Nagarakatte, "High Performance Correctly Rounded Math Libraries for 32-bit Floating Point Representations", ACM SIGPLAN Conference on Programming Language Design and Implementation (PLDI), pp. 359-374, 2021
