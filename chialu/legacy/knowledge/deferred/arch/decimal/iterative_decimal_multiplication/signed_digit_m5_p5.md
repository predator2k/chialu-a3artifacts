---
family: iterative_decimal_multiplication
pin: {multiplier_digit_recoding: signed_digit_m5_p5}
---
# signed_digit_m5_p5

Each BCD digit of both operands is recoded into signed-magnitude form
from -5 to +5, using the digit and the next-lower digit's
greater-than-or-equal-to-five flag; the multiplicand is recoded in
parallel and the multiplier digits as they are consumed, LSD first.
Digit products then need only magnitudes 2 through 5, 16 input
combinations instead of 100, and an n+1-block word-by-digit multiplier
emits an overlapped signed-magnitude partial product that a Svoboda
signed-digit adder accumulates.

The recoding is the pick when partial-product generation rather than
accumulation sets the cycle: the digit-product logic drops to 15
minterms and 6 gate levels per output from 62 and 19, while overlap
removal and recoding before the signed-digit adder cost 10 logic
levels and the LSD conversion to BCD 12. Latency stays n+4 cycles,
equal to the carry-save design, with two final cycles converting the
remaining signed-digit product to BCD. Richards describes the same
idea as complement recoding: subtracting a multiple lets the large
digits be handled through their complements, which with doubling
brings the average to 1.5 operations per digit against 4.5 for
addition alone. Against none it adds the recoders and the
overlap-removal step but shrinks each digit multiplier and needs no
stored multiples. In the ADIR grammar it is
`family: iterative_decimal_multiplication` with
`pin: {multiplier_digit_recoding: signed_digit_m5_p5}`.

## references

erle_2005 -> Erle, Schwarz, Schulte, "Decimal Multiplication with Efficient Partial Product Generation", 17th IEEE Symposium on Computer Arithmetic (ARITH-17), 2005
richards_1955 -> Richards, "Arithmetic Operations in Digital Computers", Van Nostrand, 1955
