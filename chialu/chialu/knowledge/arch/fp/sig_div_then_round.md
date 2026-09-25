# sig_div_then_round

Floating-point division as a wrapper around any significand divider:
the operands are normalized, the exponents are subtracted with a one-
digit adjustment for a significand quotient below 1, the significand
divider delivers the quotient together with enough information to
round correctly, and the rounding stage applies the ambient IEEE mode.
Digit recurrence keeps an exact quotient/remainder identity, so
exactness follows from a null remainder; functional iteration and
polynomial methods need a method-specific rounding proof, a final
precision of at least twice the target, or a remainder computed by
back-multiplication. Subnormal operands are normalized by the wrapper's norm_lzc and
norm_shifter slots.

The sig_div slot sets latency and hardware: digit recurrence takes p
iterations on integer-add hardware, a radix-4 SRT core retires two
quotient bits per cycle for 12 cycles single and 19 cycles double
precision in the 1988 R3010, and a shared radix-64 division/square-root
core reaches one operation per cycle when pipelined with 16% less area
than two 64-bit and two 32-bit iterative units and a 2.51% SpecFP2017
gain over radix-8. Functional iteration needs O(log p) iterations on a
multiplier, which one processor sizes at 76 x 76 bits for p = 64
without an FMA, and it can run as straight-line software of fused
multiply-adds, formally verified, in six parallel stages. A separate
divide/square-root block lets the adder and multiplier issue
concurrently during an iteration sequence; a divider that shares the
add unit's exponent path and rounding function needs the control unit
to schedule around the conflict.

The unit's rounder trades gates against integration with the quotient
form: a flagged prefix adder on a signed-digit quotient folds
complementation and signed round/sticky information into an adjustment
of 0.5 to 2 ulps before an optional one-bit left shift, in 18 gates of
rounding logic, whereas a preset one-third dividend injection adds no
execution time but biases right-shift cases slightly toward zero. The
contract is correct rounding in all IEEE modes with the inexact flag
from a nonzero remainder; a defective quotient-digit selection table
breaks it silently, and the published software workaround tests the
denominator and scales both operands exactly by 15/16 at less than
twice the in-line divide time. Execution is feed-forward around an
iterative core, so latency depends on the operand precision.

## references

muller_2018 -> J.-M. Muller, N. Brunie, F. de Dinechin, C.-P. Jeannerod, M. Joldes, V. Lefevre, G. Melquiond, N. Revol, S. Torres, "Handbook of Floating-Point Arithmetic", 2nd ed., Birkhauser, 2018
thornton_1970 -> J. E. Thornton, "Design of a Computer: The Control Data 6600", Scott, Foresman and Co., 1970
rowen_1988 -> C. Rowen, M. Johnson, P. Ries, "The MIPS R3010 Floating-Point Coprocessor", IEEE Micro, vol. 8, no. 3, pp. 53-62, 1988.
alpert_1993 -> D. Alpert, D. Avnon, "Architecture of the Pentium Microprocessor", IEEE Micro, vol. 13, no. 3, pp. 11-21, 1993.
coe_1995 -> Coe, Mathisen, Moler, Pratt, "Computational Aspects of the Pentium Affair", IEEE Computational Science and Engineering, 1995
harrison_2000 -> Harrison, "Formal Verification of IA-64 Division Algorithms", TPHOLs, LNCS 1869, 2000
burgess2005 -> N. Burgess, "Prenormalization Rounding in IEEE Floating-Point Operations Using a Flagged Prefix Adder", IEEE Transactions on VLSI Systems, 2005.
bruguera_2023 -> Bruguera, "Radix-64 Floating-Point Division and Square Root: Iterative and Pipelined Units", IEEE Transactions on Computers, 2023
