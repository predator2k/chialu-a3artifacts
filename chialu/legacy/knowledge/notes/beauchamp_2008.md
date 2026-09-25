---
handle: beauchamp_2008
citation: M. J. Beauchamp, S. Hauck, K. D. Underwood, K. S. Hemmert, "Architectural Modifications to Enhance the Floating-Point Performance of FPGAs", IEEE Transactions on Very Large Scale Integration (VLSI) Systems, 2008
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU, VEC_DOT_ACC]
formats: [fp32, fp64]
authority: incremental
pages_read: 12 / 12
---

## summary
The paper evaluates standalone double-precision floating-point units, embedded variable-length shifters, and dedicated 4:1 multiplexers beside FPGA LUTs (§I). The modifications reduce the area and increase the clock rate of five double-precision scientific benchmarks relative to an FPGA with embedded 18-bit x 18-bit multipliers (§VI).

## families
### barrel_mux_tree  (role: extends)
mechanism: The embedded block implements a variable-length shifter as a series of multiplexers. One block operates as one 64-bit shifter or two independent 32-bit shifters and supports logical/arithmetic shifts plus rotations. Integrated logic generates sticky bits for logical right shifts. Optional registers occur at the inputs and outputs. # §III.E
choices:
  sticky_collect: true   # §III.E
new_choices:
  word_configuration: {1x64, 2x32} — selects one double-precision datapath or two single-precision datapaths   # §III.E
  operation_modes: {shift_left_logical_arithmetic, rotate_left, shift_right_logical, shift_right_arithmetic, rotate_right} — selects the embedded block operation   # §III.E
slots:
  none
parameters: 32-bit or 64-bit datapath; maximum shifts of 24 bits for fp32 and 53 bits for fp64; 83 inputs; 66 outputs; 300 ps setup; 700 ps clock-to-q; 1.52 ns internal combinational delay; evaluated sizes of two/four/eight equivalent CLBs   # §III.E, §V.B
results:
| metric | value | unit | technology / device | baseline | condition | page |
| average clock-rate increase | 3.3 | % | modeled Virtex-II Pro / 2008 | EMBEDDED MULTIPLIER | five fp64 benchmarks | §VI.B |
| average area reduction | 14.6 | % | modeled Virtex-II Pro / 2008 | EMBEDDED MULTIPLIER | four-CLB shifter estimate | §VI.B |
| average track-count increase | 16.5 | % | modeled Virtex-II Pro / 2008 | EMBEDDED MULTIPLIER | average track count becomes 58 | §VI.B |
| fp64 adder CLB reduction | 31 | % | modeled Virtex-II Pro / 2008 | adder without embedded shifters | two embedded shifters | §VI.B |
| fp64 multiplier CLB reduction | 22 | % | modeled Virtex-II Pro / 2008 | multiplier without embedded shifters | two embedded shifters | §VI.B |
| laid-out shifter area | 0.843 10^6 | L2 | 130 nm / 2008 | none | excludes additional connection/routing area | §III.E |
errors_and_checks: Sticky-bit logic increases shifter size by less than 1%; sticky outputs are undefined except during logical right shifts. # §III.E
conditions: Only the floating-point operations were optimized, while control and the remainder of each datapath were unchanged. The two/four/eight-CLB size estimates differ by an average 3.7% in clock rate and 1.0% in area. # §V.B, §VI.B
evidence: §III.E; §V.B; §VI.B; Figs. 5 and 8–13

### fpga_mapped  (role: extends)
mechanism: Each CLB adds one 4:1 multiplexer in parallel with each 4-LUT. The multiplexer and LUT share four data inputs, while both multiplexers in a two-LUT CLB share the BX/BY select inputs. BX/BY cannot independently feed the flip-flops in mux mode, although the flip-flops remain drivable from the LUTs. # §III.F
choices:
  mapping: dedicated_4_to_1_mux_parallel_to_lut [outside domain]   # §III.F
new_choices:
  none
slots:
  none
parameters: two 4:1 multiplexers per CLB; shared select inputs; 253 ps multiplexer delay; 1.58 10^3 L2 area per multiplexer   # §III.F
results:
| metric | value | unit | technology / device | baseline | condition | page |
| average clock-rate increase | 11.6 | % | modeled Virtex-II Pro / 2008 | EMBEDDED MULTIPLIER | five fp64 benchmarks | §VI.C |
| average area reduction | 7.3 | % | modeled Virtex-II Pro / 2008 | EMBEDDED MULTIPLIER | five fp64 benchmarks | §VI.C |
| average track-count increase | 16.1 | % | modeled Virtex-II Pro / 2008 | EMBEDDED MULTIPLIER | average track count becomes 58 | §VI.C |
| fp64 adder area reduction | 17 | % | modeled Virtex-II Pro / 2008 | LUT implementation | floating-point core only | §VI.C |
| fp64 multiplier area reduction | 10 | % | modeled Virtex-II Pro / 2008 | LUT implementation | floating-point core only | §VI.C |
| 4-LUT delay increase | 1.83 | % | UNKNOWN / 2008 | unloaded 4-LUT | added 4:1-multiplexer load | §III.F |
| FPGA silicon-area increase | 0.35 | % | modeled Virtex-II Pro / 2008 | unmodified FPGA | two multiplexers per CLB | §VIII |
errors_and_checks: none
conditions: The modification avoids new CLB inputs and general-purpose routing changes, which forces both multiplexers to share select lines. Only the floating-point cores use the new multiplexers in the benchmarks. # §III.F, §VI.C
evidence: §III.F; §VI.C; §VIII; Figs. 6 and 11–13

### fpga_carry_chain  (role: analyzes)
mechanism: A dedicated vertical route connects each CLB carry-out to the carry-in of the CLB above without switch boxes or connection boxes. Each CLB handles two result bits and provides two points for entering or leaving the column-wide chain. VPR places and moves each connected carry chain as one constrained unit. # §III, §IV.B
choices:
new_choices:
  chain_extent: column_wide — the dedicated carry route runs from the bottom to the top of each CLB column   # §IV.B
slots:
  none
parameters: two output bits per CLB; upward-only vertical chain; fp64 addition uses a 57-bit adder   # §IV.B
results:
| metric | value | unit | technology / device | baseline | condition | page |
| average maximum frequency without chain | 85 | MHz | modeled Virtex-II Pro / 2008 | none | five benchmarks | §IV.B |
| average maximum frequency with chain | 128 | MHz | modeled Virtex-II Pro / 2008 | without fast carry-chain | five benchmarks | §IV.B |
| average speed increase | 49.7 | % | modeled Virtex-II Pro / 2008 | without fast carry-chain | five benchmarks | §IV.B |
errors_and_checks: none
conditions: General routing for the 57-bit adder carry would significantly reduce frequency and bias comparisons toward embedded floating-point units. # §IV.B
evidence: §III; §IV.B; Fig. 7; Table 4

## new_families
### embedded_floating_point_tile  (domain: dsp: FPGA DSP blocks, closest: hard_fp_dsp, why_not: hard_fp_dsp requires IEEE floating-point hardware inside a DSP block, while this paper replaces multiplier columns with standalone island-style FPU columns)
mechanism: A parameterizable island-style block performs fp64 multiplication, addition, or the operation X64-bit = (A64-bit * B64-bit) + C64-bit. The block has optional registered inputs/outputs and is placed in dedicated columns among CLBs/RAMs. The evaluated configuration uses blocks 32 CLBs high. Area is estimated from processor/core data and enlarged for connection blocks, while timing assumes 500 MHz at processor-like four-cycle addition and six-cycle multiplication latency. # §III.D, §V.A
choices: precision: {fp64, configurable_2xfp32}; operation_set: {multiply, add, multiply_add}; register_boundaries: {optional_input, optional_output}; tile_height_clbs: Int[4..160:1]
results:
| metric | value | unit | technology / device | baseline | condition | page |
| average clock-rate increase | 33.4 | % | modeled Virtex-II Pro / 2008 | EMBEDDED MULTIPLIER | five fp64 benchmarks | §VI.A |
| average area reduction | 54.2 | % | modeled Virtex-II Pro / 2008 | EMBEDDED MULTIPLIER | conservative FPU area estimate | §VI.A |
| average track-count reduction | 6.83 | % | modeled Virtex-II Pro / 2008 | EMBEDDED MULTIPLIER | five fp64 benchmarks | §VI.A |
| chip area occupied by FPUs | 17.6 | % | modeled Virtex-II Pro / 2008 | chosen height-32 configuration | non-floating-point applications may waste this area | §VI.A |
evidence: §III.D; §V.A; §VI.A; §VIII; Figs. 3 and 11–13; Table 1

## space_gaps
* `hard_fp_dsp.fp_format` lacks fp64, and the family does not represent a standalone island-style floating-point tile. # §III.D
* `fpga_mapped.mapping` lacks a dedicated 4:1 multiplexer placed parallel to each LUT. # §III.F
* `barrel_mux_tree` lacks fracturing into one 64-bit or two independent 32-bit shifters. # §III.E

## open_questions
* The detailed results report a 14.6% embedded-shifter area reduction, while the conclusion reports 14.3%. # §VI.B, §VIII
* The document calls the embedded operation multiply-add but does not state whether multiplication and addition use one rounding or two. # §III.D
* The document suggests configuring an fp64 FPU as two fp32 units but does not evaluate that configuration. # §VI.D
