---
handle: huang_wang2003
citation: C.-H. Huang, J.-S. Wang, "High-Performance and Power-Efficient CMOS Comparators", IEEE Journal of Solid-State Circuits, vol. 38, no. 2, 2003.
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [binary64]
authority: incremental
pages_read: 254-262 / 9
---

## summary
The paper proposes a priority-encoding binary comparator that merges priority encoding and magnitude-decision logic in multiple-output domino logic. Multilevel lookahead and a latch-based two-stage pipeline produce a one-cycle 64-b comparator in 3-V 0.6-µm CMOS. Post-layout simulation and test-chip measurements establish speed/area/power improvements over an all-n-transistor comparator.

## families
### prefix_comparator  (role: proposes)
mechanism: XOR gates identify unequal operand bits, and a priority encoder generates a one-hot token at the most significant unequal bit (MSUB). Operand bits at the MSUB determine the greater operand, while a NOR reduction generates EQUAL. The magnitude decision module merges priority encoding with the following AND functions in multiple-output domino logic. Multilevel lookahead shortens priority-token propagation. The 64-b implementation partitions the inputs into eight 8-b groups for the first half-cycle and compares the eight latched result pairs during the second half-cycle. # p.255-p.259
choices:
  function: full_ordering   # p.255-p.256
  structure: msb_first_prefix   # p.255-p.257
new_choices:
  priority_realization: multilevel_lookahead_mdm — A multilevel-lookahead priority encoder is fused with operand-bit selection in the magnitude decision module.   # p.256-p.257
  circuit_style: dynamic_modl — Serial dynamic CMOS and multiple-output domino logic implement the magnitude decision module.   # p.256, p.261
  pipeline_partition: two_stage_half_cycle — Latch-based stages execute delay-balanced portions in opposite halves of one clock cycle.   # p.258-p.259
slots:
  none
parameters: 64-b operands; eight first-stage 8-b comparators; one second-stage 8-b comparator; each 8-b macro contains two 4-b comparators; two pipeline stages; one comparison per clock cycle; transistor channel width up to 5 µm in the pull-down network.   # p.258-p.260
results:
| metric | value | unit | technology / device | baseline | condition | page |
| operating speed | 16 | % faster | 3-V 0.6-µm CMOS (2003) | Wang et al. 64-b ANT comparator [3] | Post-layout simulation using equivalent per-operation timing definitions | p.260 |
| layout area | 50 | % smaller | 3-V 0.6-µm CMOS (2003) | Wang et al. 64-b ANT comparator [3] | 64-b layouts | p.254, p.260-p.261 |
| power consumption | 79 | % less power | 3-V 0.6-µm CMOS (2003) | Wang et al. 64-b ANT comparator [3] | Post-layout simulation at maximum clock frequency | p.260 |
| dynamic-gate delay | 2.2 | ns | fabricated 3-V 0.6-µm CMOS test chip (2003) | none | Measured with both 160-MHz and 50-MHz clocks; matches simulation | p.261 |
| maximum operating frequency | around 180 | MHz | fabricated 3-V 0.6-µm CMOS test chip (2003) | none | Measured test chip | p.261 |
errors_and_checks: none
conditions: Directly flattened comparison logic is suitable only for short inputs, while direct MDM expansion beyond four inputs becomes too complex for high speed. Multilevel lookahead handles longer inputs, and the two-stage structure improves long-comparator speed at the cost of pipeline-latch transistors. Dynamic operation requires stable XOR outputs before evaluation, so XOR delay acts as setup time.   # p.254, p.256, p.258, p.260
evidence: §II-IV; Fig. 1-Fig. 7, p.255-p.259; Table I-Table III and Fig. 8-Fig. 11, p.260-p.262.

## new_families
none

## space_gaps
* `prefix_comparator` lacks a priority-encoder component slot, although the comparator explicitly instantiates a multilevel-lookahead priority encoder fused into the MDM. # p.255-p.257
* `priority_encoder.output_form` lacks `one_hot_only`; the encoder produces exactly one asserted bit at the MSUB without producing a binary index. # p.255
* `prefix_comparator` lacks choices for dynamic/static circuit style and half-cycle pipeline partitioning, which are explicit design axes in this implementation. # p.256, p.258-p.259

## open_questions
* The supplied text does not expose the numeric cells of Tables I-III, so exact transistor-count/layout-area/simulated timing/power values remain unavailable beyond the prose results.
* The paper does not assign a radix to the multilevel-lookahead comparator hierarchy, so `prefix_comparator.radix` is UNKNOWN.
