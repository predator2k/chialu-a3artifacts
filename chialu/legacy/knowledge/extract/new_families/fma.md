# new-family review: fma

Source: the 16 FMA papers registered on 2026-09-18 (`legacy/knowledge/pdf/fma/`, moved into
`legacy/knowledge/pdf/`). No `run/extract/reduce/newfam_fma.md` bundle exists, because the driver
groups new-family proposals by vocabulary domain and this corpus spans dot, fp, mul, shift, checker
and decimal. The review is built from the `## new_families`, `## space_gaps`, `new_choices` and
`[outside domain]` lines of the 14 notes written in this run (`naini_2001`, `boersma_2011`,
`quach_1991`, `galal_2011`, `galal_2013`, `jessani_1996`, `jessani_1998`, `lichtenau_2016`,
`manolopoulos_2016`, `oh_2006`, `mueller_2005`, `vangal_2006`, `zhang_2018`, `schwarz_2003`) plus the
two notes the corpus already had (`bruguera_2005`, `uguen_2017`) and `lutz_2011`, which the ALU's
`fp_fma` slot work cites. Registry read: `chialu/spaces/fma_dot_spaces.py`,
`chialu/spaces/fp_spaces.py` (`fp_add_space` and `fp_fma_space`), `chialu/spaces/mul_spaces.py`,
`chialu/spaces/shift_simd_spaces.py`, `chialu/spaces/checker_spaces.py` and
`chialu/spaces/decimal_spaces.py`.

## handle notes for the human

* Three of the 16 files duplicate papers the corpus already held. `hardware-implementations-of-denormalized-numbers.pdf` and `kulisch-acc-2017.pdf` are byte-identical to the files already registered under `schwarz_2003` and `uguen_2017`, and the third is another scan of `bruguera_2005`. The duplicates stayed in `legacy/knowledge/pdf/fma/` and the 13 new files moved up.
* `schwarz_2003` was already in `handles.json` and in `inventory.tsv`, and had no note, because its PDF is a scan whose only text layer is the ARITH'03 copyright banner. The note in this run was extracted from a tesseract OCR of that scan, so its numbers carry OCR risk and its page references are `§N` section numbers. `ocrmypdf` over the corpus file would let `python3 -m chialu.extract run --only schwarz_2003` reproduce it.
* `bruguera_2005` and `uguen_2017` already had notes, so they were not re-extracted.
* `galal_2011`, `galal_2013`, `quach_1991`, `jessani_1998`, `manolopoulos_2016`, `vangal_2006` and `zhang_2018` entered `legacy/knowledge/bib/fma_dot.md`; `naini_2001`, `jessani_1996`, `mueller_2005`, `oh_2006`, `boersma_2011` and `lichtenau_2016` entered `legacy/knowledge/bib/commercial_units.md`.
* `chialu/extract.py`'s `_named_spaces()` does not list `fp_spaces.fp_fma_space`, so the vocabulary the extractor classified against never contained `separate_multiplier_and_adder` and never contained the ALU slot's `sharing` choice. Every line below that concerns the ALU's `fp_fma` slot was therefore derived by this review from the notes' prose, rather than proposed by a note. `chialu/papers.py`'s `_all_spaces()` does list `fp_fma_space`, which is why `chialu.archdocs` sees the family and `chialu.extract` does not.
* `lutz_2011` is cited by `arch/dot/classic_fma.md` and its note predates this run; its lines below are marked with its handle so a human can see which proposals do not rest on the new corpus.
* A concurrent session edited `chialu/spaces/fp_spaces.py` while this run was in progress and added `subnormal_representation` to `_fma_common_choices()`, so the ALU slot's `classic_fma`, `reduced_latency_fma` and `multipath_fma` now carry that choice and their cards carry a `### subnormal_representation (the ALU's fp_fma slot)` table. Every line below was written against the space as it stands after that edit. The dot copies of the same three families still have no subnormal choice, which is the asymmetry the `denormal_operand_handling` line records.

## what the product FPUs bind

Five of the new papers are product floating-point units. The table records what each one settles for
the choices the spaces already carry, which is evidence for the cards rather than a proposal.

| unit | organization | negation_handling | alignment width | leading zeros | subnormals |
| --- | --- | --- | --- | --- | --- |
| PowerPC 603e (`jessani_1996`) | `classic_fma`, `subsume_fp_add=True`, dual-pass array | `end_around_carry` | `full_align` | `lzc_after_add` | prenormalized and denormalized through the writeback normalization shifter, at a stated cycle cost |
| PowerPC 604e (`jessani_1998`) | `classic_fma`, `subsume_fp_add=True`, single-pass array | `end_around_carry` | `full_align`, 53-bit input over a 161-bit range, addend 56 bits left of the product point | not stated | not stated |
| CELL SPE SPfpu / DPfpu (`mueller_2005`, `oh_2006`) | `classic_fma`, `subsume_fp_add=True` | `end_around_carry` | `full_align`, sum-addressed, 96-bit SPfpu aligner | `lza`, Hokenek-Montoye edge vector, the DPfpu splitting the folded edge vector across two counters rather than one 106-bit count | SPfpu flushes to zero and rounds toward zero only; the DPfpu computes denormal results and offers all four modes |
| POWER7 (`boersma_2011`) | `classic_fma` and `multi_precision_simd_fma` | not stated | `full_align` | `lza` over the trailing 110 bits of the sum | architected pattern plus a dirty flag, rather than the 65-bit pseudo-normalized intermediate format of POWER6 |
| IBM z13 (`lichtenau_2016`) | `single_path` adder with an `injection` rounder | `end_around_carry` | `full_align` | `lza` | not stated |
| SPARC64 (`naini_2001`) | separate FADD and FMUL units; the fused instructions are `bridge_fma` with `composition_style=cascade_mul_then_add` | not stated | `full_align`, speculative 0/1/2/3-bit pre-shift of both mantissas in stage 1 | `lza` on the close path | only normalized results; denormal operands and results trap as unfinished-FPop |

`path_count` is bound by three papers: `quach_1991`'s SNAP is 2, `manolopoulos_2016` is 2, and
`vangal_2006` is 4. `normalize_before_add` is bound by `manolopoulos_2016` (true on the far path,
with the close path normalizing in the third stage) and by `lutz_2011`, whose unified add path runs
the anticipator two cycles before the addition. `mueller_2005` compares its unit against
`multipath_fma` at five cases in the variable-latency design and two parallel paths in the
fixed-latency one, and against `reduced_latency_fma` with `rounding_position=fused_with_cpa_dual_sum`.

## absorbed

* `carry_save_toggle_detector -> lza` — the proposal is an anticipator that reads a sum/carry pair rather than an assimilated word, which is the form `arch/fp/lza.md` already names for fused units ("the anticipator reads the adder's operands; a carry-save pair ... are the fused units' forms"). Its 3-bit inspection window over the unformed sum, its 57 instances and its one-to-two-position error corrected by a compensatory shift are that family's parameters. What the family does not carry is the operand representation and the second use of the same circuit for mantissa overflow, which are the two `lza` value lines below. [vangal_2006]
* `decimal_binary_radix_conversion -> binary_decimal_conversion` — the family is already proposed and applied in `new_families/decimal.md` and `new_families/decimal.applied.md`, whose `structure` and `operand_class` choices cover the iterative cell recurrence. The z13 contribution is that the reduction hardware is the binary multiplier's own compressor rather than a dedicated array, which is the `reduction_hardware` value line below. [lichtenau_2016]
* `bridge_fma.augend_arrival -> bridge_fma.composition_style=bridge_reuse` for the composition itself — Lutz's separate early-normalizing multiply and add pipelines are the `bridge_reuse` value, which his own note pins. The deferred augend is a scheduling property of that value and is the `augend_arrival` line below, not a second composition. [lutz_2011]
* `naini_2001`'s Path 2 rounding increment through a CSA row at lsb+1 -> `injection` — a constant added below the kept lsb in place of a flagged adder is the injection family's mechanism, and the family's `injection_adder` slot is where the CSA row lands. The paper's reason, that a flagged adder's split carry chain would slow the adder topology, belongs in the `injection` card rather than in the space. [naini_2001]

## new values

Grouped by host family. Each group names the papers that give the evidence.

### classic_fma (dot), and the same family in the ALU's `fp_fma` slot

* `classic_fma += choice multiply_array_passes: Int[1..4:1]` — the number of times the multiplier operand passes through the partial-product array per double-precision product. The PowerPC 604e uses one pass over a 27-partial-product radix-4 array; the PowerPC 603e uses two passes over a 14-partial-product array, which is half a full 53 by 53 array, and one pass for single precision. The array falls from 5.1 mm2 to 2.5 mm2 and from 13 CSA groups to 7 in 0.5 um CMOS, and double-precision multiply throughput falls from one to two cycles per instruction. This is the axis the task's "single- versus dual-pass" question names, and it is the only axis on which those two product units differ. [jessani_1998, jessani_1996]
* `classic_fma += choice addend_csa_stage_placement: {multiply_stage, add_stage}` — where the 3:2 CSA group that injects the aligned addend sits. [jessani_1998]
* `classic_fma += choice aligned_addend_partition: {whole, split_across_passes}` — the 603e splits the 161-bit aligned addend into a low 26 bits consumed in pass 1 and an upper 135 bits consumed in pass 2, which turns one 161-bit adder into a 26-bit incrementer, an 81-bit carry-lookahead block and a 54-bit incrementer. The value is meaningful only when `multiply_array_passes > 1`. [jessani_1998]
* `classic_fma += choice denormal_operand_handling: {in_dataflow_correction, prenormalize_with_stall, trap_to_software}` and `choice prenormalization_scope: {none, special_cases_only, all_operands}` — Power3 prenormalizes the addend for the difficult cases only, Power4 prenormalizes every operand for single and double precision, and the later zSeries traps on the disjoint case. The disjoint case is a denormalized addend with a product below the addend's least significant bit, which the concatenated dataflow cannot represent to 53 bits of significance. The 603e prenormalizes sources and denormalizes results through the writeback normalization shifter. `subnormal_representation` says how a subnormal operand is represented and these two say what the unit does about it, so they sit beside that choice rather than replacing it. The ALU slot's copy of the family now carries `subnormal_representation` and the dot copy carries neither choice. [schwarz_2003, jessani_1996, mueller_2005]
* `classic_fma += choice internal_exponent_width_bits: Int[11..16:1]`, or the same choice on `exponent_path` — Power4 carries 13 exponent bits, two more than the architected double exponent, so a prenormalized operand below Emin still has an exponent, the product of two denormals with the underflow trap enabled is representable, and the alignment shift count cannot wrap past zero or all ones. POWER7 makes the same field a biased two's complement value rebiased by the target precision's eminT, which removes several 13-bit comparators. [schwarz_2003, boersma_2011]
* `classic_fma += choice denormal_detection: {register_tag_bits, in_unit_exponent_decode}` — Power4 carries three tag bits plus an integer bit per floating-point register, against decoding the exponent inside the unit. POWER7 carries the architected pattern plus a dirty flag. The same choice applies to the adder and multiplier families. [schwarz_2003, boersma_2011]
* `classic_fma += choice ieee_support_level: {truncation_only_no_denormals, all_rounding_modes_and_denormals}` — the measured cost of the IEEE rounding modes and denormals is 5 to 10 percent of the unit, and the CELL SPE ships both points in one processor: the SPfpu flushes to zero and rounds toward zero only, the DPfpu computes denormal results and offers all four modes. `tensor_core_mixed_precision_mac.subnormal_support` and `fp8_training_datapath.flush_subnormals` already carry the AI-datapath form of this choice, so the FMA lineage is the gap. [galal_2011, mueller_2005, oh_2006, vangal_2006]
* `classic_fma += slot exp: exponent_path` — the exponent path computes the alignment shift amount, the overflow and underflow conditions and the result exponent, and POWER7 reports it as carrying the unit's two most critical paths. The exponent path is behavioral in the library's module today, which the `arch/dot/classic_fma.md` card states; the slot would make it searchable. [boersma_2011, oh_2006, schwarz_2003]
* `classic_fma += choice operand_order_fused: {a_times_b_plus_c, a_times_c_plus_b}` — which of the three source operands is the addend. The CELL SPE reports that the second order removes a multiplexer from the multiplier inputs. The name must not collide with `fp_add_space`'s `operand_order`, which is the adder's swap decision. [mueller_2005]
* `classic_fma += choice unrounded_result_forwarding: Bool` — forwarding the unrounded intermediate result costs one additional partial product in the generated unit, and POWER7 changes exactly this property from POWER6 to reach a 5.5-cycle target. `arch/dot/classic_fma.md` already describes the POWER6 stage-6 forwarding, and `gaps/classic_fma.md` already carries a `unfinished_result_forwarding` bullet from `trong_2007`; apply once. [galal_2013, boersma_2011]

### fp_fma_space (the ALU's `fp_fma` slot, `chialu/spaces/fp_spaces.py`)

The slot currently offers `separate_multiplier_and_adder`, `classic_fma`, `reduced_latency_fma` and
`multipath_fma`. Four of the new papers measure exactly the choice this slot names, and all four
compare a fused datapath against separate multiply and add pipelines at one technology.

* `fp_fma_space += bridge_fma` (the dot family, admitted to the ALU slot as a fifth organization) — the bridge is the third point between `separate_multiplier_and_adder` and the fused families: full-rate separate multiply and add pipelines, with a bridge or an internal bus handing the unrounded product to the adder so the fused operation still rounds once. SPARC64 ships it as two functional units whose fused instructions cascade multiply into add. Galal's generator finds the cascade dominating the latency frontier, because a dependent instruction's latency and the latency of add-without-multiply are both shorter, while the fused unit dominates the throughput frontier, because the cascade trades logic for latency. Lutz's separate early-normalizing pipelines are the same organization with `composition_style=bridge_reuse`: a 4+4-stage pair beats a 7-stage fused pipeline by 3 to 23 percent on six Cortex-A8 benchmarks and cuts a four-term dot product from 28 to 17 cycles. Admitting `bridge_fma` gives the ALU slot the organization those papers actually measure, which today it can only express as `separate_multiplier_and_adder` (two roundings) or as a fused family (one rounding, add pays the window). [naini_2001, galal_2011, galal_2013, quach_1991, lutz_2011]
* `separate_multiplier_and_adder += choice product_forwarding: {none, unrounded_to_adder}` — the alternative to admitting `bridge_fma`. Under `unrounded_to_adder` the multiplier's unrounded 106-bit mantissa reaches the adder, so a multiply-add sequence rounds once while the two structures stay separate. The deciding question is whether the ALU slot should hold the bridge as an organization of its own or as a forwarding option on the separate organization; the first matches `fma_dot_spaces.py`, and the prefer-values rule argues for the second. [lutz_2011, quach_1991]
* `separate_multiplier_and_adder += choice sharing: FMA_SHARING` — the family declares no choices at all, so a mode that picks the separate organization cannot say whether its adder and multiplier are dedicated per mode or shared across formats, although its three siblings can. FPnew's PARALLEL slice is per-format by construction and its predecessors' `fpnew_add`/`fpnew_mul` units are not, which is the distinction the value names. [mach_2020 via the existing card, naini_2001]
* `fp_fma_space's fused families += choice multiply_array_passes: Int[1..4:1]` — the same line as under `classic_fma`. In the ALU slot it is the one axis that lets a narrow mode reuse a wider mode's array over two cycles, which is what the 603e does for double precision, and it needs the sequential contract the single-cycle scope excludes.
* `reduced_latency_fma += choice normalize_before_add` already exists, and `manolopoulos_2016` binds it true on the far path with the close path normalizing in the third stage; `lutz_2011` binds the equivalent on `delay_optimized_unified` as `lza_timing=two_cycles_before_addition`. No value is missing; the note is that the ALU slot's copy of `reduced_latency_fma` omits `rounding_position`, which the dot copy carries and which both papers bind to `fused_with_cpa_dual_sum`. Align the two family definitions or record why they differ. [manolopoulos_2016, mueller_2005, lutz_2011]

### multipath_fma

* `multipath_fma += choice negation_handling: NEGATION_HANDLING` in the dot space — the dot copy of the family declares no `negation_handling`, although the ALU copy does and `manolopoulos_2016` fixes it: the close path uses two's complement to avoid the end-around-carry adjustment, with the +1 added through an empty slot of the 117-bit 3:2 CSA, and a row of half adders carries the same +1 on the far path. [manolopoulos_2016]
* `multipath_fma.path_select_criterion += zero_operand_detect` — the fourth path of the Intel FPMAC selects the incoming mantissa when an early zero detector finds the accumulated result zero in carry-save form, which is needed because the feedback exponent may be non-zero while the feedback mantissa is zero. The family's `path_count` already reaches 5 and its card already describes a zero-operand bypass, so the gap is the selection criterion rather than the path. [vangal_2006]
* `multipath_fma`'s `align` slot admits `bounded_align` in the dot space through `dot_align_space`, and `vangal_2006` binds it to a constant SHR32/SHL32 pair rather than a variable bounded shift. A `bounded_align.shifter` value for a constant shift by the accumulation radix is the line; today the slot's `bound` range (2 to 8) cannot express it. [vangal_2006]

### streaming_accurate_accumulator, and the multiply-accumulate loop

* `streaming_accurate_accumulator += choice accumulation_radix: Int[2..64:2]` restricted to powers of two, or `Enum((2, 32, 64))` — the loop's exponent radix. Base 32 makes every in-loop alignment a constant 32-bit shift, because the incoming mantissa is pre-shifted by Exp[4:0] outside the loop; double precision needs base 64. The radix sets the in-loop mantissa width, here 24 bits extended to 55, and it is what removes the variable alignment shifter from the single-cycle accumulate loop. [vangal_2006]
* `streaming_accurate_accumulator += choice alignment_reference: {accumulated_result, incoming_operand_self_align}` — the incoming number aligns itself every cycle rather than being aligned to the running sum, which is the second half of the same removal. [vangal_2006]
* `streaming_accurate_accumulator += choice deferred_normalization_gating: {none, clock_gating, clock_gating_plus_power_gating}` — the conditional normalization the paper's title names. The normalization pipeline sits outside the accumulate loop and is clock-gated and power-gated by low-Vt nMOS sleep transistors under a software-set `norm_en`. The paper reports that `norm_en` must stay asserted at least four core cycles, and that clock gating alone is the recommendation at low activation rates, because switching the large sleep transistor can cost more than the leakage saved. `in_loop_normalization=False` already records that the normalization left the loop; this choice records what happens to the stage that left. [vangal_2006]
* Carry-save accumulation itself needs no new value: `window_bits` holds the 55-bit in-loop mantissa, `approach=shifted_fixed_point_window` holds the fixed-point window, and the `cpa` slot holds the delayed addition's final adder, which `vangal_2006` fills with `sparse_prefix_hybrid`. What the family cannot record is that the loop carries an unassimilated sum/carry pair at all, which is the `lza.operand_representation` line below and the `sparse_prefix_hybrid.log2_sparsity` line. [vangal_2006]

### lza

* `lza += choice operand_representation: {assimilated_twos_complement, carry_save_pair}` — the anticipator either reads one binary word or reads an unformed sum/carry pair. The carry-save form holds irrespective of the result's sign and of the operands' relative magnitudes, and its error is one or two positions rather than one, corrected by a compensatory shift after the sign-magnitude conversion. The family's card already says a carry-save pair is the fused unit's form, so the choice makes an existing statement selectable. [vangal_2006, mueller_2005]
* `lza += choice prediction_target: {leading_zero_one, leading_zero_one_and_overflow}` — the same three-bit-window toggle circuit that anticipates the leading transition also predicts mantissa overflow when applied to the three most significant bits, at the cost of six pessimistic patterns out of eighteen where no carry reaches the inspected position. [vangal_2006]
* `lza += choice count_partition: {single, per_folded_row}` — the CELL DPfpu folds the wide intermediate fraction into two or three rows and drives two smaller leading-zero counters from the folded edge vector rather than one 106-bit counter. [mueller_2005]
* `lza += choice normalization_bound: {full, bounded_at_emin}` — a denormal result stops the normalization at Emin, which Schwarz treats as a modification of the anticipator rather than an option on the normalizer. [schwarz_2003]

### booth_recoded_parallel, csa_reduction_tree and twin_precision_subword

* `booth_recoded_parallel += choice signedness_selection: {compile_time, run_time}` — one control signal switches the shared partial-product generate logic between unsigned and signed operation, which is what lets one array serve a floating-point mantissa product and packed fixed-point products. [zhang_2018]
* `booth_recoded_parallel.sign_extension += reduced_left_edge_banded` and `+= hot_one_encoding` — the 604e's encoded partial products give a 57-bit pp0 and 56-bit pp1 through pp26, and the CELL SPE uses hot-1 encoding. [jessani_1998, oh_2006]
* `booth_recoded_parallel += choice row_capacity: Int[8..32:1]` beside the rows used — the 603e's tree admits 16 rows and uses 14. Thin, one paper. [jessani_1998]
* `booth_recoded_parallel.hard_multiple_gen += synthesized_odd_multiples` — the +-5 and +-7 multiples of radix-16 Booth are left to standard synthesis rather than generated by a named structure. [galal_2013]
* `csa_reduction_tree += choice element: {counter_7_3, compressor_4_2, counter_3_2}` and `+= choice topology: {array, wallace, zm, os}` — the family appears in the vocabulary only as a slot filler and declares no choices, although the generator study fixes both axes and reports that each trades delay against track count and wire length. The Pareto designs are mostly Booth 3 with Wallace or ZM trees on the throughput frontier and Booth 2 with Wallace or OS trees on the latency frontier. [galal_2013, lutz_2011]
* `csa_reduction_tree += choice delay_balanced_interconnect: Bool` — routing level i's early carry outputs to level i+1's slow inputs and its late ones to that level's carry-in makes two levels cost 1.5 CSA delays rather than 2, which the study reports as beating both (7,3) counters and 4:2 compressors. [galal_2013]
* `twin_precision_subword += choice lane_isolation: {zero_select_cross_quadrants, explicit_carry_kill, partial_product_zero_pad}` — three ways to keep the unused quadrants from contributing. [galal_2013]
* `multi_precision_simd_fma.lane_split += 1x128` and its `multiplier` slot `+= twin_precision_subword` — one 128-bit register splits into one quadruple, two double or four single precision operands, and the one-array-serves-three-precisions multiplier is the twin-precision family. Both values are missing today; `lane_split` stops at `1x64`. [manolopoulos_2016]
* `multi_precision_simd_fma += choice exponent_unit_replication: {one_shared, per_narrow_mode}` — the design adds one double and two single precision exponent processing units beside the quadruple precision one and reuses the wider unit for a narrower instruction. [manolopoulos_2016, boersma_2011]
* `recursive_karatsuba.split_kind += unequal_two_way` — the 11-bit mantissa splits into a 3-bit high part and an 8-bit low part, which is what makes the two 8-bit submultipliers reusable as the packed fixed-point lanes. [zhang_2018]
* `integer_mac += choice float_path_bypass: Bool` — in fixed-point mode the unit bypasses the accumulator inversion, the alignment shifter and the complementer, and the result leaves after two pipeline stages rather than three. The merged unit is 21 percent smaller and 30.4 percent lower power than the two single-mode units at STM 90 nm, and its area overhead over a floating-point-only unit is the added multiplexers. The deciding question is whether the registry models one unit serving two number systems at all; if it does not, this line and the `booth_recoded_parallel.signedness_selection` line together are the whole of `fixed_floating_point_merged_mac`. [zhang_2018]

### the adder families and their slots

* `fp_add_space (every family) += slot round: rounding_space()` — the four adder families have no `round` slot, while the dot families carry `round: {increment_adder, compound_adder_select, injection, flagged_prefix}`. The z13 adder is built around an injection rounder, SPARC64's Path 2 rounds by an A+B and A+B+2 compound-adder selection with fill bits, and `sig_mul_then_round` has the same gap for the multiplier's two-level rounding selection. The rev-8 decision recorded in `fp_spaces.py` put rounding on the unit's `core.rounder` slot, so this line is a request to revisit that decision rather than an oversight; state the answer either way. [lichtenau_2016, naini_2001, quach_1991]
* `two_path.close_path_trigger += exp_diff_and_effective_sub_and_significand_range` — SPARC64 sends an exponent-difference-of-one subtraction to the close path only when the larger operand's mantissa is below 1.5, which forces the normalizing left shift and removes the close path's rounding stage. [naini_2001, seidel_2001 via `gaps/two_path.md`]
* `two_path.operand_order += speculative_preshift_then_swap` — Path 2 right-shifts both mantissas by 0 to 3 positions in stage 1, before the precedence is known, and swaps afterwards. [naini_2001]
* `single_path += choice denormal_exponent_correction: {parallel_difference_select, late_aligner_correction_stage}` — the exponent difference drives the aligner and is timing critical, so a denormal operand is handled either by computing D, D-1 and D+1 in parallel and selecting late, or by an extra aligner correction stage. The implied-bit correction stays off the critical path. `exponent_path.dual_direction_subtract` already computes d and -d; this is the third and fourth candidate. [schwarz_2003]
* `compound_flagged_prefix.outputs += sum_sum1_sum2` and `+= sum_sum1_inverted_sum` — the CELL SPE needs three outputs and the z13's H0, H1 and HC are a sum, a sum plus one and an inverted sum. [mueller_2005, lichtenau_2016]
* `compound_flagged_prefix.topology += carry_lookahead` and `+= ling`, `compound_flagged_prefix.implementation += conditional_sum` — the CELL SPE's compound adder is carry-lookahead, SNAP propagates its global carry by a modified Ling scheme, and the compound adder is built from the conditional-sum local sum logic that high-speed adders already carry, so it costs little more than a plain adder. [mueller_2005, quach_1991]
* `sparse_prefix_hybrid.log2_sparsity` reaches 3, and the FPMAC's critical tree generates one carry in sixteen, which is 4. Widen the range. [vangal_2006]
* `end_around_carry += recirculation: one_pass_group_identifier` — the 603e feeds the incrementer's propagate and the carry-lookahead's group identifier back to the carry-in in one pass, without a closed loop. [jessani_1996]
* `barrel_mux_tree += choice shift_amount_source: {computed_shift_count, sum_addressed_decode}` — the CELL SPE decodes the shift amount directly from the exponent sum, which removes the shift-amount carry-propagate adder from the critical path. A `select_encoding` value for a partial decode with partial-shift groups, and a `stage_radix` able to express a level that selects nine multiples of 16, are the 603e's two further lines. [mueller_2005, oh_2006, jessani_1996]
* `full_align += choice shifter_span_bits` separate from the maximum shift distance — a shifter's latency follows its maximum shifting distance while its area follows its span, which is why SNAP's shifters cost A106b at T53b delay. The 603e's aligner has a 53-bit input, a 136-bit output and a 161-bit range, so span and distance differ there too. [quach_1991, jessani_1998]
* `binary_decimal_conversion += choice reduction_hardware: {dedicated, reuse_binary_multiplier_compressor}` and `+= choice digits_per_iteration: Int[1..3:1]` — z13 compresses three new decimal digits with the three shifted terms of the sum and carry vectors that multiply the intermediate result by 1000, in the binary multiplier's own compressor. The rest of the algorithm is the z196 and zEC12 one. [lichtenau_2016]
* `two_rail_tree += choice check_placement: {code_disjoint_tree, in_place_cone_xor}` — SPARC64's FADD is 80 percent dynamic logic, and building it dual-rail domino lets each cone's true and complement outputs be XORed in place, with a non-zero XOR signalling an error and no code-disjoint tree built. The check holds only while the true and complement logic are independent, which in the adder means the final carry and its complement, so a `independent_dual_rail_cones: Bool` companion records the assumption. This is where `dual_rail_domino_code_check` lands. [naini_2001]
* `parity_prediction_adder`'s siblings cover an adder and a multiplier and not a shifter, and SPARC64's worked example is parity prediction through the alignment shifter. Either `parity_prediction_shifter` as a third sibling or a `datapath: {adder, multiplier, shifter}` choice on one family; the sibling set argues for the choice. [naini_2001]
* `goldschmidt.iter_add` assumes a carry-propagate adder, and SPARC64 adds the refinement constants 1 and 3/2 in unused slots of the multiplier's CSA rows. A `constant_injection: Bool` on the family, or admitting a CSA filler at that slot. [naini_2001]

## new families

Two families from six proposals. The other four proposals are absorbed or resolved into values above.

### denormalizing_result_shifter

Proposed by `schwarz_2003` (domain fp, closest `shift_round_convert`). The mechanism is the
post-normalization right shift of an underflowed intermediate result to an exponent equal to Emin,
together with the pipeline control that makes room for it. By the time underflow is detected the
normalizer is past, so the shift needs its own hardware and its own instruction ordering. The four
placements the paper names are a dedicated unit with a large right shifter fed out of order behind a
checkpoint ordering buffer, a feedback path to an early pipeline stage with a flush and non-pipelined
re-issue when another instruction occupies it, a stall that feeds the normalizer's output back to its
own input, and a small shifter at the rounder that shifts up to 4 bits per cycle. The last one takes
up to 13 cycles at double precision on the 1998 S/390 G5 FPU, against trapping to software.

* domain: fp (a family of `fp_spaces.py`, or the filler of a new `denormalize` slot on the rounder)
* execution_style: `variable_iteration` for the small-shifter placement, `feed_forward` for the dedicated unit; the family is `variable_iteration` because the shift count is data-dependent
* sources: schwarz_2003
* proposed_by: schwarz_2003 [survey]

```python
        Family(
            "denormalizing_result_shifter",
            papers=("schwarz_2003", "schwarz_2005", "gerwig_2004"),
            execution_style="variable_iteration",
            design_choices={
                "placement": Enum(("dedicated_unit", "pipeline_feedback_to_top",
                                   "normalizer_output_feedback",
                                   "small_shifter_at_rounder")),
                "shift_per_cycle_bits": Range(1, 64),
                "instruction_ordering": Enum(("out_of_order_checkpoint_buffer",
                                              "flush_and_reissue_nonpipelined",
                                              "stall_until_complete"))},
            components={"shifter": shifter_space()},
            mutations=("widen_shift_per_cycle", "move_denormalize_into_normalizer",
                       "trap_instead_of_denormalize"),
            doc="the underflowed intermediate result right-shifted to Emin before "
                "rounding, after the normalizer is past: a dedicated shifter fed out "
                "of order, a feedback path to an early stage, the normalizer's own "
                "output fed back, or a few bits per cycle at the rounder"),
```

The deciding question is whether the registry models the underflow path at all. `fp_spaces.py`'s rev-8
docstring puts the subnormal policy in the unit's daz and ftz options and leaves the adder only the
representation choice, so a human who answers no folds this proposal into
`classic_fma.denormal_operand_handling` and `single_path.subnormal_representation` and discards the
family. The paper's own framing argues the other way: it treats denormalization as a unit that a
design either builds or replaces with a trap, and it reports a cycle count for it.

### multipass_folded_pp_array

Proposed by `jessani_1998` (domain mul, closest `booth_recoded_parallel`). The partial-product array
is built for a fraction of the multiplier operand's bits and reused over several cycles. The
multiplier operand divides into parts, here 28 low bits and 25 high bits with b'000' concatenated to
the most significant bit so both passes carry 14 partial products. A pass's sum and carry re-enter the
reduction tree through inputs left free in its first level, the low result bits that later passes
cannot change latch out instead of feeding back, and a negative row's hot-one is saved for
re-injection at its full-array position in the next pass. Rows shared between passes need matching
per-bit dataflow, so extra CSAs and sign-extension multiplexors are added. The array falls from
5.1 mm2 to 2.5 mm2 and from 13 CSA groups to 7 at 0.5 um, and double-precision multiply throughput
falls from one to two cycles per instruction.

* domain: mul (integer multipliers)
* execution_style: `fixed_iteration`
* sources: jessani_1998, jessani_1996
* proposed_by: jessani_1998 [incremental]

```python
        Family(
            "multipass_folded_pp_array",
            papers=("jessani_1998", "jessani_1996"),
            execution_style="fixed_iteration",
            design_choices={
                "passes": Range(2, 4),
                "pp_rows_per_pass": Range(1, 32),
                "feedback_target": Enum(("free_csa_tree_inputs",
                                         "separate_csa_level")),
                "deferred_hot_one": Bool(),
                "shared_row_sign_extension_mux": Bool()},
            components={"reduction": adder_tree_space()},
            mutations=("unfold_to_single_pass", "raise_pp_rows_per_pass",
                       "latch_low_bits_out"),
            doc="a partial-product array built for a fraction of the multiplier "
                "operand and reused over several cycles: each pass's sum and carry "
                "re-enter the tree through free first-level inputs, the low result "
                "bits latch out, and a negative row's hot-one is deferred to its "
                "full-array position in the next pass"),
```

The alternative is `booth_recoded_parallel += choice passes: Int[1..4:1]`, which the prefer-values
rule favours. Against it: the family is `feed_forward` and this mechanism is `fixed_iteration`, the
feedback path and the latched low bits are structure rather than a parameter, and the seven named
places where the saving costs control logic and multiplexing belong to a card of its own. The
combinational VecDotAcc and single-cycle ALU contracts exclude it either way, in the same manner as
`UNSUPPORTED_DOT_CHOICES` already excludes `classic_fma.pipeline_depth`, so this entry is a
registration for the sequential scope rather than for the current one.

## rejected

* `pipeline_depth` and `pipeline_style` on the dot families — pipeline depth (1 to 8 in `galal_2011`, 3 to 16 in `galal_2013`) and the retiming style (automatic, guided, replicated half-pumping) move the Pareto frontier in both studies, and half of the latency-frontier designs carry replicated multi-cycle multipliers. `UNSUPPORTED_DOT_CHOICES` already excludes `classic_fma.pipeline_depth`, `bridge_fma.bridge_extra_stages` and `multi_term_fused_dot.pipeline_depth` from the combinational contract for the stated reason that pipeline registers require a sequential latency contract. The same reason excludes these. Re-register them together when the sequential contract lands. [galal_2011, galal_2013, jessani_1998, oh_2006]
* `layout_informed_placement` — relative X and Y coordinates planted in cell instance names and handed to the placer change which tree topology wins, notably OS1 at quad precision. This is a physical-design flow property rather than a netlist structure, and the library's realization check is of the generated module. [galal_2013]
* `clock_gating_by_instruction` and the CELL SPE's opcode- and data-dependent gating of the multiplier, incrementer and compound adder — power management of an otherwise unchanged netlist. `low_power_gated` isolates its inactive partitions at their operands, which is a structural choice and stays; gating the clock of the unused path is not. Record the distinction in `arch/fp/low_power_gated.md` rather than in the space. [galal_2013, oh_2006, mueller_2005]
* `ieee_compatible_maf_contract` — `quach_1991` defines an IEEE-compatible multiply-add-fused as one that delivers the result of a sequential FMPY then FADD, and calls the RS/6000 single-rounded unit not IEEE compatible on that definition. IEEE 754-2008 settled the opposite way and defines fusedMultiplyAdd as one rounding, which is the contract `arch/dot/classic_fma.md` states and the engine's conformance gate checks. A choice would register a definition the standard retired. Keep the sentence in the `classic_fma` card as the historical reading. [quach_1991]
* `carry_point_bit` and `candidate_sum_count` on the rounding slot — the rounding position is bit 51 for a multiplier, a function of the alignment shift distance for an aligned addend, and bit 51 again for both SNAP paths, and the selection needs five precomputed outcomes S + C + (0,4) for SNAP against two for the multiplier. `fp_spaces.rounding_space`'s docstring states that the rounder rounds a normalized value, so the rounding position is one; the candidate count follows from the family (`compound_adder_select` computes two, `flagged_prefix` three). Both are consequences of the rounder's contract rather than free axes. [quach_1991]
* `inter_level_alignment_side` on the reduction-tree slot fillers — which side carries the alignment shift between reduction levels, here the diagonally routed multiplicand rather than the CSA sum and carry outputs. One paper, one sentence, and it describes a routing convention of a specific array. [naini_2001]

absorbed 4, new values 51, new families 2 (from 6 proposals), rejected 6
