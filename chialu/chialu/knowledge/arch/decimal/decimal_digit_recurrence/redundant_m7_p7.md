---
family: decimal_digit_recurrence
pin: {quotient_digit_set: redundant_m7_p7}
---
# redundant_m7_p7

Robertson's radix-10 digit set with redundancy factor 7/9: each
quotient digit is decomposed as q = q' + q'' with q' in {-5, 0, 5} and
q'' in {-2, -1, 0, 1, 2}, so the recurrence conditionally adds or
subtracts 5d and then d or 2d, and one sequential decimal adder with a
shared doubling/quintupling circuit replaces stored multiples. The
BCD form precomputes 5d and 2d, keeps the most significant slice in
radix-2 two's complement for selection, and converts the signed-digit
quotient at the end.

It is the pick when a single adder must retire one digit per pass at
the fewest operations: 2.33 per digit on average against 3.4 for
nonrestoring with doubling and quintupling, with three selection
digits once the divisor is standardized to 1/10 < |d| < 1. The
Lang-Nannarelli unit runs 20 cycles at about 1 ns in STM 90 nm and
shares its datapath with a radix-16 binary mode for about 30% more
area. A fully redundant DSSD variant keeps operands, quotient and
remainders in signed-digit form with multiples -7d..7d and a table on
three divisor digits. The prescaled -5..5 set wins when the
selection logic, not the multiples, is the bottleneck.

## references

robertson_1958 -> Robertson, "A New Class of Digital Division Methods", IRE Transactions on Electronic Computers, 1958
lang_2007b -> Lang, Nannarelli, "Combined Radix-10 and Radix-16 Division Unit", 41st Asilomar Conference on Signals, Systems and Computers, 2007
gorgin_2009 -> Gorgin, Jaberipur, "Fully Redundant Decimal Arithmetic", 19th IEEE Symposium on Computer Arithmetic (ARITH-19), 2009
