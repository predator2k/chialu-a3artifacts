---
family: operand_modification_multiply
pin: {function: reciprocal}
---
# reciprocal

The reciprocal seed: the upper m bits select one coefficient from a
2^m by (2m+3)-bit ROM, the modifier complements the lower operand
bits, and one multiplication of coefficient by modified operand gives
2m+2 accurate bits. The decimal form indexes a table by the k leading
divisor digits to read C' = 1/(XM + 5*10^-(k+1))^2, keeps XM and takes
the nine's complement of the next k digits to form X', and truncates
R0 = C' * X' to 2k-1 digits.

The reciprocal is the pick ahead of a Newton-Raphson or Goldschmidt
divider: the binary ROM is about half the original linear
approximation's and the addition is gone, and the decimal table is
2.5 KBytes at k = 3 with DPD input and output against 12 KBytes with
BCD. The infinite-precision approximation under-approximates 1/X and
truncation keeps the error negative with more than 2k-3 accurate
fraction digits, which the directed iterations and single-bias
final selection require. The reciprocal square root is the sibling
with a shifted modifier and expansion point.

## references

ito_1997 -> Ito, Takagi, Yajima, "Efficient Initial Approximation for Multiplicative Division and Square Root by a Multiplication with Operand Modification", IEEE Transactions on Computers, 1997
wang_2004 -> Wang, Schulte, "Decimal Floating-Point Division Using Newton-Raphson Iteration", IEEE ASAP, 2004
