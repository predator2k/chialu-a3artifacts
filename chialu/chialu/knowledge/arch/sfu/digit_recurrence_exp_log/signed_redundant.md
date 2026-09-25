---
family: digit_recurrence_exp_log
pin: {digit_set: signed_redundant}
---
# signed_redundant

The redundant form of the recurrence: digits come from a symmetric
signed set, -1/0/1 at radix 2 or -10 to 10 at radix 16, the residual is
held in signed-digit or carry-save form so each step's addition carries
no propagation and its time is independent of precision, and the digit
is selected from a four-digit prefix of the scaled residual because the
selection regions overlap. The exponential iteration starts at n=1 and
the logarithm's first selector needs only two fractional digits.

This is the pick whenever the step time matters, since the restoring
sibling compares the full word at every step, and it is the form of
every high-radix and BKM unit, where a constant-time step is what makes
radix 16 or 128 pay. The cost is the selection logic and the constants:
a signed-digit selector reads a four-digit prefix or an eight-bit
direct table, and BKM stores 8p constants for p bits against CORDIC's
p. Selection by rounding is the natural selector for this digit set,
and the redundant residual must be converted once at the end.

The library's module for digit_recurrence_exp_log realizes this variant by its pin (`chialu/targets/rtl/families/sfu.py`).

## references

muller_2016 -> J.-M. Muller, "Elementary Functions: Algorithms and Implementation", 3rd ed., Birkhauser, 2016
bajard_1994 -> J.-C. Bajard, S. Kla, J.-M. Muller, "BKM: A New Hardware Algorithm for Complex Elementary Functions", IEEE Transactions on Computers, vol. 43, no. 8, pp. 955-963, 1994
ercegovac_1973 -> M. D. Ercegovac, "Radix-16 Evaluation of Certain Elementary Functions", IEEE Transactions on Computers, vol. C-22, no. 6, pp. 561-566, 1973
pineiro_2004 -> J.-A. Pineiro, M. D. Ercegovac, J. D. Bruguera, "Algorithm and Architecture for Logarithm, Exponential, and Powering Computation", IEEE Transactions on Computers, vol. 53, no. 9, pp. 1085-1096, 2004
