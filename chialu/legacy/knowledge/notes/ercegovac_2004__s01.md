---
handle: ercegovac_2004#s01
parent: ercegovac_2004
citation: M. D. Ercegovac and T. Lang, "Digital Arithmetic", Morgan Kaufmann, 2004
chapter: Digit-Serial Arithmetic
pdf_pages: 0-58
status: ok
kind: book_chapter
unit_classes: [BINARY_ALU, VEC_DOT_ACC, other]
formats: [radix-r conventional, radix-r signed-digit, radix-2 two's complement, fixed-point]
authority: textbook
pages_read: 59 / 59
---

## summary
The chapter defines digit-serial arithmetic, classifies LSDF and MSDF/online modes, and derives serial addition/multiplication plus online addition/multiplication/division. # p.0, p.2, p.7, p.13
The chapter compares latency/cost in abstract components and shows that MSDF execution overlaps dependent operations after a fixed online delay. # p.3, p.7, p.43
The chapter also develops composite online operations, reduced-slice implementations, and recursive-filter schedules. # p.37, p.38, p.40

## families
### serial_serial_parallel  (role: taxonomizes)
mechanism: The LSDF serial-serial multiplier receives both operands least-significant bit first, maintains the product residual in two carry-save vectors, adds two digit multiples through an n-position [4:2] adder, emits the low product bit each cycle, and shifts the remaining residual through a serial adder. The LSDF serial-parallel variant first converts one operand to parallel form, performs sequential carry-save multiplication while emitting low bits, and serializes the high half afterward.
choices:
  serial_operands: both (LSDF-SS), one (LSDF-SP)   # p.9
  digit_size_bits: 1   # p.9
  end_reconfigure_to_ripple: true   # p.11, p.12
new_choices:
  phase_count: 3 — input conversion, multiplication/low-bit output, and high-bit output in LSDF-SP   # p.11, p.12
slots:
  none
parameters: radix 2; n-bit operands; 2n product bits   # p.9, p.11
results:
| metric | value | unit | technology / device | baseline | condition | page |
| execution time | 2n t_cyc | time | abstract | none | LSDF-SS | p.11 |
| cycle delay | t_SEL + t_[4:2] + t_FF | time | abstract | none | LSDF-SS | p.11 |
| cost | one n-bit [4:2] adder, 5 n-bit registers, and multiple-forming gates | components | abstract | none | LSDF-SS | p.11 |
| execution time | 3n t_cyc | time | abstract | none | LSDF-SP, nonconstant operands | p.13 |
| cycle delay | t_SEL + t_CSA + t_FF | time | abstract | none | LSDF-SP | p.13 |
| concurrent operations | up to three | operations | abstract | unpipelined phases | phases used as pipeline stages | p.13 |
errors_and_checks: A rounded most-significant product half is obtained by inserting 1 into the least-significant bit of the initial carry-save partial product.   # p.13
conditions: LSDF-SS begins producing product bits while operands are still arriving, but it has a longer cycle and more circuitry than LSDF-SP. # p.11 LSDF-SP is especially suitable when one operand is constant and when throughput permits three pipelined phases. # p.11, p.13
evidence: Sections 9.2.2; Figures 9.6-9.7; equations 9.9-9.15.

### generalized_signed_digit  (role: defines)
mechanism: Online addition serializes a parallel redundant adder. For radix greater than 2 with a > r/2, the transfer digit propagates only to the adjacent more-significant digit, which gives online delay 1. Radix-2 addition uses signed digits {-1,0,1}, encoded by positive/negative binary components, and two full-adder stages, which gives online delay 2.
choices:
  radix: 2, 4   # p.15, p.16
  redundancy: a > r/2 [outside domain]   # p.14
  digit_encoding: plus_minus_pair [outside domain]   # p.16
  addition_scheme: two_stage_limited_carry   # p.14, p.16
  final_conversion: on_the_fly   # p.14
new_choices:
  serial_mode: MSDF — operands/results arrive most-significant digit first   # p.2
slots:
  none
parameters: online delay 1 for radix greater than 2; online delay 2 for radix 2   # p.15, p.16
results:
| metric | value | unit | technology / device | baseline | condition | page |
| cycle time | 2t_FA + t_FF | time | abstract | none | radix-2 online addition | p.16 |
| operation time | (2 + n + 1)t_cyc | time | abstract | none | radix-2 online addition | p.16 |
| cost | 2 FAs and 5 FFs | components | abstract | none | radix-2 online addition | p.16 |
errors_and_checks: Redundancy permits a selected output digit to be compensated in later iterations; conversion to conventional representation can use on-the-fly conversion without a carry-propagate addition.   # p.14
conditions: The radix-greater-than-2 construction requires a > r/2. # p.14 Radix 2 requires an additional input-digit lookahead and therefore has online delay 2. # p.16
evidence: Section 9.3.1; Figures 9.9-9.10; Tables 9.2-9.3; equations 9.16-9.20.

### online_arithmetic_unit  (role: defines)
mechanism: An online unit consumes MSDF operand digits, stores partial operands and a redundant residual, computes v[j] from the shifted residual and new digit multiples, selects one result digit, and updates the residual. The chapter derives the residual from a scaled error bound and derives selection either from overlapping selection intervals or by rounding a truncated residual estimate.
choices:
  radix: 2   # p.27
  online_delay: 3   # p.27
  digit_set: symmetric {-a,...,a} [outside domain]   # p.26
  residual_form: carry_save   # p.27
new_choices:
  digit_selection: {selection_constants, residual_rounding} — alternative output-digit selection methods   # p.18, p.23
  estimate_fraction_bits: 2 — assimilated residual precision for radix-2 multiplication   # p.27
slots:
  none
parameters: n + online-delay recurrence cycles plus one output cycle; radix-2 multiplication uses online delay 3 and t = 2   # p.24, p.27
results:
| metric | value | unit | technology / device | baseline | condition | page |
| execution time | online delay + 1 + n | cycles | abstract | none | generic n-digit serial operation | p.2 |
| absolute error | 2^-8 | value | abstract | true product truncated to 8 bits | worked radix-2 multiplication example | p.29 |
errors_and_checks: The residual bound and selection intervals guarantee convergence; truncation errors are included through e_min/e_max and grid-restricted intervals.   # p.20, p.21, p.22
conditions: Selection constants become impractical as radix rises above 4, while residual rounding is simpler when the recurrence preserves the required residual bounds. # p.23
evidence: Sections 9.3.2-9.3.4; Figures 9.12-9.14; equations 9.21-9.68.

### online_msdf  (role: instantiates)
mechanism: Online division maintains w[j] = r^j(x[j] - q[j]d[j]) in carry-save form. Each cycle appends a divisor digit, forms v[j] from the shifted residual/dividend digit/partial-quotient multiple, selects q[j+1], subtracts q[j+1]d[j+1], and appends the quotient digit through on-the-fly conversion.
choices:
  online_delay: 4   # p.33, p.35
  radix: 2   # p.33
new_choices:
  estimate_fraction_bits: 3 — precision used by the quotient-selection estimate   # p.33, p.35
slots:
  digit_select: qds_table   # p.33, p.35
parameters: signed operands/quotient in (-1,1); quotient digits {-1,0,1}; t = 3; selection constants ±1/4   # p.30, p.33, p.35
results:
| metric | value | unit | technology / device | baseline | condition | page |
| online delay | 4 | cycles | abstract | conventional digit-recurrence division | radix-2 online division | p.33 |
| residual adders | two [3:2] adders | adders | abstract | one [3:2] adder | online versus conventional division | p.36, p.37 |
| registers | 6 | registers | abstract | 5 registers | online versus conventional division | p.37 |
| residual estimate | 3 fractional bits | bits | abstract | 1 fractional bit | online versus conventional division | p.36, p.37 |
errors_and_checks: The selected quotient digit keeps |w[j]| below a bound smaller than d[j]; the derivation incorporates carry-save estimate truncation.   # p.32, p.33
conditions: A single selection-constant solution is obtained only for radix 2; higher radices require divisor intervals and a staircase selection function. # p.32 Online division is more complex and has a longer cycle than conventional carry-save digit-recurrence division. # p.36, p.37
evidence: Section “Online Division”; Figures 9.15-9.16; equations 9.69-9.86.

### carry_save_datapath  (role: analyzes)
mechanism: Online multiplication/division and composite operations keep residuals as pseudosum/stored-carry vectors, shift those vectors without carry propagation, and use [3:2], [4:2], or [5:2] reduction. Only a limited 3-to-6-bit carry-propagate adder assimilates the residual portion required for digit selection.
choices:
  compressor: 3_2, 4_2, 5_2 [outside domain]   # p.25
  assimilation_point: end_of_chain   # p.14
  accumulator_redundant: true   # p.25
new_choices:
  estimate_assimilation_width: 3 to 6 bits — limited CPA width used for residual estimates   # p.25
slots:
  none
parameters: p fractional slices plus i_b integer slices; p = ceil((2n + online delay + t)/3) for the analyzed [4:2] case   # p.37, p.38
results:
| metric | value | unit | technology / device | baseline | condition | page |
| implemented slices | 25 | bit slices | abstract | 34 slices | 32-bit radix-2 online multiplication with slice reduction | p.38 |
errors_and_checks: Fractional-slice truncation must satisfy p - 2h + online delay > t so corrupted residual bits do not enter the selection estimate.   # p.38
conditions: Slice reduction is valid only when propagated truncation error remains below the t-bit estimate boundary through the final cycles. # p.37, p.38
evidence: Section “The Reduction of Digit Slices in Online Implementations”; Figure 9.17; equations 9.87-9.89.

### online_pipeline_composition  (role: compares)
mechanism: MSDF result digits feed dependent modules before complete words exist, so a network’s online delay is the sum of operation delays along its longest path. Recursive computations overlap digit streams by instantiating enough multioperation modules to cover the initiation interval.
choices:
  pipeline_depth: 4   # p.44
  scheduling: digit_slice_overlapped   # p.43, p.44
new_choices:
  initiation_interval: 4 cycles — spacing of consecutive IIR outputs   # p.43
slots:
  none
parameters: n = 16 example; ceil(n/4) modules; module cycle time about 3t_FA   # p.43, p.44
results:
| metric | value | unit | technology / device | baseline | condition | page |
| vector-normalization online delay | 13 | cycles | abstract | none | radix-2 operation network | p.7 |
| conventional IIR rate | 1/(24t_FA) | outputs/time | abstract | none | n < 31 | p.43 |
| LSDF IIR rate | 1/(n t_FA) | outputs/time | abstract | none | serial arithmetic implementation | p.43 |
| online IIR rate | 1/(12t_FA) | outputs/time | abstract | conventional and LSDF | initiation interval 4 | p.43 |
errors_and_checks: none
conditions: The online IIR rate exceeds both compared alternatives for n > 12, but the rate requires ceil(n/4) multioperation modules. # p.43, p.44
evidence: Figures 9.4 and 9.21-9.22; equations 9.5-9.6 and 9.90.

## taxonomy
* Digit-serial arithmetic   # p.0
  * LSDF/right-to-left   # p.2
    * addition/subtraction -> unmapped   # p.7
    * multiplication   # p.9
      * serial-serial -> serial_serial_parallel   # p.9
      * serial-parallel -> serial_serial_parallel   # p.9
  * MSDF/left-to-right/online arithmetic   # p.2
    * addition/subtraction -> generalized_signed_digit   # p.14
    * multiplication -> online_arithmetic_unit   # p.26
    * division -> online_msdf   # p.30
    * reduced digit-slice implementation -> carry_save_datapath   # p.37
    * multioperation/composite algorithms -> unmapped   # p.38, p.39
    * recursive computation networks -> online_pipeline_composition   # p.40, p.43

## primary_sources
* Trivedi and Ercegovac, 1977 — introduction of online division and multiplication algorithms   # p.51
* Ercegovac and Lang, 1988a — method for designing online algorithms   # p.51
* Tu, 1990 — design of online selection functions   # p.51
* Ercegovac, 1978; Oklobdzija and Ercegovac, 1982 — online square-root algorithms   # p.52
* Ercegovac and Lang, 1999 — online sum-of-squares/3-D vector-normalization composite scheme   # p.38, p.39
* Brackert, Ercegovac, and Willson, 1989 — online multiply-add module for recursive digital filters   # p.53
* Chen and Willoner, 1979 — bit-sequential-input/output parallel multiplier   # p.51
* Tenca and Ercegovac, 1999 — high-radix online division for long precision   # p.52, p.58

## new_families
### digit_serial_add_subtract  (domain: adder, closest: ripple_carry, why_not: The defining structure reuses a k-bit CPA across radix-2^k digits and stores interdigit carry state rather than propagating across the full word.)
mechanism: An LSDF radix-2^k adder/subtractor accepts one k-bit digit from each operand per cycle, computes the result digit with a k-bit CPA, and stores the carry/borrow in one flip-flop. Subtraction complements the y digit and initializes the carry flip-flop to 1.
choices: digit_width_bits: Int[1..16:1]; operation: {add, subtract}; carry_state: {flip_flop, latch}
results:
| metric | value | unit | technology / device | baseline | condition | page |
| cycle delay | t_CPA(k) + t_FF | time | abstract | none | radix-2^k LSDF add/subtract | p.8 |
| total time | (n/k + 1)t_LSDFadd-k | time | abstract | none | n-bit addition | p.8 |
| cost | one k-bit CPA, k XOR gates, one flip-flop, and one k-bit output register | components | abstract | none | add/subtract implementation | p.8 |
evidence: p.7-p.8; Figure 9.5; equations 9.7-9.8.

### online_composite_multioperation  (domain: redundant online arithmetic, closest: online_pipeline_composition, why_not: It algebraically merges several operations into one residual recurrence rather than composing separate online modules.)
mechanism: A composite online unit derives one recurrence for several dependent operations, shares carry-save reduction/appending hardware, and may emit an overredundant digit set accepted directly by the successor. The sum-of-three-squares unit uses a [5:2] reduction and emits digits 0 through 8; its paired square-root recurrence computes 3-D vector magnitude.
choices: merged_operations: {sum_of_squares, multiply_add, normalization}; output_digit_set: {standard_redundant, overredundant}; reduction: {3_2, 4_2, 5_2}
results:
| metric | value | unit | technology / device | baseline | condition | page |
| online delay | 0 | cycles | abstract | 7 cycles | sum of three squares versus three multipliers/two adders | p.38 |
| online delay | 5 | cycles | abstract | 11 cycles | composite sum-of-squares plus square root | p.39 |
evidence: p.38-p.41; Figures 9.18-9.20.

## space_gaps
* `generalized_signed_digit.digit_encoding` lacks the positive/negative binary pair used for radix-2 signed digits.   # p.16
* `carry_save_datapath.compressor` lacks `5_2`, which the generic components and sum-of-squares unit use.   # p.25, p.39
* The vocabulary lacks a choice for selection by constants versus residual rounding in online units.   # p.18, p.23
* The vocabulary lacks an LSDF digit-serial adder/subtractor family.   # p.7, p.8
* The vocabulary lacks a merged online multioperation family with overredundant result digits.   # p.38, p.39

## open_questions
* Table 9.4’s OCR omits several numerical radix/redundancy/estimate/delay entries, so only the explicitly stated radix-2 multiplication pair t = 2 and online delay 3 is settled.   # p.27
* The chapter specifies symmetric/asymmetric and overredundant digit sets but does not consistently classify each example as minimally or maximally redundant.   # p.14, p.26
