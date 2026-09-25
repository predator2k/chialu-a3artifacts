# multi_residue: proposed changes to the space

* slot `syndrome_decoder_corrector` — the implementation stores the syndrome pair, decodes the faulty component and error value, and corrects the accumulator output, which `two_rail_tree` does not describe [rao_1970]
* choice `correction_realization: {table_lookup, explicit_computation}` and `table_folding: {none, complementary_symmetry}` plus a slot for the modular discrepancy checker — the RNS form corrects through a discrepancy-addressed table whose size and folding are design decisions [watson_hastings_1966]
* choice `checker_error_handling: {leave_uncorrected_and_inhibit_accumulator_correction, regenerate_residue}` — a located checker error is either retained until maintenance or regenerated [rao_1970]
