---
handle: lehman_burla1961
citation: M. Lehman, N. Burla, "Skip Techniques for High-Speed Carry-Propagation in Binary Arithmetic Units", IRE Transactions on Electronic Computers, vol. EC-10, pp. 691-698, 1961.
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [binary_integer]
authority: landmark
pages_read: 691-698 / 8
---

## summary
The paper develops carry-skip adders with optimized equal/unequal groups, nested internal skips, and intergroup skip networks for binary addition (pp.692-697). A diode-element comparison reports operation time, element count, and a combined cost-speed criterion for several carry-network families (p.698).

## families
### carry_skip  (role: proposes)
mechanism: A group skip gate bypasses stages whose operand bits satisfy a carry-propagation criterion, while the carry also propagates within the group to determine individual sums. Equal groups minimize worst-case delay at \(n=\sqrt{(m+1)/2}\); unequal groups grow toward the middle and shrink toward both ends. Internal nests and intergroup nets add bypass paths subject to target delay and maximum gate size (pp.692-696).
choices:
  block_sizing: uniform   # p.693
  block_sizing: trapezoidal_variable   # p.694
  skip_levels: 1   # pp.692-694
  skip_levels: 2   # pp.695-697
  skip_gate: and_or_bypass   # pp.692,695
new_choices:
  propagation_test: {Xi ≠ Yi, Xi ∪ Yi} — operand-bit condition that primes a skip path   # p.692
  skip_placement: {group, internal_nested, intergroup_net, interlaced, combined} — placement of additional bypass paths   # pp.694-695
  max_gate_inputs: Int — circuit fan-in limit q used during network design   # p.695
slots:
  block_adder: ripple_carry   # p.692
parameters: equal groups satisfy nk=m+1 and T=(2n+k-3) t.u.; 60-bit unequal groups are 4/5/6/7/8/8/7/6/5/4 bits; the 48-bit example uses twelve 4-bit subgroups and five groups with maximum gate size 5; the 54-bit example uses three groups and nine equal subgroups with p=3   # pp.693-696
results:
| metric | value | unit | technology / device | baseline | condition | page |
| maximum propagation time | 19 | t.u. | UNKNOWN; 1961 | equal groups | 60-bit, 6/6/6/6/6/6/6/6/6/6 | p.694 |
| maximum propagation time | 15 | t.u. | UNKNOWN; 1961 | 19 t.u. equal groups | 60-bit, 4/5/6/7/8/8/7/6/5/4 | p.694 |
| speed-up | 20 | per cent | UNKNOWN; 1961 | equal groups | no increase in equipment | p.694 |
| operation time, Simple Skip | 18 | t.u. | diode elements; 1961 | Conventional, 54 t.u. | Morgan et al. circuit | p.698 |
| relative operation time, Simple Skip | 34 | — | diode elements; 1961 | Conventional, 100 | t/t0 100 | p.698 |
| elements per bit, Simple Skip | 9.5 | — | diode elements; 1961 | Conventional, 8 | D/(m+1) | p.698 |
| Q, Simple Skip | 40 | — | diode elements; 1961 | Conventional, 100 | criterion in (13) | p.698 |
| operation time, Skip Example One | 12 | t.u. | diode elements; 1961 | Conventional, 54 t.u. | simple skip network | p.698 |
| relative operation time, Skip Example One | 22 | — | diode elements; 1961 | Conventional, 100 | t/t0 100 | p.698 |
| elements per bit, Skip Example One | 10 | — | diode elements; 1961 | Conventional, 8 | D/(m+1) | p.698 |
| Q, Skip Example One | 28 | — | diode elements; 1961 | Conventional, 100 | criterion in (13) | p.698 |
| operation time, Skip Example Two | 4 | t.u. | diode elements; 1961 | Conventional, 54 t.u. | nested/internal/intergroup skips | pp.696,698 |
| relative operation time, Skip Example Two | 7.4 | — | diode elements; 1961 | Conventional, 100 | t/t0 100 | p.698 |
| elements per bit, Skip Example Two | 18.5 | — | diode elements; 1961 | Conventional, 8 | D/(m+1) | p.698 |
| Q, Skip Example Two | 17 | — | diode elements; 1961 | Conventional, 100 | criterion in (13) | p.698 |
errors_and_checks: none
conditions: Timing uses worst-case carry propagation and excludes the normal 50 to 100 per cent safety margin (pp.692-693). Unequal end-to-middle sizing excludes units using ones'-complement negative representation with end-around carry (pp.694,696). The analysis treats gate delay as independent of gate size; practical designs are constrained by target speed and maximum fan-in (pp.693,695).
evidence: §§II-VIII; Table I; Figs. 1-7; Table II (pp.692-698).

### ripple_carry  (role: compares)
mechanism: The conventional parallel carry circuit propagates a worst-case carry through the word and supplies the normalization baseline for operation time/equipment (pp.692-693,698).
choices:
new_choices:
  none
slots:
  none
parameters: comparison number length corresponds to conventional operation time 54 t.u.   # p.698
results:
| metric | value | unit | technology / device | baseline | condition | page |
| operation time | 54 | t.u. | diode elements; 1961 | self | Conventional | p.698 |
| elements per bit | 8 | — | diode elements; 1961 | self | D/(m+1) | p.698 |
| Q | 100 | — | diode elements; 1961 | self | normalized criterion | p.698 |
errors_and_checks: none
conditions: The result is the conventional comparison baseline (p.698).
evidence: §IX, Table II (p.698).

### conditional_sum  (role: compares)
mechanism: Selecting networks determine sums/carries for possible group input carries, with the number of unconditionally determined bits doubling at each step (pp.691-692).
choices:
  selection_radix: 2   # pp.691-692
new_choices:
  none
slots:
  none
parameters: UNKNOWN
results:
| metric | value | unit | technology / device | baseline | condition | page |
| operation time | 5.5 | t.u. | diode elements; 1961 | Conventional, 54 t.u. | Sklansky | p.698 |
| relative operation time | 10 | — | diode elements; 1961 | Conventional, 100 | t/t0 100 | p.698 |
| elements per bit | 25.5 | — | diode elements; 1961 | Conventional, 8 | D/(m+1) | p.698 |
| Q | 32 | — | diode elements; 1961 | Conventional, 100 | criterion in (13) | p.698 |
errors_and_checks: none
conditions: The element count excludes temporary storage/synchronizing elements (p.698).
evidence: §I (pp.691-692); §IX, Table II (p.698).

### speculative_variable_latency  (role: compares)
mechanism: Carry-completion detection senses when actual propagation finishes and then initiates the remainder of the addition process, eliminating fixed waiting time and safety margins (p.691).
choices:
  detection: completion_sensing   # p.691
  recovery: await_completion   # p.691
new_choices:
  none
slots:
  none
parameters: average maximum propagation-chain length is less than log2 n   # p.691
results:
| metric | value | unit | technology / device | baseline | condition | page |
| average operation time | 5.6<t<6.6 | t.u. | diode elements; 1961 | Conventional, 54 t.u. | Carry Detection | p.698 |
| relative operation time | 10.4 | — | diode elements; 1961 | Conventional, 100 | average; t/t0 100 | p.698 |
| elements per bit | 19 | — | diode elements; 1961 | Conventional, 8 | D/(m+1) | p.698 |
| Q | 25 | — | diode elements; 1961 | Conventional, 100 | criterion in (13) | p.698 |
errors_and_checks: none
conditions: The completion signal must control when subsequent addition processing begins (p.691).
evidence: §I (p.691); §IX, Table II (p.698).

## new_families
### pyramid_carry_assimilation  (domain: adder, closest: conditional_sum, why_not: The circuit stores half sums/carries and assimilates every second remaining carry position per phase rather than precomputing results for possible input carries.)
mechanism: Half adders form and temporarily store partial sums/carries. Each phase absorbs every second remaining carry position, and controlled AND-gate paths propagate an absorbed carry to the next position where a carry may exist. The number of carry-bearing positions halves per phase, so completion time is proportional to the logarithm of word length (p.691).
choices: assimilation_radix: {2}; temporary_storage: Bool; carry_path: {controlled_and_gates}
results:
| metric | value | unit | technology / device | baseline | condition | page |
| operation time | 4 | t.u. | diode elements; 1961 | Conventional, 54 t.u. | Nadler Pyramid | p.698 |
| relative operation time | 7.4 | — | diode elements; 1961 | Conventional, 100 | t/t0 100 | p.698 |
| elements per bit | 25.2 | — | diode elements; 1961 | Conventional, 8 | D/(m+1) | p.698 |
| Q | 23 | — | diode elements; 1961 | Conventional, 100 | criterion in (13) | p.698 |
evidence: §I (p.691); §IX, Table II (p.698).

## space_gaps
* carry_skip lacks choices for propagation_test, skip_placement, and max_gate_inputs, although all three determine the presented designs (pp.692,694-696).
* The vocabulary lacks pyramid_carry_assimilation, whose stored-carry phased assimilation differs from conditional_sum (pp.691,698).

## open_questions
* Table II does not state the number length directly, although its conventional row reports 54 t.u. (p.698).
* The paper gives heuristic principles rather than precise rules for subgroup/group boundaries under target time p+1 and maximum gate size q (p.695).
