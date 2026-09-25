# new-family review: fp

Source bundle: `run/extract/reduce/newfam_fp.md` (30 proposals). Registry read:
`chialu/spaces/fp_spaces.py` plus the family lists of `fma_dot_spaces.py`,
`div_spaces.py`, `adder_spaces.py`, `shift_simd_spaces.py`, `dsp_posit_spaces.py`,
`approx_spaces.py`, `decimal_spaces.py`, `sfu_spaces.py`. Notes consulted:
`notes/muller_2018__s07.md` (the sqrt block).

Handle notes for the human:
* `beaumont_smith1999` (bundle) is the same ARITH-14 paper that `fp_spaces.py` and
  `adder_spaces.py` cite as `beaumont_smith1999`. The bundle spelling is kept below.
* `anderson1967` (bundle) is the Model 91 paper that `div_spaces.py` cites as
  `anderson1967`. The bundle spelling is kept below.
* `alpert_1993`, `christie_1996`, `darley_1990`, `saporito_2020`, `sato_2020` and
  `schwarz_1999` are cited by no space file today; `slegel_1999` and `watson_1972` are
  cited only by `checker_spaces.py`.
* Chapter handles (`muller_2018#s07`, `muller_2018#s08`, `bewick1994#s09`) are kept as
  given in prose; the `papers=` tuples in the snippets use the base key, which is the
  style of `fp_spaces.py` (`muller_2018`) and `mul_spaces.py` (`bewick1994`).

## absorbed

* approximate_fp_log_divider -> approx_div_space.approximate_functional.method=log_subtract_corrected (bias_correction=True) — FaNZeD is the INZeD log-subtract divider that `approximate_functional` already cites under `saadat2019`, placed in `sig_div_then_round`'s `sig_div` slot with the `round` slot removed; the 0..20-bit mantissa truncation knob has no choice yet and would be a `new value` on `approximate_functional` if wanted [saadat2019].
* combined_sum_difference -> fused_two_term_dot.second_op=add_subtract_pair — the textbook statement of the fused add-subtract unit: one shared close path yields a+b and a-b [muller_2018#s08].
* fused_fp_add_subtract -> fused_two_term_dot.second_op=add_subtract_pair (dual_path_add=True for the far/close version) — `sohn_2012` is already a family paper; the proposal's `path_structure` maps to `dual_path_add` and its `shared_front_end` is the family mechanism. A multiplier-less variant in `fp_add_space` is the same decision as the `term_source` choice under new values [sohn_2012].
* leading_one_prediction_concurrent_correction -> lza.correction_scheme=concurrent_correction, lza.string_form=dual_pos_neg_strings — `bruguera_1999` is already a family paper; the positive/negative detection trees are the dual strings and the fine-stage increment is the concurrent correction [bruguera_1999].

## new values

* multi_term_fused_dot.alignment_strategy += max_exponent_tree, pairwise_difference_reuse — FPADDn finds the maximum exponent through a tree and subtracts, or reuses pairwise exponent differences (smaller and faster under tight timing) [tenca_2009]  (from multi_operand_fp_addition)
* multi_term_fused_dot.alignment_strategy += exponent_sorted_realignment_lines — FADDn sorts operands by exponent through a pairwise-weight crossbar, assigns fixed intrinsic lines and opens a realignment line only when the exponent separation exceeds a bound [tao_2013]  (from correctly_rounded_multioperand_addition)
* multi_term_fused_dot += choice cancellation_handling: {none, detect_and_bypass_smallest_operand} — catastrophic cancellation of the larger operands is detected and the smallest operand (with its sticky) is forwarded as the result instead of the internal sum [tenca_2009, tao_2013]
* multi_term_fused_dot += choice term_source: {products, fp_operands} — the multiplier slot becomes optional so a pure N-operand FP adder (FPADD3/FADD4/FADD8) is a member; the alternative is a separate `multi_operand_add` family in `fp_add_space`, and by the prefer-new-values rule the choice is proposed [tenca_2009, tao_2013]
* multi_term_fused_dot += choice term_count: Int[3..8:1] — implemented 3 (FPADD3), 4 and 8 (FADD4/FADD8); skip if N is already a module parameter beside `elem_bits` [tenca_2009, tao_2013]
* shift_round_convert += choice output_representation: {integer_word, integral_in_fp_format} — roundToIntegral: the exponent locates the mantissa bit of rounding, retained bits are truncated or incremented per mode and the result stays in FP format; the integrated multimode (IMR) form is the existing `add_multi_mode_rounding` mutation with `rounding_modes=five_modes` [rathor_2024]  (from fp_round_to_integral)
* exponent_path += choice early_exception_safety_check: Bool — each operation is classified exception-safe from operand specials and an operand-exponent range estimate before arithmetic starts, so later instructions issue past safe ones; an unsafe operation stalls until the flag stage (rare with a wide internal exponent range). Pipeline-control flavoured; reject instead if the registry excludes precise-exception mechanisms [alpert_1993]  (from fp_safe_instruction_recognition)
* lza.correction_scheme += true_count_lsb_compare — one carry tree computes the LSB of the true count, a compare against the predicted LSB drives a final shifter stage able to shift 0, 1 or 2 positions [dimitrakopoulos_2008]  (from leading_zero_anticipation)
* lza += choice split_string_select: {true_sign, maximum_count} — how the positive and negative indicator strings (`string_form=dual_pos_neg_strings`) are chosen between [dimitrakopoulos_2008]
* lza += choice input_count: Int[2..4:1] — a bitwise pre-encoder forms the column sums of three or four possibly inverted aligned significands into one indicator vector; the MSB-first LZD overlaps the shifter (`encode_direct_to_shift`) and the 1-bit error uses `correction_scheme=concurrent_correction` [sohn_2014, sohn_2016]  (from three_input_lza and leading_zero_anticipation)
* lza += choice indicator_restriction: {general, positive_result_only, exponent_difference_one} — restricted indicators assume a nonnegative subtraction result or an exponent difference of one (the close-path cases) and are cheaper than the general leading-zeros-and-ones form [schmookler_2001]  (from leading_zero_anticipator)
* lza += choice zero_result_detect: {indicator_or, operand_function_or} — the all-zero result is detected from the indicator string or directly from an operand function [schmookler_2001]
* sig_mul_then_round += choice sticky_method: {post_cpa_or_tree, input_trailing_zero_count, carry_save_or, minus_one_group_propagate} — sticky from the low product bits after the CPA, from summed operand trailing-zero counts during the multiply, from the carry-save bits below R (positive partial products), or from the group propagate of a product-minus-one summation restored by carry-in 1 (XOR propagates make the sticky equal the group propagate); the same choice belongs on `round_fused_in_reduction`, which already cites `santoro_1989` [santoro_1989, bewick1994#s09]  (from sticky_bit_generation and minus_one_prefix_sticky)
* fp_add_space (every family) += choice dependent_result_forwarding: {none, redundant_packet_two_cycle, rounded_unnormalized_feedback} — the packet form emits sign/exponent/borrow-save principal part after cycle 2 and a two-digit carry-round part after cycle 3, so a dependent operation starts every two cycles while the IEEE result retires at cycle 4 (the consumer's operand interface accepts standard-plus-packet); the feedback form returns the correctly rounded but unnormalized significand with its predicted normalization distance and overlaps its normalization with the next addend's alignment (2-cycle accumulate, four extra multiplexers). The existing `variable_latency` mutation `bypass_result_before_round_for_dependents` is the pre-round bypass point of the same axis [nielsen_2000, beaumont_smith1999]  (from packet_forwarding_fp_adder and unnormalized_feedback_fp_accumulator)
* rounding_space.position += before_fine_normalize_multi_location — rounding signals are generated for every candidate rounding location before the fine normalization shift and the completed decision selects among duplicated redundant-to-nonredundant conversions (borrow-in 0 and 1), which removes the rounding carry from the critical path [wahba_2017]  (from rounding_while_redundant)
* rounding_space.compound_adder_select += choice speculative_locations: Int[1..3:1] — candidate rounding positions evaluated in parallel: three in binary, two in decimal because the decimal LZA may be off by one digit [wahba_2017]

## new families

Three families from 11 proposals. The first two need a new sub-space above the
datapath spaces (an `fpu_spaces.py`; `fma_dot_spaces.py` imports `fp_spaces.py`, so
the family cannot live in either without an import cycle). Whether the registry's
scope includes FPU-level organization at all is the main human decision; if it does
not, the merged proposals of `partitioned_fpu` fall to rejected except
`multi_precision_simd_fp_pipeline` (absorbed: `multi_precision_simd_fma.lane_split=2x32`
for the fp64 multiplier reused as two fp32) and
`format_separated_clock_gated_fp_datapath` (absorbed:
`bridge_fma.composition_style=cascade_mul_then_add` for the 2+2-cycle separate
multiply/add FMA).

### partitioned_fpu

Merged from: instruction_oriented_concurrent_fpu (anderson1967),
shared_partitioned_arithmetic_pipeline (watson_1972), queued_binary_fp_coprocessor
(darley_1990), multisection_pipelined_fpu (alpert_1993), parallel_fp_pipeline_cluster
(christie_1996), format_separated_clock_gated_fp_datapath (lutz_2019),
configurable_transprecision_fpu (mach_2020), multi_precision_simd_fp_pipeline
(saporito_2020). All eight describe how one FPU partitions its operation classes and
formats across units or shared sections and how issue is decoupled from them.

* domain: fp (new FPU-level sub-space; slots are the existing fp/fma spaces)
* doc: "the FPU above the datapaths: which operation classes get their own unit, per-format vs merged slices, and how issue is decoupled (Model 91 stations, Pentium sections, FPnew generator)"
* execution_style: feed_forward (default; omitted in the snippet as `fp_spaces.py` does)
* mechanism: Operation classes (add; multiply/divide; compare/move; divide/sqrt; conversion) execute in separate pipelined units, or in shared sections (TI ASC's eight partitions, Pentium's shared FEXP/FRND around dedicated FMUL/FADD/FDIV). Each unit is one merged multi-format slice or parallel per-format slices with per-unit clock gating (six gated units replace one binary32/2×binary16 FMA for about 33% dynamic power). Reservation stations, an instruction queue or a shared reorder buffer decouple issue; forwarding paths cut dependent latency; a load balancer assigns long divide/sqrt operations across pipelines.
* choices (each with the proposals that give evidence):
  * `unit_partition: {shared_sections, dedicated_per_operation, dedicated_per_operation_and_format}` [watson_1972, anderson1967, alpert_1993, christie_1996, darley_1990, lutz_2019, mach_2020]
  * `unit_count: Int[2..6:1]` [anderson1967 2, darley_1990 2, alpert_1993 3, christie_1996 3, mach_2020 4 groups, lutz_2019 6]
  * `format_slice: {single_format, merged_multi_format, parallel_per_format}` [mach_2020, lutz_2019, saporito_2020]
  * `shared_exponent_round_sections: Bool` [alpert_1993, watson_1972]
  * `issue_decoupling: {none, reservation_stations, instruction_queue, shared_reorder_buffer}` [anderson1967, darley_1990, christie_1996]
  * `station_or_queue_depth: Int[1..8:1]` [anderson1967 3/2, darley_1990 Int[1..8], christie_1996 1]
  * `pipeline_count: Int[1..4:1]` [watson_1972, saporito_2020]
  * `per_unit_clock_gating: Bool` [lutz_2019, mach_2020]
  * `result_forwarding: Bool` [alpert_1993]
  * `long_op_load_balancing: Bool` [saporito_2020]
  * `exception_completion: {full_hardware, software_trap_assist}` [darley_1990]
  * `latency_handshake: {fixed, valid_ready}` [mach_2020]
* slots: `add: fp_add_space`, `mul: fp_mul_space`, `fma: dot_acc_space` (classic_fma, multi_precision_simd_fma, bridge_fma), `div_sqrt: fp_div_space`, `cmp: fp_cmp_space`, `cvt: fp_cvt_space`
* mutations: split_unit_per_format, merge_formats_into_one_slice, add_reservation_stations, share_exponent_and_round_sections, gate_inactive_unit, add_result_forwarding_path, balance_long_ops_across_pipelines
* handles: anderson1967, watson_1972, darley_1990, alpert_1993, christie_1996, lutz_2019, mach_2020, saporito_2020
* evidence: 8 papers; 5 landmark (anderson1967, watson_1972, alpert_1993, christie_1996, mach_2020), 1 survey (saporito_2020), 2 incremental (darley_1990, lutz_2019); no textbook or thesis block. Quantified results: lutz_2019 about 33% dynamic power; mach_2020 9.3% core area for five formats plus SIMD; saporito_2020 about 15% fewer issue stalls from load balancing; alpert_1993 3-cycle latency, 1/cycle throughput.
* thin choices (one paper each, droppable): `result_forwarding`, `long_op_load_balancing`, `exception_completion`, `latency_handshake`.

```python
        Architecture(
            "partitioned_fpu",
            papers=("anderson1967", "watson_1972", "darley_1990",
                    "alpert_1993", "christie_1996", "lutz_2019",
                    "mach_2020", "saporito_2020"),
            design_choices={
                "unit_partition": EnumChoice(
                    ("shared_sections", "dedicated_per_operation",
                     "dedicated_per_operation_and_format")),
                "unit_count": IntRange(2, 6),
                "format_slice": EnumChoice(
                    ("single_format", "merged_multi_format",
                     "parallel_per_format")),
                "shared_exponent_round_sections": BoolChoice(),
                "issue_decoupling": EnumChoice(
                    ("none", "reservation_stations", "instruction_queue",
                     "shared_reorder_buffer")),
                "station_or_queue_depth": IntRange(1, 8),
                "pipeline_count": IntRange(1, 4),
                "per_unit_clock_gating": BoolChoice(),
                "result_forwarding": BoolChoice(),
                "long_op_load_balancing": BoolChoice(),
                "exception_completion": EnumChoice(
                    ("full_hardware", "software_trap_assist")),
                "latency_handshake": EnumChoice(("fixed", "valid_ready"))},
            components={"add": fp_add_space(),
                        "mul": fp_mul_space(mant_bits),
                        "fma": dot_acc_space(mant_bits),
                        "div_sqrt": fp_div_space(),
                        "cmp": fp_cmp_space(),
                        "cvt": fp_cvt_space()},
            mutations=("split_unit_per_format",
                       "merge_formats_into_one_slice",
                       "add_reservation_stations",
                       "share_exponent_and_round_sections",
                       "gate_inactive_unit",
                       "add_result_forwarding_path",
                       "balance_long_ops_across_pipelines"),
            doc="the FPU above the datapaths: which operation classes "
                "get their own unit, per-format vs merged slices, and "
                "how issue is decoupled (Model 91 stations, Pentium "
                "sections, FPnew generator)"),
```

### internal_format_datapath

Merged from: hex_internal_multiformat_fpu (schwarz_1999) and internal_format_fp_interop
(slegel_1999). Both describe the S/390 G5 unit: one design, two papers.

* domain: fp (same new FPU-level sub-space as `partitioned_fpu`, or a wrapper beside the `sig_*_then_round` families)
* doc: "architected formats converted at the operand/result boundaries into one wide internal format that an inherited datapath executes (G5: BFP through the HFP hex macros, one final binary rounder)"
* execution_style: feed_forward
* mechanism: Input converters after the operand registers translate every architected format (three HFP and three BFP formats) into one internal representation with a 56-bit hexadecimal-based fraction and a 14-bit exponent. The existing hexadecimal alignment, arithmetic and normalization macros perform the computation for add, multiply, divide, square root and stores. Sticky logic and one final binary rounder convert results back, handle five rounding modes and special values, and preserve the inherited HFP critical paths. HFP operands keep one result per cycle at 3-cycle latency; BFP operands take two cycles per result at 5-cycle latency.
* choices:
  * `internal_radix: {binary, hexadecimal}` [schwarz_1999]
  * `internal_fraction_bits: Int[53..64:1]` and `internal_exponent_bits: Int[11..16:1]` — the proposals evidence one point (56, 14); the ranges are the reviewer's brackets and need a human choice [schwarz_1999]
  * `architected_formats: {hfp_only, bfp_only, hfp_and_bfp}` [slegel_1999]
  * conversion placement (operand and result boundaries) and the preserve-inherited-timing policy are single-valued in the evidence, so they stay in the doc rather than as choices.
* slots: `core_add: fp_add_space`, `core_mul: fp_mul_space`, `core_div: fp_div_space`, `round: rounding_space` (five modes); the input converter has no existing sub-space (`fp_cvt_space.shift_round_convert` is the nearest)
* mutations: widen_internal_exponent (exists in `subnormal_space`), add_boundary_converters and unify_datapaths_over_shared_core (both exist in `posit_ieee_interop`)
* handles: schwarz_1999, slegel_1999
* evidence: 2 papers (schwarz_1999 landmark, slegel_1999 incremental) on one design; no textbook or thesis block. Results: about 100x over software BFP, 500 MHz.
* deciding question: `dsp_posit_spaces.posit_ieee_interop.interop_style=boundary_converters` is the same structure bound to posit. The prefer-new-values rule would make this `posit_ieee_interop += choice format_pair: {posit_ieee, bfp_hfp}`, which mis-names that family; a format-agnostic family with the posit case as one value of `architected_formats` is the cleaner alternative, and a human must pick one.

```python
        Architecture(
            "internal_format_datapath",
            papers=("schwarz_1999", "slegel_1999"),
            design_choices={
                "internal_radix": EnumChoice(("binary", "hexadecimal")),
                "internal_fraction_bits": IntRange(53, 64),
                "internal_exponent_bits": IntRange(11, 16),
                "architected_formats": EnumChoice(
                    ("hfp_only", "bfp_only", "hfp_and_bfp"))},
            components={"core_add": fp_add_space(),
                        "core_mul": fp_mul_space(mant_bits),
                        "core_div": fp_div_space(),
                        "round": rounding_space()},
            mutations=("widen_internal_exponent",
                       "add_boundary_converters",
                       "unify_datapaths_over_shared_core"),
            doc="architected formats converted at the operand/result "
                "boundaries into one wide internal format that an "
                "inherited datapath executes (G5: BFP through the HFP "
                "hex macros, one final binary rounder)"),
```

### sig_sqrt_then_round

From: fp_significand_sqrt_then_round (muller_2018#s07). Not merged.

* domain: fp; a second candidate in `fp_div_space` beside `sig_div_then_round` (or a new `fp_sqrt_space`, the human's call)
* doc: "significand square root (any div_space sqrt family), exponent made even and halved, correctly-rounded final step; a finite positive root never overflows or underflows"
* execution_style: feed_forward (the iteration lives in the slot family, as for `sig_div_then_round`)
* mechanism: The input is normalized (a subnormal input is pre-normalized), the exponent is adjusted to even parity and halved, the significand square root is computed by digit recurrence, functional iteration or polynomial approximation, and the result is rounded correctly. Digit recurrence keeps an exact remainder for the rounding decision; functional iteration needs the last iteration at about twice the target precision. A finite positive square root cannot produce underflow or overflow, so the exponent range check is unnecessary.
* choices: none beyond the slot. The proposal's `significand_algorithm` is the slot filler and `subnormal_input_normalization` has one evidenced value (pre_normalize), so no `design_choices` are declared, matching `sig_div_then_round`.
* slots: `sig_sqrt: div_space` (fillers: `digit_recurrence_sqrt_combined` for digit recurrence; `newton_raphson`/`goldschmidt` for functional iteration; polynomial approximation has no `div_space` filler, and `sfu_spaces` `single_poly`/`piecewise_poly` with `correct_rounding_strategy` are the nearest), `round: rounding_space`, `exp: exponent_space`, `subnormal: subnormal_space`
* mutations: fuse_div_sqrt (exists in `div_space`), drop_exponent_range_check
* handles: muller_2018#s07
* evidence: 1 textbook block (muller_2018#s07, pp.277-279), no paper; the note's taxonomy maps sqrt to `digit_recurrence_sqrt_combined` and `newton_raphson`, and lists the sqrt wrapper as a space gap. Abstract results only (iteration counts, no under/overflow).

```python
        Architecture(
            "sig_sqrt_then_round",
            papers=("muller_2018",),
            components={"sig_sqrt": div_space(),
                        "round": rounding_space(),
                        "exp": exponent_space(),
                        "subnormal": subnormal_space()},
            mutations=("fuse_div_sqrt", "drop_exponent_range_check"),
            doc="significand square root (any div_space sqrt family), "
                "exponent made even and halved, correctly-rounded final "
                "step; a finite positive root never overflows or "
                "underflows"),
```

## rejected

* arithmetic_pipeline_power_modes — chip operating modes (2.0 to 2.2 GHz boost, eco mode idling one of two FPU pipes under software control) with no datapath structure; a product operating point [sato_2020].
* fp32_bfloat16_tensor_conversion — Quantlib is a software emulation of bfloat16 (zero the low 16 bits of an fp32 container, RNE or truncation) and a format study; `bf16_fma_datapath` already cites `kalamkar_2019` and its `rounding_mode` choice covers rne/rtz [kalamkar_2019].

absorbed 4, new values 13, new families 3 (from 11 proposals), rejected 2
