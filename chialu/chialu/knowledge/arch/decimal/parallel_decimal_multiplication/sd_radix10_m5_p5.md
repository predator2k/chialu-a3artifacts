---
family: parallel_decimal_multiplication
pin: {multiplier_recoding: sd_radix10_m5_p5}
---
# sd_radix10_m5_p5

Signed-digit radix-10 recoding: each BCD multiplier digit maps to a
digit in [-5, 5], so a d-digit multiplier yields d+1 partial products,
each recoded digit selects one of 0X to 5X through a 5:1 mux, and
negative multiples come from bit inversion plus a hot one (a
corrective 1X row is the alternative when the leading digit exceeds
5). The multiples are precomputed in a code where 2X, 4X and 5X are
carry-free and only 3X needs a carry-propagate addition.

It is the pick when the reduction tree is the cost to minimize: d+1
rows is the fewest of any recoding, so the SD radix-10 multiplier is
the high-performance option with moderate area, about 0.65 the area
of the earlier parallel design at 1.15 times its speed in 90 nm. Its
limit is the 3X multiple, whose carry-propagate generation sets the
partial-product-generation latency; radix4_radix5_split avoids it with
only plus or minus X and 2X at the price of 2d rows and a larger tree,
and the XS-3 code makes 3X constant-time. With redundant [-8, 8]
internal digits the same recoding runs about 11 percent faster than
the radix-5 design at 2 percent less area.

## references

vazquez_2010 -> Vazquez, Antelo, Montuschi, "Improved Design of High-Performance Parallel Decimal Multipliers", IEEE Transactions on Computers, 2010
hickmann_2007 -> Hickmann, Krioukov, Schulte, Erle, "A Parallel IEEE P754 Decimal Floating-Point Multiplier", IEEE International Conference on Computer Design (ICCD), 2007
erle_2009 -> Erle, Hickmann, Schulte, "Decimal Floating-Point Multiplication", IEEE Transactions on Computers, 2009
han_2013 -> Han, Ko, "High-Speed Parallel Decimal Multiplication with Redundant Internal Encodings", IEEE Transactions on Computers, 2013
vazquez_2014 -> Vazquez, Antelo, Bruguera, "Fast Radix-10 Multiplication Using Redundant BCD Codes", IEEE Transactions on Computers, 2014
