---
handle: camus2019
citation: V. Camus, L. Mei, C. Enz, M. Verhelst, "Review and Benchmarking of Precision-Scalable Multiply-Accumulate Unit Architectures for Embedded Neural-Network Processing", IEEE Journal on Emerging and Selected Topics in Circuits and Systems, vol. 9, no. 4, pp. 697-711, 2019
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_DOT_ACC]
formats: [int2, int4, int8]
authority: survey
pages_read: 697-711 / 15
---

## summary
The paper classifies precision-scalable neural-network MACs by spatial/temporal scaling, one-dimensional/two-dimensional operand scaling, and Sum Apart/Sum Together accumulation (pp.698-699). It implements the classes in a commercial 28 nm CMOS process and benchmarks energy, throughput, area, and bandwidth for 2-bit, 4-bit, and 8-bit operation (pp.702-709). SWP ST performs best across the studied symmetric-scaling use cases, while weight-only scaling provides smaller benefits (pp.709-710).

## families
### lane_width_gating  (role: compares)
mechanism: The conventional baseline zeroes unused LSBs while retaining the MSBs for computation. Reduced switching activity saves energy, and the shorter active path permits higher frequency or lower voltage, but all registers remain clocked because the baseline has no selective clock gating (p.699).
choices:
  detection: static_mode   # p.699
  gating: operand_isolation   # p.699
  operation_packing: false   # p.699
new_choices:
  none
slots:
  none
parameters: one 8b×8b, one 4b×4b, or one 2b×8b operation; two pipeline stages; 4b accumulation headroom   # pp.699,702
results:
| metric | value | unit | technology / device | baseline | condition | page |
| energy saving | 0% | normalized comparison baseline | 28 nm CMOS | data-gated conventional MAC | full-precision 8b×8b | p.705 |
errors_and_checks: Arithmetic results remain exact at the selected operand precision; network-accuracy effects are not measured.   # pp.697,702
conditions: The baseline has the best 8b throughput per area and energy efficiency because scalable interconnects add overhead (p.707). The baseline remains close to optimal when 8b operations constitute 33% of use (p.707).
evidence: Fig. 3; Sections III-A, IV-A, V-E, VI-A, VII-B.

### twin_precision_subword  (role: compares)
mechanism: A single 8b array multiplier selectively activates arithmetic cells for one 8b×8b, two 4b×4b, or four 2b×2b operations. SWP SA keeps subword products in separate accumulation registers. SWP ST activates an opposite diagonal pattern so array cells add the products into one result (pp.700-701).
choices:
  partition: quarters   # pp.700-701
  base_scheme: array_multiplier [outside domain]   # pp.700-701
new_choices:
  accumulation_mode: {sum_apart, sum_together} — selects separate subword outputs or one accumulated output   # pp.698,700-701
  scalability_levels: {1, 2} — selects direct support down to 4b or 2b   # pp.702-703
slots:
  lane_cpa: UNKNOWN   # pp.700-701
parameters: 8b×8b, 4b×4b, and 2b×2b; one/two scalability levels; two pipeline stages; II=1   # pp.700-703
results:
| metric | value | unit | technology / device | baseline | condition | page |
| area overhead | 10% | percent | 28 nm CMOS | conventional MAC | SWP ST, 1-level scalability | p.705 |
| area overhead | 18% | percent | 28 nm CMOS | conventional MAC | SWP ST, 2-level scalability | p.705 |
| energy saving | 68% | percent | 28 nm CMOS | data gating | SWP ST, 2-level, symmetric 2b scaling | p.707 |
| energy saving | 32% | percent | 28 nm CMOS | data gating | SWP ST, symmetric use case with 5% 8b operations | p.709 |
errors_and_checks: Arithmetic results remain exact at each selected precision; no circuit error checker is evaluated.   # pp.697,702
conditions: SWP ST keeps input bandwidth constant across precision modes but leaves some arithmetic logic unused (p.701). SWP designs provide only data-gating benefits for weight-only scaling (p.706). SWP SA duplicates accumulation headroom, while SWP ST requires one unpartitioned accumulator (pp.700,702).
evidence: Figs. 8-9, 15, 19, 24-25, 28-30; Sections III-F–G, V-D–F, VI, VII.

### serial_serial_parallel  (role: compares)
mechanism: One-dimensional serial MACs feed weights in one-bit or multibit groups while activations remain parallel. Two-dimensional serial MACs feed both operands serially and traverse every input-bit combination. Reduced precision decreases the number of iterations; multibit variants reduce clock/register energy by processing two or four bits per cycle (pp.701-702).
choices:
  serial_operands: {one, both}   # pp.701-702
  digit_size_bits: {1, 2, 4}   # pp.701-702
new_choices:
  partial_product_shift_schedule: {regular_right_shift, irregular_2d} — distinguishes 1D and 2D serial accumulation schedules   # pp.701-702
slots:
  none
parameters: 8b×8b, 4b×8b, 2b×8b, 4b×4b, and 2b×2b; cycles equal weight precision for 1D bit serial and the product of operand precisions for 2D bit serial   # pp.701-702
results:
| metric | value | unit | technology / device | baseline | condition | page |
| area saving | up to 40% | percent | 28 nm CMOS | conventional MAC | serial designs | p.705 |
| energy | 3.3× | baseline energy/op | 28 nm CMOS | data gating | 1D bit serial, full precision | p.705 |
| energy | 14× | baseline energy/op | 28 nm CMOS | data gating | 2D bit serial, full precision | p.705 |
| energy | 1.5× | baseline energy/op | 28 nm CMOS | data gating | 1D 4-bit serial, full precision | p.705 |
errors_and_checks: Arithmetic results remain exact at the selected precision; no circuit error checker is evaluated.   # pp.701-702
conditions: Serial MACs reduce bandwidth and area but lose throughput and spend more clock-tree energy over repeated cycles (pp.703,705). Only the 1D 4-bit serial design remains competitive in the 5%-full-precision study (pp.709-710).
evidence: Figs. 10-14, 19, 26-30; Sections III-H–I, V, VI, VII.

## new_families
### divide_and_conquer_precision_scalable_mac  (domain: dot: dot-product / FMA / MAC, closest: twin_precision_subword, why_not: twin_precision_subword requires one selectively gated partial-product matrix, while D&C composes independent submultipliers with configurable shift-add logic.)
mechanism: The multiplier combines identical 2b×8b or 2b×2b submultipliers through configurable shift-add logic. One-dimensional designs scale one operand; two-dimensional designs scale both. Sum Apart bypasses combination logic and stores parallel products separately, while Sum Together reuses combination adders to accumulate one result (pp.699-701).
choices: scalable_dimensions: {one, two}; accumulation_mode: {sum_apart, sum_together}; scalability_levels: Int[1..2:1]; submultiplier_shape: {2b×8b, 2b×2b}
results:
| metric | value | unit | technology / device | baseline | condition | page |
| area | up to 4.4× | baseline area | 28 nm CMOS | conventional MAC | 2D D&C | p.705 |
| throughput | 14.5× | baseline throughput | 28 nm CMOS | full-precision conventional MAC | 2D D&C SA, symmetric 2b scaling | p.705 |
| energy saving | 68% | percent | 28 nm CMOS | data gating | 2D D&C ST, 2-level symmetric 2b scaling | p.707 |
| energy saving | 15% | percent | 28 nm CMOS | data gating | 2-level 1D D&C ST, weight-only use case with 5% 8b operations | p.709 |
evidence: Table I; Figs. 4-7, 19-23, 28-30; pp.699-710.

## space_gaps
* `twin_precision_subword` lacks the paper's Sum Apart/Sum Together accumulation choice (pp.698-701).
* Precision-scalable MAC families lack the paper's one-dimensional/two-dimensional/two-dimensional-symmetric operand-scaling choice (p.699).
* The vocabulary lacks D&C composition from independent submultipliers and configurable shift-add logic (pp.699-701).

## open_questions
* The plotted points in Figs. 16-30 do not have complete numeric labels in the supplied document text, so unquoted graph coordinates remain UNKNOWN.
* The internal final-adder topologies of the benchmarked MACs are not specified.
