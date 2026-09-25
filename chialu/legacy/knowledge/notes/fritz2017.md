---
handle: fritz2017
citation: C. Fritz, A. T. Fam, "Fast Binary Counters Based on Symmetric Stacking", IEEE Transactions on Very Large Scale Integration (VLSI) Systems, vol. 25, 2017
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [binary_integer, fixed-point]
authority: incremental
pages_read: 5 / 5
---

## summary
The paper proposes symmetric bit stacking for 6:3 and 7:3 binary counters used in partial-product reduction. The 6:3 counter removes XOR gates and multiplexers from its critical path and improves large counter-based Wallace multipliers.

## families
### popcount_counter_tree  (role: extends)
mechanism: Two 3-bit stackers group the input ones into stacks H and I. One stack is reversed, corresponding bits are OR-ed into J and AND-ed into K, and two further 3-bit stackers form a 6-bit stack. Intermediate H/I/K signals convert the stack into the three-bit binary count. The 6:3 implementation has a seven-basic-gate critical path without XOR gates or multiplexers; the 7:3 extension computes two C1/C2 cases and selects by X6. # p.1, p.2, p.3
choices:
  counter_primitive: counter_6_3 [outside domain], counter_7_3   # p.1, p.3, p.4
  tree_shape: wallace_style   # p.4
new_choices:
  construction_method: symmetric_bit_stacking — groups ones with 3-bit stackers and symmetrically merges two stacks before binary conversion   # p.1, p.2, p.3
slots:
  none
parameters: 3-bit stackers; 6 inputs/3 outputs and 7 inputs/3 outputs; seven basic gates on the 6:3 critical path; 50 MHz counter simulation; 16-bit example reduction tree; 64-bit and 128-bit multiplier conclusions   # p.1, p.3, p.4
results:
| metric | value | unit | technology / device | baseline | condition | page |
| counter latency improvement | at least 30% | faster | ON Semiconductor C5 0.5-μm process; 2017 | existing parallel counter designs | complete proposed 6:3 counter, Spectre simulation at 50 MHz | p.1 |
errors_and_checks: none
conditions: The 6:3 counter requires more crossing wires than traditional counters. # p.3 The proposed 7:3 counter is only slightly faster than existing counters and consumes more power, so the multiplier evaluation uses the 6:3 counter despite one additional reduction phase. # p.4 Counter choice has little effect at small multiplier sizes, and the standard Wallace tree consumes the least power at all evaluated sizes. # p.4 At 64 and 128 bits, the stacker-based counter Wallace multiplier is faster than the standard Wallace tree and existing 7:3-counter implementations; it also consumes less power than the existing 7:3-counter implementations. # p.4
evidence: Sections II–III and Figs. 2–5 define the counter; Tables I–II and Sections IV–V compare counters; Section VI, Fig. 6, Table III, and Fig. 7 evaluate multiplier use.

## new_families
none

## space_gaps
* `popcount_counter_tree.counter_primitive` lacks `counter_6_3`, which is the paper’s preferred reduction primitive. # p.1, p.3, p.4
* `popcount_counter_tree` lacks a construction choice for `symmetric_bit_stacking`. # p.1, p.2, p.3

## open_questions
* The supplied document text does not expose the numeric cells in Tables I–III, so the exact latency/power/transistor-count results require the rendered tables.
* The conventional final adder used after partial-product reduction is not identified by family. # p.1
