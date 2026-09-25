---
family: redundant_decimal_addition
pin: {digit_set: rbcd_m7_p7}
---
# rbcd_m7_p7

Redundant BCD with digits in [-7, 7]: each digit is a 4-bit
two's-complement code, so negation is complement plus one, and the
position sum of two digits splits into a transfer in {-1, 0, 1} and an
interim digit in [-6, 6] that absorbs the transfer from below, so no
carry travels past the adjacent position. The RBCD slice is two 4-bit
binary adders and two small PLAs; the DSSD slice forms the position sum
in carry-save form and finishes the digit with overlapping 2-bit and
1-bit additions.

The [-7, 7] set is the pick when a redundant decimal digit must fit in
the four bits of a nonredundant one: addition delay is constant with
digit count, 18 gate delays for RBCD against 7n for a conventional BCD
adder, about 6x at 15 digits, and the one-digit silicon area is stated
as equivalent to BCD. The DSSD refinement of the same digit set is 9
logic levels, 7.80 FO4 against 13.56 for RBCD, and synthesizes at 0.87
ns and 622 area units against 1.22 ns and 668 in TSMC 0.13 um, 40%
faster than the fastest previous design. Conversion is paid once for
repeated arithmetic on internally redundant data but makes a single BCD
and RBCD operation almost equivalent in cycle count, and the
two's-complement encoding is what the Svoboda 5-bit sibling lacks.

## references

shirazi_1989 -> Shirazi, Yun, Zhang, "RBCD: Redundant Binary Coded Decimal Adder", IEE Proceedings E - Computers and Digital Techniques, 1989
gorgin_2009 -> Gorgin, Jaberipur, "Fully Redundant Decimal Arithmetic", 19th IEEE Symposium on Computer Arithmetic (ARITH-19), 2009
