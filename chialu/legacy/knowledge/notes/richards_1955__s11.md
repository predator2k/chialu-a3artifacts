---
handle: richards_1955#s11
parent: richards_1955
citation: Richards, "Arithmetic Operations in Digital Computers", Van Nostrand, 1955
chapter: MISCELLANEOUS OPERATIONS
pdf_pages: 297-324
status: ok
kind: book_chapter
unit_classes: [BINARY_ALU, VEC_SFU, other]
formats: [binary, decimal, reflected binary]
authority: textbook
pages_read: 28 / 28
---

## summary
The chapter classifies programmed conversion/comparison/square-root/function-evaluation methods and describes residue checking, a digital differential analyzer, and binary/reflected-binary conversion. The chapter gives abstract accuracy/iteration relations but no technology-bound implementation results.

## families
### binary_decimal_conversion  (role: taxonomizes)
mechanism: Decimal-to-binary conversion uses repeated division or multiplication by 2, sequential subtraction of powers of 2, binary accumulation by multiplying or dividing by 1010 and adding encoded digits, or repeated addition of positional equivalents. Binary-to-decimal conversion applies direct counterparts based on division by 1010, subtraction of powers of ten, alternating digit addition and doubling, or accumulation of decimal positional equivalents. (p.297-p.301)
choices:
  direction: both   # p.300-p.301
  structure: UNKNOWN   # p.297-p.301
  digits_per_step: 1   # p.299-p.301
new_choices:
  procedure: {repeated_radix_divide_or_multiply, sequential_power_subtraction, digitwise_radix_accumulation, repeated_positional_addition} — selects the chapter's four conversion procedures   # p.297-p.301
  number_class: {integer, fraction} — determines the direction/order of the recurrence and whether round-off occurs   # p.297-p.301
slots:
  none
parameters: radix factors 2 and 1010; one source digit handled per digitwise accumulation step   # p.297-p.301
results:
| metric | value | unit | technology / device | baseline | condition | page |
| integer representation accuracy | exact | representation | abstract | none | decimal integer converted to binary | p.298 |
| fractional representation accuracy | any desired degree of accuracy | accuracy | abstract | none | sufficient binary digits are determined | p.298 |
| accumulator precision remedy | a few extra orders | accumulator orders | abstract | repeated positional addition | minimizes round-off error | p.300 |
errors_and_checks: Fractions may lack exact representations, and conversion methods can produce different round-off errors. Repeated positional addition is particularly susceptible to round-off.   # p.298, p.300-p.301
conditions: The procedure is usually selected according to machine characteristics and special features. Sequential power subtraction is unattractive when decimal powers of 2 are awkward and selection is difficult to mechanize. Repeated positional addition fits a simple binary accumulator but has greater round-off exposure.   # p.297, p.299-p.300
evidence: Decimal-to-Binary Conversion and Binary-to-Decimal Conversion, p.297-p.301

### prefix_comparator  (role: taxonomizes)
mechanism: Relative magnitude can be determined by subtraction followed by sign sensing. Equality can be added through zero detection, or corresponding bits can be compared with sum-only half adders and reduced by an AND condition. A magnitude-only circuit can reproduce the borrow portion of a subtracter without producing difference bits. (p.301-p.302)
choices:
  function: full_ordering   # p.301-p.302
  structure: subtractor_carry_out   # p.301
  radix: 2   # p.302
new_choices:
  equality_structure: pairwise_half_adder_sum_plus_zero_reduction — compares corresponding bits without subtraction   # p.302
  magnitude_structure: borrow_only_subtracter — omits the difference portion   # p.302
slots:
  none
parameters: binary pairwise comparison; decimal zero detection senses four bits per 8,4,2,1 digit or one line per 1-out-of-10 digit   # p.302
results:
| metric | value | unit | technology / device | baseline | condition | page |
| equality by subtraction | 2 | subtractions | abstract | sign-only comparison | no separate zero detector is provided | p.301 |
errors_and_checks: none
conditions: Subtraction reuses existing computer circuits but requires zero detection or a second subtraction to distinguish equality. Direct comparison omits arithmetic outputs that are unnecessary for the comparison result.   # p.301-p.302
evidence: Comparison, p.301-p.302

### digit_recurrence_sqrt_combined  (role: analyzes)
mechanism: The paper-and-pencil recurrence selects one root digit, doubles the established root prefix, appends a trial digit, subtracts the resulting product, and corrects an overdrawn remainder. A machine procedure can generate decimal trial digits by subtracting successive odd numbers. Binary operation reduces each trial to the digit 1, forms the trial divisor by shifting the root prefix, and inserts 1 in the units position. (p.304-p.306)
choices:
  radix: 2   # p.306
  shared_with_division: UNKNOWN   # p.303-p.306
  on_the_fly_conversion: UNKNOWN   # p.303-p.306
  speculation_between_subiterations: UNKNOWN   # p.303-p.306
new_choices:
  trial_digit_method: {inspection, repeated_odd_number_subtraction, binary_single_trial} — selects and verifies the next root digit   # p.304-p.306
slots:
  digit_select: UNKNOWN   # p.304-p.306
parameters: decimal digits grouped in pairs; one root digit established per recurrence step   # p.304
results:
| metric | value | unit | technology / device | baseline | condition | page |
| binary trial digit candidates | 1 | nonzero candidate | abstract | decimal trial-digit search | binary square root | p.306 |
| binary odd-number-series terms | 1 | term | abstract | decimal repeated odd-number generation | binary square root | p.306 |
errors_and_checks: A negative trial remainder is restored by adding the last subtracted odd number. Rounding follows substantially the multiplication/division procedures described elsewhere.   # p.304-p.305
conditions: A built-in recurrence can be faster than programmed square root, but built-in square root was rare and had received little speed-development attention. Binary operation is simpler because trial selection, odd-number generation, and carry formation are reduced.   # p.306
evidence: Extracting the Square Root, p.302-p.306

### newton_raphson  (role: analyzes)
mechanism: Two second-order and two third-order programmed formulas successively refine a square-root approximation. One second-order form requires division for every approximation. The other requires one reciprocal of x but needs a more accurate initial approximation. (p.303)
choices:
  steps: UNKNOWN   # p.303
new_choices:
  convergence_order: {2, 3} — identifies the number of significant-digit gains associated with a refinement formula   # p.303
slots:
  none
parameters: initial approximation b0 is nonzero for the first second-order formula; the second requires |b0| below the printed bound   # p.303
results:
| metric | value | unit | technology / device | baseline | condition | page |
| convergence gain | significant digits doubled | digits per application | abstract | previous approximation | moderately accurate approximation and second-order formula | p.303 |
| recurring divisions | 1 | division per approximation | abstract | reciprocal-based second formula | first second-order formula | p.303 |
| reciprocal computations | 1 | division total | abstract | division on every refinement | second second-order formula | p.303 |
errors_and_checks: Iteration may stop when the difference between successive approximations is below the tolerable error.   # p.303
conditions: The reciprocal-based formula suits machines without built-in division but requires a more accurate first guess. Iterative formulas are generally inconvenient as dedicated machine functions.   # p.303
evidence: Extracting the Square Root, p.302-p.303

### residue  (role: extends)
mechanism: Casting out 9's computes each operand/result remainder modulo 9 and checks addition/subtraction/multiplication/division through the corresponding modular relation. The residue can also be found from the digit sum, with decimal carries returned to the digit sum. Binary data can be grouped into three-bit octonary digits for an analogous modulo-7 check. (p.310-p.311)
choices:
  modulus: 9 [outside domain]   # p.310-p.311
  granularity: endpoint   # p.310-p.311
  comparison_point: writeback   # p.310-p.311
  generator_style: modular_ripple   # p.311
  ops_per_checker: UNKNOWN   # p.310-p.311
new_choices:
  checked_operation: {addition, subtraction, multiplication, division} — selects the modular identity used for checking   # p.310-p.311
slots:
  comparator: UNKNOWN   # p.310-p.311
parameters: decimal modulus 9; binary analogue groups digits in threes and uses modulus 7   # p.310-p.311
results:
| metric | value | unit | technology / device | baseline | condition | page |
| binary grouping width | 3 | bits | abstract | decimal digit residues | casting out 7's as an octonary system | p.311 |
errors_and_checks: Equality of computed and predicted residues is the stated check. The chapter does not quantify undetected-error coverage.   # p.310-p.311
conditions: Casting out 1's is meaningless for binary digits, so the chapter substitutes three-bit groups and modulus 7. Digit-sum generation may be preferable for machine implementation.   # p.311
evidence: Checking by “Casting Out 9’s,” p.310-p.311

### lut_plus_poly  (role: taxonomizes)
mechanism: A stored table supplies function values, and an interpolation formula computes values for arguments absent from the table. Table spacing and interpolation complexity are traded against each other. (p.312)
choices:
  degree: UNKNOWN   # p.312
  index_bits: UNKNOWN   # p.312
  basis: UNKNOWN   # p.312
  coeff_encoding: UNKNOWN   # p.312
  guard_bits: UNKNOWN   # p.312
  breakpoint_placement: uniform   # p.312
  multiplier_shape: UNKNOWN   # p.312
new_choices:
  execution: programmed — the chapter treats table interpolation as a programmed sequence   # p.312
slots:
  range_reducer: UNKNOWN   # p.312
  evaluator: UNKNOWN   # p.312
  segmenter: uniform_high_bit_decode   # p.312
parameters: UNKNOWN   # p.312
results:
| metric | value | unit | technology / device | baseline | condition | page |
| table/interpolation tradeoff | larger steps require more complex interpolation; smaller steps permit simpler interpolation | abstract tradeoff | abstract | none | stored-table evaluation | p.312 |
errors_and_checks: Accuracy is determined by table spacing/interpolation procedure, but no bound is given.   # p.312
conditions: Selection depends on storage capacity/access time, operation speed, and program-preparation difficulty. Computing a value may be preferable when arithmetic is fast relative to large-storage access.   # p.312-p.313
evidence: Trigonometric and Other Transcendental Functions, p.311-p.313

### single_poly  (role: taxonomizes)
mechanism: A polynomial approximates the desired function over a limited argument range. Polynomial complexity varies with the range and required accuracy. (p.312)
choices:
  degree: UNKNOWN   # p.312
  basis: UNKNOWN   # p.312
  coeff_encoding: UNKNOWN   # p.312
  guard_bits: UNKNOWN   # p.312
new_choices:
  execution: programmed — the approximation is evaluated through basic operations   # p.311-p.312
slots:
  range_reducer: UNKNOWN   # p.312
  evaluator: UNKNOWN   # p.312
parameters: limited argument range; accuracy unspecified   # p.312
results:
| metric | value | unit | technology / device | baseline | condition | page |
| polynomial complexity | depends on range and required accuracy | abstract complexity | abstract | none | polynomial function approximation | p.312 |
errors_and_checks: No numerical approximation bound is stated.   # p.312
conditions: Polynomial approximation is especially useful when the function is needed over a limited argument range.   # p.312
evidence: Trigonometric and Other Transcendental Functions, p.311-p.313

## taxonomy
* Number-system conversion
  * Decimal to binary
    * Repeated integer division by 2 / fractional multiplication by 2 -> binary_decimal_conversion   # p.297-p.298
    * Sequential subtraction of decimal powers of 2 -> binary_decimal_conversion   # p.298-p.299
    * Digitwise binary multiply/add or divide/add by 1010 -> binary_decimal_conversion   # p.299-p.300
    * Repeated addition of positional binary equivalents -> binary_decimal_conversion   # p.300
  * Binary to decimal
    * Repeated division by 1010 -> binary_decimal_conversion   # p.300
    * Repeated subtraction of powers of ten -> binary_decimal_conversion   # p.300-p.301
    * Alternating binary-digit addition and decimal doubling -> binary_decimal_conversion   # p.301
    * Accumulation of decimal positional equivalents -> binary_decimal_conversion   # p.301
* Comparison
  * Subtract and sense sign/zero -> prefix_comparator   # p.301-p.302
  * Pairwise half-adder equality comparison -> prefix_comparator   # p.302
  * Borrow-only magnitude circuit -> prefix_comparator   # p.302
* Square root
  * Second-order programmed iteration -> newton_raphson   # p.303
  * Third-order programmed iteration -> newton_raphson   # p.303
  * Pencil-and-paper digit recurrence -> digit_recurrence_sqrt_combined   # p.304-p.306
* Sorting
  * Least-significant-digit-first distribution -> unmapped   # p.306-p.307
  * Collating/merging through alternating storage groups -> sorting_by_collating   # p.307-p.310
* Arithmetic checking
  * Decimal casting out 9's -> residue   # p.310-p.311
  * Three-bit binary casting out 7's -> residue   # p.311
* Transcendental functions
  * Stored table plus interpolation -> lut_plus_poly   # p.312
  * Infinite-series evaluation -> series_function_evaluation   # p.312
  * Limited-range polynomial approximation -> single_poly   # p.312
* Numerical calculus
  * Programmed incremental integration/differentiation -> unmapped   # p.313-p.314
  * Interconnected digital integrators -> digital_differential_analyzer   # p.314-p.322
* Binary-code translation
  * Conventional binary to reflected binary by adjacent-bit half adders -> binary_reflected_code_conversion   # p.322-p.323
  * Reflected binary to conventional binary by a dependent half-adder chain -> binary_reflected_code_conversion   # p.324

## primary_sources
* Lord Kelvin, 1876 — first description of the principles of the analog differential analyzer   # p.314
* Vannevar Bush, 1931 — publication describing the first differential analyzer built   # p.314
* Northrop Aircraft Corporation engineers, shortly after World War II — development of the digital differential analyzer   # p.314

## new_families
### sorting_by_collating  (domain: other, closest: prefix_comparator, why_not: The mechanism is a storage-transfer sorting algorithm rather than a comparator circuit.)
mechanism: Three values X/Y/L determine which of two storage locations receives the next value. Alternating pairs of storage locations repeatedly merge ordered sequences until one sequence remains; the method generalizes to larger storage-location groups. (p.307-p.310)
choices: storage_locations_per_group: Int[2..N:1]; equal_key_policy: {arbitrary_xy_choice, keep_equal_to_l_with_l}
results:
| metric | value | unit | technology / device | baseline | condition | page |
| file transfers | (log2 N)int | transfers | abstract | none | worst case, reverse initial order | p.309 |
| file transfers | 1 + (log2 S)int | maximum transfers | abstract | none | S initial ordered sequences | p.309 |
| generalized file transfers | (logM N)int | transfers | abstract | two-location groups | M storage locations per group | p.309 |
evidence: p.307-p.310

### series_function_evaluation  (domain: sfu, closest: single_poly, why_not: An infinite series uses a variable number of terms rather than one fixed polynomial over the domain.)
mechanism: A programmed sequence evaluates enough terms of an infinite series representation to obtain the desired accuracy. (p.312)
choices: term_count: Int[1..N:1]
results:
| metric | value | unit | technology / device | baseline | condition | page |
| attainable accuracy | any desired degree of accuracy | accuracy | abstract | none | sufficient series terms are evaluated | p.312 |
evidence: p.312

### digital_differential_analyzer  (domain: other, closest: carry_save_datapath, why_not: The mechanism is a pulse-rate integrator network with stored state and programmable interconnections.)
mechanism: Each integrator repeatedly adds Y to accumulator R on dx pulses and emits dz on overflow; dy changes Y. Integrators are interconnected to represent differential equations. A serial magnetic-drum implementation stores Y/R states, circulates dz signals on a precessing Z track, and selects programmed interconnections from an L track. (p.314-p.322)
choices: sign_signaling: {pulse_absence, dual_wire}; organization: {parallel_integrators, serial_shared_arithmetic}; scale_adjustment: {dy_order_selection, dz_multiplication}
results:
| metric | value | unit | technology / device | baseline | condition | page |
| pulse relation | dz = ydx/r^n | output pulses | abstract | none | radix r and n-order registers | p.315 |
| precessing-track length | N - 1 | pulse times | magnetic drum | N pulse-time integrator | serial organization | p.319-p.320 |
evidence: p.314-p.322

### binary_reflected_code_conversion  (domain: other, closest: prefix_comparator, why_not: The circuit translates adjacent-transition codes rather than comparing operands.)
mechanism: Conventional binary converts to reflected binary by retaining the highest bit and applying the sum function of a half adder to each adjacent conventional-bit pair. Reflected binary converts back by retaining the highest bit and forming each lower conventional bit from the preceding conventional bit and the corresponding reflected bit. (p.322-p.324)
choices: direction: {binary_to_reflected, reflected_to_binary}; cell: {half_adder_sum}; organization: {adjacent_parallel, dependent_chain}
results:
| metric | value | unit | technology / device | baseline | condition | page |
| differing digits between successive reflected quantities | 1 | digit | abstract | conventional binary | reflected binary representation | p.322 |
evidence: Fig. 10-5, p.323-p.324

## space_gaps
* binary_decimal_conversion lacks the four procedures explicitly classified by the chapter.   # p.297-p.301
* residue lacks modulus 9, which is the chapter's principal decimal checking modulus.   # p.310-p.311
* prefix_comparator lacks pairwise-half-adder equality and borrow-only magnitude structures.   # p.302
* The vocabulary lacks series-function evaluation, digital differential analyzers, and conventional/reflected-binary converters.   # p.312, p.314-p.324

## open_questions
* The supplied extraction omits the two second-order square-root formulas on p.303, so their exact recurrences cannot be transcribed.
* The generalized collating expression is printed as `(logM N)int`, while the following explanation names `n` as the storage-location count; the intended symbol must not be guessed.
