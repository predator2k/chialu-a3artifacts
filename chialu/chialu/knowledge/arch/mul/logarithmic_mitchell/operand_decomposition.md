---
family: logarithmic_mitchell
pin: {correction_scheme: operand_decomposition}
---
# operand_decomposition

Two Mitchell multiplications on decomposed operands: X and Y are split
by bitwise OR, XOR and complement equations into A, B, C and D with
X times Y equal to C times D plus A times B, each decomposed product
goes through its own leading-one detectors, shifters and adder, and
a binary adder combines the two. The
decomposition lowers the probability of a 1 in the operands from a
half to a quarter, which shrinks the fractional-logarithm error and
the mantissa-to-integer carryovers.

It is the pick when a bare Mitchell multiplier is not accurate enough
and a multiplier array is still off the table: average error falls by
44.7 percent, and a divided-approximation correction on three mantissa
bits adds under 2 percent hardware on top, whereas a table of
correction values or the Mitchell error correction adds about half.
The parallel form nearly doubles the area and power of the plain
Mitchell multiplier, landing near the footprint of a 32-bit array
multiplier in 0.7 um at about 30 percent of its power; the sequential
form reuses one datapath for the two products, doubling delay for
under 4 percent area. A zero detector forces a zero output when either
input is zero.

## references

mahalingam2006 -> V. Mahalingam, N. Ranganathan, "Improving Accuracy in Mitchell's Logarithmic Multiplication Using Operand Decomposition", IEEE Transactions on Computers, vol. 55, no. 12, pp. 1523-1535, 2006
