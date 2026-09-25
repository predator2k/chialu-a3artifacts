# pairwise_tree

Dot product as separate products followed by a reduction tree. Each
element pair is multiplied in its own multiplier, which resolves its
product to a nonredundant value through its own carry-propagate adder,
and the N products are then summed by an N-input adder tree; the
integer path opens both sub-spaces to search, the multiplier family for
the product terms and the accumulator shape for the tree. With
per-level truncation off, every product and every partial sum keeps
full width, so the result is the exact integer dot product; the
accumulator can be a linear chain, a balanced binary tree of
carry-propagate adders, or a carry-save tree with one final adder.

The two slots trade independently. The multiplier slot fixes the cost
of each product term, and the conventional reference point is a fast
Dadda multiplier per term, each with its own carry lookahead adder; the
accumulator slot fixes the tree, which for two terms is one wide
carry-lookahead adder and for eight terms a tree of them. Per-product
carry resolution is the work this family spends that merged forms
avoid, so it is the exact arithmetic baseline against which merged
arithmetic, which folds every product into one reduction, is measured.
Per-level truncation trades that exactness for narrower adders at each
tree level.

Grouping products into adjacent pairs keeps each instruction's tree
shallow and composes across instructions: the MMX PMADDWD forms four
signed 16x16 products and adds adjacent pairs into two 32-bit results
with a latency of 3 cycles at one initiation per cycle, and a following
packed add completes larger reductions because no three-operand MAC
exists. A 16-element dot product on the original Pentium runs in 12
cycles against 74 for optimized floating-point code, a 6x speedup, once
the loop is unrolled far enough to issue one SIMD multiply per cycle.

The family is feed-forward with II = 1 and an exact contract. It wins
where products must be exact and individually available, where the
multiplier and accumulator are chosen or reused separately, and where
pair sums feed a software accumulation; it loses area and delay to
merged reductions once the whole dot product is committed to hardware.

The seed instantiates the library's generated module for this family (`chialu/targets/rtl/families/dot.py`: one significand or integer product per element through the `mul` component, the products aligned into the exact accumulator frame and summed by the `accum` tree (a chain, a binary tree of library adders, or a carry-save tree with a library CPA at the root); `per_level_truncation` turns the tree into one whose nodes align their inputs to the larger exponent and truncate to a node window, which the module comment reports as no longer meeting the fused contract). `python3 -m chialu.targets.rtl.families.dot --fab <format> --fc <format> --fd <format> --n <elements> --family <family> --pins k=v,...` emits it for a rewrite.

## references

peleg1996 -> A. Peleg, U. Weiser, "MMX Technology Extension to the Intel Architecture", IEEE Micro, vol. 16, no. 4, pp. 42-50, 1996
swartzlander_1980 -> Swartzlander, "Merged Arithmetic", IEEE Transactions on Computers, 1980
