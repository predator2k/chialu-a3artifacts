---
handle: oklobdzija_1982
citation: Oklobdzija, Ercegovac, "An On-Line Square Root Algorithm", IEEE Transactions on Computers, 1982
actual_citation: same
status: ok
kind: paper
unit_classes: [other]
formats: [radix_r_floating_point]
authority: landmark
pages_read: 70-75 / 6
---

## summary
The document derives a most-significant-digit-first floating-point square-root algorithm with an on-line delay of one digit (pp.70-72). The implementation uses redundant digits, truncated remainder selection, and cascaded modular LSI/VLSI slices whose recursion time does not depend on precision (pp.71-74).

## families
### online_arithmetic_unit  (role: extends)
mechanism: The algorithm consumes one new operand digit and produces one irrevocable result digit at each step after an on-line delay of one. The recurrence maintains a scaled partial remainder and selects each square-root digit by comparing its three most significant digits with truncated selection constants. Limited carry/borrow propagation addition, single-digit multiplication, and concatenation make each computational step invariant in time (pp.70-72).
choices:
  radix: general r >= 4 [outside domain]   # p.71
  online_delay: 1   # p.71
  digit_set: maximally_redundant   # p.71
  residual_form: signed_digit   # pp.70,74
new_choices:
  operation: square_root — identifies the on-line function implemented   # pp.70,72
  residual_estimate_digits: 3 — fixes the partial-remainder precision used for digit selection   # pp.71-72
  selection_constant_generation: {table_lookup, successive_approximation, hybrid} — selects the hardware method for producing comparison constants   # p.74
slots:
  none
parameters: positive normalized radix-r floating-point input; general radix r >= 4; maximal digit magnitude ρ = r-1; scaling p = 2; overlap exponent t = 2; one result digit per step; examples use r = 10 and r = 256; d-digit RM slices; at most n/2 RM modules for n result digits   # pp.70-74
results:
| metric | value | unit | technology / device | baseline | condition | page |
| online delay | 1 | digit | UNKNOWN / 1982 | basic on-line operations have delays between 1 and 4 digits | maximally redundant digits and p = 2 | p.71 |
| partial-remainder comparison precision | 3 | radix-r digits | UNKNOWN / 1982 | full partial remainder | t = 2 and r >= 4 | pp.71-72 |
| result precision from e modules | 2(n + t + 1) | digits | UNKNOWN / 1982 | UNKNOWN | cascaded recursion modules | p.74 |
| recursion-module count | no more than n/2 | modules | UNKNOWN / 1982 | UNKNOWN | d-digit RM modules and n-digit fraction precision | p.74 |
errors_and_checks: The m-digit result error satisfies |e| < (c/2)r^(-m+1) after selecting p = 2 (p.71). The document mentions that serial error-checking codes can be applied efficiently to on-line arithmetic, but it reports no implemented checker, coverage, false-alarm rate, or alias rate (p.70).
conditions: The algorithm requires redundant representation because nonredundant carry propagation would increase the on-line delay (p.70). The t = 2 selection construction applies to radix r >= 4 (p.71). Radix r = 2 requires a different algorithm (p.71). The input is shifted one radix position right to ensure positive overlap, which places X in [r^-2, r^-1) (pp.71-72). The modular implementation assumes limited carry/borrow adders and single-digit multipliers (pp.70,74).
evidence: Abstract; §I; §II, equations (5)-(31) and Fig. 1; §III, S-Algorithm and Figs. 2-3; §IV, Figs. 4-6; §V (pp.70-74).

### generalized_signed_digit  (role: instantiates)
mechanism: The operand/result fractions use the redundant digit set Dρ = {-ρ, ..., -1, 0, 1, ..., ρ}, with r/2 < ρ < r. Maximal redundancy permits a one-digit on-line delay and three-digit remainder estimates. The implementation limits carry/borrow propagation to one or two digit positions and forms the partial remainder with a carry-save adder tree (pp.70-71,74).
choices:
  radix: general r >= 4 [outside domain]   # p.71
  redundancy: maximal   # p.71
  addition_scheme: two_stage_limited_carry   # pp.70,74
new_choices:
  none
slots:
  none
parameters: Dρ with ρ = r-1; one or two digit positions of carry/borrow propagation; d-digit modular slices   # pp.70-71,74
results:
| metric | value | unit | technology / device | baseline | condition | page |
| carry/borrow propagation | 1 or 2 | digit positions | UNKNOWN / 1982 | nonredundant carry propagation | redundant number representation | p.70 |
errors_and_checks: none
conditions: Maximal redundancy reduces the required on-line delay and permits fewer remainder digits in the comparison process (p.71). The conventional-form argument requires no input conversion when the maximal digit set is used (p.71).
evidence: §I redundancy discussion; §II selection derivation; §IV implementation description (pp.70-71,74).

## new_families
none

## space_gaps
* The `online_arithmetic_unit.radix` domain excludes the demonstrated decimal radix r = 10 and radix r = 256, although the algorithm is stated for general r >= 4 (pp.71,73).
* The `online_arithmetic_unit` family lacks an `operation` choice for square root (pp.70-72).
* The `online_arithmetic_unit` family lacks choices for residual-estimate width and selection-constant generation, which determine the digit-selection hardware (pp.71-72,74).

## open_questions
* The document does not specify a binary encoding for the signed digits.
* The document permits table lookup, successive approximation, or a combination for selection constants without fixing one implementation (p.74).
* The document gives no fabrication technology, clock period, area, power, or measured implementation results.
