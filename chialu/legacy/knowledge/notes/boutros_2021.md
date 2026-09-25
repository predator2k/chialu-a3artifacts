---
handle: boutros_2021
citation: A. Boutros, V. Betz, "FPGA Architecture: Principles and Progression", IEEE Circuits and Systems Magazine, 2021
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU, VEC_DOT_ACC]
formats: [int2, int3, int4, int8, int9, int16, fp16, bfloat16, fp24, fp32]
authority: survey
pages_read: 26 / 26 (pp.4-29)
---

## summary
The article surveys FPGA architecture evolution, including hardened carry circuits and DSP blocks for integer/floating-point arithmetic. The DSP survey follows fixed multipliers through variable-precision blocks, native floating-point DSPs, and low-precision AI tensor blocks. The article establishes that hard-block flexibility is constrained by routing-port area and must be evaluated across representative applications.

## families
### fpga_carry_chain  (role: compares)
mechanism: Hardened arithmetic reuses LUT routing ports or LUT outputs and propagates carry on dedicated interconnect with little or no programmability. Low-cost implementations harden ripple carry, while commercial variants also harden carry-skip or carry-lookahead structures. # p.11
choices:
  chain_segment_length: 8  # p.11
new_choices:
  arithmetic_bits_per_logic_element: 1 / 2 / 4 — Number of arithmetic bits supported by each logic element.  # pp.11-12
slots:
  none
parameters: 32-bit reported adder comparisons; Versal 8-bit carry-lookahead start granularity; Agilex 2 arithmetic bits per logic element; proposals with 4 arithmetic bits per logic element.  # p.11
results:
| metric | value | unit | technology / device | baseline | condition | page |
| speed | 3.4 | × | UNKNOWN (year UNKNOWN) | LUT implementation | 32-bit hardened ripple-carry adder | p.11 |
| additional speed-up | 20 | % | UNKNOWN (year UNKNOWN) | hardened ripple-carry structure | 32-bit hardened carry-skip adder | p.11 |
| average performance improvement | 75 | % | UNKNOWN (year 2020) | architecture without dedicated arithmetic circuits | arithmetic microbenchmarks | p.11 |
| average performance improvement | 15 | % | UNKNOWN (year 2020) | architecture without dedicated arithmetic circuits | general benchmarks | p.11 |
| MAC density improvement | 1.7 | × | proposed FPGA logic block (year 2019/2020) | conventional logic-block arithmetic | most promising 4-bit-per-logic-element proposal | p.12 |
| logic and routing area reduction | 8 | % | proposed FPGA logic block (year 2019/2020) | conventional logic-block arithmetic | general benchmarks | p.12 |
errors_and_checks: none
conditions: Dedicated carry wiring avoids the slow LUT-to-LUT carry path, but more capable arithmetic must reuse existing routing ports to control area. # p.11
evidence: Section III-A; Fig. 7; pp.10-12.

### dsp48_style_slice  (role: compares)
mechanism: Commercial DSP tiles combine hardened multiplier arrays with registers and an adder/subtractor/accumulator. Later generations add input pre-adders, coefficient storage, bitwise ALU operations, and dedicated input/result cascades for FIR structures. # pp.21-24
choices:
  mult_shape: 18x18 / 25x18 / 27x18  # pp.21-23
  pre_adder: true  # pp.22-23
  alu_op_set: add_sub_logic  # p.23
  cascade_paths: result_and_operand  # p.22
new_choices:
  coefficient_storage: embedded_bank — Read-only filter coefficients are stored inside the DSP block.  # p.23
slots:
  none
parameters: Virtex-II 18 × 18; Virtex-5 25 × 18; Ultrascale 27 × 18; registered systolic FIR datapaths.  # pp.21-23
results:
| metric | value | unit | technology / device | baseline | condition | page |
| area | 0.49 | mm2 | 40 nm Stratix IV (year UNKNOWN) | 1.46 mm2 soft implementation | 51-tap symmetric FIR, fixed coefficients | p.23 |
| area | 0.63 | mm2 | 40 nm Stratix IV (year UNKNOWN) | 5.35 mm2 soft implementation | 51-tap asymmetric FIR, input coefficients | p.23 |
| frequency | 510 | Mhz | 40 nm Stratix IV (year UNKNOWN) | 217 Mhz soft implementation | 51-tap asymmetric FIR, input coefficients | p.23 |
errors_and_checks: none
conditions: Advanced DSP modes often require manual block instantiation, which reduces design portability. # p.22
evidence: Section III-E; Figs. 15-17; Table III; pp.20-24.

### variable_precision_dsp  (role: analyzes)
mechanism: A multiplier array is fractured into smaller arrays while routing-port counts are limited through input/output sharing. Stratix combines two 9 × 9 regions inside an 18 × 18 array by splitting partial-product compressor trees and adding border-cell inversion for Baugh-Wooley signed multiplication. # pp.21-22
choices:
  native_widths: 9_18_27_36  # pp.21-24
  fracture_granularity: 9  # pp.21-22
new_choices:
  native_operation_formats: int9 / int4 — Native low-precision multiply/MAC modes added without changing the routing interface.  # p.24
slots:
  multiplier: carry_save_array [signed_scheme=baugh_wooley]  # p.22
parameters: eight 9 × 9, four 18 × 18, or one 36 × 36 operation in Stratix; later blocks provide one 27 × 27, two 18 × 18, or four 9 × 9 operations.  # pp.21-24
results:
| metric | value | unit | technology / device | baseline | condition | page |
| area efficiency | 8.5 | × | 40 nm Stratix IV (year UNKNOWN) | soft logic | 51-tap asymmetric FIR with input coefficients | p.23 |
| frequency improvement | about 2 | × | 40 nm Stratix IV (year UNKNOWN) | soft logic | FIR implementations using hard DSP blocks | p.23 |
errors_and_checks: none
conditions: Fracturing is most economical when smaller operations share the original multiplier’s routing ports. # pp.21-22
evidence: Section III-E; Figs. 15-16; Table III; pp.21-24.

### hard_fp_dsp  (role: instantiates)
mechanism: Arria 10 adds native fp32 multiplication by reusing fixed-point hardware and the existing programmable-routing interface. The implementation omits uncommon features including subnormals, flags, and multiple rounding schemes to limit area. # p.23
choices:
  fp_format: fp32  # p.23
new_choices:
  ieee_feature_subset: no subnormals / no flags / limited rounding — IEEE features omitted from the hardened mode.  # p.23
slots:
  none
parameters: Native fp32 in Arria 10; later Agilex support includes fp16 and bfloat16.  # pp.23-24
results:
| metric | value | unit | technology / device | baseline | condition | page |
| DSP block area increase | 10 | % | Arria 10, node UNKNOWN (year 2015) | fixed-point DSP block | native fp32 support | p.23 |
| total die area increase | 0.5 | % | Arria 10, node UNKNOWN (year 2015) | device without native fp32 DSP support | native fp32 support | p.23 |
errors_and_checks: IEEE subnormals, flags, and multiple rounding schemes are not supported. # p.23
conditions: Hardware reuse and reduced IEEE functionality constrain the area increase. # p.23
evidence: Section III-E; Fig. 15; pp.23-24.

### multiprecision_block_proposal  (role: compares)
mechanism: Academic DSP proposals fracture an Intel-like or Xilinx-like multiplier to add native low-precision MAC modes while preserving routing interfaces and legacy DSP functionality. Some proposals add FIFO/register storage and dedicated inter-block paths for convolution data reuse. # p.24
choices:
  fracture_to: 4 / 8  # p.24
  runtime_composable: false  # p.24
new_choices:
  dedicated_data_reuse: FIFO register file / inter-block interconnect — Local storage and links feed convolution operands without additional fabric routing.  # p.24
slots:
  multiplier: carry_save_array  # p.24
parameters: four int9 or eight int4 multiply/MAC operations per enhanced Intel-like block; Xilinx-like proposal supports int9/int4/int2.  # p.24
results:
| metric | value | unit | technology / device | baseline | condition | page |
| DSP block area increase | 12 | % | proposed Intel-like DSP (year 2018) | Arria-10-like functionality | int9/int4 support | p.24 |
| total die area increase | 0.6 | % | proposed Intel-like FPGA (year 2018) | FPGA without native int9/int4 modes | int9/int4 support | p.24 |
| accelerator performance improvement | 1.3 | × | proposed Intel-like FPGA (year 2018) | DSPs without native mode | 8-bit DL accelerator | p.24 |
| accelerator performance improvement | 1.6 | × | proposed Intel-like FPGA (year 2018) | DSPs without native mode | 4-bit DL accelerator | p.24 |
| utilized FPGA resources reduction | 15 | % | proposed Intel-like FPGA (year 2018) | DSPs without native mode | 8-bit DL accelerator | p.24 |
| utilized FPGA resources reduction | 30 | % | proposed Intel-like FPGA (year 2018) | DSPs without native mode | 4-bit DL accelerator | p.24 |
errors_and_checks: none
conditions: Low-precision gains depend on native DSP support rather than decomposition in soft logic. # p.24
evidence: Section III-E; p.24.

### ai_tensor_block  (role: instantiates)
mechanism: Stratix 10 NX replaces legacy DSP modes with arrays specialized for low-precision DL MACs and a double-buffered data-reuse register network. Speedster7t similarly couples its MLP block to BRAM and a circular register file to expand internal operand bandwidth beyond the external routing interface. # p.24
choices:
  element_format: int8 / int4 / fp16 / bfloat16 [outside domain] / int16 [outside domain] / int3 [outside domain] / fp24 [outside domain]  # pp.21,24
new_choices:
  macs_per_block: 30 int8 / 60 int4 — Concurrent MAC capacity of the Stratix 10 NX tensor block.  # p.24
  operand_reuse_network: double-buffered registers / BRAM plus circular register file — Local reuse reduces required routing ports.  # p.24
slots:
  none
parameters: 30 int8 or 60 int4 MACs per Stratix 10 NX block; Speedster7t internal output up to 144-bit from a 72-bit external input.  # p.24
results:
| metric | value | unit | technology / device | baseline | condition | page |
| routing-port reduction | 2 | × | Achronix Speedster7t (year 2019) | internal multiplier input width supplied directly from routing | tightly coupled memory-bank output expansion | p.24 |
errors_and_checks: none
conditions: Tensor specialization removes legacy communications-oriented DSP modes, so the block targets DL compute patterns specifically. # p.24
evidence: Section III-E; Fig. 15; p.24.

## new_families
none

## space_gaps
* `fpga_carry_chain` lacks a choice for hardened carry mechanism, including ripple/carry-skip/carry-lookahead, and arithmetic bits per logic element. # p.11
* `hard_fp_dsp` lacks a choice describing omitted IEEE features and supported rounding-mode subsets. # p.23
* `ai_tensor_block.element_format` lacks int3/int16/fp24 and uses `bf16` rather than the document’s `bfloat16`. # p.24
* DSP families lack a choice for local operand/coefficient storage and data-reuse networks. # pp.23-24

## open_questions
* Figure 15 labels one Stratix 10 NX format `Bfloat24`, while the prose calls the Speedster7t format `fp24`; the merge pass must not treat them as equivalent without another source.
* Technology nodes and result years are not stated for several cited adder and FIR comparisons.
* The article does not state whether later fp16/bfloat16 DSP modes preserve full fp32 accumulation or IEEE exception behavior.
