# decimal_newton: proposed changes to the space

* an iteration-multiplier slot (`iter_mult`) with a configuration choice `{sequential, multi_digit, parallel}` — one shared decimal multiplier performs seed generation, refinement, quotient generation and the rounding product, its digits per cycle set the latency, and it dominates the core area [wang_2004, wang_2005]
* `final_round` value `product_digit_remainder_rounding` — the divider selects the rounded quotient from product digits without a full back-multiplied remainder subtraction [wang_2004]
* choice `intermediate_precision: {full, iteration_dependent}` — early multiplications use reduced or progressively doubled widths while preserving digit doubling [wang_2007, schwarz_2007]
* choice `iteration_order: {second_order, third_order}` — the third-order update triples rather than doubles the correct digits per application [richards_1955#s10]
* choice `iteration_form: truncated_nines_complement` — V approximates 2 - X x R through a nine's complement with both iteration products truncated [wang_2004]
* `seed_digits` range extended to 10 — the square-root design parameterizes the table index digits over 2 to 10 [wang_2005]
* choice `supported_rounding_modes` — the action tables support the five IEEE modes plus RNT and RAZ [wang_2005]
