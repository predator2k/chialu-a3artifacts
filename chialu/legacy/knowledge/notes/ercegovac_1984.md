---
handle: ercegovac_1984
citation: Ercegovac, "On-Line Arithmetic: An Overview", SPIE Real-Time Signal Processing VII, 1984
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU, other]
formats: [fixed_point_redundant_radix_r, floating_point_redundant_radix_r]
authority: survey
pages_read: 86-93 / 8
---

## summary
The paper surveys most-significant-digit-first on-line arithmetic, in which digit-serial operators overlap successive operations after a small on-line delay. The paper gives recurrences for fixed-point addition/multiplication and describes modular/pipelined structures for composite functions and recurrence systems. The reported benefits are reduced intermodule bandwidth and additional speedup for chained computations, with redundant representation/conversion and serial latency as costs.

## families
### online_arithmetic_unit  (role: analyzes)
mechanism: Each operator accepts and produces radix-r digits most-significant first. Result digit j requires operand digits through j+δ, where δ is a small on-line delay. A recurrence updates a residual/internal vector using addition, multiplication by one radix-r digit, shifting, concatenation, and a limited-precision selection function. Redundant digits permit the recurrence step to avoid complete carry propagation, so digit step-time is independent of operand length.   # pp.86-88
choices:
  radix: general r [outside domain]   # pp.86-88
  online_delay: 1 for OLADD when r>2 and for multiplication; 2 for OLADD when r=2; 4 for division   # pp.86,88
  digit_set: minimally_redundant, intermediate [outside domain], or maximally_redundant   # pp.86,89
  residual_form: carry_save   # pp.88,90
new_choices:
  operation: {addition_subtraction, multiplication, division, square_root, composite_function} — selects the recurrence implemented by the unit   # pp.86,88-90
  implementation_organization: {linear_nonpipelined, one_dimensional_pipelined, two_dimensional_pipelined} — selects the modular array organization   # p.87
  variable_precision: Bool — permits precision to match input significance   # p.88
slots:
  none
parameters: δ=1 to 4 in the surveyed basic operations; a pipelined unit has n+δ stages; a d-digit two-dimensional implementation uses about (n/d)^2/4 modules   # pp.86-87
results:
| metric | value | unit | technology / device | baseline | condition | page |
| on-line delay, OLADD | 1 | digits | UNKNOWN / 1984 | none | r>2, p=r-1 | p.88 |
| on-line delay, OLADD | 2 | digits | UNKNOWN / 1984 | none | r=2 | p.88 |
| on-line delay, multiplication | 1 | digits | UNKNOWN / 1984 | none | surveyed on-line multiplication | p.86 |
| on-line delay, division | 4 | digits | UNKNOWN / 1984 | none | surveyed on-line division | p.86 |
| floating-point addition latency | m+2 to m+3 | steps | UNKNOWN / 1984 | none | similar-sign operands, m+1-digit result | p.88 |
| floating-point subtraction latency | m+3 to 2m+4 | steps | UNKNOWN / 1984 | none | m+1-digit result | p.88 |
| floating-point multiplication latency | m+2 to m+5 | steps | UNKNOWN / 1984 | none | exponent and result-significand MSD obtained together | p.88 |
| additional speedup | 2-16 | factor | UNKNOWN / 1984 | conventional arithmetic networks | typical precision; overlapping/pipelined networks | pp.91-92 |
errors_and_checks: Inputs with k significant digits produce at least k-δ significant output digits. A symmetric redundant digit set prevents truncation bias. Hardware-error detection is discussed only as a cited means of restricting the significance of later digits; coverage/false-alarm behavior are not reported.   # pp.87-88
conditions: On-line arithmetic benefits multioperator/pipelined computations because operators communicate one digit per operand and overlap execution. Redundant-number conversion, nonconventional representation, and inherently serial operation make it unsuitable for isolated operations and comparisons.   # pp.86,91-92
evidence: §1 and Figs.1-4, pp.86-87; Algorithms OLADD/OLMUL and Figs.5-6, p.88; §4 and Fig.8, pp.90-92

### generalized_signed_digit  (role: instantiates)
mechanism: Operands/results use a symmetric redundant radix-r digit set {-p,...,-1,0,1,...,p}, with r/2 ≤ p ≤ r-1. Redundancy permits most-significant-first digit selection from a truncated residual and supports totally parallel recurrence operations without complete carry propagation.   # pp.86-88
choices:
  radix: general r [outside domain]   # pp.86-88
  redundancy: minimal through maximal   # pp.86,89
  addition_scheme: carry_free   # pp.86-87
new_choices:
  none
slots:
  none
parameters: r/2 ≤ p ≤ r-1; examples use r=2 and r=10, with p=9 for the decimal example   # pp.86,88
results: none reported
errors_and_checks: The symmetric digit set prevents bias when truncation is the rounding scheme in on-line floating-point arithmetic.   # p.88
conditions: Redundant representation is stated as necessary for producing results left to right and desirable for operand input. Conversion to/from conventional representation is a principal disadvantage.   # pp.86,92
evidence: §1, pp.86-87; Variable Precision/Floating-Point and OLADD, p.88

### carry_save_datapath  (role: instantiates)
mechanism: The OLMUL residual adder may be carry-save, which makes recurrence step-time independent of working precision. The polynomial E-method maps evaluation onto a linear array of identical 3-input carry-save adders and registers, with digit-serial communication between operators.   # pp.88,90
choices:
  compressor: 3_2   # p.90
  accumulator_redundant: true   # pp.88,90
new_choices:
  none
slots:
  none
parameters: The polynomial example uses four 3-input carry-save adders and 12 registers; m-bit precision requires m+1 steps   # p.90
results:
| metric | value | unit | technology / device | baseline | condition | page |
| polynomial-evaluation latency | m+1 | steps | UNKNOWN / 1984 | conventional tree of multiply-add operators | four 3-input carry-save adders and 12 registers | p.90 |
| recurrence step delay | about 10 | gate delays | UNKNOWN / 1984 | none | conventional SSI/MSI implementation | p.90 |
errors_and_checks: none
conditions: The E-method linear-system solver requires a diagonally dominant coefficient matrix. The structure replaces full-precision interoperator datapaths with digit-serial datapaths.   # p.90
evidence: Algorithm OLMUL, p.88; Algorithm OLLS, polynomial example, and Fig.7, p.90

### online_pipeline_composition  (role: analyzes)
mechanism: Operators at successive levels share a digit clock. A level begins producing digits after its on-line delay rather than waiting for the preceding full-precision result, so operations overlap across a network. Composite algorithms pass each generated digit immediately and use linear or two-dimensional modular arrays.   # pp.86,89-91
choices:
  scheduling: digit_slice_overlapped   # pp.86,90
new_choices:
  communication_width_digits: Int[1..N] — specifies interoperator bandwidth B in digits per variable   # p.91
slots:
  none
parameters: L levels, n result digits, per-level maximum delay δmax,i, digit time td, and communication bandwidth B   # pp.90-91
results:
| metric | value | unit | technology / device | baseline | condition | page |
| scalar-network latency | [n+2Σ(δmax,i+1)]td | time | UNKNOWN / 1984 | conventional L-level network | digit-clocked on-line units | p.90 |
| band matrix-vector speedup | 2≤Sp≤3 | factor | UNKNOWN / 1984 | similar conventional-arithmetic array | one-dimensional on-line array | p.89 |
| linear-recurrence speedup | log2 n≤Sp≤n | factor | UNKNOWN / 1984 | conventional arithmetic | two-dimensional on-line array, n-digit precision | p.89 |
| bandwidth-limited additional speedup | n/4B | factor | UNKNOWN / 1984 | conventional network with B-digit links | large L | p.91 |
errors_and_checks: none
conditions: Benefits increase with expression depth, repeated results, or constrained intermodule bandwidth. Simple/modular connections support partitionable and reconfigurable arrays.   # pp.89-91
evidence: Composite algorithms and E-method, pp.89-90; §4, pp.90-91

## new_families
none

## space_gaps
* `online_arithmetic_unit.radix` needs a general-r value because the recurrences and digit-set bounds are parameterized by r, and the paper includes r=10.   # pp.86,88
* `online_arithmetic_unit.digit_set` needs an intermediate-redundancy value because r/2 ≤ p ≤ r-1 permits values between the minimal/maximal endpoints.   # pp.86,89
* `online_arithmetic_unit` lacks choices for operation, modular-array organization, and variable precision.   # pp.86-88

## open_questions
* The paper does not specify the physical digit encoding used for {-p,...,p}.
* The paper cites error-coded on-line algorithms but does not describe a checker mechanism or quantify coverage.
* The paper does not specify conversion hardware between redundant and conventional representations.
