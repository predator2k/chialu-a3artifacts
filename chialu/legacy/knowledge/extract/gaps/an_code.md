# an_code: proposed changes to the space

* A domain widened to arbitrary odd positive integers — the admissible A depends on the required distance and digit base rather than the four listed values [brown_1960, garner_1966]
* offset_B / additive_correction choice — the affine An+B form controls complementation, post-add correction and the B=0 single-digit variant [brown_1960, garner_1966]
* check_modulus_form 2^a-1 and arithmetic_representation {ones_complement, twos_complement} — the low-cost complementable codes need a Mersenne A and one's-complement arithmetic [avizienis_1973, garner_1966]
* processing_granularity_bits and result_check_schedule {partial_and_final} — the STAR moves coded operands byte-serially and checks partial results [avizienis_1973]
* detection_method {division_by_A, residue_B_mod_A, mod3_even_odd_weight} and error_location_method {table_lookup, arithmetic_residue_sequence} — the legality test and the error locator are separate structures [brown_1960]
* comparator slot admitting a modulo-A checksum accumulator with equality test — the STAR checker is not a two-rail tree [avizienis_1973]
* generator_unit a, systematic layout and codeword_complement {radix, diminished_radix} — distinct isomorphisms over the same ideal give distinct codes and carry corrections [garner_1966]
