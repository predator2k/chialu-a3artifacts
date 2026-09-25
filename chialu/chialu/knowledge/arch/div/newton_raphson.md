# newton_raphson

Reciprocal refinement by the recurrence x' = x(2 - dx): each iteration
squares the relative error of the reciprocal estimate, so a seed of m
correct bits reaches n bits in ceil(log2(n/m)) iterations. One
iteration is two dependent multiplications and a complement, a final
multiplication by the dividend forms the quotient, and the same
datapath serves the inverse square root through x' = x(3 - a x^2)/2 at
three multiplications per iteration. The seed comes from a table or an
operand-derived approximation, the iteration multiplier is dedicated
or the shared floating-point multiplier/FMA, and final rounding is by
a back-multiplied remainder or an exclusion-zone proof.

The iteration count trades against the seed: a 53-bit result needs six
iterations from a one-bit seed, three from an eight-bit seed and two
from at least 14 bits, and each further seed bit doubles the table.
The dedicated-multiplier choice trades latency against sharing: a
divider on the existing FMA costs no incremental hardware and its
contention is small in typical floating-point code, but FMA-based
refinement is 4 to 6 times less power-efficient than digit recurrence
in 90-nm CMOS and its rounding is less direct; the library's iter_mult
is the divider's own multiplier, and sharing the unit's multiplier is
a unit-level sharing choice. Because the recurrence is
self-correcting, iteration-specific truncated multipliers (4, 7 and 12
recoded summands in successive passes) still deliver the exact
reciprocal, and early short operands let two multiplications share
sections of one tree. Intermediate inaccuracies do not accumulate as
they do in Goldschmidt's iteration, but the two products of each step
are dependent, so the critical path is 2r+1 multiplications for r
iterations against Goldschmidt's r+1, and the guard bits set how much
precision the last step keeps; an exponent field two bits wider for
divide and one for square root avoids intermediate overflow and
underflow that otherwise force software assistance.

Final rounding decides the contract. Back-multiplication forms the
exact residual R = a - bQ with a fused accumulate and corrects Q by
R times the reciprocal in the requested mode, which yields the
correctly rounded quotient in all four IEEE modes with a correct
inexact flag, provided Q already exceeds n-bit accuracy and the
all-ones divisor mantissa is handled by an initial overestimate. An
exclusion-zone proof reaches the same contract with higher
intermediate precision; at equal intermediate and final precision the
refined theorem must be supplemented by explicit checks of the
exceptional mantissas. Without a final correction the reciprocal
sequence is within one ulp, with 99% of operands correctly rounded for
the reciprocal and 87% for the reciprocal square root, and the error is
biased. Execution is fixed-iteration; because the sequence keeps no
hidden state between steps, it can be issued as separately schedulable
pipelined instructions.

The seed instantiates the library's generated divider for this family
(`chialu/targets/rtl/families/div.py`: a reciprocal seed of the `seed` family, exactly `iterations` unrolled steps x(2 - dx) (or the cubic step under `iteration_order` 3; the seed widened until that many steps reach the target, or the fewest steps the seed needs when the pin is absent) at `internal_guard_bits` of extra precision, the products through `iter_mult` and the sums through `iter_add`, the divisor normalized through the norm slots, the quotient a x, then the `final_round` family). `python3 -m chialu.targets.rtl.families.div --width 32 --family <family> --pins k=v,...` emits it for a rewrite (`--sqrt` for the square root).

## realization

| claim | pins | the module header matches |
| --- | --- | --- |
| a seed is refined by Newton steps whose count and order the module states | - | `\d+ Newton step\(s\) of order \d+` |

## references

richards_1955 -> Richards, "Arithmetic Operations in Digital Computers", Van Nostrand, 1955
burks1946 -> A. W. Burks, H. H. Goldstine, J. von Neumann, "Preliminary Discussion of the Logical Design of an Electronic Computing Instrument", Institute for Advanced Study report, 1946 (reprinted in B. Randell, The Origins of Digital Computers, Springer).
flynn_1970 -> Flynn, "On Division by Functional Iteration", IEEE Transactions on Computers, 1970
wallace1964 -> Wallace, "A Suggestion for a Fast Multiplier", IEEE Transactions on Electronic Computers, 1964
markstein_1990 -> Markstein, "Computation of Elementary Functions on the IBM RISC System/6000 Processor", IBM Journal of Research and Development, 1990
oberman_1997 -> Oberman, Flynn, "Division Algorithms and Implementations", IEEE Transactions on Computers, 1997
cornea_1999 -> Cornea-Hasegan, Golliver, Markstein, "Correctness Proofs Outline for Newton-Raphson Based Floating-Point Divide and Square Root Algorithms", 14th IEEE Symposium on Computer Arithmetic, 1999
liu_2012 -> Liu, Nannarelli, "Power Efficient Division and Square Root Unit", IEEE Transactions on Computers, 2012
