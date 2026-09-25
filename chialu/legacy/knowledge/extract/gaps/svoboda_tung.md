# svoboda_tung: proposed changes to the space

* choice `residual_digit_set` (α with b/2 ≤ α ≤ b − 1) and a `digit_redundancy: minimal` flag — α changes the adder complexity, the divisor multiples, and the residual encoding, and Tung restricts the algorithm to minimally redundant signed-digit systems [montalvo_1998, tung_1968]
* choice `recoding_threshold` (β with b − α − 1 ≤ β < α) — β changes the quotient-selection complexity and the prescaling range [montalvo_1998]
* choice `divisor_range` (δ = (α − β)/(bα)) or the equivalent `divisor_error_interval` bounds — δ controls how many divisor bits and which constant decomposition the prescaler uses, and Tung's e bounds fix one-step compensation [montalvo_1998, tung_1968]
* choice `algorithm_variant: {MRMR, MROR, MRmr, mr, intermediate}` — the named α/β design points differ in prescaling cycles, residual bits observed, and area [montalvo_1998]
* extend `radix` to 2, to power-of-two radices above 16, and to Tung's odd r > 3 and even r > 4 formulation [montalvo_1998, tung_1968]
