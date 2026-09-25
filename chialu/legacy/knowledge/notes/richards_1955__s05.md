---
handle: richards_1955#s05
parent: richards_1955
citation: Richards, "Arithmetic Operations in Digital Computers", Van Nostrand, 1955
chapter: BINARY ADDITION AND SUBTRACTION
pdf_pages: 92-146
status: ok
kind: book_chapter
unit_classes: [BINARY_ALU]
formats: [binary, true form, 1's complement, 2's complement]
authority: textbook
pages_read: 55 / 55
---

## summary
The chapter defines parallel/serial binary addition and subtraction, half/full adder and subtracter logic, counter-based accumulators, ripple/simultaneous carry, and complement arithmetic. It compares Boolean-switch, diode, vacuum-tube, and Kirchhoff realizations and explains completion-sensed carry propagation. It establishes that parallel end-around carry need not add a second propagation interval, whereas serial end-around carry requires a second pass.

## families
### ripple_carry  (role: defines)
mechanism: Each order forms a sum from the two operand digits and the carry from the next lower order. Two half adders plus an “or” circuit form a full adder; arranging the operand half adder before the carry half adder lets a propagated carry traverse only one half adder per order. Counter accumulators similarly pass carry pulses or steady-state carry conditions through successive higher orders.
choices:
  full_adder_cell: UNKNOWN   # p.100
  carry_polarity_alternation: true   # p.104
new_choices:
  carry_realization: half_adder_pair_or | factored_switching | vacuum_tube | counter_accumulator — physical forms used to generate and propagate carry   # p.95
slots:
  none
parameters: one full adder per parallel order; one single-order adder for serial operation   # p.93
results:
| metric | value | unit | technology / device | baseline | condition | page |
| switching-network size | 25 | switching inputs | abstract | straightforward sum/carry equations | four 3-input “and” circuits for sum and simplified carry logic | p.101 |
| switching-network size | 21 | switching inputs | abstract | 25 switching inputs | factored sum/carry forms | p.101 |
| switching-network size | 19 plus one inverter | switching inputs | diode switching; year UNKNOWN | 21 switching inputs | no inverted inputs required | p.102 |
| switching-network size | 16 | diodes | diode switching; year UNKNOWN | 19 switching inputs plus one inverter | factored forms retain one “and” and one “or” on carry path | p.103 |
| half-adder size | 8 | grids | vacuum tubes; year UNKNOWN | UNKNOWN | Fig. 4-4 circuits | p.99 |
| half-adder size | 7 | grids | vacuum tubes; year UNKNOWN | 8 grids | alternative carry generation | p.100 |
| full-adder size | 14 or 7 | grids or tubes per order | vacuum tubes; year UNKNOWN | UNKNOWN | Fig. 4-8 alternating-polarity carry implementation | p.105 |
| full-adder size reduction | one grid per order | grids | vacuum tubes; year UNKNOWN | 14 grids per order | inverted X/Y inputs and alternate inverted sum outputs | p.105 |
| full-adder size | 12 | grids per order | vacuum tubes; year UNKNOWN | 14 grids per order | inverted inputs and two tubes per order for carry propagation | p.105 |
| carry-path depth | one | tube per order | vacuum tubes; year UNKNOWN | two tubes per order | alternate true/inverted carry stages | p.104 |
errors_and_checks: Separately generated sum/not-sum and carry/not-carry outputs can indicate invalid equal-valued pairs; simple output inverters do not provide independent checking.   # p.98
conditions: Parallel operation permits higher computation speed but requires separate per-order devices, while serial operation reuses one device; neither speed nor equipment scales by exactly the number of orders.   # p.93
evidence: Tables 4-I/4-II; Figs. 4-1 through 4-10 and 4-13 through 4-21; pp.94-121

### carry_lookahead  (role: defines)
mechanism: “Simultaneous carry” expands each higher-order carry into conditions covering generation in that order and propagation through every intervening lower order. The expanded “and” terms feed the order’s carry “or” circuit, so carries become available substantially simultaneously rather than rippling successively. The same method applies to adders and counter accumulators.
choices:
  group_size: 3 or 4 [outside domain]   # p.124
  levels: UNKNOWN   # p.124
  intergroup_carry: UNKNOWN   # p.124
  block_sizing: UNKNOWN   # p.124
new_choices:
  carry_scope: all_orders | grouped — simultaneous logic may span the whole word or groups of three or four orders   # p.124
slots:
  none
parameters: groups of “say, three or four” orders when full-width simultaneous carry is impractical   # p.124
results:
| metric | value | unit | technology / device | baseline | condition | page |
| carry readiness time | independent of the order in which the carry originated | qualitative | abstract | propagated carry | simultaneous-carry accumulator | p.124 |
errors_and_checks: none
conditions: Full-width simultaneous carry requires a rather large amount of switching beyond a few orders, so grouped simultaneous carry may trade equipment for propagation speed.   # p.124
evidence: Fig. 4-24; pp.123-125

### end_around_carry  (role: defines)
mechanism: A highest-order borrow is returned to the lowest order as a borrow to convert a negative 2’s-complement result into 1’s-complement form. A highest-order carry is similarly returned when a negative balance becomes positive. Complement subtraction adds the 1’s complement of the subtrahend and returns the highest-order carry to the units order.
choices:
  modulus: mod_2n_minus_1   # p.130
  recirculation: UNKNOWN   # p.131
  topology: UNKNOWN   # p.131
new_choices:
  execution_mode: concurrent_parallel | serial_second_pass — parallel feedback is handled with ordinary propagation, while serial feedback requires retransmission   # p.131
slots:
  none
parameters: n binary orders representing powers 2^0 through 2^(n-1)   # p.136
results:
| metric | value | unit | technology / device | baseline | condition | page |
| additional parallel propagation time | none | propagation intervals | abstract | ordinary carry/borrow propagation | end-around carry or borrow cannot propagate beyond its originating order on the second traversal | p.131 |
| serial end-around cost | second pass through the adder | passes | abstract | 2’s-complement subtraction | 1’s-complement serial operation | p.144 |
errors_and_checks: The highest-order carry or borrow indicates result sign and can also indicate capacity overflow under the stated balance conditions.   # p.136
conditions: The 1’s-complement form simplifies conversion to magnitude by digit inversion but admits positive and negative zero; 2’s complement avoids end-around carry and the dual-zero representation.   # p.132
evidence: worked examples and complement equations, pp.130-138 and 143-145

### speculative_variable_latency  (role: analyzes)
mechanism: Step-by-step accumulator carry can stop when sensing establishes that no carries remain. An asynchronous ripple arrangement instead sends either a carry or no-carry signal through every order; emergence from the highest order signals completion, after which the sum pulse is applied. The completion time follows the actual carry chain rather than an unconditional fixed allowance.
choices:
  speculation_window: UNKNOWN   # p.111
  detection: completion_sensing   # p.122
  recovery: await_completion   # p.123
new_choices:
  completion_encoding: carry_no_carry_dual_line — each order forwards exactly one state only after receiving a lower-order state   # p.122
slots:
  base_adder: ripple_carry   # p.122
parameters: 40-digit example; worst case as many carry steps as number of orders   # p.111
results:
| metric | value | unit | technology / device | baseline | condition | page |
| average successive carries | 4.6 | carries | abstract | worst-case fixed allowance | addition of two forty-digit binary numbers containing random digits | p.111 |
| worst-case carry steps | number of orders | steps | abstract | UNKNOWN | step-by-step carry process | p.111 |
errors_and_checks: Completion is indicated when the carry/no-carry signal emerges from either output line of the highest order.   # p.123
conditions: Completion sensing can materially reduce addition time when actual carry chains are shorter than the word, while step-by-step carry largely removes the speed advantage of parallel operation.   # p.111
evidence: Fig. 4-23; pp.110-123

## taxonomy
* Binary addition and subtraction   # p.93
  * Parallel operation   # p.93
    * Addition   # p.94
      * Half adder   # p.94
        * Boolean switching forms -> ripple_carry   # p.97
        * Vacuum-tube forms -> ripple_carry   # p.99
      * Full adder   # p.100
        * Two half adders plus “or” -> ripple_carry   # p.100
        * Factored switching arrangements -> ripple_carry   # p.101
        * Alternating true/inverted carry -> ripple_carry   # p.104
      * Kirchhoff adders -> unmapped   # p.107
    * Accumulators   # p.109
      * Step-by-step carry -> speculative_variable_latency   # p.110
      * Automatic “ripple through” carry -> ripple_carry   # p.112
      * Carry-storage variants -> ripple_carry   # p.114
      * Automatic carry initiation -> ripple_carry   # p.118
      * Asynchronous carry/no-carry completion -> speculative_variable_latency   # p.122
      * Simultaneous carry -> carry_lookahead   # p.124
      * Grouped simultaneous carry -> carry_lookahead   # p.124
    * Direct subtraction   # p.126
      * Half subtracter -> unmapped   # p.126
      * Full subtracter -> unmapped   # p.128
      * End-around borrow -> end_around_carry   # p.131
      * Addition by subtraction -> unmapped   # p.132
      * Shared adder-subtracter -> unmapped   # p.132
      * Subtraction accumulator -> unmapped   # p.135
    * Subtraction by addition of complements   # p.135
      * 1’s-complement with end-around carry -> end_around_carry   # p.136
      * 2’s-complement subtraction -> ripple_carry   # p.144
  * Serial operation   # p.139
    * Full adder with delayed carry -> ripple_carry   # p.140
    * Half-adder arrangements with carry storage -> ripple_carry   # p.141
    * d-c/pulse/negative-pulse/two-line digit representations -> unmapped   # p.141
    * Non-return-to-zero representation -> unmapped   # p.143
    * 1’s-complement end-around second pass -> end_around_carry   # p.144
    * 2’s-complement subtraction -> ripple_carry   # p.144
  * Stored signed-number conventions   # p.146
    * True positive / true negative -> unmapped   # p.146
    * True positive / 2’s-complement negative -> unmapped   # p.146
    * True positive / 1’s-complement negative -> end_around_carry   # p.146
    * 1’s-complement positive / true negative -> end_around_carry   # p.146

## primary_sources
* Burks, Goldstine, and von Neumann, 1947 — credited with the 4.6 average successive carries for addition of two forty-digit random binary numbers   # p.111

## new_families
### counter_accumulator  (domain: adder, closest: ripple_carry, why_not: The stored counter state participates directly in addition and carry generation rather than serving only as a register around a carry-propagate adder.)
mechanism: Per-order binary counters store the running balance and toggle when addend or carry pulses arrive. Carries can be recorded, gated, propagated through switches, initiated automatically, or computed before state update.
choices: carry_mode: {step_by_step, ripple_pulse, ripple_condition, carry_storage, automatic_initiation, simultaneous}; carry_control: {separate_pulse, gate, self_initiated}; carry_storage: Bool
results:
| metric | value | unit | technology / device | baseline | condition | page |
| average successive carries | 4.6 | carries | abstract | worst-case word-length allowance | two forty-digit random binary operands | p.111 |
evidence: pp.109-124, Figs. 4-13 through 4-24

### direct_borrow_subtractor  (domain: adder, closest: ripple_carry, why_not: The propagated state is a borrow with asymmetric minuend/subtrahend inputs rather than a carry generated by addition.)
mechanism: A half subtracter produces difference and borrow from minuend/subtrahend digits. A full subtracter incorporates the lower-order borrow; arranging operand subtraction before borrow subtraction limits the propagated borrow path to one half subtracter per order.
choices: construction: {two_half_subtracters_or, half_adder_half_subtracter, direct_full_subtracter}; borrow_path: {one_half_subtracter, two_half_subtracters}
results:
| metric | value | unit | technology / device | baseline | condition | page |
| borrow-path depth | one instead of two | half subtracters per order | abstract | first subtraction variation | Fig. 4-26 arrangement | p.127 |
evidence: Tables 4-III/4-IV; Figs. 4-25 through 4-28; pp.126-135

### serial_bit_adder_subtractor  (domain: adder, closest: ripple_carry, why_not: One physical digit unit is reused over time and requires state/delay matched to the digit stream.)
mechanism: Corresponding operand digits enter a single-order unit in ascending significance. A delay stores each carry or borrow until the next digit time; transmission/storage timing fixes throughput, so faster carry generation does not increase addition speed.
choices: digit_encoding: {dc_levels, positive_pulse, bipolar_pulse, two_line, transition}; complement_policy: {ones_complement_second_pass, twos_complement}
results:
| metric | value | unit | technology / device | baseline | condition | page |
| adder count | one | single-order units | abstract | one device per parallel order | serial digit transmission | p.139 |
| 1’s-complement end-around cost | second pass | passes | abstract | 2’s-complement serial subtraction | serial end-around carry | p.144 |
evidence: Figs. 4-30 through 4-33; pp.139-145

### kirchhoff_threshold_adder  (domain: adder, closest: ripple_carry, why_not: The cell sums physical voltage/current levels and thresholds the total rather than composing Boolean full-adder gates.)
mechanism: Input voltages or currents are physically summed. Threshold devices distinguish zero/one inputs from two/three inputs to generate sum and carry, or a resistor network subtracts twice the carry from the three-input total.
choices: summed_quantity: {voltage, current}; realization: {threshold_tubes, resistor_feedback}
results:
| metric | value | unit | technology / device | baseline | condition | page |
| circuit simplicity | advantage | qualitative | vacuum tubes/resistors; year UNKNOWN | Boolean switching adders | accurately controlled, time-stable components required | p.109 |
evidence: Figs. 4-11/4-12; pp.107-109

## space_gaps
* `ripple_carry.full_adder_cell` lacks Boolean-switch/diode/vacuum-tube/Kirchhoff realizations documented in the chapter.   # p.97
* `carry_lookahead` lacks flat simultaneous-carry versus grouped simultaneous-carry scope.   # p.124
* `end_around_carry.recirculation` lacks concurrent parallel ripple feedback and serial second-pass values.   # p.131
* The vocabulary lacks counter accumulators whose storage elements execute the addition.   # p.109
* The vocabulary lacks direct-borrow subtracters and shared carry/borrow adder-subtracters.   # p.132
* The vocabulary lacks time-reused serial adders with explicit carry-delay storage.   # p.140

## open_questions
* The chapter does not give exact speed/equipment factors for parallel versus serial operation.   # p.93
* The chapter does not specify a formal probability model behind the cited 4.6-carry average beyond “random digits.”   # p.111
* The chapter does not define intergroup wiring for the suggested three- or four-order simultaneous-carry groups.   # p.124
