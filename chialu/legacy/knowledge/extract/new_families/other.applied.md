# other plan: applied

Plan: `chialu/knowledge/extract/new_families/other.md`, plus every
`## deferred (other file)` section of the sibling `*.applied.md` files.
Files edited: `chialu/spaces/fp_spaces.py`, `chialu/spaces/adder_spaces.py`,
`chialu/spaces/shift_simd_spaces.py`, `chialu/spaces/mul_spaces.py`,
`chialu/spaces/div_spaces.py`, `chialu/spaces/redundant_spaces.py`,
`chialu/spaces/approx_spaces.py`,
`chialu/knowledge/extract/gaps/back_multiply_remainder.md`. Docs written:
`chialu/knowledge/arch/div/magic_constant_bit_seed.md`,
`chialu/knowledge/extract/gaps/magic_constant_bit_seed.md` (none),
`chialu/knowledge/arch/adder/end_around_carry/generic_p_correction.md`
(variant doc; the sibling `modulus` values carry variant docs). Retired
handles are applied under their new keys: `ladner_fischer1980` (the
mismatched note) as `bund_2019`, `lee_1989` (dot plan) as `gudovskiy_2017`.

## applied

`chialu/spaces/fp_spaces.py` (2 lines):

* `rounding_space.modes += force_lsb_one_jamming, random_increment_stochastic` [richards_1955] — `modes` sits in the space's `common` dict, so `increment_adder`, `compound_adder_select`, `injection` and `flagged_prefix` all gain both values. `richards_1955` is attached to `increment_adder.papers`: the block's methods are realized at, or remove, the post-shortening increment.
* `lza.operand_source += borrow_save_pair` [seidel_2004] (shift deferred line); `seidel_2004` added to `lza.papers`. Not absorbed into `carry_save_pair`: the P-then-N recoding of the borrow-save string is its own indicator structure.

`chialu/spaces/adder_spaces.py` (6 lines):

* `prefix_comparator += choice input_code: {binary, binary_reflected_gray}` [bund_2019].
* `prefix_comparator += choice metastability_containment: Bool` [bund_2019].
* `prefix_comparator.function += two_sort_min_max` [bund_2019] — both the maximum and the minimum string are output (a 2-sort(B) element); the sorting-network composition above the unit is not registered.
* `prefix_comparator.function += min_max_select` [irwin_owens_1987] (redundant deferred line) — one selected operand's digit stream (the smaller, or the larger in the dual machine) is output. Kept distinct from `two_sort_min_max`, which emits both; the reviewer may fold one into the other.
* `prefix_comparator.structure += msdf_signed_digit_fsm` [irwin_owens_1987] (redundant deferred line) — the five-state signed-digit MSDF machine. The sibling `msdf_digit_serial_fsm` (taghavizade_2024) stays; the reviewer decides whether one value covers both. `prefix_comparator.papers` gained `bund_2019`, `irwin_owens_1987`; the `doc=` string names the 2-sort outputs and the Gray-coded containing compare. The file header carries a Rev 9 note.
* `end_around_carry.modulus += generic_p_correction` [jenkins_leon_1977] (redundant deferred line); `jenkins_leon_1977` added to `end_around_carry.papers`; the `doc=` string names the 2^L - p constant. Variant doc `arch/adder/end_around_carry/generic_p_correction.md` written from the jenkins_leon_1977 block (one reference, the only citation on file).

`chialu/spaces/shift_simd_spaces.py` (1 line):

* `masked_merged += choice field_operation: {move_only, arithmetic_logic_on_slice}` [bloch_1959] (adder deferred line); `bloch_1959` added to `masked_merged.papers`. No slice-adder slot is opened: the line is a choice line, and the slice adder is the ALU's `adder` slot (`cpa_space`).

`chialu/spaces/mul_spaces.py` (5 lines):

* `truncated_fixed_width.output_rounding += force_lsb_one_jamming, random_increment_stochastic` [richards_1955] — the integer twin of the `rounding_space.modes` line; `richards_1955` added to `truncated_fixed_width.papers`. The block's `discarded_bit_increment` is the existing `round_to_nearest`.
* `final_cpa_space.hybrid_arrival_driven.region_adder_mix += ripple_skip, ripple_skip_select` [stelling1996] (adder deferred line).
* `final_cpa_space.hybrid_arrival_driven.region_adder_mix += vba_select_cla_select_vba` [oklobdzija1996] (adder deferred line); `oklobdzija1996` added to `hybrid_arrival_driven.papers`.
* `final_cpa_space.hybrid_arrival_driven += choice boundary_search: {arrival_profile_intersection, delay_bound_boundary_enumeration}` [oklobdzija1996, stelling1996] (adder deferred line).
* `twin_precision_subword.partition += mixed_half_quarter` [codrescu_2014] (shift plan open-decision line, the 2x32x16 shape); `codrescu_2014` added to `twin_precision_subword.papers`.

`chialu/spaces/div_spaces.py` (2 lines):

* `seed_table_space += magic_constant_bit_seed` [walczyk_2021] (sfu deferred line), the plan's snippet verbatim: choices `function: {recip_sqrt}`, `floating_format`, `magic_constant_selection`, `subnormal_handling`, mutations `retune_magic_constant_for_correction`, `add_subnormal_prescale`. Doc `arch/div/magic_constant_bit_seed.md` (one reference, all the bundle has), gaps file none. No variant docs: the pinned values are format and constant-selection settings rather than named structures.
* `back_multiply_remainder += choice remainder_test: {full_residual, product_digit_compare_low_digit_zero}` [wang_2004] (decimal deferred line); `wang_2004` added to `back_multiply_remainder.papers`.

`chialu/spaces/redundant_spaces.py` (2 lines):

* `rns_channel_arithmetic += choice fused_addend: {none, injected_before_final_adder_dual_output}` [zimmermann1999] (dot deferred line); already a family paper.
* `online_pipeline_composition += choice topology: {chain, nearest_neighbor_mesh}` [irwin_owens_1987] (dot deferred line, the optional refinement); already a family paper.

`chialu/spaces/approx_spaces.py` (3 lines):

* `approximate_mac_nn.multiplier_source += power_of_two_codebook` [gudovskiy_2017] (dot deferred line); `gudovskiy_2017` added to `approximate_mac_nn.papers`.
* `approximate_mac_nn += choice codebook_terms_per_weight: Int[1..8:1]` [gudovskiy_2017].
* `approximate_mac_nn += choice codebook_index_bits: Int[3..4:1]` [gudovskiy_2017].

`chialu/knowledge/extract/gaps/back_multiply_remainder.md` (1 line):

* `selection_test` gains `midpoint_square_compare` [pasca_2011] (div deferred line; a side file for human review).

## skipped

* `dda_integrator` (new family, dot) — scope ruling: pulse-counting accumulators stay out. The plan's count line becomes new families 1, rejected 6.
* `fpga_carry_chain += choice result_merge: {output_mux, xor_with_logic_unit}` and `+= choice merge_retimed_into_forwarding: Bool` [metzgen_2004] — scope ruling: ALU-level structures are not parked on adder families; `metzgen_2004` is not added to `fpga_carry_chain.papers`.
* The cross-cutting `operation: {add_only, subtract_only, add_subtract}` choice — scope ruling, stays skipped.
* `truncated_fixed_width += choice negative_handling: {convert_to_true, ones_complement_subtract}` [richards_1955] — the block gives no result and the plan marks it the one droppable line; only the value lines of `binary_result_rounding` are applied.
* `conditional_retained_lsb_increment` — excluded by the plan until p.186 is read.
* Deferred lines already applied by a later applier: `carry_save_datapath.assimilation_point += sum_addressed_decode` (adder deferred; in `redundant_spaces.py`); `online_arithmetic_unit.operand_arrival`, `online_arithmetic_unit.radix += 32..1024`, `online_arithmetic_unit.fused_add_operand` (mul deferred; in `redundant_spaces.py`); `redundant_high_radix_cordic.scale_handling += differential` (redundant deferred; applied by the sfu applier as `differential_constant_scale`, sfu.applied.md); the fp deferred `multi_term_fused_dot` lines (`term_source`, the three `alignment_strategy` values, `cancellation_handling` applied by the dot applier; `term_count` skipped by its own condition, dot.applied.md); `hard_fp_dsp.chain_topology` (applied) and `hard_fp_dsp.chain_routing` (skipped under the FPGA-mapping ruling) by the dsp applier.
* checker deferred family `parity_prediction_divider` [nicolaidis_1997] — the checker applier's ruling stands: one incremental paper does not carry a family, and its `array` slot has no filler in `div_space()`.
* div deferred sfu alternatives (`digit_recurrence_exp_log += choice result_recurrence`, the `compose_with_division` mutation) — conditional on `continued_product_division`, which was not taken.
* The five rejected proposals of the plan (`embedding_dataflow_core`, `flexible_vector_chaining`, `ported_execution_cluster`, `slice_subslice_graphics_array`, `sorting_by_collating`): nothing to do.
* No variant docs for the new `prefix_comparator`, `rounding_space`, `truncated_fixed_width`, `hybrid_arrival_driven`, `masked_merged`, `rns_channel_arithmetic`, `online_pipeline_composition` or `approximate_mac_nn` values: they are single-paper choices or parameter settings, and the adder applier wrote none for the sibling `msdf_digit_serial_fsm`.

## still deferred

* `gray_code_converter` (new family, shift; richards_1955#s11, one textbook block, no paper). No space in `shift_simd_spaces.py` fits it: `bitcount_space` is "popcount / clz / ctz / priority encode" and is consumed by `BinaryALU` only when `popcount`/`clz`/`ctz` are provisioned, so a code converter there would be disclosed under a count op; no misc space exists; the plan's `code_converter_space()` is a one-family factory that `_all_spaces()` in `chialu/papers.py` would also have to enumerate. The plan's snippet stands for whoever opens a code-converter space; no doc was written.
* `continued_product_division` (div plan) and the two sfu lines conditional on it remain open with the div plan.

## checks

* `python3 -c "from chialu.papers import _all_spaces; s=_all_spaces(); print(len(s))"` prints 36.
* `python3 -m chialu.archdocs --strict`: `[archdocs] 233 docs for 233 families; 0 undocumented; 429 variant docs`, no ORPHAN / BAD REF / BAD VARIANT line, exit 0.
* `python3 -m chialu.extract vocab > /dev/null` passes.
* `python3 -m chialu.moves`: `[moves] 32 moves; 0 problems`.
* `kb_section_alu16()`, `kb_section_mul16()`, `kb_section_exp2()` render.
* Every handle in every `papers=` tuple reachable from `_all_spaces()` resolves in `PAPER_DB`.

applied 22 lines (21 value/choice lines on 11 families, 1 family) + 3 docs, skipped 9 entries (1 family by ruling, 2 choice lines by ruling, 1 droppable choice, 1 excluded value, 12 deferred lines already handled by later appliers, 1 checker family by ruling, 2 conditional sfu lines, 5 rejected proposals), still deferred 2 (`gray_code_converter`, the `continued_product_division` group)
