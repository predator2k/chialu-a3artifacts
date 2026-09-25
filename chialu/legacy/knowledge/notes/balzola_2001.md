---
handle: balzola_2001
citation: P. I. Balzola, M. J. Schulte, J. Ruan, C. J. Glossner, E. Hokenek, "Design Alternatives for Parallel Saturating Multioperand Adders", Proc. IEEE ICCD, pp. 172-177, 2001
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU, VEC_DOT_ACC]
formats: [int32]
authority: incremental
pages_read: 6 / 6
---

## summary
The paper presents four parallel saturating multioperand adders that reproduce serial intermediate-saturation semantics with at most one carry-propagate adder on the critical path. The designs trade feedback representation/internal pipelining against area, worst-case delay, and dot-product latency.

## families
### saturating_clamp  (role: proposes)
mechanism: The adders compute candidate temporary sums in parallel while sign detection circuits, overflow detection logic, saturation-value generators, carry-save adders, and multiplexers determine the last addition that overflows. An n-bit multiplexer selects the corresponding saturated temporary sum. Designs 1 and 2 are unpipelined; Designs 3 and 4 precompute feedback-independent values in a first pipeline stage. Designs 1 and 3 use two’s-complement feedback, while Designs 2 and 4 retain carry-save feedback. All four designs preserve the result of serial addition with saturation after every addition. (pp.173-176)
choices:
  detect: msb_sign_analysis   # pp.173-176
  clamp: result_mux   # pp.173-176
  per_lane: false   # pp.172-177
new_choices:
  feedback_format: {twos_complement, carry_save} — representation of the accumulator/feedback operand and temporary sums   # pp.173-176
  internal_pipeline_registers: Bool — whether feedback-independent intermediate values are precomputed in a first pipeline stage   # pp.175-176
  overflow_logic: {distributed_sdc_odl, pipelined_odc} — distributed sign/overflow circuits or an optimized overflow detection circuit   # pp.173-176
slots: none
parameters: (m+1)-input SMA; evaluated with m=4 and n=32; five inputs comprise four products and one feedback operand; at most one CPA on the critical path; m new products accepted per cycle in the pipelined arithmetic unit   # pp.172-176
results:
| metric | value | unit | technology / device | baseline | condition | page |
| area, serial SMA | 2624 | gates | LSI Logic 0.6 micron LCA300K gate array; 2001 | none | 5-input, n=32, 3.3 Volts, 25° C, Leonardo synthesis | p.177 |
| delay, serial SMA | 28.46 | ns | LSI Logic 0.6 micron LCA300K gate array; 2001 | none | 5-input, n=32, 3.3 Volts, 25° C, Leonardo synthesis | p.177 |
| area, Design 1 SMA-WTCF | 10873 | gates | LSI Logic 0.6 micron LCA300K gate array; 2001 | serial SMA | 5-input, n=32, 3.3 Volts, 25° C, Leonardo synthesis | p.177 |
| delay, Design 1 SMA-WTCF | 12.08 | ns | LSI Logic 0.6 micron LCA300K gate array; 2001 | serial SMA | 5-input, n=32, 3.3 Volts, 25° C, Leonardo synthesis | p.177 |
| area, Design 2 SMA-WCSF | 11460 | gates | LSI Logic 0.6 micron LCA300K gate array; 2001 | serial SMA | 5-input, n=32, 3.3 Volts, 25° C, Leonardo synthesis | p.177 |
| delay, Design 2 SMA-WCSF | 10.24 | ns | LSI Logic 0.6 micron LCA300K gate array; 2001 | serial SMA | 5-input, n=32, 3.3 Volts, 25° C, Leonardo synthesis | p.177 |
| area, Design 3 PSMA-WTCF | 15112 | gates | LSI Logic 0.6 micron LCA300K gate array; 2001 | serial SMA | 5-input, n=32, 3.3 Volts, 25° C, Leonardo synthesis | p.177 |
| delay, Design 3 PSMA-WTCF | 8.10 | ns | LSI Logic 0.6 micron LCA300K gate array; 2001 | serial SMA | 5-input, n=32, 3.3 Volts, 25° C, Leonardo synthesis | p.177 |
| area, Design 4 PSMA-WCSF | 18774 | gates | LSI Logic 0.6 micron LCA300K gate array; 2001 | serial SMA | 5-input, n=32, 3.3 Volts, 25° C, Leonardo synthesis | p.177 |
| delay, Design 4 PSMA-WCSF | 8.68 | ns | LSI Logic 0.6 micron LCA300K gate array; 2001 | serial SMA | 5-input, n=32, 3.3 Volts, 25° C, Leonardo synthesis | p.177 |
| parallel-design area increase | 4.14 to 7.14 | times more area | LSI Logic 0.6 micron LCA300K gate array; 2001 | serial SMA | four 5-input parallel SMAs | p.177 |
| parallel-design delay reduction | 2.36 to 3.51 | times less worst-case delay | LSI Logic 0.6 micron LCA300K gate array; 2001 | serial SMA | four 5-input parallel SMAs | p.177 |
errors_and_checks: The arithmetic result is identical to serial additions with saturation after every addition, which supplies GSM bit-for-bit compatibility; no fault model or concurrent error checker is reported.   # pp.172,177
conditions: Saturating addition is nonassociative, so ordinary reordering can change results. (p.172) The designs target loops containing saturating dot products, including GSM speech coders. (pp.172,177) Design 1 has the least synthesized area, while Design 3 has the least synthesized delay. (p.177) Carry-save feedback adds a cycle for final two’s-complement conversion. (pp.174,176) The reported critical paths depend on m=4, n=32, and the Section 4 implementation. (pp.174-176)
evidence: §1; §3.1-3.4; Figures 3-7; §4; Table 1

### carry_save_datapath  (role: instantiates)
mechanism: Designs 2 and 4 retain the accumulator and temporary sums as n-bit sum/carry vectors. Three-input carry-save adders produce two outputs after one full-adder delay, while sign detection circuits replace CPAs where only temporary-result signs are needed. A CPA converts the carry-save feedback result to two’s complement after the saturated dot product completes. (pp.173-176)
choices:
  compressor: 3_2   # p.173
  assimilation_point: end_of_chain   # pp.174,176
  accumulator_redundant: true   # pp.173-176
new_choices: none
slots:
  assimilator: carry_lookahead   # p.177
parameters: n-bit sum vector plus n-bit carry vector; evaluated at n=32 and m=4; final conversion adds one cycle   # pp.174,176
results:
| metric | value | unit | technology / device | baseline | condition | page |
| area, Design 2 SMA-WCSF | 11460 | gates | LSI Logic 0.6 micron LCA300K gate array; 2001 | Design 1 SMA-WTCF | 5-input, n=32, 3.3 Volts, 25° C | p.177 |
| delay, Design 2 SMA-WCSF | 10.24 | ns | LSI Logic 0.6 micron LCA300K gate array; 2001 | Design 1 SMA-WTCF | 5-input, n=32, 3.3 Volts, 25° C | p.177 |
| area, Design 4 PSMA-WCSF | 18774 | gates | LSI Logic 0.6 micron LCA300K gate array; 2001 | Design 3 PSMA-WTCF | 5-input, n=32, 3.3 Volts, 25° C | p.177 |
| delay, Design 4 PSMA-WCSF | 8.68 | ns | LSI Logic 0.6 micron LCA300K gate array; 2001 | Design 3 PSMA-WTCF | 5-input, n=32, 3.3 Volts, 25° C | p.177 |
errors_and_checks: Exact serial intermediate-saturation semantics are preserved; no fault-detection contract is reported.   # pp.172-177
conditions: Carry-save feedback reduces the unpipelined critical path but increases area and dot-product latency. (p.174) Design 4 is slightly slower than Design 3 in the reported implementation because its overflow signals drive larger multiplexers with greater fan-out. (pp.176-177)
evidence: §3.2; Figure 4; §3.4; Figure 7; §4; Table 1

## new_families
none

## space_gaps
* saturating_clamp lacks choices for feedback representation and internal pipelining, which define the four reported design alternatives.   # pp.173-176
* saturating_clamp lacks a slot for the carry-propagate adder used in temporary-sum generation or final carry-save assimilation.   # pp.173-177

## open_questions
* The paper reports int32 synthesis results but presents the architecture parametrically as n-bit, so other supported operand widths are not fixed.
