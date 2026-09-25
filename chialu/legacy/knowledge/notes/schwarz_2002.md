---
handle: schwarz_2002
citation: E. M. Schwarz, M. A. Check, C.-L. K. Shum, et al., "The Microarchitecture of the IBM eServer z900 Processor", IBM Journal of Research and Development, vol. 46, no. 4/5, pp. 381-395, 2002
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU, other]
formats: [int32, int64, bcd]
authority: landmark
pages_read: 381-395 / 15
---

## summary
The paper describes the shipped IBM eServer z900 processor, including a 64-bit fixed-point unit and hardware implementations of decimal addition, multiplication, division, and binary/decimal conversion. The decimal adder computes correction candidates in parallel, while decimal multiplication and restoring division use operand-dependent iterations. The z900 also protects a replicated instruction unit, parity-protected arrays, and ECC-protected recovery state.

## families
### bcd_direct_addition  (role: instantiates)
mechanism: The 64-bit decimal adder handles 16-digit BCD addition, subtraction, and comparison in one cycle. The adder performs binary addition and decimal correction substantially in parallel. Two pre-sum adders, a 16-digit carry network, and ±6 correction logic produce four candidate sums per digit, which the carry network selects. p.393
choices:
  digit_code: bcd8421   # p.393
  correction_placement: presum_plus6   # p.393
new_choices:
  parallel_correction_candidates: four_per_digit — A+B+0, A+B+1, A+B+6+0, and A+B+6+1 are formed for addition, with corresponding −6 candidates for subtraction.   # p.393
slots:
  digit_adder: UNKNOWN   # p.393
parameters: 64-bit; 16 BCD digits; one-cycle addition/subtraction/compare   # p.393
results:
| metric | value | unit | technology / device | baseline | condition | page |
| latency | 1 | cycle | 0.18 μm CMOS / z900 (2000) | UNKNOWN | 64-bit or 16-digit BCD addition, subtraction, and comparison | p.393 |
errors_and_checks: none
conditions: The design uses four candidate results per digit and requires a digit-carry network to select the correct candidate.   # p.393
evidence: §6, “Decimal adder,” p.393; Figure 8, p.392

### speculative_decimal_addition  (role: instantiates)
mechanism: The decimal adder precomputes corrected and uncorrected digit sums before the carry network resolves each digit’s carry. The carry network then selects among four candidate sums for every digit, which places the ±6 correction substantially in parallel with binary addition. p.393
choices:
  speculation_target: digit_correction   # p.393
  recovery: dual_path_select   # p.393
new_choices:
  subtraction_correction: plus_or_minus_6 — subtraction precomputes uncorrected and −6-corrected candidates.   # p.393
slots:
  carry_network: UNKNOWN   # p.393
parameters: 64-bit; 16 BCD digits; four candidate sums per digit   # p.393
results:
| metric | value | unit | technology / device | baseline | condition | page |
| latency | 1 | cycle | 0.18 μm CMOS / z900 (2000) | UNKNOWN | decimal addition, subtraction, and comparison | p.393 |
errors_and_checks: none
conditions: The paper does not identify the topology of the digit-carry network.   # p.393
evidence: §6, “Decimal adder,” p.393

### iterative_decimal_multiplication  (role: instantiates)
mechanism: The hardware algorithm selects its iteration count from the significant-digit counts of both operands. The unit generates multiples of the multiplicand, stores the multiples in the register file, and iterates over multiplier digits with partial-product accumulate-and-shift operations. p.393
choices:
  digits_per_cycle: 1   # p.393
new_choices:
  iteration_count_basis: operand_significant_digits — the number of iterations depends on the significant-digit counts of both operands.   # p.393
slots:
  accumulator: UNKNOWN   # p.393
  final_adder: UNKNOWN   # p.393
parameters: decimal operands; one multiplier digit examined per iteration; latency UNKNOWN   # p.393
results:
| metric | value | unit | technology / device | baseline | condition | page |
| average cycle reduction | one half to one third | G6 cycle count | 0.18 μm CMOS / z900 (2000) | G6 hardware-assisted millicode | decimal multiplication and division moved to complete hardware execution | p.393 |
errors_and_checks: none
conditions: Latency depends on the number of significant digits in both operands. The paper does not state the generated multiple set or multiplier-digit recoding.   # p.393
evidence: §6, “Decimal multiplication and division,” p.393

### decimal_digit_recurrence  (role: instantiates)
mechanism: The hardware divider uses restoring division. Each iteration generates one quotient digit by repeated subtraction, and as many as nine subtractions may be required to determine a quotient digit. The iteration count depends on the significant-digit counts of both operands. p.393
choices:
  quotient_digit_set: nonredundant_0_9   # p.393
new_choices:
  recurrence_style: restoring — each quotient digit is found with a restoring repeated-subtraction algorithm.   # p.393
  iteration_count_basis: operand_significant_digits — the total iteration count depends on the significant-digit counts of both operands.   # p.393
slots:
  digit_select: UNKNOWN   # p.393
parameters: one quotient digit per iteration; up to nine subtractions per quotient digit; total latency UNKNOWN   # p.393
results:
| metric | value | unit | technology / device | baseline | condition | page |
| average cycle reduction | one half to one third | G6 cycle count | 0.18 μm CMOS / z900 (2000) | G6 hardware-assisted millicode | decimal multiplication and division moved to complete hardware execution | p.393 |
errors_and_checks: none
conditions: The paper does not state divisor prescaling, digit splitting, or the quotient-selection circuit.   # p.393
evidence: §6, “Decimal multiplication and division,” p.393

### binary_decimal_conversion  (role: instantiates)
mechanism: Decimal-to-binary conversion maps three decimal digits through three lookup tables and combines the outputs with a three-input binary adder. Binary-to-decimal conversion maps a 12-bit binary value through three table lookups and combines the results with a BCD adder. p.393
choices:
  direction: both   # p.393
  structure: parallel_table_lookup_add [outside domain]   # p.393
  digits_per_step: 3   # p.393
new_choices:
  none
slots:
  none
parameters: three decimal digits to a 10-bit binary number in one cycle; 12-bit binary value to three BCD digits; three lookup tables per direction   # p.393
results:
| metric | value | unit | technology / device | baseline | condition | page |
| decimal-to-binary throughput | 3 | decimal digits per cycle | 0.18 μm CMOS / z900 (2000) | UNKNOWN | output is a 10-bit binary number | p.393 |
| binary-to-decimal input width | 12 | bits per conversion step | 0.18 μm CMOS / z900 (2000) | UNKNOWN | output is three BCD digits | p.393 |
errors_and_checks: none
conditions: The paper reports one-cycle latency explicitly for decimal-to-binary conversion but not for the reverse conversion.   # p.393
evidence: §6, “Decimal conversion hardware,” p.393

### commercial_decimal_fpu  (role: instantiates)
mechanism: The z900 moves decimal multiplication and division from hardware-assisted millicode into complete hardware execution within the fixed-point unit. A widened 64-bit decimal adder supports 16-digit BCD operations, while dedicated control and decimal-assist hardware support multiplication, division, and binary/decimal conversion. pp.391-393
choices:
  implementation: hardware_dfu   # pp.391-393
  datapath_width_digits: 16   # pp.392-393
new_choices:
  none
slots:
  significand_adder: speculative_decimal_addition   # p.393
  multiplier: iterative_decimal_multiplication   # p.393
  divider: decimal_digit_recurrence   # p.393
parameters: 64-bit decimal adder; 16 BCD digits; multiply/divide latency depends on significant digits   # pp.392-393
results:
| metric | value | unit | technology / device | baseline | condition | page |
| average cycle reduction | one half to one third | G6 cycle count | 0.18 μm CMOS / z900 (2000) | G6 hardware-assisted millicode | decimal multiplication and division | p.393 |
errors_and_checks: none
conditions: The fixed-point unit executes packed-decimal arithmetic rather than IEEE decimal floating point.   # pp.391-393
evidence: §6, pp.391-393; Figures 8-9, pp.392-393

### duplication  (role: instantiates)
mechanism: The z900 instruction unit is replicated, but the branch target buffer is placed outside the replicated unit. The branch target buffer uses parity for soft array failure detection, and each set can be disabled independently after a hard failure so operation continues in a degraded mode. p.387
choices:
new_choices:
  excluded_shared_arrays: branch_target_buffer — a large array is excluded from replication and protected separately with parity.   # p.387
slots:
  comparator: UNKNOWN   # p.387
parameters: replication count UNKNOWN; 8K-entry branch target buffer; four independently disableable sets   # p.387
results: none
errors_and_checks: Parity protects the branch target buffer against soft array failures. Hard failures permit independent set disabling and degraded operation; detection coverage, comparison behavior, and false-alarm behavior are not reported.   # p.387
conditions: Moving the branch target buffer outside the replicated instruction unit saves silicon area.   # p.387
evidence: §3, p.387

## new_families
none

## space_gaps
* `binary_decimal_conversion.structure` lacks a parallel lookup-table-plus-adder value for the conversion hardware described on p.393.
* `decimal_digit_recurrence` lacks a recurrence-style choice that can record the restoring repeated-subtraction algorithm on p.393.
* The checker vocabulary lacks generic parity-protected arrays with independent set disabling and degraded operation, as used for the branch target buffer on p.387.

## open_questions
* The topology and family of the decimal digit-carry network are not identified on p.393.
* The decimal multiplier’s generated multiple set, digit recoding, accumulator organization, and final adder are not identified on p.393.
* The decimal divider’s quotient-selection circuit, prescaling behavior, and exact cycle counts are not identified on p.393.
* The replicated instruction unit’s replication count, comparison point, comparator, and recovery protocol are not identified on p.387.
