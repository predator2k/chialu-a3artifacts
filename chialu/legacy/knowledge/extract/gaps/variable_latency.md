# variable_latency: proposed changes to the space

* a `near_lz` or early-completion-predictor slot — the exponent and significand leading-one predictors that classify one-cycle results are a component the space does not name [oberman_1996]
* choices `short_shift_limit_bits: {0, 1, 2}` and `collision_policy` (pipe an early result to a later stage) — the first-cycle normalization-shift limit sets the one-cycle class and the collision policy preserves result ordering [oberman_1996]
