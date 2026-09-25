---
family: posit_adder_multiplier
pin: {operator_set: add_mul_div}
---
# add_mul_div

The PACoGen divider added behind the family's shared decoder and
encoder: the decoder extracts the variable-position sign, regime,
exponent and fraction fields, the significand quotient comes from a
parameterized Newton-Raphson reciprocal in the sig_div slot, the
divisor regime and exponent are subtracted from the dividend's, the
quotient is normalized, the posit is reconstructed and
round-to-nearest-even is applied at encode.

The pick when the unit must divide without a decode and encode context
of its own: the divider reuses the field extraction and the single
rounding at encode that the adder and multiplier already pay for, and
the Newton-Raphson iteration count in the sig_div slot sets the depth,
with posit(32,6) at two iterations pipelining to 12 stages on a
Virtex-7. The registry's es_bits and iterations ranges are narrower
than the generator's, which admits a seed-only reciprocal and an es of
6, so those points sit outside the family. The add_mul sibling omits
the reciprocal multiplier and its seed table.

Under this variant the seed adds the unit's divider and square root from the `sig_div` slot (the float library's divider and square root on X) beside its adder and multiplier.

## references

jaiswal_2019 -> M. K. Jaiswal, H. K.-H. So, "PACoGen: A Hardware Posit Arithmetic Core Generator", IEEE Access, 2019
