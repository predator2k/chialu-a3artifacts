# posit_quire_mac: proposed changes to the space

* `quire_width_bits` as the general 16n (N^2/2) rule or a parameterized qsize from n, es and the product count k, admitting the 32-bit posit8 quire, the 2048-bit posit64 quire and the 1024- to 1048576-bit accumulators of the origin proposal [carmichael_2019, dedinechin_2019b, gustafson_2017, mallasen_2022, sharma_2023]
* `organization` values `segmented_pipelined_cpa` (32-bit segments updated by a pipelined adder with increment FIFOs) and a `segment_width_bits: {32, 64}` choice with an `increment_fifo_entries` parameter for the segmented forms [sharma_2023, uguen_2019]
* choices `rounding_mode: round_to_nearest_ties_to_even`, `nar_handling: {sticky_flag, encoded}` and `input_exception_policy: real_inputs_only` [carmichael_2019, uguen_2019]
* choice `implementation_location: {register, software, cache_scratch}` for accumulators too wide for a register [gustafson_2017]
* choices `external_scale_factor: Bool` and `exact_accumulation_scope` for a fixed-width quire that is exact only for the smallest format [crespo_2022]
* `op_set` value distinguishing fused divide-accumulate/subtract from fused multiply-accumulate [sharma_2023]
* component slots for the posit decoder (leading-zero detector and shifter) and the fixed-point accumulator datapath [carmichael_2019]
* a fused posit MAC generator family beside `posit_adder_multiplier` and `posit_quire_mac` [zhang_2019]
