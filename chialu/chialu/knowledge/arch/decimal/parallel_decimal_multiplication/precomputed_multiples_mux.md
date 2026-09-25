---
family: parallel_decimal_multiplication
pin: {pp_generation: precomputed_multiples_mux}
---
# precomputed_multiples_mux

Partial products selected from precomputed multiplicand multiples: a
small set such as 1X to 5X, plus or minus X and 2X, or X, 2X, 5X, 8X
and 9X is generated once, each recoded multiplier digit drives a mux
that picks one multiple (or two equally weighted components) per row,
and the sign is applied by bit inversion plus a hot one or avoided by
an unsigned double-BCD basis that needs no negative rows.

It is the pick for every parallel decimal multiplier in the evidence,
because the multiple set fixes both the generator's latency and the
row count: 1X to 5X with signed-digit radix-10 recoding gives d+1 rows
but a carry-propagate 3X, plus or minus X and 2X with the radix-5
split gives 2d rows at Booth-radix-4 generator speed, and the
double-BCD basis removes negative partial products at the cost of two
components per digit and more generator area, about 15 percent over
the 4221 design by logical effort. The alternatives are direct
digit-product lookup, which removes doublers and quintuplers but
leaves the multioperand addition, and digit-by-digit selection whose
details the evidence does not disclose.

## references

vazquez_2010 -> Vazquez, Antelo, Montuschi, "Improved Design of High-Performance Parallel Decimal Multipliers", IEEE Transactions on Computers, 2010
jaberipur_2009 -> Jaberipur, Kaivani, "Improving the Speed of Parallel Decimal Multiplication", IEEE Transactions on Computers, 2009
schmookler_1972 -> Schmookler, "Considerations in the Design of a High Speed Decimal Unit", 2nd IEEE Symposium on Computer Arithmetic (ARITH-2), 1972
hickmann_2007 -> Hickmann, Krioukov, Schulte, Erle, "A Parallel IEEE P754 Decimal Floating-Point Multiplier", IEEE International Conference on Computer Design (ICCD), 2007
