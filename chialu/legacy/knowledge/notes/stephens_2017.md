---
handle: stephens_2017
citation: N. Stephens et al., "The ARM Scalable Vector Extension", IEEE Micro, vol. 37, no. 2, pp. 26-39, 2017
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU, VEC_DOT_ACC]
formats: [int8, int16, int32, int64, fp16, fp32, fp64]
authority: landmark
pages_read: 8 / 8
---

## summary
The paper presents SVE, a vector-length-agnostic ARM architecture with implementation-selected vector lengths, per-lane predication, predicate-driven loop control, horizontal operations, and speculative first-fault loads. SVE improves auto-vectorization and lets one executable scale across vector lengths from 128 to 2048 bits. # p.1–8

## families
### vector_lane_masking  (role: extends)
mechanism: Sixteen scalable predicate registers control vector memory/arithmetic operations at per-byte granularity, with the applicable enable bit selected by element size. Predicate-generating instructions create loop masks from scalar bounds, partition masks around dynamic exits, and masks describing successfully completed first-fault loads. Predicated operations support merging and zeroing behavior. # p.2–6
choices:
  mask_storage: predicate_regfile   # p.2–3
  masked_write: merge_preserve_old | zero_inactive [outside domain]   # p.2, p.6
new_choices:
  predicate_granularity: per_byte_with_element_size_selection — Each predicate provides eight enable bits per 64-bit vector element, with one bit used for each active element at the selected size.   # p.3
  predicate_partitioning: before_break_and_nested_subpartitions — Predicate operations form ordered partitions for dynamic exits and nested conditions.   # p.4–5
slots:
  none
parameters: 16 predicate registers P0–P15; governing predicates for general memory/arithmetic restricted to P0–P7; 8 enable bits per 64-bit vector element; supports 8-, 16-, 32-, and 64-bit elements   # p.2–3
results: none
errors_and_checks: First-fault loads trap on a fault from the first active element, suppress faults from later active elements, and clear corresponding FFR positions so successful elements can be identified and later accesses retried.   # p.4
conditions: Predicate-driven loop control removes the vector induction-register overhead described for comparison-based mask generation. Vector partitioning permits speculative vectorization only when side effects after a dynamic exit are prevented by the governing predicates and first-fault mechanism.   # p.3–5
evidence: §2.3, Table 1, Figures 4–6, §3.2, §3.4, p.2–6

## new_families
### scalable_vector_length_agnostic  (domain: shift: sub-word SIMD, closest: vector_lane_masking, why_not: vector_lane_masking describes lane commitment, while SVE's defining mechanism also makes vector length an implementation choice and exposes that length implicitly to portable binaries.)
mechanism: SVE defines thirty-two scalable vector registers whose implementation-dependent length is any multiple of 128 bits from 128 through 2048 bits. Instructions use the current vector length implicitly for induction, partitioning, register-stack addressing, and loop progress, so one binary runs across implementations without recompilation. The architecture supports fixed-length sub-vectors alongside vector-length-agnostic code and overlays the scalable vector state on the existing SIMD/floating-point register file. # p.1–2, p.5–6
choices:
  vector_length_bits: Int[128..2048:128]   # p.1–2
  programming_model: {vector_length_agnostic, fixed_length_subvectors, both}   # p.2
  register_file_integration: {overlay_existing_simd_fp, separate}   # p.6
  loop_progress_source: {implicit_current_vector_length, explicit_fixed_length}   # p.5–6
results:
| metric | value | unit | technology / device | baseline | condition | page |
| speedup | up to 3× | speedup | UNKNOWN node; representative modeled medium-sized out-of-order microprocessor (2017) | Advanced SIMD | SVE and Advanced SIMD use the same 128-bit vector length; improvement comes from greater vectorization coverage | p.7–8 |
| speedup | up to 7× | speedup | UNKNOWN node; representative modeled medium-sized out-of-order microprocessor (2017) | Advanced SIMD | selected benchmarks with SVE vector lengths of 128, 256, and 512 bits | p.7–8 |
evidence: §2.2, Figure 3, §3.1, §4, Table 2, Figure 8, §5, p.1–8

## space_gaps
* `vector_lane_masking.masked_write` needs a value representing architectures that support both merging and zeroing predication. # p.2, p.6
* The vocabulary lacks first-fault predicate state and ordered predicate partitioning for speculative vector memory operations with dynamic exits. # p.4–5
* The sub-word SIMD vocabulary lacks implementation-selected vector length and a vector-length-agnostic programming model. # p.1–2
* The sub-word SIMD vocabulary lacks horizontal integer/logical/floating-point reductions, including strictly ordered floating-point reduction. # p.5–6

## open_questions
* The paper does not specify the lane-level arithmetic-unit topology, carry-chain design, physical predicate implementation, or whether inactive lanes are clock-gated.
* Figure 8 does not print per-benchmark numeric values, so only the textual maxima of up to 3× and up to 7× are extractable. # p.7–8
