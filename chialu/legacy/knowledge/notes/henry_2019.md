---
handle: henry_2019
citation: G. Henry, P. T. P. Tang, A. Heinecke, "Leveraging the bfloat16 Artificial Intelligence Datatype For Higher-Precision Computations", ARITH-26, pp. 69-76, 2019
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_DOT_ACC]
formats: [bf16, fp16, fp32, fp64]
authority: incremental
pages_read: pp.69-76 / 8 pages
---

## summary
The paper decomposes each FP32 operand into up to three BF16 components and evaluates FP32-like dot products/GEMMs using BF16 multiplication with FP32 accumulation. A six-product triplet construction approaches FP32 accuracy and has a projected speed-up of up to 5.2× when BF16 matrix throughput is sufficiently higher than FP32 throughput.

## families
### bf16_fma_datapath  (role: extends)
mechanism: A traditional FP32 FMA accepts BF16 operands interpreted as shortened FP32 values. The BF16 product is fully preserved before accumulation with 24-bit FP32 precision. Multiple invocations compute partial inner products between BF16 components of decomposed FP32 operands. # pp.69-71
choices:
  op_shape: scalar_fma   # p.69
  multi_word_composition: true   # pp.70-73
new_choices:
  none
slots:
  slot mul: behavioral_star   # p.69
parameters: BF16 has 8 exponent bits and 8 significant bits; accumulation uses FP32 with 24 significant bits; an FP32 value is represented by 1, 2, or 3 BF16 components. # pp.69-70
results:
| metric | value | unit | technology / device | baseline | condition | page |
| estimated multiplier area | 64 | area-units | UNKNOWN / 2019 | FP32 multiplier: 576 area-units | first-order significand-width-squared estimate | p.76 |
| estimated BF16 multiplier area reduction | roughly 10 | × smaller | UNKNOWN / 2019 | FP32 multiplier | first-order estimate | p.76 |
| projected BF16 compute density | 8-32 | × FP32 FLOPS | systolic-array hardware / 2019 | classic FP32 vector compute engine | suitable matrix computations | p.76 |
errors_and_checks: Each BF16 product is fully preserved by the FP32 accumulator. The paper specifies no hardware fault-detection mechanism. # p.69
conditions: Bare-metal programmable BF16 hardware was unavailable for measurement, so the hardware performance results are projections rather than measured BF16 timings. # pp.74,76
evidence: Fig. 1 and §I, pp.69-70; §V, pp.74,76.

## new_families
### low_precision_expansion_dot  (domain: dot, closest: multi_term_fused_dot, why_not: The partial inner products are separately accumulated and rounded in FP32 rather than flattened into one fused reduction with one final rounding.)
mechanism: Each FP32 operand is decomposed into an unevaluated sum of up to three BF16 values. Cross-products are grouped by significance into bins. One component uses one product, two components retain three products, and three components retain six products; the full triplet expansion has nine products. Retained bins are summed from smallest to largest, optionally collecting the final partial results in FP64. # pp.70-73
choices:
  component_count: Int[1..3:1]   # pp.70,73
  retained_cross_products: {1, 3, 6, 9}   # pp.70-73
  collection_precision: {fp32, fp64}   # pp.71,74-75
  bin_sum_order: {smallest_to_largest}   # pp.72-73
  operand_component_counts: {symmetric, asymmetric}   # p.73
results:
| metric | value | unit | technology / device | baseline | condition | page |
| projected speed-up | ≤ 1.3 | × | UNKNOWN / 2019 | FP32 dense linear algebra | BF16 density over FP32 = 8; six BF16 products | p.76 |
| projected speed-up | ≤ 2.7 | × | UNKNOWN / 2019 | FP32 dense linear algebra | BF16 density over FP32 = 16; six BF16 products | p.76 |
| projected speed-up | ≤ 5.2 | × | UNKNOWN / 2019 | FP32 dense linear algebra | BF16 density over FP32 = 32; six BF16 products | p.76 |
evidence: §II-A–G, pp.70-73; Figs. 2-5, pp.74-75; §V, p.76.

## space_gaps
* The dot vocabulary lacks a component slot for a mixed-precision FMA that multiplies BF16 operands and accumulates in FP32. # pp.69-71
* The dot vocabulary lacks choices for high-precision operand decomposition count, retained cross-product bins, and final collection precision. # pp.70-74

## open_questions
* Fig. 1 identifies the BF16 FMA externally but does not specify its multiplier/reduction/rounding microarchitecture. # p.69
* The six-product shortcut has no advance test guaranteeing FP32-comparable accuracy; strongly unequal operand magnitudes can require at least seven products. # pp.72-73
* Components can underflow for values near the FP32 lower exponent boundary; the paper suggests a working exponent range of [-110,127]. # p.72
* Figs. 2-5 provide plotted accuracy results without exact numeric values for every data point. # p.75
* The projected speed-ups assume that decomposition is hidden and that the low-precision matrix multiplications dominate execution time. # pp.74,76
