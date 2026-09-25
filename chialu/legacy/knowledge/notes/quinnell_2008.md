---
handle: quinnell_2008
citation: E. Quinnell, E. E. Swartzlander, C. Lemonds, "Bridge Floating-Point Fused Multiply-Add Design", IEEE Transactions on VLSI Systems, vol. 16, no. 12, pp. 1726-1730, 2008
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_DOT_ACC]
formats: [fp64]
authority: incremental
pages_read: 1726-1730 / 5
---

## summary
The paper proposes a bridge FMA that adds fused multiply-add to separate FADD/FMUL units while reusing their multiplier array and add/round stage (pp.1726-1729). AMD 65-nm silicon-on-insulator implementations compare the bridge against separate FADD/FMUL blocks and a classic FMA (pp.1726, 1729). The bridge preserves parallel standalone FADD/FMUL execution but trades additional area and FMA peak power for a faster FMA than cascaded FADD/FMUL execution (p.1729).

## families
### bridge_fma  (role: proposes)
mechanism: Separate dual-path FADD and FMUL units remain capable of independent parallel execution. A clock-gated bridge accepts the FMUL multiplier-array sum/carry output, combines it with a 161-bit addend supplied through the FADD path, and performs the classic FMA combination/normalization work. The FADD add/round stage then selects the bridge result and completes the single rounding (pp.1727-1729).
choices:
  composition_style: bridge_reuse   # pp.1727-1729
new_choices:
  standalone_parallel_execution: true — whether standalone FADD and FMUL instructions can execute concurrently   # pp.1727, 1729
  bridge_clock_gating: true — whether bridge-only hardware is clock-gated outside FMA instructions   # p.1727
slots:
  align: full_align   # pp.1727-1729
  lza: lza   # pp.1727-1729
  cpa: UNKNOWN
  round: compound_adder_select   # p.1729
  multiplier: UNKNOWN
parameters: IEEE-754 double precision; 64-bit operands; 53 × 53-bit significand multiplier; 106-bit sum/carry product; 161-bit aligned addend; 109-bit adder followed by a 52-bit incrementer; dual 59-bit adders producing a result and result plus 2, or result plus 1 for subtraction; implementation measurements taken with internal pipeline latches removed   # pp.1727-1729
results:
| metric | value | unit | technology / device | baseline | condition | page |
| FADD/FMUL latency improvement | 30% to 70% faster | % | AMD 65-nm silicon-on-insulator (2008) | classic FMA unit | standalone FADD or FMUL instruction | p.1729 |
| FADD/FMUL peak-power reduction | 50% to 70% lower | % | AMD 65-nm silicon-on-insulator (2008) | classic FMA unit | standalone FADD or FMUL instruction; maximum observed power over random vectors | p.1729 |
| FMA performance gain | about 12% | % | AMD 65-nm silicon-on-insulator (2008) | combination of an FADD and an FMUL | FMA instruction; total block latency with internal pipeline latches removed | p.1729 |
| area increase | about 40% | % | AMD 65-nm silicon-on-insulator (2008) | execution block containing an FADD and an FMUL | added FMA functionality | p.1729 |
| FMA peak-power increase | 65% | % | AMD 65-nm silicon-on-insulator (2008) | execution block containing an FADD and an FMUL | FMA instruction; maximum observed power over random vectors | p.1729 |
errors_and_checks: The FMA executes multiplication and addition at full precision and performs one final rounding; no numerical-error measurements or concurrent checks are reported.   # pp.1726, 1729
conditions: The bridge preserves standalone FADD/FMUL performance and permits both instructions to execute in parallel (pp.1726, 1729-1730). The bridge has higher FMA peak power and lower FMA performance than the classic FMA (p.1729). The comparison uses latchless total block latency rather than a specified pipeline frequency, and peak-power vectors differ between blocks (p.1729).
evidence: Abstract; Section III; Figs. 3, 6, and 7; Section IV; Table I; Section V (pp.1726-1729).

### classic_fma  (role: compares)
mechanism: The classic serial architecture multiplies two 53-bit significands into a 106-bit carry-save pair while aligning the addend across 161 bits. A 3:2 CSA combines the product and addend. A 161-bit adder, or a 109-bit adder followed by a 52-bit incrementer, resolves the result while a 109-bit LZA operates in parallel. Complementing, normalization, rounding, and possible post-normalization follow (p.1727).
choices:
new_choices: none
slots:
  align: full_align   # p.1727
  lza: lza   # p.1727
  cpa: UNKNOWN
  round: UNKNOWN
  multiplier: UNKNOWN
parameters: IEEE-754 double precision; 53 × 53-bit significand multiplication; 106-bit carry-save product; 161-bit aligner; 3:2 CSA; 109-bit adder plus 52-bit incrementer alternative; 109-bit LZA; 52-bit rounding adder or incrementer   # p.1727
results: none
errors_and_checks: One rounding occurs after full-precision multiplication and addition; no numerical-error measurements or concurrent checks are reported.   # pp.1726-1727
conditions: A classic FMA has better FMA performance and lower FMA peak power than the bridge, but standalone FADD/FMUL instructions have greater latency and cannot execute concurrently on the classic unit (pp.1726, 1729).
evidence: Section II-B; Fig. 2 (p.1727); Section IV and Table I (p.1729).

### two_path  (role: instantiates)
mechanism: A Farmwald dual-path FADD uses a far path when exponent difference exceeds 1 and a close path when exponents are equal or differ by 1. The far path swaps operands after exponent comparison and aligns the smaller significand. The close path evaluates shifted/non-shifted cases with three leading-one predictors, a significand comparator, and swap multiplexers. Both paths feed a shared FADD/FMA add/round stage (pp.1728-1729).
choices:
  path_threshold: 1   # p.1728
  close_path_trigger: exp_diff_only   # p.1728
  path_select_point: late_result_mux   # pp.1728-1729
  shared_rounding: true   # pp.1728-1729
new_choices: none
slots:
  sig_adder: UNKNOWN
  round: compound_adder_select   # p.1729
  exp: exponent_path   # p.1728
  subnormal: UNKNOWN
  far_align: full_align   # p.1728
  close_norm: single_barrel   # p.1728
  near_lz: lza   # p.1728
parameters: 64-bit operands; close-path shifts of one bit; three leading-one predictors; 53-bit priority encoder; 5-bit normalization control; normalization by up to 54 bits; dual 59-bit adders in the shared add/round stage   # pp.1728-1729
results: none
errors_and_checks: No numerical-error measurements or concurrent checks are reported.   # pp.1728-1729
conditions: The shared add/round stage completes standalone FADD operations and bridge FMA rounding, while the separate FADD/FMUL structure retains parallel standalone execution (pp.1728-1729).
evidence: Section III-C; Fig. 5 (p.1728); Section III-E; Fig. 7 (p.1729).

### sig_mul_then_round  (role: instantiates)
mechanism: The FMUL processes two 64-bit operands with a 53 × 53-bit significand multiplier while exponent/sign logic runs in parallel. Standalone multiplication sends the 106-bit sum/carry output to a rounding unit. FMA operation sends the unrounded sum/carry product to the bridge and clock-gates the FMUL rounding element (p.1728).
choices:
new_choices: none
slots:
  sig_mul: UNKNOWN
  round: UNKNOWN
  exp: exponent_path   # p.1728
  subnormal: UNKNOWN
parameters: IEEE-754 double precision; two 64-bit operands; 53 × 53-bit significand multiplier; 106-bit sum/carry output   # p.1728
results: none
errors_and_checks: No numerical-error measurements or concurrent checks are reported.   # p.1728
conditions: The rounding element operates for standalone FMUL instructions and is clock-gated when an FMA sends the unrounded product to the bridge (p.1728).
evidence: Section III-B; Fig. 4 (p.1728).

## new_families
none

## space_gaps
* `bridge_fma` lacks choices for independent parallel FADD/FMUL execution and clock-gating of bridge-only hardware, although both properties are explicit parts of the proposed architecture (pp.1727, 1729).
* The multiplier-array description does not identify a vocabulary multiplier family, so the `multiplier`/`sig_mul` slots cannot be filled without inference (p.1728).

## open_questions
* Table I is present as a raster without legible cell values in the supplied document text, so its absolute latency/area/peak-power figures must not be inferred from the prose summaries (p.1729).
* The paper does not specify the internal topology of the 109-bit, 52-bit, or dual 59-bit adders, so their adder-family assignments remain `UNKNOWN` (pp.1727, 1729).
* The paper does not state its handling of subnormals, NaNs, infinities, or all IEEE rounding modes (pp.1726-1729).
