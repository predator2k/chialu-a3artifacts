---
family: redundant_decimal_addition
pin: {digit_set: svoboda_signed_digit}
---
# svoboda_signed_digit

Svoboda's signed-digit decimal code: each digit takes values -6 to +6
and is stored as a 5-bit character with X = 3x for positive digits and X
- 31 = 3x for negative ones, so complementing the character negates the
digit. Each position adds two signed digits and two incoming transfers,
emits one signed digit and separate +1 and -1 transfers to the next
position that may coexist and cancel, and the transfers do not propagate
further, so the adder is built from binary adders and Boolean networks.

The Svoboda code is the origin of carry-free decimal addition and the
pick when a signed digit set with a simple negation rule matters more
than storage: the 5-bit character costs one bit over BCD, has two
encodings of zero, and gives positive characters even parity and
negative ones odd. Conversion is the price: an n-digit conventional
input needs an n + 1 place adder, input conversion maps digits through a
table and adds a constant, and output conversion repeatedly adds a
correction until no digit equals 5. The paper gives a block diagram
without timing or area, and a later synthesis in TSMC 0.13 um places the
Svoboda adder at 2.50 ns and 781 area units against 0.87 ns and 622 for
the two's-complement [-7, 7] sibling, which keeps the digit in four
bits.

## references

svoboda_1969 -> Svoboda, "Decimal Adder with Signed Digit Arithmetic", IEEE Transactions on Computers, 1969
gorgin_2009 -> Gorgin, Jaberipur, "Fully Redundant Decimal Arithmetic", 19th IEEE Symposium on Computer Arithmetic (ARITH-19), 2009
