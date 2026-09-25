# streaming_accurate_accumulator: proposed changes to the space

* choices `msb_position: MSBA`, `lsb_position: LSBA`, and `maximum_summand_msb: MaxMSBX` — the three application bounds define range, accuracy, and input-shifter size, and `window_bits` alone does not place the window [dedinechin_2008, pasca_2011#s11, muller_2018#s08]
* choice `post_normalization: {omitted, software, shared_pipelined, replicated_low_frequency, dedicated_pipelined}` — how the long accumulator becomes floating point is a separate cost decision [pasca_2011#s11, dedinechin_2008]
* choice `feedback_encoding: {twos_complement, sign_magnitude}` — the encoding changes the loop-carried critical path [brunie_2017]
* choice `overflow_indicators: Bool` for sticky input-overflow/input-underflow/accumulator-overflow outputs [dedinechin_2008, pasca_2011#s11]
* a reduction-node slot that can name a residue-preserving floating-point adder rather than only a final CPA, plus `termination_detection: residue_sum_bound`, `tie_resolution: big_tie_iteration`, and `input_parallelism: m` for the tree-refinement approach, whose iteration count is variable [kadric_2016]
* choice for normalize-before-round versus round-before-normalize arithmetic — the compensated approach applies only to the former [kahan_1965]
* choice `accumulation_radix` — base 32 sets both the constant in-loop shift amount and the in-loop mantissa width, and double precision needs base 64 [vangal_2006]
* choice `alignment_reference: {aligned_to_accumulator, incoming_operand_self_align}` — the incoming summand can align itself every cycle instead of being aligned to the accumulated result [vangal_2006]
* choice `deferred_normalization_gating: {none, clock_gating, clock_gating_plus_sleep_transistor}` — the out-of-loop normalization stage is 28 percent of the devices and is gated from a software-set enable [vangal_2006]
