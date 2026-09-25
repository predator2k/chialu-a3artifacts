---
family: speculative_decimal_addition
pin: {speculation_target: rounding_increment}
---
# rounding_increment

The rounding increment is the speculated quantity: a value set by the
rounding mode and the sign is injected into the round/sticky digit
positions before significand addition, so the IEEE rounding folds into
the one carry-propagate pass and mostly becomes truncation. A nonzero
most-significant result digit triggers an injection correction through
prefix-network flags rather than another carry propagation; z196
injects into guard/sticky of an end-around-carry AREN and selects
digit p or p+1.

Wang's adder feeds 19-digit operands to a Kogge-Stone network, with
flag set F1 for postcorrection and F2 for the injection correction;
the added trailing-nine flags cost 13.7 percent more network area but
sit in parallel with postcorrection, off the critical path. Injection
is suppressed for effective subtraction without a right shift because
the result may be negative, and roundTiesToEven clears the result LSB
on an exact halfway case after the final addition. z196 runs a carry-
select adder independent of carry-in over 36 digits, or dual 18-digit
operations, with 2-cycle simple and 3-cycle rounded output. The
digit_correction sibling speculates the +6 and leaves rounding to a
later step; the both sibling adds digit speculation to this one.
rounding_increment presumes fused_ieee_rounding and is the pick for a
DFP significand adder whose carry network can carry the extra flags.

## references

wang_2009 -> Wang, Schulte, Thompson, Jairam, "Hardware Designs for Decimal Floating-Point Addition and Related Operations", IEEE Transactions on Computers, 2009
carlough_2011 -> Carlough, Collura, Mueller, Kroener, "The IBM zEnterprise-196 Decimal Floating-Point Accelerator", 20th IEEE Symposium on Computer Arithmetic (ARITH-20), 2011
