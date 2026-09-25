---
handle: sklansky1960b
citation: J. Sklansky, "An Evaluation of Several Two-Summand Binary Adders", IRE Transactions on Electronic Computers, vol. EC-9, no. 2, pp. 213-226, 1960.
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [binary]
authority: survey
pages_read: 213-226 / 14
---

## summary
The paper describes and evaluates five two-summand binary adders using two-input-gate count G, gate-normalized addition time τ, and summand length n. The conditional-sum adder has the highest η=n/(τ log2 G) for n>3 under the stated gate assumptions, while different assumptions or efficiency criteria change the ranking. (pp.213, 221-225)

## families
### ripple_carry  (role: compares)
mechanism: The simple iterated adder is a cascade of full adders. A full adder decomposed into two half adders reduces the carry-to-carry delay to one half-adder delay. (pp.214-215)
choices: none
new_choices:
  carry_stage_realization: decomposed_two_half_adders — realizes the full-adder carry path with two half adders and an OR gate   # pp.214-215
slots: none
parameters: n-bit summands; n cascaded full adders; c0 selectable as 0 or 1   # pp.214-215
results:
| metric | value | unit | technology / device | baseline | condition | page |
| gate count G | 7n | two-input AND/OR gates | UNKNOWN; 1960 | none | NOT gates have zero delay and are not counted | p.222 |
| addition time τ | 2(n+1) | gate delays | UNKNOWN; 1960 | none | two-input AND/OR gate model | p.222 |
| addition speed | double | relative speed | UNKNOWN; 1960 | simple series adder | full adder realized as Fig. 3 | p.214 |
errors_and_checks: none
conditions: The cascade uses hardware economically relative to parallel schemes, but its carry propagates through successive stages. (pp.214, 217)
evidence: §IV.B; Figs. 3-4; Table I; Figs. 11-16.

### speculative_variable_latency  (role: compares)
mechanism: The independent-dependent carry adder initiates carries simultaneously where adjacent summand bits determine them independently. Transmission gates propagate the remaining dependent carries, and an asynchronous completion gate reports when every variable-length carry sequence has finished. (pp.214-216)
choices:
  detection: completion_sensing   # p.215
  recovery: await_completion   # p.215
new_choices:
  completion_gate_implementation: {cascaded_two_input, unit_delay_multiple_input, log_depth_multiple_input} — the completion-gate realization changes addition time and efficiency   # pp.221, 224
  dependent_carry_speed_ratio: k — ratio by which dependent carries propagate faster than independent carries   # p.224
slots: none
parameters: n-bit summands; asynchronous completion; c0 selectable as 0 or 1   # pp.214-216
results:
| metric | value | unit | technology / device | baseline | condition | page |
| gate count G | 17n-1 | two-input AND/OR gates | UNKNOWN; 1960 | none | completion gate replaced by cascaded two-input AND gates | pp.222, 225 |
| average addition time τ | 4+n | gate delays, lower bound | UNKNOWN; 1960 | none | cascaded completion-gate model | pp.222, 225 |
| average addition time upper bound | 4+n+2log2 n | gate delays | UNKNOWN; 1960 | 4+n lower bound | variable 0-carry and 1-carry sequences | pp.225-226 |
| average longest carry sequence a40 | 5.6 | carry positions | UNKNOWN; 1960 | 1+log2 40=6.3 estimate | n=40 | p.225 |
errors_and_checks: The completion gate detects termination rather than arithmetic faults.   # pp.215, 225
conditions: A fast completion gate or faster dependent-carry transmission can move the design near the conditional-sum/distant-carry efficiency region. Strong space-time correlation may prevent those advantages in ultrafast circuits. (pp.224-225)
evidence: §IV.C; Fig. 5; Table I; §IX; Appendix.

### carry_lookahead  (role: compares)
mechanism: The distant-carry adder expresses carry ci as a triangular function of carry ci-p and the intervening summand bits. Nested auxiliary-carry expressions accelerate generation, with the evaluated class using the same carry span p at every auxiliary and actual carry level. (pp.215-217)
choices:
  group_size: 2 and 5   # p.221
  intergroup_carry: lookahead   # p.217
  block_sizing: uniform   # p.217
new_choices:
  carry_span_profile: equal_at_all_levels — fixes the span of every auxiliary and actual carry level to p   # p.217
slots: none
parameters: carry span p; k auxiliary-carry levels; evaluated configurations p=2 and p=5   # pp.217, 221-222
results:
| metric | value | unit | technology / device | baseline | condition | page |
| addition time τ | 4+k(p+1) | gate delays | UNKNOWN; 1960 | none | equal carry span p at all levels | p.222 |
| speed deficit | about 50 per cent slower | relative speed | UNKNOWN; 1960 | conditional-sum adder | stated gate model | p.223 |
errors_and_checks: none
conditions: The design is advantageous when multiple-input AND/OR gates have delay independent of input count. Replacing those gates with cascaded two-input gates makes performance relatively insensitive to p. (pp.217, 223)
evidence: §IV.D; Figs. 6-8; Table I; Figs. 11-16.

### conditional_sum  (role: compares)
mechanism: The conditional-sum adder computes sums and carries for all possible carry distributions over groups of columns, then selects the applicable conditional results. The operation is synchronous and forms a logarithmic selection structure. (p.217)
choices:
  selection_radix: 2   # pp.217, 222
new_choices: none
slots: none
parameters: n-bit summands; c0 selectable as 0 or 1; seven-bit circuit and sixteen-bit process referenced from the companion paper   # p.217
results:
| metric | value | unit | technology / device | baseline | condition | page |
| gate count G | 3n[2+log2(n+1)] | two-input AND/OR gates | UNKNOWN; 1960 | none | two-input AND/OR gate model | p.222 |
| addition time τ | 2+2log2(n+1) | gate delays | UNKNOWN; 1960 | none | two-input AND/OR gate model | p.222 |
| efficiency η=n/(τ log2 G) | highest for n>3 | qualitative comparison | UNKNOWN; 1960 | four other evaluated adders | stated evaluation assumptions | pp.222, 225 |
| speed | fastest for n>1 | qualitative comparison | UNKNOWN; 1960 | four other evaluated adders | η=n/τ comparison | pp.222, 225 |
errors_and_checks: none
conditions: The reported superiority depends on admitting only two-input AND/OR gates, assigning equal delay to those gates, assigning zero delay and cost to NOT gates, and excluding control/time-domain devices. (pp.217, 221-225)
evidence: §IV.E; Table I; Figs. 11-16; §VIII; §X.

## new_families
### serial_two_summand_adder  (domain: adder, closest: ripple_carry, why_not: ripple_carry represents a spatial carry chain rather than one full adder reused sequentially)
mechanism: The simple series adder contains one full adder whose carry output returns to its carry input through a unit delay. The circuit processes one column at a time, which minimizes hardware while making carry-to-carry delay the addition-speed limit. (p.214)
choices: carry_feedback: {unit_delay}
results:
| metric | value | unit | technology / device | baseline | condition | page |
| gate count G | 7 | two-input AND/OR gates | UNKNOWN; 1960 | none | NOT gates have zero delay and are not counted | p.222 |
| addition time τ | 4n | gate delays | UNKNOWN; 1960 | none | two-half-adder carry-to-carry delay assumption | pp.214, 222 |
evidence: §IV.A; Fig. 2; Table I.

## space_gaps
* `speculative_variable_latency` lacks a completion-gate implementation choice, although the implementation changes the IDA efficiency substantially.   # p.224
* The adder vocabulary lacks a family for a single full adder reused serially across the summand columns.   # p.214

## open_questions
* The paper does not identify a fabrication technology or physical delay/area measurements.
* The conditional-sum circuit details are delegated to the companion paper, so its gate-level choices remain unsettled here.   # p.217
