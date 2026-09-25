# hard_fp_dsp

IEEE floating point hardened inside the FPGA DSP block: a
single-precision multiplier is overlaid on the block's fixed-point
multiplier pipeline, where two 18x18 multipliers combine into one
27x27, reusing its compressor and carry-propagate structures, and a
separate malleable single-precision adder is fitted around the
multiplier logic. Dedicated chain connections between neighbouring
blocks compose multiplier/adder blocks into recursive reduction trees
without general-purpose routing at each tree level. The hardened mode
flushes subnormals to zero, emits no flags and offers a limited
rounding set, which holds the area increase to about 10 percent of the
block.

The fp_format choice selects which datapath the block exposes. The fp32
mode is the Arria 10 line's single-precision multiply-add, present on
Arria 10, Stratix 10 and Agilex. The half-precision mode of Agilex
accepts four binary16 multiplier inputs, forms two products and their
sum in a low-precision multiplier pair and adder, rounds each
correctly, and converts the sum to single precision before the
single-precision adder, so a sum of two products costs one block; the
bfloat16 modes are the same block with a different low-precision
format. The accumulate chain trades routing for latency: the first
reduction level adds one cycle and each later level three, a 256-input
tree resolving in 24 cycles, and a large tree may need logic-based
registers where routing distance lowers frequency. FMA is not
supported.

The constraints that shape the family are full fixed-point backward
compatibility, unchanged fixed-point performance, similar FP frequency,
a narrow physical aspect ratio and minimal area. Under them the
multiplier overlay costs about 3 percent of block logic and the
separate adder about 10 percent, about 15 percent combined before the
routing interface amortizes it to about 10 percent, and 0.5 to 5
percent of die area in the 20 nm Arria 10 depending on the block mix.
Subnormal support is the open cost: direct handling in both units is
about 4 percent of the arithmetic area and may lengthen the final
stage, while reconfiguring the adder as the multiplier's subnormal
handler costs about 1 percent but serves only one unit at a time. The
accuracy contract is correctly rounded products and sums with
flush-to-zero on inputs and outputs. The datapath is feed-forward.

No unit template opens `dsp_block_space`: the family describes the internal organization of an FPGA DSP slice, a fixed-function unit class of its own, so no seed declares it and the library has no module for it; the ALU, dot and SFU templates cover the slice's parts (multipliers, wide adders, SIMD lanes, dot arrays) through their own slots.

## references

langhammer_2015b -> M. Langhammer, B. Pasca, "Design and Implementation of an Embedded FPGA Floating Point DSP Block", 22nd IEEE Symposium on Computer Arithmetic (ARITH), 2015
boutros_2021 -> A. Boutros, V. Betz, "FPGA Architecture: Principles and Progression", IEEE Circuits and Systems Magazine, 2021
pasca_2023 -> B. Pasca, M. Langhammer, "Extracting Low-Precision Floating-Point Adders from Embedded Hard FP DSP Blocks on FPGAs", 30th IEEE Symposium on Computer Arithmetic (ARITH), 2023
