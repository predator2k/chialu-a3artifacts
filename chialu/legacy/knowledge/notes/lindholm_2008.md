---
handle: lindholm_2008
citation: E. Lindholm, J. Nickolls, S. Oberman, J. Montrym, "NVIDIA Tesla: A Unified Graphics and Computing Architecture", IEEE Micro, vol. 28, no. 2, pp. 39-55, 2008.
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU, VEC_SFU]
formats: [fp32]
authority: landmark
pages_read: 39-55 / 17 pages
---

## summary
The document describes the Tesla GPU architecture, including scalar floating-point multiply-add units and multifunction SFUs in each streaming multiprocessor. The SFU uses quadratic interpolation for reciprocal/reciprocal-square-root/logarithm/exponential/sine/cosine evaluation and reuses the hardware for planar attribute interpolation. The SP multiply-add truncates the product before an IEEE round-to-nearest-even addition, so it is not a fused operation.

## families
### gpu_multifunction_interpolator  (role: instantiates)
mechanism: Each SM contains two fully pipelined SFUs that use quadratic interpolation based on enhanced minimax approximations. The SFUs approximate 1/x, 1/sqrt(x), log2x, 2^x, and sin/cos and reuse the datapath for planar attribute interpolation. Each SFU also contains four floating-point multipliers. The interpolation path evaluates perspective-correct attributes through interpolation of 1/W and U/W followed by multiplication by W.
choices:
  function_set: {1/x, 1/sqrt(x), log2x, 2^x, sin/cos} [outside domain]   # p.46
  interpolation_degree: 2   # p.46
  attribute_interpolation_reuse: true   # pp.46-47
new_choices:
  none
slots:
  none
parameters: two SFUs per SM; four floating-point multipliers per SFU; 32-bit floating-point output; one function result per cycle; four attribute-interpolation samples per cycle   # pp.43, 46-47
results:
| metric | value | unit | technology / device | baseline | condition | page |
| accuracy | 24.02 | good bits | TSMC 90-nm CMOS / GeForce 8800 Ultra / 2008 | none reported | 1/x over [1, 2) | p.47 |
| ULP error | 0.98 | ULP | TSMC 90-nm CMOS / GeForce 8800 Ultra / 2008 | none reported | 1/x over [1, 2) | p.47 |
| exactly rounded | 87 | % | TSMC 90-nm CMOS / GeForce 8800 Ultra / 2008 | none reported | 1/x over [1, 2) | p.47 |
| accuracy | 23.40 | good bits | TSMC 90-nm CMOS / GeForce 8800 Ultra / 2008 | none reported | 1/sqrt(x) over [1, 4) | p.47 |
| ULP error | 1.52 | ULP | TSMC 90-nm CMOS / GeForce 8800 Ultra / 2008 | none reported | 1/sqrt(x) over [1, 4) | p.47 |
| exactly rounded | 78 | % | TSMC 90-nm CMOS / GeForce 8800 Ultra / 2008 | none reported | 1/sqrt(x) over [1, 4) | p.47 |
| accuracy | 22.51 | good bits | TSMC 90-nm CMOS / GeForce 8800 Ultra / 2008 | none reported | 2^x over [0, 1) | p.47 |
| ULP error | 1.41 | ULP | TSMC 90-nm CMOS / GeForce 8800 Ultra / 2008 | none reported | 2^x over [0, 1) | p.47 |
| exactly rounded | 74 | % | TSMC 90-nm CMOS / GeForce 8800 Ultra / 2008 | none reported | 2^x over [0, 1) | p.47 |
| accuracy | 22.57 | good bits | TSMC 90-nm CMOS / GeForce 8800 Ultra / 2008 | none reported | log2x over [1, 2) | p.47 |
| accuracy | 22.47 | good bits | TSMC 90-nm CMOS / GeForce 8800 Ultra / 2008 | none reported | sin/cos over [0, π/2) | p.47 |
| function throughput | 1 | 32-bit floating-point result/cycle | TSMC 90-nm CMOS / GeForce 8800 Ultra / 2008 | none reported | SFU functional evaluation | p.46 |
| interpolation throughput | 4 | samples/cycle | TSMC 90-nm CMOS / GeForce 8800 Ultra / 2008 | none reported | fully pipelined attribute interpolation | p.47 |
errors_and_checks: Table 1 reports 0.98 ULP for 1/x, 1.52 ULP for 1/sqrt(x), and 1.41 ULP for 2^x. The exactly rounded rates are 87%, 78%, and 74%, respectively. The 1/x, 1/sqrt(x), 2^x, and log2x estimates are monotonic; sin/cos is not monotonic. ULP and exactly-rounded statistics are not applicable for the reported log2x and sin/cos entries.   # p.47
conditions: The reported accuracy applies only to the input intervals in Table 1. The paper does not claim correct rounding for every result. Attribute interpolation shares the SFU used for transcendental evaluation.   # pp.46-47
evidence: Streaming multiprocessor and Special-function unit sections, Figures 2-3, and Table 1, pp.42-47.

## new_families
### nonfused_fp_mad  (domain: dot: dot-product / FMA / MAC, closest: classic_fma, why_not: classic_fma has one terminal rounding, while the Tesla MAD truncates the multiplication before the addition)
mechanism: Each SP core contains a scalar multiply-add unit. The multiply-add operation performs a floating-point multiplication with truncation and then performs an addition with round-to-nearest-even. The fully pipelined SP also executes separate floating-point add and multiply operations. Source denormals and underflowed results are flushed to sign-preserved zero.
choices: product_handling: {truncate_before_add}; add_rounding: {round_to_nearest_even}; subnormal_handling: {flush_sources_and_underflowed_results_to_sign_preserved_zero}
results:
| metric | value | unit | technology / device | baseline | condition | page |
| processor clock | 1.5 | GHz | TSMC 90-nm CMOS / GeForce 8800 Ultra / 2008 | none reported | SP and SFU units | p.43 |
| peak throughput | 36 | Gflops/SM | TSMC 90-nm CMOS / GeForce 8800 Ultra / 2008 | none reported | aggregate of eight SP MAD units and two SFUs | p.43 |
| peak throughput | 576 | Gflops | TSMC 90-nm CMOS / GeForce 8800 Ultra / 2008 | none reported | aggregate processors in 128-SP, 16-SM GPU | p.54 |
evidence: Streaming multiprocessor and Streaming processor sections, pp.43 and 46; implementation specifics, p.54.

## space_gaps
* The dot/FMA vocabulary lacks a family for a hardware multiply-add that truncates the product before the addition rather than performing one fused rounding.   # p.46
* `gpu_multifunction_interpolator.function_set` lacks a value for the disclosed set `{1/x, 1/sqrt(x), log2x, 2^x, sin/cos}`.   # pp.46-47
* `gpu_multifunction_interpolator` lacks a choice for per-function monotonicity and approximation accuracy.   # p.47
* Floating-point datapath families lack a subnormal-handling choice for flushing source denormals and underflowed results to sign-preserved zero.   # p.46

## open_questions
* The paper does not specify the SFU polynomial evaluator/coefficients, so `quadratic_core` cannot be assigned.
* The paper does not state the MAD product truncation precision or instruction latency.
* The 36 Gflops/SM and 576 Gflops figures are aggregate processor peaks rather than isolated MAD measurements.
