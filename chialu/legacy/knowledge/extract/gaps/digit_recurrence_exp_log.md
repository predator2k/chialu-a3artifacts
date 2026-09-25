# digit_recurrence_exp_log: proposed changes to the space

* `radix` values above 16, the powers of two from 8 through 1024 and the emphasized 32 to 128 range — the high-radix powering units sweep those radices [pineiro_2004, vazquez_2013, muller_2016#s09]
* `selection` values `comparison` (restoring), `leading_bit_count` with data-dependent bit skipping, `binary_digit_prediction_with_correction` (Baker), and a mixed schedule of table lookup in iteration 1 then rounding [muller_2016#s07, chen_1972, pineiro_2004]
* choice `residual_representation: {signed_digit, carry_save}` — the redundant encoding of the residual decides the selector prefix and the conversion adder [muller_2016#s07]
* choices `digit_magnitude`, `first_step_strategy: {start_at_n_2, special_correction, table}`, `initialization: table_with_residual_correction` and `correction_schedule: repeated_last_weight` — the first iterations and Baker's block correction are separate design decisions [muller_2016#s09, muller_2016#s07]
* choice `termination_method: linear_extrapolation` — the recurrence stops after about half the bits and finishes with an add and an abbreviated multiply [chen_1972]
* choice `execution_organization: {two_arithmetic_units, one_pipelined_arithmetic_unit}` and a shifting-network slot that `barrel_mux_tree` fills — overlapping normalization and result evaluation in one unit costs 15 to 25 percent performance [ercegovac_1973]
* `normalization` as a per-operation pair — the units that compute both functions use multiplicative normalization for the logarithm and additive for the exponential [ercegovac_1973, pineiro_2004, chen_1972]
* choices `arithmetic_domain: complex`, `operation_mode: {E_mode, L_mode}`, a nine-value `complex_digit_set`, `selector_fraction_bits` and `scaling_factor_required: false` — BKM's complex recurrence and its freedom from a CORDIC scale factor [bajard_1994]
* choices `operation_set: {logarithm, exponential, integer_powering, qth_root}`, `stage_composition: overlapped_log_lrcf_exp`, `online_delay`, and an intermediate-multiplier slot filled by `left_to_right_carry_free_multiplier` [pineiro_2004, vazquez_2013]
* choice `logarithm_iteration_skipping: lzd_lod_leading_digit_skip` — leading-zero/one detection omits the initial logarithm iterations [vazquez_2013]
