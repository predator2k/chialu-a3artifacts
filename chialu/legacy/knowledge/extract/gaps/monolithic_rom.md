# monolithic_rom: proposed changes to the space

* `guard_bits` range extended past 3 — the paper tabulates g = 4 and g = 5 and proves the bound for every g >= 0 [dassarma_1994]
* `input_bits` and `output_bits` ranges starting at 3 or 1 rather than 4 — exhaustive results cover k = 3 and m = 3, and the construction is proved for k, m >= 1 [dassarma_1994]
* choices `table_entry_rule: round_to_nearest_midpoint_reciprocal`, `error_objective: minimum_maximum_relative_error` and `reciprocal_direction: {nearest_minimax, directed_high, directed_low}` — the entry rounding rule and whether the entry is nearest or one-sided are design decisions the table construction exposes [dassarma_1994]
