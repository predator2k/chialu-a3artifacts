---
family: srt_high_radix
pin: {residual_form: signed_digit}
---
# signed_digit

The partial remainder held as a signed-digit word at radix r: each
step forms p(j+1) = r p(j) - d q(j+1) in a carry-free signed-digit
adder, and the redundant quotient digits make an inexact comparison on
the first few leading digits of the residual sufficient, so the digit
is selected from a three- or four-digit prefix without a full
comparison against the divisor.

It is the pick where the residual adder must stay carry-free at any
radix and the selection reads digit signs rather than an assimilated
estimate: with minimal-redundancy quotient digits the comparison uses
the first four digits, and added comparators with divisor-multiple
generators select the digit in one addition cycle, where the simplest
form adds or subtracts the divisor repeatedly after each shift until
the range test passes. Against carry-save, which the family's tables
assume, the signed-digit residual costs a signed-digit cell per
position and a final conversion, and the truncation widths of the
table or the comparator constants are derived for it. At radix 2 the
same residual gives the digit from three digit signs and an unrolled
64-bit array of 396 gate delays.

## references

avizienis_1961 -> Avizienis, "Signed-Digit Number Representations for Fast Parallel Arithmetic", IRE Transactions on Electronic Computers, 1961
kuninobu_1987 -> Kuninobu, Nishiyama, Edamatsu, Taniguchi, Takagi, "Design of High Speed MOS Multiplier and Divider Using Redundant Binary Representation", 8th IEEE Symposium on Computer Arithmetic, 1987
