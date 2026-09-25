---
handle: koenig_2017
citation: J. Koenig, D. Biancolin, J. Bachrach, K. Asanovic, "A Hardware Accelerator for Computing an Exact Dot Product", ARITH-24, pp. 114-121, 2017
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_DOT_ACC]
formats: [fp32, fp64]
authority: incremental
pages_read: 8 / 8
---

## summary
The document presents a Chisel-generated accelerator that exactly accumulates unrounded IEEE-754 products in a 640-bit or 4288-bit fixed-point complete register. Eight configurations compare segmented/centralized accumulators, L1/L2 interfaces, and fp32/fp64 support in a Rocket Chip SoC implemented in TSMC 45 nm. # p.114, p.118

## families
### kulisch_long_accumulator  (role: extends)
mechanism: Each mantissa product and exponent sum are computed in parallel, after which the exponent selects complete-register words and controls product alignment. The aligned unrounded product is accumulated in a signed fixed-point complete register. The segmented implementation assigns an adder to every segment and propagates latched carry/borrow between segments in later cycles. The centralized implementation stores the complete register in banked SRAM, shares one accumulator, and uses all_ones/all_zeros metadata to accelerate rare carry/borrow propagation beyond the accessed words. # p.115, p.117-p.118
choices:
  accumulator_width_bits: 640; 4288 # p.115
  organization: segmented_lazy_carry; centralized_sram [outside domain] # p.117-p.118
  carry_resolution: carry_save_deferred # p.117-p.119
new_choices:
  cache_interface: {L1, L2} — selects a 64-bit or 128-bit cache interface and its available operand bandwidth # p.116, p.118
  complete_register_storage: {segment_registers, centralized_banked_sram} — selects distributed register storage or one shared memory-backed register # p.117-p.118
slots:
  none
parameters: fp32 uses a 640-bit complete register organized as 10 × 64-bit words with k = 86; fp64 uses a 4288-bit complete register organized as 67 × 64-bit words with k = 92. The centralized fp64 accumulator uses four SRAM banks, four selected words, a 104-bit summand zero-padded to 192 bits, and a shared accumulation datapath. The generator exposes segmented/centralized organization, L1/L2 attachment, fp32/fp64 support, and parameterized front-end pipeline latency. # p.115, p.117-p.119
results:
| metric | value | unit | technology / device | baseline | condition | page |
| area | 0.05 to 0.32 | mm2 | TSMC 45 nm, 2017 | none | range across eight accelerator configurations | p.114 |
| frequency | in excess of 900 | MHz | TSMC 45 nm, 2017 | none | all configurations | p.114 |
| accelerator area share | 2.1 to 12.4 | % of total SoC area | TSMC 45 nm Rocket Chip SoC, 2017 | total SoC | all eight configurations | p.120 |
| accelerator area share | 6.4 | % of total SoC area | TSMC 45 nm Rocket Chip SoC, 2017 | total SoC | centralized complete register, L2 interface, fp64 operands | p.120 |
| clock period | 1.45 | ns | TSMC 45 nm Rocket Chip SoC, 2017 | none | all configurations with L2 critical path | p.120 |
| critical-path period | 1.24 | ns | TSMC 45 nm Rocket Chip SoC without L2, 2017 | none | centralized accumulator, SRAM output to SRAM input | p.120 |
| critical-path period | 1.09 | ns | TSMC 45 nm Rocket Chip SoC without L2, 2017 | none | segmented configuration, path through Rocket Chip FPU | p.120 |
| throughput | 1 | CPE | Rocket Chip accelerator / TSMC 45 nm, 2017 | Intel MKL with AVX on Xeon E5-2667 V2 | fp64 vectors at peak memory throughput | p.120 |
| speedup | approximately 3× | faster | Rocket Chip accelerator / TSMC 45 nm, 2017 | ReproBLAS on Xeon E5-2667 V2 | exact/reproducible dot-product comparison | p.120 |
errors_and_checks: Mantissa products are unrounded and accumulated without intermediate loss in the complete register. Additional k bits prevent accumulation overflow before machine failure under the stated sizing assumption. Final conversion supports only round towards zero; other rounding modes are not implemented. # p.114-p.116
conditions: The design applies when the fixed-point range can be bounded and operations on the wide representation can be restricted. L1 variants lose performance after vectors exceed L1 capacity because four outstanding 64-bit requests do not hide miss latency. Centralized accumulation stalls only for rare carry/borrow structural hazards, while segmented accumulation may require several completion cycles to propagate outstanding carry/borrow. One-product-per-cycle issue limits fp32 L2 throughput unless the datapath is duplicated. Cache blocking for BLAS-2/BLAS-3 must account for flushing/fetching the complete register, which reduces temporal reuse. # p.114-p.115, p.119-p.120
evidence: §III-A and steps 1-6; §III-F; §III-G and Figures 3-4; §IV-B; §V and Figures 5-8. # p.115-p.120

### behavioral_star  (role: instantiates)
mechanism: The front-end datapath expresses exponent addition, mantissa multiplication, and shifting with Chisel operators that map to equivalent Verilog HDL operators. Logic synthesis infers optimized implementations, and inserted output registers are retimed across the three modules to pipeline the datapath. # p.117
choices:
new_choices:
  none
slots:
  none
parameters: The multiplier handles fp32 or fp64 mantissas; front-end pipeline latency is parameterized. # p.117-p.119
results:
| metric | value | unit | technology / device | baseline | condition | page |
| --- | --- | --- | --- | --- | --- | --- |
errors_and_checks: The mantissa product is retained without rounding before accumulation. # p.114-p.115
conditions: The paper leaves the inferred multiplier topology open and reports no multiplier-only area/delay result. # p.117
evidence: §III-A and §III-F. # p.115, p.117

## new_families
none

## space_gaps
* `kulisch_long_accumulator.organization` lacks the centralized shared-adder/banked-SRAM organization. # p.117-p.118
* `kulisch_long_accumulator` lacks a slot for the unrounded input-product multiplier, which this design implements through synthesis-inferred multiplication. # p.115, p.117
* `kulisch_long_accumulator` lacks an output-rounding choice or slot; this implementation provides round towards zero after exact accumulation. # p.116

## open_questions
* Figure 8 plots accelerator areas for all eight configurations without tabulating exact per-configuration values, so only the printed range is recorded. # p.120
* The selected front-end pipeline latencies are not reported. # p.117
* The paper excludes infinities and NaNs from its benchmarks and does not fully specify their accelerator behavior. # p.118
