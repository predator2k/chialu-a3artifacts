---
handle: srinivasan_2013
citation: S. Srinivasan, K. Bhudiya, R. Ramanarayanan, P. S. Babu, T. Jacob, S. Mathew, R. Krishnamurthy, V. Erraguntla, "Split-Path Fused Floating Point Multiply Accumulate (FPMAC)", ARITH-21, pp. 17-24, 2013
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_DOT_ACC]
formats: [fp32, fp64]
authority: incremental
pages_read: 8 / 8 (pp. 17-24)
---

## summary
The document proposes an IEEE floating-point FPMAC with separate near/far paths selected from the product-to-addend exponent difference. The near path injects the aligned addend into the sparse multiplication CSA tree, normalizes before completion addition, and combines dual-sum addition with rounding. The reported comparisons evaluate double precision through logic-level analysis, normalized area estimates, and preliminary gate-level simulation rather than completed silicon.

## families
### multipath_fma  (role: proposes)
mechanism: An exponent-difference detector selects a near path for d=Exy-Ez={-2,-1,0,1} and a far path for all other values. The near addend is shifted by at most two bits and injected into the second stage of the sparse multiplication CSA tree, which removes a separate 3:2 compression stage. Separate near/far normalization paths feed one combined addition/rounding unit, and the inactive path can be clock- or power-gated. # pp.17-21
choices:
  path_count: 2   # pp.17-18
  path_select_criterion: exponent_difference   # pp.17-18
new_choices:
  near_path_exponent_set: {-2,-1,0,1} — exponent differences assigned to the timing-critical near path   # pp.17-18
  accumulate_injection_point: second_csa_stage — location where aligned Mz enters the sparse multiplication tree   # p.20
  inactive_path_gating: clock_or_power — gating of the unused near or far datapath from the path flag   # pp.21-23
  shared_completion_rounder: true — both paths use one final combined sum/rounding unit   # pp.19-21
slots:
  align: full_align   # pp.18,20-21
  lza: lza   # pp.19-21
  cpa: UNKNOWN   # p.19
  round: compound_adder_select   # p.19
  multiplier: UNKNOWN   # pp.18-20
parameters: fp32 and fp64 techniques; reported comparisons use fp64 with 53-bit mantissa multiplication; near-path alignment is 0/1/2 bits; near normalization is up to 2m bits; far normalization is up to m+3 bits; pipeline depth and II are UNKNOWN   # pp.18-21
results:
| metric | value | unit | technology / device | baseline | condition | page |
| total critical-path logic | 72 | logic levels | UNKNOWN; 2013 | Power6: 84; Lang: 76 | analytical block-level comparison | p.23 |
| timing improvement | 14.2% | faster | UNKNOWN; 2013 | IBM Power6 FPMAC | logic-level estimate | p.22 |
| timing improvement | 5.2% | faster | UNKNOWN; 2013 | Lang FPMAC | logic-level estimate | p.22 |
| preliminary timing improvement | ~11% | faster | UNKNOWN; 2013 | Lang FPMAC | incomplete gate-level implementation including interconnect/routing delays | p.22 |
| normalized total area | 939 | relative area units | UNKNOWN; 2013 | Power6: 863; Lang: 1021 | 106-bit shifter area is normalized to 100 | pp.23-24 |
| area difference | 8% | increase | UNKNOWN; 2013 | IBM Power6 FPMAC | normalized logic-block estimate | p.23 |
| area difference | 12% | reduction | UNKNOWN; 2013 | Lang FPMAC | normalized logic-block estimate | p.23 |
| potentially gated logic | up-to ~20% | of design | UNKNOWN; 2013 | ungated operation | opportunity inferred from mutually exclusive near/far paths; not a measured power result | p.23 |
errors_and_checks: The design supports all IEEE rounding modes for double-precision FPMAC; no ulp bound, fault model, detection coverage, false-alarm rate, or alias rate is reported.   # pp.17-18
conditions: The reported area/timing comparisons apply only to double precision, although the mechanisms are illustrated for fp32 and stated to generalize to fp64. # pp.18-19 The timing analysis does not precisely include interconnect except for extra LZA/shifter stages. # p.22 The silicon implementation, final block stitching, and synthesis remain ongoing. # pp.22-24 The inputs are described as normalized IEEE floating-point operands, so subnormal handling is not established. # p.18
evidence: Abstract; §III; Figures 1-4; §IV; Tables 1-2, pp.17-24.

### reduced_latency_fma  (role: extends)
mechanism: The carry/save outputs are normalized before completion addition, so only the required m-bit result is added. A dual adder computes sum and sum+1, and carry/guard/round/sticky information selects the rounded result. The LZA supplies the near-path shift count and sign while normalization proceeds, which removes a separate 2m-bit sum/sign-detection stage. An overflow pre-shift prevents the combined add/round unit from receiving a 111.XXX form. # pp.19-21
choices:
  rounding_position: fused_with_cpa_dual_sum   # p.19
  normalize_before_add: true   # pp.19-21
new_choices:
  sign_detection_source: lza_result — the LZA output determines sign without a separate sum/sign unit   # pp.19-21
  overflow_preshift: true — an overflowing 11.XXX carry/save result is shifted right before normalization   # pp.19-20
slots:
  align: full_align   # pp.20-21
  lza: lza   # pp.19-21
  cpa: UNKNOWN   # p.19
  round: compound_adder_select   # p.19
  multiplier: UNKNOWN   # pp.18-20
parameters: dual addition over the MSB m-1 bits; carry/sticky/round computation over the LSB m+1 bits; Table 1 models a 52-bit dual add with GRTC on the lower 56 bits; pipeline depth and II are UNKNOWN   # pp.19,23
results:
| metric | value | unit | technology / device | baseline | condition | page |
| critical-path reduction from early near-path injection | 3% | logic levels | UNKNOWN; 2013 | Lang FPMAC | removal of one 3:2 compressor | p.19 |
| critical-path reduction from normalization/round-add changes | 13% | logic levels | UNKNOWN; 2013 | implementation without optimizations 2 and 3 | combined effect stated by the authors | p.19 |
errors_and_checks: Correct rounding is selected from sum/sum+1 using carry/guard/round/sticky bits; no numerical error measurement or checker is reported.   # pp.19-21
conditions: The combined round/add scheme requires the carry/save result to be no larger than 11.XXX, so overflow is pre-shifted and the exponent is incremented. # pp.19-20 The reported reductions are logic-level estimates rather than completed-silicon measurements. # pp.22-24
evidence: §III, especially the completion-adder description and §3.3; Figures 1 and 4; Table 1, pp.19-23.

## new_families
none

## space_gaps
* The multipath_fma vocabulary lacks the near-path exponent-set, CSA-tree injection-point, shared-rounder, and inactive-path-gating choices established here. # pp.17-23
* The multiplier slot lacks a family for the document's sparse Wallace-style carry-save reduction tree, so multiplier cannot be assigned without stretching carry_save_array. # pp.18-20
* The reduced_latency_fma vocabulary lacks choices for LZA-derived sign detection and the overflow pre-shift required by the combined round/add stage. # pp.19-21

## open_questions
* The document does not identify the topology/circuit family of the final dual carry-propagate adder. # p.19
* The document does not establish handling for subnormal operands, NaNs, infinities, or signed zero. # pp.17-24
* The final silicon timing, area, power, technology node, pipeline depth, and initiation interval remain unreported. # pp.22-24
