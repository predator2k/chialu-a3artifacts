# popcount_counter_tree: proposed changes to the space

* `counter_primitive` values `counter_6_3` and a `construction_method: symmetric_bit_stacking` choice — the stacking 6:3 counter is the preferred primitive of the fastest evaluated trees [fritz2017]
* `counter_primitive` value for the CDC 6600's custom 4-to-3 first-stage counter and a `first_stage_counter` choice [thornton_1970#s06]
* choices `output_scope: {total_count, prefix_population_counts}` and `stage_dependent_modulus: Bool` for the butterfly mask decoders that need every prefix count truncated to its stage's rotation period [hilewitz_2006, hilewitz_2008]
* a mixed full-adder/ROM reduction network as a `counter_primitive_mix` or `upper_reduction_adder: {ripple_carry, rom_fast_adder}` choice, and a ROM fast-adder filler for `final_adder` [swartzlander_1973]
* choices `basic_counter_arity: {2, 3, 4}` and `secondary_group_adder` for the modular Berger construction, and a `check_bit_generator` slot on the berger family that accepts popcount_counter_tree [lala_2001#s05]
* choices `vector_width_bits` and `block_vectors` for the SIMD Harley-Seal form, and a `counter_primitive` value for the AVX-512 ternary-logic CSA that cuts each carry-save step from five instructions to two [mula_2018]
