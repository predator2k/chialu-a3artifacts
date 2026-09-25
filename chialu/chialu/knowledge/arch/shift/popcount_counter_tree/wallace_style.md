---
family: popcount_counter_tree
pin: {tree_shape: wallace_style}
---
# wallace_style

Reduction by weight with the fewest counters: every column of
equal-weight lines is reduced by the largest counter available, 6:3
or 7:3 stacking counters or full adders, in as few phases as possible,
the carries move one column up, and one final carry-propagate adder
resolves the last two rows, the organization of the Wallace
partial-product tree of a multiplier.

It is the pick when the counter tree is shared with, or built like, a
multiplier's reduction tree: the standard Wallace tree consumes the
least power at every evaluated size, the counter choice hardly matters
at small sizes, and at 64 and 128 bits the tree built from 6:3
stacking counters is faster than both the standard tree and the
existing 7:3-counter trees while using less power than the latter,
despite one extra reduction phase. It loses to balanced_tree on
regularity and adder reuse, and its irregular columns cost crossing
wires, more so with the stacking counters.

## references

fritz2017 -> C. Fritz, A. T. Fam, "Fast Binary Counters Based on Symmetric Stacking", IEEE Transactions on Very Large Scale Integration (VLSI) Systems, vol. 25, 2017
swartzlander_1973 -> E. E. Swartzlander Jr., "Parallel Counters", IEEE Transactions on Computers, vol. C-22, no. 11, pp. 1021-1024, 1973
