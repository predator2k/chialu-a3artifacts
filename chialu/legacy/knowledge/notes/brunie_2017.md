---
handle: brunie_2017
citation: N. Brunie, "Modified Fused Multiply and Add for Exact Low Precision Product Accumulation", ARITH-24, pp. 106-113, 2017
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_DOT_ACC]
formats: [binary16, binary32, fixed80]
authority: incremental
pages_read: 106-113 / 8
---

## summary
The paper revisits mixed-precision FMA for binary16 products and binary32 accumulation, then proposes fixed-point accumulators that preserve binary16 products exactly until a final conversion. The fixed design uses an 80-bit product range plus optional extension bits and sustains one accumulation per cycle. Front-end synthesis compares two accumulator encodings with fp16/fp32 FMA baselines.

## families
### mixed_precision_cascade_fma  (role: extends)
mechanism: The MPFMA computes r = ◦(a × b + c) with binary16 multiplication operands and binary32 accumulator/result operands. Conversion is merged into the FMA alignment/normalization/rounding structures. The datapath supports full normalization of products involving subnormal binary16 operands because those products may remain representable in binary32. The unified addition datapath is 99 bits for the evaluated binary16/binary32 instance. # pp.107-110
choices:
  exact_product_preserved: true   # pp.107-110
new_choices:
  format_pairing: binary16_product_binary32_accumulator — fixes the multiplication-input and accumulator/output formats independently   # pp.107-110
slots: none
parameters: binary16 a/b; binary32 c/r; 99-bit unified datapath; 6 pipeline stages including I/O registers; 2.0 ns synthesis constraint   # pp.109,112
results:
| metric | value | unit | technology / device | baseline | condition | page |
| cell area | 2689.70 | μm² | TSMC 28nm HP / 2017 | fp32 FMA: 4793.10 μm² | front-end synthesis before place and route; 2.0 ns constraint; 6 stages | p.113 |
errors_and_checks: The operation produces a correctly rounded binary32 result after each fused binary16 product/addition; it does not provide exact accumulation across a sequence of MPFMAs. # pp.107-110,112
conditions: The MPFMA avoids explicit format-conversion instructions and offers binary32 accumulation accuracy for binary16 products. Full product denormalization makes its addition datapath about as wide as the fp32 FMA datapath. # pp.108-110
evidence: §IV; Table I, p.110; Table II, p.113

### kulisch_long_accumulator  (role: proposes)
mechanism: The fixed MPFMA aligns each binary16 significand product into a fixed-point accumulator with 48 fractional bits. An 80-bit range covers every possible binary16 product, and e high-order bits extend the accumulation range. The datapath contains an 80-bit alignment shifter, an 80-bit adder, and an e-bit incrementer. Two implementations encode the accumulator as 2's complement or sign magnitude. Normalization and rounding occur only during final floating-point conversion. # pp.110-112
choices:
  accumulator_width_bits: 80 [outside domain]   # p.110
  organization: monolithic   # pp.110-111
  carry_resolution: immediate   # p.112
new_choices:
  accumulator_encoding: {twos_complement, sign_magnitude} — selects whether the product or accumulator is conditionally negated   # p.111
  extension_bits: {0, 16, 64} — extends the 80-bit exact-product range for longer accumulations   # pp.110,113
slots:
  cpa: UNKNOWN   # pp.111-112
parameters: width = 80+e bits; e ∈ {0,16,64}; 48 fractional bits; 3 pipeline stages including I/O registers; II=1 accumulation/cycle; 2.0 ns synthesis constraint   # pp.110,112-113
results:
| metric | value | unit | technology / device | baseline | condition | page |
| cell area | 2195.83 | μm² | TSMC 28nm HP / 2017 | fp32 FMA: 4793.10 μm² | sign magnitude; e=0; 2.0 ns constraint | p.113 |
| cell area | 2247.70 | μm² | TSMC 28nm HP / 2017 | fp32 FMA: 4793.10 μm² | sign magnitude; e=16; 2.0 ns constraint | p.113 |
| cell area | 3631.68 | μm² | TSMC 28nm HP / 2017 | fp32 FMA: 4793.10 μm² | sign magnitude; e=64; 2.0 ns constraint | p.113 |
| cell area | 1947.01 | μm² | TSMC 28nm HP / 2017 | fp32 FMA: 4793.10 μm² | 2's complement; e=0; 2.0 ns constraint | p.113 |
| cell area | 2045.81 | μm² | TSMC 28nm HP / 2017 | fp32 FMA: 4793.10 μm² | 2's complement; e=16; 2.0 ns constraint | p.113 |
| cell area | 2794.22 | μm² | TSMC 28nm HP / 2017 | fp32 FMA: 4793.10 μm² | 2's complement; e=64; 2.0 ns constraint | p.113 |
errors_and_checks: Accumulation has no intermediate rounding and is exact while the accumulator does not overflow. An e-bit extension is sufficient for 2^e maximum-magnitude products, although smaller products may permit longer exact accumulation. # p.112
conditions: The 80-bit range is feasible because binary16 product exponents span [-48,31]. The paper states that the wider exponent range of binary32 makes the same fixed-point approach impractical without much more hardware. Final conversion is required, and overflow remains possible after the supported accumulation range. # pp.110,112
evidence: §V; Figures 4-7, pp.111-112; Table II, p.113

### streaming_accurate_accumulator  (role: instantiates)
mechanism: The fixed-point accumulator removes alignment/normalization/rounding from the loop-carried path. The 2's-complement version places only the 80-bit accumulator addition in the feedback loop, while multiplication and product alignment may use any number of pipelined stages. Accumulator bypass therefore accepts one new product each cycle. # p.112
choices:
  approach: shifted_fixed_point_window   # pp.110-112
  window_bits: 80   # pp.110-112
  in_loop_normalization: false   # pp.110-112
new_choices:
  feedback_encoding: {twos_complement, sign_magnitude} — changes the work placed on the accumulation feedback path   # pp.111-112
slots:
  cpa: UNKNOWN   # p.112
parameters: 80-bit base window; optional e-bit extension; II=1; 3 pipeline stages in evaluated fixed designs   # pp.110,112-113
results:
| metric | value | unit | technology / device | baseline | condition | page |
| initiation interval | 1 | cycle | TSMC 28nm HP / 2017 | UNKNOWN | pipelined multiply/alignment with single-cycle accumulator bypass | p.112 |
errors_and_checks: The window preserves every binary16 product bit and performs no in-loop rounding; exactness ends on accumulator overflow. # pp.110,112
conditions: The single-cycle loop depends on completing the 80-bit addition in one cycle. The fixed accumulation result differs from a sequence of FMAs because the sequence rounds after every accumulation. # p.112
evidence: §V-B-§V-D, p.112

### classic_fma  (role: compares)
mechanism: The comparison FMA computes one product/addend result with a single final rounding. The evaluated fp16 and fp32 implementations use six pipeline stages, including input/output registers. # pp.107,112
choices:
  pipeline_depth: 6 [outside domain]   # p.112
new_choices: none
slots: none
parameters: fp16 or fp32; 6 pipeline stages including I/O registers; 2.0 ns synthesis constraint   # p.112
results:
| metric | value | unit | technology / device | baseline | condition | page |
| cell area | 1841.90 | μm² | TSMC 28nm HP / 2017 | fp32 FMA: 4793.10 μm² | fp16 FMA; front-end synthesis before place and route | p.113 |
| cell area | 4793.10 | μm² | TSMC 28nm HP / 2017 | reference | fp32 FMA; front-end synthesis before place and route | p.113 |
errors_and_checks: One fused operation has a single final rounding, but repeated accumulation loses information at each FMA output. # p.107
conditions: The fp32 FMA is the synthesis-area reference. The implementations omit some standard latency optimizations, so the paper leaves their area effect unresolved. # pp.112-113
evidence: §III, pp.107-108; §VI, p.112; Table II, p.113

## new_families
none

## space_gaps
* `kulisch_long_accumulator.accumulator_width_bits` excludes the reported 80/96/144-bit exact binary16 accumulator widths. # pp.110,113
* `kulisch_long_accumulator` lacks an accumulator-encoding choice for 2's complement versus sign magnitude. # p.111
* `kulisch_long_accumulator` lacks a slot for the required final fixed-to-floating-point conversion. # p.110
* `mixed_precision_cascade_fma` lacks choices for independent multiplication-input and accumulator/output formats. # pp.107-110
* `streaming_accurate_accumulator` lacks a choice for accumulator encoding, which changes the loop-carried critical path. # pp.111-112

## open_questions
* Table II does not state whether final fixed-to-floating-point conversion hardware is included in the fixed-MPFMA cell areas.
* The accumulator-overflow response is not specified.
* The paper does not identify the adder family used for the 80-bit main adder or e-bit incrementer.
