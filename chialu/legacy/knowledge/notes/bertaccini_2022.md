---
handle: bertaccini_2022
citation: L. Bertaccini, G. Paulin, T. Fischer, S. Mach, L. Benini, "MiniFloat-NN and ExSdotp: An ISA Extension and a Modular Open Hardware Unit for Low-Precision Training on RISC-V Cores", ARITH, 2022
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_DOT_ACC]
formats: [fp8, fp8alt, fp16, fp16alt, fp32, fp64]
authority: incremental
pages_read: 1-10 / 10
---

## summary
The document proposes a parameterized SIMD ExSdotp unit that computes two low-precision products plus a wider accumulator with one normalization/rounding step (p.1, p.4). The same datapath computes expanding/non-expanding three-term additions and supports FP8-to-FP16 and FP16-to-FP32 operations (p.4-5). An eight-core 12 nm RISC-V cluster reaches 160 GFLOPS peak and 575 GFLOPS/W for FP8-to-FP16 GEMMs (p.7-9).

## families
### mixed_precision_cascade_fma  (role: proposes)
mechanism: Four w-bit operands form two full-precision mantissa products, which are zero-padded to the 2w destination precision and combined with a 2w accumulator. The exponent path sorts the three addends by absolute value. Two additions use progressively wider internal representations before one normalization and rounding step, which preserves shifted information during cancellation. Setting two multiplicands to one reuses the datapath for ExVsum; bypassing both multipliers provides Vsum (p.4-5).
choices:
  exact_product_preserved: true   # p.4-5
  two_term_expansion_output: false   # p.4
new_choices:
  operation_shape: {exsdotp, exvsum, vsum} — selects two-product accumulation, expanding three-term addition, or non-expanding three-term addition   # p.5-6
  simd_parallelism: {4x_8_to_16, 2x_16_to_32} — selects the packed operations completed per cycle through the 64-bit FPU interface   # p.5
slots:
  align: full_align   # p.4-5
parameters: four w-bit multiplicands plus one 2w-bit accumulator; FP8/FP8alt-to-FP16/FP16alt and FP16/FP16alt-to-FP32; two 16-to-32-bit plus two 8-to-16-bit modules; II=1; SDOTP pipeline stages=3 in the evaluated PE   # p.4-6
results:
| metric | value | unit | technology / device | baseline | condition | page |
| area reduction | around 30 | % | GlobalFoundries 12 nm FinFET / 2022 | two cascaded ExFMA units | standalone unpipelined unit at 333 MHz; ExFMAs constrained to 667 MHz | p.6 |
| critical-path reduction | around 30 | % | GlobalFoundries 12 nm FinFET / 2022 | two cascaded ExFMA units | standalone unpipelined unit at 333 MHz | p.6 |
| ExSdotp SIMD area | 44.5 | kGE | GlobalFoundries 12 nm FinFET / 2022 | none | placed-and-routed extended FPU | p.6 |
| ExSdotp share of FPU area | 27 | % | GlobalFoundries 12 nm FinFET / 2022 | 165 kGE FPU | placed-and-routed extended FPU | p.6 |
| ExSdotp FPU area | 0.019 | mm2 | GlobalFoundries 12 nm FinFET / 2022 | FPnew: 0.049 mm2 at 22 nm | 0.8 V, 1.26 GHz | p.7 |
| ExSdotp FPU peak throughput | 20.2 | GFLOPS | GlobalFoundries 12 nm FinFET / 2022 | FPnew: 14.8 GFLOPS | expanding FP8 | p.7 |
| ExSdotp FPU peak efficiency | 1631 | GFLOPS/W | GlobalFoundries 12 nm FinFET / 2022 | FPnew: 1245 GFLOPS/W | expanding FP8 at 0.8 V | p.7 |
| cluster area | 0.52 | mm2 | GlobalFoundries 12 nm FinFET / 2022 | Snitch: 0.66 mm2 at 22 nm | eight enhanced compute cores | p.7 |
| cluster peak throughput | 160 | GFLOPS | GlobalFoundries 12 nm FinFET / 2022 | Snitch: 16 GFLOPS FP64 | expanding FP8 | p.7 |
| measured GEMM throughput | 128 | GFLOPS | GlobalFoundries 12 nm FinFET / 2022 | none | 128×256 FP8-to-FP16 GEMM, 1.26 GHz | p.8 |
| measured cluster power | 224 | mW | GlobalFoundries 12 nm FinFET / 2022 | none | 128×256 FP8-to-FP16 GEMM, 0.8 V, 25 °C | p.8 |
| measured cluster efficiency | 575 | GFLOPS/W | GlobalFoundries 12 nm FinFET / 2022 | Snitch: 80 GFLOPS/W for FP64 | 128×256 FP8-to-FP16 GEMM, 0.8 V, 1.26 GHz | p.8 |
errors_and_checks: Relative error against an FP64 accumulation converted to the destination format is FP16-to-FP32: 0, 1.1 × 10-7, and 5.4 × 10-7 for n=500, 1000, and 2000; FP8-to-FP16: 5.9 × 10-4, 2.7 × 10-3, and 3.9 × 10-3. The corresponding ExFMA errors are 7.6 × 10-7, 1.8 × 10-6, 9.9 × 10-7 and 5.9 × 10-4, 8.2 × 10-3, 1.2 × 10-2 (p.7-8).
conditions: The fused unit avoids the double rounding and addition-order sensitivity of cascaded ExFMAs (p.3-5). The SIMD packing doubles peak computation relative to expanding FMAs, while setup overhead limits the realized speedup for small GEMMs (p.7). ExSdotp supports only the documented 8-to-16-bit and 16-to-32-bit format combinations; the extended FPU disables division/square root (p.4-5).
evidence: §III-A-III-E, Table I, Figs. 3-5, §IV-A-IV-E, Tables II-IV, Figs. 7-9 (p.3-9)

### fused_two_term_dot  (role: extends)
mechanism: ExSdotp extends a fused two-product dot operation with a wider accumulator, computing aw × bw + cw × dw + e2w. The products and accumulator are sorted by magnitude and added at increasing internal widths before one normalization/rounding step. An exact-zero detector on the first sum restores the minimum addend directly when cancellation would otherwise discard useful shifted bits (p.4-5).
choices:
  second_op: dot2   # p.3-4
new_choices:
  fused_accumulator_addend: true — includes e2w in the same unrounded datapath as both products   # p.3-4
slots:
  align: full_align   # p.4-5
parameters: two products plus one accumulator; source width w; destination width 2w; FP8-to-FP16 and FP16-to-FP32; one final normalization/rounding   # p.3-5
results:
| metric | value | unit | technology / device | baseline | condition | page |
| execution-cycle reduction | up to 10 | % | GlobalFoundries 12 nm FinFET / 2022 | FP16 FMA GEMM | FP16-to-FP32 ExSdotp GEMMs | p.7 |
| achieved performance ratio | 1.96 | × | GlobalFoundries 12 nm FinFET / 2022 | 128×128 FP16-to-FP32 GEMM | 128×256 FP8-to-FP16 GEMM | p.7 |
| achieved performance ratio | 7.23 | × | GlobalFoundries 12 nm FinFET / 2022 | 64×64 FP64 GEMM | 128×256 FP8-to-FP16 GEMM | p.7 |
errors_and_checks: The accuracy experiment uses Gaussian random source-format inputs and reports relative error against FP64; ExSdotp is more accurate than sequential ExFMAs for every tested FP16-to-FP32 and FP8-to-FP16 accumulation length (p.7-8).
conditions: Fusion provides one normalization/rounding step rather than the two rounds of a cascaded ExFMA implementation (p.3). Wider internal additions address cancellation, but the document does not claim correctly rounded dot products for all inputs (p.4-5, p.8).
evidence: Fig. 3, §III-B-III-C, Fig. 4, §IV-B, §IV-D, Table IV (p.3-8)

## new_families
none

## space_gaps
* `mixed_precision_cascade_fma` lacks a choice for a fused two-product-plus-accumulator operation and for ExVsum/Vsum reuse on the same datapath (p.4-5).
* `mixed_precision_cascade_fma` lacks a SIMD packing choice distinguishing four 8-to-16-bit operations from two 16-to-32-bit operations per cycle (p.5).

## open_questions
* The document does not identify the mantissa multiplier, carry-propagate adder, or final rounding circuit as a vocabulary family (p.4-5).
* The accuracy experiment does not report its random seed, trial count, or a worst-case error bound (p.7-8).
