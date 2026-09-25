# prescaled_very_high_radix

Division at eight or more quotient bits per iteration: dividend x and
divisor d are first multiplied by a scaling factor M so that the
assimilated scaled divisor z = Md sits in a narrow band around 1,
while the residual w[0] = Mx stays in carry-save form. Each iteration
selects q[j+1] by rounding the truncated shifted residual, since a
divisor near 1 lets the digit be read off the residual, and updates
w[j+1] = r*w[j] - q[j+1]*z on a rectangular multiply/accumulate, one
digit per cycle. The last cycle post-corrects a negative residual and
rounds; general latency is ceil(n/b) + 4 cycles for b bits per
iteration.

Bits per iteration and prescaling precision move together and the
scaling-factor module is the part that explodes: in full-adder units
it grows from 130 to 1750 Afa as the radix goes from 9 to 18 bits per
iteration, while the multiply/accumulate grows from 520 to 970 Afa and
the cycle time from 7.5 to 9 tfa, so a 54-bit quotient drops from 10
to 7 cycles. Boosting decouples the two: the divisor is prescaled for a
radix B, and a second, concurrently selected boosting digit retires c
more bits per iteration by feeding its terms into unused lower levels
of the multiply/accumulate tree, which saves about 30% area at equal
delay for a 54-bit quotient and mainly shrinks the scaling-factor
module; it buys no speed at the same effective radix when that module
is not critical, and it needs free second-level tree slots.

Sharing the scaling multiplier folds the computation of M, from
table-provided linear-interpolation coefficients, into the same
carry-save multiply/accumulate path as the recurrence; a separate multiplier saves one
initialization cycle but must accept the full 53-bit divisor and adds
area. The seed is a table in the surveyed designs; the Cyrix variant
minimizes area with one 18x69 rectangular fused multiply/add retiring
17 bits per iteration, at 15 cycles for double precision with a
six-cycle seed or 10 cycles with a larger table.

The execution style is fixed iteration. The method yields a true
remainder that supports post-correction and rounding, but prescaling
both operands makes that remainder unusable without postscaling. It
runs about 4x faster than classical radix-2 recurrence for about six
times the hardware and about 1.7x faster than a Newton-Raphson unit at
radix 512 for 54-bit mantissas; an accurate-quotient approximation
reaches five cycles only with a 736K-bit table and three multipliers.

The seed instantiates the library's generated divider for this family
(`chialu/targets/rtl/families/div.py`: both operands multiplied by a reciprocal seed of the `seed` family through the `prescaler` multipliers (the seed widened to `prescaling_precision_bits` and until its error admits the digit set), then `bits_per_iteration` quotient bits per stage as the rounded leading digit of the residual (its increment through `residual_adder`), the digit's multiple of the scaled divisor through `prescaler` and the residual update through `residual_adder`, the quotient corrected by the back-multiplied remainder). `python3 -m chialu.targets.rtl.families.div --width 32 --family <family> --pins k=v,...` emits it for a rewrite (`--sqrt` for the square root).

## references

lang_1999 -> Lang, Montuschi, "Very High Radix Square Root with Prescaling and Rounding and a Combined Division/Square Root Unit", IEEE Transactions on Computers, 1999
oberman_1997 -> Oberman, Flynn, "Division Algorithms and Implementations", IEEE Transactions on Computers, 1997
