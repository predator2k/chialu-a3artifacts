# redundant plan: applied record

Plan: `new_families/redundant.md`. File edited: `chialu/spaces/redundant_spaces.py`
only. Docs written: `arch/redundant/rns_forward_converter.md`,
`arch/redundant/rns_forward_converter/periodic_csa_moma.md`,
`arch/redundant/rns_forward_converter/channel_modular_mac.md`,
`extract/gaps/rns_forward_converter.md`. Rulings applied without re-opening:
FPU-level organization, core-level recovery/storage codes and pulse-counting
accumulators stay out (no redundant line touched them); the FPGA-mapping
ruling stands (no redundant line touched it); ALU-level structures are not
parked on adder families (no redundant line touched them);
`magic_nor_in_memory_arithmetic` is rejected as a circuit-level substrate
choice. Plan lines that target another file are deferred. The three
`online_arithmetic_unit` lines deferred by `mul.applied.md` and the
`carry_save_datapath.assimilation_point` line deferred by `adder.applied.md`
are applied here.

## applied

* `rns_channel_arithmetic.multiplier_reduction` += `iterative_carry_save_msd_estimate`; papers += noll_1991.
* `rns_channel_arithmetic` += choice `remainder_estimate_digits: IntRange(4, 5)` (noll_1991).
* `carry_save_datapath` += choice `carry_overflow_correction: Bool`, the sign-position full adder that the same plan line names in its parenthetical `+= choice carry_overflow_correction: Bool` (noll_1991 already in papers). Caveat: the plan marks it "one paper" and the `carry_save_datapath` gap file already records it, so a reviewer may drop it.
* `redundant_cordic.scale_factor_fix` += `differential`; papers += muller_2016 (base key of `muller_2016#s08`).
* `generalized_signed_digit` += choice `negation: {transfer_free, two_valued_transfer}` (parhami_1993 already in papers).
* `generalized_signed_digit` += choice `overflow_detection: {outgoing_transfer_only, real_overflow_scan}` (parhami_1993).
* `generalized_signed_digit` += choice `overflow_recovery: {guard_digit, software_exception, correction_scan}` (parhami_1993).
* `generalized_signed_digit` += choice `zero_sign_scan: {sequential, transfer_skip, transfer_lookahead}` (parhami_1993).
* `generalized_signed_digit` += choice `otf_rounding_sign_source: {exact_remainder_sign, none, estimated_b_msb}`; papers += ercegovac_1992.
* `rns_scaling_comparison.method` += `macrocoefficient_k_k_minus_1`; papers += watson_hastings_1966.
* `rns_scaling_comparison.operation` += `fractional_multiply`, `iterative_divide_sqrt` (watson_hastings_1966).
* `online_arithmetic_unit.digit_set` += `overredundant`; papers += ercegovac_2004 (base key of `ercegovac_2004#s01`).
* `online_arithmetic_unit` += choice `merged_operations: {single, sum_of_squares, multiply_add, normalization}` (ercegovac_2004).
* `online_arithmetic_unit` += choice `residual_reduction: {3_2, 4_2, 5_2}` (ercegovac_2004).
* `rns_channel_arithmetic` += choice `multioperand_adder: {none, periodic_csa_tree, periodic_csa_register}` (piestrak_1994 already in papers).
* `rns_channel_arithmetic` += choice `moma_final_converter: {rom, pla}` (piestrak_1994).
* deferred from `mul.applied.md`: `online_arithmetic_unit` += choice `operand_arrival: {both_serial, multiplicand_parallel}`; papers += pineiro_2004.
* deferred from `mul.applied.md`: `online_arithmetic_unit.radix` += 32, 64, 128, 256, 512, 1024 (now `{2, 4, ..., 1024}`) (pineiro_2004).
* deferred from `mul.applied.md`: `online_arithmetic_unit` += choice `fused_add_operand: Bool` (pineiro_2004).
* deferred from `adder.applied.md`: `carry_save_datapath.assimilation_point` += `sum_addressed_decode`; papers += silberman_1998.
* new family `rns_forward_converter` added to `rns_space` after `rns_reverse_converter`, snippet as in the plan (choices `implementation` / `chunk_bits` / `modulus_class` / `moduli_count` / `signed_input` / `final_reduction`, slots `modular_adder: cpa_space()` and `column_reducer: adder_tree_space()`, six mutations, papers jenkins_leon_1977, jullien_1978, piestrak_1994, kawamura_2000, chang_2015, all in the bibliography). The import line is now `from chialu.spaces.arith_spaces import adder_tree_space, cpa_space`; `arith_spaces` imports no space module at load time, so no cycle appears, and `linear_chain` / `binary_tree` / `csa_tree` were already lint-reachable through other slots. Docs: `arch/redundant/rns_forward_converter.md` (five references copied from the bundle's citations), `arch/redundant/rns_forward_converter/periodic_csa_moma.md` (pin `implementation: periodic_csa_moma`, from the piestrak_1994 block and the chang_2015 block), `arch/redundant/rns_forward_converter/channel_modular_mac.md` (pin `implementation: channel_modular_mac`, from the kawamura_2000 block), `extract/gaps/rns_forward_converter.md` = none. No variant doc for `rom_per_chunk` or `segmented_rom_modular_add`: the jullien_1978 and jenkins_leon_1977 blocks each list two partition settings of one table-plus-modular-adder structure, so the chunk width is the parameter and neither block pins a single value.

The absorbed entry (`on_the_fly_redundant_conversion`) and the rejected entry (`ecc_modulo_arithmetic_engine`) needed no change.

## skipped

* `rns_dnn_accelerator += choice computation_substrate: {cmos_logic, memristor_magic_nor}` [salamat_2018] — ruling: `magic_nor_in_memory_arithmetic` is a circuit-level substrate choice; the NOR-step cycle counts stay doc material.

## deferred (other file)

* `sfu_spaces.redundant_high_radix_cordic.scale_handling += differential` — the same value for the sfu twin: `dawid_1996` is already a family paper there and the family doc describes the differential form in prose (3.5N+1 full-adder delays with N stages), but neither enum carries it [muller_2016#s08] (target: `chialu/spaces/sfu_spaces.py`)
* `adder_spaces.end_around_carry.modulus += generic_p_correction` — an L-bit two's-complement adder followed by logic that detects forbidden output states or overflow and adds the fixed constant C_L = 2^L - p, the paper's generalized end-around carry hard-wired with the adder; gives `rns_channel_arithmetic.modulus_form=generic` and `rns_forward_converter.modulus_class=generic` a member in their `modular_adder` slot [jenkins_leon_1977] (target: `chialu/spaces/adder_spaces.py`)
* `adder_spaces.prefix_comparator.structure += msdf_signed_digit_fsm` — a five-state finite-state machine consumes aligned signed digits most-significant first and emits with latency 1 digit a numerically equivalent digit stream for the smaller (or, in the dual machine, the larger) operand, 350 lambda by 350 lambda in double-metal CMOS [irwin_owens_1987] (target: `chialu/spaces/adder_spaces.py`; `adder.applied.md` added the sibling `msdf_digit_serial_fsm` from taghavizade_2024, so the reviewer decides whether one value covers both)
* `adder_spaces.prefix_comparator.function += min_max_select` — the output is the selected operand's digit stream rather than an ordering flag [irwin_owens_1987] (target: `chialu/spaces/adder_spaces.py`)

applied 21 (20 value/paper lines on 6 families, 1 family), skipped 1, deferred (other file) 4

## checks

* `_all_spaces()` returns 36 spaces.
* `python3 -m chialu.archdocs`: `206 docs for 231 families; 25 undocumented; 406 variant docs`, no ORPHAN / BAD REF / BAD VARIANT line; `--strict` lists no redundant family (the 25 undocumented families are slot families of other domains, the same 25 as before this plan).
* `python3 -m chialu.extract vocab` renders.
* `kb_section_mul16()` renders.
* Every handle in a `papers=` tuple of `redundant_spaces.py` resolves in `PAPER_DB`.
