---
family: sequential_shift_add
pin: {accumulator_form: carry_save}
---
# carry_save

The partial product is held in two registers, PP1 and PP2, as an
unassimilated pair; each loop pass adds the selected multiplicand
multiples through a four-input two-output adder with no carry
propagation and shifts both registers right, and one final carry-
propagate addition assimilates the pair into the product.
Goldschmidt's unit recodes overlapping three-bit multiplier groups
into five multiples, adds two multiples per pass, shifts right four,
and retires 56 bits in 15 passes.

Removing the carry chain from the loop is what admits several
multiples per pass: the 56-bit multiply runs three four-input
additions per machine cycle, five iteration cycles plus one for
initialization and the final assimilating addition, and the signed
recoding halves the non-zero multiples to at most 29. The costs are
the second partial-product register, the final carry-propagate adder,
and a spill adder that detects a carry from the bits shifted below the
retained width. Against the carry_propagate sibling it wins once bits
per cycle rises past one or two, and it is the accumulator that the
unroll_to_array mutation turns into cascaded carry-save rows. It is
the pick when the loop must feed a fast multiply to division by
convergence or another iterative consumer.

## references

goldschmidt_1964 -> Goldschmidt, "Applications of Division by Convergence", MS thesis, MIT, 1964
