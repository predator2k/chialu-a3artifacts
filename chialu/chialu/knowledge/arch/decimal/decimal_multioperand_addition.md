# decimal_multioperand_addition

Reduction of many BCD operands to one carry-save pair ahead of one
decimal carry-propagate adder. A radix-10 carry-save cell takes two BCD
digits plus a carry bit and emits one BCD digit and one carry bit, with
the decimal correction inside every cell; recoding the digits into a
weight-sum-nine code (4221 or 5211) lets plain 4-bit binary 3:2 CSAs
produce valid decimal digits with no correction, a recoder and wired
shift doubling the carry operand; or a binary CSA tree reduces
each digit column and the correction (6 per binary carry that crosses
the 4-bit digit boundary, or a binary-to-decimal conversion of the
column sum) is applied once at the root before a decimal
carry-lookahead adder.

The reduction style trades per-cell correction against root
complexity. A BCD full-adder tree pays correction in every cell but
emits one resolved digit per level in Wallace fashion; the coded 4221
and 5211 trees remove correction altogether and cut delay by at least
45% against a BCD tree adder with about 10% less hardware. Binary
reduction then conversion has logarithmic delay, but its correction
logic is specific to the operand count and grows with it, landing at
1.44 to 2.34x the delay and 1.61 to 2.03x the area of a plain binary
tree adder for four to 16 operands in 0.18 um CMOS; counting the
inter-digit carries concurrently with the tree keeps that correction
off the reduction path. Speculative linear chains assume the first one
or two additions need no correction and select ai or ai+6 by the
previous carry, so delay grows linearly in the operand count;
two-addition speculation moves the multiplexers off the critical path,
further speculation gains nothing, and the final 0/6/12 correction is
independent of operand count, which suits iterative designs with
variable counts.

Compressor arity sets tree depth. A decimal 4:2 built from two 3:2
counters takes two BCD digits and two carry bits (sum up to 20); a
4221-coded 4:2 whose carry-out ignores carry-in gives log4(n) levels
and beats counter trees on delay as the operand count grows at a small
area cost; digit counters of 9:4, 8:4 or 7:3 form area-optimized or
delay-optimized trees that differ by about 5% delay for 10% area.
Carry bits the first level leaves behind go through radix-10 carry
counters (eight bits to one digit) or binary-to-BCD counters kept off
the critical path.

The root adder is a decimal carry-lookahead or prefix adder whose
delay depends on digit count, while the tree depends on operand count.
The family is the partial-product reducer of parallel decimal
multipliers and pays off for large addend counts; four operands fit a
two-stage ROM array with the same twelve arrays as binary addition.

The seed instantiates the library's generated decimal adder for this family (`chialu/targets/rtl/families/decimal.py`: the two operands and the carry-in word as three operands through one decimal 3:2 level with the correction per level or at the root, binary column sums converted at the root, decimal 4:2 compressors, or binary compressors on digits recoded to 4221 with the carry word doubled through the 5211 code (`reduction_style`, `compressor_arity`, `correction_placement`), then the root adder over the `root_adder` family). `python3 -m chialu.targets.rtl.families.decimal --digits 4 --kind adder --family decimal_multioperand_addition` emits it for a rewrite.

## design choices

### column_sum

| member | what it selects |
| --- | --- |
| `two_input_adders` | each digit column is summed by two binary two-input adders. |
| `compressor_and_adder` | each digit column is summed by a 3:2 compressor and one binary adder. |

### complement_generation

| member | what it selects |
| --- | --- |
| `subtract_from_power` | the nines' complement of a digit as the subtraction 9 - d. |
| `nines_digitwise_plus_one` | the same complement as a bit formula over the digit's four bits. |
| `trailing_zero_scan` | the tens' complement directly, the first nonzero digit found by a prefix scan. |

### compressor_arity

| member | what it selects |
| --- | --- |
| `3_to_2` | decimal 3:2 compressors, one carry word per level. |
| `4_to_2` | decimal 4:2 compressors: a horizontal carry leaves a digit at twenty, a vertical carry at ten. |
| `higher` | an arity above four, which the generator reduces as binary column sums with one decimal conversion at the root. |

### reduction_style

| member | what it selects |
| --- | --- |
| `bcd_csa_per_level_correction` | decimal carry-save adders whose +6 correction is applied at every level. |
| `binary_tree_then_convert` | binary column sums that keep carries inside a digit, with one decimal conversion chain at the root. |
| `decimal_compressors` | compressors that work in the decimal domain directly, at the arity the compressor choice names. |
| `signed_digit_binary_compressors` | the digits in the 4221 code, where a bitwise binary 3:2 compressor serves and the carry word is doubled through the 5211 recoding and a shift. |

## references

kenney_2005 -> Kenney, Schulte, "High-Speed Multioperand Decimal Adders", IEEE Transactions on Computers, 2005
vazquez_2010 -> Vazquez, Antelo, Montuschi, "Improved Design of High-Performance Parallel Decimal Multipliers", IEEE Transactions on Computers, 2010
dadda_2007 -> Dadda, "Multioperand Parallel Decimal Adder: A Mixed Binary and BCD Approach", IEEE Transactions on Computers, 2007
lang_2006 -> Lang, Nannarelli, "A Radix-10 Combinational Multiplier", 40th Asilomar Conference on Signals, Systems and Computers, 2006
castellanos_2008 -> Castellanos, Stine, "Compressor Trees for Decimal Partial Product Reduction", 18th ACM Great Lakes Symposium on VLSI (GLSVLSI), 2008
erle_2003 -> Erle, Schulte, "Decimal Multiplication Via Carry-Save Addition", IEEE ASAP, 2003
jaberipur_2009 -> Jaberipur, Kaivani, "Improving the Speed of Parallel Decimal Multiplication", IEEE Transactions on Computers, 2009
vazquez_2014 -> Vazquez, Antelo, Bruguera, "Fast Radix-10 Multiplication Using Redundant BCD Codes", IEEE Transactions on Computers, 2014
