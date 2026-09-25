---
family: speculative_decimal_addition
pin: {speculation_target: both}
---
# both

Digit correction and rounding increment are speculated together in one
pass: a binary 3:2 carry-save pre-correction forms Ops/Opc with the
conditional +6 bias through Gi and feeds a modified binary compound
adder returning S* and SI* = S*+2; post-correction yields S^H, SI^H
and the complement of S^H, direct combinational rounding conditions
compute inc1/inc2 for each mode, and a final selection picks the
correctly rounded sign-magnitude BCD result with no further carry
propagation.

The hand estimates from a static-CMOS logical-effort model give 26.1
FO4 and 3580 NAND2 for decimal64 against 30.3 FO4 and 4490 NAND2 for
the Wang-Schulte injection adder, and 29.1 FO4 and 7800 NAND2 against
32.2 FO4 and 9950 NAND2 for decimal128, without gate-sizing
optimization. The datapath has five stages, a (4p-1)-bit compound
adder with a 63-bit Kogge-Stone tree at decimal64, and a rounding
modification whose delay is a small constant independent of digit
count; it covers the five IEEE modes plus round-to-nearest-down and
away-from-zero. Against the rounding_increment sibling it drops the
flagged trailing-nine logic and the second injection correction by
taking the increment from the compound adder's +2 output; against
digit_correction it adds fused rounding. It is the pick for a DFP
significand adder built on a compound_flagged_prefix carry network.

## references

vazquez_2009 -> Vazquez, Antelo, "A High-Performance Significand BCD Adder with IEEE 754-2008 Decimal Rounding", 19th IEEE Symposium on Computer Arithmetic (ARITH-19), 2009
