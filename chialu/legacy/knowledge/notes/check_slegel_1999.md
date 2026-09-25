---
handle: check_slegel_1999
citation: M. A. Check, T. J. Slegel, "Custom S/390 G5 and G6 Microprocessors", IBM Journal of Research and Development, vol. 43, no. 5/6, pp. 671-680, 1999
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU, other]
formats: [ESA/390 integer, hexadecimal floating-point, IEEE 754 binary floating-point, packed decimal, zoned decimal]
authority: incremental
pages_read: 671-680 / 10
---

## summary
The document describes the G5/G6 S/390 processor architecture, including hardware-controlled decimal multiplication/conversion, an iterative decimal-divide assist, and duplicated execution units for error detection and recovery (pp. 676, 679-680). The G5 duplicates the IU/FXU/FPU while protecting the single cache/RU with result comparison, ECC, and parity (p. 679). The document reports processor-level implementation data but no arithmetic-unit area/delay or checker-coverage measurements (pp. 671-672, 679-680).

## families
### commercial_decimal_fpu  (role: instantiates)
mechanism: The G5 implements decimal multiplication entirely under hardware control and uses a lookup table to generate partial products. A hardware divide assist produces one quotient digit, and millicode invokes the assist iteratively for the full quotient. Dedicated hardware executes CVB/CVD and PACK/UNPK conversions (p. 676).
choices:
  implementation: hardware_with_millicode_assists [outside domain]   # p.676
new_choices:
  operation_implementation: per_operation_hardware_or_millicode_assist — selects full hardware control or an iterated hardware assist for each decimal operation   # p.676
slots:
  divider: decimal_digit_recurrence   # p.676
parameters: one quotient digit per divide-assist invocation; multiplier instruction entirely under hardware control   # p.676
results: none reported
errors_and_checks: none
conditions: Decimal multiplication is hardware-controlled, whereas decimal division requires a millicode loop around the quotient-digit assist (p. 676). The paper does not identify the multiplier reduction structure or quotient-digit selection method (p. 676).
evidence: Instruction performance enhancements, p.676.

### decimal_digit_recurrence  (role: instantiates)
mechanism: A hardware assist produces one decimal quotient digit. Millicode iterates the assist to produce the complete quotient (p. 676).
choices:
new_choices:
  control_placement: millicode_loop — places full-quotient iteration control in millicode around the hardware digit step   # p.676
slots:
  digit_select: UNKNOWN   # p.676
parameters: one quotient digit per hardware-assist invocation; iteration count UNKNOWN   # p.676
results: none reported
errors_and_checks: none
conditions: The document does not state the quotient digit set, digit splitting, divisor prescaling, or selection circuit (p. 676).
evidence: Instruction performance enhancements, p.676.

### binary_decimal_conversion  (role: instantiates)
mechanism: Dedicated hardware executes CONVERT TO BINARY (CVB) and CONVERT TO DECIMAL (CVD). Separate PACK and UNPACK instructions convert between zoned and packed decimal formats (p. 676).
choices:
  direction: both   # p.676
new_choices:
  format_repacking: zoned_and_packed — supports hardware conversion between the two documented decimal data formats   # p.676
slots:
  none
parameters: digits_per_step UNKNOWN; conversion latency UNKNOWN   # p.676
results: none reported
errors_and_checks: none
conditions: CVB/CVD and PACK/UNPK operate under complete hardware control, but the conversion structure is not disclosed (p. 676).
evidence: Instruction performance enhancements, p.676.

### duplication  (role: instantiates)
mechanism: The processor contains duplicated IU/FXU/FPU copies. The single cache and RU compare results arriving from the replicated units. A mismatch indicates a possible error, after which the processor resets, restores protected state, and resumes processing. Mirrored instruction units also cross-check BTB array outputs (p. 679).
choices:
  replication: 2   # p.679
  comparison_point: result_receipt_at_cache_and_RU [outside domain]   # p.679
new_choices:
  replication_scope: IU_FXU_FPU — identifies which processor units are duplicated   # p.679
  mismatch_recovery: reset_restore_resume — resets the processor, restores protected state, and resumes processing after an error   # p.679
  permanent_array_recovery: disable_failed_BTB_sets — disables one or both failed BTB sets and continues in a degraded mode   # pp.679-680
slots:
  comparator: UNKNOWN   # p.679
parameters: two IU copies; two FXU copies; two FPU copies; one cache; one RU   # p.679
results: none reported
errors_and_checks: The cache and RU detect mismatches in results from duplicated units, but the paper reports no coverage/alias/false-alarm values (p. 679). The cache uses ECC for unique data and parity for other data, while the RU uses ECC for processor state (p. 679). A second BTB error within a technology-dependent interval classifies the fault as permanent (pp. 679-680).
conditions: The cache and RU are single-copy structures rather than duplicated units (p. 679). A detected transient BTB error is handled by clearing the array (p. 679). A permanent BTB failure disables the affected set or sets, permits performance-degraded operation, and causes a spare processor to replace the defective processor at the next IML (pp. 679-680).
evidence: RAS improvements and BTB array errors, pp.679-680.

## new_families
none

## space_gaps
* `commercial_decimal_fpu.implementation` lacks a value for mixed full-hardware operations and millicode-controlled hardware assists (p. 676).
* `duplication.comparison_point` lacks comparison at result receipt by single-copy cache/RU structures (p. 679).
* `duplication` lacks choices for replication scope and reset/restore/resume recovery (p. 679).
* `duplication` lacks an array-specific clear/retry/disable recovery policy (pp. 679-680).

## open_questions
* The document does not establish whether the decimal multiplier is iterative or parallel, so the `commercial_decimal_fpu.multiplier` slot remains unresolved.
* The document does not state whether the G5 retains the G4 eight-digit decimal adder.
* The document does not specify the decimal divider's quotient digit set, prescaling, or QDS implementation.
* The document does not specify the checker circuit, exact comparison timing, fault model, detection coverage, or false-alarm rate.
