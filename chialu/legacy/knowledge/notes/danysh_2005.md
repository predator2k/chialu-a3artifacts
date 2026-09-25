---
handle: danysh_2005
citation: A. Danysh, D. Tan, "Architecture and Implementation of a Vector/SIMD Multiply-Accumulate Unit", IEEE Transactions on Computers, vol. 54, no. 3, pp. 284-293, 2005
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_DOT_ACC]
formats: [int8, uint8, int16, uint16, int32, uint32, int64, uint64]
authority: incremental
pages_read: 10 / 10
---

## summary
The document proposes shared segmentation for a 64-bit fixed-point vector MAC supporting one 64 x 64, two 32 x 32, four 16 x 16, or eight 8 x 8 signed/unsigned operations. Mode-dependent partial-product masking and carry kills vectorize a radix-4 Booth/Wallace/CLA scalar MAC. Shared segmentation has similar area/delay to shared subtree at 16-bit width and becomes better as width and mode count increase. (pp.284, 292)

## families
### integer_mac  (role: instantiates)
mechanism: A fixed-point SIMD MAC feeds radix-4 Booth partial products and the accumulator into a Wallace CSA tree, then resolves the result with a 128-bit modified CLA. Shared hardware performs one, two, four, or eight lane operations according to the selected precision. (pp.284-285)
choices:
  array_style: simd_packed_mac [outside domain]   # p.284
new_choices:
  lane_mode_control: global_precision_mode — one control selects the 8/16/32/64-bit lane organization   # pp.284-285
slots:
  mul: twin_precision_subword [base_scheme=modified_booth]   # pp.284-285
  reduction: csa_tree   # pp.284-285
parameters: 64-bit operands; 128-bit final CPA; 1x64, 2x32, 4x16, or 8x8 signed/unsigned MACs; fully pipelineable   # p.284
results:
| metric | value | unit | technology / device | baseline | condition | page |
|---|---:|---|---|---|---|---|
| delay | UNKNOWN | UNKNOWN | 90 nm SOI / 2005 | scalar MAC and shared subtree VMAC | 16-, 32-, and 64-bit implementations; PPG/PPRT/CPA components | p.291 |
| delay | UNKNOWN | UNKNOWN | 0.13 um bulk / 2005 | scalar MAC and shared subtree VMAC | 16-, 32-, and 64-bit implementations; PPG/PPRT/CPA components | p.292 |
| die area | UNKNOWN | um2 | 90 nm SOI and 0.13 um bulk / 2005 | scalar MAC and shared subtree VMAC | 16-, 32-, and 64-bit implementations | p.292 |
errors_and_checks: No numerical error contract or fault checker is reported; functional testing varies each lane's two most-significant/two least-significant bits, fixes intermediate bits to all zeros or ones, and adds random patterns.   # p.292
conditions: Shared segmentation and shared subtree have similar area/delay for 16-bit designs. Shared segmentation becomes better for 32-bit and especially 64-bit designs because shared subtree adds CSA rows, fan-out, routing, and a result mux.   # p.292
evidence: §2.1, Fig.1, §4, Tables 1-3, Fig.22, §5

### twin_precision_subword  (role: proposes)
mechanism: Shared segmentation aligns each lane's partial products so lanes do not overlap. Mode-dependent multiplicand muxing/masking changes the partial-product arrangement, while carry kills at lane boundaries segment the common reduction tree and final CPA. The final result comes from the same hardware in every mode. (pp.284-290)
choices:
  partition: {halves, quarters, eighths [outside domain]}   # pp.284-285
  base_scheme: modified_booth   # p.284
  per_lane_signed: false   # pp.284-286
new_choices:
  sharing_method: {shared_segmentation, shared_subtree} — shared segmentation uses one carry-killed structure; shared subtree builds mode-specific subtree results and selects them   # pp.285, 288-292
slots:
  lane_cpa: carry_lookahead [group_size=4]   # pp.284, 290
parameters: smallest lane 8 bits; lane counts 1/2/4/8; signed or unsigned mode selected globally   # pp.284-286
results: none separately reported; see integer_mac.
errors_and_checks: none
conditions: Shared segmentation avoids the shared subtree method's sign-extension fan-out, extra CSA rows, intermediate fan-out, and final mode mux. Its advantage increases with operand width and supported mode count.   # p.292
evidence: Figs.2-8, §§2.2-2.4, §3.2, Tables 1-3, Fig.22

### booth_recoded_parallel  (role: instantiates)
mechanism: A radix-4 vector Booth recoder inserts zeros at lane boundaries, masks multiplier bits by mode, and multiplexes/masks the multiplicand before Booth selection. Negative partial products invert the multiplicand and append seln1/seln2 “hot ones” to the next row. Unsigned lanes contribute extra sign-derived partial products combined into one 128-bit row. (pp.285-288)
choices:
  booth_radix: 4   # p.284
  hard_multiple_gen: none   # pp.286-288
  sign_extension: sign_encoding [outside domain]   # pp.286-287
  negative_pp_encoding: ones_complement_plus_neg_bit   # p.286
new_choices:
  vector_boundary_zero_insertion: mode_dependent — zero bits restart Booth recoding at each lane boundary   # p.286
slots:
  reduction: csa_reduction_tree   # p.284
parameters: 64-bit scalar width; 8/16/32/64-bit modes; final partial product is 128 bits   # pp.284-288
results: none separately reported; see integer_mac.
errors_and_checks: none
conditions: The optimized mode mux requires at most a 3-input mux at ordinary positions. The full-width last partial product requires full multiplexing but enters late enough to remain outside the stated critical path.   # pp.287-288
evidence: §§2.1.1-2.2.2, Figs.2-15

### fused_csa  (role: instantiates)
mechanism: A Wallace tree reduces Booth partial products together with the accumulator. The accumulator adds one CSA stage. Shared segmentation masks carries crossing active lane boundaries at every tree level, while retaining the scalar tree shape. (pp.284, 288-289)
choices:
  compressor: 3:2   # pp.288-289
new_choices:
  boundary_carry_kill: mode_dependent — each CSA level suppresses carries crossing selected lane boundaries   # pp.288-289
slots:
  final_cpa: carry_lookahead [group_size=4]   # pp.284, 290
parameters: Wallace PPRT; accumulator insertion adds one CSA stage   # p.284
results: none separately reported; see integer_mac.
errors_and_checks: none
conditions: Carry-kill logic is incorporated into the full-adder cell and is reported to add no significant CSA-tree delay.   # pp.288-289
evidence: Fig.1, §2.3, Figs.16-17, equation (2)

### partitioned_carry_chain  (role: extends)
mechanism: Mode-dependent kill signals suppress carries crossing 8/16/32-bit lane boundaries in both the Wallace tree and the final CPA. The implemented CPA integrates the kill term into each 4-bit CLA block instead of widening the adder with inserted boundary bits. (pp.288-290)
choices:
  boundary_mechanism: carry_kill_gate   # pp.288-290
new_choices:
  partitioned_structures: {reduction_tree, final_cpa} — the same boundary-kill principle partitions both structures   # pp.288-290
slots:
  base_adder: carry_lookahead [group_size=4]   # p.290
parameters: boundaries selected for 8/16/32/64-bit modes; alternative widened CPA would be 135 bits, but was not selected   # pp.289-290
results: none separately reported; see integer_mac.
errors_and_checks: none
conditions: The selected CLA implementation places the early kill term outside the critical carry-in/group-generate path and is reported not to add critical-path delay.   # p.290
evidence: §§2.3-2.4, Figs.17-18, equations (2)-(3)

### carry_lookahead  (role: extends)
mechanism: The final 128-bit CPA consists of modified 4-bit CLA blocks. Each block adds a mode-dependent carry-in kill factor to the carry equations so vector lanes remain independent. (pp.284, 289-290)
choices:
  group_size: 4   # pp.284, 290
  block_sizing: uniform   # pp.284, 290
new_choices:
  carry_in_kill: mode_dependent — an early kill term disables interlane carry propagation within a CLA block   # pp.289-290
slots:
  none
parameters: 128-bit CPA; 4-bit CLA blocks   # pp.284, 290
results: none separately reported; see integer_mac.
errors_and_checks: none
conditions: The kill signal is available early, so the paper reports no added critical-path delay when the term is integrated into the CLA equations.   # p.290
evidence: §2.4, Fig.18, equation (3)

## new_families
none

## space_gaps
* `twin_precision_subword.partition` lacks `eighths`, which is required for the eight 8-bit lanes in the 64-bit unit.   # pp.284-285
* `twin_precision_subword` lacks a sharing-method choice distinguishing `shared_segmentation` from `shared_subtree`.   # pp.285, 288-292
* `booth_recoded_parallel.sign_extension` lacks the document's `sign_encoding` method.   # pp.286-287
* `partitioned_carry_chain` lacks coverage of mode-dependent carry kills inside a CSA reduction tree.   # pp.288-289
* `integer_mac.array_style` lacks a SIMD packed MAC value distinct from `simd_packed_dot`.   # p.284

## open_questions
* Tables 1-3 are present, but their numeric cells are absent from the supplied text, so delay and die-area values cannot be transcribed.
* Section 4 repeats “16-bit VMAC” where the listed 8/16/32-bit modes imply a 32-bit VMAC; the merge pass must not silently correct the text.   # p.291
* The interblock carry structure and total CLA level count are not stated.   # pp.284, 289-290
