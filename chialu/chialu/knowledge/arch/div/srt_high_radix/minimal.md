---
family: srt_high_radix
pin: {digit_redundancy: minimal}
---
# minimal

The quotient digit set is the smallest redundant one, {-2, ..., 2} at
radix 4 with n = 2 and residual bound |x| < 2/3 d. Robertson selects
the digit by sign and by comparing 4x_j against 0.5d and 1.5d, so only
d and 2d are needed, formed by conditional doubling and complementing
with one binary adder. Selection needs seven binary digits of the
shifted residual for 1/4 < |d| < 1; the Pentium's carry-save table
indexes four divisor bits and seven residual bits.

Minimal redundancy is the pick when the divisor multiples must stay at
shifts of d: no 3d precompute and one fewer multiple in the selector,
at the cost of a larger and slower selection table, since maximally
redundant radix-4 selection is reported 20% faster and 50% smaller.
Taylor's radix-16 designs with {-2, ..., 2} cost 1600 cells against
1870 for {-3, ..., 3} in option 4C, at 184 ns against 178 ns. It is
the digit set of the Pentium, the R3010 and Clarke's verified divider,
which accumulate positive and negative digits separately and resolve
the quotient at the end. Burgess's truncation for qmax = 2 is
(t, f, b) = (3, 3, 1) with 15 selection inputs, against (4, 1, 2) and
12 inputs for qmax = 3. In the ADIR grammar it is
`family: srt_high_radix` with `pin: {digit_redundancy: minimal}`.

## references

robertson_1958 -> Robertson, "A New Class of Digital Division Methods", IRE Transactions on Electronic Computers, 1958
harris_1997 -> Harris, Oberman, Horowitz, "SRT Division Architectures and Implementations", 13th IEEE Symposium on Computer Arithmetic, 1997
taylor_1985 -> Taylor, "Radix 16 SRT Dividers with Overlapped Quotient Selection Stages", 7th IEEE Symposium on Computer Arithmetic, 1985
burgess_1995 -> Burgess, Williams, "Choices of Operand Truncation in the SRT Division Algorithm", IEEE Transactions on Computers, 1995
coe_1995 -> Coe, Mathisen, Moler, Pratt, "Computational Aspects of the Pentium Affair", IEEE Computational Science and Engineering, 1995
