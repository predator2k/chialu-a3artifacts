---
handle: gilchrist1955
citation: B. Gilchrist, J. H. Pomerene, S. Y. Wong, "Fast Carry Logic for Digital Computers", IRE Transactions on Electronic Computers, vol. EC-4, pp. 133-136, 1955.
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [int40]
authority: landmark
pages_read: 133-136 / 4
---

## summary
The paper proposes self-timed binary carry logic that signals completion after the longest actual 0- or 1-carry sequence rather than allowing for a full-width carry. Random 40-digit additions have an average maximum carry sequence of 5.6 stages, and an eight-stage experimental accumulator supports an estimated 0.21 µs average carry time. The paper projects 0.36 µs average addition and 10.2 µs 40-digit multiplication, exclusive of memory access.

## families
### speculative_variable_latency  (role: proposes)
mechanism: Each bit stage provides separate carry chains for 1 and 0 carries. Both chains begin off, and parallel inhibition controls their release. Stages whose addends determine the outgoing carry start sequences simultaneously, while incoming sequences stop before those stages. An N-input AND gate asserts completion when either a 1 or 0 carry has reached every stage, so completion time follows the longest carry sequence present in the operands. # pp.133-134
choices:
  detection: completion_sensing   # pp.133-134
  recovery: await_completion   # pp.133-134
new_choices:
  carry_values_tracked: both_zero_and_one — whether completion logic tracks both 0- and 1-carry sequences   # pp.133-134
slots:
  base_adder: ripple_carry   # pp.133-134
parameters: 40-digit analyzed adder; 8-stage experimental accumulator; 40-input completion AND gate for the analyzed design; variable completion latency   # pp.134-136
results:
| metric | value | unit | technology / device | baseline | condition | page |
| average maximum carry-sequence length | 5.6 | stages | IAS computer numerical experiment (1955) | full 40-stage carry allowance | 4,000 random 40-digit additions; both 0- and 1-carry sequences | p.135 |
| average carry-time saving | almost 8-fold | saving | proposed self-timed carry logic, technology UNKNOWN (1955) | full-length carry timing | 40-digit addition | pp.133-134 |
| average maximum carry-sequence length in multiplication additions | 5.6 | stages | IAS computer numerical experiment (1955) | UNKNOWN | interior additions in simple 40-digit multiplication | p.135 |
| sum of individual maximum carries | 112 | stages | IAS computer numerical experiment (1955) | UNKNOWN | typical multiplication of two 40-digit numbers; 20 × 5.6 | p.135 |
| completion time | 0.18 | µs | 8-stage experimental accumulator, tube circuit (1955) | UNKNOWN | carry sequence length 4; completion threshold below -5 volts | p.136 |
| completion time | 0.22 | µs | 8-stage experimental accumulator, tube circuit (1955) | UNKNOWN | carry sequence length 6; completion threshold below -5 volts | p.136 |
| estimated average carry time per addition | approximately 0.21 | µs | 8-stage experimental accumulator, tube circuit (1955) | full-length carry timing | inferred between measured length-4 and length-6 completion times | p.136 |
| preliminary parallel sum-formation time | about 0.15 | µs | proposed 40-digit adder, technology UNKNOWN (1955) | UNKNOWN | carry propagation excluded | p.136 |
| projected average addition time | 0.36 | µs | proposed 40-digit adder, technology UNKNOWN (1955) | UNKNOWN | 0.21 µs carry plus 0.15 µs parallel portion; memory access excluded | p.136 |
| projected multiplication time | 10.2 | µs | proposed 40-digit repeated-addition multiplier, technology UNKNOWN (1955) | UNKNOWN | 40 × 0.15 + 20 × 0.21; memory access excluded | p.136 |
errors_and_checks: Completion is defined when the completion signal passes below -5 volts in the experiment; no fault model, coverage, false-alarm rate, or alias rate is reported.   # p.136
conditions: The carry-length experiment uses random pairs of 40-digit numbers. The distribution from 4,000 additions was unchanged when the sample size increased. Both 0- and 1-carry sequences must be considered, which raises the reported average maximum from the cited 4.6 stages for 1 carries to 5.6 stages. The circuit requires more components than generally used carry circuits.   # pp.133, 135-136
evidence: Fig. 1 and Figs. 3-5, pp.133-134; Figs. 6-7 and “Properties of Carry Sequences,” p.135; Figs. 8-9 and “Experimental Results,” pp.135-136; “Conclusions,” p.136.

### ripple_carry  (role: extends)
mechanism: The adder retains serial per-stage carry propagation but provides separate 0- and 1-carry lines. A carry moves along one line and switches polarity at a stage whose addends force the opposite carry. The final circuit removes the cross-connections so forced-carry stages can start independent sequences simultaneously, limiting serial delay to runs where A ≠ B. # pp.133-134
choices:
  carry_polarity_alternation: true   # p.134
new_choices:
  none
slots:
  none
parameters: N stages generally; 40 stages in the analyzed design; 8 stages in the experimental accumulator   # pp.133-136
results:
| metric | value | unit | technology / device | baseline | condition | page |
| longest carry sequence in illustrated example | 3 | stages | conceptual 10-stage adder (1955) | full 10-stage path | six carry sequences started simultaneously | p.134 |
errors_and_checks: none
conditions: Serial propagation remains only through consecutive stages for which A ≠ B. The carry lines must begin off, enforced by explicit parallel inhibition or operation on the 11 and 00 inputs.   # p.134
evidence: Figs. 3-5 and “The Logical Circuit,” p.134.

### prefix_comparator  (role: instantiates)
mechanism: The 40-stage completion AND gate can determine equality without carry propagation. The parallel carry inhibitions remain asserted, and the completion gate produces an output if and only if the two addends are equal. # p.136
choices:
  function: equality_only   # p.136
  structure: tree_reduction   # p.136
new_choices:
  none
slots:
  none
parameters: 40-stage AND gate   # p.136
results:
| metric | value | unit | technology / device | baseline | condition | page |
| equality determination | 40 | stages observed | proposed carry-completion circuit, technology UNKNOWN (1955) | UNKNOWN | carry inhibitions are not released | p.136 |
errors_and_checks: none
conditions: Equality mode depends on retaining the parallel carry inhibitions.   # p.136
evidence: “Conclusions,” p.136.

## new_families
none

## space_gaps
* `carry_values_tracked` is absent from `speculative_variable_latency`; the paper distinguishes tracking only 1 carries from tracking both 0 and 1 carries, which changes the average maximum sequence from 4.6 to 5.6 stages. # pp.133-135
* `speculative_variable_latency` lacks an explicit non-speculative self-timed mode even though this design waits for completion without predicting or correcting a result. # pp.133-134

## open_questions
* The paper does not identify the component technology of the projected 40-digit adder or multiplier.
* The paper does not report the increased component count or area quantitatively.
