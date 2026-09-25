---
family: operand_modification_multiply
pin: {seed_synthesis: boolean_partial_product_rows}
---
# boolean_partial_product_rows

The seed synthesized inside the multiplier array: Boolean functions of
the operand bits are placed as generalized elements in the partial
product rows, back-solved so that the array's own summation produces
the reciprocal approximation, and the floating-point multiplier that
will run the iteration can be reused for the seed with no separate
table.

It is the pick when a multiplier array is already on the datapath and
a ROM seed's area is the cost to cut: 484 elements in 18 columns of a
53-row array give 12.0 bits minimum and 15.2 bits average accuracy at
39 times less area than an equivalent 12-bit ROM, and 175 elements in
the Booth array give 9.2 bits minimum and 12.7 average.
The rows are solved for the array in use, since the plain 53-row and
the Booth 27-row arrays take different element sets; the library
sums the rows through the datapath's adder.
The modified-operand product is the sibling when the seed is to come
from one multiplication of a bit-modified operand rather than from
elements inside the array.

## references

oberman_1997 -> Oberman, Flynn, "Division Algorithms and Implementations", IEEE Transactions on Computers, 1997
