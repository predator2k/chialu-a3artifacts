---
handle: manolopoulos_2016
citation: K. Manolopoulos, D. Reisis, V. A. Chouliaras, "An Efficient Multiple Precision Floating-Point Multiply-Add Fused Unit", Microelectronics Journal, vol. 49, 2016
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_DOT_ACC]
formats: [fp32, fp64, fp128]
authority: incremental
pages_read: 10-18 / 9
---

## summary
The paper presents a reconfigurable multiple precision floating-point Multiply-Add Fused (MAF) unit that executes one quadruple precision MAF instruction, or two double precision instructions, or four single precision instructions in parallel, and in each mode also stand-alone multiply or add instructions (p.10, p.12). The add stage is split into a Close and a Far path, the multiplier's carry-save products are added at the beginning of the second stage to shrink the alignment shifters, and the Far path normalizes before a final dual adder that computes sum and sum+1 for rounding (p.12, p.14). Post-layout the unit occupies 672,046 um2 and reaches 293.5 MHz at 381 mW, a 23% area and 14% latency increase over a typical quadruple precision MAF implemented in the same technology (p.16, p.17).

## families
### multi_precision_simd_fma  (role: proposes)
mechanism: One dual-path MAF datapath is built for quadruple precision and augmented so that the same components serve two double precision or four single precision instructions in SIMD fashion. Three 128-bit registers hold one quadruple, two double or four single precision operands. One 113x113 array multiplier computes 2x53-bit or 4x24-bit products by subword parallel multiplication with the off-diagonal partial-product regions Z forced to zero. Exponent processing is replicated as one quadruple, one double and two single precision units. The full-width alignment and normalization shifters are built from smaller sub-shifters that combine in the wider modes. The pipeline has three stages and a throughput of one result per cycle.
choices:
  lane_split: 1x128 / 2x64 / 4x32 [outside domain]   # p.12, p.15
new_choices:
  product_assimilation_point: start_of_add_stage — the multiplier's two carry-save vectors are added at the beginning of the second stage, before alignment, which reduces the size of the alignment shifters and of the modules after the addition   # p.12, p.13
  shared_alignment_shifter: true — one Far-path shifter aligns either A x B or C, chosen by the sign of the exponent difference, instead of one shifter per operand   # p.14
  subshifter_decomposition: per_lane_subshifters_combined_in_wider_modes — the 115-bit aligner is two shifters of 60 and 55 bits, the 111-bit alignment is two shifters of 65 and 56 bits, and the 118-bit normalization shifter is two 30-bit and two 29-bit shifters; pairs combine in DP mode and each works alone in SP mode   # p.15
slots:
  align: full_align [Far path, A x B right-shifted at most 115 bits, C at most 226 bits, realized as shifters of 115 and 111 bits]   # p.14
  lza: lza [the method of Schmookler-Nowka, run in parallel with the Close-path addition, 2-bit uncertainty resolved in the third stage]   # p.14
  norm_shifter: UNKNOWN [118-bit Close-path normalization shifter composed of two 30-bit and two 29-bit shifters; the shifter family is not stated]   # p.14, p.15
  round: compound_adder_select [two dual adders of 58 and 53 bits compute sum and sum+1 and the rounding module selects the output]   # p.14
  cpa: UNKNOWN [58-, 57-, 56- and 55-bit adders in stage two and 58-/53-bit dual adders in stage three; the carry structure is not stated]   # p.14
  multiplier: carry_save_array [113x113 array multiplier producing carry-save results; Booth encoding rejected for control complexity and subword carry suppression]   # p.13, p.15
parameters: 113x113 array multiplier; significands extended to ['1', R(111:0)]; three 128-bit operand registers; three-stage pipeline, one result per cycle; Close path aligns C by at most 1-bit right or 2-bit left with a 3-bit shifter to 116 bits, then a 117-bit 3:2 CSA; second-stage adders two dual adders of 58 and 57 bits plus adders of 56 and 55 bits; Far path 2-bit normalization shifter in stage two; third-stage Close 118-bit normalization shifter, Far dual adders of 58 and 53 bits over the upper 113 bits; DP maximum alignment shift 55 and 106 bits with at most two parallel shifts, SP 26 and 48 bits with four alignment shifts.   # p.13, p.14, p.15
results:
| metric | value | unit | technology / device | baseline | condition | page |
| --- | --- | --- | --- | --- | --- | --- |
| area | 672,046 | um2 | Faraday/UMC 65 um LL-RVT (abstract: 65 nm), 2016 | absolute | post-layout, WCCOM VCC=1.08 V, 125C, activity 0.5 | p.16 |
| AND2-Eq. gates | 420,028 | gates | Faraday/UMC 65 um LL-RVT, 2016 | absolute | post-layout | p.16 |
| power | 381 | mW | Faraday/UMC 65 um LL-RVT, 2016 | absolute | at design max post-route frequency, activity 0.5 | p.16 |
| Fmax | 293.5 | MHz | Faraday/UMC 65 um LL-RVT, 2016 | absolute | post-layout, 500 MHz synthesis constraint | p.16 |
| energy per operation | 1295.4 | pJ/op | Faraday/UMC 65 um LL-RVT, 2016 | absolute | power x period | p.16 |
| area increase | 23 | % | Faraday/UMC 65 um LL-RVT, 2016 | typical QP MAF | post-layout | p.17 |
| latency increase | 14 | % | Faraday/UMC 65 um LL-RVT, 2016 | typical QP MAF | post-layout | p.17 |
| area | approximately 4x | ratio | Faraday/UMC 65 um LL-RVT, 2016 | dual-mode dual-path MAF | post-layout | p.17 |
| area (multi-block baseline) | 812,952 | um2 | Faraday/UMC 65 um LL-RVT, 2016 | multi-block MAF (typical QP + two dual-mode dual-path units) | post-layout | p.16 |
| AND2-Eq. gates (multi-block baseline) | 508,095 | gates | Faraday/UMC 65 um LL-RVT, 2016 | multi-block MAF | post-layout | p.16 |
| power (multi-block baseline) | 320 | mW | Faraday/UMC 65 um LL-RVT, 2016 | multi-block MAF | post-layout | p.16 |
| Fmax (multi-block baseline) | 326 | MHz | Faraday/UMC 65 um LL-RVT, 2016 | multi-block MAF | post-layout | p.16 |
| energy per operation (multi-block baseline) | 979.2 | pJ/op | Faraday/UMC 65 um LL-RVT, 2016 | multi-block MAF | power x period | p.16 |
errors_and_checks: The third stage supports all rounding modes described by the IEEE standard, and rounding plus post-normalization resolve the LZA's 2-bit uncertainty (p.14). The design was implemented in VHDL and its functionality verified through simulation analysis (p.15). No ulp bound, error rate, fault model or detection coverage is reported.
conditions: The design targets applications that demand high throughput execution of multiple instructions across all floating-point precision modes under area constraints (p.17). The multi-block MAF matches it in functionality and throughput and requires less energy per operation, while the proposed design prevails in area (p.17). Synthesis used Cadence RTL Compiler V10.10 at a 500 MHz constraint with 1000 ps input and output delays, 100 ps clock uncertainty, retiming, auto-ungrouping, operand isolation and clock gating, driven by 1000 RTL testbench vectors; power came from Cadence Encounter with input, flop and clock-gate activity of 0.5, which the paper notes is very high (p.15, p.16).
evidence: Abstract; Section 4 and Figs. 3-5; Section 4.2; Section 5 with Tables 1 and 3; the comparison discussion on p.17.

### multipath_fma  (role: instantiates)
mechanism: The add stage divides into a Close path and a Far path, and only one is activated by the exponent difference. The Close path is activated for effective subtraction with exponent difference diff = -1, 0, 1, and for effective subtraction with diff = -2 together with multiplication overflow; the Far path handles the remaining cases. The Close path aligns C with a 3-bit shifter, inverts it, sums it with the multiplier result in a 117-bit 3:2 CSA whose empty slot carries the 2's complement +1, and normalizes and rounds in the third stage. The Far path performs the full-length alignment with one shared shifter, normalizes in the second stage, and adds and rounds in the third. Both paths extend into the third stage.
choices:
  path_count: 2   # p.12, p.13
  path_select_criterion: exponent_difference   # p.13
new_choices:
  normalization_placement_per_path: far_before_add, close_after_add — the Far path normalizes in the second stage before the final addition while the Close path normalizes and rounds in the third stage, so the family's single normalize-before-add flag cannot express the design   # p.12, p.14
  path_span_in_pipeline: both_paths_extend_to_third_stage — in contrast to the dual-path approach of Bruguera-Lang, which splits only the second stage   # p.12, p.14
slots:
  align: full_align [Far path, one shifter shared by A x B and C]   # p.14
  lza: lza [Close path, run in parallel with the addition]   # p.14
  norm_shifter: UNKNOWN [2-bit normalization shifter in the Far path's second stage, 118-bit normalization shifter in the Close path's third stage]   # p.14
  round: compound_adder_select [dual adders produce sum and sum+1, and the dual adders of the second stage also precompute the complement needed when the Close-path result is negative]   # p.14
  multiplier: carry_save_array   # p.13
parameters: Close path aligned operand 116 bits in quadruple mode, 117-bit 3:2 CSA, sign detection unit after the addition; Far path shifts A x B by at most 115 bits and C by at most 226 bits, implemented as shifters of 115 and 111 bits; three-stage pipeline.   # p.13, p.14
results:
| metric | value | unit | technology / device | baseline | condition | page |
| --- | --- | --- | --- | --- | --- | --- |
| area | 149,343 | um2 | Faraday/UMC 65 um LL-RVT (abstract: 65 nm), 2016 | dual-mode dual-path MAF of Bruguera-Lang, one DP or two SP instructions | post-layout | p.16 |
| AND2-Eq. gates | 93,339 | gates | Faraday/UMC 65 um LL-RVT, 2016 | dual-mode dual-path MAF | post-layout | p.16 |
| power | 268.9 | mW | Faraday/UMC 65 um LL-RVT, 2016 | dual-mode dual-path MAF | post-layout, activity 0.5 | p.16 |
| Fmax | 427 | MHz | Faraday/UMC 65 um LL-RVT, 2016 | dual-mode dual-path MAF | post-layout | p.16 |
| energy per operation | 618.47 | pJ/op | Faraday/UMC 65 um LL-RVT, 2016 | dual-mode dual-path MAF | power x period | p.16 |
errors_and_checks: none
conditions: Full-length alignment and full-length normalization are mutually exclusive, so each path carries only one full-length shifter, which the paper gives as the source of the reduced critical delay and area (p.12). The compared design of Bruguera-Lang requires two full-length alignment shifters, and the design of Qi et al. splits the Far path into two sub-paths, which cuts latency further but needs four stages and additional Far-path hardware (p.17).
evidence: Section 4 items (1) and (2); Section 4.1 second and third stage; Fig. 4; the comparison on p.17; Table 1.

### reduced_latency_fma  (role: instantiates)
mechanism: The final addition is combined with rounding by a dual adder in the third stage, and normalization is anticipated before that addition on the Far path. The Far path uses a 2-bit normalization shifter in the second stage to correct a possible overflow or an unnormalized result, and in the third stage the upper 113 bits drive two dual adders of 58 and 53 bits that produce sum and sum+1 while the remaining bits, the sticky bit and the rounding bit drive the rounding module, which selects the correct output. Stand-alone addition bypasses the first stage and uses a duplicated exponent processing module at the beginning of the second stage.
choices:
  rounding_position: fused_with_cpa_dual_sum   # p.12, p.14
  normalize_before_add: true   # p.12, p.14  (Far path; the Close path normalizes in the third stage)
  add_skip_for_pure_addition: true   # p.12, p.13  (the multiplier and first stage are bypassed for a stand-alone addition)
new_choices: none
slots:
  align: full_align   # p.14
  lza: lza   # p.14
  norm_shifter: UNKNOWN [2-bit Far-path shifter in stage two, 118-bit Close-path shifter in stage three]   # p.14
  round: compound_adder_select   # p.14
  cpa: UNKNOWN [dual adders of 58 and 53 bits combined over the upper 113 bits]   # p.14
parameters: dual adders of 58 and 53 bits over the upper 113 bits; 2-bit Far-path normalization shifter; all IEEE rounding modes in the third stage.   # p.14
results: none reported for this mechanism in isolation
errors_and_checks: The LZA's 2-bit uncertainty is resolved by rounding and post-normalization in the third stage (p.14).
conditions: The scheme was first used in floating-point addition to exploit the mutual exclusion of full-length alignment and normalization shifts, so that only one full-length shifter lies on the critical path (p.12).
evidence: Section 4 items (1) and (2); Section 4.1 second and third stage.

### twin_precision_subword  (role: instantiates)
mechanism: One array multiplier serves all three precision modes. In quadruple precision it operates as a typical 113x113 bit array multiplier producing carry-save results. In double precision the four mantissas extended with the hidden 1 enter the same array and the products A1 x B1 and A2 x B2 are computed in two 53x53 submatrices P1 and P2 by subword parallel multiplication, with the partial-product bits in the regions labelled Z set to zero so the results are not altered. The same technique gives four parallel single precision multiplications. An array multiplier was chosen over Booth encoding because Booth encoding needs more complex control for three precision formats and requires subword carry bits to be detected and suppressed in the reduction tree and the CPA.
choices: none of the family's declared choices are settled by the document
new_choices:
  precision_mode_count: 3 — the same partial-product matrix is gated into one 113x113, two 53x53 or four 24x24 products   # p.13, p.15
  zeroed_cross_region: true — the partial-product bits of the off-diagonal regions Z are forced to zero in the narrow modes   # p.15
slots: none — the products leave the multiplier in carry-save form and are assimilated by the second-stage adders   # p.13, p.14
parameters: 113x113 bits in quadruple mode, 2x53 bits in double mode, 4x24 bits in single mode.   # p.13, p.15
results:
| metric | value | unit | technology / device | baseline | condition | page |
| --- | --- | --- | --- | --- | --- | --- |
| area | 389,882 | um2 | Faraday/UMC 65 um LL-RVT (abstract: 65 nm), 2016 | absolute | post-layout, proposed quad multiplier | p.16 |
| AND2-Eq. gates | 243,676 | gates | Faraday/UMC 65 um LL-RVT, 2016 | absolute | post-layout | p.16 |
| Fmax | 341 | MHz | Faraday/UMC 65 um LL-RVT, 2016 | absolute | post-layout | p.16 |
errors_and_checks: none
conditions: The array multiplier needs a larger compression tree than a Booth multiplier, which the paper accepts as the price of supporting three precision formats with one array (p.15).
evidence: Section 4.1 first stage; Section 4.2 Multiplication with Fig. 5; Table 2.

### classic_fma  (role: compares)
mechanism: The conventional double precision MAF of Section 3 runs three serial stages. The first stage multiplies the 53-bit significands of A and B while the third operand C is inverted and aligned in parallel, positioned 56 bits left of the product, with diff = expC - (expA + expB - 1023) and shift amount sh = 56 - diff = expA + expB - expC - 967, the alignment performed as a right shift by a 161-bit aligner. The second stage adds the 106-bit product and the 161-bit aligned operand with a 106-bit 3:2 CSA and a 161-bit adder, while an LZA over the lower 106 bits of the CSA computes the normalization shift amount, and the adder result is complemented if required. The third stage normalizes, rounds and post-normalizes if required, and prepares the sign and exponent.
choices: none of the family's declared choices are settled by the document
new_choices: none
slots:
  align: full_align [161-bit aligner, C placed 56 bits left of the product]   # p.11
  lza: lza [over the lower 106 bits of the 3:2 CSA]   # p.11
  cpa: UNKNOWN [161-bit adder]   # p.11
  round: UNKNOWN [rounding followed by post-normalization if required]   # p.11
  multiplier: UNKNOWN [53-bit significand multiplication; no structure stated]   # p.11
parameters: 1-bit sign, 11-bit biased exponent and 53-bit fraction for double precision; 106-bit product; 161-bit aligner and 161-bit adder; 106-bit 3:2 CSA; three serial stages.   # p.11
results:
| metric | value | unit | technology / device | baseline | condition | page |
| --- | --- | --- | --- | --- | --- | --- |
| area | 119,668 | um2 | Faraday/UMC 65 um LL-RVT (abstract: 65 nm), 2016 | typical DP MAF | post-layout | p.16 |
| AND2-Eq. gates | 74,792 | gates | Faraday/UMC 65 um LL-RVT, 2016 | typical DP MAF | post-layout | p.16 |
| power | 246.9 | mW | Faraday/UMC 65 um LL-RVT, 2016 | typical DP MAF | post-layout, activity 0.5 | p.16 |
| Fmax | 444.24 | MHz | Faraday/UMC 65 um LL-RVT, 2016 | typical DP MAF | post-layout | p.16 |
| energy per operation | 555.52 | pJ/op | Faraday/UMC 65 um LL-RVT, 2016 | typical DP MAF | power x period | p.16 |
| area | 515,123 | um2 | Faraday/UMC 65 um LL-RVT, 2016 | typical QP MAF | post-layout | p.16 |
| AND2-Eq. gates | 321,952 | gates | Faraday/UMC 65 um LL-RVT, 2016 | typical QP MAF | post-layout | p.16 |
| power | 295 | mW | Faraday/UMC 65 um LL-RVT, 2016 | typical QP MAF | post-layout, activity 0.5 | p.16 |
| Fmax | 343 | MHz | Faraday/UMC 65 um LL-RVT, 2016 | typical QP MAF | post-layout | p.16 |
| energy per operation | 855.5 | pJ/op | Faraday/UMC 65 um LL-RVT, 2016 | typical QP MAF | power x period | p.16 |
errors_and_checks: none
conditions: The typical QP MAF executes one quadruple precision instruction per cycle and the typical DP MAF one double precision instruction per cycle, neither supporting the other precision modes (p.17).
evidence: Section 3 with Fig. 2; Section 5 with Tables 1 and 3; the functionality list on p.17.

## new_families
none

## space_gaps
* `multi_precision_simd_fma.lane_split` has no value for a 128-bit datapath, while the design splits one 128-bit register into one quadruple, two double or four single precision operands (p.12, p.15).
* The `multiplier` slot of `multi_precision_simd_fma` does not admit `twin_precision_subword`, which is the family the design's one-array-serves-three-precisions multiplier belongs to (p.13, p.15).
* `multipath_fma` carries no `negation_handling` choice although the document fixes it: the Close path uses a 2's complement representation to avoid the end-around carry adjustment, with the +1 added through an empty slot of the 117-bit 3:2 CSA, and a row of half adders carries the same +1 on the Far path (p.14).
* No choice records the shared exponent processing structure of a SIMD FMA: the design adds one double and two single precision exponent processing units beside the quadruple precision one and reuses the wider unit for a narrower instruction (p.15).

## open_questions
* The technology is printed as "Faraday/UMC 65 um Library (10 M layers)" on p.15 while the abstract states a 65 nm silicon process on p.10.
* The 23% area and 14% latency increases over the typical QP MAF are stated on p.17 without the latency figures the percentage is derived from; Table 1 reports Fmax rather than latency.
* Bypassing the first stage is described only for stand-alone quadruple addition (p.13); whether the double and single precision modes bypass it in the same way is not stated.
* Whether the rounding module is shared or replicated per lane in double and single precision mode is not stated (p.14, p.15).
* Subnormal operand handling is not stated for either the conventional MAF of Section 3 or the proposed design; the document defines only normalized numbers X = (-1)^S x 2^(E-bias) x 1.F (p.11).
* The internal structure of the second- and third-stage adders and of the alignment and normalization shifters is given only by width and composition, not by carry or mux topology (p.14, p.15).
