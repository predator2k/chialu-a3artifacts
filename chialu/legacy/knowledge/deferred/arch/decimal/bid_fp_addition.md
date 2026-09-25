# bid_fp_addition

IEEE 754 decimal addition on BID operands whose significands stay
binary integers: the operands are swapped so the larger exponent
leads, K is the exponent difference, and the digit count of the
leading significand with K selects one of three cases. Cases 1 and 2
align by multiplying a significand by 10^K, add or subtract the
binary significands, and round when needed; case 3 rounds the smaller
operand first, pushes the larger toward 16 digits by a 10^g multiply,
then adds or subtracts. Rounding multiplies by an upward-rounded
approximation of 10^-x, truncates, and applies a one-unit correction
for the mode and the inexact flag. One binary multiplier serves
alignment and rounding.

The reciprocal rounding choice trades multiplier width against a
pre-shift: multiplying by an approximation of 10^-x needs the full
approximation width, while truncating C times 2^-x first and
multiplying by an approximation of 5^-x is x bits narrower; the
discarded fractional product identifies exact results, midpoints and
the two sides of a midpoint, so one correction step implements every
rounding mode. For 19-digit coefficients and x = 3 the approximation
needs 65 bits by the general bound and 62 bits after the
boundary-inequality refinement. The equal-exponent fast path skips
the alignment multiply when K = 0, and variable latency lets that
path finish in 3 cycles against 7 for the aligned cases; a
fixed-latency unit gives up that gain. Sharing the multiplier between
alignment and rounding keeps one 64-bit multiplier, about 70% of the
adder area in 0.11 um, and the same multiplier can serve binary
floating-point multiplication or other BID operations.

The rare-case recovery choice decides what happens when case 3 yields
at least 17 digits after addition or fewer than 16 after subtraction:
feeding the result through the rounder again, recalculating the
alignment, or both. Special values in hardware adds the NaN, infinity
and exception handling that the reported design leaves outside the
implementation. The format choice sets the coefficient and multiplier
widths; the reported hardware builds decimal64 with a 54-bit
significand and 16 digits, while the software library covers bid64
and bid128 with the same rounding methods. The binary multiplier slot
carries most of the datapath cost.

The family wins where the operands arrive in BID and a binary
multiplier already exists: the 7-cycle pipelined adder, 68,459 NAND2
at 44 FO4 in 0.11 um, replaces a 71-cycle average software addition,
and the aligned cases pay one multiply where decimal_fp_addition pays
a decimal shifter plus a BCD significand adder. It loses where the
operands are stored as DPD digits, which decimal_fp_addition consumes
directly, and where no multiplier can be shared. The unit is
feed-forward; latency varies only by case.

No unit template opens `decimal_misc_space`: the family belongs to a decimal floating-point unit (or a conversion between number systems) that the ALU, dot and SFU templates do not provision, so no seed declares it and the library has no module for it; the BCD ALU's decimal adders, multipliers and dividers come from `chialu/targets/rtl/families/decimal.py`.

## references

tsen_2007 -> Tsen, Gonzalez-Navarro, Schulte, "Hardware Design of a Binary Integer Decimal-Based Floating-Point Adder", IEEE International Conference on Computer Design (ICCD), 2007
cornea_2009 -> Cornea, Harrison, Anderson, Tang, Schneider, Gvozdev, "A Software Implementation of the IEEE 754R Decimal Floating-Point Arithmetic Using the Binary Encoding Format", IEEE Transactions on Computers, 2009
