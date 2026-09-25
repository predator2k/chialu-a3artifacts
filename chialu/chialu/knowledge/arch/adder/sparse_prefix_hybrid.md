# sparse_prefix_hybrid

A parallel-prefix tree computes only every 2^k-th carry, and short sum
blocks between those boundaries produce the sums. The tree is an
ordinary prefix topology (Kogge-Stone, Han-Carlson, Sklansky, or a
mixed Knowles net) at the chosen valency, with its columns thinned to
one in 2^k, so the critical path is the prefix depth plus one select
multiplexer. Each sum block precomputes its sums for carry-in 0 and 1
by ripple or conditional-sum logic on a noncritical side path, and the
boundary carry selects between them. Sparsity halves the carry-tree
gates and wires per doubling of the spacing and lowers fanout, while
the sum blocks absorb the carries the tree no longer computes.

Sparsity trades the carry tree against the sum blocks. Each doubling of
the spacing halves the carry-tree gates, wires, and input loading,
while output branching and sum-block precompute logic grow; the trade
pays most on wide, high-fanout trees, and at sparsity 4 a small radix-4
or compound-domino tree can be slower and less energy-efficient than
its dense version. The sum block should never be deeper than the carry
path: static radix-2 designs up to 64 bits keep blocks at 4 bits or
less, dynamic radix-4 designs use 2- or 4-bit blocks, and a ripple side
path must finish before the final select.

The tree topology sets depth against wiring. The Intel 1-in-4 style
keeps the Kogge-Stone logic depth in an irregular radix-2 tree that
generates every fourth carry, cutting generate/propagate fanout by a
third to a half and the carry-merge wiring by about 80% against a full
Kogge-Stone; a 32-bit core of this kind runs at 152 ps in 1.2 V 130 nm
CMOS. At 64 bits the quaternary tree has one stage more than
Kogge-Stone, so its advantage shrinks. A spanning tree of four-bit
Manchester modules produces every eighth carry in three levels without
back-propagation and selects between eight-bit ripple sums. A 57-bit
core inside a floating-point multiply-accumulator thins its critical
tree to one carry in 16 and selects twice: that carry chooses between
conditional one-in-4 carries computed on a noncritical side path, and
those carries choose between 4-bit conditional sums, at 4200
transistors per core in 90 nm. Higher
valency shortens the tree; a 64-bit radix-4 sparse-2 domino design
reaches 240 ps, about 7.7 FO4, in 90 nm bulk CMOS. Where wire resources
differ across the floorplan, sparsity can vary by region, dense on short
wires and sparse on long ones.

The family is feed-forward and the production choice for 32- to 64-bit
adders because the side path is where energy is saved: the critical
tree can be domino while the sum blocks are static CMOS with
high-threshold devices, and the gate family (static, domino, compound
domino) moves the design along the energy-delay frontier. Ling
pseudo-carries fit the same scheme with modified select blocks and cut
delay further on 64-bit hybrids. Resetting boundary carries partitions
the tree into independent narrower additions for lower-precision lanes.
It loses to a dense prefix tree only where the tree is small or its
fanout already low.

## design choices

### sum_block_style

| member | what it selects |
| --- | --- |
| `carry_select` | the sum blocks between the sparse prefix nodes are carry-select. |
| `conditional_sum` | they are conditional-sum blocks. |
| `ripple_precompute` | they are ripple blocks precomputed for both carry-in values. |

### tree_topology

| member | what it selects |
| --- | --- |
| `sklansky` | the sparse tree is the minimum-depth doubling-fanout graph. |
| `kogge_stone` | it is the minimum-depth unit-fanout graph. |
| `han_carlson` | it is the Brent-Kung skeleton over a Kogge-Stone core. |
| `knowles_mixed` | it is the Knowles continuum's point. |

## references

mathew2003 -> S. Mathew, M. Anders, R. K. Krishnamurthy, S. Borkar, "A 4-GHz 130-nm Address Generation Unit with 32-bit Sparse-Tree Adder Core", IEEE Journal of Solid-State Circuits, 2003.
zlatanovici2009 -> R. Zlatanovici, S. Kao, B. Nikolic, "Energy-Delay Optimization of 64-Bit Carry-Lookahead Adders With a 240 ps 90 nm CMOS Design Example", IEEE Journal of Solid-State Circuits, 2009.
zeydel2010 -> B. R. Zeydel, D. Baran, V. G. Oklobdzija, "Energy-Efficient Design Methodologies: High-Performance VLSI Adders", IEEE Journal of Solid-State Circuits, vol. 45, no. 6, pp. 1220-1233, 2010.
oklobdzija2005 -> V. G. Oklobdzija, B. R. Zeydel, H. Q. Dao, S. Mathew, R. Krishnamurthy, "Comparison of High-Performance VLSI Adders in the Energy-Delay Space", IEEE Transactions on VLSI Systems, 2005.
lynch_swartzlander1992 -> T. W. Lynch, E. E. Swartzlander Jr., "A Spanning Tree Carry Lookahead Adder", IEEE Transactions on Computers, vol. 41, no. 8, pp. 931-939, 1992.
yu_2006 -> X. Y. Yu, Y.-H. Chan, M. Kelly, E. Schwarz, B. Curran, B. Fleischer, "A 5GHz+ 128-bit Binary Floating-Point Adder for the POWER6 Processor", 32nd European Solid-State Circuits Conference (ESSCIRC), 2006
dimitrakopoulos2005 -> G. Dimitrakopoulos, D. Nikolos, "High-Speed Parallel-Prefix VLSI Ling Adders", IEEE Transactions on Computers, 2005.
kaul_2012 -> H. Kaul, M. Anders, S. Mathew, S. Hsu, A. Agarwal, F. Sheikh, R. Krishnamurthy, S. Borkar, "A 1.45GHz 52-to-162GFLOPS/W Variable-Precision Floating-Point Fused Multiply-Add Unit with Certainty Tracking in 32nm CMOS", ISSCC Digest of Technical Papers, pp. 182-184, 2012.
vangal_2006 -> S. Vangal, Y. Hoskote, N. Borkar, A. Alvandpour, "A 6.2-GFlops Floating-Point Multiply-Accumulator With Conditional Normalization", IEEE Journal of Solid-State Circuits, vol. 41, no. 10, 2006
