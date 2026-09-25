# back_multiply_remainder

Final rounding of a multiplicative division by an exact residual:
once the quotient approximation Q is within one ulp of a/b, one
fused multiply-accumulate computes R = A - B*Q exactly, because the
full double-length product participates in the addition, and a
second fused operation Q' = Q + R*Y, with Y an approximate
reciprocal, selects Q or its adjacent representable value through
the requested rounding mode without a conditional correction branch.
The sign and zero test of the residual say which side of Q holds the
exact quotient and set the exact/inexact status; the decimal
square-root form selects among three candidates by an action table
on a guard digit and the remainder sign.

The number of quotient candidates trades multiplexing against
fused operations: two candidates come for free from the second
fused operation, and three candidates (the truncated trial result
and its neighbours at plus or minus one unit in the last place)
serve directed rounding modes through the action table when the
trial result is biased and truncated. The reciprocal requirement is
the other tunable: the original theorem asks for a correctly rounded
reciprocal Y, and the strengthened one only for a relative error
below 1/2^p, so Y need not be perfectly rounded. The K7 form
compares the product of the quotient candidate and the divisor
against the dividend and requires the approximation to meet a
precision-dependent relative-error bound first.

The contract is a correctly rounded IEEE result in every rounding
mode with correct inexact-flag behaviour; exact representable cases
and directed modes are handled separately in the SIMD proof, and the
residual is exactly representable only under the stated format,
range and normalization hypotheses with the 1-ulp precondition. The
family wins on any machine with a fused multiply-add, where it
replaced a compare followed by conditional branches that cost as
much as 15 cycles on the RISC System/6000 pipeline, and it is the
closing step of Newton-Raphson and Goldschmidt dividers and square
roots whose seeds keep the approximation on one side of the exact
value. The proof-based sibling removes even the residual operations
by bounding the distance to every rounding boundary.

The seed instantiates the library's generated divider for this family
(`chialu/targets/rtl/families/div.py`: the estimate within two units of the quotient (one under `quotient_candidates` 2), q b back-multiplied over the full product or its low bits alone (`product_bits`), the remainder's sign and size selecting among the candidates through the `correction_adder` family). `python3 -m chialu.targets.rtl.families.div --width 32 --family <family> --pins k=v,...` emits it for a rewrite (`--sqrt` for the square root).

## design choices

### product_bits

| member | what it selects |
| --- | --- |
| `full` | the back-multiply q * b is formed over the full product width. |
| `low_bits_sufficient` | the back-multiply runs over the low bits alone, which suffices because the remainder's magnitude stays below twice the divisor; an exactly rounded contract takes the full product instead. |

## references

markstein_1990 -> Markstein, "Computation of Elementary Functions on the IBM RISC System/6000 Processor", IBM Journal of Research and Development, 1990
harrison_2000 -> Harrison, "Formal Verification of IA-64 Division Algorithms", TPHOLs, LNCS 1869, 2000
even_2003 -> Even, Seidel, Ferguson, "A Parametric Error Analysis of Goldschmidt's Division Algorithm", 16th IEEE Symposium on Computer Arithmetic, 2003
wang_2005 -> Wang, Schulte, "Decimal Floating-Point Square Root Using Newton-Raphson Iteration", IEEE ASAP, 2005
