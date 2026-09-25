---
family: prefix_and_incrementer
pin: {structure: prefix_and_tree}
---
# prefix_and_tree

A parallel-prefix carry network with the second operand fixed at zero:
the generate terms vanish, the prefix operator collapses to AND, and the
tree computes every all-lower-bits AND in logarithmic depth in whichever
topology the adder used. The same construction serves decrementers, and
every prefix principle used for adders, including the topology choice,
stays applicable.

The tree is the pick when the increment sits on the critical path: with
the constant-zero operand removed, the incrementer is considerably
smaller and faster than the comparable adder, and parallel-prefix
structures gain more from the AND-only recurrence than other speed-up
structures do. Against the chain it spends more gates and wiring for
logarithmic rather than linear carry delay, and the topology choice
moves the same depth/fanout/wiring trade the adder family has. Dual
direction costs only the decrement form of the same tree.

## references

zimmermann1997 -> R. Zimmermann, "Binary Adder Architectures for Cell-Based VLSI and their Synthesis", PhD thesis, Diss. ETH No. 12480, ETH Zurich, 1997.
