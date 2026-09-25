---
family: approximate_truncated
pin: {lower_scheme: truncate_constant}
---
# truncate_constant

The lower k bits of both operands are replaced by constants rather than
added: the truncated stages produce a fixed pattern, generate no carry
into the accurate part, and switch no logic. The nonzeroing form forces
complementary constants on corresponding operand bits (A_i = NOT B_i),
so under uniformly distributed low-order subwords the summed truncation
error is zero-mean, which zeroing truncation does not achieve at the
same k.

Constant truncation is the pick when the lower part must cost nothing
in delay or energy: the full adders stay in place, so AND/OR input
buffers switch the truncation on per bit at run time for about 1% delay
and 4.5% area over the exact adder, and at k = 8 the 16-bit adder
spends about half the energy of the exact one in 28-nm FDSOI.
Complementary constants cut mean error distance by 60 to 67% against
zeroing truncation at the same k. The scheme suits addition; subtraction
prefers equal constants, and multiplication is excluded because its
energy depends on the constants chosen.

## references

frustaci2019 -> F. Frustaci, S. Perri, P. Corsonello, M. Alioto, "Energy-Quality Scalable Adders Based on Nonzeroing Bit Truncation", IEEE Transactions on VLSI Systems, vol. 27, no. 4, pp. 964-968, 2019
