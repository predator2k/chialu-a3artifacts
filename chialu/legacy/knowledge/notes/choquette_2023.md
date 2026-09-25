---
handle: choquette_2023
citation: J. Choquette, "NVIDIA Hopper H100 GPU: Scaling Performance", IEEE Micro, vol. 43, no. 3, pp. 9-17, 2023.
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_DOT_ACC]
formats: [tf32, fp16, bfloat16, fp32, int8, fp8_e4m3, fp8_e5m2]
authority: landmark
pages_read: 9-17 / 9
---

## summary
The document describes H100’s fourth-generation Tensor Core, which doubles per-SM clock-for-clock throughput over A100 and adds FP8 matrix multiplication with FP16 or FP32 accumulation (p.14). The document reports layer-dependent selection between E4M3 and E5M2 plus output scaling for FP8 training (pp.14-15).

## families
### tensor_core_mixed_precision_mac  (role: instantiates)
mechanism: The fourth-generation Tensor Core performs matrix multiplication in TF32, FP16, BFLOAT16, INT8, and two FP8 formats. FP8 matrix multiplication accumulates into either FP32 or FP16. Subsequent bias addition or activation runs on the SM at the higher accumulation precision before conversion to the requested output format (p.14).
choices:
new_choices:
  input_formats: tf32_fp16_bfloat16_int8_fp8_e4m3_fp8_e5m2 — formats accepted by the Tensor Core matrix-multiplication path # p.14
slots:
  none
parameters: TF32 1024 MACs/clock/SM; FP16 2048 MACs/clock/SM; BFLOAT16 2048 MACs/clock/SM; INT8 4096 MACs/clock/SM; FP8 throughput matches INT8; FP8 accumulation is selectable between FP16 and FP32 # p.14
results:
| metric | value | unit | technology / device | baseline | condition | page |
| Tensor Core throughput improvement | 2× | throughput per SM, clock-for-clock | H100, TSMC 4 N custom 4-nm, 2023 | A100 | all supported data formats | p.14 |
| TF32 throughput | 1024 | MACs/clock/SM | H100, TSMC 4 N custom 4-nm, 2023 | A100 | dense Tensor Core arithmetic | p.14 |
| FP16 throughput | 2048 | MACs/clock/SM | H100, TSMC 4 N custom 4-nm, 2023 | A100 | dense Tensor Core arithmetic | p.14 |
| BFLOAT16 throughput | 2048 | MACs/clock/SM | H100, TSMC 4 N custom 4-nm, 2023 | A100 | dense Tensor Core arithmetic | p.14 |
| INT8 throughput | 4096 | MACs/clock/SM | H100, TSMC 4 N custom 4-nm, 2023 | A100 | dense Tensor Core arithmetic | p.14 |
| sparse arithmetic throughput improvement | 2× | throughput | H100, TSMC 4 N custom 4-nm, 2023 | dense Tensor Core arithmetic | one operand is sparse | p.14 |
| operand-delivery efficiency improvement | 30% | efficiency | H100, TSMC 4 N custom 4-nm, 2023 | A100 | Tensor Core operand delivery | p.14 |
errors_and_checks: The document does not specify partial-sum rounding, subnormal behavior, or a numerical arithmetic-error bound (pp.14-15).
conditions: FP8 matrix multiplication uses FP16 or FP32 accumulation because linear-math results can exceed the FP8 representable range. Bias addition and activation can execute at the higher accumulation precision before output conversion (pp.14-15).
evidence: Figure 7 and “Accelerating Deep Learning” (pp.14-15).

### fp8_training_datapath  (role: instantiates)
mechanism: H100 supports E5M2 and E4M3 FP8 inputs. E5M2 provides greater exponent range, while E4M3 trades one bit of range for one additional bit of precision. Layer output statistics determine the selected FP8 format and scaling factor. Matrix multiplication accumulates in FP16 or FP32, and the result is scaled into the selected FP8 representable range during conversion for the next layer (pp.14-15).
choices:
  format_policy: per_layer_e4m3_or_e5m2 [outside domain] # p.15
  accumulate_precision: fp16_or_fp32 [outside domain] # p.14
new_choices:
  scale_selection: per_layer_output_statistics — output statistics determine the scaling factor used during FP8 conversion # p.15
slots:
  none
parameters: two FP8 formats, E5M2 and E4M3; FP8 throughput is twice FP16/BFLOAT16 throughput; accumulation is FP16 or FP32 # pp.14-15
results:
| metric | value | unit | technology / device | baseline | condition | page |
| FP8 throughput improvement | 2× | throughput | H100, TSMC 4 N custom 4-nm, 2023 | FP16 and BFLOAT16 | Tensor Core matrix multiplication | p.14 |
| training tensor-math throughput improvement | approximately 6× | throughput | H100, TSMC 4 N custom 4-nm, 2023 | A100 | combined FP8 use, 2× higher-throughput Tensor Cores, 1.2× more SMs, and 1.3× frequency | p.15 |
errors_and_checks: FP8 training achieves approximately the same accuracy as 16-bit training for two transformer networks and BERT. FP8 training perplexity closely matches native BF16 or FP16 during GPT-3 training, but the document gives no numerical error bound (p.15).
conditions: E5M2 suits layers requiring wider exponent range. E4M3 suits layers with narrower range that need more precision. FP16 or FP32 accumulation prevents loss when intermediate matrix-multiplication results exceed the FP8 range. Output scaling maps results into the FP8 range for the next layer (p.15).
evidence: Figures 7-8 and “Accelerating Deep Learning” (pp.14-15).

## new_families
none

## space_gaps
* `fp8_training_datapath.format_policy` lacks per-layer selection between E4M3 and E5M2 based on exponent-range and precision requirements (p.15).
* `fp8_training_datapath.accumulate_precision` cannot express hardware-selectable FP16 or FP32 accumulation (p.14).
* `fp8_training_datapath` lacks a choice for statistics-derived output scaling during conversion to FP8 (p.15).
* `tensor_core_mixed_precision_mac` lacks a choice that records its supported input-format set (p.14).

## open_questions
* The document does not identify the Tensor Core multiplier/reduction microarchitecture (pp.14-15).
* The document does not state partial-sum rounding, alignment order, subnormal handling, stochastic rounding, or whether FP8 products are retained exactly (pp.14-15).
* Figure 8 reports approximate accuracy equivalence without numerical accuracy or perplexity values (p.15).
