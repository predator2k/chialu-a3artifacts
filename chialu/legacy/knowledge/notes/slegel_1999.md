---
handle: slegel_1999
citation: T. J. Slegel et al., "IBM's S/390 G5 Microprocessor Design", IEEE Micro, vol. 19, no. 2, pp. 12-23, 1999
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU, other]
formats: [int64, bcd8, hfp32, hfp64, hfp128, fp32, fp64, fp128]
authority: incremental
pages_read: 12-23 / 12
---

## summary
The document describes the 500-MHz IBM S/390 G5 processor and its arithmetic/reliability facilities. Complete duplication of the instruction/execution units provides per-cycle error detection, while checkpointed hardware recovery handles detected transient errors (pp.19-20). The execution unit includes binary/decimal arithmetic and an FPU that converts BFP operands to HFP for computation (pp.15-18).

## families
### duplication  (role: instantiates)
mechanism: The I unit and E unit are completely duplicated. The R unit and L1 cache cross-compare signals from both copies, including instruction results, on every clock cycle; a mismatch invokes hardware error recovery (p.20).
choices:
  replication: 2   # p.20
  comparison_point: per_cycle   # p.20
  temporal_stagger: false   # p.20
new_choices:
  recovery_trigger: cross_compare_mismatch — Specifies the event that invokes recovery.   # p.20
slots:
  comparator: UNKNOWN   # p.20
parameters: Two complete I-unit/E-unit copies; comparison every clock cycle   # p.20
results: none
errors_and_checks: The processor recovery algorithm is described as essentially 100% effective for any transient processor error; false-alarm behavior is not reported.   # p.20
conditions: Complete duplication avoids placing traditional checking logic in arithmetic critical paths but costs additional die area; the paper gives no duplication-area number. Traditional checking consumed an estimated 20% to 30% of logic in earlier mainframes.   # p.20
evidence: Figure 2 (p.14); “Processor hardware error recovery” (p.20)

### commercial_decimal_fpu  (role: instantiates)
mechanism: The fixed-point unit contains an 8-digit decimal adder and a decimal multiplier. Division uses hardware that generates one quotient digit and a millicode routine that iterates the operation; dedicated control executes the remaining decimal instructions in hardware (pp.15-16).
choices:
  implementation: millicode_with_assists   # p.16
  datapath_width_digits: 8 [outside domain]   # p.15
new_choices:
  none
slots:
  significand_adder: UNKNOWN   # p.15
  multiplier: UNKNOWN   # p.16
  divider: decimal_digit_recurrence   # p.16
parameters: 8-digit decimal adder; one quotient digit per division iteration; multiplier width/latency/II UNKNOWN   # pp.15-16
results: none
errors_and_checks: none
conditions: Decimal add/subtract/compare, multiply, and other decimal instructions execute in hardware; complete division still requires an iterative millicode routine.   # pp.15-16
evidence: “I unit and E unit” (pp.15-16)

### decimal_digit_recurrence  (role: instantiates)
mechanism: Dedicated hardware generates one decimal quotient digit, and a millicode routine iterates that operation to complete decimal division (p.16).
choices:
new_choices:
  none
slots:
  digit_select: UNKNOWN   # p.16
parameters: 1 quotient digit per iteration; quotient digit set/radix/iteration count UNKNOWN   # p.16
results: none
errors_and_checks: none
conditions: The recurrence depends on millicode for the complete division operation.   # p.16
evidence: “I unit and E unit” (p.16)

## new_families
### internal_format_fp_interop  (domain: fp: floating-point datapaths, closest: shift_round_convert, why_not: shift_round_convert covers FP-to-integer conversion rather than execution of one FP format through another format’s arithmetic core.)
mechanism: BFP operands are converted to HFP after Areg/Breg, all floating-point arithmetic is performed in HFP format, and results are converted and rounded to BFP before Creg. Hardware handles 32-, 64-, and 128-bit formats and special-case operands without millicode (p.18).
choices: external_format: {hfp, bfp, both}; internal_arithmetic_format: {hfp, bfp}; conversion_placement: {operand_and_result_boundaries}
results:
| metric | value | unit | technology / device | baseline | condition | page |
| throughput | one | result per cycle | IBM CMOS 6X, 0.25-micron; 1999 | none reported | HFP operands | p.18 |
| latency | three | cycles | IBM CMOS 6X, 0.25-micron; 1999 | none reported | HFP operands | p.18 |
| throughput | two | cycles per result | IBM CMOS 6X, 0.25-micron; 1999 | none reported | BFP operands | p.18 |
| latency | five | cycles | IBM CMOS 6X, 0.25-micron; 1999 | none reported | BFP operands | p.18 |
evidence: Table 1 (p.17); “IEEE floating-point architecture” (pp.17-18)

### checkpointed_hardware_recovery  (domain: checker: concurrent error detection, closest: duplication, why_not: duplication detects disagreement, while this mechanism restores state after errors detected by duplication, parity, ECC, or control checks.)
mechanism: The R unit freezes its checkpoint, committed stores drain to L2, critical latches/arrays reset, and ECC-corrected R-unit registers repopulate shadow state. A serialization interrupt restarts execution; another error before successful completion or an uncorrectable register error causes check-stop (p.20).
choices: checkpoint_location: {dedicated_recovery_unit}; state_repair: {ecc_read_correct_rewrite}; restart: {serialization_interrupt}; failure_action: {check_stop}
results:
| metric | value | unit | technology / device | baseline | condition | page |
| recovery effectiveness | essentially 100% | transient processor errors | IBM CMOS 6X, 0.25-micron; 1999 | none reported | processor transient errors | p.20 |
| recovery latency | several thousand | clock cycles | IBM CMOS 6X, 0.25-micron; 1999 | none reported | any detected processor hardware error | p.20 |
evidence: “R unit” (p.16); “Processor hardware error recovery” (p.20)

## space_gaps
* commercial_decimal_fpu.datapath_width_digits lacks the documented 8-digit value.   # p.15
* duplication lacks a recovery-policy choice for checkpoint freeze/ECC repair/restart/check-stop behavior.   # p.20
* The checker vocabulary lacks generic parity/ECC protection for arrays and register files.   # pp.16,20
* The checker vocabulary lacks automatic cache-line/set deletion and spare-word-line replacement for solid array faults.   # pp.20-21

## open_questions
* The paper does not identify the binary adder, decimal adder, decimal multiplier, quotient-selection, or comparison-circuit topology.
* The paper does not quantify the area overhead of complete I-unit/E-unit duplication.
* The paper does not separate the die-area cost of BFP conversion/support from the rest of the FPU.
