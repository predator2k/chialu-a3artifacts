# redundant_high_radix_cordic: proposed changes to the space

* `scale_handling` values `branching`, `differential_constant_scale`, `zero_direction_length_adjustment` and `table_plus_shift_add_then_linear_cordic_multiplication` — each reported constant- or computed-scale method is a distinct mechanism outside the current enumeration [muller_2016#s08, duprat_1993, dawid_1996, timmermann_1992, antelo_1997]
* a slot for the scale-factor compensator, filled in the radix-4 design by a linear-coordinate CORDIC multiplier [antelo_1997]
* choice `mode: {rotation, vectoring, both}` — the two modes use different steering variables, delays and architectures in the differential form [dawid_1996]
* choice `selection_window` / `digit_selection_inspection_digits` — the fixed number of inspected residual digits (three, or four to five at most) sets constant-time selection and the truncation error [duprat_1993, timmermann_1992, muller_2016#s08]
* choice `zero_digit_allowed: Bool` or an explicit digit set of -1/0/+1 — the zero direction is what makes the scale factor variable [muller_2016#s08, muller_2016#s09]
* choices `architecture: {word_serial, unfolded_pipelined, application_specific}`, `zero_skipping: Bool` and `angle_source: {runtime, known_beforehand}` — organization, zero skipping and stored direction sequences for known angles [antelo_1997]
* the `cordic` family lacks `scale_handling: virtually_scaling_free`, which now appears only here although the implementation uses radix-2 two's-complement arithmetic [maharatna_2005]
