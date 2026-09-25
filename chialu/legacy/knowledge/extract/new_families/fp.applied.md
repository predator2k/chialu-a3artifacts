# fp plan: applied

Plan: `chialu/knowledge/extract/new_families/fp.md`. File edited:
`chialu/spaces/fp_spaces.py` only. Docs written:
`chialu/knowledge/arch/fp/sig_sqrt_then_round.md`,
`chialu/knowledge/arch/fp/internal_format_datapath.md`,
`chialu/knowledge/extract/gaps/sig_sqrt_then_round.md` (none),
`chialu/knowledge/extract/gaps/internal_format_datapath.md` (none).
No variant docs: `sig_sqrt_then_round` declares no design choices, and the
`internal_format_datapath` values the blocks pin (`internal_radix=hexadecimal`,
`architected_formats=hfp_and_bfp`) are parameter settings rather than named
structures.

## applied

New values (10 lines, 12 choices/values):

* `shift_round_convert += choice output_representation: {integer_word, integral_in_fp_format}` [rathor_2024]. `rathor_2024` was already in `papers=`.
* `lza.correction_scheme += true_count_lsb_compare` [dimitrakopoulos_2008]. Already in `papers=`.
* `lza += choice split_string_select: {true_sign, maximum_count}` [dimitrakopoulos_2008].
* `lza += choice input_count: Int[2..4:1]` [sohn_2014, sohn_2016]. `papers=` extended with `sohn_2014`, `sohn_2016`. Shared with the dot plan; applied here once, so the dot applier must not repeat it.
* `lza += choice indicator_restriction: {general, positive_result_only, exponent_difference_one}` [schmookler_2001]. Already in `papers=`.
* `lza += choice zero_result_detect: {indicator_or, operand_function_or}` [schmookler_2001].
* `sig_mul_then_round += choice sticky_method: {post_cpa_or_tree, input_trailing_zero_count, carry_save_or, minus_one_group_propagate}` [santoro_1989, bewick1994]. `sig_mul_then_round` had no `papers=`; it now cites `santoro_1989`, `bewick1994`. The line states the same choice belongs on `round_fused_in_reduction`, so that family carries the choice as well, with `bewick1994` added to its `papers=`. The choice is a shared helper `_sticky_method_choice()`.
* `fp_add_space (every family) += choice dependent_result_forwarding: {none, redundant_packet_two_cycle, rounded_unnormalized_feedback}` [nielsen_2000, beaumont_smith1999]. Added to all five families (`single_path`, `two_path`, `delay_optimized_unified`, `variable_latency`, `low_power_gated`) through a `_fp_add_common_choices()` helper; `nielsen_2000` and `beaumont_smith1999` were added to every family's `papers=` where missing. Shared with the dot plan; applied here once, so the dot applier must not repeat it.
* `rounding_space.position += before_fine_normalize_multi_location` [wahba_2017]. `position` is in the space's `common` dict, so all four rounding families gain the value; `wahba_2017` was added to `compound_adder_select`'s `papers=` (the family whose block evidences the duplicated conversions).
* `rounding_space.compound_adder_select += choice speculative_locations: Int[1..3:1]` [wahba_2017].

New families (2):

* `sig_sqrt_then_round` in `fp_div_space`, `papers=("muller_2018",)`, slots `sig_sqrt: div_space`, `round`, `exp`, `subnormal`, mutations `fuse_div_sqrt`, `drop_exponent_range_check`. Qualifies on the textbook block (muller_2018#s07). Doc: 1 reference (the bundle has only the textbook citation for this family).
* `internal_format_datapath` in `fp_cvt_space`, `papers=("schwarz_1999", "slegel_1999")`, choices `internal_radix`, `internal_fraction_bits: Int[53..64:1]`, `internal_exponent_bits: Int[11..16:1]`, `architected_formats`, slots `core_add: fp_add_space`, `core_mul: fp_mul_space`, `core_div: fp_div_space`, `round: rounding_space`, the three mutations from the plan. Qualifies as one design described by two papers. Placement: the plan named the FPU-level sub-space (ruled out) or "a wrapper beside the `sig_*_then_round` families"; a family whose slots are `fp_add_space`/`fp_mul_space`/`fp_div_space` cannot live inside any of those three spaces without recursing at construction, and `_all_spaces()` in `chialu/papers.py` (not editable here) enumerates only the five existing fp spaces, so the family sits in `fp_cvt_space` (domain "format converters"), whose defining structure it shares. `fp_cvt_space` gained a `mant_bits: int = 11` default parameter for the `core_mul` slot; every existing caller passes no argument. Doc: 2 references (all the bundle has for it). A human may re-home the family if an FPU-level space is created later.

## skipped

* `exponent_path += choice early_exception_safety_check: Bool` [alpert_1993] — scope ruling: pipeline-control-flavoured line, skipped.
* `partitioned_fpu` (merged from instruction_oriented_concurrent_fpu, shared_partitioned_arithmetic_pipeline, queued_binary_fp_coprocessor, multisection_pipelined_fpu, parallel_fp_pipeline_cluster, format_separated_clock_gated_fp_datapath, configurable_transprecision_fpu, multi_precision_simd_fp_pipeline) — scope ruling: FPU-level organization stays out of the registry. The plan's fallback applies: `multi_precision_simd_fp_pipeline` is absorbed into `multi_precision_simd_fma.lane_split=2x32` and `format_separated_clock_gated_fp_datapath` into `bridge_fma.composition_style=cascade_mul_then_add` (both values already exist in `fma_dot_spaces.py`; nothing to do); the other six proposals are rejected.
* No family was deferred for single-incremental-paper support: `sig_sqrt_then_round` has a textbook block and `internal_format_datapath` has two papers.
* Absorbed (4) and rejected (2) entries of the plan: nothing to do.

## deferred (other file)

All five target `multi_term_fused_dot`, which lives in `chialu/spaces/fma_dot_spaces.py`:

* `multi_term_fused_dot.alignment_strategy += max_exponent_tree, pairwise_difference_reuse — FPADDn finds the maximum exponent through a tree and subtracts, or reuses pairwise exponent differences (smaller and faster under tight timing) [tenca_2009]  (from multi_operand_fp_addition)`
* `multi_term_fused_dot.alignment_strategy += exponent_sorted_realignment_lines — FADDn sorts operands by exponent through a pairwise-weight crossbar, assigns fixed intrinsic lines and opens a realignment line only when the exponent separation exceeds a bound [tao_2013]  (from correctly_rounded_multioperand_addition)`
* `multi_term_fused_dot += choice cancellation_handling: {none, detect_and_bypass_smallest_operand} — catastrophic cancellation of the larger operands is detected and the smallest operand (with its sticky) is forwarded as the result instead of the internal sum [tenca_2009, tao_2013]`
* `multi_term_fused_dot += choice term_source: {products, fp_operands} — the multiplier slot becomes optional so a pure N-operand FP adder (FPADD3/FADD4/FADD8) is a member; the alternative is a separate `multi_operand_add` family in `fp_add_space`, and by the prefer-new-values rule the choice is proposed [tenca_2009, tao_2013]`
* `multi_term_fused_dot += choice term_count: Int[3..8:1] — implemented 3 (FPADD3), 4 and 8 (FADD4/FADD8); skip if N is already a module parameter beside `elem_bits` [tenca_2009, tao_2013]`

The dot plan proposes `term_source` and the pairwise alignment value on the same family; the dot applier owns both in `fma_dot_spaces.py`.

## checks

* `python3 -c "from chialu.papers import _all_spaces; s=_all_spaces(); print(len(s))"` prints 36.
* `python3 -m chialu.archdocs`: `[archdocs] 195 docs for 220 families; 25 undocumented; 400 variant docs`, no ORPHAN / BAD REF / BAD VARIANT lines. The 25 undocumented families (`lza`, `coarse_fine`, `exponent_path`, `compound_adder_select`, `csa_tree`, `qds_table`, ...) are pre-existing slot families that a concurrent change to `archdocs._all_families()` (it now walks component slots) surfaced; none of them comes from this plan.
* `python3 -m chialu.extract vocab > /dev/null` passes.
* `kb_section_exp2()` renders.
* Every handle in every `papers=` tuple reachable from the five fp spaces exists in `PAPER_DB`.

applied 10 value lines (12 values/choices) + 2 families, skipped 2 (1 value line, 1 family with 8 merged proposals), deferred 5 lines
