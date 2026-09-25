# Deferred families

This document records the families, the choice values and the spaces
that chiALU does not realize in this version, the rule that defers
them, and what the later version needs to bring them back.

## The rule

Every unit chiALU generates in this version is single-cycle and
combinational: one operation per vector, no registers, the combinational
delay and area as the synthesis metrics. A family is deferred when its
defining structure needs cycles (a datapath reused over iterations, a
data-dependent latency, a recomputation in a later cycle), when it is
state or an interface the unit does not carry, when it is a system-level
kernel larger than one unit's operation, when it is a method rather
than a structure, or when no unit template opens its space. The same
rule applies to a choice value whose structure needs cycles.

* A deferred family is removed from the family spaces, so no menu
  offers it and no declaration can name it. Its knowledge card and
  variant cards move to `legacy/knowledge/deferred/arch/<domain>/`, and
  its `Family(...)` definition is kept verbatim in
  `legacy/knowledge/deferred/spaces_deferred.py`.
* A deferred choice value leaves its enum (or its sub-slot space, when
  the value is a family of that space). Its variant card moves the same
  way, the enum's original text is recorded in `spaces_deferred.py`, and
  the generator branch that raised on the value is removed.
* A deferred space's factory is removed from `chialu/spaces`, and
  `chialu/papers.py` and `chialu/extract.py` drop it from
  `_all_spaces()`.

The verify layer keeps the spec fields `latency_cycles` and
`variable_latency_max` for the later version; no unit template sets
them. The knowledge path holds 198 family cards and 341 variant cards;
`legacy/knowledge/deferred/arch/` holds 42 family cards and 88 variant
cards.

## The 21 families deferred on 2026-09-12

| Family | Domain | Class | Recorded reason |
| --- | --- | --- | --- |
| speculative_variable_latency | adder | sequential structure | the rare long carry takes a spare cycle |
| digit_serial_adder | adder | sequential structure | one digit adder reused over the cycles |
| sequential_shift_add | mul | sequential structure | one adder row reused over the cycles |
| serial_serial_parallel | mul | sequential structure | bit- or digit-serial operands over the cycles |
| iterative_reuse | mul | sequential structure | a fractional tree cycled with an accumulator |
| self_timed_variable_latency | div | sequential structure | the cycle count follows the data |
| variable_latency (fp adder) | fp | sequential structure | completes in a data-dependent number of cycles |
| iterative_decimal_multiplication | decimal | sequential structure | one or two multiplier digits per cycle into a carry-save accumulator |
| time_redundancy | checker | sequential structure | a recomputation of a transformed operation over cycles (RESO, REDWC, Razor sampling); the checker is combinational |
| lane_width_gating | shift (subword) | sequential structure | narrow-operand detection funds clock gating and packed scheduling: a sequential control |
| posit_quire_mac | dsp (posit) | state outside the unit | the quire is an accumulator register across operations and the ALU has no accumulate op |
| vector_lane_masking | shift (subword) | interface outside the unit | the lane mask is architectural state the unit interface does not carry |
| rns_dsp_datapath | redundant | system-level kernel | a MAC-chain kernel (FIR/IIR/FFT) rather than an ALU op |
| rns_montgomery_crypto | redundant | system-level kernel | Montgomery multiplication in two bases: a cryptographic kernel |
| rns_dnn_accelerator | redundant | system-level kernel | inner products with per-layer conversion: an accelerator kernel |
| abft_checksum | checker | system-level kernel | a checksum over a matrix of dot products; the dot unit computes one inner product per output |
| self_checking_datapath | checker | outside the checker seam | the core itself would emit codewords (dual-rail carries, m-out-of-n or Berger outputs), which the interface does not carry |
| approximate_mac_nn | approx | method | a per-layer multiplier selection method |
| approximate_logic_synthesis | approx | method | a synthesis method under an error bound |
| error_analysis_quality | approx | method | the evaluation discipline |
| correct_rounding_strategy | sfu | method | a methodology over another evaluator (Ziv retry, worst-case precision, coefficient synthesis) |

The `approx_method` slot of an approximate ALU held the three method
families alone, so the slot is gone with them. The subword family list of
`targets/int_subword_alu.yaml` drops lane_width_gating. The realization
count of the family library is 155 of 155 declarable families; the
coverage check of `docs/work-plan.md` item 2 restates it.

## The nine choice values deferred on 2026-09-12

Each value was a member of a realized family's enum, or a family of a
sub-slot space, whose structure needs cycles. The generator raised on
each of them before; the tables `SEQUENTIAL_FP`, `SEQUENTIAL_SFU` and
the matching entries of `dot.EXCEPTIONS` are gone with the values.

| Value | Where it was | Recorded reason | Card moved |
| --- | --- | --- | --- |
| `trap_to_software` | fp adder `subnormal` slot, a family of `subnormal_space` | a software trap on subnormals has no hardware realization in a combinational unit | `arch/fp/trap_to_software.md` |
| `shared_multiplier` | SFU `evaluator` slot, a family of `poly_datapath_space` | one multiplier time-shared across the terms of a polynomial is a multi-cycle datapath | `arch/sfu/shared_multiplier.md` |
| `microcoded_fpu_sequence` | `sharing` of every SFU family (`SHARINGS`) | a microcoded sequence over an FPU is a multi-cycle program | none existed |
| `folded_sequential` | `cordic.topology` | the folded CORDIC reuses one stage over the cycles | `arch/sfu/cordic/folded_sequential.md` |
| `msdf_online_serial` | `transformer_activation_lut.method` | a most-significant-digit-first serial evaluator with early termination is digit-serial | `arch/sfu/transformer_activation_lut/msdf_online_serial.md` |
| `sequential_reuse` | `add_table_add.table_access` | one table read per cycle over several cycles | none existed |
| `bit_serial_composable` | `integer_mac.array_style` | the products are formed bit-serially over cycles | none existed |
| `compensated_two_sum` | `streaming_accurate_accumulator.approach` | the compensation term is carried across the loop of operations; one operation has no loop | `arch/dot/streaming_accurate_accumulator/compensated_two_sum.md` |
| `ordered_fp_loop_lookahead` | `streaming_accurate_accumulator.approach` | the lookahead reorders the loop-carried additions across operations | `arch/dot/streaming_accurate_accumulator/ordered_fp_loop_lookahead.md` |

Two consequences of the removals:

* `cordic.topology` keeps its one remaining member, `unrolled_pipelined`,
  so the variant card of the unrolled form stays valid; the later
  version re-extends the enum.
* The mutation `add_compensation_term` of `streaming_accurate_accumulator`
  left with the approach it named.

## The three groups deferred on 2026-09-12

No unit template opened these spaces, or the family was a core
partitioning whose structure is time-shared or streaming.

| Family | Space | Class | Recorded reason |
| --- | --- | --- | --- |
| online_arithmetic_unit | `online_space` (redundant) | sequential structure | one result digit per cycle after the on-line delay |
| online_pipeline_composition | `online_space` | sequential structure | a pipeline of on-line operators over cycles |
| redundant_cordic | `online_space` | sequential structure | CORDIC iterations over cycles; the SFU's cordic families realize the unrolled rotations |
| bit_serial_dnn_datapath | `online_space` | sequential structure | bit-serial MACs whose cycle count follows the precision |
| online_msdf_core | core family (`chialu/modules/alu.py`) | sequential structure | digit-serial MSDF operators stream over cycles; it opened `online_space` as its `operators` slot |
| merged_mul_div | core family (`chialu/modules/alu.py`) | sequential structure | the divider reuses the multiplier (Newton-Raphson or Goldschmidt) over cycles |
| dsp48_style_slice | `dsp_block_space` (dsp) | no unit template | the DSP48 lineage as a unit: pre-adder, asymmetric multiplier, wide SIMD ALU, pattern detector, cascades |
| variable_precision_dsp | `dsp_block_space` | no unit template | one block with several native multiply widths |
| hard_fp_dsp | `dsp_block_space` | no unit template | hardened IEEE floating point inside the DSP block |
| ai_tensor_block | `dsp_block_space` | no unit template | hard dot-product arrays with cascade chains |
| multiprecision_block_proposal | `dsp_block_space` | no unit template | deeper fracturing and runtime composition of the block |
| embedded_fpu_block | `dsp_block_space` | no unit template | a hard fp64 multiply-add block in fabric columns |
| decimal_fp_addition | `decimal_misc_space` (decimal) | no unit template | IEEE 754 decimal add on DPD-stored significands |
| bid_fp_addition | `decimal_misc_space` | no unit template | decimal add on BID significands kept binary |
| decimal_fma | `decimal_misc_space` | no unit template | a times b plus c with one decimal rounding |
| decimal_fp_multiplication | `decimal_misc_space` | no unit template | decimal multiply with one decimal rounding |
| decimal_encoding_codec | `decimal_misc_space` | no unit template | the DPD and BID encodings and their placement |
| binary_decimal_conversion | `decimal_misc_space` | no unit template | binary to decimal and decimal to binary conversion |
| redundant_decimal_conversion | `decimal_misc_space` | no unit template | redundant decimal digits to and from BCD |
| decimal_cordic_transcendental | `decimal_misc_space` | no unit template | decimal pseudo-division and CORDIC for log, exp and trig |
| commercial_decimal_fpu | `decimal_misc_space` | no unit template | the shipped decimal floating-point units' organization |

The core families `online_msdf_core` and `merged_mul_div` had no card;
their `Family(...)` blocks are recorded in `spaces_deferred.py` with the
previous `core_families` function. The `div_space` family `online_msdf`,
which is a combinational shift-and-subtract array in `families/div.py`,
is unrelated to the on-line group and stays.

## Choices, slots and families removed under the coverage check (2026-09-12)

The coverage check (`python3 -m chialu.targets.rtl.families.coverage`,
`docs/work-plan.md` item 2) reports every design choice and slot a
generator ignores. The rule that decides them: a choice or slot stays in
a space only if it selects a structure the single-cycle binary unit
realizes and that changes the module's netlist. A choice that names a
sequential or circuit-level property, an interface or an op the unit
does not carry, or an output subset synthesis prunes, is removed and
recorded here with its reason; the others are realized.

The leaf families (the shifters, the bit counters, the comparator, the
logic row):

| Family | Item removed | Reason |
| --- | --- | --- |
| barrel_mux_tree | `crosspoint_control` (diagonal_one_hot, arbitrary_n2) | the n-squared crosspoint control of a crossbar needs a per-crosspoint control input; the unit's shifter is controlled by the amount |
| funnel | `input_forming` (duplicate_for_rotate, sign_extend, zero_fill, two_register_pair) | the window is formed per op (the first three are what a rotate, an arithmetic and a logical shift need); the register pair needs a double-width shift op the unit lacks |
| funnel | `amount_preprocess = none` | an offset precomputed outside the unit; the one's complement and the subtraction from N are realized |
| masked_merged | `deposit_path` | an insert op the unit lacks |
| masked_merged | `subword_boundary` (cross, block) | lane packing is the subword slot's |
| masked_merged | `field_operation` (move_only, arithmetic_logic_on_slice) | sharing the merge network with the adder is a unit-level sharing family rather than the shifter's |
| butterfly_network | `network = butterfly_inverse_pair, butterfly_two_inverse` | the permutation and grp networks serve ops the unit lacks (the variant card butterfly_inverse_pair is under legacy) |
| butterfly_network | `mask_binding` (static, loop_invariant, dynamic) | control registers and decode latency: an ISA and pipeline property |
| butterfly_network | `control_generation` and the slots `prefix_popcount`, `lrotc_rotator` | the hardware mask decoder serves pex and pdep, which the unit lacks; the rotation's controls are a closed form of the amount |
| fpga_mapped | the family | FPGA fabric mapping is outside the ASIC scope (the card and its variant dsp_multiplier are under legacy) |
| popcount_counter_tree | `lane_taps` | the prefix taps serve the butterfly mask decoder |
| lzd_cell_tree | `formulation` (hierarchical_valid_position, carry_lookahead_flags) | the hierarchical form is the family itself; the carry-lookahead formulation is the prefix_lzc family's `count_form = lookahead_flags` (the variant card moved there; hierarchical_valid_position is under legacy) |
| lzd_cell_tree | `count_output` (binary_position, decimal_digit_count) | the decimal digit count is the decimal families' |
| recursive_doubling_lzd | the family (fp `lzc_space`) | the same structure as lzd_cell_tree (Oklobdzija's block tree); merged: `tree_radix` is `block_primitive`, `output_form` and `valid_flag_propagation` are lzd_cell_tree's choices now (the card is under legacy) |
| prefix_comparator | `function` (equality_only, magnitude, full_ordering, min_max_select, two_sort_min_max) | the op set fixes which outputs are used; an unused output is pruned by synthesis |
| prefix_comparator | `structure = msdf_digit_serial_fsm, msdf_signed_digit_fsm` | digit-serial state machines: sequential |
| prefix_comparator | `structure = subtractor_carry_out` | became the family subtractor_comparator, whose `subtractor` slot names the adder and whose `zero_detect` picks the equality source |
| prefix_comparator | `digit_encoding` (binary, posibit_negabit), `input_code` (binary, binary_reflected_gray) | the unit's operands are binary |
| prefix_comparator | `metastability_containment` | a synchronizer property |
| lane_replicated_gates | `sign_ops` (per_lane, masked) | the float sign ops are the float lane's |
| wide_gate_row | `sign_mask` (mode_mux, precomputed_table) | the same |
| alu_pg_fused | `pg_source`, `or_form` | the fusion is the synthesizer's sharing inside the lane; the seed cannot bind the adder's internal propagate definition |
| prefix_and_incrementer | `dual_direction` | a decrement mode needs a direction input; the unit's incrementer uses (rounding, negation, carry-increment blocks) increment alone |

The same batch realized what stayed: the shifters' `stage_radix`,
`select_encoding`, `direction_handling` (all three values), `stage_order`
and `sticky_collect` (every shifter module now has a `sticky` output),
the funnel's `window_mux_radix` and `amount_preprocess`, the masked
family's `mask_generator`, `merge_style` and its rotator slot's pins,
the butterfly's `network`; the bit counters as generated modules
(`families/count.py`) with the popcount's `counter_primitive`,
`tree_shape` and `final_adder` slot, lzd_cell_tree's `block_primitive`,
`output_form` and `valid_flag_propagation`, prefix_lzc's
`prefix_topology`, `count_form` and `counter` slot, the priority
encoder's `levels` and `output_form`, trailing_zero's three strategies,
`isolate_circuit` and the new slots `lzd` and `negation_incrementer`;
the comparator's `radix` and the subtractor form's adder slot
(`families/comparator.py`); the logic row's `not_via_xor`. The float
datapath's `lzc_space` is defined once with the bit-count families
(`shift_simd_spaces.lzc_space`).

The adder families (the carry-propagate adders of `cpa_space`):

| Family | Item removed | Reason |
| --- | --- | --- |
| ripple_carry | `full_adder_cell` (static_cmos_mirror, transmission_gate, transmission_function, hybrid_pass) | transistor-level cell styles |
| ripple_carry | `carry_stage_realization` (4 values) | the same axis as `full_adder_logic`, which is realized (four gate-level forms of the cell) |
| ripple_carry | `carry_polarity_alternation` | an inverter-saving circuit property; synthesis chooses the polarities |
| ripple_carry | `arithmetic_signal` (carry, borrow), `subtracter_cell` (3 values) | the lane subtracts through the adder with the complemented operand and a carry-in; a borrow chain is another interface |
| ripple_carry | `output_drive` (unbuffered, inverter_buffered, intermediate_buffers) | buffering |
| ripple_carry | `pipeline_structure` (chunked_registered_carry, per_bit_registered_half_adder) | registered chains: sequential (the later version) |
| manchester_carry_chain | `circuit_style` (dynamic, static, transmission_gate) | circuit style |
| carry_lookahead | `block_sizing` (uniform, dp_optimized) | a per-group size schedule needs a delay model the space does not carry; the group size is the lookahead's fan-in (the variant card dp_optimized is under legacy) |
| carry_lookahead | `group_signal_source` (bit_gp_reduction, block_comparators) | two formulations of the same group propagate that synthesis maps alike |
| conditional_sum | `mux_style` (static_gate, transmission_gate) | circuit style |
| carry_select | `block_sizing = equal_power_sized` | transistor sizing |
| carry_select | `duplication = bec_increment` | merged into `shared_add_one` with the `add_one` incrementer slot at structure ripple_and_chain, which is the binary-to-excess-one converter (the variant card is under legacy) |
| parallel_prefix | `wire_track_budget` | Harris's t follows from l and f (l + f + t = log2 n - 1) |
| parallel_prefix | `node_style` (and_or, aoi_oai_alternating, dynamic_domino), `phased_evaluation` | circuit style and dynamic-logic phasing |
| parallel_prefix | `flag_outputs`, `zero_detect` | the lane forms its flags from the sum and the carry-out; the adder interface carries no flag ports |
| ling_prefix | `order` (1 to 4) | the second-order factoring's pre-signals (Jackson and Talwar) are not in the library: not realized in this version |
| ling_prefix | `propagated_function` (ling_h, doran_ling_type, doran_locally_recoverable) | Doran's transfer-function variants are not in the library: not realized in this version |
| ling_prefix | `radix_schedule` (uniform, mixed) | a mixed-radix level schedule needs a valency per level; the valency choice is parallel_prefix's |
| prefix_synthesis_nonuniform_arrival | `search_method` (dynamic_programming, heuristic_rewrite, reinforcement_learning) | the method that produced a graph rather than the graph; the library's greedy construction stands (the variant cards are under legacy) |
| prefix_synthesis_nonuniform_arrival | `fanout_cap` | a duplicated node is merged back by synthesis: not a netlist freedom in this flow |
| prefix_synthesis_nonuniform_arrival | `region_hybridization` | the greedy construction adapts per position; a region split needs a region rule the card does not give: not realized in this version |
| fpga_carry_chain | `ternary_packing` | a three-operand chain cell needs a third operand the adder interface lacks |

The same batch realized what stayed: ripple_carry's `full_adder_logic`
(four cell forms) and chunking; manchester_carry_chain's segments with
`variable_skip`; carry_lookahead's `levels` (a recursive lookahead over
groups of groups) and `intergroup_carry` select; conditional_sum's
`base_block_width` and `selection_radix`; the block-composed families
generated by `families/adder_ext.py` around the `block_adder` slot's
library adder, with carry_skip's `block_sizing` (uniform, trapezoidal,
a unit-delay dynamic program), `skip_levels` and `skip_gate`,
carry_select's `block_width` (declared now), `block_sizing` (uniform,
square-root ramp, a unit-delay dynamic program, doubling), `duplication`
through the new `add_one` incrementer slot and `select_source`,
carry_increment's `block_sizing`, `intergroup_carry`, `increment_levels`
and its `increment_stage` slot; sparse_prefix_hybrid as a generated
module (its `tree_topology`, `valency`, `sum_block_style` and `sum_block`
slot); parallel_prefix's `valency` (radix-3 and radix-4 nodes for
sklansky, kogge_stone and brent_kung; the other topologies reject a
valency above 2); ling_prefix's `pseudo_carry_group` (blocks of 1 to 4
bits) and `sum_recovery`; compound_flagged_prefix's `outputs` (a `sm1`
port), `implementation` (a second carry tree) and `late_carry_in`, with
`log2_sparsity` and `fanout_cap` declared for its harris point (and for
end_around_carry's); end_around_carry's `modulus_value` (declared) and
its `incrementer` slot; approximate_truncated's `speculation_window`
(declared) and `correction_incrementer` slot; fpga_carry_chain's
`prefix_over_chain`. block_adder_space gains conditional_sum. The
prefix generator no longer reads `tree_topology` for every family.

The dot families (the accumulators and the FMA lineage of
`dot_acc_space`, `families/dot.py`):

| Family | Item removed or changed | Reason |
| --- | --- | --- |
| every accumulator family | the `align` slot's space is the dot's own (`fma_dot_spaces.dot_align_space`): full_align with its shifter slot; bounded_align with `sticky_method`, `bound`, its shifter slot and a `tzc` slot | the fp adder's `swap_before_shift` orders two operands before one shifter, which a multi-term alignment has no place for (every term shifts by its own amount); the shifter slot carries the radix |
| fused_two_term_dot, streaming_accurate_accumulator, tensor_core_mixed_precision_mac | the `align` slot's space is `dot_window_align_space` (full_align with its shifter slot alone) | their terms align to a window at the largest exponent or per tree level, where the band of the products has no separate addend path |
| multi_precision_simd_fma, fused_two_term_dot, multi_term_fused_dot | the `round` slot | the seed rounds their result once; no partial result is rounded inside (the tensor-core and fp8 datapaths keep the slot for their partial sums) |
| bf16_fma_datapath | the alignment of a floating-point mode is the frame (it was the window at the largest exponent, which under the exact contract is wider than the frame) | the family names the products and the accumulate, not the alignment; the frame admits bounded_align |

The same batch realized what stayed: the `align`, `lza` and
`norm_shifter` slots of every accumulator family (the alignment shifter,
the anticipator or counter and the normalize shifter of the final
normalization), the `round` slot of the tensor-core and fp8 datapaths
(the library rounder of the partial sums), bounded_align as the banded
alignment (`docs/work-plan.md` item 4, the card
`arch/fp/bounded_align.md`), the realignment lines of
`exponent_sorted_realignment_lines` (its card), the kulisch width range
64 to 4288, and the `_cpa_of` default as the sklansky prefix adder.

The multiplier families (`mul_spaces.py`; the approximate space's
multipliers, the decimal multiplier and twin_precision_subword belong to
their own batches):

| Family | Item removed | Reason |
| --- | --- | --- |
| hybrid_arrival_driven (final CPA) | the `region_adder` slot | the region adders' families are the `region_adder_mix` choice's kinds (ripple, skip, lookahead, select, variable-block skip), one per region |
| csa_reduction_tree | `geometry = overturned_stairs` | Mou-Jutand's connector-and-branch construction is a layout regularity of the same 3:2 counters; its netlist is a Wallace-class tree's |
| csa_reduction_tree | `tree_order`, `os_branch_tree` | the branching order of the regular-layout trees (Zuras-McAllister, overturned stairs): a layout organization; the delay-balanced schedule realized combines the earliest bits |
| csa_reduction_tree | `tdm_objective` | the undominated-profile objective is a tree-and-CPA co-design method (Stelling 1998); the greedy realizes the mini-max schedule |
| csa_reduction_tree | `pipeline_cut_levels` | latches between levels: sequential |
| compressor_4_2_tree | `circuit_style` (static_cmos, pass_transistor, cpl) | a circuit style |
| compressor_4_2_tree | `levels_pipelined` | registers between levels: sequential |
| booth_recoded_parallel | `hard_multiple_gen = none` | radix 4 needs no hard multiple and radix 8 and 16 cannot do without one; the generation form is the choice |
| direct_pp_parallel | `signed_scheme = unsigned, modified_baugh_wooley` | the mode fixes the signedness; in the column model the original and the modified Baugh-Wooley forms complement the same sign-bit terms and add the same constant (`baugh_wooley` stays, `sign_extension` is the other form) |
| direct_pp_parallel | `first_level_fusion` | the fusion of the partial-product AND into the first counter is a cell-library matter |
| direct_pp_parallel | `output_form` (assimilated, sum_carry) | a redundant sum/carry output is an interface the multiplier slot does not carry (the dot unit's fused families keep their own) |
| carry_save_array | `signed_scheme = unsigned, modified_baugh_wooley` | the same as for direct_pp_parallel (`pezaris_negative_weight` is realized with negative-weight cells) |
| carry_save_array | `rows_per_pipeline_stage` | bit-level pipelining: sequential |
| recursive_karatsuba | `base_multiplier = fpga_dsp_block` | an FPGA DSP block is outside the ASIC scope (the variant card is under legacy); `direct_tree` joins array and booth_tree |
| truncated_fixed_width | `output_rounding = random_increment_stochastic` | a random source the unit does not carry |
| approximate_compressor | `error_recovery_stages = 0` | zero recovery stages is the plain compressor technique; the range starts at one |
| squarer | `combined_signed_unsigned` | a control input selecting the signedness at runtime: the mode fixes it |
| segmented_grid | `mode_select` (fixed_wide, runtime_wide_or_lanes) | a runtime lane mode is the subword slot's interface |
| segmented_grid | `composition` (spatial, temporal, spatio_temporal) | temporal reuse of the blocks over cycles: sequential |

The same batch realized what stayed: the reduction slot's three families
(the counter tree in five geometries over 3:2, 4:2, 5:2 and 7:3
counters; the compressor tree over 4:2, 5:2, 7:3 and
symmetric-stacking 6:3 cells; the tiled CPA tree with its adder width,
carry assimilation, terminal reduction and `tile_adder` slot), the
hybrid final adder's regions, Booth radix 16 with the hard multiples
through the `hard_multiple_adder` slot, as partially redundant short
adders or through the lookahead specialized to a + 2^k a, Roorda's
compact sign extension, the precomputed negative multiples through the
new `negation_incrementer` slot, the 2-bit groups with the 3M
precompute, the Pezaris array, Karatsuba's three-way and rectangular
splits with its adds through the new `adder` slot and its base trees
over the `reduction` slot, the squarer's signed squares with the new
`cross` and `pre_adder` slots, the logarithmic multiplier's `lod`,
`normalize_shifter`, `log_adder`, `antilog_shifter` and `exact` slots,
DRUM's `lod`, `normalize_shifter` and `core` slots, the segmented
grid's rectangular shape, recursion depth and `segment` and
`merge_tree` slots, the redundant binary multiplier's radix-2 Booth
rows, and module names that carry a tag of their pins.

The special-function families (`sfu_spaces.py`, `families/sfu.py`):

| Family | Item removed or changed | Reason |
| --- | --- | --- |
| every evaluator family | new slots `adder`, `shifter`, `lzc` and (with a variable multiply) `multiplier`; a value table (direct_lut, compressed_lut) carries none | the `Net` primitives (add, subtract, multiply, variable shift, leading-zero count) rendered as the language's operators; a declared family now renders through the library module (`Net.bind`), a constant multiply stays an operator (synthesis folds it), and a primitive under 4 bits stays an operator |
| every family | the module name carries a 48-bit tag of the pins | two pin sets rendered two texts under one name |

The float families (the significand adders, multipliers, comparators,
divider and square-root wrappers, the rounder, the unpacker and the
converter; the generator is `families/fp.py`):

| Family | Item removed | Reason |
| --- | --- | --- |
| single_path, two_path, delay_optimized_unified, low_power_gated | `dependent_result_forwarding` (none, redundant_packet_two_cycle, ...) | result forwarding between dependent ops is a pipeline property; the single-cycle unit has one result |
| single_path | `pipeline_depth`, `post_round_renorm` | the depth is sequential; the renormalization after a rounding carry is the rounder's (every rounding family carries it) |
| two_path | `shared_rounding` | the unit's rounder rounds once after the path mux; a rounder per path is the unit's sharing |
| delay_optimized_unified | `lz_count_source` (exact_operands, approximate_borrow_save) | the approximation over the redundant borrow-save difference is a circuit-level form of the same count; the library anticipates from the operands (the variant cards are under legacy) |
| low_power_gated | `clock_gate_inactive_paths`, `speculative_rounding`, `lz_logic_style` (full_lza, pseudo_lza, low_power_lzc) | clock gating is sequential (the unit isolates the inactive partition's operands, which `datapath_partitions` realizes); speculative rounding is the rounder's compound_adder_select; the anticipator's family is the lz slot (the variant card pseudo_lza is under legacy) |
| the fp add families' `subnormal` slot (full_hardware, flush_to_zero_mode) | the slot | the representation choice became the family choice `subnormal_representation` (as_stored, pseudo_normalized_wide_exponent); `denorm_result_shift` names the rounder's shifter, `extra_latency_cycles` is sequential; flush to zero is the mode's ftz/daz option (the cards are under legacy) |
| the fp add families' `round` slot; the multipliers', dividers' and square root's `round`, `exp` and `subnormal` slots | the slots | the arithmetic structures deliver X values; the unit's rounder rounds them (the `round` slot lives on the rounder and the converter); the exponent adder became the `exp_adder` slot; the subnormal operands of a divider or square root are normalized by the new `norm_lzc` and `norm_shifter` slots |
| exponent_path | `tentative_exponent`, `overflow_check_point`, `bias_handling` | the tentative exponent is the larger operand's (one mux); the range check is the rounder's, after rounding; the internal exponent is the engine's unbiased exponent of bit 0 |
| full_align | `mux_radix` | the shifter slot's `stage_radix` |
| full_align | `swap_before_shift` | became the fp add families' `operand_order` (swap_before_shift, shift_each_operand): the order is the datapath's, since the unswapped form needs two shifters and two subtractors |
| bounded_align | the family (`bound`) | the engine's X keeps every bit of the alignment window and its stochastic rounding compares the dropped bits exactly, so a shift bound below the window changes the packed result (the harness found it at bf16 and fp8e4m3 under the stochastic mode); the only exact bound is the window, which is full_align (the card is under legacy) |
| coarse_fine, single_barrel | `correction_shift_stage`, the `lz` slot | the one-bit correction is the lza family's `correction_scheme`; the count comes from the fp add family's lz / near_lz slot rather than a second anticipator inside the normalizer |
| lza | `operand_source` (raw_operands, carry_save_pair), `input_count`, `encode_direct_to_shift` | the carry-save pair and the four inputs are the fused units' anticipators; the direct shift encoding is a shifter-control encoding the library's binary count does not use |
| lza | `string_form = dual_pos_neg_strings` under `operand_order = swap_before_shift`, `split_string_select` under a single string | rejected and inert by construction: the dual strings serve the unswapped datapath, whose difference is taken both ways (allowlisted) |
| increment_adder, compound_adder_select, injection, flagged_prefix | `modes`, `position`, `unified_add_sub_cases`; compound_adder_select's `speculative_locations` | the modes are the engine's rounding modes, all realized; the position is after normalization in the rounder (the value-exact X contract); the add/subtract cases are the adder's; the speculative locations are a two-binade rounder before normalization |
| integer_compare_on_bits | `nan_semantics`, `signed_zero_ordering` | the op contract: the engine orders both zeros equal and leaves a NaN unordered |
| sig_mul_then_round | `sticky_method` | the exact product carries no dropped bits; the sticky is the operands' |
| round_fused_in_reduction | `sticky_method = carry_save_or, minus_one_group_propagate` | circuit-level forms inside the multiplier's reduction; the library's product is the sig_mul family's completed product |
| shift_round_convert | `rounding_modes`, `overflow_behavior`, `output_representation`, `reuse_add_datapath`; the `shift_unit` and `lz` slots | the modes and the overflow are the mode's contract; the output word is the target format's; sharing the adder's datapath is the unit's; the converter is the target's rounder, whose slots (lzc, shifter, round, exp_adder, exp_incrementer) it carries |
| internal_format_datapath | the family | a wide internal format with its own cores is a unit organization rather than a converter (the card is under legacy) |
| rounder (dedicated_per_op, shared_per_lane, shared_across_formats) | `lzc` (count_then_shift, leading_one_prediction), `input_select`, `width_select`, `rounding_increment` | the count is the new `lzc` slot's family; the input and width selects are the unit's sharing muxes; the increment is the `round` slot's family (compound_adder_select is the sum-plus-one) |
| unpacker (shared_per_lane, shared_across_formats) | `special_detect`, `width_select` | the specials are decoded once in the unpacker (the V carries the class); the width select is the unit's |
| the fp datapaths' shifters | `butterfly_network` at a non-power-of-two width | the network needs a power-of-two width; the fp16 engine's window is 27 bits, so the generator rejects it (allowlisted) |

The same batch realized what stayed: the fp add families' `operand_order`
(one shifter after the magnitude swap, or one per operand with the
difference taken both ways), `subnormal_representation` (the operands
normalized first through the lz slot's counter and the norm slot's
shifter), two_path's `path_threshold`, `close_path_trigger` and
`path_select_point` (operand isolation of the inactive path),
delay_optimized_unified's `path_separation` and `subtraction_style` (the
ones' complement end-around carry through the new `eac_incrementer`
slot), low_power_gated's `datapath_partitions` (one, two or three
isolated partitions), the align slot's `sticky_method` (the shifter's
sticky output, a thermometer mask, or the `tzc` slot's count), the
exponent path's `dual_direction_subtract` on the `exp.adder` slot, the
lza's `correction_scheme`, `string_form`, `split_string_select`,
`indicator_restriction` and `zero_result_detect` (the general
Schmookler-Nowka string and the positive-result string, checked exact
within one position by brute force over the adder's window), the
normalizer's `coarse_granularity`; the multiplier's `sig_mul` family
with its pins (twin_precision_subword included), the `exp_adder`,
`injection_adder`, `lzc` and `tzc` slots and `sticky_method`; the
comparators' `comparator` slot; the rounder's `lzc`, `shifter`,
`round` (all four rounding families, with their `incrementer`,
`injection_adder` and `compound_adder` slots), `exp_adder` and
`exp_incrementer` slots; the unpacker's `denormal_handling` on its `lzc`
and `shifter` slots; the divider's and square root's `sig_div` /
`sig_sqrt`, `norm_lzc`, `norm_shifter` and `exp_adder` slots. Every
mask over a variable position is a per-bit compare (a thermometer or a
one-hot decode) rather than a variable shift, every module name carries
a tag of its pins, and dot.py's forwarding keys `near_lz.*` and
`subnormal.internal_representation` for single_path are now `lz.*` and
`subnormal_representation` (the dot batch's change).

The approximate families (`approx_spaces.py` rev 8, `families/approx.py`):

| Family | Item removed or changed | Reason |
| --- | --- | --- |
| segmented_carry_speculative | `correction = extra_cycle` | a second cycle: sequential |
| lower_part_approximate | `window` declared (the speculation window under carry_to_upper window_speculation) | the generator read an undeclared pin |
| accuracy_configurable | `error_detection`, `power_gate_unused`, `recovery` | runtime error detection, power gating and extra-cycle recovery: not a single-cycle structure |
| accuracy_configurable | `reconfig_grain = subadder_select, carry_chain_switch, signal_substitution_switch` | they name the runtime switching mechanism of the same static structure (the correction stages); `operating_mode` (the static point) is declared and the sub-adders come from the new `sub_adder` slot |
| truncated_fixed_width (approximate space) | the family is the exact space's family itself | its correction ladder mapped onto `correction_scheme`, and `target`, `truncation_control`, `tree_mapping` selected nothing |
| dynamic_segment | `runtime_width_scaling` | a runtime width control |
| dynamic_segment | `core_multiplier` is a multiplier space (it was typed as the adder space); new slots `lod`, `shifter`, `adder` | the window product is a multiplier; the leading-one detectors, the window and product shifts and the position arithmetic rendered as hard-coded instances and operators |
| operand_rounding | new slots `lod`, `shifter`, `adder` | the same |
| logarithmic | `correction_table_bits` declared; slots `lod`, `normalize_shifter`, `log_adder`, `antilog_shifter` (the exact family's, passed through to its core) | the core's slots were hard-coded and `log_adder` was never read |
| pp_perforation | `accuracy_modes`, `configuration_time` | runtime accuracy modes |
| pp_perforation | `cell` realized (Kulkarni's 2x2 inaccurate blocks; the AWTM band with `multiplicand_rounding_bit` and `carry_prediction`); the `cpa` slot declared as the final-CPA space | the cells rendered one text and the final adder's pins were undeclared |
| approximate_compressor_tree | `compressor = akbari_dual_quality, ansari_encoded, strollo_extended` (the design-1 rule), `venkatachalam_pp_alter` (the OR rule) | each rendered the text of the rule it names; the three rules stay (momeni_d1_d2, yang_inexact, esposito_unbiased) |
| approximate_compressor_tree | `error_recovery = configurable_recovery`, `dual_quality_runtime` | runtime configuration |
| approximate_booth | `radix = hybrid_high_radix` | one radix per module; `encoder = rounded_high_radix_digit` is realized at radix 8 (3a rounded to 4a) |
| approximate_recurrence | `cell = inexact_signed_digit` | it rendered axsc2's rule; `radix` 4 and 8 are realized (the divisor's odd multiples through the new `multiple_adder` slot) |
| approximate_functional | `runtime_quality_scaling`, `operation = sqrt`, `exact_core` | runtime scaling; the square root is the sqrt slot's; the exact core of the window method is the small restoring divider (`lut` and `sequential` selected nothing) |
| approximate_functional | `iterations` declared; slots `seed_table`, `lod`, `shifter`, `multiplier` | the seed table, the leading-zero counters, the shifts and the products were hard-coded or operators |
| every family | the module name carries a 48-bit tag of the pins | two pin sets rendered two texts under one name |

The approximate functional divider's `seed_table` slot forwards its
family and pins to the division library's seed generator; the seed's own
choices (input and output bits, guard bits, function) render alike until
that generator reads them, which the divider batch decides.

The same batch fixed a latent defect the new vectors found: the
log_subtract_corrected divider took Mitchell's antilog line 2^x ~ 1 + x
on a negative fraction difference as well, where 2^x is 2^(x + 1) / 2 ~
1 + x / 2; a quotient of 130 / 26 rendered 3 for 5.

The decimal families (`decimal_spaces.py` rev 9, `families/decimal.py`):

| Family | Item removed or changed | Reason |
| --- | --- | --- |
| speculative_decimal_addition, redundant_decimal_addition, decimal_multioperand_addition | `complement_generation` declared | the generator read the choice of bcd_direct_addition alone |
| speculative_decimal_addition | `speculation_target = both` | the digit correction is speculated under every target; `both` rendered rounding_increment's text |
| decimal_multioperand_addition | the `reduction_tree` slot becomes the choice `column_sum` (two two-input adders, or a 3:2 compressor and one adder per digit, under binary_tree_then_convert) | the unit's contract gives three operands (a, b, the carry-in word), so an adder tree's families, compressor and CPA slots selected nothing; `compressor_arity` holds the decimal compressors' arity |
| parallel_decimal_multiplication | the reduction tree's `cpa` / `final_cpa` sub-slot drives the final adder when declared (the family's `final_adder` otherwise) | under the carry-save trees the tree's CPA was never read |
| decimal_digit_recurrence | `divisor_prescaling`, `radix_modes`, `selection_constant_module`, the `digit_select` slot | the redundant digit sets' rounding selection needs the prescaled divisor and the comparison selection needs none; a runtime radix-16 mode; the separate or combined constant module is the same logic; the digit selection is fixed by the digit set (comparisons against the multiples, or the rounding of the residual estimate) |
| decimal_digit_recurrence, decimal_newton | a `multiplier` slot (the decimal multiplier space) | the multiplications rendered as a procedural function with no slot to name a family; the slot's family renders the library multiplier, and an undeclared slot keeps the behavioral decimal product, since a partial-product tree per multiply dominates the divider (the binary functional dividers' rule, `families/div.py`) |
| decimal_newton | `operation` (divide, sqrt, both) | the BCD mode has no square-root op |
| decimal_newton | the `seed` slot holds the one ROM the generator builds, the `final_round` slot the two forms it builds (back-multiply remainder, exclusion zone), without the binary seed's and rounding's choices | the binary families' choices rendered one text here |
| every family | the module name carries a 48-bit tag of the pins | two pin sets rendered two texts under one name |

The subword and posit families (`shift_simd_spaces.py`,
`dsp_posit_spaces.py` rev 9, `families/subword.py`, `families/posit.py`):

| Family | Item removed or changed | Reason |
| --- | --- | --- |
| partitioned_carry_chain | `per_lane_flags` | the module already gives a carry-out per finest lane, and the lane's flags are the seed's (`alu_int.py` builds them from the lane's sum and carry-out) |
| partitioned_carry_chain | `operand_preshift`, `fused_average` | the averaging op and its pre-shift are ops the unit lacks |
| partitioned_carry_chain | the `saturation` slot, and with it the family saturating_clamp and `saturation_space` | the saturating ops' clamp depends on the mode's format, so the seed builds it (`alu_int.py`: add_sat, sub_sat, mul_sat); the card is under legacy |
| replicated_lanes | `register_file`, `rearrangement` | the register file is the unit's, and the pack/permute networks are ops the ALU lacks |
| posit_adder_multiplier | `es_bits` | the format's parameter: the generator builds the mode's es |
| posit_ieee_interop | `quire_present` | a quire is a register |
| posit_adder_multiplier, posit_ieee_interop | new slots `lzc` and `shifter`; `regime_decode` and `internal_representation` declared on the interop family too | the decoder's regime run and the encoder's normalizer instantiated `lzd_cell_tree` and `barrel_mux_tree` as constants, and the interop family's decoder reads the two choices the other family declared |
| every family | the module name carries a 48-bit tag of the pins | two pin sets rendered two texts under one name |

The posit unit's `approximation`, `operator_set`, `sig_datapath`,
`sig_div`, `interop_style` and `conversion_direction` stay and are
recorded in the coverage allowlist: the seed realizes them around the
decoder and the encoder (`alu_float.py` puts the PLAM multiplier, the
divider and the square root, and the boundary converters, in the lane).

The redundant, residue-number-system and checker families
(`redundant_spaces.py` rev 8, `checker_spaces.py` rev 8,
`families/redundant.py`, `families/mul_ext.py`, `alu_checker.py`,
`targets/rtl/residue.py`):

| Family | Item removed or changed | Reason |
| --- | --- | --- |
| generalized_signed_digit | `negation`, `overflow_detection`, `overflow_recovery`, `zero_sign_scan`, `otf_rounding_sign_source`; the `cpa` slot declared | the lane presents the complemented operand with a carry-in and reads its flags off the converted sum, so the negation and the flag scans are the seed's; the on-the-fly rounding's sign is a divider's; the exit conversion's adder was read without a slot |
| carry_save_datapath | `assimilation_point`, `accumulator_redundant` | the lane's op leaves a binary result, so the assimilation is per operation and a redundant accumulator across ops is a register |
| hybrid_signed_digit | the `cpa` slot declared | the same exit conversion |
| redundant_binary_multiplier | `rb_encoding` realized (the plus/minus pair, the sign-magnitude pair, the complemented pair; the rows and the carry-free cells carry the digits in the code and decode at each cell) | the three codes rendered one text |
| rns_channel_arithmetic | `multioperand_adder`, `moma_final_converter`, `fused_addend` | a multi-operand modular adder and a fused addend have no place in the lane's two-operand op |
| rns_forward_converter | `modulus_class`, `signed_input`, `final_reduction = pla` | the moduli follow modulus_form and the channel width; the operand encoding is the unit's (the comparator offsets the pattern); a PLA and a ROM are the same table, and the mapping is the synthesizer's |
| rns_scaling_comparison | `operation`, `method = redundant_modulus, macrocoefficient_k_k_minus_1` | the unit's op is the compare (scaling, base extension and the iterative ops are ops it lacks); the two methods need a redundant channel the generator does not build |
| every RNS family | a `modular_adder` slot on all four, the `column_reducer` slot read under periodic_csa_moma | every modular add, end-around carry, residue sum and constant-multiply term goes through the channel's adder family when the slot names one, and the folding's column sum through the reducer's tree; with no family declared they stay the operator, since a library adder at each of them (three channels, both conversions) takes the lane's multiplier from 29 s to past the harness's 600 s simulation budget, which the allowlist records (the multiplier's behavioral_star rule) |
| two_rail_tree | `input_code`, `embedded`, `fail_safe_lockout`, `safe_value`, `realization` | the checker's tree is the morphic-cell tree of its arity; the lockout and the safe value are a state element and a system convention |
| m_out_of_n_checker | `partitioning`, `intermediate_code`, `deep_case_delay_style`, `gate_polarity`; `code_class` and `realization` narrowed to what the generator builds | the checker realizes the k-out-of-2k threshold pair, the translator cascade and the cellular array; the rest are circuit-level styles of the same function |
| majority_voter | `disagreement_indication`; the family is duplication's comparator alone | the voter's disagreement output is not the seam's check_err, and a vote needs replicas |
| residue | `granularity`, `comparison_point`, `ops_per_checker`; `generator_style` realized (a carry-save tree, a chain of end-around-carry adders, or a table over the chunk pairs) | where the check sits and how many ops share it are placements of the seam; the generator's structure is real |
| inverse_residue | `inverse_on` realized (the complement on the check channel, or on both) | it rendered one text |
| multi_residue | `code_distance`; `moduli_set` realized (the low-cost 2^a - 1 set or a general coprime set) | a correcting distance needs a corrected output the seam lacks |
| an_code | `code_distance`, `decode_point`; a `coded_adder` slot | the correction and the decode point need an output and a place the seam lacks; the coded operands' sum and difference were the checker's own adds |
| rns_redundant | `correction` | the syndrome names a channel, and the interface carries no corrected result |
| berger | `check_field`, `burst_type`, `granularity`; `construction` narrowed to berger and bose_lin_method2 and realized (the full count, or its low bits) | the burst classes and the field's use are the code's application; the placement is the seam's |
| parity_prediction_adder | `parity_groups`, `interleaving` and `carry_scheme` realized (the groups contiguous or interleaved; the carries from the replica adder of the `carry_replica` slot or from the checked sum itself) | all three rendered one text and the slot was never read |
| parity_prediction_multiplier | `check_depth`, `fault_secure_structuring`; a `row_adder` slot | the datapath's stage carries and its tree are not visible at the seam; the replica's row chain was the checker's own adds |
| reduced_precision | `correct_by_substitution`; a `replica_adder` slot | a substituted result needs an output the seam lacks; the narrow replica's own difference was an add |
| duplication | `comparison_point`, `temporal_stagger`, `organization`, `storage_correction`, `voter_replication`, `voter_placement`, `module_granularity`, `recovery_policy`, `standby_spares`, `post_fault_mode` | every one of them is a system-level or sequential property (a checkpoint, a spare, a recovery policy), not a structure of the single-cycle seam |

The checker probes now render an integer mode and a float mode with the
float ops, since a family's float replica, residue and parity paths live
in the second; the `reduced_precision` float replica keeps the engine's
own reference functions, which the allowlist records.

The divider families (`div_spaces.py`, `families/div.py`; every divider
here is an unrolled array, so a "cycle" of an iterative algorithm is one
stage of the array):

| Family | Item removed | Reason |
| --- | --- | --- |
| restoring_nonrestoring | `bits_per_cycle`, `shift_over_zeros`, `shift_policy`, `shifter_limit` | the sequential machine's iteration count; the array retires one bit per stage and skips nothing |
| restoring_nonrestoring | `divisor_multiple_set`, `multiple_selection` | the multiple set of the shifting-over-zeros machine (the variant card three_quarters_one_three_halves is under legacy) |
| srt_radix2 | `implementation_topology` (reused_clocked_stage, combinatorial_array) | the array is the single-cycle unit's only form (the variant card combinatorial_array is under legacy) |
| srt_radix2 | `quotient_prediction` | predicting the next digit while the clocked stage's residual settles: a cycle-time property; the array's later stages read the earlier digits directly |
| srt_radix2 | `residual_estimate_bits` | the estimate's width is the digit_select slot's (`residual_truncation_bits` of the table, `comparison_bits` of the comparators) |
| srt_radix2, srt_high_radix | `residual_form = signed_digit` | a signed-digit residual needs signed-digit adders and a redundant-to-binary converter: the redundant representation's core (`redundant_spaces.py`) rather than a form of the binary recurrence (the variant cards signed_digit are under legacy) |
| srt_radix2, srt_high_radix | `quotient_conversion = serial_msd_borrow_scan` | a digit-at-a-time conversion: sequential (the variant card is under legacy) |
| srt_high_radix | `digit_redundancy = intermediate` | radix 8 and above are cascades of radix-4 sub-stages, whose digit sets are minimal (-2..2) or maximal (-3..3); an intermediate set needs a monolithic radix-8 stage (the variant card is under legacy) |
| qds_table | `residual_input` (redundant_direct, short_cpa, full_cpa) | the table reads an estimate assimilated by a short adder, whose width is `assimilator_bits` now; the redundant-direct input is the comparator family's `residual_input`, the full assimilation the recurrence's `residual_form` |
| qds_table | `exhaustive_pd_region_check`, `formal_recurrence_invariant`, `table_generation` | validation methods of the generation flow; the generator checks every cell for containment at generation regardless |
| qds_table | `folding = t_bit_converter` | a circuit-level form of the estimate's assimilation; the signed-magnitude fold is realized |
| comparator_digit_selection | `comparator_count` | fixed by the digit set (2a comparators per divisor row) |
| comparator_digit_selection | `constant_source` (hardwired, registers_at_init, rom) | constants loaded into registers at initialization are sequential; hardwired constants and a constant ROM synthesize alike |
| comparator_digit_selection | `estimate_cut` (binary_bit, decimal_digit) | the decimal cut is the decimal divider's |
| comparator_digit_selection | `comparison_bits` below 6 | the estimate carries four integer bits and at least two fraction bits |
| the seed families | `function` (reciprocal, recip_sqrt, both) | the consumer fixes the function (the divider asks for the reciprocal, the square root for the reciprocal square root); the variant cards recip_sqrt and reciprocal of operand_modification_multiply are under legacy |
| operand_modification_multiply | `multiplier_array` (plain_53_row, booth_27_row) | the multiplier's structure is the `mul` slot's family |
| operand_modification_multiply | a `sum_adder` slot | the seed synthesized inside the multiplier array (`seed_synthesis = boolean_partial_product_rows`) has no adder of its own: its rows are summed by the consumer's adder (`iter_add`, or the prescaled recurrences' `residual_adder`); the modified-operand product needs none |
| magic_constant_bit_seed | `floating_format`, `subnormal_handling`, `magic_constant_selection = floating_point_experimental` | the format is the consumer's and the seed acts on the normalized fixed-point operand; the experimental constant is a measured value of a software library rather than a structure |
| magic_constant_bit_seed | `input_bits` | no table: the seed is one subtraction on the operand's top bits, sized by `output_bits` and `guard_bits` |
| the prescaled recurrences' `seed` slot | the member magic_constant_bit_seed | the prescaling must land the divisor inside 2^-(`bits_per_iteration` + 2) of one, which the table-free linear seed's 0.17 relative error cannot reach at any width; those two families take `prescale_seed_space()`, the table seeds alone |
| poly_seed | `exponent_parity_tables` | the exponent's parity is folded into the square root's even normalization before the seed |
| multipartite | `tables = 2` | two tables is bipartite_rom |
| back_multiply_remainder | `remainder_test` (full_residual, product_digit_compare_low_digit_zero) | the digit-compare test is the decimal divider's |
| back_multiply_remainder | `residual_operation` (quotient_times_divisor, candidate_square) | the consumer fixes the operation (the divider back-multiplies q b, the square root squares the candidate); the variant card candidate_square is under legacy |
| newton_raphson | `dedicated_multiplier` | sharing the unit's multiplier is a unit-level sharing family; the `iter_mult` slot is the divider's own multiplier |
| prescaled_very_high_radix | `shared_scaling_multiplier` | the same; the `prescaler` slot |
| direct_polynomial | `target` (reciprocal, ratio, square_root) | the consumer fixes the function |
| direct_polynomial | the `approximator` slot over `sfu_space` | the elementary-function families are the SFU generator's; the feed-forward divider's approximator is the table-indexed polynomial (`poly_seed_space`) |
| direct_polynomial | the `iter_add` slot | the one refinement step sums through the polynomial's own `sum_adder` |
| digit_recurrence_sqrt_combined | `shared_with_division` | an instance is a divider or a square root; sharing one datapath between the two ops is a unit-level multiplexing of the operand paths |
| online_msdf | `online_delay = 2` | the on-line terms exceed the digit set's redundancy at every radix (radix 2 needs 4, which the generator enforces) |

The same batch realized what stayed: the normalization's counter and
shifter as the slots `norm_lzc` and `norm_shifter` of every family that
normalizes (the dividend scaled and the remainder de-scaled through the
same shifter); the recurrences' `residual_adder` (the trial and
restoring subtractions, the assimilations, the divisor's non-shift
multiples, the speculated candidate residuals, the final corrections,
the square root's subtrahends, the de-scaled root's square by adder
rows); the table as a case ROM in a module of its own with
`divisor_truncation_bits`, `residual_truncation_bits`,
`assimilator_bits`, the four digit encodings and the signed-magnitude
fold; the comparators' `comparison_bits`, `residual_input` (the two-word
input through a 3:2 row per comparator), `symmetry_folding`, the four
output encodings, `speculative_candidate_residuals` and the
`comparator_adder` slot; srt_radix2's `residual_form` and
`quotient_conversion`; srt_high_radix's `radix` (8, 16 and 32 as
cascades of radix-4 and radix-2 sub-stages), `digit_redundancy` (the
maximal set's 3d through the residual adder), `overlapped_stages` (the
later selections speculated per candidate digit of the earlier ones),
`residual_form` and `quotient_conversion`; the shared recurrence's
`radix` (16 and 64 as radix-4 sub-stages), `on_the_fly_conversion`
(Q+ - Q- with the partial root assimilated per stage) and
`speculation_between_subiterations`, and its square root as the SRT
recurrence in the halved residual form with a selection table
generated and checked per stage index; the on-line divider's `radix` 4
and its `digit_select` slot (the table built with the residual bound
tightened for the on-line terms); newton_raphson's `iterations`,
`iteration_order` and `internal_guard_bits` with the `iter_add` slot;
goldschmidt's `iterations`, `internal_guard_bits` and
`truncated_intermediate_multiplies`; direct_polynomial's `composition`;
the prescaled families' `bits_per_iteration`,
`prescaling_precision_bits`, `msd_recoding` and svoboda_tung's own
`seed` slot; the seeds' `input_bits`, `output_bits` and `guard_bits`,
the sums through `sum_adder`, `seed_synthesis` (the Boolean
partial-product rows), poly_seed's `degree`, `slope_encoding` and
`tail_bits` with its `mul` slot, the magic constant's
`magic_constant_selection`; the final rounding's `quotient_candidates`,
`product_bits` and `correction_adder`, exclusion_zone_proof (the
rounding add at half a quotient step) and extra_precision_quotient
(two more precision bits, the error bound added and the estimate
truncated) as distinct netlists. Every module name carries a tag of its pins, and the
multiplier slots' default `behavioral_star` is the library's module of
that family.

## Choices removed under the coverage check (2026-09-13)

The coverage check's choice rule is the one above: a choice value stays
only when it selects a structure the generator realizes and the module's
text changes with it.

| Family | Item removed | Reason |
| --- | --- | --- |
| twin_precision_subword | `partition` (halves, quarters, mixed_half_quarter) | the lane split is the unit's mode set, which the generator receives as the lane widths; the pin said the same thing a second time and reached the header comment alone |
| twin_precision_subword | `base_scheme` (baugh_wooley, modified_booth) | the matrix is Baugh-Wooley; a Booth-recoded twin-precision matrix, whose recoding gates at the lane boundaries, is not realized in this version |

`fam_mul_twin_precision_*` now carries a 48-bit tag of the pins its name
does not spell out, so two pin sets never share a name.

## Exceptions that are not deferrals

Two groups are exceptions of the mode rather than of a cycle:
`block_fp_accumulation` and `mx_microscaling_dot` on a scalar mode (the
shared exponent is the block format's), and the FMA lineage
(`classic_fma`, `reduced_latency_fma`, `multipath_fma`, `bridge_fma`,
`mixed_precision_cascade_fma`) on a mode of several elements under the
fused contract (an FMA sums one product and the addend). They stay in
the spaces; the mode set decides them.

Contract notes that are not exceptions: the approximate ALU's runtime
quality controls (dual-quality cells, runtime width scaling) are realized
at a static operating point named in the module comment (a run that asks
for runtime configurability gets a port, `docs/work-plan.md` item 7);
the posit PLAM fraction and the SFU polynomial families' default segment
and degree pins meet an approximate contract; the dot cascade styles of a
one-element mode meet the sequential contract; `per_level_truncation`
and the mixed-precision cascade round partial results.

## What the later version needs

* **Sequential structures (the 10 families of the first table, the nine
  choice values, the on-line group and the two core families)**: a
  multi-cycle unit contract, which is a latency or valid protocol
  variable on the templates, registers in the seed, the testbench's
  fixed-latency and iterative protocols (they exist in
  `chialu/verify/tb_gen.py`), and a timing metric of cycle time times
  cycles or of throughput. `docs/future-work.md` section 1 states the
  work.
* **State and interface (2)**: an accumulate op with a quire register for
  the posit unit; a lane-mask port for the vector unit.
* **Kernels and the checker seam (5)**: a system-level space above the
  unit templates, or a core-level checker contract; not unit structures.
* **Methods (4)**: tactics or evaluation methodology rather than family
  entries; they never return as structures.
* **The DSP block group (6)**: a unit template for the slice's own
  organization, which the ASIC scope ruling of the dsp space's header
  left outside the targets.
* **The decimal floating-point group (9)**: a unit template with decimal
  floating-point modes (formats, the cohort and preferred-exponent rules
  of IEEE 754-2019 clause 5, the DPD and BID encodings) in the verify
  layer and the seed. `docs/future-work.md` section 2 states the work.
