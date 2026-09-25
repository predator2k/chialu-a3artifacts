# adder plan: applied record

Plan: `new_families/adder.md`. File edited: `chialu/spaces/adder_spaces.py`
only. Docs written: `arch/adder/digit_serial_adder.md`,
`extract/gaps/digit_serial_adder.md`. Rulings applied without re-opening:
no ALU-level line on an adder family, no pulse-counting accumulator
family, no FPGA-mapping-only value, plan lines for other files deferred.

## applied

* `carry_lookahead` (leaf, so every blocked slot too): choice `group_signal_source: {bit_gp_reduction, block_comparators}` added; papers += pasca_2011.
* `ling_prefix`: choice `propagated_function: {ling_h, doran_ling_type, doran_locally_recoverable}` added (doran1988 already in papers).
* `ling_prefix`: `order` widened from IntRange(1, 2) to IntRange(1, 4) (jackson_talwar2004 already in papers).
* `ling_prefix`: choice `radix_schedule: {uniform, mixed}` added.
* `ripple_carry` (leaf): choice `arithmetic_signal: {carry, borrow}` added; papers += richards_1955.
* `ripple_carry`: choice `subtracter_cell: {two_half_subtracters_or, half_adder_half_subtracter, direct_full_subtracter}` added.
* `ripple_carry`: choice `full_adder_logic: {two_half_adders_or, generate_propagate, xor_majority, half_sum_mux_carry}` added; papers += zimmermann1997 (shams2002 already).
* `ripple_carry.full_adder_logic` += `one_hot_operand_reduced`; papers += ansari2021.
* `ripple_carry`: choice `output_drive: {unbuffered, inverter_buffered, intermediate_buffers}` added (shams2002 already).
* `ripple_carry`: choice `pipeline_structure: {unpipelined, chunked_registered_carry, per_bit_registered_half_adder}` added; papers += hinton_2001, hatamian1986.
* `ripple_carry`: choice `chunk_width_bits: IntRange(1, 32)` added.
* `ripple_carry`: the `counter_accumulator` fallback. The family is not added (scope ruling); the plan's stated fallback, the `ripple_carry` gap file's `carry_stage_realization += counter_accumulator`, is applied as choice `carry_stage_realization: {half_adder_pair_or, factored_switching, decomposed_two_half_adders, counter_accumulator}` with the gap file's members; papers += sklansky1960b (richards_1955 already added). Caveat: the three non-counter members overlap `full_adder_logic` (both name the per-order cell composition), so a reviewer may fold them into one axis.
* `parallel_prefix`: choice `flag_outputs: {none, carry_overflow, carry_overflow_zero_negative}` added on `parallel_prefix` only (the plan line targets that family; the other prefix families are unchanged); papers += zimmermann1997.
* `parallel_prefix`: choice `zero_detect: {postsum_nor, subtraction_propagate, carry_free_add_sub}` added.
* `parallel_prefix`: choice `phased_evaluation: Bool` added; papers += lehman_burla1961. The family stays feed_forward (the plan prefers new values over a `pyramid_carry_assimilation` family).
* `prefix_comparator.structure` += `msdf_digit_serial_fsm`; papers += taghavizade_2024. The family stays feed_forward.
* `prefix_comparator`: choice `digit_encoding: {binary, posibit_negabit}` added.
* `carry_select.block_adder` slot += `parallel_prefix`, applied as a widening of `block_adder_space()`: the family now comes from one shared constructor `_parallel_prefix()` that `block_adder_space()` lists after `carry_lookahead` and `cpa_space()` lists at its former position (the leaf copy is filtered out of `cpa_space` so no family name is duplicated). The widening therefore reaches `carry_skip.block_adder`, `carry_select.block_adder`, `carry_increment.block_adder`, `speculative_variable_latency.base_adder`, `sparse_prefix_hybrid.sum_block`, `approximate_truncated.upper_adder` and `digit_serial_adder.digit_adder`; `parallel_prefix` opens no slot, so the recursion still bottoms out at the leaf. Disclosure order of `cpa_space` is unchanged.
* `carry_select.block_sizing` += `delay_matched_doubling`, `equal_power_sized` (tyagi1993 already in papers).
* new family `digit_serial_adder` appended to `cpa_space` after `fpga_carry_chain`, snippet as in the plan (`execution_style="fixed_iteration"`, choices `digit_width_bits` / `carry_state` / `subtraction`, slot `digit_adder: block_adder_space()`, papers ercegovac_2004, sklansky1960b, richards_1955). Docs: `arch/adder/digit_serial_adder.md` (three references, copied from the bundle's citations; sklansky1960 is not cited because its note is a mismatch for the same evaluation paper), `extract/gaps/digit_serial_adder.md` = none. No variant doc: the pinned values (`unit_delay` carry feedback, the complement policies) are circuit realizations or operation modes rather than named structures.

Absorbed entries (`binary_counter_compressor`, `independent_dependent_carry`, `rom_lookup_adder`) and rejected entries (`commercial_binary_execution_unit`, `kirchhoff_threshold_adder`) needed no change.

## skipped

* `carry_lookahead.intergroup_carry += fast_carry_chain_ccc_cr` — FPGA-mapping ruling: the value names the device's fast-carry-chain network with carry recovery, which is a mapping of the block carry onto the hard chain rather than a datapath structure. `group_signal_source=block_comparators` (the CCA structure itself) is applied above.
* `ripple_carry += choice early_forward_low_chunk: Bool` — ALU-level: the forwarding of the low chunk to a dependent operation is the ALU bypass loop, not adder structure. The adder-level content of the same paper (`pipeline_structure=chunked_registered_carry`, `chunk_width_bits`) is applied above.
* `ripple_carry += choice flag_stage: Bool` — ALU-level: the flag phase of the staggered ALU pipeline; `ripple_carry` produces no flags.
* `manchester_carry_chain += choice function_control: {fixed_add, programmable_pkr}` — ALU-level: the P/K/R truth-table fabric programs the whole operation set (the proposal is `programmable_pkr_alu`, and the plan's open decision places it on an ALU wrapper together with the two lines below).
* `manchester_carry_chain += choice carry_in_source: {zero, one, flag, complemented_flag}` — ruling: Mead-Conway carry-in choice is ALU-level.
* `manchester_carry_chain += choice conditional_operation: {unconditional, multiply_step, divide_step, and_or}` — ruling: Mead-Conway conditional-operation choice is ALU-level.
* `cpa_space (every family) += choice operation: {add_only, subtract_only, add_subtract}` — ruling: cross-cutting ALU-level choice, not parked on adder families.
* new family `counter_accumulator` — ruling: the 1946–1955 pulse-counting accumulators stay out as families; the plan's fallback value is applied (see applied).

## deferred (other file)

* `mul.final_cpa_space.hybrid_arrival_driven.region_adder_mix += ripple_skip, ripple_skip_select` — heterogeneous ripple-carry / one-level carry-skip blocks sized and placed to the known per-bit arrival times (23.75 against 25.75 equivalent XOR delays for the 32-bit Latest-Earliest TDM profile), and the same block set with one carry-select block (20.25 against 22.625; 10% over a CLA final adder in a 32 x 32 multiplier); the `region_adder` slot already admits `carry_skip`, so absorbed is defensible [stelling1996]
* `mul.final_cpa_space.hybrid_arrival_driven.region_adder_mix += vba_select_cla_select_vba` — region 1 (positive arrival slope) is ripple carry or a variable-block adder, region 2 (maximum delay) is carry-select with CLA blocks, region 3 (negative slope) is carry-select with variable-block-adder blocks; `region_count=3`, `arrival_model=measured_tree_profile`, and the variable-block adder is `carry_skip.block_sizing=trapezoidal_variable` in the slot; oklobdzija1996 is cited only under `csa_reduction_tree` and joins this family's papers [oklobdzija1996]
* `mul.final_cpa_space.hybrid_arrival_driven += choice boundary_search: {arrival_profile_intersection, delay_bound_boundary_enumeration}` — the region boundaries S1/S2 are the integer positions where the candidate-adder delay curves meet the arrival profile, found iteratively so that selection occurs at the required time, or a search over the delay bound and every legal block boundary under the permitted block set; the timing basis (equivalent XOR delay against raw gate delay) and the area/power constraints are search parameters rather than structure; the `carry_select` gap file lists the same choices as `arrival_profile_regioning` / `region_boundary_method` [oklobdzija1996, stelling1996]
* `redundant.carry_save_datapath.assimilation_point += sum_addressed_decode` — one dynamic gate merges the low 12 bits of two operands into a nonunique carry-free sum whose upper six bits drive a self-strobing NOR row decoder directly, with the remaining bits in column select and alignment, so no CPA sits on the load/store path (1.15 ns cycle at 0.25 µm); a single-paper value whose only choices are single-valued [silberman_1998]
* `shift.masked_merged += choice field_operation: {move_only, arithmetic_logic_on_slice}` — the Stretch serial arithmetic unit: a switch matrix extracts 16 consecutive bits from each 128-bit register pair, a wrap-around circuit aligns the field's low-order bit at the right, a CPA or logic unit processes the slice with true-complement or binary-to-decimal post-processing, and the inverse matrix reinserts the result without disturbing the neighbouring positions, all in one cycle (2.0 µs variable-field ADD for 1 to 64 bits; 10,000 datapath transistors); `deposit_path=True` covers the move-only case, and the slice adder is `cpa_space`; the `masked_merged` gap file's rotation/addition merge-network sharing [silberman_1998] is the same direction [bloch_1959]

applied 20 (18 new-value lines, 1 family, 1 fallback value), skipped 8 (7 lines, 1 family), deferred 5

## checks

* `_all_spaces()` returns 36 spaces.
* `python3 -m chialu.archdocs`: `191 docs for 192 families; 1 undocumented; 392 variant docs`, no ORPHAN / BAD REF / BAD VARIANT line. The undocumented family is `direct_polynomial` in `chialu/spaces/div_spaces.py` (the div plan's family, no adder doc missing).
* `python3 -m chialu.extract vocab` renders.
* `kb_section_mul16()` and `kb_section_alu16()` render.
* Every handle in a `papers=` tuple of `adder_spaces.py` resolves in `PAPER_DB`.
