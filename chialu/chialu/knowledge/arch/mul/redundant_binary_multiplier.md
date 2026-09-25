# redundant_binary_multiplier

Parallel multiplication with partial products summed as redundant
binary digits in {-1, 0, 1}: each partial product is formed or
converted into signed-digit form, as a plus/minus signal pair per
digit or a sign and magnitude bit, pairs of redundant numbers are
added by a constant-depth redundant binary adder whose two-step digit
addition looks only at a bounded set of neighbouring digits, so a
binary tree of log2 of the row count levels reduces every row with no
carry propagation, and one converter turns the final signed-digit word
into two's complement. Booth recoding halves the rows first, and two
adjacent binary rows, one inverted plus a negative digit, form one
redundant row for free.

The family trades wiring for regularity. Its depth matches the
Wallace tree, 27 against 28 computation elements at 16 bits with
fewer gates, and grows as log n where the array grows linearly, so a
32-bit tree is about four times faster than an array in the
bounded-fan-in model; the layout is a repeated cell pattern like an
array's, in a V-shaped tree with one-directional signal flow, but the
two-wire digits give about twice the signal lines of a conventional
multiplier, a chip-area order of n^2 log n and a transistor count
between array and Wallace. rb_encoding sets what the sign costs: with
a plus/minus pair a negative Booth product needs neither an added one
nor sign terms and the RBA cell of inverters, two-input NANDs and
transmission gates adds faster than a normal-binary cell once each
(1, 1) state is normalized, while the sign-magnitude code goes with
paired Booth groups. booth_radix sets the row count: radix 4 gives
n/2 rows, pairing adjacent radix-4 groups and subtracting the two
multiples gives n/4 signed-digit rows, which puts a 64-bit design at
90 percent of the path and 75 percent of the transistors of Booth
plus Wallace, and binding two encoders into an
opposite-polarity dipole gives one row per four multiplier bits with
no correction vector at all; a radix-8 sign-digit tree is what the
TI SPARC coprocessor built. rbnb_converter is the last third of the
path: a modified lookahead adder, a carry-select chain of increasing
group widths whose propagation is multiplexers only, or on-the-fly
conversion.

The reference point is the 54x54 design at 8.8 ns in 0.5 um with
78,800 transistors, fewer than its conventional rivals, 2.3 ns of it partial-product generation, 3.8 ns the
four-stage tree and 2.7 ns the 80-bit conversion, at 38 percent less
estimated power. The family wins where a Wallace tree's irregular
wiring is the problem and a cellular layout is wanted at the same
depth, and loses on wiring tracks and on the converter; the product
is exact and no error or fault contract is reported.

The seed instantiates the library's module for this family
(`chialu/targets/rtl/families/mul_ext.py`: AND rows, radix-2 Booth rows (+a or -a per multiplier bit pair) or radix-4 Booth rows as plus/minus digit rows, a binary tree of carry-free redundant adders (the two-step rule keyed on the lower digit's sign), the plus word less the minus word through the `final_converter` adder family, a carry-select adder, or the on-the-fly digit conversion; the sign-magnitude and NP codes recode at the cell boundary).

As the `representation` of a `redundant_internal` core the family names the lane's multiplier: the seed builds it from this generator with the representation slot's pins (`chialu/targets/rtl/families/redundant.py` routes it to `mul_ext.redundant_binary_sv`).

## design choices

### booth_radix

| member | what it selects |
| --- | --- |
| `none` | the rows are the plain partial products. |
| `2` | radix-2 Booth recoding. |
| `4` | radix-4 Booth recoding. |

### rb_encoding

| member | what it selects |
| --- | --- |
| `sign_magnitude_2bit` | the digit as a sign bit and a magnitude bit. |
| `plus_minus_pair` | the digit as its positive and negative bits. |
| `np_coding` | the digit as the complements of those bits, so the cells' inverters fold into the code. |

### rbnb_converter

| member | what it selects |
| --- | --- |
| `cpa` | the redundant result is converted by a carry-propagate adder. |
| `carry_select` | the conversion is a carry-select adder. |
| `on_the_fly` | the conversion keeps the word and its decrement and selects, so no carry propagates. |

## references

takagi_1985 -> Takagi, Yasuura, Yajima, "High-Speed VLSI Multiplication Algorithm with a Redundant Binary Addition Tree", IEEE Transactions on Computers, 1985
harata_1987 -> Harata, Nakamura, Nagase, Takigawa, Takagi, "A High-Speed Multiplier Using a Redundant Binary Adder Tree", IEEE Journal of Solid-State Circuits, 1987
makino_1996 -> Makino, Nakase, Suzuki, Morinaka, Shinohara, Mashiko, "An 8.8-ns 54x54-bit Multiplier with High Speed Redundant Binary Architecture", IEEE Journal of Solid-State Circuits, 1996
kuninobu_1987 -> Kuninobu, Nishiyama, Edamatsu, Taniguchi, Takagi, "Design of High Speed MOS Multiplier and Divider Using Redundant Binary Representation", 8th IEEE Symposium on Computer Arithmetic, 1987
he_chang_2009 -> He, Chang, "A New Redundant Binary Booth Encoding for Fast 2^n-Bit Multiplier Design", IEEE Transactions on Circuits and Systems I, 2009
darley_1990 -> M. Darley, B. Kronlage, D. Bural, B. Churchill, D. Pulling, P. Wang, et al., "The TMS390C602A Floating-Point Coprocessor for Sparc Systems", IEEE Micro, vol. 10, no. 3, pp. 36-47, 1990.
