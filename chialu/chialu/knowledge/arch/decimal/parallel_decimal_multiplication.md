# parallel_decimal_multiplication

Decimal multiplication with every partial product generated at once:
the multiplier digits are recoded to a signed-digit set, radix-10
digits in [-5, 5] or a radix-5 split into 5 times {0, 1, 2} plus
[-2, 2], each digit selects a precomputed multiple through a mux,
negatives come from bit inversion plus a hot one, and a carry-save
tree reduces the d+1 or 2d rows to two words that a decimal CPA
resolves. The internal
digit code decides the tree: BCD-4221, 5211 or excess-3/ODDS make
every 4-bit pattern a valid digit, so binary CSAs and compressors
reduce decimal rows with a doubling or times-6 correction per level,
while BCD-8421 needs radix-10 carry-save cells and carry counters.

The recoding trades rows against multiple generation. Signed-digit
radix-10 gives the fewest rows but needs the 3X multiple, whose
carry-propagate generation sets the partial-product-generation
latency; the radix-5 split needs only plus or minus X and 2X with
fixed shifts for the factor five, so its generator is as fast as
binary Booth radix-4, but it doubles the rows and the worst column, so
at the minimum-delay point it is faster than radix-10 at greater area.
The digit code trades code conversions against tree cells: 4221 lets a
slightly modified binary CSA tree reduce the rows, XS-3 makes 3X
constant-time and negation a bit inversion while ODDS needs no
invalid-code correction in the tree, and 8421 keeps the operand code
but takes six levels of decimal carry-save adders for 16 digits.
Redundant internal encodings, signed digits in [-8, 8] or a
double-signed-digit set, reduce the rows with carry-free adders and
omit the final conversion when the product feeds a fused multiply-add
adder; an unsigned double-BCD basis of X, 2X, 5X, 8X and 9X removes
the negative rows at the cost of generator area.

The final_adder slot holds a decimal carry-propagate adder rather than
a binary one: a direct BCD adder with an interdigit prefix carry
network, a conditional-speculative quaternary tree computing 2H + S,
or a hybrid prefix converter partitioned by the per-column arrival
times of the tree. A column-wise reduction, each 4-bit column reduced
by a binary tree and then converted to units, tens and hundreds, is
the form that shares hardware with a binary multiplier.

The family wins on throughput and latency: one product per cycle,
about 7 times faster than a sequential decimal multiplier at 2.5 to 3
times its area in 90 nm, and it is the largest component of a decimal
fused multiply-add unit. It loses to binary on both axes, about 1.9
times the delay and 1.5 times the area of a radix-4 binary
double-precision multiplier at 16 digits, and the fully parallel
Decimal128 form is large enough that a sequential commercial
implementation is considered more realistic.

The seed instantiates the library's generated decimal multiplier for this family (`chialu/targets/rtl/families/decimal.py`: the multiplicand's multiples by digitwise doubling and quintupling and one addition each, the multiplier digits as they are, recoded to -5..5 or split into a radix-5 and a radix-2 part (`multiplier_recoding`), the rows from the multiples or from digit-product tables (`pp_generation`), reduced in BCD 8421 by decimal carry-save adders, in 4221 or 5211 by binary compressors with the carry word doubled by the code switch, in excess-3 with overloaded digits or as signed digits -8..8 (`internal_digit_code`), by a chain, a tree of 3:2, 4:2 or 7:3 cells or a tree of decimal adders (`reduction_tree`), then the final decimal adder (`final_adder`)). `python3 -m chialu.targets.rtl.families.decimal --digits 4 --kind multiplier --family parallel_decimal_multiplication` emits it for a rewrite.

## design choices

### internal_digit_code

| member | what it selects |
| --- | --- |
| `bcd8421` | the plain BCD weights, so the tree carries decimal digits. |
| `bcd4221` | the 4221 weights, in which a binary carry-save adder is a decimal one. |
| `bcd5211` | the 5211 weights, which the generator builds from its own code table; doubling a 4221 word lands in this code. |
| `xs3_odds` | excess-3 digits, whose nines' complement is the bit inversion. |
| `sd_m8_p8_posibit_negabit` | signed digits from -8 to 8 as a posibit and negabit pair, which the tree carries in five bits per digit. |

### multiplier_recoding

| member | what it selects |
| --- | --- |
| `sd_radix10_m5_p5` | the multiplier digits recoded to -5 through 5, so the multiples 1 to 5 suffice. |
| `radix4_radix5_split` | the digit split into a radix-4 and a radix-5 part, whose multiples are 1, 2, 5 and 10. |
| `none` | no recoding, so every multiple from 1 to 9 is generated. |

### pp_generation

| member | what it selects |
| --- | --- |
| `precomputed_multiples_mux` | the multiples of the multiplicand are precomputed once and a multiplexer picks one per digit. |
| `digit_by_digit` | a table gives each digit product as a tens and units pair, which is two rows per multiplier digit and no precomputed multiples. |

## references

hickmann_2007 -> Hickmann, Krioukov, Schulte, Erle, "A Parallel IEEE P754 Decimal Floating-Point Multiplier", IEEE International Conference on Computer Design (ICCD), 2007
erle_2009 -> Erle, Hickmann, Schulte, "Decimal Floating-Point Multiplication", IEEE Transactions on Computers, 2009
lang_2006 -> Lang, Nannarelli, "A Radix-10 Combinational Multiplier", 40th Asilomar Conference on Signals, Systems and Computers, 2006
vazquez_2010 -> Vazquez, Antelo, Montuschi, "Improved Design of High-Performance Parallel Decimal Multipliers", IEEE Transactions on Computers, 2010
vazquez_2014 -> Vazquez, Antelo, Bruguera, "Fast Radix-10 Multiplication Using Redundant BCD Codes", IEEE Transactions on Computers, 2014
han_2013 -> Han, Ko, "High-Speed Parallel Decimal Multiplication with Redundant Internal Encodings", IEEE Transactions on Computers, 2013
jaberipur_2009 -> Jaberipur, Kaivani, "Improving the Speed of Parallel Decimal Multiplication", IEEE Transactions on Computers, 2009
gorgin_2009 -> Gorgin, Jaberipur, "Fully Redundant Decimal Arithmetic", 19th IEEE Symposium on Computer Arithmetic (ARITH-19), 2009
