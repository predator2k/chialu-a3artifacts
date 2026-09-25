---
handle: irwin_owens_1987
citation: Irwin, Owens, "Digit-Pipelined Arithmetic as Illustrated by the Paste-Up System: A Tutorial", IEEE Computer, 1987
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU, VEC_DOT_ACC]
formats: [base4_signed_digit, fixed_point_twos_complement]
authority: survey
pages_read: 61-73 / 13
---

## summary
The tutorial defines the Paste-Up system for MSD-first, base-4 signed-digit arithmetic with one-cycle primitive latency and one result digit per subsequent cycle. It presents add/compare/scale primitives, a semi-systolic programmable multiplier, format converters, and a restricted matrix-vector processor, while explaining why a conforming divider had not been built. # pp.61-72

## families
### generalized_signed_digit  (role: instantiates)
mechanism: The adder first maps two input digits into an interim sum and carry. A second digit addition combines the previous interim sum with the present carry and is guaranteed to be carry free because the interim digit sets are restricted. The Paste-Up system uses symmetric base-4 signed-digit sets and twos-complement binary encodings. # pp.62,64-65
choices:
  radix: 4   # p.62
  redundancy: maximal (operand set); minimal (recoded/interim sets)   # pp.62,64-65
  digit_encoding: twos_complement   # p.62
  addition_scheme: two_stage_limited_carry   # p.65
new_choices:
  symmetric_digit_set: true — the largest negative and positive digits have equal magnitude   # p.64
slots:
  none
parameters: p base-4 digits; one stored interim-sum digit; primitive latency one cycle; two digit-adder cells and one digit storage cell   # pp.62-65
results:
| metric | value | unit | technology / device | baseline | condition | page |
| adder layout dimensions | 250λ by 250λ | as printed | custom-logic, double-metal CMOS; 1987 | UNKNOWN | Add primitive | p.65 |
| full-precision parallel-add delay | 4 | gate delays | UNKNOWN; 1987 | UNKNOWN | carry-limited word-parallel form of the same technique | p.65 |
errors_and_checks: Overflow is disallowed by the system convention. The unused digit encoding `10` is available for overflow/NAN signaling or error detection, but no detection implementation or coverage is reported. # p.62
conditions: Base 4 is selected because base 8 requires more complex logic/interconnect, while a redundant base-2 MSD-first adder cannot have latency one. # pp.64-65
evidence: Table 1; Figures 3-4; Tables 5-6; pp.62,64-65.

### online_arithmetic_unit  (role: instantiates)
mechanism: Operand digits enter MSD first, one set per clock cycle. A primitive emits its first result after a fixed online delay of one digit and emits one result digit during each subsequent cycle. Time-aligned operands, an MSD synchronization signal, and fixed primitive latency permit direct digit-level pipelines of nearest-neighbor components. # pp.62-64
choices:
  radix: 4   # p.62
  online_delay: 1   # p.63
  digit_set: minimally_redundant and maximally_redundant   # pp.62,64
  residual_form: signed_digit   # pp.64-65
new_choices:
  digit_order: msdf — Paste-Up defines right-directed communication as MSD first   # pp.62,64
slots:
  none
parameters: fixed word length p digits; one input/output digit per cycle; two-phase nonoverlapping clock; 10-GD worst-case clock cycle   # pp.62-63
results:
| metric | value | unit | technology / device | baseline | condition | page |
| worst-case clock cycle | 10 | gate delays | CMOS; 1987 | UNKNOWN | each phase high for four GDs with two one-GD intervals | p.62 |
| steady-state output rate | 1 | result digit per cycle | Paste-Up system; 1987 | UNKNOWN | after the first result digit | p.63 |
errors_and_checks: The communication encoding reserves `10`, but the paper reports no fault model, coverage, false-alarm behavior, or alias rate. # p.62
conditions: Primitive components must be fine grained and use local/nearest-neighbor interconnect. Shift distance must be one digit for latency-one online shifting, while zero detection requires full-precision latency. # pp.63-64
evidence: Figure 2; Tables 2-4; pp.62-65.

### serial_serial_parallel  (role: instantiates)
mechanism: The semi-systolic programmable multiplier preloads recoded multiplier digits into generalized scale cells. The multiplicand is broadcast MSD first, one digit per cycle, while intermediate data moves between neighboring cells. The programmable organization trades a separate programming interval for low processing latency and limited intercomponent wiring. # pp.70-71
choices:
  serial_operands: one   # p.70
  digit_size_bits: 2   # pp.62,70
new_choices:
  operand_loading: preloaded_programmable — the multiplier is loaded before processing   # p.70
  systolic_style: semi_systolic — multiplicand digits are broadcast while intermediate values use neighbor links   # p.70
slots:
  none
parameters: p-digit operands; p+3 generalized Sca cells; processing latency two cycles; programming time excluded; one multiplicand digit broadcast per cycle   # pp.70-71
results:
| metric | value | unit | technology / device | baseline | condition | page |
| processing latency | 2 | cycles | Paste-Up composite design; 1987 | pure systolic latency O(p) | programming time excluded | p.70 |
| component count | p+3 | generalized Sca components | Paste-Up composite design; 1987 | UNKNOWN | multiplication of two p-digit values | p.70 |
errors_and_checks: No numerical error is reported; multiplier digits are recoded into `[-2,-1,0,1,2]`, and overflow remains disallowed by the system convention. # pp.62,70
conditions: The low latency assumes repeated operations with the same preloaded multiplier. Portions of the multiplier were prototyped rather than a complete implementation being reported. # pp.70,72
evidence: Figures 11-13; Tables 12-13; pp.70-72.

### srt_high_radix  (role: analyzes)
mechanism: The discussed base-4 online division approach selects each quotient digit by inspecting the three most significant divisor digits and three most significant shifted-partial-remainder digits. A normalized divisor permits bounded-precision selection, but the required full-precision state transfers prevent a linear array from meeting Paste-Up restrictions. # pp.71-72
choices:
  radix: 4   # pp.64,71
new_choices:
  none
slots:
  none
parameters: quotient-selection inspection width three divisor digits and three partial-remainder digits; latency at least three cycles   # p.72
results:
| metric | value | unit | technology / device | baseline | condition | page |
| minimum implied latency | at least 3 | cycles | UNKNOWN; 1987 | one-cycle Paste-Up primitive | normalized divisor and three-digit selection inspection | p.72 |
errors_and_checks: none
conditions: The divisor must satisfy `1/2 ≤ X_in < 1`. No divider conforming to all Paste-Up conventions had been designed. # p.72
evidence: Division discussion, pp.71-72.

## new_families
### online_signed_digit_comparator  (domain: redundant: online arithmetic, closest: prefix_comparator, why_not: the design is a sequential finite-state scan of redundant MSD-first digits rather than a prefix or subtractor comparator)
mechanism: A five-state finite-state machine examines aligned signed digits MSD first and emits a numerically equivalent digit stream for the minimum operand. The state preserves enough ordering information to handle redundant representations; a corresponding machine implements maximum. # p.66
choices: function: {minimum, maximum}; state_count: Int[5..5:1]; digit_order: {msdf}
results:
| metric | value | unit | technology / device | baseline | condition | page |
| latency | 1 | digit | custom-logic, double-metal CMOS; 1987 | UNKNOWN | Min primitive | p.66 |
| layout dimensions | 350λ by 350λ | as printed | custom-logic, double-metal CMOS; 1987 | UNKNOWN | Min primitive | p.66 |
evidence: Figures 5-6; Table 7; p.66.

### restricted_coefficient_matrix_vector  (domain: dot: dot-product / FMA / MAC, closest: pairwise_tree, why_not: the processor uses a nearest-neighbor Pos/Neg/Del mesh for coefficients `-1,0,1` rather than per-element multipliers and a reduction tree)
mechanism: An `m × n` mesh implements a fixed matrix whose coefficients are `-1`, `0`, or `1`. Positive, negative, and delay primitives receive digit-skewed vector elements and propagate intermediate results through nearest-neighbor links. # p.72
choices: coefficient_set: {-1, 0, 1}; interconnect: {nearest_neighbor_mesh}; input_schedule: {digit_skewed}
results:
| metric | value | unit | technology / device | baseline | condition | page |
| component count | n×m | primitive components | Paste-Up composite design; 1987 | UNKNOWN | m×n matrix and n-element vector | p.72 |
| first-output latency | n+1 | cycles | Paste-Up composite design; 1987 | UNKNOWN | first digit of `Z1` | p.72 |
| completion time | n+m+p | cycles | Paste-Up composite design; 1987 | UNKNOWN | last digit of `Zm` | p.72 |
evidence: Figure 14; restricted matrix-vector discussion, p.72.

## space_gaps
* `online_arithmetic_unit` needs a `digit_order` choice because MSD-first versus LSD-first determines which operations satisfy bounded online delay. # pp.63-64
* `serial_serial_parallel` needs choices for a preloaded operand and pure/semi-systolic communication. # p.70
* The dot-product vocabulary lacks a restricted-coefficient nearest-neighbor mesh using Pos/Neg/Del primitives. # p.72

## open_questions
* Table 9 is not legible enough in the supplied document text to enumerate every Paste-Up library primitive.
* The paper does not identify which prototyped multiplier portions were fabricated or measured. # p.72
