---
handle: muller_1994
citation: Muller, "Some Characterizations of Functions Computable in On-Line Arithmetic", IEEE Transactions on Computers, 1994
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU, other]
formats: [fixed_point_radix_r_signed_digit]
authority: landmark
pages_read: 152-155 / 4
---

## summary
The paper proves that sufficiently regular functions computable on-line by bounded-size finite automata are piecewise affine with rational coefficients and rational breakpoints. p.154 A bounded-size operator therefore cannot perform arbitrary-length multiplication/division/square root, although affine functions with rational coefficients can use such an operator. p.152, p.155

## families
### online_arithmetic_unit  (role: analyzes)
mechanism: A bounded-size on-line operator is modeled as a finite-state transducer. At step n, the transducer derives its next state and output digit from its current state and the incoming operand digit or digits; output digit j follows input digit j+δ. p.152-153 The finite state set makes the operator size independent of operand length. p.152
choices:
  none
new_choices:
  operator_size_scaling: bounded_independent_of_operand_length — whether storage and computation remain independent of operand length # p.152
  realization_model: finite_automaton_transducer — the state-machine model used to characterize bounded-size operators # p.152-153
slots:
  none
parameters: delay δ; M finite states; one or p input variables; operands/results streamed most-significant digit first; arbitrary operand length # p.152-153
results: none
errors_and_checks: none
conditions: A one-variable function with piecewise continuous second derivative is affine with rational coefficients on each interval of continuity when a finite automaton computes it on-line. p.154 Its breakpoints are rational. p.154 A corresponding two-variable function with continuous second derivatives in rectangles has the form βx+γy+δ with rational coefficients, and the result generalizes to more variables. p.154-155 Multiplication/division/square root of arbitrary-length operands cannot use bounded-size on-line operators. p.152, p.155
evidence: Introduction and operator model, p.152-153; Theorems 1-3, p.154-155; Conclusion, p.155

### generalized_signed_digit  (role: analyzes)
mechanism: Operands use a fixed-point radix-r signed-digit system with digit set Dα = {-α, -α+1, ..., 0, 1, ..., α}. p.152-153 Redundancy permits several digit chains to represent the same number, so valid transducers must map equivalent input chains to output chains representing the same result. p.152-153
choices:
  none
new_choices:
  digit_alphabet_parameter: Dα = {-α, ..., α} — the symbolic signed-digit alphabet used by the finite-automaton model # p.152-153
slots:
  none
parameters: radix r; digit bound α; fixed-point numbers considered in [0,1], with the results stated to extend to any interval # p.152-153
results: none
errors_and_checks: none
conditions: Most-significant-digit-first on-line flow requires a redundant number system; carry-save representation is possible, while the literature considered here uses Avizienis signed-digit systems. p.152 A rational number can have an aperiodic signed-digit representation but also has an eventually periodic representation; a finite automaton maps an eventually periodic input to an eventually periodic output. p.154
evidence: Introduction, p.152; number-system definition, p.152-153; periodic-representation argument, p.154

## new_families
none

## space_gaps
* `online_arithmetic_unit` lacks an `operator_size_scaling` choice for the paper's bounded/proportional/superlinear classification. p.152
* `online_arithmetic_unit` lacks a `realization_model` choice for finite-automaton transducers. p.152-153
* `generalized_signed_digit.redundancy` cannot express the paper's symbolic digit-bound parameter α. p.152-153

## open_questions
* The paper conjectures that the second class of functions, including multiplication/division/square root, equals the algebraic functions, but it does not prove the conjecture. p.155
* The theorem excludes bounded-size operators for multiplication/division/square root; the proportional-size classification is presented as empirical rather than proved. p.152, p.155
