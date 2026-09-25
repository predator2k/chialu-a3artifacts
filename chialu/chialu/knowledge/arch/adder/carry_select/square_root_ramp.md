---
family: carry_select
pin: {block_sizing: square_root_ramp}
---
# square_root_ramp

The SQRT carry-select adder: block widths grow toward the MSB in an
arithmetic progression, so that each block's speculative ripple for
both carry cases finishes just as its select carry emerges from the
multiplexer of the block below. With rippled block carries the
critical path is the first block's ripple plus one multiplexer per
block, and the progression makes that path grow with the square root
of the word length rather than linearly.

The ramp is the pick whenever the selects ripple from block to block;
uniform blocks belong with tree-fed selects, where the tree rather
than the previous block sets when each select arrives. A
delay-balanced sizing is the same idea with the block lengths fitted
to measured adder, multiplexer or LUT delays instead of the
progression. The ramp is the baseline that the binary-to-excess-1
duplication cut is measured against at 8 to 64 bits, and the area and
power savings of that cut grow with width along the ramp.

## references

ramkumar2012 -> B. Ramkumar, H. M. Kittur, "Low-Power and Area-Efficient Carry Select Adder", IEEE Transactions on VLSI Systems, vol. 20, no. 2, pp. 371-375, 2012.
