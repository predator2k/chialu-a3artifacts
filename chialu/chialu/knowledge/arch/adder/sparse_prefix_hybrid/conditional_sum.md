---
family: sparse_prefix_hybrid
pin: {sum_block_style: conditional_sum}
---
# conditional_sum

The sum block precomputes both candidate sums of its bits, one for
carry-in 0 and one for carry-in 1, on a noncritical side path whose
conditional carries ripple inside the block, and the boundary carry
delivered by the sparse tree selects one of the two through a
multiplexer. The critical path is the carry tree plus one multiplexer;
the side path only has to finish before the tree carry arrives, so it
is built in static CMOS and can absorb high-threshold devices.

This is the sum block of the energy-delay-optimal sparse adders: the
Intel 1-in-4 trees use 4-bit static conditional-sum generators with
transmission-gate selection, the 64-bit sparse-2 designs in 90 nm and
the Ling variants use 2-bit blocks, and the POWER6 adder derives its
conditional sums inside the Kogge-Stone blocks. Sparseness moves the
carry-merge work off the critical path but increases output branching
and sum-precompute complexity, and the block depth must not exceed the
carry-path depth: static prefix-2 designs up to 64 bits keep at most
4-bit blocks, dynamic prefix-4 designs 2-bit or 4-bit blocks. A 57-bit
core in a floating-point multiply-accumulator precomputes conditional
carries as well as conditional sums, so its one-in-16 tree carry
selects the one-in-4 carries and those carries select the 4-bit sums.
Against carry_select it keeps the blocks short and the precompute
static; the side-path slack is what pays for the leakage reduction in
the dual-threshold designs. In the ADIR grammar it is `family:
sparse_prefix_hybrid` with `pin: {sum_block_style: conditional_sum}`.

## references

mathew2003 -> S. Mathew, M. Anders, R. K. Krishnamurthy, S. Borkar, "A 4-GHz 130-nm Address Generation Unit with 32-bit Sparse-Tree Adder Core", IEEE Journal of Solid-State Circuits, 2003.
wijeratne_2007 -> S. B. Wijeratne, et al., "A 9-GHz 65-nm Intel Pentium 4 Processor Integer Execution Unit", IEEE Journal of Solid-State Circuits, vol. 42, no. 1, pp. 26-37, 2007.
zeydel2010 -> B. R. Zeydel, D. Baran, V. G. Oklobdzija, "Energy-Efficient Design Methodologies: High-Performance VLSI Adders", IEEE Journal of Solid-State Circuits, vol. 45, no. 6, pp. 1220-1233, 2010.
zlatanovici2009 -> R. Zlatanovici, S. Kao, B. Nikolic, "Energy-Delay Optimization of 64-Bit Carry-Lookahead Adders With a 240 ps 90 nm CMOS Design Example", IEEE Journal of Solid-State Circuits, 2009.
yu_2006 -> X. Y. Yu, Y.-H. Chan, M. Kelly, E. Schwarz, B. Curran, B. Fleischer, "A 5GHz+ 128-bit Binary Floating-Point Adder for the POWER6 Processor", 32nd European Solid-State Circuits Conference (ESSCIRC), 2006
vangal_2006 -> S. Vangal, Y. Hoskote, N. Borkar, A. Alvandpour, "A 6.2-GFlops Floating-Point Multiply-Accumulator With Conditional Normalization", IEEE Journal of Solid-State Circuits, vol. 41, no. 10, 2006
