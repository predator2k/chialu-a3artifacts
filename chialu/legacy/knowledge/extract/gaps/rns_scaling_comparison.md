# rns_scaling_comparison: proposed changes to the space

* `method` values `parity_of_modular_difference`, `iterated_approximations`, `lpn_reference_residue`, `hierarchical_crt_mrs`, `simplified_szabo_tanaka`, `dynamic_range_partitioning`, and `mixed_radix_crt` — each is the implemented method of one design and none maps onto the four listed [garner_1959, posch_posch_1995, salamat_2018, sousa_2015, samimi_2020]
* `exactness` value `approximate_bounded_uncorrected` — the modulo-reduction extension accepts an off-by-one estimate and relies on later range adjustment [posch_posch_1995]
* choices `diagonal_modulus_integration: {redundant_extra_modulus, incorporated_nonredundant_modulus}` and `modulus_organization: {individual_moduli, grouped_virtual_moduli}`, plus a slot for the modulo-SQ summation network — the improved SQT folds SQ into the dynamic range and groups moduli to shrink it [dimauro_1993]
* choices `redundant_modulus_requirement` (relatively prime, p >= n), `stage_implementation: {lookup_tables, modulo_adders, combination}`, and `first_stage_table_inputs: {single, multiple}` — the redundant-modulus base extension is parameterized by these [shenoy_kumaresan_1989]
* choices `scale_factor: 2^n`, `moduli_set` structure, and `hierarchy_levels: {1, 2}`, with slots for channel modular adders, end-around-carry CSAs, and the second-level modulo multiplier — the special-moduli scaler is defined by them [sousa_2015]
* choices `summand_representation: fractional`, stored-fraction precision, and `stored_value_quantization: {truncate_up, truncate_down, round}` — the fractional CRT sign detector depends on all three [vu_1985]
* choice `rounding: {round_down, round_off}` for estimate scaling — adds a fixed half-scale quantity before scaling [jullien_1978]
* choice `comparison_threshold: {variable_operand, fixed_M_over_2}` — a trimmed half-comparator serves a fixed ReLU threshold [garner_1959]
