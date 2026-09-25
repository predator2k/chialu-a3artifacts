# manchester_carry_chain

Ripple carry at the transistor level: each bit derives generate,
propagate, and kill from its operands, and the carry runs along a
chain of pass devices, three transistors per bit, in which propagate
opens the series switch, kill grounds the carry-out, and generate
drives it. The chain is precharged (or predischarged to VSS) before
evaluation so only the fast transition crosses the series switches,
and a restoring buffer is inserted every few bits because unbuffered
pass-chain delay grows as about n^2 transit times with chain length.
A bypass transistor that conducts when every propagate in a segment
is true adds a variable carry-skip over the chain.

The segment length trades series-switch loading against buffer delay.
In abstract transit-time units a four-stage chain costs about 72 and
its double-inverter buffer about 30, so the buffer is a large share of
each block and shorter segments do not pay, while longer segments lose
level and speed through the series switches, which is why the
original junction-transistor chain restored the level after ten
stages. Circuit style decides what the chain is good at. Dynamic
chains supply precharged nodes and wired-OR fanin, which let a
distributed Manchester gate combine Ling group terms directly from the
operands, and predischarging to VSS removes the threshold drop of a
VDD precharge; the cost is that long precharged chains lose their
attraction at low supply voltage, and an MOS chain propagates a high
carry slowly unless it is precharged. Variable skip helps only the
all-propagate worst case, and the block-output element that merges
bypass and chain carry sets a further trade, since a NAND merges
faster than an inverter but restores more slowly.

The family is area-efficient for short chains and for non-critical
intermediate carries, and it loses to lookahead and prefix trees once
the critical path is a long series chain, whose delay needs
implementation-level simulation to compare reliably. Its main modern
use is as the node circuit of other families: four-bit chain modules
form the cells of a spanning-tree lookahead adder, eight-bit
predischarged chains feed the carry-select halves of a 64-b hybrid
adder in a 200 MHz dual-issue microprocessor, a distributed Manchester
gate builds the quadrant terms of a sub-nanosecond 0.5 um 64-b adder,
a bypassed Manchester chain resolves the 108-b product of a tree
multiplier, and a precharged chain run left-to-right serves as a
leading-zero anticipator. Execution is feed-forward and combinational.

## references

kilburn1959 -> T. Kilburn, D. B. G. Edwards, D. Aspinall, "Parallel Addition in Digital Computers: A New Fast 'Carry' Circuit", Proceedings of the IEE - Part B, vol. 106, pp. 464-466, 1959.
mead_conway1980 -> C. Mead, L. Conway, "Introduction to VLSI Systems", Addison-Wesley, 1980.
zimmermann1997 -> R. Zimmermann, "Binary Adder Architectures for Cell-Based VLSI and their Synthesis", PhD thesis, Diss. ETH No. 12480, ETH Zurich, 1997.
chan_schlag1990 -> P. K. Chan, M. D. F. Schlag, "Analysis and Design of CMOS Manchester Adders with Variable Carry-Skip", IEEE Transactions on Computers, vol. 39, no. 8, pp. 983-992, 1990.
dobberpuhl_1992 -> D. W. Dobberpuhl, et al., "A 200-MHz 64-b Dual-Issue CMOS Microprocessor", IEEE Journal of Solid-State Circuits, vol. 27, no. 11, pp. 1555-1567, 1992.
lynch_swartzlander1992 -> T. W. Lynch, E. E. Swartzlander Jr., "A Spanning Tree Carry Lookahead Adder", IEEE Transactions on Computers, vol. 41, no. 8, pp. 931-939, 1992.
naffziger1996 -> S. Naffziger, "A Sub-Nanosecond 0.5 um 64 b Adder Design", IEEE International Solid-State Circuits Conference (ISSCC), pp. 362-363, 1996.
schmookler_2001 -> M. S. Schmookler, K. J. Nowka, "Leading Zero Anticipation and Detection — A Comparison of Methods", Proc. ARITH-15, pp. 7-12, 2001
