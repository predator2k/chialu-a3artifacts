---
handle: ercegovac_1992
citation: Ercegovac, Lang, "On-the-Fly Rounding", IEEE Transactions on Computers, 1992
actual_citation: same
status: ok
kind: paper
unit_classes: [other]
formats: [radix_r_signed_digit, sign_magnitude]
authority: landmark
pages_read: 1497-1503 / 7
---

## summary
The paper incorporates rounding into on-the-fly conversion for digit-recurrence division/square root/left-to-right multiplication and online arithmetic. Three methods trade rounding error against remainder-sign detection time/hardware. Every method avoids carry-propagate addition in the rounding step.

## families
### generalized_signed_digit  (role: extends)
mechanism: Signed-digit result digits are converted most-significant-first using conditional forms Q[k] and QM[k] = Q[k] - r^-k. Concatenation and conditional register loading replace carry/borrow propagation. Rounding adds the conditional form QP[k] = Q[k] + r^-k and selects among Q[n]/QM[n]/QP[n] after one extra recurrence digit. # p.1498-1499
choices:
  final_conversion: on_the_fly   # p.1497-1499
new_choices:
  rounding_during_conversion: {exact_sign, no_sign, estimated_sign} — selects the remainder information used during conversion/rounding   # p.1497, p.1500-1502
slots:
  none
parameters: radix r; digits p_k in {-a,...,a}, a ≤ r-1; Q/QM registers for conversion; Q/QM/QP registers for general rounding; one extra result digit; radix-2 and radix-4 examples   # p.1498-1502
results:
| metric | value | unit | technology / device | baseline | condition | page |
| conversion carry propagation | none | UNKNOWN | UNKNOWN / 1992 | traditional carry-propagate conversion | conditional concatenation/loading | p.1498 |
errors_and_checks: Conversion itself is exact; the rounding contract depends on the selected rounding method. # p.1498-1502
conditions: The scheme supports sequential and combinational linear-array implementations. # p.1497-1498 A carry-propagate adder remains necessary if the conventional remainder value is required. # p.1498
evidence: §II, (2.1)-(2.6), Fig. 1, Tables I-II, p.1498-1499; §III, (3.2)-(3.5), Fig. 2, Tables III-IV, p.1499-1500

### online_arithmetic_unit  (role: extends)
mechanism: The rounding methods consume a most-significant-digit-first signed-digit result stream and update conventional conditional forms as each digit is produced. The paper states that the same conversion/rounding process applies to online arithmetic operations, although it does not instantiate a complete online operator. # p.1497, p.1502
choices:
new_choices:
  result_rounding: {exact_sign, no_sign, estimated_sign} — chooses exact IEEE rounding, unbiased larger-error rounding, or bounded estimated-sign rounding   # p.1497, p.1500-1502
slots:
  none
parameters: generic radix r; signed-digit result stream; one additional result digit; optional b-bit remainder-sign estimate   # p.1497-1501
results:
| metric | value | unit | technology / device | baseline | condition | page |
| rounding carry-propagate additions | none | UNKNOWN | UNKNOWN / 1992 | conventional restoration/increment rounding | all three methods | p.1502 |
errors_and_checks: Method 1 provides IEEE rounding to nearest; Methods 2 and 3 provide unbiased alternatives with larger bounded errors. # p.1497, p.1500-1502
conditions: The extension applies to online operations that produce signed digits most-significant-first. # p.1497, p.1502 The paper does not specify online delay/radix/digit-set choices for a complete operator. # p.1497-1502
evidence: Introduction, p.1497-1498; §VII, p.1502

## new_families
### on_the_fly_rounding  (domain: redundant: online arithmetic, closest: online_arithmetic_unit, why_not: online_arithmetic_unit describes the streaming operator rather than its redundant-to-conventional rounding mechanism)
mechanism: Three methods select a rounded n-digit result from Q[n], QM[n], and QP[n]. Method 1 uses the exact final-remainder sign and zero test for IEEE rounding to nearest. Method 2 omits remainder inspection and selects solely from p_(n+1), producing unbiased but larger error. Method 3 applies Method 1 with a sign estimate from the b most-significant remainder bits. Conditional-form selection absorbs decrement/increment operations, so rounding requires no carry-propagate addition. # p.1497, p.1499-1502
choices:
  sign_handling: {exact_remainder_sign, no_sign_detection, estimated_b_msb}   # p.1497, p.1500-1501
  tie_handling: {jam_to_even, balanced_error_choice}   # p.1499-1501
  sign_detector: {existing_cpa, carry_skip_network, carry_lookahead_network, msb_estimate}   # p.1499-1501
  imprecise_flag: Bool   # p.1501
results:
| metric | value | unit | technology / device | baseline | condition | page |
| rounding error | (1/2)r^-n | UNKNOWN | UNKNOWN / 1992 | exact rounding to nearest | Method 1 | p.1502 |
| rounding error bound | ±2^-n | UNKNOWN | UNKNOWN / 1992 | rounding to nearest | Method 2, radix 2 | p.1501 |
| rounding error bound | r^-n(2^-1 + 2^-b) | UNKNOWN | UNKNOWN / 1992 | rounding to nearest | Method 3 using b remainder bits | p.1501 |
| error difference | less than 1% | % | UNKNOWN / 1992 | rounding to nearest | Method 3, radix 2, b = 8 | p.1501 |
| sign-estimation time | one short cycle | cycles | UNKNOWN / 1992 | about four cycles for complete sign detection | Method 3, radix 2, b = 8 | p.1501 |
| complete sign-detection time | about four cycles | cycles | UNKNOWN / 1992 | one short cycle for eight-bit estimate | example comparison | p.1501 |
evidence: §III, (3.1)-(3.8), Figs. 2-3, Tables III-IV, p.1498-1500; §IV, (4.1)-(4.4), Table V, p.1500-1501; §V, p.1501; §VII, p.1502

## space_gaps
* Digit-recurrence division/square-root/left-to-right multiplication and `online_arithmetic_unit` lack a result-conversion/rounding slot for `on_the_fly_rounding`. # p.1497, p.1502
* `generalized_signed_digit.final_conversion` records on-the-fly conversion but cannot distinguish unrounded conversion from the three rounding methods. # p.1497-1502

## open_questions
* The paper provides no technology/device, area, clock period, or absolute hardware-delay result.
* The paper says other IEEE rounding schemes can be implemented similarly but does not specify their rules or hardware. # p.1498
* The paper does not fix a radix/digit set or complete online-operator architecture for general deployment. # p.1497-1502
