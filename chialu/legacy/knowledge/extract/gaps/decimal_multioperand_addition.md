# decimal_multioperand_addition: proposed changes to the space

* `reduction_style` values `binary_csa_linear_array`, `binary_csa_with_concurrent_carry_count_correction`, `signed_digit_multioperand_recoding`, `rom_array_two_stage` — correction-speculation chains, concurrent carry counting, signed-digit recoding per level and cascaded ROM arrays fit none of the three listed styles [kenney_2005, vazquez_2014, han2013, schmookler_1972]
* `correction_placement` values `speculated_during_reduction` and `none` — speculation differs from per-level and at-root, and weight-sum-nine coded CSA trees need no correction at all [kenney_2005, vazquez_2010]
* choice `correction_speculation_span: {one_addition, two_additions}` — two-addition speculation moves the multiplexers off the critical path [kenney_2005]
* choice `internal_digit_code: {bcd8421, 4221, 5211, mixed_4221_5211}` — the digit code decides whether binary CSAs produce valid decimal digits [vazquez_2010, castellanos_2008]
* `root_adder` slot admitting `bcd_direct_addition` — every word-wide design terminates in a decimal carry-lookahead or radix-10 prefix adder [kenney_2005, lang_2006, erle_2003, vazquez_2014]
* a carry-collection choice (`carry_counter: 8_bits_to_1_decimal_digit`, `carry_collection: binary_to_bcd_counters_off_critical_path`) — leftover carry vectors are grouped by counters outside the main tree [lang_2006, jaberipur_2009]
* a converter slot accepting `binary_decimal_conversion` and a choice for independent equal-weight column reduction before major-partial-sum alignment — conversion of each column sum is a defining stage of the mixed binary/BCD scheme [dadda_2007]
* `parallel_decimal_multiplication.reduction_tree` admitting `decimal_multioperand_addition` — decimal compressor trees are built to reduce multiplier partial products [castellanos_2008, schmookler_1972]
* choice `counter_input_encoding: two_bcd_digits_plus_carry_bits` — the decimal counter distinguishes 4-bit digit inputs from 1-bit carry inputs [erle_2003]
* choices `result_digit_set: [-8,7]` and `maximum_sd_operands: 4` — signed-digit reduction bounds the operand count per level by the chosen digit set [han2013]
* choice `correction_evaluation: concurrent_carry_count` — inter-digit binary carries are counted while the tree reduces [vazquez_2014]
