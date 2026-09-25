---
family: parallel_decimal_multiplication
pin: {internal_digit_code: xs3_odds}
---
# xs3_odds

Excess-3 multiples with overloaded-decimal-digit-set reduction: 0X to
5X are precomputed in XS-3 by carry-free logic, since XS-3 gives
constant-time 3X and negation by bit inversion, a constant correction
recodes the XS-3 partial products to ODDS digits, a binary
CSA/compressor tree reduces the ODDS rows with no invalid-code
correction while concurrent carry counting supplies the decimal
times-6 correction, and a BCD carry-propagate adder converts the last
two words.

It is the pick for the fastest nonredundant parallel BCD multiplier:
the 16x16-digit design runs at 41.5 FO4 and 44,200 NAND2 in 90 nm
against 31.1 FO4 and 34,000 NAND2 for a 53x53-bit Booth radix-4
multiplier, and it takes 20 to 35 percent less area than the fastest
compared BCD designs at a given delay. Against bcd4221 it removes the
carry-propagate 3X and the per-level doubling; against the redundant
signed-digit encodings it still pays a final conversion, which those
omit when the product feeds a fused multiply-add adder. The fully
parallel Decimal128 form is large enough that a sequential commercial
implementation is considered more realistic.

## references

vazquez_2014 -> Vazquez, Antelo, Bruguera, "Fast Radix-10 Multiplication Using Redundant BCD Codes", IEEE Transactions on Computers, 2014
