# restoring_nonrestoring

Shift-and-subtract division with a full comparison per quotient bit.
Each step shifts the partial remainder left, subtracts the divisor with
a carry-propagate adder, and reads the sign: restoring accepts a
nonnegative result as quotient bit 1 and adds the divisor back after a
negative one; nonperforming compares first and selects either the
difference or the shifted old remainder through a multiplexer, so no
restoring addition exists; nonrestoring keeps the negative remainder,
emits a signed digit, and reverses the next operation, at the price of
a final remainder correction. Unrolling k steps, or trying 1x, 2x, and
3x in parallel subtractors, retires more than one bit per cycle.

The style choice trades a register and a correction against operation
count. Restoring costs n trial subtractions plus an average of n/2
corrections, which is 3n/2 addition times in abstract units, while
nonrestoring and nonperforming cost one addition time per quotient
digit; under lock-step scheduling true restoring needs twice the
clocks of nonperforming. Nonperforming reaches that rate with a
multiplexer instead of a signed digit, so the exact cell is slightly
simpler and lower in power than the nonrestoring cell, which carries a
remainder-correction circuit. Nonrestoring is attractive when the
remainder is discarded; recovering it needs a further addition or
subtraction, and rounding in any direction other than downward needs a
final correction. Restoring backtracking is simple in radix 2 and
undesirable at higher radices because it recomputes. The residual
adder sits on the critical path, so production units use lookahead
carries, and an end-around-borrow lets quotient selection start before
the residual sign settles.

Bits per cycle trades area and cycle time against cycle count.
Replicating the restoring step from one to eight bits per cycle at 64
bits grows area from 2.44 to 8.79 k um^2 and delay from 0.18 to 1.10 ns
in TSMC 28HPC+, so the product barely moves. Shifting over zeros
normalizes the remainder into [0.5, 1) every iteration and emits a
variable number of quotient bits: about 8/3 per iteration for the plain
divisor and about 4 with a set of two or three easy multiples such as
0.75D, 1.0D, and 1.5D, but latency becomes data-dependent, multiple
sets need a quotient correction, and practical sets stop at two or
three multiples.

The family is fixed-iteration, exact, and the baseline the space's
other dividers are measured against: it is chosen where area matters
and latency is tolerable, for extended-precision operands next to a
Goldschmidt path for short ones, and for merged division/square root
in small FPUs. It loses to multiplicative iteration wherever a
multiplier exists and latency counts, and the exact contract
X = YQ + R holds only until approximate subtractor cells are
substituted.

The seed instantiates the library's generated divider for this family
(`chialu/targets/rtl/families/div.py`: the shift-and-subtract array (restoring, nonperforming or nonrestoring by `style`), one quotient bit per stage through the `residual_adder` family; as a square root the restoring recurrence, one root bit per stage from the trial subtraction of 4 R + 1 through the same adder family). `python3 -m chialu.targets.rtl.families.div --width 32 --family <family> --pins k=v,...` emits it for a rewrite (`--sqrt` for the square root).

## references

tocher_1958 -> Tocher, "Techniques of Multiplication and Division for Automatic Binary Computers", Quarterly Journal of Mechanics and Applied Mathematics, 1958
freiman_1961 -> Freiman, "Statistical Analysis of Certain Binary Division Algorithms", Proceedings of the IRE, 1961
davis_1969 -> R. L. Davis, "The ILLIAC IV Processing Element", IEEE Transactions on Computers, vol. C-18, no. 9, pp. 800-816, 1969
kim_2025 -> Kim, Parry, Harris, Turek, Maiuolo, Thompson, Stine, "Shared Recurrence Floating-Point Divide/Sqrt and Integer Divide/Remainder With Early Termination", IEEE Transactions on Computers, 2025
chen2016 -> L. Chen, J. Han, W. Liu, F. Lombardi, "On the Design of Approximate Restoring Dividers for Error-Tolerant Applications", IEEE Transactions on Computers, vol. 65, no. 8, pp. 2522-2533, 2016
schwarz_1999 -> E. M. Schwarz and C. A. Krygowski, "The S/390 G5 Floating-Point Unit", IBM Journal of Research and Development, 1999
mach_2020 -> S. Mach, F. Schuiki, F. Zaruba, L. Benini, "FPnew: An Open-Source Multi-Format Floating-Point Unit Architecture for Energy-Proportional Transprecision Computing", arXiv:2007.01530, 2020
muller_2018 -> J.-M. Muller, N. Brunie, F. de Dinechin, C.-P. Jeannerod, M. Joldes, V. Lefevre, G. Melquiond, N. Revol, S. Torres, "Handbook of Floating-Point Arithmetic", 2nd ed., Birkhauser, 2018
