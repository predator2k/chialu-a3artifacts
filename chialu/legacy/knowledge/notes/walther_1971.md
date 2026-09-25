---
handle: walther_1971
citation: J. S. Walther, "A Unified Algorithm for Elementary Functions", AFIPS Spring Joint Computer Conference, pp. 379-385, 1971
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU, VEC_SFU]
formats: [fp48, fp32, int32]
authority: landmark
pages_read: 379-385 / 7 pages
---

## summary
Walther unifies multiplication, division, trigonometric/hyperbolic functions, logarithm, exponential, and square root through coordinate rotation in linear/circular/hyperbolic systems using shifts, additions/subtractions, and stored constants. # p.379-380
A built Hewlett-Packard floating-point processor implements the algorithm with three parallel arithmetic units and calculates functions to 40 bits of precision. # p.383-384

## families
### cordic  (role: proposes)
mechanism: Three recurrences update x, y, and accumulated angle z while m selects circular (1), linear (0), or hyperbolic (-1) coordinates. Each iteration selects a rotation direction that forces A or z toward zero. Binary shifts implement multiplication by δi = 2^-Fi; the hyperbolic sequence repeats indices 4, 13, 40, 121, and subsequent 3k+1 indices to satisfy convergence. A transformed recurrence keeps floating-point registers normalized for small arguments. # p.379-384
choices:
  mode: both  # p.380
  coordinate_set: unified  # p.379-380
  topology: folded_sequential  # p.384
  scale_compensation: initial_value_correction [outside domain]  # p.381, p.383
new_choices:
  radix: 2 — the implemented shift sequences use binary arithmetic  # p.381, p.384
  hyperbolic_repeat_sequence: {4, 13, 40, 121, ..., k, 3k+1, ...} — repeated iterations restore the convergence criterion  # p.381
  register_normalization: exponent_scaled_recurrence — x/y/z and constants are scaled using E so small arguments retain L significant bits  # p.383
slots: none
parameters: Three parallel arithmetic units; each has a 64-bit register, 8-bit parallel adder/subtracter, and 8-out-of-48 multiplex shifter; ROM is 512 words × 48 bits with 200 nanoseconds cycle time; supported data are 48-bit floating point, 32-bit floating point, and 32-bit integer; calculated precision is 40 bits (approximately 12 decimal digits). # p.384
results:
| metric | value | unit | technology / device | baseline | condition | page |
| total LOAD time | 30 | μsec | UNKNOWN; 1971 | UNKNOWN | maximum; 0 CORDIC + 5 prescale/normalize/misc. + 25 data transfer | p.384 |
| total STORE time | 15 | μsec | UNKNOWN; 1971 | UNKNOWN | maximum; 0 CORDIC + 0 prescale/normalize/misc. + 15 data transfer | p.384 |
| total ADD time | 40 | μsec | UNKNOWN; 1971 | UNKNOWN | maximum; 0 CORDIC + 15 prescale/normalize/misc. + 25 data transfer | p.384 |
| total SUBTRACT time | 50 | μsec | UNKNOWN; 1971 | UNKNOWN | maximum; 0 CORDIC + 25 prescale/normalize/misc. + 25 data transfer | p.384 |
| total MULTIPLY time | 100 | μsec | UNKNOWN; 1971 | UNKNOWN | maximum; 60 CORDIC + 15 prescale/normalize/misc. + 25 data transfer | p.384 |
| total DIVIDE time | 100 | μsec | UNKNOWN; 1971 | UNKNOWN | maximum; 60 CORDIC + 15 prescale/normalize/misc. + 25 data transfer | p.384 |
| total SIN time | 160 | μsec | UNKNOWN; 1971 | UNKNOWN | maximum; 70 CORDIC + 85 prescale/normalize/misc. + 5 data transfer | p.384 |
| total COS time | 160 | μsec | UNKNOWN; 1971 | UNKNOWN | maximum; 70 CORDIC + 85 prescale/normalize/misc. + 5 data transfer | p.384 |
| total TAN time | 220 | μsec | UNKNOWN; 1971 | UNKNOWN | maximum; 130 CORDIC + 85 prescale/normalize/misc. + 5 data transfer | p.384 |
| total ATAN time | 90 | μsec | UNKNOWN; 1971 | UNKNOWN | maximum; 70 CORDIC + 15 prescale/normalize/misc. + 5 data transfer | p.384 |
| total SINH time | 130 | μsec | UNKNOWN; 1971 | UNKNOWN | maximum; 70 CORDIC + 55 prescale/normalize/misc. + 5 data transfer | p.384 |
| total COSH time | 130 | μsec | UNKNOWN; 1971 | UNKNOWN | maximum; 70 CORDIC + 55 prescale/normalize/misc. + 5 data transfer | p.384 |
| total TANH time | 190 | μsec | UNKNOWN; 1971 | UNKNOWN | maximum; 130 CORDIC + 55 prescale/normalize/misc. + 5 data transfer | p.384 |
| total ATANH time | 120 | μsec | UNKNOWN; 1971 | UNKNOWN | maximum; 70 CORDIC + 45 prescale/normalize/misc. + 5 data transfer | p.384 |
| total EXPONENTIAL time | 130 | μsec | UNKNOWN; 1971 | UNKNOWN | maximum; 70 CORDIC + 55 prescale/normalize/misc. + 5 data transfer | p.384 |
| total LOGARITHM time | 120 | μsec | UNKNOWN; 1971 | UNKNOWN | maximum; 70 CORDIC + 45 prescale/normalize/misc. + 5 data transfer | p.384 |
| total SQUARE-ROOT time | 100 | μsec | UNKNOWN; 1971 | UNKNOWN | maximum; 70 CORDIC + 25 prescale/normalize/misc. + 5 data transfer | p.384 |
errors_and_checks: The nth-step theoretical accuracy is set by the last rotation; choosing Fn-1 = L gives approximately L digits. Truncating intermediate results over L iterations causes at most log2 L bits of error, which L+log2 L intermediate bits render harmless. The built processor produces 40-bit results (approximately 12 decimal digits), with accuracy limited by input truncation; no ulp or rounding-mode bound is reported. # p.382-384
conditions: Circular/linear/hyperbolic binary sequences have maximum angle domains of approximately 1.74/1.0/1.13 and radius factors of approximately 1.65/1.0/0.80. # p.381; Hyperbolic convergence requires repeated shift indices. # p.381; Small floating-point arguments require normalized registers and the exponent-scaled recurrence to preserve all L result bits. # p.383
evidence: Equations (3)-(45), Figures 2-4, Tables I-II and IV, “Convergence Scheme,” “Use of Shifters,” “Accuracy,” and “Hardware Implementation,” pp.379-384.

### range_reduction  (role: instantiates)
mechanism: Function-specific prescaling identities reduce large arguments to the CORDIC convergence domain. Trigonometric arguments are divided by π/2 and selected by Q mod 4; logarithms split a value into mantissa M and binary exponent E; hyperbolic, exponential, square-root, and multiplication identities similarly transform operands and reconstruct results. # p.382
choices:
  method: identity_prescaling [outside domain]  # p.382
  reduction_type: additive_and_multiplicative [outside domain]  # p.382
new_choices:
  reconstruction_selector: quotient_or_exponent_bits — Q mod 4 or E controls sign/function selection and result rescaling  # p.382
slots: none
parameters: Trigonometric remainder |D| < π/2; hyperbolic/exponential remainder |D| < loge 2 = 0.69; logarithm mantissa 0.5 < M < 1.0. # p.382
results: none
errors_and_checks: none
conditions: Prescaling is required when an argument lies outside the finite convergence domain. # p.382
evidence: Table III and “Extending the Domain,” p.382.

## new_families
none

## space_gaps
* `cordic.scale_compensation` lacks initial-value correction by the reciprocal radius factor 1/K. # p.381, p.383
* `cordic` lacks radix/shift-sequence and repeated-hyperbolic-iteration choices. # p.381
* `range_reduction.method` lacks function-specific CORDIC prescaling identities. # p.382

## open_questions
* The paper does not state one fixed iteration count or initiation interval for the 40-bit processor; it defines termination through Fm,i-E = L and reports execution time instead. # p.383-384
* The paper does not state a rounding mode or maximum-ulp guarantee for the built processor. # p.382, p.384
