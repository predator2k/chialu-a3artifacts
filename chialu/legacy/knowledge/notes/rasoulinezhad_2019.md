---
handle: rasoulinezhad_2019
citation: S. Rasoulinezhad, H. Zhou, L. Wang, P. H. W. Leong, "PIR-DSP: An FPGA DSP Block Architecture for Multi-Precision Deep Neural Networks", IEEE Symposium on Field-Programmable Custom Computing Machines (FCCM), 2019
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_DOT_ACC]
formats: [int2, uint2, int4, uint4, int9, uint9, int18, uint18, int27, uint27]
authority: incremental
pages_read: 35-44 / 10
---

## summary
PIR-DSP modifies a Xilinx DSP48E2 with a run-time decomposable multiplier, semi-2D low-precision chaining, and an embedded FIFO/register file for DNN convolutions (p.35). The block performs 6/12/24 MACs per cycle at 9/4/2-bit precision and reduces estimated DNN run-time energy at the cost of one extra latency cycle and 28% more area (pp.40, 42).

## families
### multiprecision_block_proposal  (role: proposes)
mechanism: The MAC-IP chops the 27×18 operands into 3×2 9-bit parts, then recursively decomposes each signed/unsigned 9×9 Baugh-Wooley multiplier into two 4×4 or four 2×2 multipliers. Mode-controlled partial-product logic and blocked carry paths preserve independent products. PIR-DSP adds precision-aware ALU partitions, forwarding to either of the next two DSPs, and a configurable FIFO/register file (pp.37-40).
choices:
  fracture_to: 24 [outside domain]   # pp.38, 40
  runtime_composable: true   # pp.37-38
new_choices:
  chopping_factors: independently parameterized i and j — the counts of operand chops in M×NCijDk   # p.37
  recursive_decomposition_depth: k — the recursive depth in M×NCijDk   # p.37
  runtime_signedness_control: per operand — each operand can be signed or unsigned at run time   # p.38
  chain_forwarding_distance: 1 or 2 DSPs — selects the next DSP or bypasses it   # p.39
  embedded_reuse_storage: FIFO/RF — a sequentially loaded register file with two read ports and adjustable FIFO length   # p.39
slots:
  multiplier: twin_precision_subword [partition=quarters, base_scheme=baugh_wooley, per_lane_signed=true]   # pp.37-38
parameters: 27×18C32D0/D1/D2 and 27×27C33D0/D1/D2 MAC-IP configurations; 27×18C32D2 in PIR-DSP; 27×18, 9×9, 4×4, and 2×2 modes; one additional pipeline-register layer   # pp.37-40
results:
| metric | value | unit | technology / device | baseline | condition | page |
| area ratio, 27×18C32D0/D1/D2 | 1.46/1.86/1.70 | ratio | SMIC 65-nm / 2019 | 27×18-MAC, ratio 1 = 9224 um2 | MAC-IP | p.40 |
| Fmax, 27×18C32D0/D1/D2 | 730/671/538 | MHz | SMIC 65-nm / 2019 | 27×18-MAC, 763 MHz | MAC-IP | p.40 |
| MACs per cycle, 27×18C32D2 | 1/6/12/24 | MAC/cycle | SMIC 65-nm / 2019 | 27×18-MAC, 1/1/1/1 | 27×18/9-bit/4-bit/2-bit | p.40 |
| energy per MAC, 27×18C32D2 | 47.9/8.0/4/2.0 | pJ | SMIC 65-nm / 2019 | 27×18-MAC, 28.4/28.4/28.4/28.4 pJ | 27×18/9-bit/4-bit/2-bit | p.40 |
| area ratio, 27×27C33D0/D1/D2 | 2.12/2.21/2.36 | ratio | SMIC 65-nm / 2019 | 27×18-MAC, ratio 1 = 9224 um2 | generated MAC-IP | p.40 |
| Fmax, 27×27C33D0/D1/D2 | 714/581/380 | MHz | SMIC 65-nm / 2019 | 27×18-MAC, 763 MHz | generated MAC-IP | p.40 |
| MACs per cycle, 27×27C33D2 | 1/9/18/36 | MAC/cycle | SMIC 65-nm / 2019 | 27×18-MAC, 1/1/1/1 | 27×27/9-bit/4-bit/2-bit | p.40 |
| energy per MAC, 27×27C33D2 | 90.8/10.1/5.0/2.5 | pJ | SMIC 65-nm / 2019 | 27×18-MAC, 28.4/28.4/28.4/28.4 pJ | 27×27/9-bit/4-bit/2-bit | p.40 |
| PIR-DSP area | 32505 | um2 | SMIC 65-nm / 2019 | DSP48E2, 25419 um2 | MAC-IP + interconnect + reuse | p.40 |
| PIR-DSP area ratio | 1.28 | ratio | SMIC 65-nm / 2019 | DSP48E2, 1.00 | complete PIR-DSP | p.40 |
| PIR-DSP Fmax | 357 | MHz | SMIC 65-nm / 2019 | DSP48E2, 463 MHz | complete PIR-DSP | p.40 |
| estimated energy, NASNet-A/MobileNet-v2/ShuffleNet-v2 | 31/19/13 | % of baseline | SMIC 65-nm / 2019 | conventional DSP implementation, 100/100/100% | 9/4/2-bit, all optimizations | p.42 |
| estimated energy, SqueezeNet | 29/17/12 | % of baseline | SMIC 65-nm / 2019 | conventional DSP implementation, 100/100/100% | 9/4/2-bit, all optimizations | p.42 |
errors_and_checks: The 27×18, six 9×9, twelve 4×4, and twenty-four 2×2 MAC modes operate without precision loss; prediction-accuracy error is not reported (p.38).
conditions: PIR-DSP targets standard/depth-wise/point-wise convolution and benefits low-precision operation; FC computations are unaffected by the changes (p.37). PIR-DSP has better reported performance at 8×8 and below than the compared Boutros design, but worse PPA at 16×16 and above (p.42). The complete block adds one latency cycle and 28% area, and an unused pre-adder remains on the critical path (p.42).
evidence: §III, Figures 2-4, Tables II-III, §IV.B-E, Tables VI-VIII (pp.37-42)

### twin_precision_subword  (role: extends)
mechanism: Each 9-bit operand is extended under independent sign controls and multiplied by a signed 10×10 Baugh-Wooley structure. Mode controls alter partial-product cells and stop carry propagation so one 9×9 multiplier becomes two half-precision or four quarter-precision multipliers; the decomposition is applied recursively (pp.37-38).
choices:
  partition: quarters   # pp.37-38
  base_scheme: baugh_wooley   # p.37
  per_lane_signed: true   # pp.37-38
new_choices:
  decomposition_depth: 0/1/2 — the number of recursive twin-precision decompositions   # pp.37-38
slots:
  lane_cpa: UNKNOWN
parameters: 9×9 base multiplier; depth factors 0/1/2; two 4×4 or four 2×2 products per base multiplier   # pp.37-38
results:
| metric | value | unit | technology / device | baseline | condition | page |
| parallel products per 9×9 multiplier | 1/2/4 | products | SMIC 65-nm / 2019 | depth 0, 1 product | decomposition depth 0/1/2 | pp.37-38 |
errors_and_checks: Extra bits preserve full precision across the decomposed modes (p.38).
conditions: The technique requires changes to partial-product logic and carry-propagation paths; each operand’s signed/unsigned mode is controlled at run time (p.38).
evidence: §III.A.2, Figures 3-4 (pp.37-39)

### dsp48_style_slice  (role: extends)
mechanism: PIR-DSP retains the DSP48E2 pre-adder, multiplier/ALU organization, pattern detector, and cascade concept while replacing the multiplier/ALU with the decomposable MAC-IP. The ALU partitions become 4/8/18/48-bit, and the input chains gain precision-controlled forwarding to either of the next two DSPs (pp.36, 39-40).
choices:
  mult_shape: 27x18   # p.36
  pre_adder: true   # p.36
  alu_width: 48   # p.36
  alu_op_set: add_sub_logic_wide_xor   # pp.36, 40
  simd_partition: 4/8/18/48-bit [outside domain]   # p.40
  pattern_detector: true   # pp.36, 40
  cascade_paths: result_and_operand   # pp.36, 39
new_choices:
  semi_2d_forwarding: true — each DSP can forward data/results to two DSP destinations   # pp.38-39
  fifo_register_file: 4×2 30-bit — embedded two-read-port storage configurable as a FIFO   # pp.39-40
slots:
  multiplier: twin_precision_subword [partition=quarters, base_scheme=baugh_wooley, per_lane_signed=true]   # pp.37-38
  alu_adder: carry_lookahead   # p.40
parameters: 48-bit ALU; 4/8/18/48-bit SIMD; 4×2 30-bit RF; bypassable registers; one added multiplier pipeline layer   # pp.38-40
results:
| metric | value | unit | technology / device | baseline | condition | page |
| critical path | 3.85 | ns | SMIC 65-nm / 2019 | Virtex-5 DSP48E1 speed grade -1, 3.94 ns | synthesized DSP48E2 model | p.39 |
| standard/DW read-access energy | 31 | % of baseline | XC5VLX155T estimates / 2019 | off-DSP streaming, 100% | stream + embedded RF, cited MobileNet-v2 layer | pp.41-42 |
| PW read-access energy | 44 | % of baseline | XC5VLX155T estimates / 2019 | off-DSP streaming, 100% | stream + embedded RF, cited MobileNet-v2 layer | pp.41-42 |
errors_and_checks: none
conditions: Semi-2D chaining is intended for mappings with a small second dimension, especially 3×3 convolutions (p.39). The energy analysis assumes BRAM-resident inputs/weights, 65-nm-scaled movement costs, and linear energy scaling with word length outside the MAC (pp.40-41).
evidence: §II.B.1, Figure 1, §III.B-C, Figure 2, §IV.A-D, Tables III-VI (pp.36-42)

## new_families
none

## space_gaps
* `multiprecision_block_proposal.fracture_to` does not represent PIR-DSP’s six/twelve/twenty-four parallel MAC lanes or distinguish chopping from recursive decomposition (pp.37-40).
* `dsp48_style_slice.simd_partition` lacks PIR-DSP’s 4/8/18/48-bit ALU partition modes (p.40).
* The DSP vocabulary lacks choices for semi-2D chain fanout/bypass distance and embedded run-time FIFO/register-file reuse (pp.38-40).

## open_questions
* The paper does not report whether the final lane accumulation uses a registry CPA family beyond the stated carry-lookahead modifications.
* The vocabulary does not define whether `fracture_to` means recursive subdivision factor, number of multiplier lanes, or minimum operand width, so the reported value 24 must not be normalized during merging.
