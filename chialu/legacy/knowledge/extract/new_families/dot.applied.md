# dot plan: applied

Plan: `chialu/knowledge/extract/new_families/dot.md`, plus the five
`multi_term_fused_dot` lines under `## deferred (other file)` in
`new_families/fp.applied.md`. File edited: `chialu/spaces/fma_dot_spaces.py`
only (rev 7 to rev 8). Handles were applied under their re-keyed names:
`muller_2018#s08` enters `papers=` as `muller_2018`, `beaumont_smith_1999` is
`beaumont_smith1999`, and the ShiftCNN lines cite `gudovskiy_2017` rather than
`lee_1989`.

## applied

18 changes on 6 families: 13 new choices and 5 new values on existing choices.
Six handles were added to `papers=` tuples; every handle exists in `PAPER_DB`.

`multi_term_fused_dot` (`papers=` gains `muller_2018`; `tenca_2009`, `tao_2013`,
`sohn_2014` were already cited):
* `+= choice term_source: {products, fp_operands}` [tenca_2009, tao_2013, sohn_2014, muller_2018]. The dot line and the fp deferred line are one change.
* `alignment_strategy += max_exponent_tree, pairwise_difference_reuse` [tenca_2009, sohn_2014]. The dot plan's `parallel_pairwise_difference` is the same value; the fp.md name `pairwise_difference_reuse` is kept, as the plan's header states.
* `alignment_strategy += exponent_sorted_realignment_lines` [tao_2013].
* `+= choice cancellation_handling: {none, detect_and_bypass_smallest_operand}` [tenca_2009, tao_2013].
* `+= choice sign_handling: {post_add_complement, dual_reduction_positive_pair_select}` [sohn_2014].
* `+= choice normalize_before_add: Bool` [sohn_2014].
* `+= choice pipeline_depth: Int[1..3:1]` [sohn_2014].
* The family `doc=` now names the operand-fed members (FPADD3/FADDn, the fused three-term adder).

`streaming_accurate_accumulator` (`papers=` gains `lutz_2019`):
* `approach += ordered_fp_loop_lookahead` [lutz_2019].

`mixed_precision_cascade_fma` (`papers=` gains `muller_2018`):
* `+= choice error_term_normalization: {dedicated, on_demand_copy}` [muller_2018].
* `+= choice error_term_ops: {addition, multiplication, both}` [muller_2018].

`integer_mac` (`papers=` gains `camus2019`, `tremblay_1996`):
* `+= choice accumulation_mode: {sum_apart, sum_together}` [camus2019].
* `+= choice scalable_dimensions: {one, two}` [camus2019].
* `+= choice scalability_levels: Int[1..2:1]` [camus2019].
* `array_style += composable_submultiplier` [camus2019]. The plan's rename of `bit_serial_composable` was applied as a pure addition; the old value stays because `integer_mac.md` and the mutation `bit_serial_compose` name it.
* `+= choice element_op: {product, absolute_difference}` [tremblay_1996].
* The family `doc=` now names the divide-and-conquer composition, the two accumulation modes and pdist.

`fp8_training_datapath` (`agrawal_2021` was already cited):
* `+= choice op_shape: {scalar_fma, dot2_accumulate}` [agrawal_2021].
* `+= choice unified_internal_format: Bool` [agrawal_2021].

`bridge_fma` (`papers=` gains `lindholm_2008`):
* `+= choice cascade_product_rounding: {rne, truncate}` [lindholm_2008].

Variant docs written (13), each with front matter `family:` + `pin:`, a first
paragraph under 500 characters, 122 to 138 words after it, and verbatim
citations from the dot bundle (`tenca_2009` and `tao_2013` from the fp bundle,
which carries the evidence for the deferred lines):
* `chialu/knowledge/arch/dot/multi_term_fused_dot/fp_operands.md` (4 refs)
* `chialu/knowledge/arch/dot/multi_term_fused_dot/pairwise_difference_reuse.md` (2 refs)
* `chialu/knowledge/arch/dot/multi_term_fused_dot/max_exponent_tree.md` (1 ref)
* `chialu/knowledge/arch/dot/multi_term_fused_dot/exponent_sorted_realignment_lines.md` (1 ref)
* `chialu/knowledge/arch/dot/multi_term_fused_dot/dual_reduction_positive_pair_select.md` (1 ref)
* `chialu/knowledge/arch/dot/multi_term_fused_dot/detect_and_bypass_smallest_operand.md` (2 refs)
* `chialu/knowledge/arch/dot/streaming_accurate_accumulator/ordered_fp_loop_lookahead.md` (1 ref)
* `chialu/knowledge/arch/dot/integer_mac/absolute_difference.md` (1 ref)
* `chialu/knowledge/arch/dot/integer_mac/composable_submultiplier.md` (1 ref)
* `chialu/knowledge/arch/dot/integer_mac/sum_apart.md` (1 ref)
* `chialu/knowledge/arch/dot/integer_mac/sum_together.md` (1 ref)
* `chialu/knowledge/arch/dot/mixed_precision_cascade_fma/on_demand_copy.md` (1 ref)
* `chialu/knowledge/arch/dot/fp8_training_datapath/dot2_accumulate.md` (1 ref)

`fp8_training_datapath/dot2_accumulate` shares its bare name with
`bf16_fma_datapath/dot2_accumulate`, so `variant_table()` resolves only the
qualified names for the two; no yaml or preset in the repo uses the bare name.

## skipped

* `multi_term_fused_dot += choice term_count: Int[3..8:1]` (fp deferred line) — N is the module parameter `elements` of `chialu.VecDotAcc` in `chialu/modules/dot.py`, beside `elem_bits`; the line's own condition skips it.
* `multi_term_fused_dot.alignment_strategy += parallel_pairwise_difference` as a name — merged into `pairwise_difference_reuse` (above).
* `streaming_accurate_accumulator.approach += unnormalised_feedback_with_lza_distance` [beaumont_smith1999] — the plan states that one of this line and `fp_add_space.dependent_result_forwarding: rounded_unnormalized_feedback` is applied and the other absorbed; the fp applier applied the fp line, so this one is absorbed into it. `beaumont_smith1999` is not added to the family's `papers=`.
* `leading_zero_anticipation=direct_three_input` and `rounding_structure=compound_sum_sum1` (sohn_2014) — no choice here; the first is `lza.input_count=3`, which the fp applier applied, and the second is the `round` slot's `compound_adder_select`.
* `mixed_precision_cascade_fma.residual_width: Int[1..p:1]` — binds to `elem_bits` (plan).
* `integer_mac.submultiplier_shape` — follows from `scalable_dimensions` (plan).
* Rename of `integer_mac.array_style=bit_serial_composable` — not renamed; `composable_submultiplier` was added alongside.
* `fp8_training_datapath += choice weight_update_error_feedback: Bool` [sun_2019] — scope ruling: optimizer-side mechanism.
* `tensor_core_mixed_precision_mac += choice multi_word_composition: Bool` [markidis_2018] — a conditional mirror line in the plan's absorbed section rather than a `new values` line; left to the human.
* Promotion candidates `multi_operand_fp_add` and `ordered_fp_loop_accumulator` — promotion left to the human; the plan proposes no family.
* No variant doc for `bridge_fma.cascade_product_rounding=truncate` (a rounding setting on the existing `cascade_mul_then_add` structure), for `error_term_normalization=dedicated`, `sign_handling=post_add_complement`, `term_source=products`, `element_op=product`, `op_shape=scalar_fma`, `scalable_dimensions`, `cancellation_handling=none` (baselines or parameter settings), or for the Bool and Int choices.
* Absorbed (3) and rejected (2) entries of the plan: nothing to do in this file.

## deferred (other file)

* `approximate_mac_nn.multiplier_source += power_of_two_codebook` [gudovskiy_2017, re-keyed from lee_1989] — `chialu/spaces/approx_spaces.py`.
* `approximate_mac_nn += choice codebook_terms_per_weight: Int[1..8:1]` [gudovskiy_2017] — `approx_spaces.py`.
* `approximate_mac_nn += choice codebook_index_bits: Int[3..4:1]` [gudovskiy_2017] — `approx_spaces.py`.
* `rns_channel_arithmetic += choice fused_addend: {none, injected_before_final_adder_dual_output}` [zimmermann1999] — `chialu/spaces/redundant_spaces.py`.
* `hard_fp_dsp += choice chain_topology: {linear_accumulate, recursive_tree}` [langhammer_2015b] — `chialu/spaces/dsp_posit_spaces.py`. The plan places the dedicated chain on the block-architecture side, beside `dsp48_style_slice.cascade_paths`, so the FPGA-mapping ruling does not exclude it; the dsp applier decides.
* `hard_fp_dsp += choice chain_routing: {dedicated_chain, balanced_soft_routing}` [langhammer_2015b] — `dsp_posit_spaces.py`, same ruling.
* `online_pipeline_composition += choice topology: {chain, nearest_neighbor_mesh}` [irwin_owens_1987] — `redundant_spaces.py`; an optional refinement in the plan's absorbed section.

## checks

* `python3 -c "from chialu.papers import _all_spaces; s=_all_spaces(); print(len(s))"` prints 36.
* `python3 -m chialu.archdocs`: `[archdocs] 206 docs for 231 families; 25 undocumented; 419 variant docs`, exit 0, no ORPHAN / BAD REF / BAD VARIANT lines. `--strict` lists no family of this plan among the 25 undocumented slot families.
* `python3 -m chialu.extract vocab > /dev/null` exits 0.
* `kb_section_exp2()` renders.
* Every handle in every `papers=` tuple of `dot_acc_space(8)` exists in `PAPER_DB`.

applied 18 changes (13 choices, 5 values) on 6 families + 13 variant docs, skipped 11 items, deferred 7 lines
