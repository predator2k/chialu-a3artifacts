---
family: hard_fp_dsp
pin: {subnormal_support: shared_adder_handler}
---
# shared_adder_handler

The block's subnormal-capable adder reconfigured as the multiplier's
normalization and rounding resource: it accepts the multiplier's
pre-rounding mantissa, the low product bits and a modified exponent,
and its left and right shifters, leading-zero counter,
guard/round/sticky update and rounding logic finish the subnormal
product. The configuration is set per DSP block, and the adder is
unavailable for add, accumulate, multiply-add and recursive modes
while it serves the multiplier.

The pick when subnormal products must be handled and the block area
cannot grow: the shared handler adds about 1 percent to the Arria 10
DSP in 20 nm, against about 4 percent for dedicated normalization and
rounding in both multiplier and adder, which may also lengthen the
final stage. It covers normal-times-normal and normal-times-subnormal
underflow. The cost is exclusivity, since a block in this
configuration multiplies or adds rather than both, so a multiply-add
chain that needs subnormals uses the dedicated sibling or accepts
flush-to-zero, which is the shipped contract.

The family's space is opened by no unit template; the variant is documented for the knowledge base alone.

## references

langhammer_2015 -> M. Langhammer, B. Pasca, "Floating-Point DSP Block Architecture for FPGAs", ACM/SIGDA International Symposium on Field-Programmable Gate Arrays (FPGA), 2015
