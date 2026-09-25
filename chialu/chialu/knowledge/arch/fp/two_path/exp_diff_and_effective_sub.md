---
family: two_path
pin: {close_path_trigger: exp_diff_and_effective_sub}
---
# exp_diff_and_effective_sub

The textbook near/far partition: the near path takes only effective
subtraction with exponent difference at most one, the single case that
can cancel many leading bits, and the far path takes every addition and
every subtraction with a larger difference. The far path performs the
full alignment, adds or subtracts, and prenormalizes by at most two
bits with no leading-zero anticipator; the near path aligns by at most
one bit, subtracts, and runs the anticipator and the full normalization
shift.

This is the pick when the near path should be as small as possible: its
operands are exact after subtraction, so its rounding reduces to three
complex gates or disappears, and separate anticipators for the
difference-0 and difference-1 cases can start alongside operand
swapping and inversion. The far path carries all rounding for both
operation types, which a compound or flagged prefix adder absorbs. It
is the form in the AMD 3DNow! lanes, the DSP-block adder and the
two-cycle fp64 designs, and a concurrent correction of the one-position
anticipator error gives both paths equal delay. The Farmwald sibling
moves small-difference additions into the close path instead, to make
the far path a shared add-and-round stage.
A third condition narrows it further: the SPARC64 adder
sends an exponent-difference-1 subtraction to the close path only when
the larger operand's mantissa is below 1.5, which forces the
normalizing left shift, lands the guard bit on the LSB and removes that
path's rounding stage altogether.

## references

muller_2018 -> J.-M. Muller, N. Brunie, F. de Dinechin, C.-P. Jeannerod, M. Joldes, V. Lefevre, G. Melquiond, N. Revol, S. Torres, "Handbook of Floating-Point Arithmetic", 2nd ed., Birkhauser, 2018
schmookler_2001 -> M. S. Schmookler, K. J. Nowka, "Leading Zero Anticipation and Detection — A Comparison of Methods", Proc. ARITH-15, pp. 7-12, 2001
burgess2005 -> N. Burgess, "Prenormalization Rounding in IEEE Floating-Point Operations Using a Flagged Prefix Adder", IEEE Transactions on VLSI Systems, 2005.
oberman_favor_1999 -> S. Oberman, G. Favor, F. Weber, "AMD 3DNow! Technology: Architecture and Implementations", IEEE Micro, vol. 19, no. 2, pp. 37-48, 1999.
bruguera_1999 -> J. D. Bruguera and T. Lang, "Leading-One Prediction with Concurrent Position Correction", IEEE Transactions on Computers, 1999
naini_2001 -> A. Naini, A. Dhablania, W. James, D. Das Sarma, "1-GHz HAL SPARC64 Dual Floating Point Unit with RAS Features", ARITH-15, 2001
