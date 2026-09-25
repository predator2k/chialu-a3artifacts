---
handle: busaba_2001
citation: Busaba, Krygowski, Li, Schwarz, Carlough, "The IBM z900 Decimal Arithmetic Unit", 35th Asilomar Conference on Signals, Systems and Computers, 2001
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU, other]
formats: [bcd8421, packed_decimal, zoned_decimal, int32, int64]
authority: landmark
pages_read: 1335-1339 / 5
---

## summary
The paper describes the IBM z900 decimal arithmetic engine, which combines a 64-bit binary/decimal adder with conversion-assist hardware inside the fixed-point unit (pp.1335-1336). The decimal adder supports addition/subtraction and supplies the iterative datapath for decimal multiplication/division, while separate tables accelerate packed/zoned and binary/decimal conversions (pp.1336-1339).

## families
### commercial_decimal_fpu  (role: instantiates)
mechanism: The fixed-point unit executes variable-length signed-decimal arithmetic as multicycle operations. A 64-bit combined binary/decimal adder performs addition/subtraction, generates decimal multiples for multiplication, and performs repeated subtraction for division. A decimal-assist macro supplies packed/zoned conversion and chunked binary/decimal conversion. The entire fixed-point unit is replicated for error detection and fault isolation. # pp.1335-1339
choices:
  implementation: hardware_dfu  # pp.1335-1336
  datapath_width_digits: 16  # p.1336
  shared_with_binary_fpu: true  # p.1336
new_choices:
  optimization_target: common_business_workload_cases — leading-zero detection and operand selection reduce iterations for typical data # pp.1337-1339
slots:
  significand_adder: bcd_direct_addition [digit_code=bcd8421, correction_placement=presum_plus6]  # pp.1336-1337
  multiplier: iterative_decimal_multiplication [multiplier_digit_recoding=none, digits_per_cycle=1]  # pp.1337-1338
  divider: decimal_digit_recurrence [quotient_digit_set=nonredundant_0_9, digit_split=none, divisor_prescaling=false]  # p.1338
parameters: 64-bit decimal/binary adder; 64-bit decimal-assist macro; variable-length operands; multicycle execution  # pp.1335-1336
results:
| metric | value | unit | technology / device | baseline | condition | page |
| chip frequency at introduction | 770 | MHz | 0.18 um CMOS 8s / IBM z900 / 2000 | none | whole microprocessor | p.1335 |
| laboratory frequency | over a gigahertz | UNKNOWN | 0.18 um CMOS 8s / IBM z900 / 2000 | none | whole microprocessor | p.1335 |
errors_and_checks: The fixed-point unit is replicated for error detection and fault isolation; coverage and false-alarm behavior are not reported. # p.1335
conditions: Decimal results are limited to the first-operand length; lost nonzero high digits set condition code 3 and may cause a decimal-overflow interruption. # pp.1335-1336
evidence: §§3-5; Fig. 1; instruction sequences in §§4.1-4.5

### bcd_direct_addition  (role: instantiates)
mechanism: Two digitwise presum paths calculate sums and carry outputs for assumed carry-ins of 0 and 1. A digit carry network generates hot carries for 16 presums, after which multiplexers select the proper presum. Decimal addition conditionally includes +6, while decimal subtraction conditionally applies -6. Input multiplexers also support binary addition/subtraction, ten's complementation, masking, and sign insertion. # pp.1336-1337
choices:
  digit_code: bcd8421  # pp.1335-1336
  correction_placement: presum_plus6  # pp.1336-1337
new_choices:
  presum_paths: carry_in_0_and_1 — each digit computes alternatives before the decimal carry is known # p.1336
slots:
  digit_adder: UNKNOWN  # p.1336
parameters: 64 bits; 16 BCD digits; AP/SP process 15 digits in the first cycle and up to 16 digits in the second cycle  # pp.1336-1337
results: none
errors_and_checks: none
conditions: The digit carry network uses low Vt devices, while the presum logic obtains the same performance with normal Vt devices. # p.1336
evidence: §3.1; Fig. 1; §4.1

### iterative_decimal_multiplication  (role: instantiates)
mechanism: The instruction counts significant digits and iterates over the operand requiring fewer iterations. The decimal adder precomputes W, 2W, 4W, 6W, and 8W in the local register file. Each multiplier digit selects or derives a multiple, shifts that partial product by 4j bits, and accumulates it into P. Leading zeros are ignored. # pp.1337-1338
choices:
  multiple_set: precomputed_1x_2x_4x_6x_8x [outside domain]  # pp.1337-1338
  multiplier_digit_recoding: none  # p.1337
  digits_per_cycle: 1  # pp.1337-1338
new_choices:
  iteration_operand_selection: fewer_significant_digits — iteration may switch between operands according to significant-digit counts # p.1337
slots:
  accumulator: UNKNOWN  # p.1338
  final_adder: bcd_direct_addition  # pp.1337-1338
parameters: multiplier at most 15 digits plus sign; one digit per iteration; result cases split at 15 significant digits  # pp.1337-1338
results:
| metric | value | unit | technology / device | baseline | condition | page |
| operand-read/control work | 5 | cycles | 0.18 um CMOS 8s / IBM z900 / 2000 | none | initial steps | p.1338 |
| multiple generation | 4 | cycles | 0.18 um CMOS 8s / IBM z900 / 2000 | none | generate stored multiples | p.1338 |
| iteration latency | 2.4 | cycles average | 0.18 um CMOS 8s / IBM z900 / 2000 | none | result has 15 significant digits or less | p.1338 |
| iteration latency | 4.4 | cycles average | 0.18 um CMOS 8s / IBM z900 / 2000 | none | result exceeds 15 significant digits | p.1338 |
| result alignment/storage | 1 to 3 | cycles | 0.18 um CMOS 8s / IBM z900 / 2000 | none | after accumulation | p.1338 |
errors_and_checks: Operand restrictions are checked to prevent product overflow; violations cause a data exception. # p.1337
conditions: Odd multiples 3W, 5W, 7W, and 9W require an additional add cycle, while six of ten digit multiples are already stored. # p.1338
evidence: §4.2

### decimal_digit_recurrence  (role: instantiates)
mechanism: A restoring recurrence generates one quotient digit per iteration by repeatedly subtracting the divisor until the remainder becomes negative, taking the quotient digit as the number of subtractions minus one. The remainder is then restored, shifted by one decimal digit, and merged with the next dividend digit. # p.1338
choices:
  quotient_digit_set: nonredundant_0_9  # p.1338
  digit_split: none  # p.1338
  divisor_prescaling: false  # p.1338
new_choices:
  digit_selection_method: repeated_subtraction — the quotient digit is determined from the subtraction count # p.1338
slots:
  digit_select: UNKNOWN  # p.1338
parameters: one quotient digit per iteration; up to 9 subtractions per quotient digit  # p.1338
results: none
errors_and_checks: none
conditions: Subtracting divisor multiples could reduce the iteration count, but the paper reports increased control complexity and decimal-adder carryout fanout. # p.1338
evidence: §4.3

### binary_decimal_conversion  (role: instantiates)
mechanism: Binary-to-decimal conversion maps 12-bit chunks through three parallel tables and combines 4-digit decimal chunks by Horner evaluation with multiplication by 4096. Decimal-to-binary conversion maps 3-digit decimal chunks to 10-bit binary values and combines them by Horner evaluation with multiplication by 1000. Leading-zero detection determines the required iteration count in both directions. # pp.1336, 1338-1339
choices:
  direction: both  # pp.1338-1339
  structure: constant_multiply  # pp.1338-1339
new_choices:
  conversion_frontend: parallel_lookup_tables — three tables convert each input chunk before Horner accumulation # pp.1336, 1338-1339
slots:
  none
parameters: binary-to-decimal uses 12 binary bits per step and produces 4 decimal digits; decimal-to-binary uses 3 decimal digits per step and produces 10 binary bits  # pp.1336, 1338-1339
results:
| metric | value | unit | technology / device | baseline | condition | page |
| multiply by 4096 | 4 | cycles | 0.18 um CMOS 8s / IBM z900 / 2000 | none | binary-to-decimal, except final oversized multiply | p.1339 |
| final multiply by 4096 | 9 | cycles | 0.18 um CMOS 8s / IBM z900 / 2000 | none | result exceeds 64-bit FXU dataflow | p.1339 |
| typical binary-to-decimal conversion | 1 | iteration | 0.18 um CMOS 8s / IBM z900 / 2000 | none | typical small-magnitude workload data | p.1339 |
| maximum decimal-to-binary conversion | 11 | iterations | 0.18 um CMOS 8s / IBM z900 / 2000 | none | 31-digit input | p.1339 |
| typical decimal-to-binary conversion | 1 or 2 | iterations | 0.18 um CMOS 8s / IBM z900 / 2000 | none | actual workloads | p.1339 |
| multiply by 1000 | 3 | cycles | 0.18 um CMOS 8s / IBM z900 / 2000 | none | decimal-to-binary iteration | p.1339 |
errors_and_checks: CVB/CVBG may cause a fixed-point-divide exception when the binary result does not fit the specified length. # p.1339
conditions: A 12-bit binary chunk balances iteration count against conversion-hardware area and cycle time. # p.1339
evidence: §3.2; §§4.4-4.5

### decimal_encoding_codec  (role: instantiates)
mechanism: Dedicated pack/unpack hardware converts as many as 32 decimal digits between zoned and packed representations. Decimal arithmetic consumes and produces packed operands, while zoned format supports input/editing/output uses. # pp.1335-1337
choices:
  significand_encoding: packed_bcd_and_zoned [outside domain]  # pp.1335-1336
  codec_placement: inside_operation  # pp.1335-1337
new_choices:
  conversion_pair: zoned_packed — the hardware converts both directions between the two S/390 encodings # pp.1335-1337
slots:
  none
parameters: up to 32 decimal digits per packed/zoned conversion  # p.1337
results: none
errors_and_checks: none
conditions: Arithmetic is performed in packed format; zoned format is primarily used for human-readable input/editing/output. # pp.1335-1336
evidence: §§1-3.2

### duplication  (role: instantiates)
mechanism: The complete fixed-point unit, including the decimal arithmetic engine, is replicated for concurrent error detection and fault isolation. # p.1335
choices:
  replication: 2  # p.1335
new_choices:
  none
slots:
  comparator: UNKNOWN  # p.1335
parameters: two fixed-point-unit instances  # p.1335
results: none
errors_and_checks: The paper states error detection and fault isolation but gives no fault model, detection coverage, comparison point, alias rate, or false-alarm behavior. # p.1335
conditions: The replication applies to the whole fixed-point unit rather than only the decimal engine. # p.1335
evidence: §1

## new_families
none

## space_gaps
* `iterative_decimal_multiplication.multiple_set` lacks the implemented W/2W/4W/6W/8W stored-multiple set. # pp.1337-1338
* `binary_decimal_conversion` lacks independent binary-chunk and decimal-chunk widths for asymmetric bidirectional converters. # pp.1338-1339
* `decimal_encoding_codec.significand_encoding` lacks packed BCD and zoned decimal. # pp.1335-1337
* `decimal_digit_recurrence` lacks repeated-subtraction quotient-digit selection. # p.1338
* `bcd_direct_addition` lacks the dual-presum carry-in-0/carry-in-1 organization. # p.1336

## open_questions
* The paper does not identify the topology used by the 16-digit carry network. # p.1336
* The paper reports whole-chip frequency/power/transistor data but no decimal-unit area, power, or standalone delay. # p.1335
* The paper does not state the comparator structure or comparison point used by the replicated fixed-point units. # p.1335
