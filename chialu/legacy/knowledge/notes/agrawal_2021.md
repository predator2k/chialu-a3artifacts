---
handle: agrawal_2021
citation: A. Agrawal, S. K. Lee, J. Silberman, et al., "A 7nm 4-Core AI Chip with 25.6TFLOPS Hybrid FP8 Training, 102.4TOPS INT4 Inference and Workload-Aware Throttling", IEEE ISSCC, 2021
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_DOT_ACC]
formats: [DLFloat16, hfp8, fp9, fp32, int16, int4, int2]
authority: incremental
pages_read: pp.144-146 / 3
---

## summary
The document presents a 7nm EUV four-core AI chip with separate mixed-precision training and integer-inference pipelines (p.144). The training pipeline executes an hfp8 fused-multiply-multiply-accumulate operation and accumulates product terms in fp16 (p.144). The inference pipeline performs int4/int2 multiply-accumulate operations with int16 addends/results (p.144).

## families
### fp8_training_datapath  (role: instantiates)
mechanism: Each Mixed Precision Engine contains a 128b training datapath with separate fp16 and hfp8 multiplicand paths. The 8-way SIMD FPUs execute an hfp8 fused-multiply-multiply-accumulate instruction comprising two multiplications and two additions. Incoming hfp8 operands are converted to a unified fp9 format. Product terms are aligned to the larger product exponent and accumulated in fp16. The fp16/hfp8 paths merge at the adder. The unused multiplicand path is clock gated, and zero multiplicands bypass the entire FPU pipeline.
choices:
  format_policy: distinct forward/backward hfp8 formats [outside domain]   # p.144
  accumulate_precision: fp16   # p.144
new_choices:
  internal_operand_format: fp9 with 5b exponent and 3b fraction — unified representation used by the hfp8 circuit   # p.144
  zero_multiplicand_bypass: entire FPU pipeline — the addend passes directly to the result   # p.144
slots:
  none
parameters: 128b datapath; 8-way SIMD FPUs; two multiplications and two additions per hfp8 FMMA; 4b multipliers in the hfp8 multiplicand path   # p.144
results:
| metric | value | unit | technology / device | baseline | condition | page |
| fp8 throughput | 25.6 | TFLOPS | 7nm EUV, 2021 | none | 0.75V core / 0.95V SRAM | p.144 |
| fp8 power efficiency | 3.5 | TFLOPS/W | 7nm EUV, 2021 | none | nominal 0.55V core / 0.7V SRAM | p.144 |
| hfp8 performance | 2 | × | 7nm EUV, 2021 | fp16 mode | same power | p.144 |
| zero-skipping power-performance gain | 20 | % | 7nm EUV, 2021 | zero-skipping disabled | fp16 mode at 50% activation sparsity | p.144 |
errors_and_checks: The chip maintains model accuracy equivalent to single-precision computation, but the document reports no arithmetic error/ulp bound (p.144).
conditions: Different hfp8 formats serve forward/backward passes to preserve model accuracy (p.144). The fp16/hfp8 compute paths share the adder because both produce fp16 results (p.144). The unused multiplicand path is clock gated, and zero multiplicands bypass computation (p.144).
evidence: p.144 training-engine description; Fig. 9.1.2, p.145; Figs. 9.1.6-9.1.7, pp.145-146

### integer_mac  (role: instantiates)
mechanism: Each Mixed Precision Engine contains a decoupled inference engine for int4/int2 multiply-accumulate operations with int16 addends/results. The inference engine uses a 256b datapath with eight-way SIMD fixed-point units, each containing an eight-way int4 multiply-accumulate pipeline. The decoupled implementation uses shorter wires, fewer latch stages, and simpler operand multiplexers than extending the training FPU pipeline.
choices:
  array_style: simd_packed_dot   # p.144
  accumulator_width_bits: 16   # p.144
new_choices:
  element_precision_modes: int4, int2 — int2 mode doubles throughput relative to int4   # p.144
slots:
  none
parameters: 256b datapath; 8-way SIMD fixed-point units; 8-way int4 multiply-accumulate pipeline per unit; int16 addends/results   # p.144
results:
| metric | value | unit | technology / device | baseline | condition | page |
| int4 throughput | 102.4 | TOPS | 7nm EUV, 2021 | none | 0.75V core / 0.95V SRAM | p.144 |
| int4 power efficiency | 16.5 | TOPS/W | 7nm EUV, 2021 | none | nominal 0.55V core / 0.7V SRAM | p.144 |
| area overhead | ~16 | % | 7nm EUV, 2021 | training FPU augmented with integer instructions | decoupled inference engine | p.144 |
| power-efficiency improvement | ~2 | × | 7nm EUV, 2021 | training FPU augmented with integer instructions | decoupled inference engine | p.144 |
| integer-engine count | 2 | × | 7nm EUV, 2021 | traditional sub-word SIMD | same power budget | p.144 |
| int2 throughput | 2 | × | 7nm EUV, 2021 | int4 mode | comparable power consumption | p.144 |
errors_and_checks: Int2 mode applies when some accuracy loss is permissible; no numerical error distribution or bound is reported (p.144).
conditions: The decoupled engine is selected because AI inference requires greater power efficiency than an integer extension of the training FPU (p.144). The inference-specific dataflow removes some operand latches (p.144). Int2 mode permits accuracy loss in exchange for twice the int4 throughput at comparable power (p.144).
evidence: p.144 inference-engine description; Fig. 9.1.3, p.145; Figs. 9.1.6-9.1.7, pp.145-146

## new_families
### fused_multiply_multiply_accumulate  (domain: dot, closest: multi_term_fused_dot, why_not: The operation combines two products with an addend, while the document does not establish the unrounded-product or single-rounding contract required by multi_term_fused_dot.)
mechanism: The hfp8 FMMA instruction performs two multiplications and two additions. Three terms are aligned to the exponent of the larger product. The smaller product is shifted using the calculated product-exponent difference. The hfp8 operands use a unified fp9 internal representation, and the operation produces an fp16 result through the adder shared with the fp16 path.
choices: product_count: Int[2..2:1]; addend_present: Bool; alignment_target: {larger_product}; internal_operand_format: {fp9}; result_format: {fp16}
results:
| metric | value | unit | technology / device | baseline | condition | page |
| hfp8 FMMA performance | 2 | × | 7nm EUV, 2021 | fp16 mode | same power | p.144 |
evidence: p.144; Fig. 9.1.2, p.145

## space_gaps
* `fp8_training_datapath.format_policy` lacks a value for distinct but unspecified forward/backward hfp8 formats (p.144).
* `fp8_training_datapath` lacks choices for unified internal-format conversion and zero-multiplicand pipeline bypass (p.144).
* The dot vocabulary lacks an explicit two-product-plus-addend FMMA family whose rounding contract remains unspecified (p.144).
* `integer_mac` lacks an element-precision choice for int4/int2 SIMD MAC pipelines (p.144).

## open_questions
* The document does not identify the exact hfp8 forward/backward encodings (p.144).
* The document does not state whether FMMA rounds only once or whether intermediate additions/products are rounded (p.144).
* The document does not identify the multiplier/reduction/terminal-adder families used in either compute engine (p.144).
