---
family: popcount_counter_tree
pin: {tree_shape: balanced_tree}
---
# balanced_tree

Pairwise addition of partial counts: the inputs are cut into groups,
each group is counted by a small first-stage counter (four bits to a
three-bit count in the CDC 6600, 2-, 3- or 4-input counter modules in
the Berger generator), and the group counts are added two at a time by
a tree of adders, so the depth is one first-stage counter plus one
adder level per halving of the group count, and every level is a plain
binary addition of equal-width operands.

It is the pick when the adders already exist or the layout must stay
regular: the 6600 counts a 60-bit word in 800 ns on the divide unit's
own lookahead adder, and the modular Berger construction recursively
partitions blocks until predesigned counters and standard 2-bit adders
apply, with a special 2-bit adder for a five-bit block. It spends more
cells than wallace_style, which reduces by weight with the fewest
counters and a single final adder, and its ripple form costs m - 1
stages per addition, so it wins on reuse and modularity rather than on
delay.

## references

thornton_1970 -> J. E. Thornton, "Design of a Computer: The Control Data 6600", Scott, Foresman and Co., 1970
lala_2001 -> P. K. Lala, "Self-Checking and Fault-Tolerant Digital Design", Morgan Kaufmann, 2001
