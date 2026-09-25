# self_timed_variable_latency: proposed changes to the space

* choices `incorrect_speculation_action: {rollback_correction, fixed_partial_advance}` and `speculation_function: {reduced_input_table, reduced_output_set, approximate_arithmetic_function}` — the speculative divider's speed depends on partial advance, and the simplification of the digit guess is a separate design decision [cortadella_1994]
* `mechanism` as a composable set rather than one value — the self-timed ring also terminates early on a repeating remainder, and the z990 combines early termination with idle clock gating [williams_1991, gerwig_2004]
* choices `ring_stages: Int`, `execution_overlap: adjacent_stage` and `early_done_detection: repeating_partial_remainder` for the self-timed ring [williams_1991]
* choice `termination_conditions: {special_case, short_integer_quotient, zero_residual, radix2_exact_negative_residual}` naming which events stop the recurrence [kim_2025]
* `mechanism` value or separate choice `cached_value: {quotient, reciprocal}` for result reuse through a division or reciprocal cache [oberman_1997]
