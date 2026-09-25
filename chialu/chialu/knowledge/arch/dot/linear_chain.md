# linear_chain

Sequential multi-operand reduction: operands enter one adder in order and each partial sum becomes the next operand, so hardware is one adder row (or one carry-save row plus a register) and delay grows linearly with the operand count. The chain is the accumulator form of reduction; it spreads across time what a tree spreads across space.

The chain wins where operands arrive one per cycle and area or clock period dominate: a Double MAC unit updates two accumulations from a shared activation exactly, a block-floating-point vector is aligned once and then accumulated in fixed point with one final normalization, and the POWER6 and z10 decimal multipliers generate one easy multiple per cycle and add it into a running sum, interleaving multiple generation with accumulation so no extra iteration latency appears. In a combinational linear array of binary carry-save adders the critical path is the m-1 correction multiplexers; speculating that the first one or two additions need no correction removes most of them and leaves a final correction independent of m, which suits iterative designs with variable operand counts.

Against csa_tree the chain loses on latency whenever all operands are present at once; against binary_tree it uses the same number of two-input adders with linear rather than logarithmic depth. Its loop-carried add is the thing to keep short: a carry-save row in the loop and one CPA at the end recover most of the tree's speed at chain area.

## references

lee_2019 -> S. Lee, D. Kim, D. Nguyen, J. Lee, "Double MAC on a DSP: Boosting the Performance of Convolutional Neural Networks on FPGAs", IEEE Transactions on Computer-Aided Design of Integrated Circuits and Systems, 2019
kenney_2005 -> Kenney, Schulte, "High-Speed Multioperand Decimal Adders", IEEE Transactions on Computers, 2005
eisen_2007 -> Eisen, Ward, Tast, Mading, Leenstra, Mueller, Granito, Prasad, Whitcomb, Mansfield, "IBM POWER6 accelerators: VMX and DFU", IBM Journal of Research and Development, 2007
schwarz_2009 -> Schwarz, Kapernick, Cowlishaw, "Decimal Floating-Point Support on the IBM System z10 Processor", IBM Journal of Research and Development, 2009
