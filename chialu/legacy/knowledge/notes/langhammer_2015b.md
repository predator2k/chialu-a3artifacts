---
handle: langhammer_2015b
citation: M. Langhammer, B. Pasca, "Design and Implementation of an Embedded FPGA Floating Point DSP Block", 22nd IEEE Symposium on Computer Arithmetic (ARITH), 2015
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU, VEC_DOT_ACC]
formats: [fp32, fixed18, fixed27]
authority: incremental
pages_read: 26-33 / 8
---

## summary
The paper presents a production 20nm FPGA DSP block that overlays an SP FP multiplier on fixed-point multiplier hardware and adds a separate SP FP adder while retaining fixed-point modes (pp.26-28). A flagged-prefix CPA combines multiplier reduction/normalization/rounding, and dedicated inter-block connections form low-latency recursive FP reduction trees (pp.28-30). A future configuration reuses the FP adder to handle multiplier subnormals at an estimated ≈1% additional DSP-block area (pp.30-33).

## families
### hard_fp_dsp  (role: proposes)
mechanism: The DSP block retains two 18x18 fixed-point multipliers that combine into a 27x27 multiplier. The SP FP multiplier overlays the 27x27 pipeline, while a separate malleable FP adder fits around the multiplier logic. Dedicated chain connections compose multiplier/adder blocks into recursive reductions without general-purpose routing. FMA is not supported (pp.27-30).
choices:
  fp_format: fp32   # p.26
  accumulate_chain: true   # p.28
new_choices:
  fixed_point_overlay: fp_multiplier_over_27x27_fixed_pipeline — the FP multiplier reuses the fixed-point multiplier/compressor/CPA structures   # pp.27-29
  fp_adder_integration: separate_malleable_unit — the FP adder shares no arithmetic logic but fits within the DSP-block aspect ratio   # p.30
  subnormal_resource_sharing: fp_adder_reconfigured_as_multiplier_handler — configuration-time sharing provides adder or multiplier subnormal handling, but not both simultaneously   # p.31
slots:
  none
parameters: two 18x18 multipliers; combined 27x27 mode; SP FP multiplier latency 2 or 3 cycles; first reduction level adds 1 cycle; each later level adds 3 cycles   # pp.27-28
results:
| metric | value | unit | technology / device | baseline | condition | page |
| FP multiplier support logic increase | ≈ 3% | DSP-block logic | 20nm Arria 10 / 2015 | fixed-point multiplier structures | without subnormal support | p.32 |
| separate FP adder contribution | ≈ 10% | DSP-block area | 20nm Arria 10 / 2015 | fixed-point-only DSP block | without subnormal support | p.32 |
| combined DSP-block increase | around 15% | DSP-block area | 20nm Arria 10 / 2015 | fixed-point-only implementation | arithmetic additions before routing-interface amortization | p.32 |
| effective DSP cost increase | about 10% | DSP-block area | 20nm Arria 10 / 2015 | fixed-point-only DSP block including routing interface | implemented FP support | pp.32-33 |
| device die-area increase | 0.5% to 5% | die area | 20nm Arria 10 / 2015 | device without FP-enhanced DSP block | depends on logic/memory/DSP/transceiver ratio | p.32 |
| direct adder and multiplier subnormal support | about 4% | arithmetic-component area | 20nm estimate / 2015 | implemented DSP arithmetic components | first-order estimate | p.33 |
| shared-adder subnormal support | ≈ 1% | DSP-block area | 20nm estimate / 2015 | implemented FP DSP block | adder and multiplier cannot use subnormal support simultaneously | p.33 |
errors_and_checks: The implemented Arria10 FP multiplier and adder flush subnormal inputs and outputs to zero; the proposed enhanced architectures emit no flags but can be extended for underflow detection before rounding (pp.30,32).
conditions: Full fixed-point backward compatibility, unchanged fixed-point performance, similar FP frequency, minimal area increase, and a narrow physical aspect ratio constrain the design. Direct subnormal logic may increase final-stage delay and fixed-point cost (pp.28,33).
evidence: Abstract; §§III-VII; Figs.2-8; Tables I-IV.

### round_fused_in_reduction  (role: extends)
mechanism: The SP multiplier combines final carry-save sub-product reduction, one-bit normalization, and RNE rounding into one CPA level. Float/round logic selects aa+bb, aa+bb+1, or aa+bb+2 from flagged-prefix outputs, avoiding a separate post-normalization rounding CPA (pp.27-29).
choices:
new_choices:
  selected_sum_set: sum_sum1_sum2 — the CPA generates three pre-shifted candidates for normalization and rounding   # p.29
slots:
  subnormal: flush_to_zero_mode   # p.30
parameters: 24-bit input sum; 23-bit sum-plus-one; 24-bit sum-plus-two; 23-bit SP fraction; RNE   # pp.27,29
results:
| metric | value | unit | technology / device | baseline | condition | page |
| FP multiplier normalized area | 2 | relative area | 20nm Synopsys DesignWare / 2015 | 18x18 multiplier = 1 | no subnormal support, latency 3, same synthesized performance | p.32 |
| FP multiplier normalized area | 2.4 | relative area | 20nm Synopsys DesignWare / 2015 | 18x18 multiplier = 1 | subnormal support, latency 3, same synthesized performance | p.32 |
errors_and_checks: Rounding is round to nearest, ties to even. The implemented multiplier flushes subnormal inputs/outputs to zero (pp.27,30).
conditions: The fused CPA must preserve all legacy fixed-point modes, including independent 18x18 products and wider 38-to-64-bit results (pp.28-30).
evidence: §III; §IV; Figs.4-6; Tables I-II; Table IV.

### compound_flagged_prefix  (role: extends)
mechanism: Half adders prepare two 32-bit sum/carry vectors for a split Kogge-Stone prefix network. Flagged outputs compute aa+bb, aa+bb+1, and aa+bb+2, while overlapping carry-select and prefix structures preserve fixed-point configurations (pp.28-30).
choices:
  outputs: sum_sum1_sum2 [outside domain]   # p.29
  implementation: flag_row   # pp.28-29
  topology: kogge_stone   # p.29
new_choices:
  increment_range: 0_to_2 — rounding and normalization require three candidate sums rather than only sum/sum+1   # p.29
slots:
  none
parameters: two 32-bit vectors; split prefix modules; 24-bit/23-bit FP candidates; low/middle/high CPA groups   # pp.28-30
results:
| metric | value | unit | technology / device | baseline | condition | page |
| FP multiplier extension | ≈ 3% | DSP-block logic | 20nm Arria 10 / 2015 | reused fixed-point multiplier structures | includes exponent/exception/normalization/rounding logic | p.32 |
errors_and_checks: none
conditions: The split modules are required for two independent fixed-point multipliers, while the full carry-select path spans all three adder groups for wider fixed-point products (pp.29-30).
evidence: §IV; Figs.5-6; Tables I-II.

### two_path  (role: instantiates)
mechanism: The separate SP adder uses a near path for opposite-sign operands within one exponent and a far path for all other cases. The near path performs trivial alignment/subtraction/full normalization; the far path performs full alignment/addition or subtraction/trivial normalization (p.30).
choices:
  path_threshold: 1   # p.30
  close_path_trigger: exp_diff_and_effective_sub   # p.30
new_choices:
  physical_malleability: fit_around_multiplier_logic — the Verilog implementation conforms to the fixed DSP-block height   # p.30
slots:
  subnormal: flush_to_zero_mode   # p.30
parameters: fp32; latency 3 in the reported area comparison; combinatorial FP ALU in the production DSP block   # p.32
results:
| metric | value | unit | technology / device | baseline | condition | page |
| FP ALU normalized area | 0.9 | relative area | 20nm Synopsys DesignWare / 2015 | 18x18 multiplier = 1 | no subnormal support, latency 3 | p.32 |
| FP ALU normalized area | 1 | relative area | 20nm Synopsys DesignWare / 2015 | 18x18 multiplier = 1 | subnormal support, latency 3 | p.32 |
errors_and_checks: The production adder flushes subnormal inputs/outputs to zero. The proposed enhancement supports subnormal arithmetic but produces no flags (pp.30,32).
conditions: The adder is separate from legacy fixed-point logic and must fit without increasing DSP-block height. In multiplier-subnormal-handler mode, the adder is unavailable for addition/accumulation/multiply-add/recursive modes (pp.30-31).
evidence: §IV; §V; Figs.7-8; Tables III-IV.

## new_families
### recursive_fp_dsp_reduction  (domain: dot, closest: pairwise_tree, why_not: pairwise_tree is identified as an integer path and cannot express chained hardened FP DSP blocks with per-level pipeline/routing rules)
mechanism: Adjacent DSP blocks assume different multiplier/adder roles and exchange FP results through dedicated inter-block connections. The multiplier contributes two or three cycles, the first adder-tree level contributes one cycle, and each subsequent level contributes three cycles. Optional balanced logic-register depths accommodate longer physical routes (p.28).
choices: multiplier_latency: {2, 3}; later_level_latency_cycles: 3; routing: {dedicated_chain, balanced_soft_routing}
results:
| metric | value | unit | technology / device | baseline | condition | page |
| 256-element vector latency | 24 | clock cycles | 20nm production FPGA / 2015 | UNKNOWN | recursive reduction, reported as 3 log2(length) | p.28 |
evidence: §III; Fig.3; p.28.

## space_gaps
* `compound_flagged_prefix.outputs` lacks the reported `sum_sum1_sum2` value (p.29).
* `round_fused_in_reduction.slot sig_mul` cannot name a hardened fixed/FP DSP multiplier overlay (pp.27-29).
* The dot vocabulary lacks a recursive FP DSP-block reduction family with dedicated chain routing and per-level pipeline latency (p.28).
* `hard_fp_dsp` lacks choices for fixed-point overlay, separate-adder integration, and configuration-time sharing of subnormal hardware (pp.27-33).

## open_questions
* The paper identifies Kogge-Stone for the middle split prefix network but does not state whether every high/low flagged-prefix portion uses the same topology (p.29).
* The subnormal-sharing design is future work supported by synthesis estimates rather than an implementation in the production FPGA (pp.30-33).
* The paper does not quantify frequency, power, or absolute silicon area for the production block (pp.32-33).
