---
family: approximate_functional
pin: {method: truncated_reciprocal_multiply}
---
# truncated_reciprocal_multiply

TruncApp: leading-one positions normalize the dividend and divisor, a
truncation unit keeps t bits of each, and the divisor reciprocal is
approximated by inverting the retained fraction bits and prepending a
leading 1, with no reciprocal table. A t-bit multiplier forms the
product with the truncated dividend, a shift restores the exponent
difference kA-kB, and sign units serve signed operands. TruncApp_AM
replaces the exact multiplier with one that omits selected partial
products.

The truncation length t sets accuracy: the maximum relative error
stays at 12.5% for every evaluated 32-bit configuration, while mean
absolute error falls from about 10% at t=3 to about 4% at t=4, nearly
independent of operand width. Beyond t=4 more than half of the
outputs err high, so the partial-product-omitting multiplier lowers
the mean error. It is the pick when a multiplier-based single-cycle
divider must beat SEERAD on area and energy at equal or better mean
error, which it does by about two thirds against level 3, and when
the same-sign error ceiling of logarithmic division is acceptable;
bias-corrected logarithmic and dynamic-segment methods win when the
error bias or the worst case must be small.

## references

vahdat2017b -> S. Vahdat, M. Kamal, A. Afzali-Kusha, M. Pedram, Z. Navabi, "TruncApp: A Truncation-Based Approximate Divider for Energy Efficient DSP Applications", Design, Automation and Test in Europe (DATE), pp. 1635-1638, 2017
