---
family: compound_flagged_prefix
pin: {topology: kogge_stone}
---
# kogge_stone

The compound or flagged prefix adder built on a Kogge-Stone carry
tree: the minimum-depth prefix network whose output cells, turned into
black cells, deliver the flags for sum, sum+1 and sum+2 at every
position. The reported instances are a split Kogge-Stone network whose
prefix boundaries align with the fixed-point and floating-point modes
of an FPGA DSP block, and a log2(4p-1)-level tree, 63 bits for
Decimal64, whose secondary carry set yields S+2 for decimal rounding.

Kogge-Stone is the pick when the compound adder sits on the rounding
critical path and its wiring is affordable. A single-precision fused
multiply-add chose it for the main adder and for the separate carry
generation adder to avoid fanout problems, the carry-only adder produces
the carry-out from which the result multiplexer's select signals are
derived. In the flagged prefix
comparison it costs more transistors than Ladner-Fischer at both 16
and 64 bits, 1,088 against 928 and 5,632 against 4,352 for the full
cell, while keeping the same one-XOR-plus-buffer overhead over its
plain form. The FPGA block splits the network into two prefix modules
so that two independent fixed-point multipliers keep their modes, and
a carry-select network spans the low, middle and high adder groups for
wider fixed-point products, all for about 3% extra logic on a 20 nm
Arria 10.

## references

langhammer_2015b -> M. Langhammer, B. Pasca, "Design and Implementation of an Embedded FPGA Floating Point DSP Block", 22nd IEEE Symposium on Computer Arithmetic (ARITH), 2015
vazquez_2009 -> Vazquez, Antelo, "A High-Performance Significand BCD Adder with IEEE 754-2008 Decimal Rounding", 19th IEEE Symposium on Computer Arithmetic (ARITH-19), 2009
burgess2002 -> N. Burgess, "The Flagged Prefix Adder and its Applications in Integer Arithmetic", Journal of VLSI Signal Processing, vol. 31, no. 3, pp. 263-271, 2002.
oh_2006 -> H.-J. Oh et al., "A Fully Pipelined Single-Precision Floating-Point Unit in the Synergistic Processor Element of a CELL Processor", IEEE Journal of Solid-State Circuits, vol. 41, no. 4, 2006
