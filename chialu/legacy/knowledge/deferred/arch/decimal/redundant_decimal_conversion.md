# redundant_decimal_conversion

Conversion between redundant decimal digits and BCD. BCD to RBCD
detects the digits 7, 8 and 9, adds 6 to each detected digit in
parallel and applies the generated carries in a second digitwise
step, so the delay is constant in the word length. Redundant to BCD
treats a negative digit as generating a borrow and a zero digit as
propagating one, resolves the borrows in a ripple, look-ahead or
prefix network, and corrects each digit by a conditional constant:
add 6 to a negative digit, or select S, S-1, S+10 or S+9 from the
neighbouring carries. The same correction pass can absorb the
rounding increment of +1, 0 or -1 and the absolute value.

Direction and digit set fix the converter's ends: BCD to RBCD feeds a
redundant adder, while RBCD digits in [-7,7] or the [-8,7] digits of
a signed-digit multiplier tree convert back to BCD at the tail. A
negative sign-magnitude BCD operand converts digitwise and is then
negated by the two's complement of each RBCD digit. The borrow
network is where the delay goes: the digitwise constant scheme serves
only the BCD to RBCD direction, ripple propagates the borrow digit by
digit, carry look-ahead resolves it in parallel, and the
arrival-partitioned hybrid joins several small Ladner-Fischer, 2-bit
carry-lookahead and Han-Carlson networks according to when the
partial-product-reduction digits arrive, which gives a 410 ps
converter tail at 90 nm for a 16 by 16 digit multiplier. The carry
network slot holds that prefix structure.

The correction choice follows the digit set: add 6 digitwise suits
RBCD, while the conditional constant select suits the [-8,7] digits
whose neighbouring carries pick among four candidates. Fused rounding
folds the +1, 0 or -1 increment, which is derived from the rounding
digit, the signed sticky, the sign, the rounding mode and the LSD
parity, into the same negative-carry prefix and correction pass
together with the absolute value; the fused rounder runs at 11.11 FO4
against 30.85 FO4 for a separate rounding setup, at 1364 against
11,847 NAND2. The family is feed-forward and is the final conversion
of redundant_decimal_addition, of parallel_decimal_multiplication and
of a decimal_fma with a redundant internal encoding; its cost is the
encoding step on the way in, which the carry-free addition of the
redundant families pays for.

No unit template opens `decimal_misc_space`: the family belongs to a decimal floating-point unit (or a conversion between number systems) that the ALU, dot and SFU templates do not provision, so no seed declares it and the library has no module for it; the BCD ALU's decimal adders, multipliers and dividers come from `chialu/targets/rtl/families/decimal.py`.

## references

shirazi_1989 -> Shirazi, Yun, Zhang, "RBCD: Redundant Binary Coded Decimal Adder", IEE Proceedings E - Computers and Digital Techniques, 1989
han_2013 -> Han, Ko, "High-Speed Parallel Decimal Multiplication with Redundant Internal Encodings", IEEE Transactions on Computers, 2013
han_2016 -> Han, Zhang, Ko, "Decimal Floating-Point Fused Multiply-Add with Redundant Internal Encodings", IET Computers & Digital Techniques, 2016
