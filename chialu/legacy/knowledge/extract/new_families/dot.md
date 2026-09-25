# new-family review: dot

Source bundle: `run/extract/reduce/newfam_dot.md` (18 proposals). Registry read:
`chialu/spaces/fma_dot_spaces.py` plus the family lists of `fp_spaces.py`,
`mul_spaces.py`, `dsp_posit_spaces.py`, `approx_spaces.py`, `redundant_spaces.py`,
`adder_spaces.py` and `shift_simd_spaces.py`. Notes consulted for the thin proposals and
for mapping checks: `geva_2022`, `lee_1989`, `lindholm_2008`, `irwin_owens_1987`,
`wijeratne_2007`, `muller_2018__s08`, `camus2019`, `langhammer_2015b`, `lutz_2019`,
`tremblay_1996`, `zimmermann1999`, `agrawal_2021`, `markidis_2018`, `sun_2019`,
`henry_2019`, `sohn_2014`, `beaumont_smith1999`.

Handle notes for the human:
* `lee_1989` is a mismatch. The note file records `status: mismatch` with the actual
  citation D. A. Gudovskiy and L. Rigazio, "ShiftCNN: Generalized Low-Precision
  Architecture for Inference of Convolutional Neural Networks", arXiv:1706.02393, 2017,
  while `shift_simd_spaces.py` cites `lee_1989` for R. B. Lee's Precision Architecture
  (`funnel`, `masked_merged`). The handle is kept as given below; the ShiftCNN lines need
  a re-keyed handle before they enter `approx_spaces.py`.
* `beaumont_smith1999` (bundle, `fp_spaces.py`) and `beaumont_smith1999`
  (`adder_spaces.py`, `new_families/fp.md`) are the same ARITH-14 paper; both note files
  exist. The bundle spelling is kept below.
* `muller_2018#s08` is kept as given in prose; a `papers=` tuple uses the base key
  `muller_2018`, which is the `fp_spaces.py` style.
* `sohn_2014`, `lutz_2019`, `henry_2019`, `markidis_2018`, `sun_2019` and `agrawal_2021`
  are already family papers in `fma_dot_spaces.py`. `zimmermann1999` is cited by
  `adder_spaces.end_around_carry` and `redundant_spaces.rns_channel_arithmetic`,
  `camus2019` by `approx_spaces.approximate_mac_nn`, `langhammer_2015b` by
  `dsp_posit_spaces.hard_fp_dsp`, `irwin_owens_1987` by
  `redundant_spaces.online_pipeline_composition`. `lindholm_2008`, `wijeratne_2007`,
  `geva_2022` and `tremblay_1996` are cited by no space file; `tremblay_1996` also
  appears in `new_families/mul.md` for the VIS partitioned multiplier.
* Four lines below coincide with lines already in `new_families/fp.md`
  (`multi_term_fused_dot.term_source`, the pairwise alignment value, `lza.input_count`,
  `fp_add_space.dependent_result_forwarding`). Each is applied once; the line here names
  the fp.md line it merges into.

## absorbed

* low_precision_expansion_dot -> bf16_fma_datapath.multi_word_composition=True — henry_2019 is already a family paper and its note binds `multi_word_composition: true` to the decomposition (pp.70-73): each fp32 operand becomes up to three bf16 components, the cross-products are binned by significance and the bins are summed smallest to largest; the component count (1..3), the retained products (1/3/6/9) and the fp64 collection are software schedule knobs on that Bool, so no choice is added [henry_2019].
* residual_refined_gemm -> bf16_fma_datapath.multi_word_composition=True (fp16 instance on tensor_core_mixed_precision_mac, which already cites markidis_2018) — an fp32 operand matrix split into its fp16 rounding plus an fp16 residual and summed over 2 (A only) or 4 (A and B) Tensor Core GEMMs is the henry_2019 multiword composition run as software over an unchanged MAC (35x error decrease at 5x cost, N = 4096); `tensor_core_mixed_precision_mac += choice multi_word_composition: Bool` mirrors it if the fp16 binding matters [markidis_2018].
* restricted_coefficient_matrix_vector -> redundant_spaces.online_pipeline_composition.scheduling=digit_slice_overlapped — irwin_owens_1987 is already the family's paper; the m x n mesh of Pos/Neg/Del digit-pipelined primitives with digit-skewed vector inputs is one composition of online nodes (first digit after n+1 cycles, completion at n+m+p), and the coefficient set {-1, 0, 1} removes the multiplier rather than adding structure; `online_pipeline_composition += choice topology: {chain, nearest_neighbor_mesh}` is the optional refinement [irwin_owens_1987].

## new values

Grouped by host family; the source proposal follows each group.

### multi_term_fused_dot  (from fused_three_input_add and fused_three_term_adder, merged)

* `multi_term_fused_dot += choice term_source: {products, fp_operands}` — already proposed in `new_families/fp.md` from tenca_2009/tao_2013; the fused three-operand adder without a multiplier is the same value: three normalized operands, one reduction, one rounding under all five IEEE modes, at about one third of an FMA's area (textbook) and 15-20% less area and power and 35% less latency than a discrete three-term adder built from delay-optimized FP adders (45 nm, fp32 and fp64). Apply once with all four handles [sohn_2014, muller_2018#s08]
* `multi_term_fused_dot.alignment_strategy += parallel_pairwise_difference` — six parallel exponent-difference computations whose partial results drive the shifters, instead of locating the largest exponent first and then shifting; the same value as `pairwise_difference_reuse` in fp.md (tenca_2009), so one name is kept [sohn_2014]
* `multi_term_fused_dot += choice sign_handling: {post_add_complement, dual_reduction_positive_pair_select}` — dual 3:2 reduction trees form the opposite-sign alternatives and a significand comparison selects the positive pair, so no complement follows the addition [sohn_2014]
* `multi_term_fused_dot += choice normalize_before_add: Bool` — the three-input LZA drives normalization before a reduced-width prefix addition (the `reduced_latency_fma.normalize_before_add` axis on the multi-term family) [sohn_2014]
* `multi_term_fused_dot += choice pipeline_depth: Int[1..3:1]` — unpipelined, or exponent/alignment, invert/normalize and add/round stages (2.7x throughput, one result per cycle, latches paid in area and latency); thin, one paper [sohn_2014]
* The proposal's `leading_zero_anticipation=direct_three_input` is the `lza` slot with fp.md's `lza.input_count=3` (concurrent 1-bit correction), and `rounding_structure=compound_sum_sum1` is the `round` slot bound to `compound_adder_select`; neither needs a choice here.

### streaming_accurate_accumulator  (from in_order_fp_vector_reduction and unnormalised_feedback_fp_accumulator)

* `streaming_accurate_accumulator.approach += ordered_fp_loop_lookahead` — a floating-point adder stays on the loop-carried path and the recurrence is one cycle: a setup cycle analyzes the first two operands' signs and exponents, each iteration produces the exponent early enough to analyze the running sum against the next operand while its significand completes, and a forwarding cycle ends the ordered reduction (n + 2 cycles for n elements; the Arm SVE ordered reduction). The clock skew inside the single-cycle loop is circuit detail for the doc rather than a choice; `in_loop_normalization=True` [lutz_2019]
* `streaming_accurate_accumulator.approach += unnormalised_feedback_with_lza_distance` — the second pipeline stage feeds back the correctly rounded but possibly unnormalised significand with its exponent, sign and LZA normalisation distance; bypass multiplexers let the next accumulation skip normalisation, skip alignment after a partial left shift, or normalise the feedback while the new addend aligns (2-cycle accumulate against the 3-cycle add, four added multiplexers, 0.5 um). `new_families/fp.md` proposes the same mechanism as `fp_add_space (every family) += choice dependent_result_forwarding: rounded_unnormalized_feedback` under the spelling `beaumont_smith1999`; a human applies one of the two lines and the other is then absorbed [beaumont_smith1999]
* Both values keep an IEEE adder on the loop-carried path, which the family doc treats as the case to avoid. A merged family `ordered_fp_loop_accumulator` from the two proposals plus `multipath_fma.accumulate_forwarding_loop` (srinivasan_2013) is the alternative; the prefer-new-values rule decides for the values.

### mixed_precision_cascade_fma  (from compensated_residual_register)

* `mixed_precision_cascade_fma += choice error_term_normalization: {dedicated, on_demand_copy}` — how a two-term expansion (`two_term_expansion_output=True`) delivers its low part: a dedicated 2Sum operator with its own error-term LZC and shifter (50% larger than a standard adder at identical delay, FPGA), or a p-bit residual register that captures the low product or sum bits already formed for the sticky and a separate instruction that normalizes them through the adder's LZC/shifter, accounting for whether rounding chose the truncated significand or its successor (2Sum/2Mult in 2 instructions, under 10% area over a binary32 GPU unit) [muller_2018#s08]
* `mixed_precision_cascade_fma += choice error_term_ops: {addition, multiplication, both}` — which operations fill the residual register [muller_2018#s08]
* The proposal's `residual_width: Int[1..p:1]` is the significand width p and is skipped where it binds to `elem_bits`. `streaming_accurate_accumulator.approach=compensated_two_sum` (mutation `add_compensation_term`) consumes the error term, and `classic_fma` is the alternative home if the expansion concept is not to stay tied to the mixed-precision family.

### integer_mac  (from divide_and_conquer_precision_scalable_mac and simd_sum_absolute_differences)

* `integer_mac += choice accumulation_mode: {sum_apart, sum_together}` — Sum Apart bypasses the combination logic and keeps the narrow products in separate accumulators; Sum Together reuses the combination adders to accumulate one result (2D D&C ST at two levels: 68% energy below data gating; 2D D&C SA: 14.5x throughput at symmetric 2b for up to 4.4x area, 28 nm). The same axis exists as the sum_apart/sum_together values of `approximate_mac_nn.precision_scaling`, and the camus2019 note lists it as a new choice on `mul.twin_precision_subword` [camus2019]
* `integer_mac += choice scalable_dimensions: {one, two}` — one operand scales (2b x 8b submultipliers; the weight-only case saves 15% energy at 5% 8b operations) or both operands scale (2b x 2b submultipliers) [camus2019]
* `integer_mac += choice scalability_levels: Int[1..2:1]` — direct support down to 4b, or down to 2b [camus2019]
* The D&C composition itself (identical submultipliers combined through configurable shift-add logic) is the existing `integer_mac.array_style=bit_serial_composable`, whose doc names Bit Fusion (sharma_2018: 2-bit bricks fused spatially). That value name labels a spatial composition as serial; a rename to `composable_submultiplier` is for the human. The proposal's `submultiplier_shape` follows from `scalable_dimensions` and is not added.
* `integer_mac += choice element_op: {product, absolute_difference}` — pdist forms |a - b| on eight 8-bit lane pairs and accumulates their sum (3-cycle latency, one per cycle; 5.5x on 16 x 16 motion estimation, 32 instructions per block); with `absolute_difference` the `mul` slot is replaced by a per-lane subtract with conditional negate, for which `adder_spaces.compound_flagged_prefix` (its doc yields the absolute difference) is the filler; `array_style=simd_packed_dot` [tremblay_1996]

### fp8_training_datapath  (from fused_multiply_multiply_accumulate and round_off_residual_weight_update)

* `fp8_training_datapath += choice op_shape: {scalar_fma, dot2_accumulate}` — the hfp8 FMMA: two products and an addend aligned to the larger product's exponent, the smaller product shifted by the product-exponent difference, the fp16 result through the adder shared with the fp16 path (2x the fp16-mode performance at equal power, 7 nm); mirrors `bf16_fma_datapath.op_shape`. The rounding contract is unstated, so `multi_term_fused_dot` does not apply [agrawal_2021]
* `fp8_training_datapath += choice unified_internal_format: Bool` — both hfp8 formats convert to one fp9 internal container (5-bit exponent, 3-bit fraction per the note) before the shared datapath [agrawal_2021]
* `fp8_training_datapath += choice weight_update_error_feedback: Bool` — the FP8 weight update subtracts the gradient and the previous round-off residual, requantizes to FP8 and stores the new residual in FP16, the deterministic counterpart of `stochastic_rounding` for the update (32-38% end-to-end training time reduction on ResNet50 together with the distribution change); the reduce-scatter partition and the FP8 all-gather payload are communication choices and are not registered. Optimizer-flavoured; reject instead if the registry excludes update-side mechanisms [sun_2019]

### bridge_fma  (from nonfused_fp_mad)

* `bridge_fma += choice cascade_product_rounding: {rne, truncate}` — under `composition_style=cascade_mul_then_add` the product is rounded before the add; the Tesla SP multiply-add truncates it and rounds the add to nearest even (1.5 GHz, 90 nm, 36 Gflops per SM). The sign-preserved flush of source denormals and underflowed results is `fp_spaces.subnormal_space.flush_to_zero_mode` [lindholm_2008]

### approximate_mac_nn  (approx domain; from precomputed_codebook_convolution)

* `approximate_mac_nn.multiplier_source += power_of_two_codebook` — each weight is a sum of N entries from signed power-of-two codebooks addressed by B-bit indices; a ShiftALU forms all P = M + 2(N - 1) shifted and sign-flipped copies of each input once through a pass-through path and cascaded right shifts, a shift-register array stores (P - 1) x C-bar terms, the weight indices select a stored term or zero through multiplexers, and an adder tree accumulates the N selected terms plus bias (Zynq XA7Z030 at 200 MHz: 4016 LUTs, 0 DSPs, 102 mW; 2.5x fewer resources and 4x less dynamic power than an 8-bit fixed-point pipeline; the adder tree takes 75% of the power). `alphabet_set_shared` is the nearest existing value; whether it subsumes a power-of-two-only codebook is for a human with sarwar2018 in hand [lee_1989]
* `approximate_mac_nn += choice codebook_terms_per_weight: Int[1..8:1]` — N; evaluated at 1, 2 and 3 (N = 2, B = 4 stays within 1% top-1 on SqueezeNet/GoogleNet/ResNet-18), and N = 8 with B = 3 reproduces 8-bit fixed point [lee_1989]
* `approximate_mac_nn += choice codebook_index_bits: Int[3..4:1]` — B [lee_1989]
* C-bar (concurrent input channels, evaluated at 128) is a throughput parameter rather than a choice.

### rns_channel_arithmetic  (redundant domain; from modulo_multiplier_adder)

* `rns_channel_arithmetic += choice fused_addend: {none, injected_before_final_adder_dual_output}` — the IDEA multiply-add unit injects the addend into the modulo (2^n + 1) multiplier's carry-save product before final propagation; two parallel final adders return the modulo (2^n + 1) product and the modulo 2^n sum, and the product adder's inverted carry-out corrects both paths (8/16/32-bit: 15/13/9% area and 18/10/5% delay over the bare modulo multiplier, 0.25 um; four serial carry propagations reduced to one). zimmermann1999 is already a family paper; `fused_csa` is the binary analogue (the addend as one more carry-save row) and the `modular_adder` slot stays `end_around_carry` [zimmermann1999]

### hard_fp_dsp  (dsp domain; from recursive_fp_dsp_reduction)

* `hard_fp_dsp += choice chain_topology: {linear_accumulate, recursive_tree}` — adjacent blocks take multiplier or adder roles and pass FP results over dedicated inter-block connections; the multiplier contributes 2 or 3 cycles, the first adder level 1 and each later level 3, so a 256-element reduction takes 24 cycles (3 log2 n, 20 nm). `accumulate_chain=True` is the linear case [langhammer_2015b]
* `hard_fp_dsp += choice chain_routing: {dedicated_chain, balanced_soft_routing}` — balanced logic-register depths absorb longer physical routes [langhammer_2015b]
* `dsp_posit_spaces.py` rules FPGA mapping out of scope. The dedicated chain is block architecture, as `dsp48_style_slice.cascade_paths` is, so the values are in scope; the human confirms.

## new families

None. Each proposal's mechanism is a new value on the structure of an existing family
(an element operation, a loop policy, a chain topology, an error-term output, a
composition mode), so no `Architecture(...)` snippet is proposed. Two groups of value
lines are the strongest cases for promotion, and the prefer-new-values rule decides for
the values:
* `multi_operand_fp_add` from fused_three_input_add and fused_three_term_adder, with
  tenca_2009 and tao_2013 from the fp bundle: four handles, one textbook block (the
  fp.md review already flagged this alternative under `term_source`).
* `ordered_fp_loop_accumulator` from in_order_fp_vector_reduction and
  unnormalised_feedback_fp_accumulator: two incremental papers, no textbook or thesis
  block.

## rejected

* fp_systolic_mac_array — too thin to define: the source reports 6 FP16 TFLOPS, ring and feed bandwidths and the presence of systolic MAC arrays with activation blocks, and no accumulator format, dot width, dataflow, alignment or rounding (the note's own open questions); with a fuller disclosure it becomes an array-organization value beside `integer_mac.array_style=systolic_array` or on `tensor_core_mixed_precision_mac`, and the sigmoid/softmax blocks belong to `sfu_spaces` [geva_2022].
* two_frequency_domino_execution_core — a clocking and circuit technique (locally doubled pulsed clock, four gates and at most two domino stages per phase, self-timed pulse-width control, 16 post-fabrication stretch settings) spanning ALU, AGU, register file, bypass network and rotator, with no arithmetic topology of its own; the ALU's sparse radix-2 tree with conditional-sum blocks is the note's instantiation of `adder_spaces.sparse_prefix_hybrid`, and the proposal's domain is commercial_units rather than dot [wijeratne_2007].

absorbed 3, new values 13, new families 0 (from 0 proposals), rejected 2
