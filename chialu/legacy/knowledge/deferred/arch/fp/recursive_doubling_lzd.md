# recursive_doubling_lzd

A modular leading-zero detector built by recursive doubling from 2-bit blocks: each block reports a valid flag (a one is present) and a one-bit position, and each level merges two neighbours into a block of twice the width with one more position bit and a combined flag, so the count and its validity emerge after log2(n) levels. The algorithmic tree beat logic synthesis, at under 200 ps for 64 bits in ECL.

tree_radix 4 merges four blocks per level for fewer levels at wider cells; the origin anticipator used four-bit initial groups because its cell is more complex than a carry cell. output_form decides whether the tree emits a binary count or one-hot shift controls that drive the normalizer stages directly and skip the binary-count round trip. valid_flag_propagation carries the all-zero indication up the tree, which a zero-result detect and a saturating shift need. Against prefix_lzc the detector is fixed in shape and cheap to reason about; the prefix form is the pick when the counter must follow a prefix topology or an energy target.

As the encoder of an anticipator the detector consumes the indicator string whose first set bit marks the leading digit, and as the counter of a post-add scheme it reads the sum directly; in both roles the count plus valid flag is what the normalizer, its subnormal clamp and the zero-result test consume, so the flag output is rarely omitted. The origin anticipator ORed and encoded its group states for a partial-decode shifter, which is the one-hot output form in a coarse/fine split.

## references

oklobdzija_1994 -> V. G. Oklobdzija, "An Algorithmic and Novel Design of a Leading Zero Detector Circuit: Comparison with Logic Synthesis", IEEE Transactions on VLSI Systems, 1994
schmookler_2001 -> M. S. Schmookler and K. J. Nowka, "Leading Zero Anticipation and Detection - A Comparison of Methods", 15th IEEE Symposium on Computer Arithmetic, 2001
hokenek_cook_1990 -> E. Hokenek, R. K. Montoye, P. W. Cook, "Second-Generation RISC Floating Point with Multiply-Add Fused", IEEE Journal of Solid-State Circuits, vol. 25, no. 5, pp. 1207-1213, 1990
