# csa_tree

Carry-save reduction of N operands to a sum/carry pair in O(log N) compressor levels with a single carry-propagate adder at the root; the compressor choice (3:2 counter, 4:2 compressor, 7:3 counter) sets levels per operand and wiring, and the final_cpa slot fixes the one carry propagation. Inputs may arrive already redundant (multiplier sum/carry pairs), so products, aligned addends and an accumulator merge without intermediate assimilation.

The compressor trades depth against cell complexity: 4:2 compressors give a binary tree with log4 levels and a carry-out independent of carry-in, and they outperform 3:2 counter trees in delay as operand size grows at a small area overhead; 7:3 counters remove more bits per cell at the cost of denser wiring. The root CPA is where cancellation, sign and rounding are resolved, so fused designs place work around it: duplicated trees form opposite-sign candidate pairs so a comparison picks the positive one, sorting products by exponent and reserving adder regions keeps the internal adder narrower than the exponent range, and an LZA over the redundant pair predicts the normalization shift before the CPA completes. In lane-partitioned MACs the tree feeds one wide final adder with boundary carries killed. Decimal trees reuse the structure on digit codes that make binary 3:2 cells valid decimal reducers.

csa_tree is the pick whenever only the final value is needed and the terms are plentiful, since reduction depth and the wide CPA are two of the three serial links of a fused datapath. binary_tree wins when intermediates must be visible, and linear_chain when operands arrive over time into a loop-carried accumulator. A pipelined tree with carry-save registers between levels keeps the same structure.

## references

sohn_2016 -> J. Sohn, E. E. Swartzlander, "A Fused Floating-Point Four-Term Dot Product Unit", IEEE TCAS-I, vol. 63, no. 3, pp. 370-378, 2016
tao_2013 -> T. Yao, D. Gao, X. Fan, J. Nurmi, "Correctly Rounded Architectures for Floating-Point Multi-Operand Addition and Dot-Product Computation", IEEE ASAP, pp. 346-355, 2013
danysh_2005 -> A. Danysh, D. Tan, "Architecture and Implementation of a Vector/SIMD Multiply-Accumulate Unit", IEEE Transactions on Computers, vol. 54, no. 3, pp. 284-293, 2005
castellanos_2008 -> Castellanos, Stine, "Compressor Trees for Decimal Partial Product Reduction", 18th ACM Great Lakes Symposium on VLSI (GLSVLSI), 2008
kenney_2005 -> Kenney, Schulte, "High-Speed Multioperand Decimal Adders", IEEE Transactions on Computers, 2005
vazquez_2010 -> Vazquez, Antelo, Montuschi, "Improved Design of High-Performance Parallel Decimal Multipliers", IEEE Transactions on Computers, 2010
