---
family: sparse_prefix_hybrid
pin: {tree_topology: kogge_stone}
---
# kogge_stone

The sparse carry tree is a Kogge-Stone network thinned to every
2^k-th output: it keeps the stage count and fanout-1 critical carries
of the dense tree but computes only the carries at the block
boundaries, so sparsity 2 halves the carry-structure gate count and
reduces wiring while preserving the four-stage domino or three-stage
compound-domino organisation. Sparseness cuts tree gates, wires and
input loading at the cost of output branching and sum-precompute
complexity.

Kogge-Stone is the pick for the sparse tree when depth is the
constraint and the tree is large or high-fanout, which is where
sparseness helps most; sparsity 4 can make a small radix-4 or
compound-domino tree slower and less energy-efficient. The 64-bit
radix-4 sparse-2 design in 90 nm runs at 240 ps at 1 V, about 7.7 FO4,
with delayed-precharge domino in the carry tree and static precompute
paths interleaved bit-slice by bit-slice. The POWER6 adder uses it at
two sparsities chosen by wire length, with the fanout-1 critical carry
replicated for the intermediate carries. Against han_carlson, which the
energy-delay comparison also classes as sparse, it holds the
high-performance end of the curve while Han-Carlson and the quaternary
tree consume less energy at lower-performance targets. In the ADIR
grammar it is `family: sparse_prefix_hybrid` with
`pin: {tree_topology: kogge_stone}`.

## references

zeydel2010 -> B. R. Zeydel, D. Baran, V. G. Oklobdzija, "Energy-Efficient Design Methodologies: High-Performance VLSI Adders", IEEE Journal of Solid-State Circuits, vol. 45, no. 6, pp. 1220-1233, 2010.
zlatanovici2009 -> R. Zlatanovici, S. Kao, B. Nikolic, "Energy-Delay Optimization of 64-Bit Carry-Lookahead Adders With a 240 ps 90 nm CMOS Design Example", IEEE Journal of Solid-State Circuits, 2009.
yu_2006 -> X. Y. Yu, Y.-H. Chan, M. Kelly, E. Schwarz, B. Curran, B. Fleischer, "A 5GHz+ 128-bit Binary Floating-Point Adder for the POWER6 Processor", 32nd European Solid-State Circuits Conference (ESSCIRC), 2006
oklobdzija2005 -> V. G. Oklobdzija, B. R. Zeydel, H. Q. Dao, S. Mathew, R. Krishnamurthy, "Comparison of High-Performance VLSI Adders in the Energy-Delay Space", IEEE Transactions on VLSI Systems, 2005.
