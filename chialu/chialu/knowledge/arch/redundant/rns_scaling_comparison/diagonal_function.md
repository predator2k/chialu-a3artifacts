---
family: rns_scaling_comparison
pin: {method: diagonal_function}
---
# diagonal_function

For pairwise coprime moduli m_1 ... m_n with M_i = M/m_i and
SQ = sum of the M_i, the diagonal function D(X) = |sum k_i x_i|_SQ,
with constants k_i from multiplicative inverses modulo SQ, is
monotonic over the represented range: two numbers with different D
values are ordered directly, and equal values are resolved by
comparing corresponding residues. The improved form adds SQ to the
modulus set, applies D to X' = [X/SQ] and uses the SQ coordinate for
ties, with no excluded buffer zone.

The diagonal function is the pick for magnitude comparison without
reverse conversion or a redundant modulus: the nonredundant SQT takes
3 operation cycles for its first stage and n - 1 for the summation
modulo SQ, where a lookup-table mixed-radix comparison needs
n(n - 1)/2 multiplications and subtractions over 2n cycles, and direct
CRT comparison stalls on the lack of effective adders modulo a large
arbitrary integer. A large SQ raises hardware cost with many moduli;
grouping physical moduli into virtual moduli shrinks it, 40808 to 930
for the set 17, 29, 19, 23, under 0.5 percent of M, at the price of a
fast MRC inside each group. Theorems 3 and 4 prove the ordering and
the tie resolution, and no approximation error is involved. The
fractional CRT gives sign and threshold tests more cheaply but not
arbitrary comparison, and the redundant modulus serves base extension
rather than ordering.

The library realizes this method as D(X) = |sum k_i x_i|_SQ with the
residue tie rule. Generation checks the coefficient identities exactly:
`sum(k_i) = 0 mod SQ` and `k_i*m_i = -1 mod SQ`. A modulus without the
required inverse is an explicit error.

Writing `x_i = X - m_i*floor(X/m_i)` in the residue sum proves that
`D(X) = sum(floor(X/m_i)) mod SQ`. For `0 <= X < M`, that floor sum
lies between zero and `SQ - n`, so the final modulus does not wrap.
Every summand is monotonic. When the sum ties for two inputs, every
individual quotient ties as well. The first residue then orders the
inputs within their common quotient interval.

This identity replaces the old random ordering check. A failed
coefficient check does not substitute a fractional CRT implementation.

## references

dimauro_1993 -> Dimauro, Impedovo, Pirlo, "A New Technique for Fast Number Comparison in the Residue Number System", IEEE Transactions on Computers, 1993
vu_1985 -> Vu, "Efficient Implementations of the Chinese Remainder Theorem for Sign Detection and Residue Decoding", IEEE Transactions on Computers, 1985
shenoy_kumaresan_1989 -> Shenoy, Kumaresan, "Fast Base Extension Using a Redundant Modulus in RNS", IEEE Transactions on Computers, 1989
