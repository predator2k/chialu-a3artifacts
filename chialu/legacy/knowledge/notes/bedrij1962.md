---
handle: bedrij1962
citation: O. J. Bedrij, "Carry-Select Adder", IRE Transactions on Electronic Computers, vol. EC-11, pp. 340-346, 1962.
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [int25, int100]
authority: landmark
pages_read: 340-346 / 7
---

## summary
The paper proposes a carry-select adder that generates two subsums for each section and selects the true subsum using independently generated multiple-radix carries (pp.340-344). A 100-bit design requires 1122 logical elements and 11 logical time levels, compared with 500 elements and 202 levels for a ripple-carry adder (p.346).

## families
### carry_select  (role: proposes)
mechanism: The operands are divided into sections that simultaneously form one subsum with a forced carry input and another without a forced carry input. Multiple-radix carry logic determines the actual carry into each section and selects the corresponding subsum. The 100-bit implementation arranges 5-bit sections into four 25-bit groups and combines each group's X/Z carry functions to form C25, C50, C75, and C100. Primary A V B and AB functions are shared between the two subsum paths rather than completely duplicated (pp.340-344).
choices:
  block_sizing: uniform   # pp.343-344
  duplication: shared_primary_functions [outside domain]   # pp.340, 342
  select_source: multiple_radix_group_carries [outside domain]   # pp.343-344
new_choices:
  carry_hierarchy: multilevel_multiple_radix — sections form groups whose X/Z carry functions are combined at successive levels   # pp.343-344
slots:
  block_adder: ripple_carry [carry path=short sequential]   # pp.340, 343
parameters: 25-bit example: five 5-bit sections; 100-bit design: twenty 5-bit sections arranged as four 25-bit groups; 6-step operating sequence   # pp.340, 343-344
results:
| metric | value | unit | technology / device | baseline | condition | page |
| carry-select hardware | 1122 | logical elements | UNKNOWN; 1962 | ripple-carry: 500 logical elements | 100-bit adder | p.346 |
| carry-select delay | 11 | logical time levels | UNKNOWN; 1962 | ripple-carry: 202 logical time levels | 100-bit adder | p.346 |
| speed improvement | 20 | factor | UNKNOWN; 1962 | 100-bit ripple-carry adder | stated comparison | p.346 |
| hardware increase | approximately twice | hardware | UNKNOWN; 1962 | 100-bit ripple-carry adder | stated comparison | p.346 |
errors_and_checks: none
conditions: The subsum-generation path and carry-select path should be approximately equal, because producing subsums before selection carries provides no speed advantage (p.343). Short ripple-carry paths within sections save components (p.343). Carry-selection circuits become more costly and complex as the number of sections grows, so large adders use higher-order radix grouping (p.343). The reported section/group arrangement is illustrative and can be modified (p.346).
evidence: Summary and basic theory (p.340); duplicated 5-bit section in Fig. 2 and (1)-(12) (pp.342-343); selection equations (13)-(17) (p.343); group-carry equations (18)-(23), 100-bit sequence, and Figs. 3-4 (pp.344-345); Table I (p.346).

### ripple_carry  (role: compares)
mechanism: The comparison adder generates sums sequentially from the lowest-order bit, with each carry propagated into the next position. Short ripple-carry paths also generate the provisional sums inside each carry-select section (pp.340, 343).
choices:
new_choices:
  none
slots:
  none
parameters: 100-bit comparison adder; 5-bit ripple paths inside the proposed carry-select sections   # pp.343, 346
results:
| metric | value | unit | technology / device | baseline | condition | page |
| ripple-carry hardware | 500 | logical elements | UNKNOWN; 1962 | carry-select: 1122 logical elements | 100-bit adder | p.346 |
| ripple-carry delay | 202 | logical time levels | UNKNOWN; 1962 | carry-select: 11 logical time levels | 100-bit adder | p.346 |
errors_and_checks: none
conditions: The 100-bit ripple-carry design serves as the hardware and logical-delay baseline for Table I (p.346).
evidence: Introduction (p.340); Table I (p.346).

## new_families
none

## space_gaps
* `carry_select.duplication` lacks a value for two provisional-sum paths that share the primary A V B and AB functions rather than duplicating complete adders (pp.340, 342).
* `carry_select.select_source` lacks the paper's hierarchical multiple-radix X/Z group-carry network (pp.343-344).
* `carry_select` lacks a choice for single-level versus multilevel section/group organization (pp.343-344).

## open_questions
* The paper does not identify the circuit technology or physical delay represented by one logical time level.
* The supplied text does not provide a gate-by-gate derivation of the 1122-element and 11-level totals in Table I.
