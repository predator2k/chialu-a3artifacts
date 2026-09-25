# barrel_mux_tree: proposed changes to the space

* `stage_radix` as a per-stage valency sequence (16/4/1, 8-way then 5-way, 3-2-2-2-2, 3-4-4, 5-8, 4/2/4, and a level selecting nine multiples of 16) with a `decode_style: {fully_encoded, partial_decode, fully_decoded}` choice — the fastest and the wiring-optimized designs mix radices across stages and partially decode the amount [hokenek_1990, montoye_1990, huntzicker_2008, metzgen_2004, jessani_1996]
* choice `structure: {mux_based_data_reversal, mask_based_data_reversal, mask_based_twos_complement, mask_based_ones_complement}` with `flag_generation: {post_result, parallel_masked}` and `amount_transform: {none, twos_complement, ones_complement_plus_one_bit_rotate}` — the four bidirectional constructions differ in area, delay, and flag timing [pillmeier_2002]
* choices `speculative_byte_rotate: Bool` and `output_mux_merged_stage: Bool` — a byte-bounded first stage corrected by the second select cuts wire length and fanout, and the last stage can absorb the ALU output mux [wijeratne_2007]
* choice `arithmetic_network_sharing: addition_rotation` — the rotator can reuse the parallel-prefix adder's merge cells and wiring [silberman_1998]
* choices `word_configuration: {1x64, 2x32}` and `operation_modes` for an embedded FPGA shifter block, and `final_stage_reuse` of a byte rotator [beauchamp_2008, metzgen_2004]
* choice `wrap_action: complement_on_wrap` — the LROTC rotator complements wrapping control bits and has m + 1 stages for 2m bits [hilewitz_2008]
* choices `pipeline_depth` (a register per stage), `circuit_style` (TSPC dynamic cells), `instruction_programming: {online, static}`, and an output fill choice distinguishing zero fill from sign extension [pereira_1995]
* choices `multiplexer_circuit: {ganged_tristate, pass_transistor, fanout_splitting}`, `placement: {base, zhu_swizzling, hillebrand_swizzling}`, `sizing_granularity: {uniform, uniquified}`, and `operation_subset: {all_five, shifts_only, right_rotate_only}` — the energy-delay study varies all four [huntzicker_2008]
* a single-stage crossbar topology with one-of-n diagonal selection, and `shift_function: rotate` for the N N:1-mux form [mead_conway1980#s06, gigliotti_2004]
* a shifting-network slot in `digit_recurrence_exp_log` that this family fills [ercegovac_1973]
* choice `shift_amount_source: {decoded_adder_output, sum_addressed_decode}` — the sum-addressed decode unary-decodes the carry-save shift amount and rotates the decode by the group carry, so the shift-amount CPA leaves the critical path [mueller_2005, oh_2006]
