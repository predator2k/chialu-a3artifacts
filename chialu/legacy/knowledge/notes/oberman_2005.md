---
handle: oberman_2005
citation: S. F. Oberman, M. Y. Siu, "A High-Performance Area-Efficient Multifunction Interpolator", 17th IEEE Symposium on Computer Arithmetic (ARITH-17), pp. 272-279, 2005
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_SFU]
formats: [fp32]
authority: landmark
pages_read: 8 / 8
---

## summary
The document proposes a fully pipelined GPU unit that shares quadratic transcendental-function evaluation with planar attribute interpolation. The unit evaluates reciprocal/reciprocal-square-root/exponential/logarithm/sine/cosine functions and interpolates four single-precision pixel samples. Enhanced minimax coefficients, rectangular multipliers, carry-save datapaths, a truncated squarer, and superpipelining reduce table/datapath area and latency.

## families
### gpu_multifunction_interpolator  (role: proposes)
mechanism: The unit reuses two optimized multiplier trees, alignment shifters, carry-save summation, carry-propagate adders, and normalization logic for quadratic function approximation and planar interpolation. Function mode adds coefficient tables and a special truncated squarer. Modified radix-4 Booth logic accepts sign-magnitude/two’s-complement multiplicands and unsigned/two’s-complement multipliers. Carry-save values remain redundant through alignment and summation to avoid intermediate carry-propagate adders.
choices:
  function_set: full_transcendental_set   # p.2
  interpolation_degree: 2   # p.2
  coefficient_precision_grading: per_function   # p.5
  attribute_interpolation_reuse: true   # p.6
new_choices:
  none
slots:
  quadratic_core: parallel_monomial   # p.3
parameters: five function classes covering 1/X, 1/√X, 2^X, log2 X, and sin/cos; 448 x 52b coefficient ROM; 17b special-squarer input/15b output; optimized 24x17 shared multiplier trees; 32b outputs; four pixel samples; fully pipelined with II=1; pipeline stages/latency UNKNOWN   # p.2, p.5, p.7
results:
| metric | value | unit | technology / device | baseline | condition | page |
| function-support area | about 20 | % | UNKNOWN; 2005 | multifunction total | five transcendental functions added to planar interpolator | p.7 |
| 17b squarer area | 90 | full-adders | UNKNOWN; 2005 | one full-adder in in-house library | RTL area estimate | p.8 |
| CS-to-radix-4-SD converter area | 45 | full-adders | UNKNOWN; 2005 | one full-adder in in-house library | RTL area estimate | p.8 |
| lookup-table ROM area | 1380 | full-adders | UNKNOWN; 2005 | one full-adder in in-house library | RTL area estimate | p.8 |
| function overhead total | 1515 | full-adders | UNKNOWN; 2005 | one full-adder in in-house library | five-function support | p.8 |
| two optimized 17x24 multipliers area | 945 | full-adders | UNKNOWN; 2005 | one full-adder in in-house library | RTL area estimate | p.8 |
| eight 5x24 multipliers area | 2040 | full-adders | UNKNOWN; 2005 | one full-adder in in-house library | RTL area estimate | p.8 |
| three 24b right-shifters area | 280 | full-adders | UNKNOWN; 2005 | one full-adder in in-house library | RTL area estimate | p.8 |
| three 24b two’s complementers area | 110 | full-adders | UNKNOWN; 2005 | one full-adder in in-house library | RTL area estimate | p.8 |
| four 45b right-shifters area | 840 | full-adders | UNKNOWN; 2005 | one full-adder in in-house library | RTL area estimate | p.8 |
| four CSA trees area | 730 | full-adders | UNKNOWN; 2005 | one full-adder in in-house library | RTL area estimate | p.8 |
| four 45b CPAs area | 640 | full-adders | UNKNOWN; 2005 | one full-adder in in-house library | RTL area estimate | p.8 |
| four normalizers area | 930 | full-adders | UNKNOWN; 2005 | one full-adder in in-house library | RTL area estimate | p.8 |
| planar-interpolation total area | 6515 | full-adders | UNKNOWN; 2005 | one full-adder in in-house library | RTL area estimate | p.8 |
| multifunction total area | 8030 | full-adders | UNKNOWN; 2005 | one full-adder in in-house library | RTL area estimate | p.8 |
errors_and_checks: Exhaustive simulation covers all single-precision inputs for the five functions and compares results with x86 double-precision results. Random/directed-random/directed interpolation tests match an existing NVIDIA GPU bit-accurately.   # p.7
conditions: Sharing applies because the function evaluator and attribute interpolator have similar computational cores and neither separate unit remains fully utilized. Architectural studies find that the shared unit satisfies shader throughput requirements.   # p.1
evidence: §2.2.2, Figure 1, §4.2, Figures 4-5, §4.3, §4.4, Table 2, pp.3-8

### lut_plus_poly  (role: instantiates)
mechanism: The upper m significand bits select finite-width C0/C1/C2 coefficients. The lower bits evaluate C0 + C1Xl + C2Xl². Enhanced minimax generation rounds C1, adjusts C2 to compensate for C1 rounding, and recomputes C0 to compensate for both rounded coefficients. A function-specific bias centers the aggregate error distribution. The polynomial uses a truncated special squarer, parallel rectangular multiplier trees, carry-save summation, and final normalization.
choices:
  degree: 2   # p.3
  index_bits: 6/7   # p.5
  basis: minimax_remez   # p.3
  coeff_encoding: per_coeff_width   # p.5
  breakpoint_placement: uniform   # p.2
  multiplier_shape: rectangular   # p.4
new_choices:
  error_centering_bias: per_function — a precomputed bias centers approximation error from coefficient/squarer truncation   # p.4
slots:
  range_reducer: UNKNOWN   # p.2
  evaluator: parallel_monomial   # p.3
  segmenter: uniform_high_bit_decode   # p.2
parameters: m=7 with configuration 26,16,10 for 1/X; m=6 with configuration 26,16,10 for 1/√X, 2^X, and log2 X; m=6 with configuration 26,15,11 for sin/cos; total ROM 448 x 52b   # p.5
results:
| metric | value | unit | technology / device | baseline | condition | page |
| accuracy | 24.02 | good bits | UNKNOWN; 2005 | exact function | 1/X over [1,2) | p.5 |
| maximum error | 0.98 | ulp | UNKNOWN; 2005 | exactly rounded-to-nearest | 1/X; monotonic | p.5 |
| exactly rounded | 87 | % | UNKNOWN; 2005 | exactly rounded-to-nearest | 1/X | p.5 |
| lookup-table size | 6.50 | Kb | UNKNOWN; 2005 | none | 1/X | p.5 |
| accuracy | 23.40 | good bits | UNKNOWN; 2005 | exact function | 1/√X over [1,4) | p.5 |
| maximum error | 1.52 | ulp | UNKNOWN; 2005 | exactly rounded-to-nearest | 1/√X; monotonic | p.5 |
| exactly rounded | 78 | % | UNKNOWN; 2005 | exactly rounded-to-nearest | 1/√X | p.5 |
| lookup-table size | 6.50 | Kb | UNKNOWN; 2005 | none | 1/√X | p.5 |
| accuracy | 22.51 | good bits | UNKNOWN; 2005 | exact function | 2^X over [0,1) | p.5 |
| maximum error | 1.41 | ulp | UNKNOWN; 2005 | exactly rounded-to-nearest | 2^X; monotonic | p.5 |
| exactly rounded | 74 | % | UNKNOWN; 2005 | exactly rounded-to-nearest | 2^X | p.5 |
| lookup-table size | 3.25 | Kb | UNKNOWN; 2005 | none | 2^X | p.5 |
| accuracy | 22.57 | good bits | UNKNOWN; 2005 | exact function | log2 X over [1,2); monotonic | p.5 |
| lookup-table size | 3.25 | Kb | UNKNOWN; 2005 | none | log2 X | p.5 |
| accuracy | 22.47 | good bits | UNKNOWN; 2005 | exact function | sin/cos over [0,π/2]; nonmonotonic | p.5 |
| lookup-table size | 3.25 | Kb | UNKNOWN; 2005 | none | sin/cos | p.5 |
| total lookup-table size | 22.75 | Kb | UNKNOWN; 2005 | none | five function classes | p.5 |
errors_and_checks: Reciprocal is monotonic with 0.98 ulp maximum error. Reciprocal square root is monotonic with 1.52 ulp maximum error. Exponential is monotonic with 1.41 ulp maximum error. The document does not report ulp or exactly-rounded rates for log2 X or sin/cos.   # p.5
conditions: The design targets 32b IEEE single precision, high frequency, full pipelining, and one result per clock. The evaluator presumes that argument reduction has already placed each input in the required interval. Exhaustive single-precision simulation permits parameter/bias adjustment for area or latency.   # p.2, p.3
evidence: §2.2, Figure 1, §2.3, Table 1, pp.2-5

## new_families
none

## space_gaps
* gpu_multifunction_interpolator lacks slots for the special squarer and coefficient ROM, which are the major added components for function evaluation.   # p.6
* gpu_multifunction_interpolator lacks a choice for mixed sign-magnitude/two’s-complement and variable-width operand support in its shared Booth multiplier trees.   # p.6
* lut_plus_poly lacks a choice for the function-specific bias used to center errors from coefficient and datapath truncation.   # p.4

## open_questions
* The ASIC process/technology node and operating frequency are not reported.   # pp.7-8
* The superpipeline stage count and operation latency are not reported.   # pp.1-2
* The document presumes external argument reduction but does not identify its implementation.   # p.2
* The document does not report normalized ulp error or exactly-rounded rates for log2 X and sin/cos.   # p.5
