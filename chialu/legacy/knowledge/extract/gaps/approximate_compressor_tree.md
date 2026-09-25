# approximate_compressor_tree: proposed changes to the space

* `compressor` values for the mirror-adder-based 4:2/8:2 cells, the Lin inaccurate 4:2 counter, and the Lin/Ha/Sabetz/Ahma topologies of the comparative map, plus sub-variant choices (DQ4:2C1 to C4 and mixed, ACCI1 to ACCI3) — each is a distinct truth table with its own error rate [gupta2013, gupta2011, lin2013, strollo2020, akbari2017, yang2015]
* choice `approximation_extent: {C-N, C-FULL, Hybrid}` with per-region mixing of cell types — the map separates column-bounded, full-matrix and hybrid trees, and the dual-quality design mixes cells by significance [strollo2020, akbari2017]
* choice `input_pin_assignment: {probability_optimized, input_commutative}` — non-symmetric cells need probability-aware assignment of partial products to inputs [strollo2020]
* choices `input_encoding: generate_propagate` / `partial_product_transform: propagate_generate_pairing`, `generate_reduction_group_limit`, `approximate_cell_set` — encoded or altered partial products change the error probabilities before compression [ansari2018, venkatachalam2017]
* recursive-composition choices `base_multiplier_block_width`, `recursive_exactness_placement`, `terminal_carry_handling: {retain_c4, omit_c4}` — 4x4 blocks compose into larger multipliers with selectable exact subproducts [ansari2018, lin2013, mazahir2017b]
* choices `compressor_arity: {2/1, 3/2, 4/2, 5/3, 6/3, composed}`, `reduction_steps_approximated: {1, 2}`, `allocation_policy: error_aware_column_height` — the carry-free cells are allocated by column height rather than by a fixed region [esposito2018]
* choice `carry_interface: {retained, eliminated}` — Design 1 keeps cin/cout, Design 2 removes both [momeni2015]
* choice `mode_implementation: approximate_part_plus_supplementary_part` — dual-quality cells power-gate a supplementary exact part [akbari2017]
* `cpa` slot admitting `lower_part_approximate` and `segmented_carry_speculative` — the mirror-adder multiplier ends in an approximate RCA and the Lin multiplier in a speculative adder with extra-cycle correction [gupta2013, lin2013]
* `approximate_columns` domain admitting 1, odd counts (5 to 9, 15) and `all` — the base block approximates one column, the mirror-adder design 5 to 9 LSBs, and the full-tree designs every column [lin2013, gupta2013, venkatachalam2017, momeni2015]
* choice `counter_gate_substitution: xor_to_2_1_mux` — the Lin counter shortens delay by a gate substitution [lin2013]
* `approximate_booth` reduction slot admitting `approximate_compressor_tree` — the encoded design pairs an exact Booth encoder with approximate compressors [ansari2018]
