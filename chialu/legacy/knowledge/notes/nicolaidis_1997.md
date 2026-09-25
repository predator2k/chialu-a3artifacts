---
handle: nicolaidis_1997
citation: M. Nicolaidis, R. O. Duarte, S. Manich, J. Figueras, "Fault-Secure Parity Prediction Arithmetic Operators", IEEE Design & Test of Computers, vol. 14, pp. 60-71, 1997
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [binary_integer]
authority: landmark
pages_read: 60-71 / 12
---

## summary
The paper derives necessary and sufficient conditions for fault-secure parity prediction in cellular adders/multipliers/dividers and instantiates those conditions with redundant-carry cells (pp.61-68). Synthesized multiplier/divider implementations use an ES2 1.0-µm CMOS standard-cell library (pp.69-70).

## families
### parity_prediction_adder  (role: extends)
mechanism: Each full-/half-adder cell generates its sum, normal carry, and parity-prediction carry so faults change the result parity or predicted parity by opposite parity. The compact cell shares propagate signal P only when any fault affecting both carries also affects S (pp.61-64).
choices:
  parity_groups: 1   # p.64
  carry_scheme: duplicate_carry   # pp.61-64
new_choices:
  replica_cell_style: {independent_outputs, shared_propagate} — selects Figure 3/type 1 or Figure 4/type 2 carry-replica logic   # pp.62-64
slots:
  carry_replica: ripple_carry   # p.64
parameters: n-bit ripple-carry adder/ALU; one redundant carry and carry-parity contribution per cell   # p.64
results:
| metric | value | unit | technology / device | baseline | condition | page |
| hardware overhead | 21.4 | % | UNKNOWN / 1993 | conventional carry-lookahead adder | 16-bit self-checking carry-lookahead adder | p.70 |
errors_and_checks: Fault secure for arbitrary cell-function changes, including combinational/sequential functions, stuck-at/stuck-open faults, and interconnection-branch stuck-at faults; false-alarm behavior is UNKNOWN (p.63).
conditions: Single-cell fan-out networks satisfy the proof assumptions (pp.63-64). Ripple-carry adders and ALUs using the proposed cells are fault secure against cell/primary-input faults (p.64).
evidence: Lemmas 1-5, Theorems 1-2, Figures 1-5 (pp.61-64).

### parity_prediction_multiplier  (role: proposes)
mechanism: AND-generated partial products enter a Braun array or Wallace full-/half-adder network whose cells use redundant carries. The carry parity combines with operand parities to predict product parity. A carry-lookahead final adder instead uses redundant carries and a double-rail checker (pp.64-66).
choices:
  recoding: none   # pp.64-65
  check_depth: final_only   # pp.64-65
  fault_secure_structuring: true   # pp.64-65
new_choices:
  replica_cell_style: {type_1_independent, type_2_shared_propagate} — selects the full-adder implementation   # pp.62-64
slots:
  comparator: two_rail_tree   # p.65
parameters: Braun/Wallace 4×4, 8×8, 16×16, and 32×32 multipliers   # pp.69-70
results:
| metric | value | unit | technology / device | baseline | condition | page |
| area simple/secure/overhead | 0.05/0.09/74.50 | mm2/mm2/% | ES2 1.0-µm CMOS / 1997 | simple Braun | 4×4, FA type 1 | p.69 |
| area simple/secure/overhead | 0.05/0.08/49.75 | mm2/mm2/% | ES2 1.0-µm CMOS / 1997 | simple Braun | 4×4, FA type 2 | p.69 |
| area simple/secure/overhead | 0.26/0.46/78.24 | mm2/mm2/% | ES2 1.0-µm CMOS / 1997 | simple Braun | 8×8, FA type 1 | p.69 |
| area simple/secure/overhead | 0.26/0.38/47.83 | mm2/mm2/% | ES2 1.0-µm CMOS / 1997 | simple Braun | 8×8, FA type 2 | p.69 |
| area simple/secure/overhead | 1.13/2.03/79.85 | mm2/mm2/% | ES2 1.0-µm CMOS / 1997 | simple Braun | 16×16, FA type 1 | p.69 |
| area simple/secure/overhead | 1.13/1.66/47.32 | mm2/mm2/% | ES2 1.0-µm CMOS / 1997 | simple Braun | 16×16, FA type 2 | p.69 |
| area simple/secure/overhead | 4.70/8.49/80.61 | mm2/mm2/% | ES2 1.0-µm CMOS / 1997 | simple Braun | 32×32, FA type 1 | p.69 |
| area simple/secure/overhead | 4.70/6.92/47.14 | mm2/mm2/% | ES2 1.0-µm CMOS / 1997 | simple Braun | 32×32, FA type 2 | p.69 |
| delay simple/secure/overhead | 14.78/18.06/22.19 | ns/ns/% | ES2 1.0-µm CMOS / 1997 | simple Braun | 4×4, FA type 1 | p.69 |
| delay simple/secure/overhead | 14.78/19.31/30.65 | ns/ns/% | ES2 1.0-µm CMOS / 1997 | simple Braun | 4×4, FA type 2 | p.69 |
| delay simple/secure/overhead | 34.37/37.85/10.13 | ns/ns/% | ES2 1.0-µm CMOS / 1997 | simple Braun | 8×8, FA type 1 | p.69 |
| delay simple/secure/overhead | 34.37/42.20/22.78 | ns/ns/% | ES2 1.0-µm CMOS / 1997 | simple Braun | 8×8, FA type 2 | p.69 |
| delay simple/secure/overhead | 74.71/78.98/6.72 | ns/ns/% | ES2 1.0-µm CMOS / 1997 | simple Braun | 16×16, FA type 1 | p.69 |
| delay simple/secure/overhead | 74.71/88.40/18.32 | ns/ns/% | ES2 1.0-µm CMOS / 1997 | simple Braun | 16×16, FA type 2 | p.69 |
| delay simple/secure/overhead | 155.26/164.68/6.07 | ns/ns/% | ES2 1.0-µm CMOS / 1997 | simple Braun | 32×32, FA type 1 | p.69 |
| delay simple/secure/overhead | 155.26/183.32/18.07 | ns/ns/% | ES2 1.0-µm CMOS / 1997 | simple Braun | 32×32, FA type 2 | p.69 |
| area simple/secure/overhead | 0.07/0.11/50.63 | mm2/mm2/% | ES2 1.0-µm CMOS / 1997 | simple Wallace | 4×4, FA type 1 | p.69 |
| area simple/secure/overhead | 0.07/0.10/43.76 | mm2/mm2/% | ES2 1.0-µm CMOS / 1997 | simple Wallace | 4×4, FA type 2 | p.69 |
| area simple/secure/overhead | 0.31/0.50/64.64 | mm2/mm2/% | ES2 1.0-µm CMOS / 1997 | simple Wallace | 8×8, FA type 1 | p.69 |
| area simple/secure/overhead | 0.31/0.45/45.83 | mm2/mm2/% | ES2 1.0-µm CMOS / 1997 | simple Wallace | 8×8, FA type 2 | p.69 |
| area simple/secure/overhead | 1.23/2.12/72.39 | mm2/mm2/% | ES2 1.0-µm CMOS / 1997 | simple Wallace | 16×16, FA type 1 | p.69 |
| area simple/secure/overhead | 1.23/1.80/46.45 | mm2/mm2/% | ES2 1.0-µm CMOS / 1997 | simple Wallace | 16×16, FA type 2 | p.69 |
| area simple/secure/overhead | 4.92/8.70/76.64 | mm2/mm2/% | ES2 1.0-µm CMOS / 1997 | simple Wallace | 32×32, FA type 1 | p.69 |
| area simple/secure/overhead | 4.92/7.22/46.71 | mm2/mm2/% | ES2 1.0-µm CMOS / 1997 | simple Wallace | 32×32, FA type 2 | p.69 |
| delay simple/secure/overhead | 16.27/21.00/29.17 | ns/ns/% | ES2 1.0-µm CMOS / 1997 | simple Wallace | 4×4, FA type 1 | p.70 |
| delay simple/secure/overhead | 16.27/21.03/29.26 | ns/ns/% | ES2 1.0-µm CMOS / 1997 | simple Wallace | 4×4, FA type 2 | p.70 |
| delay simple/secure/overhead | 26.95/33.55/24.49 | ns/ns/% | ES2 1.0-µm CMOS / 1997 | simple Wallace | 8×8, FA type 1 | p.70 |
| delay simple/secure/overhead | 26.95/34.46/27.87 | ns/ns/% | ES2 1.0-µm CMOS / 1997 | simple Wallace | 8×8, FA type 2 | p.70 |
| delay simple/secure/overhead | 42.04/49.85/18.58 | ns/ns/% | ES2 1.0-µm CMOS / 1997 | simple Wallace | 16×16, FA type 1 | p.70 |
| delay simple/secure/overhead | 42.04/52.90/25.83 | ns/ns/% | ES2 1.0-µm CMOS / 1997 | simple Wallace | 16×16, FA type 2 | p.70 |
| delay simple/secure/overhead | 77.79/84.75/8.95 | ns/ns/% | ES2 1.0-µm CMOS / 1997 | simple Wallace | 32×32, FA type 1 | p.70 |
| delay simple/secure/overhead | 77.79/93.82/20.61 | ns/ns/% | ES2 1.0-µm CMOS / 1997 | simple Wallace | 32×32, FA type 2 | p.70 |
errors_and_checks: The design detects modeled single faults in multiplier cells/AND gates; primary-input faults require input checking when PB=0 can mask an A-input fault (p.65).
conditions: Ripple final adders retain the cellular proof (p.65). Carry-lookahead final adders require redundant carries and a double-rail checker (p.65). FA type 2 reduces area but increases worst-case parity delay relative to type 1 (pp.69-70).
evidence: Figures 6-8; Tables 1-4 (pp.64-70).

## new_families
### parity_prediction_divider  (domain: checker, closest: parity_prediction_multiplier, why_not: divider multiple-cell fan-out requires protection choices absent from the multiplier family)
mechanism: A nonrestoring array replaces each CAS adder with a redundant-carry cell. Carries feeding multiple cells use cut-safe routing or duplicated normal/redundant signals checked by a double-rail checker. Separate quotient/remainder parity equations combine partial carry/input parities (pp.66-69).
choices: fanout_class: {odd_cell, even_cell}; interconnect_protection: {cut_safe_routing, duplicated_two_rail}; primary_input_checking: Bool
results:
| metric | value | unit | technology / device | baseline | condition | page |
| area simple/secure/overhead | 0.06/1.02/59.97 | mm2/mm2/% | ES2 1.0-µm CMOS / 1997 | simple divider | 4×4, FA type 1 | p.70 |
| area simple/secure/overhead | 0.06/0.09/37.28 | mm2/mm2/% | ES2 1.0-µm CMOS / 1997 | simple divider | 4×4, FA type 2 | p.70 |
| area simple/secure/overhead | 0.31/0.51/63.38 | mm2/mm2/% | ES2 1.0-µm CMOS / 1997 | simple divider | 8×8, FA type 1 | p.70 |
| area simple/secure/overhead | 0.31/0.42/35.51 | mm2/mm2/% | ES2 1.0-µm CMOS / 1997 | simple divider | 8×8, FA type 2 | p.70 |
| area simple/secure/overhead | 1.35/2.23/64.86 | mm2/mm2/% | ES2 1.0-µm CMOS / 1997 | simple divider | 16×16, FA type 1 | p.70 |
| area simple/secure/overhead | 1.35/1.83/35.04 | mm2/mm2/% | ES2 1.0-µm CMOS / 1997 | simple divider | 16×16, FA type 2 | p.70 |
| area simple/secure/overhead | 5.64/9.34/65.56 | mm2/mm2/% | ES2 1.0-µm CMOS / 1997 | simple divider | 32×32, FA type 1 | p.70 |
| area simple/secure/overhead | 5.64/7.61/34.88 | mm2/mm2/% | ES2 1.0-µm CMOS / 1997 | simple divider | 32×32, FA type 2 | p.70 |
| delay simple/secure/overhead | 16.26/20.77/27.74 | ns/ns/% | ES2 1.0-µm CMOS / 1997 | simple divider | 4×4, FA type 1 | p.70 |
| delay simple/secure/overhead | 16.26/22.21/36.59 | ns/ns/% | ES2 1.0-µm CMOS / 1997 | simple divider | 4×4, FA type 2 | p.70 |
| delay simple/secure/overhead | 37.81/43.53/15.13 | ns/ns/% | ES2 1.0-µm CMOS / 1997 | simple divider | 8×8, FA type 1 | p.70 |
| delay simple/secure/overhead | 37.81/48.53/28.35 | ns/ns/% | ES2 1.0-µm CMOS / 1997 | simple divider | 8×8, FA type 2 | p.70 |
| delay simple/secure/overhead | 82.18/90.83/10.53 | ns/ns/% | ES2 1.0-µm CMOS / 1997 | simple divider | 16×16, FA type 1 | p.70 |
| delay simple/secure/overhead | 82.18/101.66/23.70 | ns/ns/% | ES2 1.0-µm CMOS / 1997 | simple divider | 16×16, FA type 2 | p.70 |
| delay simple/secure/overhead | 170.79/189.38/10.88 | ns/ns/% | ES2 1.0-µm CMOS / 1997 | simple divider | 32×32, FA type 1 | p.70 |
| delay simple/secure/overhead | 170.79/210.82/23.44 | ns/ns/% | ES2 1.0-µm CMOS / 1997 | simple divider | 32×32, FA type 2 | p.70 |
evidence: Theorem 3, Figures 9-11, Tables 5-6 (pp.66-70).

## space_gaps
* parity_prediction_multiplier lacks a choice for independent redundant-carry generation and type 1/type 2 cell sharing (pp.62-65).
* checker lacks a parity-prediction divider family with multiple-cell fan-out/interconnection protection (pp.66-69).

## open_questions
* Table 5 prints the 4×4 FA type 1 secure-area entry as 1.02 mm2, which is inconsistent with the printed 0.06 mm2 baseline and 59.97% overhead (p.70).
* Tables 3-6 retain “Braun” headings although Tables 3-4 describe Wallace multipliers and Tables 5-6 describe dividers (pp.69-70).
* The evaluated operands’ signedness is not stated.
