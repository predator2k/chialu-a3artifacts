---
family: redundant_decimal_addition
pin: {digit_set: overloaded_0_15}
---
# overloaded_0_15

The overloaded decimal digit: every 4-bit pattern from 0 to F is
accepted as a base-10 digit, so the digit set is [0, 15] without a sign
and the adder is a 4-bit binary carry-save adder followed by a 4-bit
binary carry-propagate adder per digit. A carry out of a digit means
sixteen, so the +6 correction that restores decimal weight is applied to
the multiple entering the next iteration rather than in the current one,
and clean-up blocks add six to digits A through F to return the result
to BCD.

The overloaded set is the pick for an iterative accumulator whose one
redundant operand is the running partial product: correction happens
only after a digit exceeds fifteen, so the iterative stage is 8 logic
levels against 10 for a decimal 4:2 compression in the LSI 0.11 um
library, and the binary adders need no decimal-specific cells. The set
is unsigned and reaches only one operand, so it does not give the
carry-free two-operand addition of the signed sets, and every overloaded
digit leaving the iterative structure plus every remaining intermediate
digit must pass through a BCD clean-up before output. The deferred
correction schedule and the separate output clean-up are the two
mechanisms a designer sizes.

## references

kenney_2004 -> Kenney, Schulte, Erle, "A High-Frequency Decimal Multiplier", IEEE International Conference on Computer Design (ICCD), 2004
