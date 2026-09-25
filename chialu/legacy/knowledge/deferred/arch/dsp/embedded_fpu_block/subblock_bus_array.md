---
family: embedded_fpu_block
pin: {composition: subblock_bus_array}
---
# subblock_bus_array

The Ho coarse-grained unit: registered floating-point multiplier and
adder/subtractor subblocks and wordblocks built from identically
configured bitblocks, joined by unidirectional left-to-right bus
multiplexers so each subblock takes inputs from the subblocks to its
left, with feedback registers that carry outputs back for accumulation
and right-to-left dependencies. Multiplier subblocks are placed before
adder subblocks so multiply-add needs no feedback register.

The pick when a datapath of several chained operators should live in
one block: subblock count, type, placement, buses and feedback
registers are design-time parameters synthesized from an HDL, and
configuration bits select the datapath at run time, so fifty FPUs of
one benchmark fit in sixteen units at a small fraction of the host
area. Against a conventional Virtex II the units cut area by 25x on
average and delay by several times, with the bus width following the
single or double precision chosen at design time. The cost is
fine-grained control logic outside the block and idle subblocks where
a kernel does not match the placed mix, a mismatch the multiply-add
sibling cannot have.

The family's space is opened by no unit template; the variant is documented for the knowledge base alone.

## references

ho_2009 -> C. H. Ho, C. W. Yu, P. H. W. Leong, W. Luk, S. J. E. Wilton, "Floating-Point FPGA: Architecture and Modeling", IEEE Transactions on Very Large Scale Integration (VLSI) Systems, 2009
