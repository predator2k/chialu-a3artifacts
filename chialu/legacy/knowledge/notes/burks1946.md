---
handle: burks1946
citation: A. W. Burks, H. H. Goldstine, J. von Neumann, "Preliminary Discussion of the Logical Design of an Electronic Computing Instrument", Institute for Advanced Study report, 1946 (reprinted in B. Randell, The Origins of Digital Computers, Springer).
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [binary40_fixed_point]
authority: landmark
pages_read: 15 / 15 supplied pages (pp.399-413)
---

## summary
The report specifies a parallel binary machine with 40-digit fixed-point words and built-in addition/subtraction/multiplication/division, although the supplied pages do not specify their circuit structures. The report analyzes Newton refinement for reciprocal/division and proposes synchronized whole-machine duplication for concurrent error detection. The report also proposes detecting unused operation codes in the control decoder.

## families
### newton_raphson  (role: analyzes)
mechanism: An estimate X of 1/a is refined with X' = 2X - aX², so the new error 1 - aX' equals (1 - aX)². An initial estimate accurate to 2^-5 is obtained from a small table of 2^4 entries. Three iterations use six multiplications to produce a result accurate to 2^-40, after which multiplication by b produces b/a. (p.407)
choices:
  iterations: 3   # p.407
new_choices:
  none
slots:
  seed: monolithic_rom [input_bits=4, function=reciprocal]   # p.407
  iter_mult: UNKNOWN   # p.407
  final_round: UNKNOWN   # p.407
parameters: initial estimate precision 2^-5; target precision 2^-40; 3 iterations; 6 refinement multiplications; 1 final multiplication for b/a   # p.407
results:
| metric | value | unit | technology / device | baseline | condition | page |
| reciprocal latency | 6 | multiplication times | UNKNOWN (1946) | initial estimate accurate to 2^-5 | 3 iterations; final result good to 2^-40 | p.407 |
| quotient latency | 7 | multiplication times | UNKNOWN (1946) | reciprocal method above | forms b/a after reciprocal refinement | p.407 |
errors_and_checks: The recurrence squares the preceding reciprocal error; the stated initial error scale is 2^-5 and the stated final accuracy is 2^-40. Rounding behavior is UNKNOWN.   # p.407
conditions: A dedicated divider is justified only if division takes a good deal less than 7 multiplication times. The proposed machine includes such a faster divider because its additional equipment beyond the multiplier is described as unimportant.   # p.407
evidence: §5.4, p.407

### duplication  (role: proposes)
mechanism: Two identical computers operate in parallel under the same clock and automatically compare selected state. The proposed checking circuit compares the Selectron register and accumulator, with accumulator-only comparison considered possible, and stops the clock or machine when a discrepancy appears. The retained flip-flop state then supports stepwise fault localization. (pp.412-413)
choices:
  replication: 2   # p.412
  comparison_point: per_cycle   # p.412
  temporal_stagger: false   # p.412
new_choices:
  comparison_scope: selectron_register_and_accumulator; accumulator_only_tentative — identifies which duplicated state is compared   # p.412
slots:
  comparator: UNKNOWN   # p.412
parameters: 2 identical synchronized computers; comparison at the Selectron register and accumulator, possibly accumulator only; single-pulse diagnostic clock mode   # pp.412-413
results:
| metric | value | unit | technology / device | baseline | condition | page |
errors_and_checks: The method checks the computation at every checked point, detects transient and steady-state errors, and stops the machine when a discrepancy occurs. Detection coverage and false-alarm behavior are UNKNOWN.   # p.412
conditions: The two machines may operate separately for problems with adequate mathematical checks and operate in parallel for first runs or fault localization. Duplicating only the arithmetic unit or following an operation with its complement fails to check memory/control.   # p.412
evidence: §6.5, pp.412-413

## new_families
### invalid_opcode_detector  (domain: checker, closest: duplication, why_not: This mechanism validates control-code membership rather than comparing replicated arithmetic results.)
mechanism: A six-input decoding function table produces outputs for operation codes. Outputs corresponding to unused operation codes may be connected to a checking circuit that indicates when the control receives an unintelligible code word. (pp.409-410)
choices: code_width_bits: {6}; checked_codes: {unused_operation_codes}; response: {indication}
results: none
evidence: §6.3, pp.409-410

## space_gaps
* `duplication` lacks a choice for the compared state/register scope, which the report varies between Selectron-register-plus-accumulator and accumulator-only checking.   # p.412
* The checker vocabulary lacks control-code validity checking for unused operation codes.   # pp.409-410

## open_questions
* The supplied pages do not specify the carry-propagation family used for the 40-digit binary adder.   # pp.404, 407
* The physical implementation and output width of the reciprocal seed table are unspecified.   # p.407
* The duplication comparator circuit and exact sampling cadence are unspecified.   # p.412
