# goldschmidt: proposed changes to the space

* `iterations` domain extended to 1 — single precision on the K7 and the 30-bit-seed modified iteration both finish in one iteration [even_2003, pineiro_2002]
* choice `intermediate_rounding: {nearest, directed, strict_directed}` — the error analysis rounds products down and the factor up [even_2003]
* choices `precision_allocation: per_product_unequal_width` and a factor precision schedule — each intermediate product may use its own multiplicand length, and the Model 91 factors run 10/7/9/9/32 bits [even_2003, anderson1967]
* choice `seed_error_budget: independently_optimized` — the seed accuracy is sized jointly with the multiplier dimensions [even_2003]
* choice `numerator_denominator_concurrency: {concurrent, sequential}` — overlapping the two products in a pipelined multiplier is the source of the latency advantage [goldschmidt_1964#s01, anderson1967, oberman_1997]
* `final_round` value for truncating an extra-precision quotient without a remainder test — the original unit and the POWER6 non-IEEE mode round that way [goldschmidt_1964#s01, trong_2007]
* `seed` slot value `linear_pwl_reciprocal_seed` — POWER6 combines coefficient tables with a linear multiplier for a seed of slightly more than 14 bits [trong_2007]
* choice `approximate_reciprocal: {RAK, RBK, RCK, generalized_RCK}` with per-iteration `reciprocal_length_CK`, and a decimal `factor_approximation` — the thesis and textbook distinguish how each convergence factor is formed [goldschmidt_1964#s01, richards_1955#s10]
* choice `final_refinement: conditional_newton_raphson` — fixed-point 64-bit division adds one Newton step unless the numerator is short [trong_2007]
* choices `operation_set: {divide, divide_sqrt, divide_sqrt_inverse_sqrt}` and `iteration_form: reordered_modified_single_iteration` — the same datapath serves square root and inverse square root [darley_1990, pineiro_2002, schwarz_1999]
* `iter_mult` slot value `iterative_decimal_multiplication` — the decimal textbook variant iterates on a decimal multiplier [richards_1955#s10]
