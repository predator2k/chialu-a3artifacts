---
handle: kilburn1959
citation: T. Kilburn, D. B. G. Edwards, D. Aspinall, "Parallel Addition in Digital Computers: A New Fast 'Carry' Circuit", Proceedings of the IEE - Part B, vol. 106, pp. 464-466, 1959.
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [binary]
authority: landmark
pages_read: 464-466 / 3
---

## summary
The document proposes a binary parallel-adder carry path made from saturated transistor switches connected in series, with local logic fixed before carry propagation begins. p.465-466. The document also analyzes completion-based variable latency, deferred carry assimilation, and fully decoded carry generation. p.465.

## families
### manchester_carry_chain  (role: proposes)
mechanism: Each stage selects a carry source through mutually exclusive transistor switches controlled only by that stage's x and y digits. The switch settings remain unchanged while carry propagates through series-connected saturated transistors. An emitter-follower reconstitutes the voltage level after ten stages, while a local 1 mA leak supplies saturation current without loading the carry source. p.465-466.
choices:
  chain_segment_length: 10 [outside domain]   # p.466
  circuit_style: saturated_junction_transistor_switch [outside domain]   # p.465-466
new_choices:
  switch_device: {2N240, 2N501} — the junction-transistor type used as the saturated bilateral switch   # p.465
slots:
  none
parameters: 18 constructed stages; intended 40-stage adder; OA47 diode control logic; 1 mA positive leak; carry level -3 volts; no-carry level -4-5 volts; function waveforms from -2 • 5 to -5 • 5 volts.   # p.466
results:
| metric | value | unit | technology / device | baseline | condition | page |
| carry-path transmission delay | approximately 20 | millimicrosec | 18 plug-in-board stages; device UNKNOWN; year 1959 | none | approximately 5 ft of carry-path wire | p.465-466 |
| voltage drop | approximately 0-3 | volt | ten 2N240 or 2N501 switches; year 1959 | none | negligible direct current through the T1 transistors | p.466 |
| delay plus rise time | approximately 80 | millimicrosec | 18-stage junction-transistor prototype; device UNKNOWN; year 1959 | none | includes transistor switching/waveform-generation delay and approximately 20 millimicrosec transmission delay | p.466 |
| projected complete addition time | 0-2 | microsec | projected 40-stage junction-transistor adder; year 1959 | none | assumes 60 millimicrosec switching time and approximately 1 millimicrosec transmission time per stage | p.466 |
errors_and_checks: The -3-volt source is current-limited to avoid excessive current if fault/transient conditions close mutually exclusive switches simultaneously; no detection coverage or false-alarm behavior is reported.   # p.466
conditions: Series-switch loading and voltage loss limit chain length, so an emitter-follower restores the level after ten stages. p.465-466. Shorter board wiring is expected to reduce the measured transmission delay, probably by a factor of two. p.466. The 40-stage timing is a feasibility projection rather than a measured result. p.466.
evidence: Fig. 1 and circuit discussion, p.465; Figs. 2-3 and prototype measurements, p.465-466.

### speculative_variable_latency  (role: analyzes)
mechanism: An addition period can terminate after the longest carry sequence has propagated rather than waiting for a possible full-width sequence. The document reports an Institute of Advanced Study estimate for random 40-digit additions but does not describe the completion detector circuit. p.465.
choices:
  recovery: await_completion   # p.465
new_choices:
  none
slots:
  none
parameters: 40-digit random-number addition; variable completion at the end of the longest carry sequence.   # p.465
results:
| metric | value | unit | technology / device | baseline | condition | page |
| average maximum carry-sequence length | 5 • 6 | stages | device UNKNOWN; year UNKNOWN | full 40-stage carry path | random-number 40-digit addition | p.465 |
| average carry-propagation-time saving | factor of seven | UNKNOWN | device UNKNOWN; year UNKNOWN | waiting for full-width carry propagation | addition terminates at the end of the longest carry sequence | p.465 |
errors_and_checks: none
conditions: The saving requires circuitry that can terminate the addition period when the longest active carry sequence ends. p.465.
evidence: Carry-sequence estimate and termination proposal, p.465.

### carry_save_datapath  (role: analyzes)
mechanism: Partial sum and carry are stored separately so carry does not propagate after every addition. Assimilation occurs only when the answer must be standardized, transferred, or tested for sign, although sign testing does not always require complete assimilation. A group of operands therefore incurs one carry-propagation interval. p.465.
choices:
  assimilation_point: end_of_chain   # p.465
  accumulator_redundant: true   # p.465
new_choices:
  none
slots:
  none
parameters: separate carry register; number of operands UNKNOWN; width UNKNOWN.   # p.465
results:
| metric | value | unit | technology / device | baseline | condition | page |
| carry propagations per operand group | one | carry propagation time | technology UNKNOWN; year 1959 | propagation after every addition | more than two operands are accumulated | p.465 |
errors_and_checks: none
conditions: The scheme benefits multioperand accumulation and is identified as particularly useful when multiplication adds numerous subproducts. p.465. Assimilation remains necessary when the complete answer is standardized or transferred. p.465.
evidence: Deferred-carry discussion, p.465.

### carry_lookahead  (role: compares)
mechanism: A logical gating system derives the carry for stage k from all less-significant x and y digits rather than from stage k-1. The gating complexity increases for more-significant stages. p.465.
choices:
new_choices:
  none
slots:
  none
parameters: 52 stages in the cited National Bureau of Standards implementation.   # p.465
results:
| metric | value | unit | technology / device | baseline | condition | page |
| complete addition time | 1 | microsec | 1Mc/s circuits; node UNKNOWN; year 1956 | none | 52 stages | p.465 |
errors_and_checks: none
conditions: The document characterizes the all-less-significant-digit gating method as expensive because its complexity increases with stage significance. p.465.
evidence: Comparison of the two carry-generation approaches and cited National Bureau of Standards result, p.465.

## new_families
none

## space_gaps
* The manchester_carry_chain `chain_segment_length` domain ends at 8, while the document restores the carry level after ten stages. p.466.
* The manchester_carry_chain `circuit_style` domain lacks saturated junction-transistor switches operated as bilateral pass devices. p.465-466.

## open_questions
* The document does not identify whether the constructed 18-stage chain uses 2N240 or 2N501 transistors. p.465-466.
* The document does not specify the completion-sensing circuit required by the variable-latency proposal. p.465.
