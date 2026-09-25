# fused_csa: proposed changes to the space

* choices `term_count: K`, `expansion_addends: one_or_more`, `reduction_schedule: Dadda_height_sequence` — the number of merged products, the addends injected into the initial matrix and the counter height schedule determine the merged construction [swartzlander_1980]
* `compressor` value for mixed full-adder/half-adder counters — the Dadda-style reduction uses both counter types rather than a single compressor kind [swartzlander_1980]
* choice `boundary_carry_kill: mode_dependent` — SIMD lanes need carries suppressed across lane boundaries at every CSA level [danysh_2005]
