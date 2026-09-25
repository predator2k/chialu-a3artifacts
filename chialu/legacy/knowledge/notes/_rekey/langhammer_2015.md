---
handle: langhammer_2015
citation: M. Langhammer, B. Pasca, "Floating-Point DSP Block Architecture for FPGAs", ACM/SIGDA International Symposium on Field-Programmable Gate Arrays (FPGA), 2015
actual_citation: Martin Langhammer, Bogdan Pasca, "Design and Implementation of an Embedded FPGA Floating Point DSP Block", 2015 IEEE 22nd Symposium on Computer Arithmetic, 2015
status: mismatch
kind: paper
unit_classes: [BINARY_ALU, VEC_DOT_ACC]
formats: [int18, int27, fp32]
authority: incremental
pages_read: 26-33 / 8
---

## summary
The document implements fixed-point and single-precision floating-point multiplication/addition in one production FPGA DSP block while preserving the existing fixed-point modes (p.26, p.33). A flagged Kogge-Stone prefix structure combines final product reduction, normalization, and RNE rounding in one CPA level (p.28-29). A proposed extension reuses the FP adder as the multiplier's subnormal handler for about 1% additional DSP-block area, but the two functions cannot operate simultaneously (p.31-33).

## families
### hard_fp_dsp  (role: proposes)
mechanism: The unified DSP block overlays an SP FP multiplier on the fixed-point multiplier pipeline and adds a separate SP FP adder. Two 18x18 multipliers can operate independently or combine as one 27x27 multiplier. Dedicated inter-block connections compose multiplier/adder blocks into recursive reduction trees without general routing at every tree level (p.26-28).
choices:
  fp_format: fp32   # p.26
  accumulate_chain: true   # p.27-28
new_choices:
  fixed_point_cohabitation: unified_overlay — FP multiplication reuses and enhances the existing fixed-point pipeline (p.26, p.28)
  fp_adder_integration: separate_unit — the FP adder shares no legacy fixed-point logic (p.28, p.30)
slots:
  none
parameters: two 18x18 multipliers or one 27x27 multiplier; multiplier latency 2 or 3 cycles; first reduction-tree level adds 1 cycle; each later level adds 3 cycles; a 256-element example has 24 clock cycles latency (p.27-28)
results:
| metric | value | unit | technology / device | baseline | condition | page |
| DSP-block area increase | around 15 | % | 20nm production FPGA, 2015 | fixed-point-only DSP block | physical DSP block before routing-interface amortization | p.32 |
| effective DSP cost increase | about 10 | % | 20nm production FPGA, 2015 | fixed-point-only DSP cost | includes fixed existing routing-interface cost | p.32 |
| die-area increase | 0.5 to 5 | % | 20nm production FPGA, 2015 | fixed-point-only FPGA | depends on logic/memory/DSP/transceiver ratio | p.32 |
| SP FP support cost | roughly 10 | % DSP-block area | Arria10 20nm production FPGA, 2015 | existing fixed-point DSP block | implemented design without subnormal support | p.33 |
errors_and_checks: The implemented multiplier and adder flush subnormal inputs/outputs to zero and do not output flags. The proposed architecture can add underflow signaling using tininess detection before rounding (p.30, p.32).
conditions: Full fixed-point backward compatibility, unchanged fixed-point performance, similar FP frequency, minimal area increase, and the FPGA fabric's restricted DSP-block dimensions constrain the design (p.28). Large reduction trees may require added logic-based registers when routing distance reduces frequency (p.28).
evidence: Abstract; §III; Fig. 3; §IV; §VI; §VII (p.26-33)

### round_fused_in_reduction  (role: proposes)
mechanism: The multiplier's carry-save output enters a final CPA that also performs normalization and RNE rounding. The flagged-prefix CPA produces the unincremented sum and incremented candidates, and selection logic chooses the normalized rounded fraction without a second rounding CPA (p.27-29).
choices:
new_choices:
  rounding_candidates: sum_sum1_sum2 — the CPA generates aa+bb, aa+bb+1, and aa+bb+2 (p.29)
slots:
  sig_mul: carry_save_array   # p.27-28
  exp: exponent_path   # p.29
  subnormal: flush_to_zero_mode   # p.30
parameters: fp32; wF=23; 32-bit sum/carry vectors; three pre-shifted candidates; one-level final CPA (p.28-30)
results:
| metric | value | unit | technology / device | baseline | condition | page |
| FP multiplier logic increase | ≈ 3 | % | Arria10 20nm production FPGA, 2015 | existing fixed-point multiplier structures | exception/exponent handling plus normalization/rounding and flagged-prefix extension | p.32 |
| normalized SP FP multiplier area | 2 | normalized area | 20nm commercial DesignWare synthesis, 2015 | 18x18 multiplier = 1 | no subnormal support; latency 3; same synthesized performance | p.32 |
errors_and_checks: Rounding is round to nearest, ties to even. Exception/error-condition postprocessing is present, but the architecture outputs no flags (p.27, p.29, p.32).
conditions: The fusion preserves fixed-point modes that require the first CPA and avoids the area/delay of a separate rounding CPA (p.27-28).
evidence: §III; Fig. 4; §IV; Figs. 5-6; Tables I-II; §VI (p.27-32)

### compound_flagged_prefix  (role: instantiates)
mechanism: Split Kogge-Stone prefix modules generate carry/propagate vectors for independent fixed-point modes and FP multiplication. Flagged-prefix logic produces aa+bb, aa+bb+1, and aa+bb+2, while a carry-select network spans the low/middle/high adder groups for wider fixed-point products (p.28-29).
choices:
  outputs: sum_sum1_plus2 [outside domain]   # p.29
  implementation: flag_row   # p.28-29
  topology: kogge_stone   # p.29
new_choices:
  increment_set: {0, 1, 2} — available additions to the sum for normalization/rounding selection (p.29)
slots:
  none
parameters: two split prefix modules; 32-bit sum/carry inputs; 24-bit sum, 23-bit sum+1, and 24-bit sum+2 FP values; 32-bit fixed-point candidate results (p.29)
results:
| metric | value | unit | technology / device | baseline | condition | page |
| flagged-prefix FP multiplier extension | ≈ 3 | % logic | Arria10 20nm production FPGA, 2015 | existing fixed-point multiplier | includes other FP exception/exponent/normalization logic | p.32 |
errors_and_checks: none
conditions: Prefix boundaries align with fixed-point and FP boundaries. The overlay must retain independent 18x18 modes and wider 38-to-64-bit fixed-point products (p.28-29).
evidence: §IV; Figs. 5-6; Tables I-II; §VI (p.28-32)

### two_path  (role: instantiates)
mechanism: A separate textbook dual-path SP adder sends opposite-sign operands within one exponent difference to a near subtraction/normalization path. All other cases use a far alignment/operation path with trivial normalization (p.30).
choices:
  path_threshold: 1   # p.30
  close_path_trigger: exp_diff_and_effective_sub   # p.30
new_choices:
  physical_malleability: fit_around_multiplier — the Verilog implementation is shaped around deeper multiplier logic without increasing DSP-block height (p.30)
slots:
  subnormal: flush_to_zero_mode   # p.30
  near_lz: lzc_after_add   # p.30
parameters: fp32; latency 3 in the reported area comparison (p.30, p.32)
results:
| metric | value | unit | technology / device | baseline | condition | page |
| FP adder DSP-block contribution | ≈ 10 | % | Arria10 20nm production FPGA, 2015 | fixed-point DSP block | standalone FP adder without subnormal support | p.32 |
| normalized SP FP ALU area | 0.9 | normalized area | 20nm commercial DesignWare synthesis, 2015 | 18x18 multiplier = 1 | no subnormal support; latency 3; same synthesized performance | p.32 |
| normalized SP FP ALU area | 1 | normalized area | 20nm commercial DesignWare synthesis, 2015 | 18x18 multiplier = 1 | subnormal support; latency 3; same synthesized performance | p.32 |
errors_and_checks: The implemented adder flushes subnormal inputs/outputs to zero. The future enhanced adder supports subnormal arithmetic and can be adapted from single-path or dual-path organization (p.30).
conditions: The adder must fit within the DSP-block height. The separate adder does not provide fused multiply-add; multiplier and adder communicate as separate units (p.28, p.30).
evidence: §III; §IV; §V; Fig. 7; Table IV (p.28-32)

## new_families
### shared_subnormal_handler  (domain: dsp, closest: hard_fp_dsp, why_not: hard_fp_dsp lacks a configurable cross-unit mechanism in which an FP adder temporarily becomes a multiplier normalization/rounding resource)
mechanism: A subnormal-capable FP adder accepts the multiplier's pre-rounding mantissa, low product bits, and modified exponent. The adder's left/right shifters, LZC, guard/round/sticky update, and rounding logic normalize multiplier results. Configuration occurs independently per DSP block, and the adder is unavailable for addition/accumulation/multiply-add/recursive modes while serving the multiplier (p.30-32).
choices: handler: {fp_adder}; configuration_granularity: {per_dsp_block}; concurrency: {mutually_exclusive}; supported_cases: {normal_times_normal_underflow, normal_times_subnormal_underflow}
results:
| metric | value | unit | technology / device | baseline | condition | page |
| direct subnormal support for both units | about 4 | % DSP increase | Arria10 20nm production FPGA, 2015 | DSP without subnormal support | dedicated support in both multiplier and adder | p.33 |
| shared-handler subnormal support | ≈ 1 | % DSP increase | Arria10 20nm production FPGA, 2015 | DSP without subnormal support | adder and multiplier support subnormals, but not simultaneously | p.33 |
evidence: §V; Figs. 7-8; Table III; §VI; §VII (p.30-33)

## space_gaps
* hard_fp_dsp lacks a choice for overlaying FP functionality on fixed-point multiplier structures while preserving legacy modes (p.26, p.28).
* hard_fp_dsp lacks a choice for per-block, mutually exclusive reuse of an FP adder as a multiplier subnormal handler (p.30-33).
* compound_flagged_prefix.outputs lacks the document's sum/sum+1/sum+2 candidate set (p.29).
* round_fused_in_reduction lacks a choice that distinguishes rounding fused into a fixed-point-compatible flagged-prefix CPA from rounding fused into the carry-save tree (p.28-29).

## open_questions
* Table IV says its commercial-IP areas are “normalized relative only to themselves,” so equivalence between those normalized values and the implemented Arria10 blocks must not be assumed (p.32).
* The document calls the FP adder combinatorial for FP multiply-accumulate support but also states that FMA is unsupported, so the exact multiply-accumulate arithmetic contract remains ambiguous (p.28, p.32).
* The proposed shared subnormal architecture is analyzed rather than reported as implemented in the production FPGA (p.30-33).
