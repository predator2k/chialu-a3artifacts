---
handle: schwarz_2005
citation: E. M. Schwarz, M. Schmookler, S. D. Trong, "FPU Implementations with Denormalized Numbers", IEEE Transactions on Computers, 2005
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU, other]
formats: [fp32, fp64, fp80, fp128, binary_fp, hexadecimal_fp]
authority: survey
pages_read: 12 / 12
---

## summary
The paper surveys hardware/software techniques for processing denormalized floating-point inputs and underflowed results. The paper analyzes tagging, inline operand correction, prenormalization, result denormalization, bounded normalization, and the implementations used in the IBM Z990, Power3, and Power4/5 FPUs.

## families
### full_hardware  (role: analyzes)
mechanism: Denormal inputs are handled through register tags, operand prenormalization, or late corrections to exponent differences/implied bits. Underflowed results are handled by a dedicated right-shifting unit, pipeline feedback, iterative small shifts, or normalization bounded at the denormal radix point. The Z990 applies inline corrections and bounded normalization; Power3 combines tags/direct handling with selected prenormalization stalls; Power4 prenormalizes every denormal operand and recycles unusual results through its normalizer and rounder.
choices:
new_choices:
  input_detection: {register_tags, late_exponent_and_fraction_detection} — identifies denormal operands before or during execution   # pp.826-827
  input_handling: {prenormalization_stall, inline_exponent_and_significand_correction} — selects normalization before execution or corrections within the arithmetic pipeline   # pp.827, 832-835
  result_handling: {dedicated_denormalization_unit, pipeline_feedback, iterative_small_shift, bounded_normalization} — produces denormal results after underflow   # pp.830-833
  unusual_case_policy: {pipelined_hardware, short_stall, slow_mode, internal_software} — handles cases outside the normal dataflow   # pp.832-835
slots: none
parameters: S/390 G5 iterative denormalization shifts 1 to 4 bits per cycle and may require up to 13 cycles for fp64; Power4 adds two internal exponent bits and usually uses a two-cycle back-end stall   # pp.830, 835
results:
| metric | value | unit | technology / device | baseline | condition | page |
| denormalization latency | up to 13 | cycles | UNKNOWN / S/390 G5 / 1998 | software trap | fp64 result, 1-to-4-bit feedback shifter | p.830 |
| back-end stall latency | 2 | cycles | UNKNOWN / Power4 / year UNKNOWN | unstalled normal case | most unusual-result stalls | p.835 |
| added latency per additional denormal operand | 3 | cycles | UNKNOWN / Power4 / year UNKNOWN | first denormal operand | pipelined multiply-add prenormalization | p.835 |
errors_and_checks: Hardware paths preserve IEEE 754 denormal inputs and produce an underflowed result by aligning it to Emin and rounding it; the Z990 uses internal software for one enabled-underflow FMA case before taking the architected trap   # pp.830, 833
conditions: Register tags can remove arithmetic critical paths, but tag generation adds detection logic/register state and complicates mixed-format execution and verification   # pp.826-827. A dedicated denormalization unit requires a large right shifter and instruction reordering, while pipeline reuse requires stalls, squashing, or reordering   # p.830. Bounded normalization avoids a separate denormalization pass by preventing the normalizer from shifting beyond the denormal radix point   # pp.831-833.
evidence: §§3-6 and §§8-10, pp.826-835; Figs. 5-7

### trap_to_software  (role: compares)
mechanism: A detected denormal operand or underflowed result invokes software or internal millicode when the hardware dataflow cannot produce the required form. The Z990 uses millicode for the enabled-underflow FMA case in which a denormal addend is greater than the product and significant product bits must enter the rebiased result.
choices:
new_choices: none
slots: none
parameters: UNKNOWN
results:
| metric | value | unit | technology / device | baseline | condition | page |
| external trap latency | thousands | cycles | UNKNOWN / general processors / year 2005 | hardware handling | denormal trap | p.832 |
errors_and_checks: The Z990 millicode recalculates the result before the architected underflow trap, preserving the required rebiased result   # p.833
conditions: Software traps cause long execution times and make denormal support impractical for programmers   # p.825. The Z990 confines internal software to a case where an architected underflow trap must already be taken   # pp.832-833.
evidence: §§1, 7, 8.3, pp.825, 832-833

### flush_to_zero_mode  (role: analyzes)
mechanism: The Apple G4/G5 vector unit supports a noncompliant mode that forces denormal inputs and underflow results to zero instead of computing denormal values.
choices:
new_choices: none
slots: none
parameters: UNKNOWN
results:
| metric | value | unit | technology / device | baseline | condition | page |
errors_and_checks: IEEE 754 denormal semantics are not preserved   # p.825
conditions: The mode avoids denormal computation but is explicitly described as noncompliant   # p.825.
evidence: §1, p.825

### classic_fma  (role: instantiates)
mechanism: The pipeline forms A*C and aligns/complements only addend B while product sum/carry development proceeds, then merges B into the product with a final carry-save adder. Add/subtract sets C to 1.0, while multiply sets B to zero. Denormal operands require corrected exponent differences/implied bits, and the aligner retains two positions beyond the product LSB for a rare subtraction/rounding case.
choices:
  subsume_fp_add: true   # p.828
  negation_handling: dual_adder   # p.832
  pipeline_depth: 5   # p.832
new_choices: none
slots:
  lza: lza   # p.835
  multiplier: booth_recoded_parallel [booth_radix=4]   # p.832
parameters: Z990 fraction dataflow 176 bits; two 116-bit fraction adders calculate A-B and B-A; Power3 uses a 108-bit LZA and 161-bit normalizer; Power4 recycles unusual results through the normalizer/rounder   # pp.832, 835
results:
| metric | value | unit | technology / device | baseline | condition | page |
| pipeline depth | 5 | stages | UNKNOWN / Z990 / year UNKNOWN | UNKNOWN | fused binary/hexadecimal multiply-add dataflow | p.832 |
errors_and_checks: The product is not rounded before addition/subtraction; underflow with traps disabled produces a rounded denormal result   # pp.828, 830
conditions: Aligning only B avoids shifting/complementing product sum/carry signals on the critical path   # p.828. Correct denormal-input rounding requires two retained bit positions beyond the product LSB   # p.828. Some enabled-underflow/cancellation arrangements require a wider shifter, bounded-result manipulation, prenormalization, or a trap   # pp.829, 833-835.
evidence: §4.3 and §§7-10, pp.828-835; Figs. 1-7

### booth_recoded_parallel  (role: instantiates)
mechanism: The Z990 uses radix-4 Booth recoding for a 56-by-56-bit multiplier. The multiplier integer bit selects between Booth coefficients computed for integer-bit values zero and one. A denormal multiplicand is corrected by subtracting a multiplier-scaled leading-bit term through an available input in the 3:2 carry-save reduction tree.
choices:
  booth_radix: 4   # pp.827, 832
new_choices:
  denormal_integer_bit_correction: {late_partial_product, leading_one_addition, leading_zero_subtraction} — corrects partial products after late denormal detection   # pp.827-828
slots:
  reduction: csa_reduction_tree   # p.833
parameters: 56 by 56 bits; 29 partial-product terms; one correction term for a denormal multiplicand   # pp.832-833
results:
| metric | value | unit | technology / device | baseline | condition | page |
errors_and_checks: Exact denormal significand multiplication is retained through explicit integer-bit correction terms   # pp.827-828, 833
conditions: One or two delayed correction rows avoid added latency when the reduction tree has unused inputs and does not gain a stage   # p.828. The Z990 correction term does not affect timing because its 29-term 3:2 tree has free inputs   # p.833.
evidence: §§4.2 and 8.1, pp.827-828, 832-833

## new_families
none

## space_gaps
* `full_hardware`, `trap_to_software`, and `flush_to_zero_mode` appear as slot values but lack declared family choices for detection, prenormalization, result generation, and stall/trap policy   # pp.825-835
* `classic_fma` lacks a `subnormal` slot even though denormal operands/results materially change its aligner, exponent correction, normalization, and exception paths   # pp.828-835
* Floating-point register representation lacks a choice for normalized/unnormalized storage, tag bits, implied-bit storage, and widened internal exponents   # pp.826-827, 833-835

## open_questions
* The paper does not report technology nodes, frequency, area, or power for the Z990, Power3, or Power4 implementations.
* The paper does not identify the carry-propagate-adder topology used in the surveyed FMA implementations.
