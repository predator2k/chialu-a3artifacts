---
handle: swartzlander_1973
citation: E. E. Swartzlander Jr., "Parallel Counters", IEEE Transactions on Computers, vol. C-22, no. 11, pp. 1021-1024, 1973
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [binary]
authority: landmark
pages_read: 1021-1024 / 1021-1024
---

## summary
The paper analyzes full-adder-network, full-adder/fast-adder, and quasi-digital parallel counters that count active binary inputs. The full-adder/fast-adder array reduces digital delay by replacing upper ripple-carry stages with READ-ONLY-memory adders, while the quasi-digital counter uses analog current summing and threshold digitization. # p.1021, p.1024

## families
### popcount_counter_tree  (role: extends)
mechanism: Inputs are grouped three at a time, and each full adder reduces three equal-weight lines to sum/carry lines of weights 1 and 2. Reduction continues by weight until one line of each weight remains. A constructive alternative recursively joins two smaller counters with ripple-carry adders. The faster variant retains the first full-adder reductions but replaces upper ripple-carry stages with READ-ONLY-memory fast adders. # p.1021-p.1022
choices:
  counter_primitive: full_adder_3_2   # p.1021
new_choices:
  counter_primitive_mix: {full_adder, full_adder_and_half_adder} — whether incomplete counter sizes use half adders with full adders   # p.1022
  upper_reduction_adder: {ripple_carry, READ-ONLY-memory_fast_adder} — the adder used to combine intermediate counter outputs   # p.1021-p.1022
slots:
  final_adder: ripple_carry   # p.1021-p.1022
parameters: N inputs; M = 1 + [log2(N)] outputs; completely utilized sizes N = 2^j - 1; 15-input example with three adder levels   # p.1021-p.1022
results:
| metric | value | unit | technology / device | baseline | condition | page |
| delay lower/upper bounds | [log3(N - 1)] + [log2(N)] < δ ≤ 2[log2(N)] - 1 | full-adder delay times | UNKNOWN (1973) | none | full-adder network | p.1022 |
| module count | Nadd = N - j | full adders | UNKNOWN (1973) | none | N = 2^j - 1 | p.1022 |
| maximum module count | N | adder modules | UNKNOWN (1973) | none | arbitrary counter sizes; modules may include half adders | p.1022 |
| 15-input delay | δFA + 2δROM | delay | UNKNOWN (1973) | full-adder network | full-adder/fast-adder array | p.1022 |
| general fast-array delay | δFA + (M - 2)δROM | delay | UNKNOWN (1973) | full-adder network | ROM access delay assumed independent of memory size | p.1022 |
| equal-delay fast-array delay | δFA[log2(N)] | delay | UNKNOWN (1973) | comparable full-adder counter | δROM = δFA; roughly half the full-adder-counter value | p.1022 |
| relative speed | up to twice | speed | UNKNOWN (1973) | full-adder network counter | full-adder/fast-adder array | p.1024 |
errors_and_checks: none
conditions: The READ-ONLY-memory method is impractical for M > 6, corresponding to counters with more than 63 inputs. The method is practical for counters with under 32 inputs. # p.1023
evidence: Full-Adder Network Counters, (2)-(6), Figs. 1-2, p.1021-p.1022; Full-Adder/Fast-Adder Array Counters, (7)-(8), p.1022-p.1023

## new_families
### rom_lookup_adder  (domain: adder, closest: carry_lookahead, why_not: the sum is stored and selected by the complete operand address rather than produced by a carry-propagation network)
mechanism: A fast adder for two K-bit numbers is realized as a 2^(2K+1)-word by K+1-bit READ-ONLY memory. The counter combines full-adder outputs and one remaining input through progressively wider ROM adders until one M - 1 stage fast adder generates the M-bit count. The analysis assumes that ROM access delay does not depend on memory size.
choices:
  stored_function: {binary_sum}
  access_delay_model: {size_independent}
results:
| metric | value | unit | technology / device | baseline | condition | page |
| ROM size per K-bit fast adder | 2^(2K+1) by K + 1 | bits per word organization | UNKNOWN (1973) | none | two K-bit numbers | p.1023 |
| total ROM storage | φ = Σ(K + 1)2^(M+K), K = 2 to M - 1 | bits | UNKNOWN (1973) | none | N-input fast-adder array | p.1023 |
evidence: Full-Adder/Fast-Adder Array Counters, (7)-(8), p.1022-p.1023

### quasi_digital_counter  (domain: shift: bit counting, closest: popcount_counter_tree, why_not: the count is formed by analog current summing and comparator thresholds rather than a digital counter tree)
mechanism: Input resistors sum currents at a node whose voltage is proportional to the fraction n/N of active inputs. A bank of comparators tests count-dependent thresholds, and one or two logic levels encode the comparator outputs as the binary count. Emitter-coupled logic supports the comparator function and wired-OR operation. Larger counters may use a quasi-digital first stage followed by ripple-carry adders.
choices:
  summing_network: {resistor_current_summing}
  digitizer: {parallel_threshold_comparators}
  output_logic_levels: {1, 2}
  hierarchy: {all_quasi_digital, quasi_digital_first_stage_then_ripple}
results:
| metric | value | unit | technology / device | baseline | condition | page |
| node voltage | Vn = Vref n/N | voltage | UNKNOWN (1973) | none | n active inputs among N | p.1023 |
| settling delay | -Ry Cin log(1/2N - et) | time | UNKNOWN (1973) | none | Cstray ≈ NCin | p.1023 |
| total delay | Tsettling + Tcomp + 2Tgate | time | UNKNOWN (1973) | none | two logic levels | p.1023 |
| total delay | Tsettling + 5 ns | time | emitter-coupled logic (1973) | none | wired-OR implementation | p.1024 |
| advantageous counter range | 10 < N < 50 | inputs | emitter-coupled logic (1973) | both fully digital methods | moderate-size counters appear faster | p.1024 |
errors_and_checks: Comparators respond correctly when en + et < 1/2N. The accumulated error et includes divider-resistor tolerance, input-resistor tolerance, and comparator error band Voffset/Vref. # p.1023
conditions: Delay increases with input count. More accurate resistors or a smaller comparator error band mitigate the increase. Resistors may require trimming, stray capacitance/inductance must be minimized, and noise suppression may be difficult. # p.1023-p.1024
evidence: Quasi-Digital Counters, (9)-(15), Figs. 3-4, p.1023-p.1024

## space_gaps
* `popcount_counter_tree.counter_primitive` cannot represent a mixed full-adder/READ-ONLY-memory reduction network. # p.1022
* `popcount_counter_tree.final_adder` lacks a READ-ONLY-memory fast-adder filler. # p.1022-p.1023
* The vocabulary lacks a quasi-digital parallel-counter family based on analog current summing and comparator digitization. # p.1023-p.1024

## open_questions
* The paper reports analytical delay formulas rather than a fabricated technology/device implementation. # p.1021-p.1024
* The ROM analysis assumes size-independent access delay but does not identify a ROM technology that satisfies the assumption. # p.1022
* The quasi-digital speed comparison is stated as potential/expected performance and is not supported by measured hardware results. # p.1023-p.1024
