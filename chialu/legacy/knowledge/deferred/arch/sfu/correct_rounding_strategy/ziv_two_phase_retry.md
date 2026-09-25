---
family: correct_rounding_strategy
pin: {strategy: ziv_two_phase_retry}
---
# ziv_two_phase_retry

Ziv's rounding test with a bounded second phase: a quick evaluation
carrying 60 to 80 bits, or 7 to 10 extra bits in the accurate-table
form, returns only when its confidence interval excludes every
rounding breakpoint; otherwise one accurate phase, sized from the
published hardest-to-round cases at 120 to 150 bits, recomputes and
rounds. Two phases suffice because the worst case is known; without
it the retry becomes multilevel and must assume hundreds of bits.

It is the pick for software libraries where the average must track
the non-rounded libm: the accurate phase runs in under 1% of calls
at about ten times the quick phase, so the double-precision
logarithm averages 339 cycles against 323 with a 4824-cycle worst
case against 8424 on a Pentium 4, all four rounding modes proven,
while a multilevel fallback with unknown worst cases reaches
hundreds of thousands of cycles. The accurate-table variants test a
discriminant within 1/1024 ulp, or nine trailing bits, and retry at
double length about once per thousand calls. The single pass wins in
hardware at short formats, and interval synthesis where the whole
format can be checked exhaustively.

The library's module for correct_rounding_strategy realizes this variant by its pin (`chialu/targets/rtl/families/sfu.py`).

## references

dedinechin_2007 -> F. de Dinechin, C. Q. Lauter, J.-M. Muller, "Fast and Correctly Rounded Logarithms in Double-Precision", RAIRO Theoretical Informatics and Applications, vol. 41, no. 1, pp. 85-102, 2007
muller_2018 -> J.-M. Muller, N. Brunie, F. de Dinechin, C.-P. Jeannerod, M. Joldes, V. Lefevre, G. Melquiond, N. Revol, S. Torres, "Handbook of Floating-Point Arithmetic", 2nd ed., Birkhauser, 2018
markstein_1990 -> Markstein, "Computation of Elementary Functions on the IBM RISC System/6000 Processor", IBM Journal of Research and Development, 1990
gal_1991 -> S. Gal, B. Bachelis, "An Accurate Elementary Mathematical Library for the IEEE Floating Point Standard", ACM Transactions on Mathematical Software, vol. 17, no. 1, pp. 26-45, 1991
