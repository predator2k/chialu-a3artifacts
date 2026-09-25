---
family: embedded_fpu_block
pin: {composition: multiply_add_block}
---
# multiply_add_block

One coarse-grained fp64 block that performs multiplication, addition
or the fused operation X = (A x B) + C through a single set of ports,
with optional registered inputs and outputs. The block sits in
dedicated columns between the CLB and RAM columns, horizontal routing
crosses it and vertical routing stays at its periphery, and its height
in CLBs is a modeled parameter.

This is the pick when the kernel is dominated by fp64 multiply-add and
the block's fixed silicon is acceptable: over five fp64 benchmarks the
block cuts area by about half and raises the clock rate by a third or
more against an embedded-multiplier architecture on a modeled
Virtex-II Pro-like FPGA, with fewer routing tracks. It offers no
integer reuse, so non-floating-point designs waste the block area, and
it holds one operation per block where the linked sibling exposes its
components and the bus sibling chains several subblocks. The journal
form adds a configurable two-lane fp32 mode. Latency is modeled at
processor-like multi-cycle addition and multiplication.

The family's space is opened by no unit template; the variant is documented for the knowledge base alone.

## references

beauchamp_2006 -> M. J. Beauchamp, S. Hauck, K. D. Underwood, K. S. Hemmert, "Embedded Floating-Point Units in FPGAs", ACM/SIGDA International Symposium on Field-Programmable Gate Arrays (FPGA), 2006
beauchamp_2008 -> M. J. Beauchamp, S. Hauck, K. D. Underwood, K. S. Hemmert, "Architectural Modifications to Enhance the Floating-Point Performance of FPGAs", IEEE Transactions on Very Large Scale Integration (VLSI) Systems, 2008
