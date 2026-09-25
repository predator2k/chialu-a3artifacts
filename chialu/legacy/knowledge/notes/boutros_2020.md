---
handle: boutros_2020
citation: A. Boutros, E. Nurvitadhi, R. Ma, S. Gribok, Z. Zhao, J. C. Hoe, et al., "Beyond Peak Performance: Comparing the Real Performance of AI-Optimized FPGAs and GPUs", International Conference on Field-Programmable Technology (ICFPT), 2020
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_DOT_ACC]
formats: [int8]
authority: incremental
pages_read: 10 / 10
---

## summary
The paper enhances a Brainwave NPU overlay to use Stratix 10 NX AI tensor blocks for persistent int8 matrix-vector inference. The enhanced NPU reorganizes operand delivery, accumulation, tile reduction, and multicore execution to improve tensor-block utilization on low-batch MLP/RNN/GRU/LSTM workloads. Measurements compare implementation efficiency, core throughput, system latency, and energy efficiency against Stratix 10 MX/GX NPUs and Nvidia T4/V100 GPUs.

## families
### ai_tensor_block  (role: analyzes)
mechanism: The Stratix 10 NX block contains three dot-product units, each with ten 8×8 multipliers, and three optional accumulators. Two ping-pong register banks receive operands through an 80-bit data port or a dedicated cascade; another ten operands are broadcast to all three dot-product units. One bank supplies computation while the other loads over three cycles, and accumulator chains connect blocks into longer dot products. The evaluated NPU uses the block's int8 tensor mode. (p.12)
choices:
  dot_width: 10 [outside domain]   # p.12
  element_format: int8   # p.12
  accumulate_format: int32   # p.13
  cascade_tensor_chain: true   # p.12
new_choices:
  dot_units_per_block: 3 — number of independent dot-product units in one tensor block   # p.12
  operand_delivery: broadcast_plus_ping_pong_cascade — one operand set is broadcast while the other is supplied by cascaded reuse banks   # p.12
  accumulators_per_block: 3 — number of optional hard accumulators   # p.12
slots:
  none
parameters: 3 dot-product units; 10 int8 multipliers per unit; two ping-pong banks; three registers per bank; 3-cycle bank loading; outputs after 3 cycles   # p.12
results:
| metric | value | unit | technology / device | baseline | condition | page |
| multiplier count | 67,200 | multipliers | Intel 14nm / Stratix 10 NX, 2020 | 12,800 on Stratix 10 MX 2100; 19,200 on Stratix 10 GX 2800 | largest enhanced NPU overlay | p.13 |
| tensor-block use | 3,600 (91%) | tensor blocks | Intel 14nm / Stratix 10 NX, 2020 | UNKNOWN | complete NPU | p.13 |
| MVU tensor-mode use | 2,240 (57% of device tensor blocks) | tensor blocks | Intel 14nm / Stratix 10 NX, 2020 | UNKNOWN | blocks counted toward NPU peak TOPS | p.13 |
| frequency | 300 | MHz | Intel 14nm / Stratix 10 NX, 2020 | 290 MHz MX; 275 MHz GX | largest overlay | p.13 |
| peak int8 throughput | 40.3 | TOPS | Intel 14nm / Stratix 10 NX, 2020 | 7.4 TOPS MX; 10.6 TOPS GX | only MVU tensor blocks counted | p.13 |
| compute density | 19.45 | TOPS/Mil.LEs | Intel 14nm / Stratix 10 NX, 2020 | 3.58 MX; 3.84 GX | largest overlay | p.13 |
| soft-logic reduction | 36%; 55% | percent | Intel 14nm / Stratix 10 NX, 2020 | MX; GX implementations | tensor blocks plus NPU microarchitectural optimizations | p.14 |
errors_and_checks: none
conditions: The application must provide enough operands each cycle to keep the multipliers busy. (p.12) Longer tensor-block chains require larger batches when matrix blocks occupy the reuse banks; the selected mapping instead broadcasts matrix rows and keeps a low batch size. (p.12) Only the int8 tensor mode is evaluated. (p.12)
evidence: §III-B, Figs. 2-3, Table I, §IV-B (pp.12-14)

### integer_mac  (role: extends)
mechanism: The enhanced NPU maps batches of three input vectors onto each core and reuses each vector block across matrix rows. A BRAM scratchpad stores interleaved int32 partial results for a shared adder after inter-tile reduction. Each tile performs local binary reduction and passes results through a daisy chain. Two complete five-stage cores share persistent matrix register files and execute one instruction stream, producing an effective batch size of six. (p.13)
choices:
  array_style: simd_packed_dot   # p.12
  accumulator_width_bits: 32   # p.13
new_choices:
  persistent_weight_storage: shared_mrf — cores share on-chip matrix register files containing persistent model weights   # p.13
  inter_tile_connection: daisy_chain — each tile locally reduces prior and current results before forwarding them   # p.13
  accumulator_storage: bram_scratchpad — interleaved partial results share one adder through BRAM storage   # p.13
slots:
  reduction: binary_tree   # p.13
parameters: 2C-7T-40D-40L; 2 cores; 7 tiles; 40 DPEs; 40 lanes; batch 3 per core; effective batch 6; 300 MHz   # p.13
results:
| metric | value | unit | technology / device | baseline | condition | page |
| maximum measured throughput | 32.4 | TOPS | Intel 14nm / Stratix 10 NX, 2020 | 40.3 TOPS NPU peak | RNN-1792-256, batch 6 | p.14 |
| maximum measured utilization | 80.3% | percent | Intel 14nm / Stratix 10 NX, 2020 | NPU peak | RNN-1792-256, batch 6 | p.14 |
| latency | 1.1 | ms | Intel 14nm / Stratix 10 NX, 2020 | UNKNOWN | GRU-1152-256, batch 6 | p.14 |
| performance density speedup | ∼3.5× | ratio | Intel 14nm / Stratix 10 NX, 2020 | baseline NPU on Stratix 10 MX/GX | geometric mean across studied workloads | p.14 |
| core-compute speedup | 24.2×; 11.7× | ratio | Intel 14nm / Stratix 10 NX, 2020 | Nvidia T4; Nvidia V100 | average, batch 6 | p.15 |
| core-compute speedup | 22.3×; 9.3× | ratio | Intel 14nm / Stratix 10 NX, 2020 | Nvidia T4; Nvidia V100 | average, batch 3 | p.15 |
| accelerator utilization | 37.1% | percent | Intel 14nm / Stratix 10 NX, 2020 | T4 1.5%; V100 3% | geometric mean, batch 6 | p.15 |
| system speedup, short RNN | 16-19×; 15-25× | ratio | Intel 14nm / Stratix 10 NX, 2020 | T4; V100 systems | batch 6, sequence length 8 | p.16 |
| system speedup, long RNN | 11-16×; 5-6× | ratio | Intel 14nm / Stratix 10 NX, 2020 | T4; V100 systems | batch 6, sequence length 256 | p.16 |
| board power | 54-70 | W | Intel 14nm / Stratix 10 NX development kit, 2020 | T4 27-45 W; V100 35-72 W | continuously running GEMV/DL workloads | p.17 |
| energy-efficiency gain | 12-16×; 8-12× | TOPS/Watt ratio | Intel 14nm / Stratix 10 NX, 2020 | T4; V100 | average, batch 6 | p.17 |
errors_and_checks: none
conditions: D=L=40 limits the bandwidth mismatch between the MVU and the remaining pipeline. (p.13) Batch sizes divisible by six fully use the two batch-3 cores; batches 8, 32, and 256 reach at most 67%, 89%, and 99% of batch-6 performance. (p.15) Persistent weights must fit in on-chip memory. (pp.11,15) The comparison excludes initialization/kernel-launch/host-device-transfer overhead for core-compute results and includes those costs only in the system-level evaluation. (pp.14,16)
evidence: §IV-A, Fig. 4, Tables I-II, Figs. 5-9, §§V-VII (pp.13-17)

## new_families
none

## space_gaps
* `ai_tensor_block.dot_width` excludes the implemented width 10 because its domain advances in steps of four. (p.12)
* `ai_tensor_block` lacks choices for dot-unit count, ping-pong/cascade operand reuse, broadcast delivery, and optional accumulator count. (p.12)
* `integer_mac` lacks choices for persistent weight storage, BRAM-based interleaved accumulation, and daisy-chained tile reduction. (p.13)

## open_questions
* The paper does not specify saturation or overflow behavior for the int32 accumulators.
* The paper reports native int4/fp32/block-floating-point/bfloat modes for the tensor block but evaluates only int8 tensor mode.
