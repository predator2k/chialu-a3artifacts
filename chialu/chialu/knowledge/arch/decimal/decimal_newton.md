# decimal_newton

Newton-Raphson reciprocal refinement on a decimal multiplier: a seed
reciprocal comes from a table indexed by the leading divisor digits
and multiplied by a modified divisor, each iteration computes
R(i+1) = R(i) x (2 - X x R(i)) with two decimal multiplications and a
nine's complement in place of the subtraction, so the accurate digits
double per iteration, and a final multiplication by the dividend
yields the quotient. Rounding is settled by a back-multiplied remainder
whose sign and zero status pick the result, or by extra quotient
guard digits. Square root iterates
R(i+1) = R(i)/2 x (3 - X x R(i)^2) with three multiplications and a
halving, and X - Q^2 selects the rounded root.

operation decides how much of the datapath is shared: the divide and
square-root forms run seed generation, refinement, final product and
the rounding product through one decimal multiplier, and the
third-order update, which triples rather than doubles the digits,
buys fewer iterations with more multiplications each. seed_digits
and iterations trade table size against iteration count: three seed
digits give three iterations at decimal64, four seed digits give two
but grow the table from 2.5 KB to 54 KB, and against the additive
POWER6 divider a 0.5 KB, 12 KB or 256 KB seed table gave 190, 152 or
128 cycles at decimal64 where the shipped recurrence took 82. The
seed slot is an operand-modification multiply in the evaluated
designs; the final_round slot is the back-multiplied remainder or
extra-precision guard digits.

The multiplier sets the latency: at decimal64 with three seed digits
a sequential one-digit-per-cycle multiplier gives 150 cycles, four
digits per cycle 80, and a three-cycle parallel multiplier 37, and
the multiplier block is about two thirds of the logic area.
Intermediate precision is progressively widened so early
multiplications use the minimum digits the current accuracy needs,
and the iteration products are truncated with directed intermediate
rounding that keeps the reciprocal below the exact value, so the
final selection among Q, Q + 10^-n and Q - 10^-n from the guard
digit and remainder test is correctly rounded in the five IEEE modes
plus round-to-nearest-toward-zero and away. The family is fixed
iteration: the count follows from seed digits and format. It wins
over one-digit-per-iteration recurrence at wide formats, where
doubling pays most, and loses under a decimal multiplier costly
enough that the prescaled additive recurrence is faster, as the
POWER6 designers concluded. Convergence needs a seed between 0 and
2/x.

The seed instantiates the library's generated decimal divider for this family (`chialu/targets/rtl/families/decimal.py`: the reciprocal seed from a table over the normalized divisor's leading digits (`seed_digits`, at most three), the iterations x(2 - bx) on decimal products at D + 3 fraction digits with their count sized by the seed's error bound (`iterations` is raised when the bound needs more), the quotient estimate a x with the back-multiplied remainder and a one-unit correction, or the estimate at 2D + 3 fraction digits biased into the gap below the next integer for the exclusion-zone roundings (`final_round`); the products are behavioral decimal products left to synthesis, and a BCD mode has no square root op, so the divide path alone is built). `python3 -m chialu.targets.rtl.families.decimal --digits 4 --kind divider --family decimal_newton` emits it for a rewrite.

## references

richards_1955 -> Richards, "Arithmetic Operations in Digital Computers", Van Nostrand, 1955
wang_2004 -> Wang, Schulte, "Decimal Floating-Point Division Using Newton-Raphson Iteration", IEEE ASAP, 2004
wang_2005 -> Wang, Schulte, "Decimal Floating-Point Square Root Using Newton-Raphson Iteration", IEEE ASAP, 2005
schwarz_2007 -> Schwarz, Carlough, "Power6 Decimal Divide", IEEE ASAP, 2007
