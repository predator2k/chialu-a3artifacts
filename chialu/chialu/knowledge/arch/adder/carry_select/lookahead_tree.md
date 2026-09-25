---
family: carry_select
pin: {select_source: lookahead_tree}
---
# lookahead_tree

Tree-fed selection: a separate lookahead network, a spanning tree in
the origin design, computes the carries into every block boundary in
logarithmic depth, while each uniform block ripples its sum for both
carry cases in parallel. The tree's carry, rather than the previous
block's multiplexer, selects each block's result, so the multiplexer
chain of the linear form disappears and the delay is the tree depth
plus one selection.

The pick when delay dominates at 32 to 64 bits and the tree's wiring
is affordable: the spanning-tree adder uses 8-bit blocks whose ripple
results are ready slightly before the tree's selects, with the 8-bit
multiplexers keeping carry-output loading within target, where a
Manchester-lookahead hybrid needed at least 16-bit sections; the
sub-nanosecond 64-bit adder ripples 16-bit quadrants with fanout-of-1
local carries timed to reach each sum gate just before the long
select, and fuses selection and sum generation into one gate. Rippled
selects are cheaper where the multiplexer chain is short enough.

## references

lynch_swartzlander1992 -> T. W. Lynch, E. E. Swartzlander Jr., "A Spanning Tree Carry Lookahead Adder", IEEE Transactions on Computers, vol. 41, no. 8, pp. 931-939, 1992.
naffziger1996 -> S. Naffziger, "A Sub-Nanosecond 0.5 um 64 b Adder Design", IEEE International Solid-State Circuits Conference (ISSCC), pp. 362-363, 1996.
