# rns_reverse_converter: proposed changes to the space

* `algorithm` values `iterative_radix_extraction` (repeated extraction through a channel fixed at 2^r), `hybrid_crt_mixed_radix` and a macrocoefficient-based conversion [guillermin_2010, chang_2015, watson_hastings_1966]
* `implementation` values `rom_plus_adder_shifter` and `table_plus_parallel_adder_network` — the filter decoder and the fully parallel mixed-radix converter combine tables with adders [jenkins_leon_1977, huang_1983]
* choice `conversion_schedule: {stage_parallel_recurrence, fully_parallel_two_stage}` — the classical digit chain and the column-parallel form differ in latency by n-1 versus 2 cycles [huang_1983]
* choice `moduli_set` with its dynamic range — {2^n-1, 2^n, 2^n+1}, {2^n-1, 2^n, 2^n+1, 2^(2n+1)-1} and {2^n-1, 2^n+1, 2^(2n), 2^(2n)+1} determine the conversion equations, hardware and internal arithmetic speed [piestrak_1995, wang_2002, molahosseini_2010]
* slot `modular_adder`/`adder_network: {csa_eac_plus_ones_complement, one_2n_bit_ones_complement, four_n_bit_cla, two_n_bit_cla_plus_incrementers}` with a `ones_complement_adder_variant: {CE_EAC_CPA, HS_dual_CPA_mux}` choice — the end-around-carry adders and their organisation are the first-order architectural decision of adder-based converters [piestrak_1995, wang_2002, molahosseini_2010]
* choices `summand_representation: quotient_remainder` and `selected_modulus: {power_of_two, power_of_two_minus_one}` — the quotient/remainder CRT depends on which channel absorbs the modular accumulation [vu_1985]
* choices `signed_output_transform: circular_then_linear_shift` and `output_scaling: {full_precision, modulus_scaled_quantized}` — signed decoding without comparison and scaled decoding with bounded quantization error are output-side options [vu_1985, jenkins_leon_1977]
* choice `zero_representation_control: NAND_in_EAC_path` — suppressing the negative zero of one's-complement adders is a distinct design decision [piestrak_1995]
* `rns_dsp_datapath` slots `input_encoder`/`output_decoder` admitting `rns_forward_encoder`/`rns_reverse_converter` [jenkins_leon_1977]
