---
family: bcd_direct_addition
pin: {carry_scheme: digit_group_lookahead}
---
# digit_group_lookahead

The Schmookler-Weinberger adder: each BCD digit is split into bit 1
and bits 8/4/2, functions K and L generate and propagate the decimal
carry in two logic levels, Boolean expressions produce S1, S2, S4
and S8 directly, and digit generate/propagate functions form
byte-level lookahead signals available after three levels, where a
byte holds two adjacent decimal digits. The eight-digit Model 195
adder has four bytes and produces all sums in six logic levels or
less.

Byte lookahead is the pick when circuit fan-in and wired-OR limits
(four outputs per wired OR in the current-switch circuits) rule out
one word-wide carry network: it avoids the two correction levels of
a correction-based adder, needs fewer circuits than one, and costs
about 18 percent more circuitry than a 32-bit binary adder at the
same depth, or one extra level at equal cost. A lookahead version
of the same adder reaches 1.54 ns at 1336 gates for 64 bits in TSMC
0.18 um against 1.40 ns for the prefix-network form, which is the
sibling for the 32-digit widths of multiplier final adders.

## references

schmookler_1971 -> Schmookler, Weinberger, "High Speed Decimal Addition", IEEE Transactions on Computers, 1971
schmookler_1972 -> Schmookler, "Considerations in the Design of a High Speed Decimal Unit", 2nd IEEE Symposium on Computer Arithmetic (ARITH-2), 1972
bayrakci_2007 -> Bayrakci, Akkas, "Reduced Delay BCD Adder", IEEE ASAP, 2007
