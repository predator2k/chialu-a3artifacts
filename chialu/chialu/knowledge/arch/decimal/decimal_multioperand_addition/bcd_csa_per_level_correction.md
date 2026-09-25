---
family: decimal_multioperand_addition
pin: {reduction_style: bcd_csa_per_level_correction}
---
# bcd_csa_per_level_correction

The reduction tree is built from BCD full adders acting as 3-to-2
cells, each emitting an in-place BCD digit and a decimal carry to the
next position, so the decimal correction is applied inside every
level. First-level cells omit the carry-in because every partial
product is positive, and the decimal carries left unused are collected
off the critical path by (9:4) and (6:3) binary-to-BCD counters. A
Wallace-like organization emits one low BCD product digit after each
level.

Six levels reduce 32 operands to two, leaving six BCD digits resolved
and 26 double-BCD digits for a Kogge-Stone final adder; the modified
regular BCD-FA has a sum latency of 6.05 FO4 against 6.88 for the
earlier cell, and the 32-to-2 reduction of a 16-by-16-digit
multiplication takes 32.35 FO4 against 36.98 to 42.02 FO4 for the
compared trees in a static-CMOS logical-effort model (jaberipur_2009).
The early-digit trick holds because each cell emits an in-place BCD
digit and does not apply to the in-place 4221 reduction methods. The
style is the pick when low product digits should leave the tree early;
decimal_compressors in 4221/5211 codes is the alternative when
correction-free cells are wanted, and binary_tree_then_convert when
the operand count makes one root correction cheaper than BCD cells at
every level.

## references

jaberipur_2009 -> Jaberipur, Kaivani, "Improving the Speed of Parallel Decimal Multiplication", IEEE Transactions on Computers, 2009
