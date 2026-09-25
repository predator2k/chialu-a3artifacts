# redundant_binary_multiplier: proposed changes to the space

* `booth_radix` values 8 and 16, and a value that preserves the term "second-order Booth" without a numeric radix — the TI coprocessor's sign-digit tree uses a radix-8 recoder, the covalent encoder binds two radix-4 encoders into radix 16, and the 54x54 design names its recoding second-order Booth [darley_1990, he_chang_2009, makino_1996]
* `rb_encoding` value `positive_negative_complement` with choices `rb_booth_encoding: covalent_adjacent_digit_polarization` and `correction_vector: {present, none}` — the dipole encoding forms one RB partial product per four multiplier bits and removes the negative-multiple and NB-to-RB compensation rows [he_chang_2009]
* choice `adjacent_booth_grouping: paired_even_odd` — pairing two adjacent radix-4 groups reduces n/2 Booth rows to n/4 redundant rows [kuninobu_1987]
* choices `rbpp_generation: paired_nb_invert_plus_negative_digit`, `rba_cell_circuit` and `converter_grouping: increasing_group_width` for the RB partial-product formation, the adder cell style and the carry-select converter of the 54x54 design [makino_1996]
* choice `physical_tree_layout: {H, L, V, improved_V}` — the tree layout materially affects wiring area and aspect ratio [harata_1987]
* a reduction slot naming the binary tree of carry-free RB adders, and admission of `redundant_binary_multiplier` in the `booth_recoded_parallel` reduction slot, since both origin designs reduce modified-Booth partial products with a redundant binary tree [he_chang_2009, harata_1987, takagi_1985]
* choice `tree_dimensions` or a two-pass mode for a sign-digit tree narrower than the fp64 significand [darley_1990]
