---
handle: bhardwaj2014
citation: K. Bhardwaj, P. S. Mane, J. Henkel, "Power- and Area-Efficient Approximate Wallace Tree Multiplier for Error-Resilient Systems", 15th International Symposium on Quality Electronic Design (ISQED), pp. 263-269, 2014
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [uint4, uint8, uint16]
authority: incremental
pages_read: 263-269 / 7
---

## summary
The document proposes an accuracy-configurable Approximate Wallace Tree Multiplier that omits part of selected partial-product computations, forces an intermediate bit region to ones, and predicts the carry into the retained accurate region (pp.264-267). A bit-width-aware algorithm adjusts the approximation region for operand width and provides four accuracy modes (p.266). Synthesized 4×4/8×8/16×16 designs trade mean relative error for area/power/latency reductions (pp.267-269).

## families
none

## new_families
### bit_width_aware_wallace_tree  (domain: approx: approximate multipliers, closest: pp_perforation, why_not: pp_perforation removes rows or substitutes 2×2 cells, whereas AWTM omits an internal bit-band of selected recursive partial products, forces output bits, and injects a predicted carry)
mechanism: A 2b×2b product is decomposed into AHXH/AHXL/ALXH/ALXL. AHXH remains accurate, while the other three products compute b/2 low bits, force the next b/2 bits to one, and accurately compute the remaining terms using a predicted carry from the maximum-height partial-product column (pp.264-265). AHXH is recursively decomposed into four b/2×b/2 multipliers, and Wallace reduction shortens the approximate paths (pp.265-267). Four modes vary which AHXH submultipliers are accurate, while AHHXHH remains accurate (p.266).
choices:
  operand_width_awareness: Bool   # p.266
  approximate_partial_product_set: {AHXL_ALXH_ALXL}   # p.264
  inaccurate_band_width: {b_over_2}   # pp.265-266
  inaccurate_band_value: {all_ones}   # p.265
  carry_prediction: {two_or_more_threshold, simplified_or}   # p.265
  accuracy_modes: Int[1..4:1]   # p.266
  reduction_tree: {wallace}   # p.267
  implementation_timing: {two_stage_pipelined, single_cycle}   # pp.266,268
results:
| metric | value | unit | technology / device | baseline | condition | page |
| mean error | 5.26 | % | UNKNOWN node / 2014 | exact product | mode 1; operands >1; 5000-random-number C simulation | p.267 |
| acceptance probability | 27.34 | % | UNKNOWN node / 2014 | MAA=99% | mode 1; operands >1 | p.267 |
| mean error | 4.59 | % | UNKNOWN node / 2014 | exact product | mode 1; operands >1000 | p.267 |
| acceptance probability | 28.18 | % | UNKNOWN node / 2014 | MAA=99% | mode 1; operands >1000 | p.267 |
| mean error | 3.42 | % | UNKNOWN node / 2014 | exact product | mode 2; operands >1 | p.267 |
| acceptance probability | 46.18 | % | UNKNOWN node / 2014 | MAA=99% | mode 2; operands >1 | p.267 |
| mean error | 3.16 | % | UNKNOWN node / 2014 | exact product | mode 2; operands >1000 | p.267 |
| acceptance probability | 46.04 | % | UNKNOWN node / 2014 | MAA=99% | mode 2; operands >1000 | p.267 |
| mean error | 0.46 | % | UNKNOWN node / 2014 | exact product | mode 3; operands >1 | p.267 |
| acceptance probability | 91.58 | % | UNKNOWN node / 2014 | MAA=99% | mode 3; operands >1 | p.267 |
| mean error | 0.29 | % | UNKNOWN node / 2014 | exact product | mode 3; operands >1000 | p.267 |
| acceptance probability | 94.28 | % | UNKNOWN node / 2014 | MAA=99% | mode 3; operands >1000 | p.267 |
| mean error | 0.13 | % | UNKNOWN node / 2014 | exact product | mode 4; operands >1 | p.267 |
| acceptance probability | 98.44 | % | UNKNOWN node / 2014 | MAA=99% | mode 4; operands >1 | p.267 |
| mean error | 0.035 | % | UNKNOWN node / 2014 | exact product | mode 4; operands >1000 | p.267 |
| acceptance probability | 99.72 | % | UNKNOWN node / 2014 | MAA=99% | mode 4; operands >1000 | p.267 |
| area reduction | 34.49 | % reduction | 45nm Nangate Opencell Library / 2014 | accurate 16×16 multiplier | mode 1 | p.268 |
| leakage-power reduction | 34.06 | % reduction | 45nm Nangate Opencell Library / 2014 | accurate 16×16 multiplier | mode 1 | p.268 |
| dynamic-power reduction | 43.4 | % reduction | 45nm Nangate Opencell Library / 2014 | accurate 16×16 multiplier | mode 1 | p.268 |
| total-power reduction | 41.96 | % reduction | 45nm Nangate Opencell Library / 2014 | accurate 16×16 multiplier | mode 1 | p.268 |
| area reduction | 31.91 | % reduction | 45nm Nangate Opencell Library / 2014 | accurate 16×16 multiplier | mode 2 | p.268 |
| leakage-power reduction | 32.52 | % reduction | 45nm Nangate Opencell Library / 2014 | accurate 16×16 multiplier | mode 2 | p.268 |
| dynamic-power reduction | 41.46 | % reduction | 45nm Nangate Opencell Library / 2014 | accurate 16×16 multiplier | mode 2 | p.268 |
| total-power reduction | 40.63 | % reduction | 45nm Nangate Opencell Library / 2014 | accurate 16×16 multiplier | mode 2 | p.268 |
| area reduction | 29.89 | % reduction | 45nm Nangate Opencell Library / 2014 | accurate 16×16 multiplier | mode 3 | p.268 |
| leakage-power reduction | 30.97 | % reduction | 45nm Nangate Opencell Library / 2014 | accurate 16×16 multiplier | mode 3 | p.268 |
| dynamic-power reduction | 39.68 | % reduction | 45nm Nangate Opencell Library / 2014 | accurate 16×16 multiplier | mode 3 | p.268 |
| total-power reduction | 38.86 | % reduction | 45nm Nangate Opencell Library / 2014 | accurate 16×16 multiplier | mode 3 | p.268 |
| area reduction | 27.90 | % reduction | 45nm Nangate Opencell Library / 2014 | accurate 16×16 multiplier | mode 4 | p.268 |
| leakage-power reduction | 29.43 | % reduction | 45nm Nangate Opencell Library / 2014 | accurate 16×16 multiplier | mode 4 | p.268 |
| dynamic-power reduction | 37.90 | % reduction | 45nm Nangate Opencell Library / 2014 | accurate 16×16 multiplier | mode 4 | p.268 |
| total-power reduction | 37.10 | % reduction | 45nm Nangate Opencell Library / 2014 | accurate 16×16 multiplier | mode 4 | p.268 |
| area reduction | 55.76 | % reduction | 45nm Nangate Opencell Library / 2014 | accurate 4×4 multiplier | AWTM configuration unspecified | p.268 |
| total-power reduction | 53.16 | % reduction | 45nm Nangate Opencell Library / 2014 | accurate 4×4 multiplier | AWTM configuration unspecified | p.268 |
| area reduction | 51.93 | % reduction | 45nm Nangate Opencell Library / 2014 | accurate 8×8 multiplier | AWTM configuration unspecified | p.268 |
| total-power reduction | 57.19 | % reduction | 45nm Nangate Opencell Library / 2014 | accurate 8×8 multiplier | AWTM configuration unspecified | p.268 |
| latency reduction | 23.91 | % reduction | 45nm Nangate Opencell Library / 2014 | accurate 16×16 multiplier | single-cycle implementation | p.268 |
| latency reduction | 32 | % reduction | 45nm Nangate Opencell Library / 2014 | accurate 8×8 multiplier | single-cycle implementation | p.268 |
| power reduction | 39 | % reduction | 45nm Nangate Opencell Library / 2014 | accurate multiplier | DCT/iDCT benchmark; negligible image-quality loss | p.269 |
| area reduction | 30 | % reduction | 45nm Nangate Opencell Library / 2014 | accurate multiplier | DCT/iDCT benchmark; negligible image-quality loss | p.269 |
evidence: Fig.1 and §IV define recursive decomposition (p.264); Figs.2-3 define the inaccurate band/carry prediction (p.265); Fig.4/Table I/Algorithm 1 define pipeline modes and bit-width awareness (p.266); Fig.5/Table II define Wallace reduction and accuracy results (p.267); Tables III-IV define synthesis results (p.268); Fig.10 defines the image experiment (p.269).

## space_gaps
* The approximate-multiplier vocabulary lacks internal partial-product-band omission with forced-one substitution and predicted carry injection (p.265).
* The approximate-multiplier vocabulary lacks recursive-submultiplier accuracy modes with one always-accurate anchor multiplier (p.266).
* The vocabulary lacks a Wallace/carry-save reduction-tree family that can fill multiplier reduction slots without implying approximate compressor cells (p.267).

## open_questions
* Table III does not identify the accuracy mode used for its 4×4/8×8/16×16 AWTM reductions (p.268).
* The paper describes run-time bit-width configuration but does not specify operand-width detection/control hardware, and the synthesized HDL omits bit-width awareness (pp.266-267).
* The DCT/iDCT experiment does not specify the floating-point format or the exact substitution boundary for the unsigned AWTM (p.269).
