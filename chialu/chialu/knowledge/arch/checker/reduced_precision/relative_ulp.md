---
family: reduced_precision
pin: {bound_type: relative_ulp}
---
# relative_ulp

A reduced-precision floating-point adder runs beside the primary
adder on the operands' most-significant bits: it keeps the full sign
and exponent, truncates the mantissa to m bits, and omits its rounder. An adjustment unit maps the two-bit difference
between the full result and the checker result to chk, chk+1, chk+2
or chk-1 before comparison, so the check tolerates differences in the
checker's last places, and the maximum undetected error is below
4 x 2^-m of the correct result.

The relative bound is the pick for floating-point addition where the
tolerated difference must scale with the result: widening the checker
mantissa cuts the undetected-error bound from 25.0% at 4 bits to
0.02% at 14 bits, while area overhead grows from 30% to 62% of a
32-bit primary adder and false positives from the larger checker grow
with it. Checking is suppressed for unlike-sign operands with an
exponent difference of zero or one, because cancellation makes the
truncated computation a poor predictor, and detection may run lazily
one cycle later when the result stays uncommitted. The checker only
detects, so correct_by_substitution is false, and chains of operations
can accumulate more error than one addition. Against absolute it adds
the adjustment unit and the check_valid gate in exchange for a bound
that follows the result. In the ADIR grammar it is
`family: reduced_precision` with `pin: {bound_type: relative_ulp}`.

The generated checker realizes this variant (`checker.bound_type: relative_ulp`): the product's bound at the result's own scale; a sum's bound stays at the larger operand's scale, because the replica's error is relative to the operands and a cancelled sum would alarm on a correct core.

## references

eibl_2009 -> P. J. Eibl, A. D. Cook, D. J. Sorin, "Reduced Precision Checking for a Floating Point Adder", Proc. DFT 2009, pp. 145-152, 2009
