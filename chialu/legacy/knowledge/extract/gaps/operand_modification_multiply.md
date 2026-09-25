# operand_modification_multiply: proposed changes to the space

* `function` value `sqrt` — the mechanism applies directly to square-root seeds as well as reciprocal and reciprocal-square-root seeds [ito_1997]
* choices `operand_modification: {lower_bit_inversion, lower_bit_inversion_plus_one_bit_shift, nine_complement}` and `multiplier_source: {reused_iteration_multiplier, dedicated_multiplier}` — the modifier hardware and multiplier sizing follow from these [ito_1997, wang_2007]
* decimal digit-count choices (`input_digits`, `coefficient_digits`) and `coefficient_encoding: {bcd, dpd}` — the k-digit DPD tables are not expressible through bit counts, and DPD storage cuts the table by 4.5 times [wang_2004, wang_2005, wang_2007]
* choice `expansion_point: {XM, XM_plus_2_thirds_10_minus_k}` — the shifted Taylor point gains one digit for the reciprocal square root [wang_2005]
