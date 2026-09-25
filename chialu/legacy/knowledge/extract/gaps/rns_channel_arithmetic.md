# rns_channel_arithmetic: proposed changes to the space

* a moduli-set choice with cardinality, balance and heterogeneous forms (mixed pow2_minus_1/pow2/pow2_plus_1 channels, conjugate {2^n+/-1, 2^(n+1)+/-1}, small generic sets such as {16,13,11,9,7}) — performance and converter cost depend on the set, and `modulus_form` cannot express one datapath with several forms [chang_2015, conway_nelson_2004, garner_1959, jenkins_leon_1977, samimi_2020]
* choice `modulus_set_selection: exhaustive_minimum_area_delay_product` — the set is chosen from per-modulus stage costs [conway_nelson_2004]
* `multiplier_reduction` values `pseudo_mersenne_folding`, `square_lookup_identity` and a fixed two-MCSA diminished-1 reduction — 2^r - epsilon channels fold the high product part, in-memory channels replace multiplication by squares from a table, and the diminished-1 reduction is a specific structure [guillermin_2010, salamat_2018, ma_1998]
* `modular_adder` slot values `generalized_modular_correction_adder` and an in-memory MAGIC-NOR adder [jenkins_leon_1977, salamat_2018]
* choice `operation_realization: {rom_lookup, boolean_logic}` — stored outcomes versus implemented functions per channel [jullien_1978]
* choices `partial_product_recoding: {none, booth_bit_pair}` and `accumulation_ranging: {per_operation, final_only}` — Booth halves the rows, and widened accumulation defers the residue reduction to one final ranging [zimmermann1999, salamat_2018]
* heterogeneous channel widths (5/5/6 bits) and `channel_width_n` values below 4 and above 32 — reported sets use 3 to 36 bits [samimi_2020, conway_nelson_2004, guillermin_2010]
