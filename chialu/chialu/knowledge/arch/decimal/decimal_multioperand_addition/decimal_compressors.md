---
family: decimal_multioperand_addition
pin: {reduction_style: decimal_compressors}
---
# decimal_compressors

The operands are reduced by decimal carry-save cells. A radix-10 CSA
takes two BCD digit vectors plus a carry-bit vector and returns one
BCD digit vector and one carry-bit vector, and a tree of them holds a
decimal result at every level. In the weight-sum-nine codes 4221 and
5211, plain binary 3:2 CSAs yield valid decimal digits with no
correction, recoders plus wired shifts double the carry operand, and
two such stages form a decimal 4:2 compressor with carry-out
independent of carry-in.

The compressor tree has log4(n) levels for column height n and beats
comparable counter trees in delay as operand size grows, at a small
area cost (castellanos_2008). The 4221/5211 p:2 trees with 9:4, 8:4
and 7:3 bit-counter rows give at least 45% less delay and about 10%
less hardware than an earlier decimal tree adder in a logical-effort
model, and a delay-optimized version is 5% faster for 10% more area
(vazquez_2010). A radix-10 CSA tree leaves the first-level carry
vectors unaccounted for, so radix-10 carry counters that turn eight
equal-weight carry bits into one digit are required (lang_2006). A
direct-decimal cell acts as a decimal 3:2 counter, and two of them make
a decimal 4:2 compressor (erle_2003). The style is the pick for
high-performance partial-product reduction at moderate area;
binary_tree_then_convert wins when the operand count is large enough
that one root correction is cheaper than decimal cells at every level.

## references

castellanos_2008 -> Castellanos, Stine, "Compressor Trees for Decimal Partial Product Reduction", 18th ACM Great Lakes Symposium on VLSI (GLSVLSI), 2008
vazquez_2010 -> Vazquez, Antelo, Montuschi, "Improved Design of High-Performance Parallel Decimal Multipliers", IEEE Transactions on Computers, 2010
lang_2006 -> Lang, Nannarelli, "A Radix-10 Combinational Multiplier", 40th Asilomar Conference on Signals, Systems and Computers, 2006
erle_2003 -> Erle, Schulte, "Decimal Multiplication Via Carry-Save Addition", IEEE ASAP, 2003
