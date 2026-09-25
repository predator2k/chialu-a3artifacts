# binary_tree

Multi-operand reduction as a balanced tree of two-input carry-propagate adders: N inputs pass through ceil(log2 N) adder levels, each level completing a nonredundant sum before the next, so every intermediate is an ordinary value that can be stored, rounded, saturated or forwarded. The cpa slot fixes the adder family at every node; delay is log2 N adder delays and cost is N-1 adders.

The tree is the conventional baseline that merged and fused reductions are measured against: each product finishes in its own multiplier with its own carry-lookahead adder and an N-input adder tree combines the results, whereas a csa_tree keeps the intermediates redundant and pays one carry propagation at the root. It wins when the intermediates are architecturally visible or physically separated: PMADDWD adds adjacent product pairs into 32-bit results and a following PADDD completes the reduction against an accumulator, and an NPU tile reduces locally in a binary tree and daisy-chains int32 partials to the next tile. For exact integer dot products exactness is free and width and saturation are the only choices, so the tree costs nothing in accuracy.

Against linear_chain it spends the same N-1 adders for logarithmic rather than linear depth; against csa_tree it loses whenever only the root value matters, because the carry propagation at every level is wasted work.

## references

swartzlander_1980 -> Swartzlander, "Merged Arithmetic", IEEE Transactions on Computers, 1980
peleg1996 -> A. Peleg, U. Weiser, "MMX Technology Extension to the Intel Architecture", IEEE Micro, vol. 16, no. 4, pp. 42-50, 1996
boutros_2020 -> A. Boutros, E. Nurvitadhi, R. Ma, S. Gribok, Z. Zhao, J. C. Hoe, et al., "Beyond Peak Performance: Comparing the Real Performance of AI-Optimized FPGAs and GPUs", International Conference on Field-Programmable Technology (ICFPT), 2020
jouppi_2017 -> N. P. Jouppi, C. Young, N. Patil, D. Patterson, et al., "In-Datacenter Performance Analysis of a Tensor Processing Unit", ISCA, 2017
