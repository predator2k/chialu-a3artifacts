---
family: restoring_nonrestoring
pin: {style: nonrestoring}
---
# nonrestoring

The divisor is added or subtracted at every quotient position and a
negative remainder is never restored: the divisor shifts and the next
operation is reversed, so each quotient digit costs one addition time,
one register disappears, and the quotient digits are non-zero signed
digits at every position. The final remainder, when wanted, needs a
correcting addition or subtraction, so the style is attractive when the
remainder is discarded.

Nonrestoring is the pick when the remainder is discarded or recovered
rarely: n addition times against 3/2 n for restoring. Freiman's
shift-over-zeros form normalizes the remainder into [0.5, 1.0) after
each add or subtract and emits s_j quotient bits per iteration, a
nominal average of 8/3 for the single multiple {1.0D} and 3.82 for
{0.75D, 1.0D, 1.5D}, whose quotient correction is simpler than that of
a nominally faster set. FPnew's merged iterative divider and square
root produces three mantissa bits per cycle in 19 kGE in 22FDX, and
PERI's posit DIV/SQRT runs one nonrestoring iteration per cycle.
Against nonperforming it keeps arithmetic at every step but carries
the remainder-correction circuit that the restoring cell arrangement
eliminates. In the ADIR grammar it is `family: restoring_nonrestoring`
with `pin: {style: nonrestoring}`.

## references

richards_1955 -> Richards, "Arithmetic Operations in Digital Computers", Van Nostrand, 1955
tocher_1958 -> Tocher, "Techniques of Multiplication and Division for Automatic Binary Computers", Quarterly Journal of Mechanics and Applied Mathematics, 1958
freiman_1961 -> Freiman, "Statistical Analysis of Certain Binary Division Algorithms", Proceedings of the IRE, 1961
mach_2020 -> S. Mach, F. Schuiki, F. Zaruba, L. Benini, "FPnew: An Open-Source Multi-Format Floating-Point Unit Architecture for Energy-Proportional Transprecision Computing", arXiv:2007.01530, 2020
tiwari_2021 -> S. Tiwari, N. Gala, C. Rebeiro, V. Kamakoti, "PERI: A Configurable Posit Enabled RISC-V Core", ACM Transactions on Architecture and Code Optimization, 2021
