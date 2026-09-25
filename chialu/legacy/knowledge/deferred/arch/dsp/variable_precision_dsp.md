# variable_precision_dsp

A hard FPGA multiplier block whose array is fractured into several
native widths: the partial-product compressor tree of an 18x18 array
is split so two 9x9 regions can operate independently, border cells
are inverted for Baugh-Wooley signed multiplication, and the smaller
products share the input and output routing ports of the original
multiplier, so one block yields eight 9x9, four 18x18, or one 36x36
product in Stratix II and one 27x27, two 18x18, or four 9x9 in later
generations. A flexible adder tree sums two or four of the products,
and Stratix III and IV split the block into two largely independent
half-DSPs whose outputs cascade into a neighbouring accumulator.

The native-width set trades configurations against port pressure.
Every added width is a further compressor-tree split that must fit the
same routing interface, which is why the block's int9 and int4 modes
were added without changing that interface and why fracturing is most
economical when the smaller operations share the original ports.
Widths that do not match the workload waste the array: 5x5 and 8x8
products gain little from a 9x9 sub-array and a 32x32 product leaves
the 36x36 mode partly idle, while the 36x36 mode reduces the
sub-products of a double-precision significand multiplication even
though the vendor tool does not expose it stand-alone.

Fracture granularity trades independence against density. Splitting
the block into half-DSPs roughly doubles multiplier density but
benefits only applications that do not need independent outputs from
every multiplier; the adder-tree modes turn a half-DSP into a
two-product or four-product sum that feeds a cascaded accumulator.
The block is feed-forward and exact, and its case against soft logic
is area: a hard-block FIR on 40 nm Stratix IV is 8.5x more
area-efficient and about 2x faster than the soft-logic version, and
hard DSP blocks narrow the FPGA-to-ASIC area gap from about 40x to
28x at 90 nm. Fixed block placement can return the speed gain to the
routing, so the family wins on multiply-dense datapaths and loses to
soft logic only where operand widths are odd or the blocks sit far
from their sources.

No unit template opens `dsp_block_space`: the family describes the internal organization of an FPGA DSP slice, a fixed-function unit class of its own, so no seed declares it and the library has no module for it; the ALU, dot and SFU templates cover the slice's parts (multipliers, wide adders, SIMD lanes, dot arrays) through their own slots.

## references

pasca_2011 -> B. Pasca, "High-Performance Floating-Point Computing on Reconfigurable Circuits", PhD thesis, ENS Lyon, 2011
boutros_2021 -> A. Boutros, V. Betz, "FPGA Architecture: Principles and Progression", IEEE Circuits and Systems Magazine, 2021
