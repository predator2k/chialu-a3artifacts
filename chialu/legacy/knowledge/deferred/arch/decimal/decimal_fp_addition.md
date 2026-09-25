# decimal_fp_addition

IEEE 754 decimal addition on integer coefficients: each operand is a
sign, a biased exponent, and a DPD-packed significand expanded to BCD;
the operands are ordered by exponent, the significands are shifted by
the exponent difference to a common exponent, added or subtracted by a
decimal significand adder with guard and sticky digits, corrected to
valid BCD, rounded, and packed to DPD. There is no automatic
normalization: an exact result keeps the smaller operand exponent, so
equal-exponent operands need no alignment and results may hold leading
zeros. Commercial units split execution into equal-exponent,
align-to-smaller, and shift-both cases; the first is the common case
and ends early.

Alignment trades shifter width against sequencing. A full rotator that
shifts either operand left or right by up to 34 digits, with
operation-dependent pre-alignment that assumes a carry-out for
addition and cancellation for subtraction, pins the rounding position
to two decimal locations and removes the exponent decrementor, at two
pipeline cycles. Parallel left and right barrel shifters driven by the
exponent difference and the leading-zero count reach the same fixed
rounding position in a single-pass pipeline. The case-split units keep
the adder at p digits and pay with variable latency, 12 to 28 cycles
for a 16-digit add on z10, and the back-to-back minimum is set by
dispatch notice rather than by the datapath.

Rounding trades a second carry propagation against injection. An
increment of one at the least significant digit after the sum extends
execution by a pass through the adder. Injecting a rounding-dependent
value before the significand addition, with trailing-nine flag vectors
performing the conditional increment after a most-significant-digit
shift, removes that pass and gives 21% less delay at 1.6% less area
than the flag-corrected excess-3 design in the same 0.11 um library.
The significand adder slot decides the digit code and correction
placement: excess-3 through a binary adder with flag generation, BCD
with +6 pre-correction, or a speculative sum with fused IEEE rounding.

The format choice sets datapath width, with a 34-digit adder and
shifters for decimal128 and a 36-digit internal path in the IBM
accelerators. The rounding contract covers every 754-2008 mode plus
the commercial half-up, half-down, up, and Java BigDecimal modes, and
underflow logic is unnecessary because a decimal sum cannot be both
subnormal and inexact. The family wins wherever scale-preserving
decimal semantics are mandated; a pipelined adder delivers one result
per cycle at 0.148 mm2 in 0.11 um, and the same datapath extends to
compare, minNum, maxNum, quantize, and roundToIntegral.

No unit template opens `decimal_misc_space`: the family belongs to a decimal floating-point unit (or a conversion between number systems) that the ALU, dot and SFU templates do not provision, so no seed declares it and the library has no module for it; the BCD ALU's decimal adders, multipliers and dividers come from `chialu/targets/rtl/families/decimal.py`.

## references

cowlishaw_2003 -> Cowlishaw, "Decimal Floating-Point: Algorism for Computers", 16th IEEE Symposium on Computer Arithmetic (ARITH-16), 2003
muller_2018 -> J.-M. Muller, N. Brunie, F. de Dinechin, C.-P. Jeannerod, M. Joldes, V. Lefevre, G. Melquiond, N. Revol, S. Torres, "Handbook of Floating-Point Arithmetic", 2nd ed., Birkhauser, 2018
thompson_2004 -> Thompson, Karra, Schulte, "A 64-bit Decimal Floating-Point Adder", IEEE Computer Society Annual Symposium on VLSI (ISVLSI), 2004
wang_2009 -> Wang, Schulte, Thompson, Jairam, "Hardware Designs for Decimal Floating-Point Addition and Related Operations", IEEE Transactions on Computers, 2009
schwarz_2009 -> Schwarz, Kapernick, Cowlishaw, "Decimal Floating-Point Support on the IBM System z10 Processor", IBM Journal of Research and Development, 2009
carlough_2011 -> Carlough, Collura, Mueller, Kroener, "The IBM zEnterprise-196 Decimal Floating-Point Accelerator", 20th IEEE Symposium on Computer Arithmetic (ARITH-20), 2011
