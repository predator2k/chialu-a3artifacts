---
family: operand_modification_multiply
pin: {function: recip_sqrt}
---
# recip_sqrt

The reciprocal-square-root seed: the modifier complements the lower
operand bits and shifts them by one bit, and the coefficient times
the modified operand replaces the linear approximation's multiply
and add. The decimal form splits X into k-digit XM and lower XL,
rearranges a first-order Taylor expansion around A = XM + 2/3 *
10^-k as R0 = C' * X', forms X' in parallel with the lookup while
ignoring its trailing 10^-(n+1) term to avoid a carry propagation,
and stores the 7-digit C' in DPD.

The reciprocal square root is the pick ahead of a square-root
iteration: the shifted expansion point gives one more digit than
expanding at XM, the approximation error is bounded below
sqrt(10)/6 * 10^(-2k+2), and at least 2k-2 accurate fraction digits
survive truncation with the seed kept below the exact value. The
DPD table is 3 KBytes at k = 3, a factor 4.5 below BCD indexing and
storage. The binary double-precision seed needs 896 bits of ROM
ahead of two Newton-Raphson iterations and 224K bits ahead of one;
the reciprocal is the sibling for division.

## references

ito_1997 -> Ito, Takagi, Yajima, "Efficient Initial Approximation for Multiplicative Division and Square Root by a Multiplication with Operand Modification", IEEE Transactions on Computers, 1997
wang_2005 -> Wang, Schulte, "Decimal Floating-Point Square Root Using Newton-Raphson Iteration", IEEE ASAP, 2005
