---
family: digit_recurrence_exp_log
pin: {selection: rounding_of_scaled_residual}
---
# rounding_of_scaled_residual

Selection by rounding: the residual is scaled by r^n, truncated to a
few fractional digits, five binary or six carry-save digits at radix
16, and the next digit is the nearest integer to that truncated value.
No comparison constants and no selection table are needed, because the
shrinking convergence intervals are wide enough that the rounded
estimate always lands inside them once n is large enough.

This is the pick for any high-radix or redundant recurrence, since it
turns digit selection into a short adder and a rounding and is what
lets radix 16 through 128 iterate at constant step time. Its limit is
the first iterations: nearest-integer selection is valid from n=3, or
from n=2 on a restricted domain, so the first digit comes from a table,
a special correction step, or a start at n=2 with a smaller convergence
domain, and the powering units require radix at least 8 with a
two-digit residual truncation. The table-lookup sibling covers those
first steps and the low-radix selectors; a full-word comparison is the
restoring alternative that gives up the constant-time step.

For the real exponential core, the implemented [startup contract](contracts/convergent_start.md)
uses table selection at indices one and two, then this rounded selector
from index three. Signed radix 16 additionally executes a fixed first-index
bootstrap. These are live stages and thresholds, including with leading-bit
advancement; geometry that cannot activate index three is rejected.
The real logarithm follows its separate [product-floor startup contract](contracts/log_convergent_start.md):
table selection at indices one and two and a fixed signed radix-16
bootstrap, then rounded selection from index three.

The library's module for digit_recurrence_exp_log realizes this variant by its pin (`chialu/targets/rtl/families/sfu.py`).

## references

muller_2016 -> J.-M. Muller, "Elementary Functions: Algorithms and Implementation", 3rd ed., Birkhauser, 2016
ercegovac_1973 -> M. D. Ercegovac, "Radix-16 Evaluation of Certain Elementary Functions", IEEE Transactions on Computers, vol. C-22, no. 6, pp. 561-566, 1973
vazquez_2013 -> A. Vazquez, J. D. Bruguera, "Iterative Algorithm and Architecture for Exponential, Logarithm, Powering, and Root Extraction", IEEE Transactions on Computers, vol. 62, no. 9, pp. 1721-1731, 2013
bajard_1994 -> J.-C. Bajard, S. Kla, J.-M. Muller, "BKM: A New Hardware Algorithm for Complex Elementary Functions", IEEE Transactions on Computers, vol. 43, no. 8, pp. 955-963, 1994
