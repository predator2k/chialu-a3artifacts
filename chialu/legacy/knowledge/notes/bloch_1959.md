---
handle: bloch_1959
citation: E. Bloch, "The Engineering Design of the Stretch Computer", Proc. Eastern Joint Computer Conference, pp. 48-58, 1959.
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU, other]
formats: [int1-64, stretch_fp_single, stretch_fp_double, decimal1-21]
authority: landmark
pages_read: 48-58 / 11
---

## summary
The paper describes the IBM Stretch arithmetic system, including its floating-point adder/multiplier/divider, variable-field serial unit, decimal hardware, and concurrent checking. The arithmetic units overlap exponent/mantissa work and process several multiplier or quotient bits per cycle. # pp.51-54

## families
### carry_lookahead  (role: instantiates)
mechanism: The 96-bit floating-point carry-propagate adder uses carry look-ahead over four bits at a time. # p.52
choices:
  group_size: 4   # p.52
new_choices:
  none
slots:
  none
parameters: 96-bit adder; single- and double-precision floating-point operations. # p.52
results:
| metric | value | unit | technology / device | baseline | condition | page |
| adder delay | 150 | mμsec | IBM Stretch current-switching logic (1959) | UNKNOWN | 96-bit binary-number addition | p.52 |
errors_and_checks: none
conditions: The adder performs one's-complement addition/subtraction with automatic end-around carry. # p.52
evidence: Arithmetic Units; Fig. 8. # pp.52-53

### end_around_carry  (role: instantiates)
mechanism: The floating-point adder performs all additions and subtractions in one's-complement form and automatically returns the end-around carry. # p.52
choices:
  recirculation: automatic_end_around_carry [outside domain]   # p.52
new_choices:
  none
slots:
  none
parameters: 96-bit floating-point mantissa datapath. # p.52
results: none
errors_and_checks: none
conditions: The paper does not identify the carry recirculation circuit or prefix topology. # p.52
evidence: Parallel Arithmetic Unit; Fig. 8. # p.52

### single_path  (role: instantiates)
mechanism: One double-length 96-bit shifter/adder datapath handles single- and double-precision floating-point operations. The serial arithmetic unit performs exponent arithmetic while the parallel unit performs mantissa multiplication/division. # pp.52-53
choices:
  none
new_choices:
  none
slots:
  sig_adder: carry_lookahead [group_size=4]   # p.52
  exp: exponent_path   # p.53
  align: bounded_align   # p.52
parameters: 96-bit shifter/adder; shifts up to 4 positions right or 6 positions left per operation; larger shifts use successive operations. # p.52
results:
| metric | value | unit | technology / device | baseline | condition | page |
| floating add | 1.0 | USEC | IBM Stretch current-switching logic (1959) | IBM 704: 84 USEC | Stretch floating point | p.54 |
| parallel-unit datapath | 32,700 | transistors | IBM Stretch current-switching logic (1959) | UNKNOWN | shared floating-point/multiply/divide unit | p.54 |
| parallel-unit controls | 3,000 | transistors | IBM Stretch current-switching logic (1959) | UNKNOWN | shared floating-point/multiply/divide unit | p.54 |
| parallel-unit share | 21.0 | % OF TOTAL | IBM Stretch current-switching logic (1959) | UNKNOWN | shared floating-point/multiply/divide unit | p.54 |
errors_and_checks: Arithmetic is checked by parity, duplication, or casting out three; assignment by operation is UNKNOWN. # pp.52-53
conditions: Floating-add time depends on pre-shift/post-shift cycles; the discussion reports that 80 per cent of numbers are handled within six shifting cycles. # p.58
evidence: Arithmetic Units; Figs. 8-10; discussion. # pp.52-54, p.58

### booth_recoded_parallel  (role: instantiates)
mechanism: Each cycle processes 12 multiplier bits as four three-bit groups. Each group is decoded with the lowest-order bit of the next higher group to select a signed even multiple of the multiplicand. Four carry-save adders reduce the four multiples and prior partial product to product-sum/product-carry form before final carry propagation. # pp.52-53
choices:
  booth_radix: 8   # p.52
new_choices:
  recoded_bits_per_cycle: 12 — multiplier bits handled in one cycle   # p.52
  groups_per_cycle: 4 — three-bit groups decoded concurrently   # p.52
slots:
  reduction: csa_reduction_tree   # p.53
parameters: 48-bit floating-point mantissa; 12 multiplier bits/cycle; four three-bit groups; four carry-save adders. # pp.52-54
results:
| metric | value | unit | technology / device | baseline | condition | page |
| floating MPY | 1.8 | USEC | IBM Stretch current-switching logic (1959) | IBM 704: 204 USEC | Stretch floating point | p.54 |
| binary MPY | 10.0 | USEC | IBM Stretch current-switching logic (1959) | UNKNOWN | variable field, 1 TO 64 bits | p.54 |
errors_and_checks: Arithmetic checking method for multiplication is UNKNOWN among parity/duplication/casting out three. # p.53
conditions: The multiply time is worst-case; exponent arithmetic overlaps mantissa processing. # pp.53,58
evidence: Parallel Arithmetic Unit; Figs. 8 and 10; discussion. # pp.52-54, p.58

### duplication  (role: instantiates)
mechanism: The serial arithmetic procedure is repeated in a duplicate unit and compared. Machine arithmetic checks overlap execution of the next instruction. # pp.52-53
choices:
  replication: 2   # p.52
  comparison_point: per_cycle   # p.52
new_choices:
  none
slots:
  comparator: UNKNOWN
parameters: duplicate serial arithmetic unit; extraction/arithmetic/reinsertion occurs in one clock cycle. # p.52
results:
| metric | value | unit | technology / device | baseline | condition | page |
| checking hardware | 24,500 | transistors | IBM Stretch current-switching logic (1959) | UNKNOWN | all checking hardware, not duplication alone | p.54 |
| checking share | 14.5 | % OF TOTAL | IBM Stretch current-switching logic (1959) | UNKNOWN | all checking hardware, not duplication alone | p.54 |
errors_and_checks: Fault model, detection coverage, false-alarm behavior, and comparator implementation are UNKNOWN. # pp.52-54
conditions: The paper explicitly assigns duplication/comparison to the serial unit but does not map every arithmetic operation to a checking method. # pp.52-53
evidence: Serial Arithmetic Unit; Checking; Fig. 9. # pp.52-54

### residue  (role: instantiates)
mechanism: Some internal arithmetic operations are checked by a “casting out three” process, overlapped with the next instruction. # p.53
choices:
  modulus: 3   # p.53
new_choices:
  none
slots:
  comparator: UNKNOWN
parameters: UNKNOWN
results: none
errors_and_checks: Detection coverage, alias rate, protected operations, generator structure, and comparison point are UNKNOWN. # p.53
conditions: The paper does not distinguish which operations use casting out three rather than parity or duplication. # p.53
evidence: Checking. # p.53

### commercial_decimal_fpu  (role: instantiates)
mechanism: Stretch provides hardware variable-field decimal arithmetic. Decimal add-type operations use the serial unit's extracted field, carry-propagate adder, and output binary-to-decimal correction unit; decimal multiply/divide datapaths are not described. # p.52
choices:
  implementation: hardware_dfu   # p.52
new_choices:
  none
slots:
  significand_adder: UNKNOWN
  multiplier: UNKNOWN
  divider: UNKNOWN
parameters: 1 TO 21 digits; Fig. 10 timings are for 5 digits. # p.54
results:
| metric | value | unit | technology / device | baseline | condition | page |
| decimal ADD | 3.5 | USEC | IBM Stretch current-switching logic (1959) | IBM 705: 119 USEC | 5 digits | p.54 |
| decimal MPY | 40.0 | USEC | IBM Stretch current-switching logic (1959) | IBM 705: 799 USEC | 5 digits | p.54 |
| decimal DIVIDE | 65.0 | USEC | IBM Stretch current-switching logic (1959) | IBM 705: 4828 USEC | 5 digits | p.54 |
| decimal LOAD/STORE | 3.2 | USEC | IBM Stretch current-switching logic (1959) | IBM 705: 204 USEC | 5 digits | p.54 |
errors_and_checks: Decimal-operation checking method is UNKNOWN among parity/duplication/casting out three. # p.53
conditions: The decimal digit code, correction formula, multiplication algorithm, and division algorithm are not stated. # pp.52-54
evidence: Arithmetic Units; Figs. 7 and 10. # pp.52-54

## new_families
### variable_field_slice_arithmetic  (domain: adder, closest: ripple_carry, why_not: Existing adder families do not represent field extraction/alignment/reinsertion through a narrow reusable slice.)
mechanism: A switch matrix extracts 16 consecutive bits from each 128-bit register pair. A wrap-around circuit aligns the field's low-order bit at the right, a carry-propagate adder or logic unit processes the slice, and an inverse matrix reinserts the result without disturbing neighboring positions. Extraction, arithmetic, and reinsertion complete in one clock cycle. # p.52
choices: slice_width_bits: Int[1..128:1]; alignment: {wrap_around_low_bit_right}; post_adder_processing: {true_complement, binary_to_decimal_correction}
results:
| metric | value | unit | technology / device | baseline | condition | page |
| binary ADD/LOAD/STORE | 2.0 | USEC | IBM Stretch current-switching logic (1959) | UNKNOWN | variable field, 1 TO 64 bits | p.54 |
| serial-unit datapath | 10,000 | transistors | IBM Stretch current-switching logic (1959) | UNKNOWN | complete shared serial datapath | p.54 |
| serial-unit controls | 8,700 | transistors | IBM Stretch current-switching logic (1959) | UNKNOWN | complete shared serial unit | p.54 |
| serial-unit share | 10.5 | % OF TOTAL | IBM Stretch current-switching logic (1959) | UNKNOWN | complete shared serial unit | p.54 |
evidence: Serial Arithmetic Unit; Figs. 7, 9, and 10. # pp.52-54

### string_skipping_multiple_division  (domain: dividers / square root, closest: restoring_nonrestoring, why_not: The quotient advances by a variable number of bits using divisor multiples and skips over strings of both ones and zeros.)
mechanism: The divider selects 1, 3/2, or 3/4 times a normalized divisor and skips strings of quotient ones and zeros. The method produces a variable number of quotient bits at each subtraction and overlaps mantissa division with exponent arithmetic. # p.53
choices: divisor_multiple_set: {{1, 3/4, 3/2}}; string_skip: {ones_and_zeros}; quotient_bits_per_subtraction: variable; normalized_divisor_required: Bool
results:
| metric | value | unit | technology / device | baseline | condition | page |
| quotient generation | 48 | bits in thirteen machine cycles | IBM Stretch current-switching logic (1959) | most nonrestoring machines: 48 cycles for 48 quotient bits | normalized divisor | p.53 |
| average quotient generation | 3.7 | quotient bits per subtraction | IBM Stretch current-switching logic (1959) | UNKNOWN | normalized divisor | p.53 |
| floating DIV | 7.0 | USEC | IBM Stretch current-switching logic (1959) | IBM 704: 216 USEC | Stretch floating point | p.54 |
| binary DIVIDE | 15.0 | USEC | IBM Stretch current-switching logic (1959) | UNKNOWN | variable field, 1 TO 64 bits | p.54 |
evidence: Divide scheme and worked examples; Fig. 10. # pp.53-54

## space_gaps
* `csa_reduction_tree` is a permitted slot value but has no declared family choices; Stretch implements a four-adder carry-save reduction network. # pp.52-53
* A generic parity-checking family is absent; Stretch parity-checks switch matrices without describing adder parity prediction. # pp.52-53
* `bounded_align` and `exponent_path` are permitted slot values without family definitions, while Stretch describes bounded repeated shifting and a concurrent exponent unit. # pp.52-53
* `end_around_carry.recirculation` lacks the document's `automatic_end_around_carry` implementation value. # p.52

## open_questions
* The paper does not state the look-ahead adder's intergroup carry scheme or number of levels. # p.52
* The paper does not state how signed multiplicand multiples are generated or encoded. # pp.52-53
* The paper does not identify which arithmetic operations use parity, duplication, or casting out three. # p.53
* The paper does not describe the decimal multiplication/division algorithms or decimal digit code. # pp.52-54
