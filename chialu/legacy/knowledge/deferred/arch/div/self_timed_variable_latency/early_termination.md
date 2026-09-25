---
family: self_timed_variable_latency
pin: {mechanism: early_termination}
---
# early_termination

Iteration count derived from the data: integer operands are
normalized, leading-zero counts give the effective quotient width, and
start and stop pointers make the shared SRT engine run only the
required radix-4 iterations. Iterations also stop on a zero carry-save
residual, a dividend smaller than the divisor, or a special case found
in preprocessing, and radix 2 adds a detector for the exact negative
residual that would otherwise emit endless -1 digits and a false
Inexact flag.

It is the pick for a shared integer and floating-point divider, where
small integer quotients and exact results are common: the z990 integer
divide runs 30 to 61 cycles, 25 to 56 pipelined, instead of the fixed
maximum of its predecessors, and the detection logic runs beside the
recurrence off the critical path for a few hundred to about a thousand
square micrometres in 28 nm. Its gain depends on the operand
distribution, which also limits the self_timed repeating-remainder
check, and it needs no asynchronous design and no speculation
hardware; an idle divider can be clock-gated on top of it, and
subnormal inputs could shorten the loop further but are not exploited.

## references

gerwig_2004 -> G. Gerwig, H. Wetter, E. M. Schwarz, J. Haess, C. A. Krygowski, B. M. Fleischer, M. Kroener, "The IBM eServer z990 Floating-Point Unit", IBM Journal of Research and Development, 2004
kim_2025 -> Kim, Parry, Harris, Turek, Maiuolo, Thompson, Stine, "Shared Recurrence Floating-Point Divide/Sqrt and Integer Divide/Remainder With Early Termination", IEEE Transactions on Computers, 2025
oberman_1997 -> Oberman, Flynn, "Division Algorithms and Implementations", IEEE Transactions on Computers, 1997
