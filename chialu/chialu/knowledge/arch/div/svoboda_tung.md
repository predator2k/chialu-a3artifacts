# svoboda_tung

Digit-recurrence division without quotient-digit selection. A prescaler multiplies divisor and dividend by the same constant K until the divisor has the form 1 + e with e bounded, and each iteration R(j+1) = bR(j) - q(j+1)Y then takes the quotient digit straight from the leading digit of the signed-digit partial remainder, with no comparison of divisor multiples against the residual. Tung's form bounds e so that an overshooting trial digit is compensated in the next step. New Svoboda-Tung (NST) instead conditionally recodes the two leading residual digits r1 r2 into r1a r2a with b*r1a + r2a = b*r1 + r2 and takes q = r1a, which removes the compensation. The divisor stays nonredundant.

The family is fixed-iteration: the prescaler runs for a small operand-length-independent number of cycles and the recurrence for one radix-b digit per cycle, so at W = 53 a radix-4 recurrence needs W/2 cycles before quotient conversion. msd_recoding separates the two forms. Tung's original works with a minimally redundant digit set and a divisor error interval chosen so that a mistaken prospective digit corrects itself one step later; two_digit_recode is NST, whose recoding keeps the residual value and makes the leading digit directly usable as the quotient digit. Within NST the residual digit set bound α and the recoding threshold β name the design points: α changes the adder complexity, the divisor multiples, and the residual encoding, while β changes the quotient-selection complexity and the prescaled divisor range, which in turn fixes how many divisor bits the prescaler inspects. The mr point (α = 2, β = 1) is preferred at radix 4 because it avoids non-power-of-two divisor multiples, needs two rather than three prescaling cycles, and observes six residual bits; in an analytical gate-delay model at W = 53 it runs about 1.19x faster than the MROR point and 1.44x faster than prescaled regular radix-4, and in a 1-µm CMOS 32-bit combinational layout it takes 110 ns and 35.2 mm² against 117 ns and 39.5 mm² for MROR.

radix trades recurrence count against the prescaler and the digit set; the mutation raise_radix moves along it. The prescaler slot is a multiplier, and its cost is what the family pays for the removed selection logic, so the family wins for longer operands, where cheaper digit generation outweighs the preprocessing, and against SRT at the same radix in the analytical comparison. It loses wherever an unscaled remainder is required: both operands are scaled by the same K and the final residual is KR rather than R.

The seed instantiates the library's generated divider for this family
(`chialu/targets/rtl/families/div.py`: the prescaled recurrence (its own `seed` slot for the reciprocal seed, `prescaler` multipliers) with the digit as the truncated leading residual digit at the radix (no selection), or the rounded digit under `msd_recoding` two_digit_recode, the residual update through `residual_adder`, the quotient corrected by the back-multiplied remainder). `python3 -m chialu.targets.rtl.families.div --width 32 --family <family> --pins k=v,...` emits it for a rewrite (`--sqrt` for the square root).

## design choices

### msd_recoding

| member | what it selects |
| --- | --- |
| `none` | the leading residual digit is taken as the quotient digit, with the overflow compensation the method needs. |
| `two_digit_recode` | the NST recoding of the two leading digits, which removes that compensation. |

## references

tung_1968 -> Tung, "A Division Algorithm for Signed-Digit Arithmetic", IEEE Transactions on Computers, 1968
montalvo_1998 -> Montalvo, Parhi, Guyot, "New Svoboda-Tung Division", IEEE Transactions on Computers, 1998
