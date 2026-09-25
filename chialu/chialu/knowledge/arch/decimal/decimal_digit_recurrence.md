# decimal_digit_recurrence

Radix-10 digit recurrence for division: each iteration forms
w[j+1] = 10 w[j] - q[j+1] d, selects one decimal quotient digit from a
few leading digits of the partial remainder and divisor, and retires
one digit, so a p-digit quotient takes about p iterations plus
prescaling, conversion and rounding cycles. The quotient digit set
fixes the selection: 0 to 9 by repeated subtraction or nine parallel
compares; -5 to 5 by reading the most significant remainder digit once
the divisor is prescaled into 1.0 to 1.1; -7 to 7 by splitting the
digit as q = 5 qH + qL so that only d, 2d and 5d multiples are needed
and two conditional add/subtract steps form each digit.

The digit set trades divisor multiples against selection work. A
nonredundant set is the restoring or nonrestoring textbook recurrence:
subtract-and-restore averages 6.3 operations per digit, doubling and
quintupling circuits bring that to 3.4, and nine parallel comparisons
reach one operation per digit at the cost of nine comparators and all
generated multiples. The split redundant set of -7 to 7 needs one
sequential decimal adder, no stored multiples beyond d, and averages
2.33 operations per digit with three-digit selection when the divisor
is standardized; its BCD form keeps 5d and 2d precomputed, runs the
most significant slice in radix-2 two's complement, and takes 20
cycles. A maximally redundant set with a signed-digit residual selects
by nine truncated comparisons and concurrent sign detection, and is
optimized for speed at the expense of area. The minimally redundant
set with prescaling is the POWER6 and z10 choice: the digit is the
most significant partial-remainder digit, a 32 KB selection table
becomes a 256-byte prescale table, and decimal64 and decimal128 take
82 and 154 cycles against 207 and 423 for restoring division at four
cycles per digit.

Prescaling costs 6 to 19 startup cycles and a two-digit reciprocal
table but removes the selection table from the loop; two partial
remainders PA and PB per iteration let stored multiples 1 to 5 also
produce 6 to 9. Digit splitting removes the multiples instead, at two
adder passes per digit through one shared doubling/quintupling
circuit. The digit-select slot is a table, a bank of comparison
multiples, or the direct digit read.

The family is fixed-iteration and wins because decimal addition is far
cheaper than decimal multiplication: the subtractive divider is
shorter in FO4 latency than the Newton-Raphson decimal dividers it is
compared against, and the exact remainder gives correct rounding with
one extra iteration and a sign and zero test. The mainframe lineage
runs from a millicode loop around a one-digit hardware assist, through
the z900 full-hardware restoring divider, to the prescaled units. A
redundant-adder residual is the fastest variant reported but needs
more area.

The seed instantiates the library's generated decimal divider for this family (`chialu/targets/rtl/families/decimal.py`: one radix-10 quotient digit per unrolled stage; the nonredundant digits by comparison against the divisor's multiples, split into a radix-2 and a radix-5 comparison under `digit_split`; the redundant sets -5..5 and -7..7 by rounding the residual estimate after the divisor is prescaled near one by table factors from its leading digits (one stage for -7..7, two for -5..5), the signed digits converted at the end and the remainder from the back-multiplied quotient; the prescaling and back-multiply products are behavioral decimal products left to synthesis; the radix-16 runtime mode is outside the module). `python3 -m chialu.targets.rtl.families.decimal --digits 4 --kind divider --family decimal_digit_recurrence` emits it for a rewrite.

## design choices

### digit_split

| member | what it selects |
| --- | --- |
| `none` | the quotient digit is selected whole. |
| `radix2_times_radix5` | the radix-10 digit is selected as a radix-2 and a radix-5 part, which shortens the selection; a redundant digit set selects by rounding the residual estimate and does not take the split. |

## references

richards_1955 -> Richards, "Arithmetic Operations in Digital Computers", Van Nostrand, 1955
robertson_1958 -> Robertson, "A New Class of Digital Division Methods", IRE Transactions on Electronic Computers, 1958
schwarz_2007 -> Schwarz, Carlough, "Power6 Decimal Divide", IEEE ASAP, 2007
nikmehr_2006 -> Nikmehr, Phillips, Lim, "Fast Decimal Floating-Point Division", IEEE Transactions on Very Large Scale Integration (VLSI) Systems, 2006
lang_2007b -> Lang, Nannarelli, "Combined Radix-10 and Radix-16 Division Unit", 41st Asilomar Conference on Signals, Systems and Computers, 2007
schwarz_2009 -> Schwarz, Kapernick, Cowlishaw, "Decimal Floating-Point Support on the IBM System z10 Processor", IBM Journal of Research and Development, 2009
carlough_2011 -> Carlough, Collura, Mueller, Kroener, "The IBM zEnterprise-196 Decimal Floating-Point Accelerator", 20th IEEE Symposium on Computer Arithmetic (ARITH-20), 2011
busaba_2001 -> Busaba, Krygowski, Li, Schwarz, Carlough, "The IBM z900 Decimal Arithmetic Unit", 35th Asilomar Conference on Signals, Systems and Computers, 2001
