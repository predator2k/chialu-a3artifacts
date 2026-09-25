# self_timed_variable_latency

Digit-recurrence division whose cycle count follows the data: a
self-timed ring of precharged stages
with completion detection starts each iteration as soon as the
previous residual is valid, speculation guesses each quotient digit
from a simplified selection function and checks it against a
conservative bound, rolling back or advancing partially when it fails,
early termination stops once the residual is zero or the quotient
width derived from leading-zero counts is exhausted, and clock gating
switches an idle divider off. The digit_select slot is the
quotient-digit selection table of the SRT recurrence underneath, which
may be shared between integer and floating-point operands.

The mechanism choice trades where the variable time comes from. The
self-timed ring removes the latches and the clock margin, about 30
percent of a latched ring's cycle, and lets adjacent stages overlap
through replicated carry-propagate branches, so a 54-bit divider
finishes in 45 to 160 ns depending on the data in 1.2 um CMOS; the
price is asynchronous design and test, dual-monotonic wiring, and a
ring of at least three stages to circulate data, spacer and bubble.
Speculation with partial advance reaches radix 512 at 1.17 cycles per
digit, 1.4 times faster than the fastest conventional radix-16 design
at 3.4 times the area of a radix-2 divider in 1 um CMOS, while
speculation without partial advance does not beat the conventional
design and every wrong guess costs a correction iteration. Early
termination costs almost nothing: the detection runs beside the
recurrence off the critical path, and the shared integer and
floating-point engine of the z990 runs 30 to 61 cycles for an integer
divide instead of its predecessors' fixed maximum.

shared_int_fp_datapath is what makes early termination pay, since
integer quotients are short and exact results common; the integer
operands are normalized first, and radix 2 needs an extra detector for
the exact negative residual that would otherwise emit an endless
string of -1 digits and a false Inexact flag. A reciprocal or quotient
cache is the survey's fifth route, about a two-times speedup when the
base divider is slow enough to make hits worthwhile.

The contract is exact IEEE division with an operand-dependent
latency: the surrounding system must accept variable completion and
control dependencies, the conservative bound check may reject a
correct speculation but never accepts an invalid residual, and early
termination marks an exact result by clearing Inexact. The gain of
every mechanism depends on the operand distribution, and the reported
figures assume uniform operands.

The family's defining structure is sequential (the cycle count follows the data), so the library has no combinational module for it; a seed that declares it stays behavioral and the family is listed as an exception in `chialu.targets.rtl.families.div.SEQUENTIAL_DIV`.

## references

williams_1991 -> Williams, Horowitz, "A Zero-Overhead Self-Timed 160-ns 54-b CMOS Divider", IEEE Journal of Solid-State Circuits, 1991
cortadella_1994 -> Cortadella, Lang, "High-Radix Division and Square-Root with Speculation", IEEE Transactions on Computers, 1994
gerwig_2004 -> G. Gerwig, H. Wetter, E. M. Schwarz, J. Haess, C. A. Krygowski, B. M. Fleischer, M. Kroener, "The IBM eServer z990 Floating-Point Unit", IBM Journal of Research and Development, 2004
kim_2025 -> Kim, Parry, Harris, Turek, Maiuolo, Thompson, Stine, "Shared Recurrence Floating-Point Divide/Sqrt and Integer Divide/Remainder With Early Termination", IEEE Transactions on Computers, 2025
oberman_1997 -> Oberman, Flynn, "Division Algorithms and Implementations", IEEE Transactions on Computers, 1997
