---
family: streaming_accurate_accumulator
pin: {approach: compensated_two_sum}
---
# compensated_two_sum

Kahan's loop: each term Y_I is first added into a correction
accumulator S2, the tentative sum T = S + S2 is formed, the part lost
in that rounding is estimated as S2 = (S - T) + S2 with the
parentheses forcing S - T first, and S = T closes the step. The
difference S - T is usually exact because the sum is normalized before
it is rounded or truncated, so S2 carries the rounding error of the
last step into the next one.

Compensation is the pick when the adder is a standard normalizing
floating-point adder that cannot be changed and the terms are
accurate to nearly full machine precision, because straightforward
summation of N terms of similar magnitude can lose almost log10 N
significant decimals. Its condition is that sums be normalized before
rounding or truncation: the IBM 704/709/7090/7094/7040/7044/360
short-word arithmetic qualifies, while machines that discard precision
before normalizing, such as the IBM 650/1620, Univac 1107 and Control
Data 3600, do not. Kahan names double-precision accumulation as the
simplest and fastest prevention where available. The fixed-point
window removes normalization from the loop altogether and adds
exactly within its LSBA bound, and the refinement tree recovers the
correctly rounded sum of a block of terms rather than of a stream.

The library realizes this choice as a pin of the generated streaming_accurate_accumulator module (`chialu/targets/rtl/families/dot.py`); the family card names the construction.

## references

kahan_1965 -> W. Kahan, "Pracniques: Further Remarks on Reducing Truncation Errors", Communications of the ACM, vol. 8, no. 1, p. 40, 1965
muller_2018 -> J.-M. Muller, N. Brunie, F. de Dinechin, C.-P. Jeannerod, M. Joldes, V. Lefevre, G. Melquiond, N. Revol, S. Torres, "Handbook of Floating-Point Arithmetic", 2nd ed., Birkhauser, 2018
