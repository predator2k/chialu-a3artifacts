---
handle: boutros_2018
citation: A. Boutros, S. Yazdanshenas, V. Betz, "Embracing Diversity: Enhanced DSP Blocks for Low-Precision Deep Learning on FPGAs", International Conference on Field Programmable Logic and Applications (FPL), 2018
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU, VEC_DOT_ACC]
formats: [int4, int8, int9, int18, int27]
authority: incremental
pages_read: 35-42 / 8
---

## summary
The document proposes an Arria-10-like DSP block that supports one 27-bit, two 18-bit, four 9-bit, or eight 4-bit multiplications/MACs while preserving the baseline modes and interface (p.37-p.39). The final design has 12% block-area overhead, maintains 600 MHz, and raises total FPGA core area by 0.6% (p.39-p.40). CNN accelerator experiments report higher performance and lower utilized area at 8-bit and 4-bit precision (p.41-p.42).

## families
### multiprecision_block_proposal  (role: proposes)
mechanism: The enhanced DSP fractures selected Baugh-Wooley multiplier arrays and adds four standalone 4×4 multipliers. Modified/added 4:2 compressors separate or combine packed results while keeping the existing 72 output ports, routing-chain width, 27-bit mode, and dual 18-bit modes. Four 9×9 products or eight 4×4 products are supported. MAC mode groups products into two results that can enter soft logic or dedicated DSP chains (p.37-p.39).
choices:
  fracture_to: 8   # p.39
new_choices:
  native_multiply_mac_modes: {1x27, 2x18, 4x9, 8x4} — supported parallel multiplication/MAC widths and counts   # p.39
  small_multiplier_implementation: fracture M2/M3 plus four standalone 4×4 multipliers — option (2), the selected minimum post-P&R-area design   # p.38-p.40
  mac_result_grouping: two products per result at 9-bit and four products per result at 4-bit — avoids or limits extra compressor depth   # p.38-p.39
slots:
  multiplier: baugh_wooley_dadda_tree [signed_encoding=baugh_wooley, reduction_tree=dadda]   # p.37
parameters: 72 output ports; 600 MHz target; one 27×27, two 18×18, four 9×9, or eight 4×4 multiplications/MACs; two accumulated outputs in 9-bit and 4-bit MAC modes   # p.37-p.39
results:
| metric | value | unit | technology / device | baseline | condition | page |
| enhanced multiplication density | 2× | × | 28nm STMicroelectronics, 2018 | Arria-10-like DSP block | 9-bit multiplication | p.35 |
| enhanced multiplication density | 4× | × | 28nm STMicroelectronics, 2018 | Arria-10-like DSP block | 4-bit multiplication | p.35 |
| post-P&R area ratio | 1.04 | × | 28nm STMicroelectronics, 2018 | baseline DSP block | add 9×9 multiplication | p.40 |
| post-P&R area ratio | 1.05 | × | 28nm STMicroelectronics, 2018 | baseline DSP block | add 9×9 MAC | p.40 |
| post-P&R area ratio | 1.09 | × | 28nm STMicroelectronics, 2018 | baseline DSP block | add 4×4 multiplication using option (2) | p.40 |
| post-P&R area ratio | 1.18 | × | 28nm STMicroelectronics, 2018 | baseline DSP block | add 4×4 multiplication using option (3) | p.40 |
| post-P&R area ratio | 1.20 | × | 28nm STMicroelectronics, 2018 | baseline DSP block | add 4×4 MAC using C2 | p.40 |
| final post-P&R area | 11108 | μm2 | 28nm STMicroelectronics, 2018 | baseline DSP block, 9875 μm2 | add 4×4 MAC using C5 | p.40 |
| final block area overhead | 12% | % | 28nm STMicroelectronics, 2018 | baseline Arria-10-like DSP block | all proposed modes | p.39-p.40 |
| operating frequency | 600 | MHz | 28nm STMicroelectronics, 2018 | commercial DSP frequency target | final enhanced DSP block | p.39 |
| FPGA core area increase | 0.6% | % | 28nm FPGA model, 2018 | FPGA with baseline DSP blocks | assumes DSP blocks consume approximately 5% of FPGA area | p.40 |
| average accelerator performance enhancement | 1.32× | × | Arria 10 10AX115N2F45I1SG, 2018 | original FPGA | 8-bit DLA/ASU benchmarks | p.42 |
| average accelerator performance enhancement | 1.6× | × | Arria 10 10AX115N2F45I1SG, 2018 | original FPGA | 4-bit DLA/ASU benchmarks | p.42 |
| average DSP-only performance enhancement | 1.62× | × | Arria 10 10AX115N2F45I1SG, 2018 | original FPGA | 8-bit benchmarks; multiplications only in DSP blocks | p.42 |
| average DSP-only performance enhancement | 2.97× | × | Arria 10 10AX115N2F45I1SG, 2018 | original FPGA | 4-bit benchmarks; multiplications only in DSP blocks | p.42 |
| average utilized-area reduction | 15% | % | Arria 10 10AX115N2F45I1SG, 2018 | original FPGA | 8-bit benchmarks | p.42 |
| average utilized-area reduction | 30% | % | Arria 10 10AX115N2F45I1SG, 2018 | original FPGA | 4-bit benchmarks | p.42 |
errors_and_checks: Exact signed Baugh-Wooley multiplication is required; supported modes were checked with corner-case and randomly generated RTL vectors. No fault-coverage or false-alarm result is reported.   # p.37, p.39
conditions: The modified block must retain every baseline mode, must not add input/output ports, and must meet 600 MHz (p.37). Full fracturing option (1) fails timing after place and route, while option (2) has the lowest routed area (p.38-p.40). Accelerator gains depend on routing/BRAM limits and assume HBM plus a memory layout that fully uses available bandwidth (p.41-p.42).
evidence: §III-B-III-D, Fig. 4-Fig. 8, Table II, §IV, Fig. 11-Fig. 12, §V-C (p.37-p.42)

### carry_save_datapath  (role: instantiates)
mechanism: Multiplier outputs remain as redundant sum/carry pairs until immediately before DSP-block exit. All intermediate sum-of-products and MAC additions use 4:2 compressors, and a final CPA resolves the redundant result. Compressor carry-out depends on compressor inputs rather than carry-in, which removes carry-propagation delay between bit positions (p.37).
choices:
  compressor: 4_2   # p.37
  assimilation_point: end_of_chain   # p.37
  accumulator_redundant: true   # p.37
new_choices:
  none
slots:
  none
parameters: compressors C1-C5; one final CPA; split 9-bit MAC and two-level 4-bit MAC structures   # p.37-p.39
results: none reported separately
errors_and_checks: none
conditions: An added third compressor stage in the four-product 9-bit MAC fails the 600 MHz timing constraint, so the implemented mode splits four products into two pairwise sums (p.38). A dedicated C5 plus output selection costs less routed area than input multiplexing around C2 for the second 4-bit MAC addition level (p.39-p.40).
evidence: §III-A, §III-C-III-D, Fig. 5-Fig. 8, Table II (p.37-p.40)

## new_families
### baugh_wooley_dadda_tree  (domain: mul: integer multipliers, closest: carry_save_array, why_not: carry_save_array specifies a regular 2-D CSA array, while this document uses Baugh-Wooley partial products followed by a Dadda reduction tree)
mechanism: A generated signed multiplier forms two’s-complement partial products with the Baugh-Wooley algorithm and reduces them with a Dadda tree. The tree emits redundant sum/carry outputs for later assimilation inside the DSP block. The implemented arrays include 18×18, 9×9, and 9×18 sizes; selected arrays are fractured for packed 9×9 or 4×4 operations (p.37-p.39).
choices: signed_encoding: {baugh_wooley}; reduction_tree: {dadda}; output_form: {sum_carry}; fracturable: Bool
results: none reported separately
evidence: §III-A-III-D, Fig. 2-Fig. 8 (p.37-p.39)

## space_gaps
* multiprecision_block_proposal lacks a native-width/mode choice for `{1x27, 2x18, 4x9, 8x4}` and a choice distinguishing fractured arrays from added standalone multipliers (p.38-p.39).
* multiprecision_block_proposal.multiplier cannot name the document’s Baugh-Wooley/Dadda-tree multiplier because no existing multiplier family represents that combination (p.37).
* carry_save_datapath.compressor uses vocabulary value `4_2`, while the document prints the circuit as `4:2` (p.37).

## open_questions
* The document does not state whether enhanced-mode selection is runtime-controlled or configuration-time-controlled, so `runtime_composable` remains UNKNOWN.
* The document calls the terminal structure a CPA but does not identify its adder family, so the assimilator/final-adder slot remains UNKNOWN.
* The benchmark mapping uses 8-bit weights/activations with the enhanced block’s 9-bit multiplier mode, but the treatment of the unused ninth input bit is not stated.
