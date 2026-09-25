---
family: redundant_high_radix_cordic
pin: {residual_arithmetic: signed_digit}
---
# signed_digit

The recurrences hold x, y and the angle residual as binary signed
digits in -1/0/1, so each microrotation is a constant-time addition and
the direction is read from the first fractional digit of the scaled
residual, with a truncation error of at most a half. The residual's
sign may need many digits to settle, which the branching form exploits:
it inspects a three-digit prefix and, when the sign is uncertain, runs
both directions in parallel until a later evaluation keeps the valid
one.

This is the pick when negation must be exact and cheap, because a
signed-digit absolute value needs no deferred correction, which is why
the differential CORDIC prefers it over carry-save, and when the
directions are to stay in -1/+1 for a constant scale factor, which
branching achieves at the price of two conventional modules. The
carry-save sibling uses ordinary full-adder cells and is the choice of
the length-adjusting and radix-4 designs; both share the same
selection-by-prefix scheme and the same accuracy as conventional
CORDIC.

The library's module for redundant_high_radix_cordic realizes this variant by its pin (`chialu/targets/rtl/families/sfu.py`).

## references

muller_2016 -> J.-M. Muller, "Elementary Functions: Algorithms and Implementation", 3rd ed., Birkhauser, 2016
duprat_1993 -> J. Duprat, J.-M. Muller, "The CORDIC Algorithm: New Results for Fast VLSI Implementation", IEEE Transactions on Computers, vol. 42, no. 2, pp. 168-178, 1993
dawid_1996 -> H. Dawid, H. Meyr, "The Differential CORDIC Algorithm: Constant Scale Factor Redundant Implementation without Correcting Iterations", IEEE Transactions on Computers, vol. 45, no. 3, pp. 307-318, 1996
