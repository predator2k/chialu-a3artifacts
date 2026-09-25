---
family: sparse_prefix_hybrid
pin: {sum_block_style: carry_select}
---
# carry_select

The spanning-tree adder of Lynch and Swartzlander: a three-level,
four-way tree of four-bit Manchester carry-chain modules combines
propagate/generate intervals, using the associativity and idempotency
of the carry operator, and delivers the carries at every eighth bit
boundary without a back-propagation pass; each boundary carry then
selects between two precomputed eight-bit ripple-carry sums, one built
for carry-in 0 and one for carry-in 1.

The block is the pick when the sum blocks are wide, eight bits here
against the 2-bit and 4-bit conditional-sum blocks of the later sparse
designs, and a ripple chain inside the block is cheap: the critical
path is three Manchester carry-chain levels plus the select. The
56-bit implementation in 1 um CMOS measures about 3.2 ns from clock
edge to the most significant sum output, and that speed is expected to
stay nearly constant for 24 <= N < 64. The dynamic implementation
needs an idle clock phase for precharging with the operands stable at
the start of evaluation, and the equal-length chains chosen for layout
regularity leave some speed to mixed chain lengths. The Ling hybrid of
Dimitrakopoulos keeps the select structure but drives modified
carry-select blocks from paired even/odd pseudo-carries. In the ADIR
grammar it is `family: sparse_prefix_hybrid` with
`pin: {sum_block_style: carry_select}`.

## references

lynch_swartzlander1992 -> T. W. Lynch, E. E. Swartzlander Jr., "A Spanning Tree Carry Lookahead Adder", IEEE Transactions on Computers, vol. 41, no. 8, pp. 931-939, 1992.
dimitrakopoulos2005 -> G. Dimitrakopoulos, D. Nikolos, "High-Speed Parallel-Prefix VLSI Ling Adders", IEEE Transactions on Computers, 2005.
