---
handle: seetharam_2013
citation: Seetharam, Keh, Nathan, Sorin, "Applying Reduced Precision Arithmetic to Detect Errors in Floating Point Multiplication", Proc. PRDC 2013, pp. 232-235, 2013
actual_citation: same
status: ok
kind: paper
unit_classes: [other]
formats: [fp32]
authority: incremental
pages_read: p.232-p.235 / 4
---

## summary
The paper extends reduced precision checking from floating-point addition to floating-point multiplication. A reduced-mantissa multiplier detects errors by comparing its product against the most significant mantissa bits of the full-precision product while allowing bounded fault-free differences caused by truncation and rounding.

## families
### reduced_precision  (role: extends)
mechanism: A full 32-bit floating-point multiplier is checked by a multiplier with the same sign/exponent fields and a shorter mantissa. For checker mantissa length X, the checker computes AhighBhigh and compares it with the upper 2X+1 bits of the full product. A two-bit overlap between the reduced product and omitted cross-products permits a fault-free base-10 difference below 8, so differences within 7 do not signal an error. Checking is disabled for infinity, NaN, and denormal operands or products.
choices:
  replica_width_bits: 7 [outside domain]   # p.234
  bound_type: absolute   # p.234
  correct_by_substitution: false   # pp.232-235
new_choices:
  comparison_tolerance: 7 — maximum allowed base-10 difference between compared mantissa values   # p.234
  special_value_policy: checking_disabled — disables checking for infinity, NaN, and denorm   # p.234
slots: none
parameters: 32-bit floating-point operands; 1 sign bit, 7 exponent bits, and 24 computational mantissa bits; 7-bit checker mantissa; 1,000 sampled multiplier wires and 1,000 sampled adder wires; 48 random-operand experiments per wire   # pp.233-234
results:
| metric | value | unit | technology / device | baseline | condition | page |
| error detection among unmasked multiplier faults | 26.5 | % | UNKNOWN / 2013 | unmasked injected faults | permanent single stuck-at faults, including faults in RPC hardware | p.234 |
| error detection among unmasked adder faults | 48.8 | % | UNKNOWN / 2013 | unmasked injected faults | permanent single stuck-at faults, including faults in RPC hardware | p.234 |
| masked injected faults | approximately 85 | % | UNKNOWN / 2013 | all injected faults | reported for both multiplier and adder | p.234 |
| multiplier SDCs with result error below 1% | 90.8 | % | UNKNOWN / 2013 | unmasked undetected multiplier faults | 7-bit checker mantissa | p.235 |
| maximum undetected error for X=7 | about 5.5 | % | UNKNOWN / 2013 | maximum mantissa value 2^X-1 | allowed difference is 7 | p.234 |
| area overhead | 17.8 | % | 45nm / 2013 | FPU without RPC | combined floating-point multiplier and adder, Synopsys layout | p.235 |
| dynamic power | 0.210 | mW | 45nm / 2013 | 0.155mW | 35% overhead; 1,000 random inputs; post-layout parasitics | p.235 |
| static power | 0.114 | mW | 45nm / 2013 | 0.098mW | 16% overhead; post-layout parasitics | p.235 |
| total power | 0.324 | mW | 45nm / 2013 | 0.253mW | 28% overhead | p.235 |
| multiplier SDCs above 1% relative to addition RPC | about 3 | times | UNKNOWN / 2013 | RPC for addition | 7-bit checker mantissas | p.235 |
errors_and_checks: The fault model is one permanent stuck-at fault on a randomly selected flattened-netlist wire, whose fan-out can create multiple downstream faults (p.234). The checker detects errors whose compared mantissa difference exceeds 7; for X=7, an undetected error can be about 5.5% of the maximum mantissa value (p.234). Fault-free truncation/rounding discrepancies are accepted, but a false-alarm rate is not reported (pp.232-234).
conditions: A shorter checker mantissa reduces checker cost but increases the maximum error that can escape detection (p.232). Checking is disabled for infinity, NaN, and denorm cases, which reduces cost while permitting undetected errors in those cases (p.234). Transient faults were excluded because masking made statistically significant evaluation impractical (p.234). The reported 17.8% area and 28% total-power overheads apply to the combined multiplier-and-adder FPU rather than the multiplier alone (p.235).
evidence: §II-III and Figure 1, pp.232-234; §IV-V and Figures 2-3, pp.234-235; §VI and Table 1, p.235; §VII, p.235.

## new_families
none

## space_gaps
* `reduced_precision.replica_width_bits` excludes 7, the implemented checker mantissa length, and its meaning does not distinguish total checker width from mantissa width (p.234).
* `reduced_precision` lacks a choice for the allowed mantissa comparison difference; this implementation uses 7 (p.234).
* `reduced_precision` lacks a policy for bypassing infinity/NaN/denorm cases (p.234).

## open_questions
* The document reports 7 as the checker mantissa length rather than the total checker width, so the intended interpretation of `replica_width_bits` remains ambiguous.
* Multiplier-only area and power overheads are not reported separately from the combined multiplier-and-adder FPU.
