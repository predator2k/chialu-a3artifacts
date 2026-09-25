---
handle: stevens_2021
citation: J. R. Stevens, R. Venkatesan, S. Dai, B. Khailany, A. Raghunathan, "Softermax: Hardware/Software Co-Design of an Efficient Softmax for Transformers", ACM/IEEE Design Automation Conference (DAC), pp. 469-474, 2021
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_SFU]
formats: [fixed_point_Q6_2, fixed_point_Q1_15, fixed_point_Q10_6, fixed_point_Q1_7]
authority: incremental
pages_read: 6 / 6
---

## summary
Softermax replaces the natural exponential with a low-precision base-two implementation and replaces the explicit maximum pass with online normalization. Its hardware uses an Unnormed Softmax Unit for maximum/exponentiation/denominator accumulation and a shared Normalization Unit for numerator renormalization/division. A TSMC 7nm implementation reports 0.90x area and 0.43x energy against a 16-bit floating-point DesignWare baseline, with a worst reported task-accuracy drop under 0.5%.

## families
### softmax_layernorm  (role: proposes)
mechanism: Softermax computes base-two exponentials, maintains a running integer maximum and denominator, and shift-renormalizes the running sum whenever a new maximum appears. The Unnormed Softmax Unit contains IntMax, Power of Two, and Reduction subunits. The Normalization Unit shift-renormalizes stored numerators and multiplies them by a piecewise-linear reciprocal. The organization removes the separate pass used only to find the global maximum.
choices:
  exp_evaluation: lut_pwl   # p.4
  max_subtraction: true   # p.3
  normalization_division: reciprocal_multiply   # p.4
  passes_over_vector: 2   # pp.3-4
  layernorm_support: false   # pp.3-4
new_choices:
  exponential_base: 2 — selects the exponential base used by softmax   # p.3
  normalization_schedule: online_running_max — updates the maximum and denominator during the input pass   # p.3
  maximum_quantization: integer_ceiling — applies ceiling before maximum selection so renormalization becomes a shift   # pp.3-4
slots:
  none
parameters: input/local maximum Q(6,2); unnormalized output Q(1,15); power sum Q(10,6); reciprocal/output Q(1,7); 8-bit input/output; 24-bit accumulation; VectorSize/NLanes 16 or 32   # pp.4-5
results:
| metric | value | unit | technology / device | baseline | condition | page |
| area | 0.25x | Area (um2) | TSMC 7nm / 2021 | 16-bit floating-point DesignWare softmax | Unnormed Softmax Unit, SQuAD sequence length 384 | p.5 |
| energy | 0.10x | Energy (uJ) | TSMC 7nm / 2021 | 16-bit floating-point DesignWare softmax | Unnormed Softmax Unit, SQuAD sequence length 384 | p.5 |
| area | 0.65x | Area (um2) | TSMC 7nm / 2021 | 16-bit floating-point DesignWare softmax | Normalization Unit | p.5 |
| energy | 0.39x | Energy (uJ) | TSMC 7nm / 2021 | 16-bit floating-point DesignWare softmax | Normalization Unit | p.5 |
| area | 0.90x | Area (um2) | TSMC 7nm / 2021 | MAGNet PE with 16-bit floating-point DesignWare softmax | Full PE | p.5 |
| energy | 0.43x | Energy (uJ) | TSMC 7nm / 2021 | MAGNet PE with 16-bit floating-point DesignWare softmax | Full PE | p.5 |
| average accuracy change | +0.9% | accuracy | UNKNOWN / 2021 | eight-bit quantized baseline | BERT-Base across SQuAD/GLUE tasks | p.5 |
| average accuracy change | +0.7% | accuracy | UNKNOWN / 2021 | eight-bit quantized baseline | BERT-Large across SQuAD/GLUE tasks | p.5 |
| worst accuracy drop | under 0.5% | accuracy | UNKNOWN / 2021 | eight-bit quantized baseline | BERT-Base/BERT-Large across SQuAD/GLUE tasks | p.5 |
errors_and_checks: Softermax-aware quantization fine-tuning yields a worst task-accuracy drop under 0.5%; average accuracy changes are +0.9% for BERT-Base and +0.7% for BERT-Large. No numerical error bound or hardware fault check is reported.   # p.5
conditions: Softermax requires custom low-precision hardware and Softermax-aware fine-tuning; the fine-tuning replaces the downstream fine-tuning already required rather than adding another training phase. The Unnormed Softmax throughput should match MAC throughput, while the Normalization Unit can operate between the processing tile and global memory. Energy scales more slowly than the baseline as sequence length increases.   # pp.3-5
evidence: Figure 3 and §III-A-C, pp.3-4; Figure 4 and §IV-A-C, p.4; Tables I-IV and Figure 5, pp.4-5.

### pwl  (role: instantiates)
mechanism: The Power of Two Unit splits a fixed-point operand into integer/fractional parts. A four-segment linear piece-wise function evaluates the fractional part using slope and constant LUTs, after which the integer part controls a shift. With two or fewer fractional bits, the slope multiplication vanishes because the scaled fractional term is zero. The reciprocal used for final division is also linear piece-wise, but its segment count and coefficient widths are not reported.
choices:
  segments: 4 [outside domain]   # p.4
  segmentation: uniform   # p.4
  x_frac_bits: 2 [outside domain]   # pp.4-5
  slope_encoding: plain   # p.4
new_choices:
  coefficient_table_structure: separate_mlut_clut — stores segment slopes and constants in separate LUTs   # p.4
slots:
  segmenter: uniform_high_bit_decode   # p.4
parameters: fractional domain [0, 1); four power-of-two segments; Q(6,2) input; reciprocal segment count UNKNOWN   # pp.4-5
results: none
errors_and_checks: No approximation-error bound is reported; task-level effects are evaluated after Softermax-aware fine-tuning.   # p.5
conditions: The m LUT is unused when the input has two or fewer fractional bits. General-purpose hardware is stated to use 64-128 entries, while this implementation uses four segments.   # p.4
evidence: §IV-A Power of Two Unit and §IV-B, p.4; Table I, p.4.

## new_families
none

## space_gaps
* `softmax_layernorm` lacks choices for exponential base, online running-maximum normalization, and maximum quantization, which determine Softermax's shift-only renormalization.   # pp.3-4
* `pwl.segments` and `pwl.x_frac_bits` exclude the four-segment, two-fractional-bit implementation reported here.   # pp.4-5

## open_questions
* The reciprocal unit's segment count/coefficient widths and the stored numerator buffering required for the normalization pass are not specified.
* The paper does not report standalone numerical approximation error for the base-two exponential or reciprocal units.
