---
handle: langhammer_2021
citation: M. Langhammer, E. Nurvitadhi, B. Pasca, S. Gribok, "Stratix 10 NX Architecture and Applications", ACM/SIGDA International Symposium on Field-Programmable Gate Arrays (FPGA), 2021
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU, VEC_SFU, VEC_DOT_ACC]
formats: [int4, int8, int15, int32, fp12_block, fp16, fp16_block, bfp24, fp32]
authority: landmark
pages_read: 57-67 / 11
---

## summary
The document introduces the Stratix 10 NX AI Tensor Block, which combines dense INT8/INT4 dot products, shared-exponent block floating point, INT32/FP32 accumulation, and dedicated block cascades (pp.57-59). The document also demonstrates larger multipliers, sigmoid/tanh implementations, and chip-scale tensor arrays built from the blocks (pp.61-66).

## families
### ai_tensor_block  (role: proposes)
mechanism: Each block contains 30 INT8 multipliers decomposable into 60 INT4 multipliers and arranged as three 10-element dot products. Tensor mode preloads one operand dimension and streams the other; vector mode changes both operands each cycle; scalar mode exposes individual multipliers or three FP32 ALUs. Dedicated inter-block buses cascade INT32/FP32 results through chains of up to 36 blocks. One or two terminal blocks can act as accumulators, with accumulated values stored in soft registers or embedded memory (pp.58-60).
choices:
  dot_width: 10 [outside domain]   # p.58
  element_format: int8   # p.58
  element_format: int4   # p.58
  accumulate_format: int32   # pp.58-59
  accumulate_format: fp32   # pp.58-59
  cascade_tensor_chain: true   # p.58
new_choices:
  operating_mode: {tensor, vector, scalar} — controls operand reuse and operator accessibility   # p.58
  weight_loading: {parallel, side, cascade} — selects weight-loading bandwidth/routing behavior   # pp.59-60
  shared_exponent: optional_8_bit_per_vector_input — enables block floating-point operands   # p.58
slots:
  multiplier: UNKNOWN   # p.58
parameters: 30 INT8 or 60 INT4 multipliers/block; three DOTs/block; 10 multipliers/DOT; cascade length up to 36 blocks; two weight banks; 3-cycle parallel load; 15-cycle side load per half plus 3 exponent clocks; 3 cycles per cascade-loaded weight set   # pp.58-60
results:
| metric | value | unit | technology / device | baseline | condition | page |
| peak throughput | 143 | INT8 TOPs / FP16 TFLOPs | Stratix 10 NX, node UNKNOWN (2021) | UNKNOWN | 600MHz | p.57 |
| peak throughput | 286 | INT4 TOPs / FP12 TFLOPs | Stratix 10 NX, node UNKNOWN (2021) | UNKNOWN | 600MHz | p.57 |
| power efficiency | 1-2 | TFLOPs/W | Stratix 10 NX, node UNKNOWN (2021) | UNKNOWN | INT8/FP16 typical use | p.60 |
| power efficiency | 2-4 | TFLOPs/W | Stratix 10 NX, node UNKNOWN (2021) | UNKNOWN | INT4/FP12 typical use | p.60 |
| Design 1 FMax | 440 | MHz | Stratix 10 NX, node UNKNOWN (2021) | UNKNOWN | 2541 AI blocks, 115K MACs | p.65 |
| Design 1 throughput | 50 | TOPs | Stratix 10 NX, node UNKNOWN (2021) | UNKNOWN | 7x32 PE, 8 multipliers/block | p.65 |
| Design 1 ALMs | 82,828 (12%) | ALMs | Stratix 10 NX, node UNKNOWN (2021) | UNKNOWN | chip-scale array | p.65 |
| Design 1 AI blocks | 2541 (64%) | blocks | Stratix 10 NX, node UNKNOWN (2021) | UNKNOWN | chip-scale array | p.65 |
| Design 1 M20Ks | 1050 (15%) | M20Ks | Stratix 10 NX, node UNKNOWN (2021) | UNKNOWN | chip-scale array | p.65 |
| Design 2 FMax | 400 | MHz | Stratix 10 NX, node UNKNOWN (2021) | Design 1 | 3528 AI blocks, 206K MACs | p.65 |
| Design 2 throughput | 78 | TOPs | Stratix 10 NX, node UNKNOWN (2021) | Design 1 | all 10 multipliers used | p.65 |
| Design 2 ALMs | 132,307 (19%) | ALMs | Stratix 10 NX, node UNKNOWN (2021) | Design 1 | chip-scale array | p.65 |
| Design 2 AI blocks | 3528 (89%) | blocks | Stratix 10 NX, node UNKNOWN (2021) | Design 1 | chip-scale array | p.65 |
| Design 2 M20Ks | 1617 (24%) | M20Ks | Stratix 10 NX, node UNKNOWN (2021) | Design 1 | chip-scale array | p.65 |
errors_and_checks: none
conditions: Tensor mode requires operand reuse because the interface cannot service all multipliers with independent operands each cycle (p.58). Cascade loading minimizes routed weight buses but sacrifices the first block for loading and loads slowly; side loading permits concurrent compute but routes a 16-bit bus to every block (pp.59-60). Full-chip arrays stress long wires while leaving most short/opposite-direction wires available (pp.65-66).
evidence: §2.3, Figures 1-3, Table 1, §6, Tables 3-5, Figures 8-11.

### block_fp_accumulation  (role: instantiates)
mechanism: An optional shared 8-bit exponent is applied to each vector input before each 10-element dot product. Fixed-point dot sums are converted to FP32 and then cascaded or accumulated by FP32 ALUs. BFP16/BFP24 modes permit all three terminal accumulators to reside in one block, while block FP16/FP12 provide the advertised low-precision throughput modes (pp.57-60).
choices:
  block_size: 10 [outside domain]   # p.58
  mantissa_bits: 8   # p.58
  mantissa_bits: 4   # p.58
  exponent_sharing_granularity: block   # p.58
  inter_block_accumulate: fp32   # pp.58-60
new_choices:
  exponent_width_bits: 8 — width of the optional exponent shared by a vector input   # p.58
slots:
  mul: UNKNOWN   # p.58
  reduction: UNKNOWN   # p.58
parameters: three 10-element dot products/block; optional 8-bit shared exponent per vector input; INT32 or FP32 output/cascade; BFP16/BFP24 terminal accumulation modes   # pp.58-60
results:
| metric | value | unit | technology / device | baseline | condition | page |
| peak throughput | 143 | FP16 TFLOPs | Stratix 10 NX, node UNKNOWN (2021) | UNKNOWN | block FP16 at 600MHz | p.57 |
| peak throughput | 286 | FP12 TFLOPs | Stratix 10 NX, node UNKNOWN (2021) | UNKNOWN | block FP12 at 600MHz | p.57 |
errors_and_checks: The paper does not report a numerical error contract for block FP12/FP16/BFP24 (pp.57-60).
conditions: Shared-exponent operation targets matrix/vector AI calculations, and terminal accumulator placement depends on output width (pp.58-60).
evidence: Abstract, §2.3, Figures 1-3.

### piecewise_poly  (role: instantiates)
mechanism: The mapped sigmoid datapath takes |x|, performs interval selection, selects C2/C1/C0 coefficients, evaluates a fused arithmetic core, and reconstructs the sign/result. Variants reduce mantissa-multiplier widths or change adder C to BFP24 to trade resource use and latency for ulp accuracy (pp.63-64).
choices:
new_choices:
  arithmetic_precision_configuration: {full_fp32, reduced_A_mantissa, reduced_A_mantissa_and_BFP24_C} — selects multiplier/adder widths for area/latency/accuracy tradeoffs   # p.63
slots:
  range_reducer: UNKNOWN   # p.64
  evaluator: UNKNOWN   # p.64
  segmenter: UNKNOWN   # p.64
parameters: sigmoid range [-8,8] for FP16 and [-16,16] for FP32; reduced A inputs {wE=8, wF=13}; reduced BFP24 variant uses a 16x24 mantissa multiplier   # p.63
results:
| metric | value | unit | technology / device | baseline | condition | page |
| sigmoid latency | 16 | cycles | Stratix 10 NX, node UNKNOWN (2021) | UNKNOWN | FP16 | p.63 |
| sigmoid resources | 211 ALMs, 4 AIs, 0 M20Ks | resources | Stratix 10 NX, node UNKNOWN (2021) | UNKNOWN | FP16 | p.63 |
| sigmoid frequency | 550 | MHz | Stratix 10 NX, node UNKNOWN (2021) | UNKNOWN | FP16 | p.63 |
| sigmoid latency | 39 | cycles | Stratix 10 NX, node UNKNOWN (2021) | UNKNOWN | full-accuracy FP32 † | p.63 |
| sigmoid resources | 501 ALMs, 10 AIs, 4 M20Ks | resources | Stratix 10 NX, node UNKNOWN (2021) | UNKNOWN | full-accuracy FP32 † | p.63 |
| sigmoid maximum error | 4 | ulps | Stratix 10 NX, node UNKNOWN (2021) | UNKNOWN | full-accuracy FP32 † | p.63 |
| sigmoid latency | 36 | cycles | Stratix 10 NX, node UNKNOWN (2021) | FP32 † | reduced A mantissa ‡ | p.63 |
| sigmoid resources | 426 ALMs, 8+1/3 AIs, 4 M20Ks | resources | Stratix 10 NX, node UNKNOWN (2021) | FP32 † | reduced A mantissa ‡ | p.63 |
| sigmoid maximum error | 6 | ulps | Stratix 10 NX, node UNKNOWN (2021) | FP32 † | reduced A mantissa ‡ | p.63 |
| sigmoid latency | 34 | cycles | Stratix 10 NX, node UNKNOWN (2021) | FP32 ‡ | BFP24 adder C § | p.63 |
| sigmoid resources | 382 ALMs, 6+1/2 AIs, 4 M20Ks | resources | Stratix 10 NX, node UNKNOWN (2021) | FP32 ‡ | BFP24 adder C § | p.63 |
| sigmoid maximum error | 9 | ulps | Stratix 10 NX, node UNKNOWN (2021) | FP32 ‡ | BFP24 adder C § | p.63 |
| sigmoid frequency | 550 | MHz | Stratix 10 NX, node UNKNOWN (2021) | UNKNOWN | all FP32 variants | p.63 |
| tanh latency | 16 | cycles | Stratix 10 NX, node UNKNOWN (2021) | UNKNOWN | FP16 | p.63 |
| tanh resources | 154 ALMs, 4 AIs, 0 M20Ks | resources | Stratix 10 NX, node UNKNOWN (2021) | UNKNOWN | FP16 | p.63 |
| tanh frequency | 550 | MHz | Stratix 10 NX, node UNKNOWN (2021) | UNKNOWN | FP16 | p.63 |
| tanh latency | 47 | cycles | Stratix 10 NX, node UNKNOWN (2021) | UNKNOWN | FP32 | p.63 |
| tanh resources | 705 ALMs, 14 AIs, 3 M20Ks | resources | Stratix 10 NX, node UNKNOWN (2021) | UNKNOWN | FP32 | p.63 |
| tanh frequency | 550 | MHz | Stratix 10 NX, node UNKNOWN (2021) | UNKNOWN | FP32 | p.63 |
errors_and_checks: Sigmoid variants report maximum errors of 4 ulps, 6 ulps, and 9 ulps; no error figure is reported for tanh (p.63).
conditions: Full IEEE754 compliance is optional for the reduced-resource variants, and the 550MHz result is capped by the Quartus 20.3 restriction applied to AI Tensor Blocks (p.63).
evidence: §5, Table 2, Figures 6-7.

## new_families
### tensor_block_aggregated_multiplier  (domain: mul: integer multipliers, closest: segmented_grid, why_not: segmented_grid fixes 16-bit operand segmentation and a CPA merge, while this mechanism composes hard dot-product blocks with either soft-logic or FP32 accumulation)
mechanism: An INT15 operand is split into signed INT8 upper and unsigned UINT7 lower parts. Four INT8 products form (ac ≪ 14) + ((ad + cb) ≪ 7) + bd, with shifted dot-product outputs summed in soft logic. Larger constructions instead apply shared exponents to partial-product groups, convert them to FP32 inside the block, and sum them through embedded FP32 adders. The paper also describes approximate FP32 multiplication using nine INT8 multipliers for a 20-bit mantissa or six when LSB accuracy is relaxed (pp.61-63).
choices: component_width: {int4, int8}; composition: {soft_logic_shift_sum, shared_exponent_fp32_sum}; target: {integer, floating_point}; vectorized_dot_construction: Bool
results:
| metric | value | unit | technology / device | baseline | condition | page |
| component count | 4 | INT8 multipliers/INT15 multiplier | Stratix 10 NX, node UNKNOWN (2021) | UNKNOWN | INT15 construction | pp.61-62 |
| component count | 9 | INT8 multipliers | Stratix 10 NX, node UNKNOWN (2021) | full IEEE754 FP32 using 16 INT8 multipliers | approximately 20-bit mantissa | p.61 |
| component count | 6 | INT8 multipliers | Stratix 10 NX, node UNKNOWN (2021) | full IEEE754 FP32 using 16 INT8 multipliers | relaxed LSB accuracy | p.61 |
evidence: §4, Figures 4-5.

## space_gaps
* `ai_tensor_block.dot_width` excludes the implemented value 10 (p.58).
* `ai_tensor_block` lacks operating-mode, weight-loading, shared-exponent-width, and maximum-cascade-length choices (pp.58-60).
* `ai_tensor_block.element_format` does not distinguish shared-exponent block FP12/FP16 from IEEE FP formats (pp.57-58).
* No existing multiplier family represents aggregation of hard tensor dot-product blocks into wider integer/floating-point multipliers (pp.61-63).

## open_questions
* The internal microarchitecture of each INT8/INT4 multiplier and dot-product reduction network is not disclosed.
* The exact sign/exponent/fraction layouts of FP12 block, FP16 block, and BFP24 are not defined.
* The sigmoid/tanh segment count, polynomial degree, coefficient encoding, and evaluator structure are not stated explicitly.
* The process node for the reported Stratix 10 NX implementation is not stated explicitly.
