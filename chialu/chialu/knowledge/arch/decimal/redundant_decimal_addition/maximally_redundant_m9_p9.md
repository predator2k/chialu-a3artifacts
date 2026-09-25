---
family: redundant_decimal_addition
pin: {digit_set: maximally_redundant_m9_p9}
---
# maximally_redundant_m9_p9

The maximally redundant decimal signed-digit set: each digit takes any
value from -9 to 9 and is encoded as an 8-bit vector of four binary
signed digits, so a BCD operand is already a valid DSD operand and
conversion into the code costs no hardware delay. Carry-free addition of
a DSD operand to a BCD one limits carry propagation to a small number of
digit positions, which makes each digitwise addition independent of
operand length.

The [-9, 9] set is the pick when one operand of every addition arrives
in BCD, as in the decimal division recurrence on file, where the DSD
partial remainder is added to BCD divisor multiples and four-digit
carry-free comparators select the digit: the free BCD-to-DSD direction
removes an input conversion that the [-7, 7] and Svoboda sets require.
The price is storage and the reverse conversion: the digit occupies
eight bits, twice the four of the [-7, 7] two's-complement code, and
DSD-to-BCD conversion needs carry generation and remains time consuming,
so it is done once at the output. The design instantiates an adder
attributed to earlier work and reports no standalone adder delay or
area.

## references

nikmehr_2006 -> Nikmehr, Phillips, Lim, "Fast Decimal Floating-Point Division", IEEE Transactions on Very Large Scale Integration (VLSI) Systems, 2006
