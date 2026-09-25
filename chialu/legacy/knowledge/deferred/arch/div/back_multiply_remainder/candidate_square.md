---
family: back_multiply_remainder
pin: {residual_operation: candidate_square}
---
# candidate_square

The rounding test for a square root: the faithful candidate r at wF+1
bits is either representable at wF or a midpoint between two
representable values, and only at a midpoint is r squared and
compared with the operand x, which decides between truncation and the
upward correction by 2^-(wF+1) followed by truncation. Only the
square-product bits that settle the comparison are computed.

It is the pick for a square-root unit whose approximation is faithful
at one extra bit, where the quotient-times-divisor residual has no
divisor to multiply by: the candidate error is below 2^-(wF+1) and the
comparison difference is bounded by one ulp at wF, so a partial
low-order square suffices when product_bits is low_bits_sufficient.
On a Virtex-4 the correct-rounding step adds 2 to 5 DSP blocks and 4
to 13 cycles to the faithful (8,23) unit. The quotient-times-divisor
form is the sibling for division, where the residual a - qb selects
among the quotient candidates.

## references

pasca_2011 -> B. Pasca, "High-Performance Floating-Point Computing on Reconfigurable Circuits", PhD thesis, ENS Lyon, 2011
