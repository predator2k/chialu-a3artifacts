# exclusion_zone_proof

Correct rounding of a multiplicative divide or square root by a
proof rather than by a per-result remainder: the argument bounds the
distance between the exact quotient or root and every floating-point
number or rounding midpoint c (for representable a and b, either
a/b = c or |a/b - c| is at least |a/b|/2^(2p+2)), so any final
unrounded approximation that lies closer to the exact result than
half the minimum exclusion-zone width rounds identically to it in
every rounding mode. The finitely many quotient and square-root
cases nearest a boundary are enumerated and handled by strengthened
theorems or by separately verified algorithms.

The family has no hardware tunables: what it trades is proof effort
against datapath. It needs proved approximation-error bounds for the
whole iteration, an extra precision bit to represent midpoints, and
separate treatment of exact quotients, denormal midpoints and the
difficult boundary sets. The divide zones are 2^-N ulp around
floating-point numbers and 2^-(N+1) ulp around midpoints, and the
generic square-root zones 2^-(N+1) and 2^-(N+3) ulp, so the last
iteration must land inside them.

The contract is correct IEEE rounding in the four rounding modes
together with correct overflow, underflow and inexact flags under
the stated software-assistance assumptions. The family wins when the
pipeline offers intermediate precision above the target format,
which is how the scalar single-precision algorithm meets the bound
after register-double rounding; extended and SIMD algorithms cannot
in general obtain the bound from higher intermediate precision and
need more precise theorems or the residual-based sibling, which
computes an exact remainder with two fused operations instead.

The seed instantiates the library's generated divider for this family
(`chialu/targets/rtl/families/div.py`: the reciprocal carried to Q + D + 3 fraction bits so the estimate rounded at half the smallest quotient step (the rounding add through `correction_adder`) is the quotient without candidate selection; the remainder still back-multiplied for the r output). `python3 -m chialu.targets.rtl.families.div --width 32 --family <family> --pins k=v,...` emits it for a rewrite (`--sqrt` for the square root).

## references

cornea_1999 -> Cornea-Hasegan, Golliver, Markstein, "Correctness Proofs Outline for Newton-Raphson Based Floating-Point Divide and Square Root Algorithms", 14th IEEE Symposium on Computer Arithmetic, 1999
harrison_2000 -> Harrison, "Formal Verification of IA-64 Division Algorithms", TPHOLs, LNCS 1869, 2000
