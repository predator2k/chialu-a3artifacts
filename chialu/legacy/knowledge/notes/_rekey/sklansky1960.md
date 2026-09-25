---
handle: sklansky1960
citation: J. Sklansky, "Conditional-Sum Addition Logic", IRE Transactions on Electronic Computers, vol. EC-9, pp. 226-231, 1960.
actual_citation: J. Sklansky, "An Evaluation of Several Two-Summand Binary Adders", IRE Transactions on Electronic Computers, vol. EC-9, pp. 213-226, 1960.
status: mismatch
kind: paper
unit_classes: [BINARY_ALU]
formats: [binary]
authority: survey
pages_read: 14 / 14
---

## summary
The document describes and compares five two-summand binary adders using gate count G, gate-normalized addition time τ, and summand length n (pp.213, 221-223). The conditional-sum adder has the highest efficiency under the preferred criterion η=n/(τ log₂G) when n>3, subject to the document's two-input-gate assumptions (pp.222-225).

## families
### ripple_carry  (role: compares)
mechanism: The simple iterated adder consists of a cascade of full adders. Each carry passes through one half-adder delay, assuming the full adder is decomposed into two half adders and an OR gate (pp.214-215).
choices:
  none
new_choices:
  full_adder_realization: AND-OR-NOT — the gate-level realization used for comparison # pp.214-215
slots:
  full_adder_cell: UNKNOWN # pp.214-215
parameters: n-bit binary operands; c₀ can be 0 or 1 # p.214
results:
| metric | value | unit | technology / device | baseline | condition | page |
| gate count G | 7n | two-input AND/OR gates | UNKNOWN; 1960 | none | simple iterated adder | p.222 |
| addition time τ | 2(n+1) | gate delays | UNKNOWN; 1960 | none | simple iterated adder | p.222 |
errors_and_checks: none
conditions: The half-adder carry path doubles addition speed relative to the evaluated simple series adder, whose carry path contains two half-adder delays (p.214). The circuit remains limited by carry propagation through n full-adder positions (pp.214, 222).
evidence: Section IV-B; Figs. 3-4; Table I (pp.214-215, 222).

### carry_lookahead  (role: compares)
mechanism: The distant-carry adder obtains cᵢ from cᵢ₋ₚ and the intervening summand bits. Nested auxiliary-carry expressions permit multiple levels, and each level may use a different carry span p; the evaluated class uses an equal p at every level (pp.217-220).
choices:
  group_size: 2 or 5 # pp.217, 221-222
  intergroup_carry: lookahead # p.217
new_choices:
  none
slots:
  none
parameters: n-bit binary operands; carry span p; k=logₚ[1+(n−1)(p−1)] levels; evaluated with p=2 and p=5 # pp.217, 221-222
results:
| metric | value | unit | technology / device | baseline | condition | page |
| addition time τ | 4+k(p+1) | gate delays | UNKNOWN; 1960 | none | distant-carry adder | p.222 |
| approximate gate count G | 14n | two-input AND/OR gates | UNKNOWN; 1960 | none | n<100 | p.223 |
| relative speed | about 50 per cent slower | relative time | UNKNOWN; 1960 | conditional-sum adder | evaluated curves | p.223 |
errors_and_checks: none
conditions: The design is synchronous and becomes advantageous when multiple-input AND/OR gates have delay independent of input count (p.217). The design requires slightly fewer gates than the conditional-sum adder but is about 50 per cent slower under the evaluated assumptions (p.223).
evidence: Section IV-D; Figs. 6-8; Table I; Figs. 11-16 (pp.217-223).

### conditional_sum  (role: compares)
mechanism: The conditional-sum adder computes sums and carries for all possible carry distributions over groups of columns, then selects the applicable conditional results. Its operation is synchronous (p.217).
choices:
  none
new_choices:
  none
slots:
  none
parameters: n-bit binary operands; c₀ can be 0 or 1; a seven-bit circuit is referenced in the companion paper # p.217
results:
| metric | value | unit | technology / device | baseline | condition | page |
| gate count G | 3n[2+log₂(n+1)] | two-input AND/OR gates | UNKNOWN; 1960 | none | conditional-sum adder | p.222 |
| addition time τ | 2+2log₂(n+1) | gate delays | UNKNOWN; 1960 | none | conditional-sum adder | p.222 |
| efficiency threshold | n>3 | bits | UNKNOWN; 1960 | four compared adders | η=n/(τ log₂G) | pp.222-223 |
| relative speed | about 50 per cent faster | relative time | UNKNOWN; 1960 | distant-carry adder | evaluated curves | p.223 |
errors_and_checks: none
conditions: The design is fastest for n>1 and no slower than the compared adders at n=1 under equal-delay two-input AND/OR gates and zero-delay uncounted NOT gates (pp.221-223). The preferred efficiency criterion ranks the design highest for n>3, but different component/control assumptions can change the ranking (pp.223-225).
evidence: Sections IV-E and VI-X; Table I; Figs. 11-16 (pp.217, 221-225).

## new_families
### serial_binary_adder  (domain: adder, closest: ripple_carry, why_not: one full adder is reused sequentially through feedback rather than instantiated as an n-bit carry chain)
mechanism: The simple series adder uses one three-input/two-output full adder whose carry output returns to its carry input through a unit delay. One carry is computed at a time, which minimizes hardware and makes carry-to-carry delay the speed limitation (p.214).
choices: full_adder_realization: {AND-OR-NOT}; carry_feedback: {unit_delay}
results:
| metric | value | unit | technology / device | baseline | condition | page |
| gate count G | 7 | two-input AND/OR gates | UNKNOWN; 1960 | none | simple series adder | p.222 |
| addition time τ | 4n | gate delays | UNKNOWN; 1960 | none | simple series adder | p.222 |
evidence: Section IV-A; Fig. 2; Table I (pp.214-215, 222).

### independent_dependent_carry  (domain: adder, closest: speculative_variable_latency, why_not: the circuit waits for asynchronous carry completion and performs no speculative result correction)
mechanism: Independent carries begin simultaneously where adjacent summand bits are equal. Transmission gates propagate unchanged dependent carries between independent-carry positions, and a carry-completion gate signals when all variable-length carry sequences finish (pp.214-216).
choices: carry_transmission_device: {AND-OR-NOT, relay-like}; carry_completion_gate: {cascaded_two_input, fast_multiple_input}
results:
| metric | value | unit | technology / device | baseline | condition | page |
| gate count G | 17n−1 | two-input AND/OR gates | UNKNOWN; 1960 | none | cascaded completion gate | pp.222, 225 |
| average addition time lower bound τ | 4+n | gate delays | UNKNOWN; 1960 | none | cascaded completion gate | pp.222, 225 |
| average addition time upper bound τ | 4+n+2log₂n | gate delays | UNKNOWN; 1960 | none | cascaded completion gate | p.225 |
| measured example a₄₀ | 5.6 | carry positions | UNKNOWN; 1960 | 1+log₂40=6.3 estimate | n=40 | p.225 |
evidence: Section IV-C; Fig. 5; Section IX; Appendix (pp.214-216, 222, 224-226).

## space_gaps
* The adder vocabulary lacks a sequential one-full-adder family for the simple series adder (pp.214, 222).
* The adder vocabulary lacks an asynchronous independent/dependent-carry family with completion sensing but without speculation or correction (pp.214-216, 224-226).
* The carry_lookahead `levels` domain stops at 4, while the distant-carry level count k varies with n and p without that stated limit (pp.217, 222).

## open_questions
* The conditional-sum grouping/base-block choices are deferred to the companion paper and are not fixed by this document (p.217).
* The extracted Table I expression for distant-carry gate count is not reliably legible, so only the document's printed approximation G≈14n for n<100 is recorded (pp.222-223).
