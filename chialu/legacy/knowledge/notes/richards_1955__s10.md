---
handle: richards_1955#s10
parent: richards_1955
citation: Richards, "Arithmetic Operations in Digital Computers", Van Nostrand, 1955
chapter: DECIMAL MULTIPLICATION AND DIVISION
pdf_pages: 258-296
status: ok
kind: book_chapter
unit_classes: [other]
formats: [decimal, 8,4,2,1 coded decimal, biquinary coded decimal]
authority: textbook
pages_read: 39 / 39
---

## summary
The chapter taxonomizes decimal multiplication/division methods by digit manipulation, stored/generated multiples, trial digits, and iterative approximation. The chapter compares these methods mainly by average additions/subtractions per multiplier or quotient digit and describes decimal round-off/error-detecting mechanisms.   # p.258, p.272, p.284, p.290, p.294

## families
### iterative_decimal_multiplication  (role: taxonomizes)
mechanism: Multiplier digits are handled one at a time. A partial product is obtained from a stored digit table, repeated addition/subtraction, or generated multiplicand multiples; the partial product is accumulated in its decimal orders. Doubling/quintupling/quadrupling and complement recoding reduce the required accumulation operations.   # p.259, p.261, p.263, p.268, p.271
choices:
  multiple_set: full_1x_to_9x   # p.268
  multiplier_digit_recoding: signed_digit_m5_p5   # p.262
  digits_per_cycle: 1   # p.259
new_choices:
  product_generation: {stored_digit_table, switching_array, repeated_add_subtract, generated_multiple} — selects how each digit-controlled partial product is formed   # p.259, p.261, p.268
  available_easy_multiples: {1, 2, 4, 5, all_1_to_9} — selects the multiplicand multiples supplied directly or by cascaded units   # p.264, p.266, p.268
  multiplier_digit_order: {ascending, descending} — changes accumulator length and complement handling   # p.273
slots:
  accumulator: UNKNOWN   # p.260
  final_adder: UNKNOWN   # p.261
parameters: multiplier digits handled one at a time; 10-digit by 8-digit table multiplication example; 80 operations for pairwise sequential lookup   # p.259
results:
| metric | value | unit | technology / device | baseline | condition | page |
| operations | 80 | operations | abstract | UNKNOWN | 10-digit multiplicand and 8-digit multiplier, sequential pair products | p.259 |
| additions | multiplier digits + 1 | additions | abstract | two additions per multiplier digit | separate simultaneous left/right accumulators plus final combination | p.261 |
| time saved | approaches 50% | percent | abstract | separate sequential component accumulation | multipliers of many digits | p.261 |
| average operations | 4.5 | operations per multiplier digit | abstract | UNKNOWN | addition only, random digits | p.272 |
| average operations | 2.5 | operations per multiplier digit | abstract | addition only | addition and subtraction, random digits | p.272 |
| average operations | 2.5 | operations per multiplier digit | abstract | addition only | addition and doubling, random digits | p.272 |
| average operations | 2.5 | operations per multiplier digit | abstract | addition only | addition and quintupling, random digits | p.272 |
| average operations | 1.7 | operations per multiplier digit | abstract | addition only | addition, doubling, and quintupling | p.272 |
| average operations | 1.5 | operations per multiplier digit | abstract | addition only | addition, subtraction, and doubling | p.272 |
| average operations | 1.7 | operations per multiplier digit | abstract | addition only | addition, subtraction, and quintupling | p.272 |
| average operations | 1.3 | operations per multiplier digit | abstract | addition only | addition, subtraction, doubling, and quintupling | p.272 |
| average operations | 1.2 | operations per multiplier digit | abstract | addition only | addition, subtraction, doubling, and quadrupling | p.272 |
| average operations | 1.4 | operations per multiplier digit | abstract | addition only | addition, doubling, quadrupling, and quintupling | p.272 |
| average operations | 0.9 | operations per multiplier digit | abstract | addition only | N-tupling, random digits | p.272 |
errors_and_checks: A biquinary N-tupler can preserve one-of-two/one-of-five validity, so a circuit error is eventually transmitted to a checked product digit.   # p.274, p.277
conditions: Separate left/right accumulation saves time because both component streams proceed simultaneously.   # p.261
evidence: Table 9-1; Figs. 9-1 through 9-5; Table 9-II; sections “The Decimal Multiplication Table” through “Error-detecting Multiplier”   # p.259-p.277

### decimal_digit_recurrence  (role: taxonomizes)
mechanism: Each quotient digit is determined by subtracting aligned divisor multiples from the current remainder. Variants restore negative remainders, switch between subtraction and addition after a sign change, use easy divisor multiples, compare all nine multiples, or select and correct a trial quotient digit.   # p.279, p.281, p.283, p.286, p.287
choices:
  quotient_digit_set: nonredundant_0_9   # p.279
  digit_split: none   # p.279
  divisor_prescaling: false   # p.279
new_choices:
  quotient_selection: {repeated_subtraction, alternating_add_subtract, easy_multiple_sequence, nine_parallel_compares, trial_digit_table} — selects the quotient-digit determination procedure   # p.281, p.283, p.286, p.288
  trial_digit_correction: {none, add_or_subtract_divisor} — corrects an overestimated or underestimated trial digit   # p.289
slots:
  digit_select: qds_table   # p.288
parameters: one decimal quotient digit per recurrence step; trial selection may inspect one leading digit or two leading digits   # p.288, p.289
results:
| metric | value | unit | technology / device | baseline | condition | page |
| average operations | 6.3 | operations per quotient digit | abstract | UNKNOWN | subtract and restore, random quotient digits | p.282 |
| average operations | 5.4 | operations per quotient digit | abstract | subtract and restore | shift and add after a negative remainder | p.284 |
| average operations | 5.4 | operations per quotient digit | abstract | subtract and restore | simple quintupled-divisor method | p.284 |
| average operations | 3.8 | operations per quotient digit | abstract | subtract and restore | divisor and quintupled divisor sequence | p.284 |
| average operations | 4.0 | operations per quotient digit | abstract | subtract and restore | doubling with addition/subtraction | p.285 |
| average operations | 3.4 | operations per quotient digit | abstract | subtract and restore | doubling and quintupling with addition/subtraction | p.285 |
| throughput | 1.0 | operation per quotient digit | abstract | subtract and restore | all nine multiples compared in parallel | p.286 |
| trial-digit error | 1 | quotient digit | IBM Type 602, year UNKNOWN | UNKNOWN | two leading dividend/divisor digits and 23 table combinations | p.289 |
errors_and_checks: A remainder-sign test detects a wrong trial digit and correction adds/subtracts the divisor while decrementing/incrementing the quotient digit.   # p.289
conditions: Parallel comparison requires nine comparing circuits and generated divisor multiples, while serial digit handling overlaps comparison with the preceding subtraction.   # p.286
evidence: sections “Division” through “Division Through the Use of Trial Quotient Digits”; Tables 9-III and associated operation tables   # p.279-p.289

### decimal_newton  (role: analyzes)
mechanism: The reciprocal is refined with either bk+1 = bk(2 - xbk) or bk+1 = bk[3(1 - xbk) + (xbk)^2], after which the reciprocal is multiplied by the dividend. Successive approximations may be subtracted to test whether the allowed reciprocal error has been reached.   # p.290
choices:
  operation: divide   # p.290
  seed_digits: UNKNOWN   # p.290
  iterations: UNKNOWN   # p.290
new_choices:
  iteration_order: {second_order, third_order} — determines whether correct digits approximately double or triple per application   # p.290
slots:
  seed: UNKNOWN   # p.290
  final_round: UNKNOWN   # p.290
parameters: b0 greater than zero and less than 2/x   # p.290
results:
| metric | value | unit | technology / device | baseline | condition | page |
| convergence order | second order | correct-digit growth | abstract | UNKNOWN | bk+1 = bk(2 - xbk) | p.290 |
| convergence order | third order | correct-digit growth | abstract | UNKNOWN | bk+1 = bk[3(1 - xbk) + (xbk)^2] | p.290 |
errors_and_checks: Completion occurs when the difference between successive approximations is less than the allowed reciprocal error.   # p.290
conditions: The initial approximation must satisfy 0 < b0 < 2/x or the series does not converge.   # p.290
evidence: section “Division by Iteration—First Method”   # p.290

### goldschmidt  (role: taxonomizes)
mechanism: Numerator and divisor approximations are multiplied by the same factor, 2 - Di, so their ratio remains unchanged while Di approaches 1 and Ni approaches the quotient. The second method replaces the factor by 1 + di from leading nonnine digits; the third method uses successively wider digit groups approximating Di - 1.   # p.290-p.293
choices:
  iterations: 4   # p.292
  internal_guard_bits: 1 to 2   # p.291
  truncated_intermediate_multiplies: UNKNOWN   # p.291
new_choices:
  factor_approximation: {leading_nonnine_digit, doubling_digit_group} — selects digits used to approximate 2 - Di   # p.291-p.293
slots:
  seed: UNKNOWN   # p.290
  iter_mult: iterative_decimal_multiplication   # p.291
  final_round: UNKNOWN   # p.293
parameters: D0 normalized to 0.1 ≤ D0 < 1 in the second method; first two divisor digits forced to 0.9 or 1.0 in the third method   # p.291, p.292
results:
| metric | value | unit | technology / device | baseline | condition | page |
| example iterations | 14 | iterations | abstract | UNKNOWN | second method, 359 divided by 273 | p.291 |
| example iterations | 4 | iterations | abstract | UNKNOWN | third method, 359 divided by 273 | p.292 |
errors_and_checks: Successive zeros or nines to the right of the point in Di indicate the number of correct quotient digits in Ni.   # p.293
conditions: Approximate factors require more iterations but simplify each multiplication to a one-digit multiplication plus one addition.   # p.291
evidence: Tables 9-IV and 9-V; sections “Division by Iteration—Second Method” and “Third Method”   # p.290-p.293

### self_checking_datapath  (role: instantiates)
mechanism: A biquinary N-tupler generates left/right product components through independently generated binary/quinary signal sets. Every valid set carries one and only one signal; checking the product digit is sufficient because carry-path errors reach the next higher product digit.   # p.274-p.277
choices:
  encoding: biquinary [outside domain]   # p.274
new_choices:
  none
slots:
  comparator: UNKNOWN   # p.277
parameters: binary part one-of-two; quinary part one-of-five   # p.274-p.277
results:
| metric | value | unit | technology / device | baseline | condition | page |
| checked observation points | product digit P only | signal set | abstract | checking every inter-box line | carry error appears in the next higher P digit | p.277 |
errors_and_checks: The circuit detects missing/multiple signals caused by a fault under the stated independent-output assumption.   # p.277
conditions: The guarantee depends on every box output being generated independently and every valid binary/quinary set carrying exactly one signal.   # p.277
evidence: Fig. 9-5 and “Error-detecting Multiplier”   # p.274-p.277

## taxonomy
* Decimal multiplication   # p.258
  * Decimal multiplication table   # p.258
    * sequential digit-pair products -> iterative_decimal_multiplication   # p.259
    * separated left/right components -> iterative_decimal_multiplication   # p.259-p.261
  * over-and-over addition -> iterative_decimal_multiplication   # p.261
    * subtraction/complement recoding -> iterative_decimal_multiplication   # p.262
    * doubling -> iterative_decimal_multiplication   # p.263
    * quintupling -> iterative_decimal_multiplication   # p.266
    * N-tupling -> iterative_decimal_multiplication   # p.268
    * counter accumulation -> iterative_decimal_multiplication   # p.270
    * combined subtraction/doubling/quintupling/quadrupling -> iterative_decimal_multiplication   # p.271-p.272
    * descending multiplier digits -> iterative_decimal_multiplication   # p.273
  * error-detecting biquinary N-tupler -> self_checking_datapath   # p.274-p.277
  * serial-parallel multiplication -> decimal_serial_parallel_multiplication   # p.277
  * multiplication by duplation -> decimal_duplation_arithmetic   # p.278-p.279
* Decimal division   # p.279
  * over-and-over subtraction with restoration -> decimal_digit_recurrence   # p.279-p.282
  * alternating subtraction/addition -> decimal_digit_recurrence   # p.282-p.284
  * doubling/quintupling divisor multiples -> decimal_digit_recurrence   # p.284-p.286
  * nine parallel multiple comparisons -> decimal_digit_recurrence   # p.286
  * division by duplation -> decimal_duplation_arithmetic   # p.286-p.287
  * trial quotient digits -> decimal_digit_recurrence   # p.287-p.289
  * reciprocal iteration -> decimal_newton   # p.290
  * simultaneous numerator/divisor iteration -> goldschmidt   # p.290-p.293
* Round-off procedures -> decimal_rounding   # p.293-p.296

## primary_sources
none

## new_families
### decimal_serial_parallel_multiplication  (domain: decimal: decimal multipliers, closest: parallel_decimal_multiplication, why_not: The multiplicand is serial and the multiplier is parallel rather than all partial products being presented simultaneously.)
mechanism: All nine multiples of each arriving multiplicand digit are generated while parallel multiplier digits select multiples into a cascade of decimal adders. One final product digit appears after each cycle.   # p.277
choices: digit_form: {serial_digit_parallel_bit, serial_digit_serial_bit}; multiple_generation: {all_1_to_9}; multiplier_form: {parallel}   # p.277
results:
| metric | value | unit | technology / device | baseline | condition | page |
| latency | product digits × one cycle time | time | abstract | UNKNOWN | one product digit determined per cycle | p.277 |
evidence: Fig. 9-6   # p.277-p.278

### decimal_duplation_arithmetic  (domain: decimal: decimal multipliers/dividers, closest: iterative_decimal_multiplication, why_not: Binary-weight halving/doubling replaces decimal multiplier-digit recurrence.)
mechanism: Multiplication repeatedly halves one factor and doubles the other, accumulating doubled values when halving leaves remainder 1. Division repeatedly halves a scaled divisor and the value 1, subtracting eligible divisor values and accumulating corresponding binary fractions.   # p.278-p.279, p.286-p.287
choices: operation: {multiply, divide}; starting_scale: {largest_doubled_divisor, dividend_no_greater_than_twice_divisor}   # p.286
results:
| metric | value | unit | technology / device | baseline | condition | page |
| exactness | exact only when quotient is representable in binary and decimal | representation contract | abstract | UNKNOWN | division by repeated halving | p.287 |
evidence: sections “Multiplication by ‘Duplation’” and “Division by ‘Duplation’”   # p.278-p.279, p.286-p.287

### decimal_rounding  (domain: decimal: decimal misc, closest: decimal_fp_addition, why_not: The chapter defines standalone rounding procedures for multiplication/division rather than a decimal floating-point adder.)
mechanism: Decimal digits are discarded after an adjustment to the lowest retained order. Variants inspect/double the highest discarded digit, add 5 there, pre-add five times the divisor, force a retained digit, or add a random bit. Complement-form numbers require sign-aware handling.   # p.293-p.296
choices: method: {half_up, add_5_discarded_order, double_discarded_digit, preadd_5x_divisor, force_5, random_increment, parity_conditioned_increment}; negative_form: {convert_true, nines_complement_adjust}   # p.294-p.296
results:
| metric | value | unit | technology / device | baseline | condition | page |
| average error | +5 in the 5th order | decimal order | abstract | zero | exact 4-digit numbers rounded to 3 digits | p.294 |
| error range | +0.5 to -0.4999... | lowest retained order | abstract | UNKNOWN | discarded-digit half-up procedures | p.296 |
| error range | +1 to -0.999... | lowest retained order | abstract | half-up | random increment or parity-conditioned procedure | p.296 |
evidence: section “Round-off Procedures”   # p.293-p.296

## space_gaps
* iterative_decimal_multiplication lacks product-generation and easy-multiple choices for the chapter’s stored-table/repeated-operation/generated-multiple taxonomy.   # p.259, p.261, p.268
* decimal_digit_recurrence lacks quotient-selection choices for repeated subtraction, alternating sign recurrence, easy multiples, parallel comparison, and corrected trial digits.   # p.281-p.289
* self_checking_datapath lacks biquinary as an encoding value.   # p.274-p.277
* The vocabulary lacks decimal serial-parallel multiplication, decimal duplation, and standalone decimal rounding families.   # p.277-p.279, p.286-p.287, p.293-p.296
* The decimal divider vocabulary lacks the simultaneous numerator/divisor iteration described for the Harvard Mark IV.   # p.290-p.293

## open_questions
* The chapter does not specify the accumulator/reduction-tree family used by the multiplication variants.
* The chapter does not state years or bibliographic citations for the IBM Type 602/602A or Harvard Mark IV mechanisms.
* The chapter does not state a seed-table mechanism or fixed iteration count for reciprocal iteration.
