---
handle: christie_1996
citation: D. Christie, "Developing the AMD-K5 Architecture", IEEE Micro, vol. 16, no. 2, pp. 16-27, 1996.
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU, VEC_SFU]
formats: [x86_integer, x87]
authority: landmark
pages_read: pp.16-26 / 12 pages
---

## summary
The paper describes the AMD K5 microarchitecture and its development/verification process. The K5 integrates parallel floating-point add, multiply, and compare/move pipelines into an out-of-order core, and it implements transcendental operations with table-driven polynomial algorithms. The paper does not disclose the arithmetic recurrence, topology, precision, or rounding structure of those pipelines.

## families
### lut_plus_poly  (role: instantiates)
mechanism: The floating-point unit implements the x86 transcendental operations using table-driven polynomial algorithms. The floating-point team develops and verifies the operations hierarchically at successively lower abstraction levels; the paper refers elsewhere for the algorithm details. # p.18
choices:
new_choices:
  none
slots:
  none
parameters: function set includes x86 transcendental operations; degree, index bits, coefficient encoding, guard bits, breakpoints, multiplier shape, range reducer, evaluator, segmenter, latency, and II are UNKNOWN. # p.18
results:
| metric | value | unit | technology / device | baseline | condition | page |
|---|---:|---|---|---|---|---|
| reported comparative results | UNKNOWN | UNKNOWN | UNKNOWN; 1996 | UNKNOWN | No table-driven-polynomial implementation results are reported | p.18 |
errors_and_checks: The operations use a rigorous hierarchical development and verification process, but numerical accuracy/error bounds are UNKNOWN. # p.18
conditions: The mechanism applies to the complex transcendental operations required by the x86 floating-point architecture. # p.18
evidence: p.18, paragraph beginning “The pitfalls of floating-point verification.”

## new_families
### parallel_fp_pipeline_cluster  (domain: fp, closest: single_path, why_not: The existing fp families describe individual operation datapaths rather than a shared floating-point unit containing independent add/multiply/compare pipelines.)
mechanism: The floating-point unit contains parallel add, multiply, and compare/move pipelines. The unit shares the core register file, operand/result buses, and reorder buffer. Floating-point stack registers are mapped into the unified register file through a renaming table. Two 41-bit operand buses combine to carry each 82-bit internal floating-point operand, and a floating-point operation occupies two dispatch positions. # pp.20, 22, 24
choices: operation_pipelines: {add_multiply_compare_move}; core_integration: {shared_register_file_buses_reorder_buffer}; stack_mapping: {renaming_table}; operand_transport: {paired_half_width_buses}
results:
| metric | value | unit | technology / device | baseline | condition | page |
|---|---:|---|---|---|---|---|
| internal floating-point operand size | 82 | bits | UNKNOWN; 1996 | UNKNOWN | K5 execution core | p.24 |
| operand bus width | 41 | bits | UNKNOWN; 1996 | UNKNOWN | Two buses supply one floating-point operand | p.24 |
| floating-point reservation-station capacity | 1 | entry | UNKNOWN; 1996 | UNKNOWN | Other listed functional units have two entries | p.22 |
| floating-point dispatch limit | 1 | ROP per cycle | UNKNOWN; 1996 | Up to four total ROPs per cycle | p.22 |
evidence: Figure 1 and general-features list on p.20; execution-core description on p.22; “FPU integration and physical structure” on p.24.

## space_gaps
* The fp vocabulary lacks a family for a shared floating-point cluster with independent add/multiply/compare pipelines and common register-file/reorder-buffer integration. # pp.20, 24
* `lut_plus_poly` lacks a choice for the set of transcendental functions implemented by a shared table-driven polynomial unit. # p.18
* The vocabulary lacks a slot for the floating-point compare/move pipeline within an integrated floating-point cluster. # p.24

## open_questions
* The paper does not identify the adder, multiplier, comparator, divider, rounding, normalization, or subnormal-handling families used inside the floating-point unit.
* The paper states that formal verification was used for division but does not disclose the division algorithm, radix, latency, precision, or correctness contract. # p.18
* The paper does not specify whether the table-driven polynomial hardware is shared among functions or replicated. # p.18
* The cited page range ends at p.27, but the supplied document text contains readable article content only through p.26.
