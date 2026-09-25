---
family: decimal_digit_recurrence
pin: {quotient_digit_set: minimally_redundant_m5_p5}
---
# minimally_redundant_m5_p5

The prescaled nonrestoring recurrence of the POWER6 decimal divider:
dividend and divisor are multiplied by a two-digit reciprocal
approximation so that 1.0 <= D' < 1.1, after which the next quotient
digit is simply the most significant partial-remainder digit, recoded
from -9..9 into -5..5. Each iteration computes PA = P - qD' and
PB = P - (q +/- 1)D', so multiples 6 to 9 become a 10-weighted digit
plus a small signed digit, and decimal on-the-fly correction converts
the redundant quotient.

It is the pick when a general quotient-selection table is the
obstacle: the 32 KB table for direct maximally redundant selection
becomes a 256-byte prescale table, at 6 to 12 prescaling cycles and
four cycles per digit, for 82 and 154 cycles on decimal64 and
decimal128 against 207 and 423 for restoring division, above 5 GHz.
The zEnterprise-196 unit keeps the same selection with 7 startup
cycles and four cycles per iteration instead of five. It loses to the
split -7..7 set when prescaling latency dominates short operands, and
a redundant-adder residual would cut the digit loop further at more
area. Selection error must stay under one digit.

## references

schwarz_2007 -> Schwarz, Carlough, "Power6 Decimal Divide", IEEE ASAP, 2007
carlough_2011 -> Carlough, Collura, Mueller, Kroener, "The IBM zEnterprise-196 Decimal Floating-Point Accelerator", 20th IEEE Symposium on Computer Arithmetic (ARITH-20), 2011
