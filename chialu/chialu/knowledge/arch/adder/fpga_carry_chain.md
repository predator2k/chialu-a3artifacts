# fpga_carry_chain

Ripple-carry addition on the FPGA's dedicated carry logic: each logic
element forms propagate and sum in its LUT and hands the carry to its
neighbour over a dedicated fast carry line rather than the general
routing network (LUT, MUXCY and XORCY on Xilinx; dedicated full
adders inside the Altera ALM), so the chain runs at logic speed while
general-purpose routing costs 3 to 4 times a logic element delay.
Xilinx carry lines traverse vertically across CLBs; Altera chains
stay within one LAB, so wider additions incur inter-LAB routing
delay. The tunables are how the chain is segmented and pipelined and
how operands are packed onto it, since the carry topology is fixed by
the fabric.

Chain segment length trades chain latency against pipeline registers
and cluster boundaries: an adder of at most 16 bits stays inside one
Stratix-II LAB and 20 bits inside one Stratix-III/-IV LAB, and a
32-LE adder on Apex 20KE adds in about 5.0 ns but crosses a MegaLab
boundary at a 2.5 ns routing cost that a 16-bit adder inside one
MegaLab cuts to 1.0 ns. Overlaying a prefix structure on the chain
pays only at very large widths, because dedicated chains favour
ripple carry over lookahead and prefix structures everywhere else,
and a coarse-grained FPGA with a vendor fast-carry macro prefers
ripple for all but very large word lengths. Ternary packing uses the
shared arithmetic chain that lets one logic element add three
operands, and newer fabrics raise the arithmetic bits per logic
element from one to two or four.

The family wins against every LUT-built adder: a 32-bit hardened
ripple adder is 3.4 times faster than its LUT implementation, a
hardened carry-skip structure adds 20 percent more, and a modeled
Virtex-II Pro-like device gains 49.7 percent average frequency (128
against 85 MHz) across five floating-point benchmarks once the 57-bit
adder uses the chain. Commercial fabrics also harden carry-skip or
8-bit carry-lookahead granularity, which shifts the width at which
the chain alone is best. The chain loses only where a fine-grained
FPGA has no dedicated carry logic, where the architecture choice
returns to regularity, wiring and routability.

Portable HDL cannot tap the internal carries across vendors, so
non-arithmetic prefix functions with kill/propagate/generate
behaviour are mapped onto the chain by choosing addends that induce
the required carry transitions and recovering the outputs from the
sum bits, at about 3 to 4 times fewer LUTs than general-purpose
synthesis. Register controls of the logic element (synchronous clear,
synchronous load) absorb ALU functions without extra multiplexers.

## references

pasca_2011 -> B. Pasca, "High-Performance Floating-Point Computing on Reconfigurable Circuits", PhD thesis, ENS Lyon, 2011
zimmermann1997 -> R. Zimmermann, "Binary Adder Architectures for Cell-Based VLSI and their Synthesis", PhD thesis, Diss. ETH No. 12480, ETH Zurich, 1997.
boutros_2021 -> A. Boutros, V. Betz, "FPGA Architecture: Principles and Progression", IEEE Circuits and Systems Magazine, 2021
beauchamp_2008 -> M. J. Beauchamp, S. Hauck, K. D. Underwood, K. S. Hemmert, "Architectural Modifications to Enhance the Floating-Point Performance of FPGAs", IEEE Transactions on Very Large Scale Integration (VLSI) Systems, 2008
preusser2009 -> T. B. Preusser, R. G. Spallek, "Mapping Basic Prefix Computations to Fast Carry-Chain Structures", International Conference on Field Programmable Logic and Applications (FPL), 2009.
metzgen_2004 -> P. Metzgen, "A High Performance 32-bit ALU for Programmable Logic", Proc. ACM/SIGDA International Symposium on FPGAs, pp. 61-70, 2004
