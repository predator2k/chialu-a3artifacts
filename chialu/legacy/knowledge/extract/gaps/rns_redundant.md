# rns_redundant: proposed changes to the space

* correctable_error_class {all_single_residue_digit_errors, selected_single_residue_digit_errors, single_bit_encoding_errors} — the guaranteed fault class decides the redundant product needed [barsi_maestrini_1973]
* correction_algorithm modulus_projection_search and redundancy_bound — projection-based correction performed entirely with residue modular operations under m_R > max(m_i m_j) [barsi_maestrini_1973]
* residue_digit_encoding hamming_distance_constrained_binary — constrains distance-one transitions to the correctable error set [barsi_maestrini_1973]
* decoding {legitimate_range, iterative_channel_exclusion, maximum_likelihood} — the decoder method is a separate design axis [chang_2015]
* consistency_check base_extension_discrepancies and redundancy_domain {time, hardware} — recomputed redundant residues compared with stored ones, with check arithmetic reusing the information modules or using separate modules [watson_hastings_1966]
