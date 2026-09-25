# poly_seed: proposed changes to the space

* slot or choice `evaluator_structure` (specialized truncated squarer plus fused carry-save accumulation tree) — the evaluator's arithmetic is a design decision the space does not record [pineiro_2002]
* choice `per_function_coefficient_tables: Bool` — reciprocal and inverse-square-root modes share the evaluator and replicate only tables [pineiro_2002]
* extend `output_bits` domain beyond 24 — the double-precision seeds are 30 (reciprocal) and 29 (inverse square root) bits wide [pineiro_2002]
