---
handle: richards_1955#s09
parent: richards_1955
citation: Richards, "Arithmetic Operations in Digital Computers", Van Nostrand, 1955
chapter: DECIMAL ADDITION AND SUBTRACTION
pdf_pages: 220-257
status: ok
kind: book_chapter
unit_classes: [BINARY_ALU, other]
formats: [8,4,2,1 decimal, excess-3, 5,4,2,1 decimal, biquinary, 2,4,2,1 decimal, 9's complement, 10's complement]
authority: textbook
pages_read: 38 / 38
---

## summary
The chapter classifies decimal addition by combinational adders/counters and by parallel/serial handling of digits and bits. It defines binary-assisted adders for 8,4,2,1/excess-3/5,4,2,1 codes, error checking through redundancy or biquinary coding, several counter-carry mechanisms, and direct/complement decimal subtraction. The chapter gives component/path counts but no technology-bound measurements.

## families
### bcd_direct_addition  (role: taxonomizes)
mechanism: Decimal digits enter a coded combinational adder with a carry from the next lower decimal order. Binary-compatible codes use binary half/full adders followed by code-dependent correction: 8,4,2,1 adds 6 after a decimal carry, excess-3 adds 13 without a decimal carry or 3 with one, and 5,4,2,1 adds 3 or equivalently subtracts 5. Digit-propagate logic bypasses binary-order carry paths when the uncarried digit sum is 9.
choices:
  digit_code: bcd8421   # p.221
  digit_code: excess3   # p.227
  digit_code: 5,4,2,1 [outside domain]   # p.229
  digit_code: biquinary [outside domain]   # p.236
  correction_placement: postsum_plus6   # p.222
  correction_placement: postsum_code_dependent_correction [outside domain]   # p.227
  carry_scheme: ripple   # p.223
new_choices:
  carry_propagation_cell: binary_order_path | digit_propagate_and_or — selects ordinary binary carry traversal or a one-“and”/one-“or” decimal propagate path   # p.223
  correction_value: 0_or_6 | 3_or_13 | add_3_or_subtract_5 — selects the correction required by the digit code   # p.224
slots:
  digit_adder: ripple_carry   # p.222
parameters: minimum 9 input lines and 5 output lines for a 4-bit decimal code   # p.220
results:
| metric | value | unit | technology / device | baseline | condition | page |
| input lines | 9 | lines | abstract | minimum | 4-bit decimal code | p.220 |
| output lines | 5 | lines | abstract | minimum | 4-bit decimal code | p.220 |
| propagated-carry path | one “and” switch and one “or” switch | switches | abstract | two full adders | 8,4,2,1 sum of 9 | p.224 |
| component count | two inverters and seven full adders | components | abstract | UNKNOWN | excess-3 adder | p.228 |
| propagated-carry path | one “and” switch and one “or” switch | switches | abstract | four binary orders | excess-3 sum of 9 | p.229 |
| direct-table sum detections | thirty | input pairs | abstract | UNKNOWN | one code bit set for digits 2, 4, and 9 | p.230 |
| carry-generating pairs | forty-five | input pairs | abstract | UNKNOWN | decimal addition table | p.231 |
errors_and_checks: none
conditions: Binary addition techniques apply readily to 8,4,2,1/excess-3/5,4,2,1 codes.   # p.221, p.227, p.229
conditions: Direct switching-table implementations for other codes require many components and generally compete poorly with binary techniques.   # p.230, p.231
evidence: Decimal Adders; Figs. 8-1 through 8-6; Table 8-I   # p.220, p.230

### parity_prediction_adder  (role: analyzes)
mechanism: A redundancy bit records the odd/even count of ones in each coded decimal digit. The predicted sum redundancy is formed independently from the two input redundancy bits and the carries, including the relevant effect of the corrective 6. A second redundancy bit is formed from the produced sum, and a half adder compares the two bits.
choices:
  parity_groups: 1   # p.231
  carry_scheme: duplicate_carry   # p.235
  interleaving: UNKNOWN   # p.231
new_choices:
  parity_convention: redundancy_bit_1_for_even — defines the chapter’s usual redundancy-bit polarity   # p.231
slots:
  comparator: two_rail_tree   # p.234
  carry_replica: UNKNOWN   # p.235
parameters: 4 digit bits plus 1 redundancy bit   # p.232
results:
| metric | value | unit | technology / device | baseline | condition | page |
| parallel parity count capacity | two | signals | abstract | half adder | half-adder sum output | p.232 |
| parallel parity count capacity | three | signals | abstract | full adder | full-adder sum output | p.232 |
errors_and_checks: Separately generated carries prevent a carry fault from corrupting both the sum and predicted redundancy, but some faults change the carry count by an even number and escape detection.   # p.235, p.236
conditions: Complete checking requires enough additional logic that full adder duplication with bit-by-bit comparison is probably as attractive.   # p.236
evidence: Redundancy Bits for Checking Addition; Figs. 8-7 and 8-8   # p.231, p.235

### self_checking_datapath  (role: instantiates)
mechanism: The biquinary adder separately combines one-hot quinary parts and two-line binary parts. Both “carry” and “no carry” signals participate in sum formation. A single switch failure or an invalid input produces an invalid number of active quinary lines or an invalid carry/no-carry pair.
choices:
  encoding: biquinary_one_hot_plus_carry_no_carry [outside domain]   # p.239
new_choices:
  checked_output_code: one_of_five_plus_one_of_two — checks the quinary sum and complementary carry outputs   # p.239
slots:
  comparator: UNKNOWN   # p.241
parameters: 5 quinary sum lines and 2 carry-status lines   # p.239
results:
| metric | value | unit | technology / device | baseline | condition | page |
| detectable output multiplicity | none or two | active signals | abstract | one valid signal | individual switch failure or invalid input | p.239 |
errors_and_checks: Any individual “and”/“or” switch failure is detectable; correction is unavailable, and two or more simultaneous failures may escape.   # p.239
conditions: An odd/even checker is sufficient for the original circuit’s single-error objective, but the component-reduced form requires a one-and-only-one checker because three active outputs can occur.   # p.239, p.241
evidence: Checking Addition Through the Use of an Error-detecting Code; Figs. 8-9 and 8-10   # p.236, p.241

## taxonomy
* Decimal addition devices   # p.220
  * steady-state adder   # p.220
    * 8,4,2,1 adder
      * binary addition plus corrective 6 -> bcd_direct_addition   # p.221
      * high-speed digit-propagate carry -> bcd_direct_addition   # p.223
      * Boolean/component-reduced form -> bcd_direct_addition   # p.224
    * excess-3 adder
      * correction by 3 or 13 -> bcd_direct_addition   # p.227
      * high-speed digit-propagate carry -> bcd_direct_addition   # p.228
    * 5,4,2,1 adder
      * add 3 or subtract 5 correction -> bcd_direct_addition   # p.229
      * high-speed digit-propagate carry -> bcd_direct_addition   # p.230
    * arbitrary-code addition-table switching -> bcd_direct_addition   # p.230
    * redundancy-bit checked 8,4,2,1 adder -> parity_prediction_adder   # p.231
    * error-detecting biquinary adder -> self_checking_datapath   # p.236
  * decimal digit counter accumulator -> decimal_counter_accumulator   # p.241
    * stored carry followed by carry pulse -> decimal_counter_accumulator   # p.242
    * immediately propagated carry-storage output -> decimal_counter_accumulator   # p.243
    * carry-gate ripple -> decimal_counter_accumulator   # p.244
    * automatic carry initiation without carry storage -> decimal_counter_accumulator   # p.245
    * “leaving 9” carry for intermediate-state counters -> decimal_counter_accumulator   # p.247
* Operand handling   # p.248
  * parallel digit, parallel bit -> bcd_direct_addition   # p.248
  * serial digit, parallel bit -> bcd_direct_addition   # p.248
  * parallel digit, serial pulse -> decimal_counter_accumulator   # p.248
  * serial digit, serial pulse -> decimal_counter_accumulator   # p.248
  * serial 8,4,2,1 bit-entry arrangement -> decimal_counter_accumulator   # p.249
* Decimal subtraction   # p.250
  * direct subtraction
    * decimal subtracter with borrow and corrective subtraction of 6 -> decimal_direct_subtraction   # p.250
    * reversible decimal counter -> decimal_direct_subtraction   # p.251
  * addition of complements
    * 10’s-complement addition with discarded carry -> decimal_complement_subtraction   # p.252
    * 9’s-complement addition with end-around carry -> decimal_complement_subtraction   # p.253
    * 9’s-complement subtraction with end-around borrow -> decimal_complement_subtraction   # p.254
    * timed-pulse true/complement generator -> decimal_complement_subtraction   # p.255
    * self-complementing counter -> decimal_counter_accumulator   # p.256

## primary_sources
none

## new_families
### decimal_counter_accumulator  (domain: decimal: decimal adders, closest: bcd_direct_addition, why_not: The mechanism accumulates pulse counts in decimal-state counters rather than forming coded digits with combinational adders.)
mechanism: Each decimal order has a ten-state counter. Digit value is represented by a pulse count, and transition through 9 to 0 generates a carry. Variants store carries for a later carry pulse, propagate stored-carry state immediately, ripple under a carry gate, initiate carries without storage, or use the signal produced when leaving 9.
choices: carry_storage: stored | automatic; carry_transfer: carry_pulse | propagated_state | carry_gate; carry_event: arriving_zero | leaving_nine; digit_parallelism: parallel | serial   # p.241, p.248
results:
| metric | value | unit | technology / device | baseline | condition | page |
| delay-device count | none | delay devices | abstract | pulse-propagation methods | carry-gate method | p.245 |
| propagated-carry delay path | one D1 and one D2 | delay devices | abstract | cumulative delay | automatic carry initiation | p.246 |
| counter output reduction | one | output line eliminated | abstract | separate 0 and 9 outputs | “leaving 9” carry | p.247 |
evidence: Figs. 8-11 through 8-16   # p.242, p.249

### decimal_direct_subtraction  (domain: decimal: decimal adders, closest: bcd_direct_addition, why_not: The vocabulary has no decimal subtracter or borrow-propagation family.)
mechanism: A decimal subtracter accepts two coded digits and a borrow, produces a coded difference and decimal borrow, and applies code-dependent correction. For 8,4,2,1 digits, four binary full subtracters form the uncorrected difference; a borrow from the 8-order becomes the decimal borrow, and a borrowed result is corrected by subtracting 6.
choices: implementation: combinational_subtracter | reversible_counter; correction: subtract_6; complement_output: tens_complement | nines_complement_end_around_borrow   # p.250, p.251
results:
| metric | value | unit | technology / device | baseline | condition | page |
| input lines | 9 | lines | abstract | minimum | 4-bit decimal code | p.250 |
| output lines | 5 | lines | abstract | minimum | 4-bit decimal code | p.250 |
evidence: Decimal Subtraction; Direct Subtraction   # p.250, p.251

### decimal_complement_subtraction  (domain: decimal: decimal adders, closest: end_around_carry, why_not: Decimal 9’s/10’s-complement subtraction is not covered by the binary/modular modulus choices.)
mechanism: Subtraction is converted to decimal addition by complementing the subtrahend. A 10’s-complement operation discards the highest carry. A 9’s-complement operation returns the highest carry to the lowest order. The absence of the highest carry indicates a negative complement-form result; end-around borrow provides a variant that keeps positive zero in true form.
choices: complement: nines | tens; circulation: discard_carry | end_around_carry | end_around_borrow; zero_convention: positive_zero | negative_zero_allowed; complement_generation: subtract_from_power | nines_plus_one | trailing_zero_scan | timed_pulse | self_complementing_counter   # p.252, p.256
results:
| metric | value | unit | technology / device | baseline | condition | page |
| timed complement pulse train | nine | source pulses | abstract | UNKNOWN | one-out-of-ten timed input | p.255 |
evidence: Subtraction by the Addition of Complements through Self-complementing Counters   # p.252, p.257

### one_hot_validity_checker  (domain: checker: two-rail / self-checking, closest: two_rail_tree, why_not: The circuit recognizes exactly one active line rather than validity of a two-rail codeword.)
mechanism: A switching network indicates whether one and only one signal is active among the checked outputs. The construction expands to any number of input lines and is required when a component-reduced biquinary adder can produce three active outputs after a fault.
choices: accepted_count: exactly_one; input_lines: Int[2..N]   # p.241
results:
| metric | value | unit | technology / device | baseline | condition | page |
| accepted active signals | one and only one | signals | abstract | odd-count checker | component-reduced biquinary adder | p.241 |
evidence: Fig. 8-10   # p.240, p.241

## space_gaps
* `bcd_direct_addition.digit_code` lacks 5,4,2,1 and biquinary values.   # p.229, p.236
* `bcd_direct_addition` lacks code-dependent correction values 3/13 and add-3/subtract-5.   # p.227, p.230
* `self_checking_datapath.encoding` lacks biquinary one-hot plus carry/no-carry coding.   # p.239
* The decimal vocabulary lacks counter-based addition and decimal direct/complement subtraction families.   # p.241, p.250

## open_questions
* The chapter does not give a component count for the simplified 8,4,2,1 adder in Fig. 8-4.   # p.227
* The chapter does not identify the separate carry generator used by redundancy prediction as a named binary-adder topology.   # p.235
