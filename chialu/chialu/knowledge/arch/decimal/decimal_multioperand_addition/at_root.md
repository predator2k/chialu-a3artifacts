---
family: decimal_multioperand_addition
pin: {correction_placement: at_root}
---
# at_root

The digit columns are reduced as plain binary and the decimal
correction is applied once, at the final adder. The correction is
derived from the preliminary binary sum as a modulo-16 sum and a
decimal carry correction per digit, produced by a per-column binary-
to-decimal converter, or computed concurrently: a counter tallies the
binary carries Wi crossing each 4-bit digit boundary while the tree
runs, and Wi times 6 repairs the gap between binary weight 16 and
decimal weight 10.

Root correction keeps the reduction levels as plain binary cells, so
the tree depth is that of a binary CSA tree, but the correction logic
grows with operand count and the 32-bit nonspeculative adder costs 1.44
to 2.34 times the delay and 1.61 to 2.03 times the area of a binary
tree adder for four to 16 operands (kenney_2005). The concurrent
carry-count form needs one correction digit for Decimal64 and two for
Decimal128 and reaches 25.5 FO4 for a 16 x 16-digit PPR tree in a
logical-effort model (vazquez_2014). A column adder at N=16 has 6
compression stages before its converter (dadda_2007), and in a ROM
array adder the decimal correction folds into the second array stage
at no extra array count (schmookler_1972). Root placement is the pick
when the operand count is large; per_level wins when every level must
hold a decimal result, as in a Wallace-like early-digit tree.

## references

kenney_2005 -> Kenney, Schulte, "High-Speed Multioperand Decimal Adders", IEEE Transactions on Computers, 2005
vazquez_2014 -> Vazquez, Antelo, Bruguera, "Fast Radix-10 Multiplication Using Redundant BCD Codes", IEEE Transactions on Computers, 2014
dadda_2007 -> Dadda, "Multioperand Parallel Decimal Adder: A Mixed Binary and BCD Approach", IEEE Transactions on Computers, 2007
schmookler_1972 -> Schmookler, "Considerations in the Design of a High Speed Decimal Unit", 2nd IEEE Symposium on Computer Arithmetic (ARITH-2), 1972
