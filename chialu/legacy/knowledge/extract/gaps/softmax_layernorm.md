# softmax_layernorm: proposed changes to the space

* exponential_base {e, 2} — the substituted base 2 is the defining pseudo-softmax and Softermax choice, not recorded by exp_evaluation [cardarilli_2021, stevens_2021]
* exp_evaluation value group_lookup_table, with a valid_data_window and data-dependent calculation_accuracy_control — multiplicatively composed exponential tables enabled by input proximity to the maximum [du_2019]
* slots for the exponential, logarithm, accumulation, divider and square-root/reciprocal evaluators — ESHA, EFSHA and the layernorm designs expose these as modules filled by LUT, PWL or polynomial families [du_2019, hussain_2021, koca_2025, wang_2023]
* normalization_schedule online_running_max and maximum_quantization integer_ceiling — online renormalization as a shift [stevens_2021, wang_2023]
* quantization_point {before_max_subtraction, after_max_subtraction} — FP8 quantization must follow x - xmax [sun_2019]
* exp_range_reduction subtract_max_then_ln2_decompose and layernorm_sqrt integer_newton_recurrence — the I-BERT integer kernels [kim_2021]
* variance_algorithm {standard, pairwise} and degree_of_parallelism — distinguish the three-pass and two-pass layernorm schedules [koca_2025]
* exponent_output_quantization (4-bit log2 codes), layernorm_statistic_compression (8-bit to 4-bit), layernorm_square_implementation (16-entry LUT) and intermediate_storage_width — the E2Softmax/AILayerNorm buffer economics [wang_2023]
* output_representation {probability, logarithmic_ranking_only} — omitting the final exponential limits the unit to ranking consumers [yuan_2016]
