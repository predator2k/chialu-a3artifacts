---
handle: arora_2021
citation: A. Arora, S. Mehta, V. Betz, L. K. John, "Tensor Slices to the Rescue: Supercharging ML Acceleration on FPGAs", ACM/SIGDA International Symposium on Field-Programmable Gate Arrays (FPGA), 2021
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_DOT_ACC, BINARY_ALU]
formats: [int8, int16, fp16, fp32]
authority: incremental
pages_read: 11 / 11
---

## summary
The paper proposes a hard FPGA Tensor Slice for matrix multiplication/element-wise operations with runtime-selectable int8/fp16 modes and fracturing into scalar adders/multipliers/MACs. The evaluated FPGA devotes about 3% of its area to Tensor Slices and improves ML benchmark frequency/area while causing about 1% average frequency/wirelength effects on non-ML benchmarks. (pp.23–32)

## families
### ai_tensor_block  (role: proposes)
mechanism: The Tensor Slice contains a 2D array of 16 physical PEs, input/output control, mode muxing, and a 50% sparsely populated local input crossbar. Matrix multiplication moves operands systolically across the PE array. Each PE shares multiplier/adder hardware between four int8 MACs with int16 accumulation and one fp16 MAC with fp32 accumulation. Runtime controls select tensor or individual-PE operation, precision, matrix multiplication, element-wise addition/subtraction, element-wise multiplication, bias preload, and tiled accumulation. Multiple slices chain in both matrix dimensions. (pp.24–27)
choices:
  element_format: {int8, fp16}   # p.24
  accumulate_format: {int16 [outside domain], fp32}   # p.24
  cascade_tensor_chain: true   # p.26
new_choices:
  runtime_mode_selection: true — operation/precision controls can change without FPGA reconfiguration   # p.25
  tensor_operations: {matrix_multiply, eltwise_add_sub, eltwise_multiply} — operations supported in Tensor mode   # p.25
  scalar_fracturing: individual_pe — exposes PEs as separately configured adders/multipliers/MACs   # p.25
  local_input_crossbar_population: 50% — sparsely populated crossbar makes input pins swappable   # p.24
  bias_preload: true — PE accumulators can be preloaded with an input matrix   # p.25
  tiled_accumulation: true — PE results can persist across tiled/blocked operations   # p.25
slots: none
parameters: 16 physical PEs; 4x4 fp16 or 8x8 int8 matrices; 16 fp16 or 64 int8 MACs/cycle; 32 fp16 or 128 int8 ops/clock; 16 bytes/clock input bandwidth; 12 of 16 PEs exposed in Individual PE mode; 481 inputs and 306 outputs including clock/reset   # pp.25–28
results:
| metric | value | unit | technology / device | baseline | condition | page |
| throughput | 47.49 | Gops/sec | 22nm modeled, 2021 | Agilex-like DSP slice: 3.13 Gops/sec | int8; 15.18x baseline | p.30 |
| throughput | 10.4 | Gops/sec | 22nm modeled, 2021 | Agilex-like DSP slice: 1.34 Gops/sec | fp16; 7.74x baseline | p.30 |
| frequency | 371 | MHz | 22nm modeled, 2021 | Agilex-like DSP slice: 391 MHz | int8; 0.95x baseline | p.30 |
| frequency | 325 | MHz | 22nm modeled, 2021 | Agilex-like DSP slice: 336 MHz | fp16; 0.97x baseline | p.30 |
| area | 50032 | 𝑢𝑚 2 | 22nm modeled, 2021 | Agilex-like DSP slice: 12433 𝑢𝑚 2 | complete slice; 4.02x baseline | p.30 |
| frequency | 817 | MHz | 10nm scaled model, 2021 | none | fixed-point mode | p.28 |
| frequency | 716 | MHz | 10nm scaled model, 2021 | none | floating-point mode | p.28 |
| core area | 13338 | 𝑢𝑚 2 | 22nm modeled, 2021 | none | 4x4 fp16 matrix multiplication only | p.29 |
| core area | 16368 | 𝑢𝑚 2 | 22nm modeled, 2021 | none | 8x8 int8 matrix multiplication only | p.29 |
| core area | 20598 | 𝑢𝑚 2 | 22nm modeled, 2021 | int8-only core: 16368 𝑢𝑚 2 | dual-precision matrix multiplication; 1.26x | p.29 |
| core area | 24673 | 𝑢𝑚 2 | 22nm modeled, 2021 | int8-only core: 16368 𝑢𝑚 2 | Individual PE modes added; 1.51x | p.29 |
| core area | 29062 | 𝑢𝑚 2 | 22nm modeled, 2021 | int8-only core: 16368 𝑢𝑚 2 | element-wise modes added; 1.78x | p.29 |
| ML benchmark frequency | 2.44x | baseline | 22nm VTR Agilex-like FPGA, 2021 | FPGA without Tensor Slices | average, Proposed_3pct | p.30 |
| ML benchmark frequency | 2.82x | baseline | 22nm VTR Agilex-like FPGA, 2021 | FPGA without Tensor Slices | maximum, Proposed_3pct | p.30 |
| ML benchmark used area | 0.4x | baseline | 22nm VTR Agilex-like FPGA, 2021 | FPGA without Tensor Slices | average | p.31 |
| ML benchmark used area | 0.3x | baseline | 22nm VTR Agilex-like FPGA, 2021 | FPGA without Tensor Slices | best case, fcl8 | p.31 |
| non-ML frequency degradation | less than 1 | % | 22nm VTR Agilex-like FPGA, 2021 | FPGA without Tensor Slices | average | p.30 |
| non-ML frequency degradation | 4.2 | % | 22nm VTR Agilex-like FPGA, 2021 | FPGA without Tensor Slices | worst case, arm_core/Proposed_9pct | p.30 |
| non-ML routing wirelength increase | 1 | % | 22nm VTR Agilex-like FPGA, 2021 | FPGA without Tensor Slices | average | p.32 |
errors_and_checks: none
conditions: Matrix dimensions that do not divide the native 4x4/8x8 shapes waste PEs, although the paper considers this insignificant for typical ML/DL matrix sizes. Individual PE mode is slower than LB-based addition or DSP-based multiplication because of Tensor Slice access delay. ML designs manually instantiate Tensor Slices because the synthesis tool cannot infer them. Large Tensor Slice allocations can increase non-ML wirelength or exhaust resources. (pp.25, 29–32)
evidence: §3, Figures 1–5, Tables 1 and 4–6; §4, Tables 7–10; §5, Figures 8–10 and Table 11 (pp.24–32)

## new_families
none

## space_gaps
* `ai_tensor_block.accumulate_format` lacks `int16`, which is the native int8 accumulation format. (p.24)
* `ai_tensor_block` lacks choices for runtime precision/operation selection, scalar PE fracturing, bias preload, tiled accumulation, and local-crossbar population. (pp.24–25)
* `ai_tensor_block` lacks a representation for precision-dependent matrix shapes and MAC counts: 4x4/16 MACs for fp16 and 8x8/64 MACs for int8. (pp.25, 27)

## open_questions
* The paper does not specify the internal microarchitecture families of the shared fixed-point/floating-point multipliers and adders. (p.28)
* The vocabulary’s `dot_width` does not state whether it denotes matrix dimension, dot-product length, PE count, or concurrent MAC count, so no value is assigned. (pp.25, 27)
* The 10nm frequencies are scaled estimates rather than measurements from fabricated Tensor Slice silicon. (p.28)
