---
handle: arora_2022
citation: A. Arora, S. Ghosh, S. Mehta, V. Betz, L. K. John, "Tensor Slices: FPGA Building Blocks for the Deep Learning Era", ACM Transactions on Reconfigurable Technology and Systems, 2022
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_DOT_ACC]
formats: [int8, int16, int32, int48, fp16, bf16, fp32]
authority: incremental
pages_read: 34 / 34
---

## summary
The paper proposes an FPGA Tensor Slice containing a dynamically configurable systolic PE array for matrix/matrix-vector operations, element-wise operations, multipliers, and MACs in int8/int16/fp16/bf16 formats (p.3-5). The slice increases compute density for DL benchmarks while retaining an I/O-limited Individual PE mode for other workloads (p.13, p.20-23).

## families
### ai_tensor_block  (role: proposes)
mechanism: The Tensor Slice contains a 2D array of 16 physical PEs behind a 50% sparsely populated local input crossbar. Each PE combines small adders/multipliers into larger integer or floating-point MAC datapaths. A physical PE operates as four logical PEs for int8 or one logical PE for int16/fp16/bf16. Tensor mode performs systolic matrix-matrix/matrix-vector operations and element-wise operations. Individual PE mode exposes eight PEs as independent multipliers or MACs. Multiple slices chain in two dimensions for larger matrices (p.4-6, p.8-13).
choices:
  element_format: {int8, int16 [outside domain], fp16, bf16}   # p.4
  accumulate_format: {int32, int48 [outside domain], fp32}   # p.4
  cascade_tensor_chain: true   # p.10-12
new_choices:
  operation_set: {matrix_matrix, matrix_vector, elementwise_add, elementwise_subtract, elementwise_multiply, multiplier, mac} — dynamically selected operating modes   # p.5, p.13
  precision_fracturing: {4x_int8, 1x_16bit} — logical PEs supplied by each physical PE   # p.5
  individual_pe_exposure: 8_of_16 — PEs exposed through the available slice I/O footprint   # p.13
  local_input_crossbar_population: 50% — sparse crossbar population used for routability   # p.4
slots:
  multiplier: UNKNOWN   # p.14-15
parameters: 16 physical PEs; 64 logical int8 PEs or 16 logical 16-bit PEs; 8×8 int8 or 4×4 int16/fp16/bf16 tensor operations; 64 int8 MACs/clock, 16 int16/fp16/bf16 MACs/clock for matrix-matrix mode; 310 inputs and 298 outputs; 8-row block; 3.5× LB-column width   # p.4-8, p.13, p.15
results:
| metric | value | unit | technology / device | baseline | condition | page |
| area | 55218 | um2 | 22nm modeled FPGA; 2022 | Agilex-like DSP Slice: 12597 um2 | complete Tensor Slice | p.21 |
| INT8 throughput | 25.0 | GigaMACs/sec | 22nm modeled FPGA; 2022 | Agilex-like DSP Slice: 1.7 GigaMACs/sec | matrix-matrix mode | p.21 |
| INT8 throughput/area | 453.2 | GigaMACs/sec/mm2 | 22nm modeled FPGA; 2022 | Agilex-like DSP Slice: 136.2 GigaMACs/sec/mm2 | matrix-matrix mode | p.21 |
| INT16 throughput | 6.2 | GigaMACs/sec | 22nm modeled FPGA; 2022 | Agilex-like DSP Slice: 0.8 GigaMACs/sec | matrix-matrix mode | p.21 |
| FP16/BF16 throughput | 4.8 | GigaMACs/sec | 22nm modeled FPGA; 2022 | Agilex-like DSP Slice: 0.7 GigaMACs/sec | matrix-matrix mode | p.21 |
| peak INT8 FPGA throughput | 1.86× | baseline | 22nm modeled FPGA; 2022 | FPGA without Tensor Slices | Prop_10pct | p.25 |
| peak INT16/FP16/BF16 FPGA throughput | ~1.42× | baseline | 22nm modeled FPGA; 2022 | FPGA without Tensor Slices | Prop_10pct | p.25 |
| used area | 0.45× | baseline | 22nm modeled FPGA; 2022 | FPGA without Tensor Slices | average across DL benchmarks | p.26-27 |
| achieved frequency | 1.63× | baseline | 22nm modeled FPGA; 2022 | FPGA without Tensor Slices | average across DL benchmarks | p.27 |
| routed wirelength | 0.45× | baseline | 22nm modeled FPGA; 2022 | FPGA without Tensor Slices | average across DL benchmarks | p.27-28 |
| VTR flow runtime reduction | 73% | reduction | 22nm modeled FPGA; 2022 | FPGA without Tensor Slices | average across DL benchmarks | p.29 |
| non-DL frequency degradation | 2.3% | degradation | 22nm modeled FPGA; 2022 | FPGA without Tensor Slices | Prop_30pct average | p.27 |
| non-DL routed wirelength increase | 7.7% | increase | 22nm modeled FPGA; 2022 | FPGA without Tensor Slices | Prop_30pct average | p.28 |
errors_and_checks: Integer products accumulate in int32 or int48, while fp16/bf16 products accumulate in fp32; outputs optionally retain the accumulation precision or use convergent round-half-to-even rounding to the input precision; floating-point exception flags are provided (p.4, p.7, p.12-13).
conditions: Matrix dimensions not divisible by 8 for int8 or 4 for 16-bit formats waste PEs through fragmentation (p.21-22). Individual PE mode has lower performance than DSP slices because the local input crossbar increases access delay (p.13). Tensor Slice columns should remain close because dispersed columns reduce frequency and can increase the minimum FPGA grid area (p.17, p.30). RTL must manually instantiate Tensor Slices because the evaluated synthesis flow cannot infer them (p.17-18, p.20).
evidence: Sections 3-6; Figures 1-18; Tables 1, 4-6, 9, 11-16 (p.4-32).

### integer_mac  (role: instantiates)
mechanism: The Tensor Slice implements matrix multiplication with a 2D systolic PE array. Matrix A values travel left-to-right, matrix B values travel top-to-bottom, and each PE retains its accumulated result until computation finishes. Bias preloading and accumulation across tiles are supported (p.8).
choices:
  array_style: systolic_array   # p.4, p.8
  accumulator_width_bits: {32, 48}   # p.4
new_choices:
  none
slots:
  mul: UNKNOWN   # p.5-6
  reduction: UNKNOWN   # p.5-6
parameters: 64 int8 MACs/clock with int32 accumulation; 16 int16 MACs/clock with int48 accumulation; 16 fp16/bf16 MACs/clock with fp32 accumulation   # p.4, p.8
results:
| metric | value | unit | technology / device | baseline | condition | page |
| matrix-vector utilization | 25% | utilization | 22nm modeled FPGA; 2022 | 100% matrix-matrix utilization | int8 | p.22 |
| matrix-vector utilization | 50% | utilization | 22nm modeled FPGA; 2022 | 100% matrix-matrix utilization | int16/fp16/bf16 | p.22 |
errors_and_checks: none
conditions: Larger M/N dimensions use chained slices, while larger K dimensions use additional accumulation cycles so extended-precision intermediates remain within the slices (p.12).
evidence: Sections 3.2-3.3; Figures 3-8 (p.5-12).

## new_families
none

## space_gaps
* ai_tensor_block.element_format lacks int16, which the Tensor Slice supports natively (p.4).
* ai_tensor_block.accumulate_format lacks int48, which the int16 mode uses (p.4).
* ai_tensor_block lacks choices for tensor operation set, precision fracturing, Individual PE exposure, and local input crossbar population (p.4-5, p.13).

## open_questions
* The paper does not specify the internal integer multiplier/adder microarchitectures, so the multiplier and CPA-related component slots remain UNKNOWN (p.14-15).
* The paper does not establish whether floating-point MAC execution has a fused single-rounding contract, so no FMA family is assigned (p.6, p.12-13).
* Table 4 reports total Tensor Slice area as 55219 um2, while Table 11 reports 55218 um2 (p.15, p.21).
