# prefix_comparator

Comparison as an MSB-first scan or a balanced tree over per-bit
(equal, less) pairs; the adder form with the sum path stripped is the
subtractor_comparator family, whose slot names the adder. Equality is the whole-word propagate of A - B, which is an XNOR
tree over the operand bits with no carry propagation, and magnitude is
the carry-out of A + not(B) + 1, so only the borrow portion of a
subtractor is built. The MSB-first
form XORs the operands into per-bit unequal flags, runs a prefix or
priority-encoder network that enables only the most significant unequal
position, and reads the operand bit at that position to decide which
operand is greater; a NOR over the flags gives equality. Radix sets how
many bits each prefix node groups, so the scan depth falls as the
logarithm of the width.

The function choice sets how much of the network exists. Equality alone
needs no carry network: the completion AND gate of an early carry
circuit reports equality while the parallel carry inhibitions stay
asserted, and on a parallel-prefix adder the flag is free because the
whole-word propagate already exists. Greater-or-equal is likewise free
from the subtraction carry-out, so the subtractor form is the right
structure wherever an adder is already present and the comparator can
share its prefix tree; its cost is that equality then needs a zero
detector or a second subtraction on top of the sign. Full ordering from
a standalone unit favours the MSB-first scan, which reports greater,
less, and equal from one pass.

The MSB-first scan trades transistors for depth and activity. Grouping
bits into four-bit partitions gives a delay of 4 + ceil(log16 N) +
ceil(log4 N) gate delays in an abstract CMOS gate model, and a 64-b unit
runs at 0.86 ns with about 4000 transistors in 0.15 um CMOS at 1.5 V.
Forcing every lower-significance output to zero after the first unequal
bit keeps fewer than 35% of the transistors active, but the first set
always switches and the larger transistor count raises leakage relative
to smaller comparators. Flattened comparison logic suits only short
inputs; multilevel lookahead in the priority encoder handles long ones,
and a two-stage half-cycle pipeline speeds a 64-b unit at the cost of
latch transistors. Dynamic realizations need the XOR outputs stable
before evaluation, so the XOR delay becomes setup time; the domino 64-b
design is 50% smaller in layout and uses 79% less power than its ANT
comparator baseline in 0.6 um CMOS.

The family is feed-forward and combinational; optional pipelining
raises throughput at the cost of power and latency. It loses to a
reused adder whenever the datapath already has one, and it wins as a
standalone wide comparator, where logarithmic depth and terminated
activity beat a full subtractor whose difference bits are discarded.

## references

abdel_hafeez2013 -> S. Abdel-Hafeez, A. Gordon-Ross, B. Parhami, "Scalable Digital CMOS Comparator Using a Parallel Prefix Tree", IEEE Transactions on VLSI Systems, vol. 21, no. 11, pp. 1989-1998, 2013.
gilchrist1955 -> B. Gilchrist, J. H. Pomerene, S. Y. Wong, "Fast Carry Logic for Digital Computers", IRE Transactions on Electronic Computers, vol. EC-4, pp. 133-136, 1955.
huang_wang2003 -> C.-H. Huang, J.-S. Wang, "High-Performance and Power-Efficient CMOS Comparators", IEEE Journal of Solid-State Circuits, vol. 38, no. 2, 2003.
richards_1955 -> Richards, "Arithmetic Operations in Digital Computers", Van Nostrand, 1955
zimmermann1997 -> R. Zimmermann, "Binary Adder Architectures for Cell-Based VLSI and their Synthesis", PhD thesis, Diss. ETH No. 12480, ETH Zurich, 1997.
