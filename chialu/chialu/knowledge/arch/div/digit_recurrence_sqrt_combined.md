# digit_recurrence_sqrt_combined

Square root by digit recurrence: each iteration selects one signed
root digit from a truncated estimate of the residual, subtracts a
term formed from the partial root established so far (the unified
update R[i+1] = r R[i] - F[i] q[i+1] takes F[i] from the partial root
rather than from a fixed divisor), keeps the residual in carry-save
form, and appends the digit to positive and negative partial-root
words that an on-the-fly converter holds in non-redundant form.
Residual adder, digit selection, and converter have the same shape as
SRT division, so one unit serves both, and a high effective radix
comes from overlapping or cascading radix-4 or radix-8 sub-iterations
inside one cycle.

Radix buys bits per cycle with selection and speculation hardware.
Radix 2 adds square root to a divider for very little hardware, since
the root reuses the remainder subtractor, the invert/select logic, the
quotient registers, and a merged selection table. Radix 4 replaces
the table by a few comparisons of the top remainder bits, computes
every candidate remainder update before the digit is known, and
assimilates the leading residual bits so each critical path holds one
carry-propagate operation, at the price of a carry-save adder per
candidate. Radix 16 overlaps two radix-4
selections with the low digit speculated for every high-digit
outcome, and placing that speculation in a narrow selection path
rather than the wide residual path keeps the power down; adding
square root to such a division-only unit costs about 65 percent area
and 11 percent latency in 90 nm. Radix 64 is three overlapped radix-4
iterations for division with square root at radix 16, or two cascaded
radix-8 iterations serving both, where deriving the square-root
selection constants from the division constants plus a small offset
table cuts selection storage by about 60 percent. Very high radix
with speculation or with prescaling needs the square term retimed
into the next cycle or two cycles per root digit, so division keeps
its cycle time and square root runs slower.

Sharing pays when the unit covers at least double precision and
retires four or more bits per cycle, and loses at one to two bits per
cycle; extending the shared recurrence to integer divide and
remainder saves 9 to 18 percent area in 28 nm at four to eight bits
per cycle.
On-the-fly conversion can be dropped when the main FPU adder
assimilates the signed-digit root before rounding, and it extends to
producing the 3x partial-root multiple without an adder. Execution is
fixed iteration with precision-dependent latency, rounding comes from
the final remainder, and the unit runs outside the main pipeline so
independent instructions proceed; a fully pipelined organization
accepts one same-precision operation per cycle at about 2.5x the
iterative area. Digit recurrence is several times more
energy-efficient than FMA-based Newton-Raphson.

The seed instantiates the library's generated divider for this family
(`chialu/targets/rtl/families/div.py`: the shared SRT recurrence with a carry-save residual at radix 2, 4, 16 or 64 (radix 16 and 64 as radix-4 sub-stages, their selections speculated under `speculation_between_subiterations` or cascaded), the digit from the `digit_select` slot (the table, or comparators against its thresholds), the result on the fly or, without `on_the_fly_conversion`, as Q+ minus Q- (the square root then assimilates the partial root each stage for its subtrahend); as a square root the halved residual form w' = r w - s (S + s r^-(j+1) / 2) with the selection table generated and checked per stage index over the partial root's cells, the remainder of an unnormalized radicand recomputed from the de-scaled root). `python3 -m chialu.targets.rtl.families.div --width 32 --family <family> --pins k=v,...` emits it for a rewrite (`--sqrt` for the square root).

## references

burgess_2007 -> N. Burgess, C. N. Hinds, "Design of the ARM VFP11 Divide and Square Root Synthesisable Macrocell", Proc. 18th IEEE Symposium on Computer Arithmetic (ARITH-18), pp. 87-96, 2007.
richards_1955 -> Richards, "Arithmetic Operations in Digital Computers", Van Nostrand, 1955
bruguera_2023 -> Bruguera, "Radix-64 Floating-Point Division and Square Root: Iterative and Pipelined Units", IEEE Transactions on Computers, 2023
liu_2012 -> Liu, Nannarelli, "Power Efficient Division and Square Root Unit", IEEE Transactions on Computers, 2012
cortadella_1994 -> Cortadella, Lang, "High-Radix Division and Square-Root with Speculation", IEEE Transactions on Computers, 1994
lang_1999 -> Lang, Montuschi, "Very High Radix Square Root with Prescaling and Rounding and a Combined Division/Square Root Unit", IEEE Transactions on Computers, 1999
kim_2025 -> Kim, Parry, Harris, Turek, Maiuolo, Thompson, Stine, "Shared Recurrence Floating-Point Divide/Sqrt and Integer Divide/Remainder With Early Termination", IEEE Transactions on Computers, 2025
gerwig_2004 -> G. Gerwig, H. Wetter, E. M. Schwarz, J. Haess, C. A. Krygowski, B. M. Fleischer, M. Kroener, "The IBM eServer z990 Floating-Point Unit", IBM Journal of Research and Development, 2004
