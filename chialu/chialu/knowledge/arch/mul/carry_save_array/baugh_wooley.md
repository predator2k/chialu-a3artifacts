---
family: carry_save_array
pin: {signed_scheme: baugh_wooley}
---
# baugh_wooley

The Baugh-Wooley transform: the partial-product bits that carry a
negative weight because they involve the sign bit of the multiplier or
the multiplicand are gathered into the last two rows, and each negative
row is replaced, through the two's-complement negation identities, by
complemented partial-product bits plus added constants. The result is a
uniform array in which every coefficient is positive, ordinary cells
stay AND plus full adder, and five extra bits account for the sign
correction.

Baugh-Wooley is the pick for signed two's-complement multiplication on a
regular array: the five sign-correction bits are absorbed without
increasing total propagation delay, the only extra requirement is the
complement of each operand bit, which current-mode logic supplies for
free and registers or high-fanout drivers supply otherwise, and the
resulting array preserves the unsigned structure with minor inversions
and constant-bit changes, so a bit-level pipeline built for unsigned
operands carries over. The uniform array also accepts any summation
technique, tree or array. The two most significant columns admit
equivalent variants, and the highest product bit may be omitted when it
is redundant, except when the product of the two greatest negative
operands is needed.

## references

baugh1973 -> C. R. Baugh, B. A. Wooley, "A Two's Complement Parallel Array Multiplication Algorithm", IEEE Transactions on Computers, vol. C-22, no. 12, pp. 1045-1047, 1973
blankenship1974 -> P. E. Blankenship, "Comments on 'A Two's Complement Parallel Array Multiplication Algorithm'", IEEE Transactions on Computers, 1974
hatamian1986 -> M. Hatamian, G. L. Cash, "A 70-MHz 8-bit x 8-bit Parallel Pipelined Multiplier in 2.5-um CMOS", IEEE Journal of Solid-State Circuits, vol. SC-21, no. 4, pp. 505-513, 1986
