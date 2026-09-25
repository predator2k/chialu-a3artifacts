---
family: self_timed_variable_latency
pin: {mechanism: speculation_rollback}
---
# speculation_rollback

High-radix division whose quotient digit is guessed rather than
selected: a simplified function (reduced-input table, reduced output
set or approximate arithmetic) speculates each digit and the
recurrence uses it at once; a conservative bound check on truncated
residual and divisor estimates accepts a full advance when the next
residual is valid, and a wrong guess triggers incremental digit
correction or a fixed partial advance of log2(p) bits. The check
overlaps the next speculation.

It is the pick when a very high radix is wanted without a full
selection table: radix 512 with a 6-bit partial advance averages 1.17
cycles per digit and 5.6 tau per quotient bit, 1.4 times faster than
the fastest conventional radix-16 design with two overlapped radix-4
stages, at 3.4 times the area of a conventional radix-2 divider in
1 um CMOS. Speculation without partial advance does not beat the
conventional design, a wrong speculation costs at least one correction
iteration, and the conservative check can reject a correct guess. The
results assume uniformly distributed operands and a system that
tolerates variable latency, which self_timed needs as well and
early_termination needs less.

## references

cortadella_1994 -> Cortadella, Lang, "High-Radix Division and Square-Root with Speculation", IEEE Transactions on Computers, 1994
oberman_1997 -> Oberman, Flynn, "Division Algorithms and Implementations", IEEE Transactions on Computers, 1997
