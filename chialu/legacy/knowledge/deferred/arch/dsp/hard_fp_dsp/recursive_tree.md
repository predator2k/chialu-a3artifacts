---
family: hard_fp_dsp
pin: {chain_topology: recursive_tree}
---
# recursive_tree

Adjacent DSP blocks take multiplier or adder roles and pass
floating-point results over the dedicated inter-block connections, so
a vector reduction is composed as a tree of blocks without
general-purpose routing at each level. The multiplier contributes two
or three cycles, the first adder level one cycle and each later level
three cycles; optional balanced logic-register depths accommodate
longer physical routes.

The pick when many products must be summed at the block's frequency
rather than accumulated serially: a 256-element reduction resolves in
24 cycles on the 20 nm production FPGA, which the paper reports as
3 log2 of the vector length. The linear accumulate sibling feeds the
adder back on itself and holds one running sum per block, so it costs
no extra blocks and serializes the reduction. The tree consumes one
block per node, and a large tree may need logic-based registers where
routing distance lowers frequency.

The family's space is opened by no unit template; the variant is documented for the knowledge base alone.

## references

langhammer_2015b -> M. Langhammer, B. Pasca, "Design and Implementation of an Embedded FPGA Floating Point DSP Block", 22nd IEEE Symposium on Computer Arithmetic (ARITH), 2015
