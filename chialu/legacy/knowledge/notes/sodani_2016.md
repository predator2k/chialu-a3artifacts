---
handle: sodani_2016
citation: A. Sodani, R. Gramunt, J. Corbal, H.-S. Kim, K. Vinod, S. Chinthamani, et al., "Knights Landing: Second-Generation Intel Xeon Phi Product", IEEE Micro, vol. 36, no. 2, pp. 34-46, 2016.
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU, VEC_SFU, VEC_DOT_ACC]
formats: [binary_integer, fp32, fp64]
authority: incremental
pages_read: 34-46 / 13
---

## summary
The document describes the shipped Knights Landing processor, including two 512-bit vector processing units per core and AVX-512 packed multiply-add/exponential/reciprocal operations. The document reports architectural throughput/latency but does not disclose arithmetic circuits, reduction structures, rounding paths, or technology node.

## families
### multi_precision_simd_fma  (role: instantiates)
mechanism: Each core connects to two mostly symmetrical VPUs. Each VPU can sustain one AVX-512 instruction per cycle, and one 512-bit instruction packs eight double-precision or 16 single-precision multiply-add operations. The document does not describe whether the multiply-add has a fused single-rounding datapath or how its multiplier/CPA/rounder are implemented.
choices:
  lane_split: 8x64_or_16x32 [outside domain]   # p.40
new_choices:
  none
slots:
  none
parameters: two VPUs per core; 512-bit vectors; eight fp64 or 16 fp32 multiply-add lanes per instruction; one AVX-512 instruction/cycle/VPU; most floating-point arithmetic latency 6 cycles   # pp.38, 40
results:
| metric | value | unit | technology / device | baseline | condition | page |
| steady-state instruction throughput | 1 | AVX-512 instruction/cycle/VPU | UNKNOWN / Knights Landing, 2016 | none | each VPU | p.38 |
| combined fp32 peak throughput | 64 | floating-point operations/cycle | UNKNOWN / Knights Landing, 2016 | none | both VPUs | p.38 |
| combined fp64 peak throughput | 32 | floating-point operations/cycle | UNKNOWN / Knights Landing, 2016 | none | both VPUs | p.38 |
| packed fp32 multiply-add work | 32 | flops/instruction | UNKNOWN / Knights Landing, 2016 | none | one AVX-512 instruction | p.40 |
| packed fp64 multiply-add work | 16 | flops/instruction | UNKNOWN / Knights Landing, 2016 | none | one AVX-512 instruction | p.40 |
| floating-point arithmetic latency | 6 | cycles | UNKNOWN / Knights Landing, 2016 | none | most floating-point arithmetic operations | p.38 |
| other floating-point operation latency | 2 or 3 | cycles | UNKNOWN / Knights Landing, 2016 | none | depends on operation type | p.38 |
| chip fp64 peak | more than 3 | Teraflops | UNKNOWN / Knights Landing, 2016 | none | chip peak | p.34 |
| chip fp32 peak | 6 | Teraflops | UNKNOWN / Knights Landing, 2016 | none | chip peak | p.34 |
errors_and_checks: none
conditions: The throughput figures apply to two mostly symmetrical VPUs, while one VPU additionally supports x87/MMX and a subset of byte/word SSE instructions. The reported preproduction application performance also includes core count/memory/interconnect effects and cannot be attributed to the FMA datapath alone.   # pp.38, 44-45
evidence: Core and VPU Architecture, pp.37-38; Instruction-Set Architecture, pp.39-40; Figure 3, p.37

### vector_lane_masking  (role: instantiates)
mechanism: AVX-512 provides true vector predication through eight mask registers. The document identifies the architectural mask storage but does not state inactive-lane write semantics, clock gating, or the physical mask implementation.
choices:
  mask_storage: dedicated_mask_register   # p.39
new_choices:
  none
slots:
  none
parameters: eight mask registers; 512-bit SIMD instructions   # p.39
results:
| metric | value | unit | technology / device | baseline | condition | page |
| mask-register count | 8 | registers | UNKNOWN / Knights Landing, 2016 | none | AVX-512 architectural state | p.39 |
errors_and_checks: none
conditions: The document establishes architectural predication support but does not establish whether masked lanes preserve old values, write zero, or receive physical clock gating.   # p.39
evidence: Instruction-Set Architecture, pp.39-40

## new_families
none

## space_gaps
* The `multi_precision_simd_fma.lane_split` domain lacks the documented 8x64 and 16x32 packed configurations.   # p.40
* `multi_precision_simd_fma` lacks a replication/issue-rate choice for two VPUs that each sustain one AVX-512 instruction per cycle.   # p.38

## open_questions
* The document calls the operations “multiply-add” but does not state whether multiplication and addition are fused with one rounding.   # p.40
* The document does not identify which operations occupy the 2-cycle, 3-cycle, and 6-cycle latency classes.   # p.38
* The document does not report the fabrication technology node for the arithmetic results.
