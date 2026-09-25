---
handle: perri_2004
citation: S. Perri, P. Corsonello, M. A. Iachino, M. Lanuzza, G. Cocorullo, "Variable Precision Arithmetic Circuits for FPGA-Based Multimedia Processors", IEEE Transactions on VLSI Systems, vol. 12, no. 9, pp. 995-999, 2004
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [int8, int16, int32]
authority: incremental
pages_read: 995-999 / 5
---

## summary
The paper proposes three FPGA multiplier architectures that select 32-, 16-, or 8-bit signed/unsigned SIMD operations at instruction level without FPGA reconfiguration. The architectures trade maximum-precision throughput, low-precision parallelism, power, and slice count through different arrangements of generated multiplier macros and carry-propagate adders. (pp.995-998)

## families
none

## new_families
### runtime_composed_subword_multiplier  (domain: mul: integer multipliers, closest: twin_precision_subword, why_not: The architectures compose several generated multiplier macros through extensions, shifts, multiplexers, and CPAs rather than partitioning one gated partial-product matrix.)
mechanism: A control unit selects precision and signedness and routes extended operand subwords into CBPxS multiplier macros. Shifted or extended macro outputs are combined by 48- and 64-bit carry-propagate adders for wide products, while lower-precision products bypass unneeded adders and appear as independent SIMD results. NVM3229 uses four 32x9 macros; NVM32217 uses two 32x17 macros; NVM16217 uses two 16x17 macros and takes two cycles for a 32x32 product. (pp.996-998)
choices:
  macro_partition: {four_32x9_CBPxS, two_32x17_CBPxS, two_16x17_CBPxS} — generated multiplier-macro arrangement (pp.997-998)
  operand_signedness: {signed_signed, signed_unsigned, unsigned_unsigned} — supported operand interpretations (p.997)
  precision_selection: {instruction_level_control} — precision changes through control signals without bit-stream reconfiguration (pp.995, 997)
  partial_result_merge: {shift_extend_cpa} — wide products are assembled through shifts/extensions and CPAs (pp.996-998)
  lower_precision_bypass: {enabled} — low-precision results bypass unneeded CPA stages (p.998)
  inactive_multiplier_control: {stop_and_force_zero} — unused NVM3229 multipliers are stopped and their outputs forced to zero (p.998)
  pipeline_configuration: {two_stage, maximum_core_pipeline} — the proposed pipeline and the additionally characterized maximum-pipelining variant (pp.997-998)
parameters: NVM3229 supports one 32x32, one 32x16, two 16x16, or four 8x8 operations; NVM32217 and NVM16217 support one 32x32, one 32x16, two 16x16, or two 8x8 operations; output width is 64 bits; NVM16217 requires two cycles for 32x32; the maximum-pipelined NVM3229 has 6-8 cycles of latency across 8x8, 16x16, and 32x32 modes. (pp.997-998)
results:
| metric | value | unit | technology / device | baseline | condition | page |
| MOPS increase | ~434% | percent | XILINX VIRTEX XCV400; 2004 | conventional 32x32 fixed-precision core-generated multiplier, minimum pipelining | NVM3229 at lowest precision | p.998 |
| MOPS increase | ~84% | percent | XILINX VIRTEX XCV400; 2004 | conventional 32x32 fixed-precision core-generated multiplier, maximum pipelining | NVM3229 at lowest precision | p.998 |
| running frequency | >110 | MHz | XILINX VIRTEX XCV400; 2004 | none | maximum-pipelined NVM3229 | p.998 |
| latency | 6-8 | clock cycles | XILINX VIRTEX XCV400; 2004 | none | maximum-pipelined NVM3229 across 8x8, 16x16, and 32x32 modes | p.998 |
| 32x32 performance reduction | ~46.3% | percent | XILINX VIRTEX XCV400; 2004 | conventional 32x32 fixed-precision multiplier, minimum pipelining | NVM16217, which needs two cycles for 32x32 | p.998 |
| power reduction | ~19% | percent | XILINX VIRTEX XCV400; 2004 | NVM3229 | NVM32217 | p.998 |
| slice reduction | ~17% | percent | XILINX VIRTEX XCV400; 2004 | NVM3229 | NVM32217 | p.998 |
| running frequency | well over 160 | MHz | XILINX VIRTEX II; 2004 | none | NVM3229 retargeted to a more recent FPGA family | p.998 |
errors_and_checks: The circuits compute full-width signed-signed, signed-unsigned, and unsigned-unsigned products; no approximation, fault model, or error-detection result is reported. (pp.997-998)
conditions: NVM3229 is the fastest proposed architecture and provides four-way 8x8 parallelism. NVM16217 is the cheapest architecture but sacrifices 32x32 throughput because the operation takes two cycles. NVM32217 doubles lower-precision throughput while maintaining 32x32 performance and uses less power and fewer slices than NVM3229. Placement constraints are required to exploit the target FPGA's logic/routing resources, and the fixed 64-bit output register prevents NVM3229 from retaining two simultaneous 32x16 results. (p.998)
evidence: §III, equations (1)-(3), Fig. 1, Table I, §IV, Table II, and §V (pp.996-998)

## space_gaps
* The multiplier vocabulary lacks a family for runtime composition of several heterogeneous-width FPGA multiplier macros into SIMD lanes through shift/extend/CPA merging. (pp.996-998)
* The proposed family needs choices for instruction-level precision selection, supported signedness combinations, low-precision CPA bypass, and disabling unused multiplier macros. (pp.997-998)
* `twin_precision_subword.partition` lacks the 32/16/8 three-precision operating set and four-way 8-bit mode reported by NVM3229. (pp.997-998)

## open_questions
* The numeric cells of Table II are absent from the supplied document text, so its absolute slice, power, frequency, and MOPS values cannot be extracted. (p.998)
* The statement giving 6-8 latency cycles does not assign an exact cycle count to each of the 8x8, 16x16, and 32x32 modes. (p.998)
* The internal arithmetic architecture of the automatically generated CBPxS multiplier macros is not specified. (p.997)
