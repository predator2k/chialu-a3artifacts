---
family: decimal_multioperand_addition
pin: {correction_placement: per_level}
---
# per_level

Every reduction level leaves a valid decimal digit vector, so no root
conversion is needed. The BCD-full-adder form corrects inside each
3-to-2 cell and passes a decimal carry to the next position. The
4221/5211 form recodes the carry vector to BCD-5211 and shifts it so
that the doubled operand returns to BCD-4221 with its 10-weight bit
passed to the next decimal column, and two such stages form a decimal
4:2 compressor whose carry-out does not depend on its carry-in.

Per-level placement gives regular trees of log4(n) levels whose
compressors beat comparable counter trees in delay as operand size
grows, with a small area overhead and a regular structure meant for
custom VLSI (castellanos_2008). A BCD-FA tree can emit one low product
digit after each level because each cell produces an in-place BCD
digit, which the in-place 4221 methods cannot do, and its 32-to-2
reduction takes 32.35 FO4 against 36.98 to 42.02 FO4 for the compared
trees (jaberipur_2009). Every cell carries its own correction, so
at_root wins when the operand count is large and one correction after
a plain binary tree is cheaper; per_level is the pick when the levels
must stay decimal, for a Wallace-like early-digit tree or a regular
compressor layout.

## references

castellanos_2008 -> Castellanos, Stine, "Compressor Trees for Decimal Partial Product Reduction", 18th ACM Great Lakes Symposium on VLSI (GLSVLSI), 2008
jaberipur_2009 -> Jaberipur, Kaivani, "Improving the Speed of Parallel Decimal Multiplication", IEEE Transactions on Computers, 2009
