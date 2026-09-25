---
family: decimal_multioperand_addition
pin: {reduction_style: binary_tree_then_convert}
---
# binary_tree_then_convert

Each BCD digit column is reduced as plain binary by a logarithmic
carry-save tree, and the decimal correction is applied once at the
root. Dadda's scheme converts each column sum with a binary-to-decimal
converter, skews the digits by decimal weight into two to four major
partial sums and feeds a decimal CLA. Kenney's nonspeculative adder
derives a modulo-16 sum and a decimal carry correction from the
preliminary binary sum and applies them in a digit CPA and a decimal
lookahead adder.

Delay grows logarithmically in the operand count m, with roughly
floor(log3/2(m-1)) CSAs on the critical path, and the 32-bit
nonspeculative adder is lower delay than the speculative linear arrays
in a 0.18 um library, at 1.44 to 2.34 times the delay and 1.61 to 2.03
times the area of a binary tree adder for four to 16 operands
(kenney_2005). The correction logic grows with m, while the column
structures depend on the operand count N and the final decimal adder
only on the digit length n, so the style becomes especially applicable
for a large number of addends; its initial binary depth at N=16 is 6
stages against 14 for the compared nonspeculative tree (dadda_2007).
decimal_compressors is the pick when every level must hold a decimal
result, and bcd_csa_per_level_correction when a Wallace-like tree
should release low product digits early.

## references

dadda_2007 -> Dadda, "Multioperand Parallel Decimal Adder: A Mixed Binary and BCD Approach", IEEE Transactions on Computers, 2007
kenney_2005 -> Kenney, Schulte, "High-Speed Multioperand Decimal Adders", IEEE Transactions on Computers, 2005
