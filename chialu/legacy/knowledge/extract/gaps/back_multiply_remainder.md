# back_multiply_remainder: proposed changes to the space

* choice `reciprocal_requirement: {correctly_rounded, relative_error_bounded}` — the strengthened theorem replaces the correctly rounded reciprocal precondition with a relative-error bound of 1/2^p [harrison_2000]
* choice `selection_test: {fma_residual_sign, guard_digit_action_table, product_compare, midpoint_square_compare}` — the decimal square root selects by guard digit plus remainder sign/zero through an action table, the K7 form compares the back-multiplied product against the dividend, and the FPGA square root compares the square of a midpoint candidate against the radicand [wang_2005, even_2003, pasca_2011]
