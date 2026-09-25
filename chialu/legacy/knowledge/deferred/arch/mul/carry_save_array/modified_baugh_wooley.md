---
family: carry_save_array
pin: {signed_scheme: modified_baugh_wooley}
---
# modified_baugh_wooley

The modified Baugh-Wooley array: the sign-correction terms of the two
most significant partial-product columns are rearranged into one of the
equivalent forms, the original constants, the Pezaris AND functions, or
an inclusive-OR of the sign bits, while the rest of the array keeps its
uniform cells. In the FPGA-embedded form a 4 by 4 block reduces its
product to two rows in carry-save form and a following adder finishes it
only when the block sits in the last column of the grid.

The modified form is the pick when one array must serve both signed and
unsigned operands or must tile into larger multipliers: the block
configuration selects two's-complement or unsigned operation, the
two-row carry-save output lets blocks chain across an n by m grid, and
the correction logic in the top columns is the part that changes between
the variants while the full-adder logic stays equivalent. The trade
against the original transform is that the highest product bit may be
omitted when it is redundant, which is invalid when the product of the
two greatest negative operands is required, and that the final adder and
its topology are not specified in the embedded design, so the designer
supplies the carry-propagate stage.

## references

haynes_1998 -> S. D. Haynes, P. Y. K. Cheung, "Configurable Multiplier Blocks for Embedding in FPGAs", Electronics Letters, 1998
blankenship1974 -> P. E. Blankenship, "Comments on 'A Two's Complement Parallel Array Multiplication Algorithm'", IEEE Transactions on Computers, 1974
