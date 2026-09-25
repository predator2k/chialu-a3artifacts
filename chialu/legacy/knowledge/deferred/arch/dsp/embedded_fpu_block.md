# embedded_fpu_block

A standalone hard floating-point block in dedicated columns of an
island-style FPGA among the CLB and RAM columns: horizontal routing
crosses it and vertical routing stays at its edge. The Beauchamp block
computes an fp64 multiply, add or (A x B) + C with optional input and
output registers. The Chong block pairs a dual-precision multiplier,
53x53 or two 24x24, with a dual-precision adder over a configurable
link and exposes multiplier, adder, 64-bit right shifter and 54-bit
left shifter for integer use through configuration multiplexers. The
Ho unit chains registered multiplier and adder/subtractor subblocks
over unidirectional left-to-right bus multiplexers with feedback
registers.

The precision choice sets the block's width and mode set: one fp64
datapath, or one that also splits into two fp32 lanes; the Ho unit
fixes single or double precision at design time. The composition
choice is the structural difference between the three works: one
multiply-add block that runs multiply, add or multiply-add through the
same ports; a multiplier and an adder joined by a configurable link,
which is the cascade form of bridge_fma seen from the block level; or
several subblocks on a bus, where multiplier subblocks precede adder
subblocks so multiply-add needs no feedback register. Integer component
access pays configuration multiplexers and pins to expose the
significand multiplier, the adder and the two shifters to integer
circuits. The io_registers choice adds the registered boundary every
work pipelines through; feedback_registers, present only in the Ho
unit, carry outputs back to earlier subblocks for accumulation, and in
that unit subblock count, type, placement and buses are design-time
parameters while configuration bits select the datapath at run time.

The family wins on floating-point kernels otherwise built from CLBs
and embedded multipliers: the Beauchamp block cuts area by 55 percent
and raises speed by 40.7 percent on average against an
embedded-multiplier architecture over five fp64 benchmarks on a
modeled Virtex-II Pro-like FPGA, the Chong block improves fp64 area by
5.2x and delay by 5.8x over a Virtex-II model, and the Ho units cut
area by 25x on average against a conventional Virtex II. The cost is
fixed silicon that non-floating-point designs waste, a routing
interface enlarged to supply the block's many outputs, and mode
multiplexers on the linked and bus datapaths.

Against hard_fp_dsp the family is the earlier academic line: an FP
block of its own rather than an overlay on a fixed-point DSP block, so
it keeps fp64 and integer exposure and gives up the fixed-point modes
and cascades. The multiplier slot is the fp64 significand tree, where
the Chong dual-mode 53x53 tree is the prevention-constant variant of
booth_recoded_parallel; the adder and shifter slots hold the
significand adder and the exposed shifters. Execution is feed-forward.

No unit template opens `dsp_block_space`: the family describes the internal organization of an FPGA DSP slice, a fixed-function unit class of its own, so no seed declares it and the library has no module for it; the ALU, dot and SFU templates cover the slice's parts (multipliers, wide adders, SIMD lanes, dot arrays) through their own slots.

## references

beauchamp_2006 -> M. J. Beauchamp, S. Hauck, K. D. Underwood, K. S. Hemmert, "Embedded Floating-Point Units in FPGAs", ACM/SIGDA International Symposium on Field-Programmable Gate Arrays (FPGA), 2006
beauchamp_2008 -> M. J. Beauchamp, S. Hauck, K. D. Underwood, K. S. Hemmert, "Architectural Modifications to Enhance the Floating-Point Performance of FPGAs", IEEE Transactions on Very Large Scale Integration (VLSI) Systems, 2008
chong_2009 -> Y. J. Chong, S. Parameswaran, "Flexible Multi-Mode Embedded Floating-Point Unit for Field Programmable Gate Arrays", ACM/SIGDA International Symposium on Field-Programmable Gate Arrays (FPGA), 2009
ho_2009 -> C. H. Ho, C. W. Yu, P. H. W. Leong, W. Luk, S. J. E. Wilton, "Floating-Point FPGA: Architecture and Modeling", IEEE Transactions on Very Large Scale Integration (VLSI) Systems, 2009
