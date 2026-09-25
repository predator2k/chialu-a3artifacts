---
handle: decaro_2009
citation: D. De Caro, N. Petra, A. G. M. Strollo, "High-Performance Special Function Unit for Programmable 3-D Graphics Processors", IEEE Transactions on Circuits and Systems I, vol. 56, no. 9, pp. 1968-1978, 2009
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_SFU]
formats: [fp32]
authority: incremental
pages_read: 1968-1978 / 11
---

## summary
The document presents a five-stage IEEE-754 single-precision SFU for reciprocal, square root, reciprocal square root, logarithm, and exponential functions using constrained piecewise quadratic approximation (pp.1968-1969, 1977). Adjacent segment pairs share constant and linear coefficients, which reduces coefficient ROM size while preserving faithful rounding (pp.1970, 1974-1975).

## families
### piecewise_poly  (role: extends)
mechanism: The reduced input interval is uniformly divided into segment pairs, with separate quadratic polynomials for the left and right segments. The implemented approximation constrains the two polynomials to share their constant and linear coefficients. A linear program minimizes sampled maximum error subject to these constraints, and a 27-candidate quantization search determines fixed-point coefficients. A rounded, fixed-width squarer and a fused partial-product carry-save multiply-and-add tree evaluate the polynomial (pp.1970-1973).
choices:
  degree: 2   # p.1969
  coeff_encoding: per_coeff_width   # pp.1969, 1973
  coefficient_optimization: joint_wordlength_search   # pp.1973-1975
  rounding_contract: faithful   # p.1974
new_choices:
  adjacent_segment_constraints: shared_constant_and_linear — adjacent left/right polynomials share the constant coefficient and linear coefficient, imposing value and first-derivative continuity at the segment-pair midpoint   # pp.1970, 1972, 1975
  quantized_coefficient_search: three_pass_27_candidate — rounded linear/quadratic coefficients are perturbed by one LSB and the best of 27 cases is retained after constant-coefficient optimization   # p.1973
slots:
  range_reducer: range_reduction   # pp.1969, 1976
  evaluator: fma_based   # pp.1973, 1976
  segmenter: uniform_high_bit_decode   # p.1976
parameters: degree 2; 32-bit IEEE-754 input/output; 23-bit stored mantissa fraction; segment-pair count UNKNOWN; separate constant/linear ROMs and left/right quadratic-coefficient ROMs; squarer output 17 bit; five pipeline levels   # pp.1969, 1975-1977
results:
| metric | value | unit | technology / device | baseline | condition | page |
| total coefficient ROM size | 21,216 | bit | TSMC 0.18-μm CMOS / 2009 | none | shared constant and linear coefficients | p.1975 |
| coefficient ROM reduction | 40 | % | TSMC 0.18-μm CMOS / 2009 | Pineiro et al. unconstrained piecewise quadratic approximation | same faithful-rounding accuracy; shared constant and linear coefficients | p.1975 |
| coefficient ROM reduction | 27 | % | TSMC 0.18-μm CMOS / 2009 | Pineiro et al. unconstrained piecewise quadratic approximation | shared constant coefficient only | p.1975 |
errors_and_checks: Faithful rounding returns one of the two fixed-point numbers closest to the exact value. The error budget includes approximation, coefficient quantization, squarer truncation, fixed-width partial-product accumulation, and final round-to-nearest errors. Exhaustive bit-level simulation verifies the final configurations. The logarithm exception occurs when the input exponent is zero and the mantissa is close to 1, because hardware needed to preserve the general absolute-error bound was omitted (p.1974).
conditions: Uniform segmentation avoids the segment-index encoder overhead associated with nonuniform segmentation (p.1969). The shared constant-and-linear configuration gives the lowest reported ROM size, while constraints involving quadratic coefficients increase approximation error more severely (pp.1972, 1975).
evidence: Sections III.A-III.F; Figs. 3-6; Tables I-III (pp.1970-1975).

### gpu_multifunction_interpolator  (role: instantiates)
mechanism: A 3-bit function-selection word configures one pipelined SFU for reciprocal, square root, reciprocal square root, logarithm, or exponential. Preprocessing performs function-specific range reduction and exponent/mantissa transformations. A shared mantissa datapath evaluates the selected quadratic approximation, while a parallel exponent/sign path computes function-specific metadata. Postprocessing normalizes the mantissa and converts the exponent to excess-127 representation (pp.1969, 1975-1977).
choices:
  function_set: full_transcendental_set   # pp.1968-1969
  interpolation_degree: 2   # p.1969
  coefficient_precision_grading: per_function   # pp.1974-1975
new_choices:
  none
slots:
  quadratic_core: fma_based   # pp.1973, 1976
parameters: five functions; 3-bit function select; fp32; five pipeline levels; maximum clock frequency 420 MHz   # pp.1969, 1977
results:
| metric | value | unit | technology / device | baseline | condition | page |
| maximum clock frequency | 420 | MHz | TSMC 0.18-μm CMOS / 2009 | none | fabricated five-stage SFU | p.1977 |
| power dissipation | 160 | mW | TSMC 0.18-μm CMOS / 2009 | none | operation at 420 MHz | p.1977 |
| pipeline depth | 5 | levels | TSMC 0.18-μm CMOS / 2009 | none | fabricated SFU | p.1977 |
| ROM area share | 48 | % | TSMC 0.18-μm CMOS / 2009 | total SFU area | standard-cell ROM implementation | p.1977 |
| mantissa arithmetic area share | 27 | % | TSMC 0.18-μm CMOS / 2009 | total SFU area | squarer and partial-product carry-save tree | p.1977 |
| generated-ROM area increase | 25 | % | TSMC 0.18-μm CMOS / 2009 | standard-cell ROM implementation | commercially available ROM generators | p.1977 |
| generated-ROM power increase | 300 | % | TSMC 0.18-μm CMOS / 2009 | standard-cell ROM implementation | commercially available ROM generators | p.1977 |
errors_and_checks: The datapath targets faithful rounding, subject to the logarithm exception described above. Built-in self-test logic is included, but no fault model or coverage is reported. NaN/infinity and other arithmetic exceptions are ignored for hardware simplicity (pp.1974, 1976-1977).
conditions: The design targets programmable graphics accelerators and other high-throughput function-evaluation applications (pp.1968, 1977). Arithmetic-exception handling is outside the implemented datapath (p.1976).
evidence: Sections II, IV, and V; Figs. 1-2 and 7-12; Table IV (pp.1969, 1975-1977).

## new_families
none

## space_gaps
* `piecewise_poly` lacks a choice for equality/continuity constraints between coefficients of adjacent segments (pp.1970-1972).
* `piecewise_poly` lacks slots for the explicit squarer and fused fixed-width carry-save polynomial evaluator (pp.1973, 1976).
* `gpu_multifunction_interpolator.function_set` cannot state the exact implemented set of reciprocal/square root/reciprocal square root/logarithm/exponential functions (pp.1968-1969).
* `range_reduction.method` does not cover the function-specific exponent/mantissa reductions shown for the five implemented functions (p.1969).

## open_questions
* Exact segment counts, coefficient widths, and per-function ROM sizes in Table III are unreadable in the supplied transcription (p.1975).
* Total area and latency values, if present in Table IV, are unreadable in the supplied transcription (p.1977).
