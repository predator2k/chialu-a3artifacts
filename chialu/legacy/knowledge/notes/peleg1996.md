---
handle: peleg1996
citation: A. Peleg, U. Weiser, "MMX Technology Extension to the Intel Architecture", IEEE Micro, vol. 16, no. 4, pp. 42-50, 1996
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU, VEC_DOT_ACC]
formats: [int8, int16, int32, int64]
authority: landmark
pages_read: 42-50 / 9
---

## summary
MMX extends IA with 64-bit packed-integer SIMD operations for multimedia and communications workloads. The architecture provides parallel arithmetic/comparison/shift/data-rearrangement operations, saturating arithmetic, and a packed multiply-add operation while reusing the floating-point register state. The paper reports instruction-level and application-level performance on a Pentium processor.

## families
### replicated_lanes  (role: proposes)
mechanism: MMX packs eight bytes, four 16-bit words, two 32-bit doublewords, or one quadword into a 64-bit register and applies one instruction to multiple elements in parallel. Packed operations include add/subtract, compare, multiply, shift, pack/unpack, and logic. Eight randomly accessed MMX registers reuse the IA floating-point registers, and EMMS marks the aliased floating-point stack empty after an MMX section. # pp.43-47
choices:
  register_file: fp_shared   # pp.45-46
  rearrangement: pack_unpack   # pp.44-45
new_choices:
  lane_shapes: {8x8, 4x16, 2x32, 1x64} — packed element counts and widths within a 64-bit register   # p.43
  state_reuse_protocol: floating_point_alias_with_emms — protocol for sharing MMX and floating-point register state   # pp.46-47
slots:
  none
parameters: 64-bit packed registers; eight MMX registers; 57 instructions; nonmultiply latency 1 cycle; multiply latency 3 cycles; multiply II 1 cycle   # pp.43-45
results:
| metric | value | unit | technology / device | baseline | condition | page |
| application performance | 1.5 to 2 | times faster | Pentium-class processor / 1996 | same application on the same processor without MMX | full applications | pp.42, 50 |
| computational inner-loop performance | 3 to 5 | times faster | Intel processors with MMX / 1996 | corresponding non-MMX code | SIMD-suitable inner loops/subroutines | p.50 |
| MPEG-1 decoding performance | 1.5 | times faster | Pentium-class processor / 1996 | same application on the same processor without MMX | cited MPEG-1 decoder | p.50 |
| image-filter performance | just over 4 | times faster | Pentium-class processor / 1996 | non-MMX implementation | assortment of image filters | p.50 |
| chroma-key throughput | 3/8 | cycles per pixel | Pentium processor microarchitecture / 1996 | almost 3 cycles per pixel with regular IA integer instructions | eight pixels processed in three cycles; on-chip-cache data; baseline assumes 85 percent correct branch prediction | p.49 |
errors_and_checks: none
conditions: MMX benefits routines with small packed data and exploitable data-level parallelism. # pp.42-43, 50 MMX code should use 64-bit-aligned memory accesses and shifts to realign data when needed. # pp.44-45 MMX and floating-point code cannot use the shared registers simultaneously, so transitions require explicit state discipline with EMMS. # p.46
evidence: Data types and Enhanced instruction set, pp.43-45; FU and register mapping, pp.45-47; Performance examples, pp.47-50; Tables 1-2; Figures 1, 5.

### saturating_clamp  (role: proposes)
mechanism: Packed add/subtract instructions provide wraparound, signed-saturation, and unsigned-saturation variants. Saturating operations replace an overflowing or underflowing result with the largest or smallest representable value for the element type. Saturation is encoded by the instruction rather than enabled as a processor mode. # pp.43-44
choices:
  per_lane: true   # p.44
new_choices:
  saturation_signedness: {signed, unsigned} — selects signed or unsigned representable limits   # p.44
  overflow_policy: {wraparound, saturate} — selects truncating wraparound or clamping semantics   # pp.43-44
slots:
  none
parameters: packed byte/word/doubleword add and subtract; byte limits FFh/OOh for unsigned and 7Fh/80h for signed values   # p.44
results:
| metric | value | unit | technology / device | baseline | condition | page |
| packed add/subtract latency | 1 | cycle | Pentium processor / 1996 | UNKNOWN | wraparound or saturating instruction | pp.43-44 |
errors_and_checks: Saturating results clamp to the signed or unsigned type limits; the paper reports no approximation error or concurrent fault checking. # pp.43-44
conditions: Saturation prevents wraparound artifacts in overflow-sensitive visual algorithms and removes explicit overflow/underflow checks. # p.43 Saturation applies only to instructions whose operation specifies it rather than globally to every arithmetic instruction. # p.43
evidence: Enhanced instruction set and packed addition/subtraction discussion, pp.43-44; Table 1.

### pairwise_tree  (role: instantiates)
mechanism: PMADDWD multiplies four corresponding signed 16-bit elements to produce four 32-bit products and adds adjacent product pairs into two 32-bit results. A following PADDD can combine those pair sums with an accumulator or complete a larger dot-product reduction. # pp.44, 48
choices:
  per_level_truncation: false   # p.44
new_choices:
  product_grouping: adjacent_pairs — PMADDWD adds products zero/one and two/three into separate 32-bit results   # pp.44, 48
slots:
  mul: UNKNOWN   # p.44
  accum: binary_tree   # pp.44, 48
parameters: four signed 16x16 multiplications; four 32-bit products; two adjacent 32-bit pair sums; instruction latency 3 cycles; II 1 cycle   # pp.43-44
results:
| metric | value | unit | technology / device | baseline | condition | page |
| 16-element dot-product instruction count | 19 | instructions | Pentium processor microarchitecture / 1996 | 76 regular integer or floating-point instructions | signed 16-bit inputs; 32-bit accumulation; loop unrolling | p.48 |
| 16-element dot-product cycle count | 12 | cycles | Pentium processor microarchitecture / 1996 | 74 cycles floating-point; just over 200 cycles integer | data/instructions in on-chip caches; both pipelines used | p.48 |
| 16-element dot-product speedup | 6 | times | Pentium processor microarchitecture / 1996 | floating-point optimized assembly | same cache and pipeline assumptions | p.48 |
| 16x16 matrix-vector instruction count | 316 | instructions | Pentium processor microarchitecture / 1996 | 1,228 floating-point instructions | four vector dot products per unrolled iteration | p.48 |
| 16x16 matrix-vector cycle count | 207 | cycles | Pentium processor microarchitecture / 1996 | just under 1,200 cycles for floating-point optimized code | four vector dot products per unrolled iteration | p.48 |
| 16x16 matrix-vector speedup | 5.8 | times | Pentium processor microarchitecture / 1996 | floating-point optimized code | full matrix-vector multiply | p.48 |
errors_and_checks: PMADDWD preserves 32-bit products and uses 32-bit pair sums; the paper reports no approximation error or fault checking. # p.44
conditions: PMADDWD accepts signed 16-bit elements and returns packed 32-bit pair sums. # p.44 MMX lacks a three-operand MAC instruction, so PADDD supplies the remaining accumulation step. # p.48 Loop unrolling is required to obtain one SIMD multiply initiation per cycle. # pp.43-44
evidence: Packed multiplications, p.44; Figure 2; Table 1; Figures 6-7; Performance examples, pp.47-48.

## new_families
none

## space_gaps
* replicated_lanes lacks a lane-shape choice for the documented 8x8/4x16/2x32/1x64 packed organizations. # p.43
* replicated_lanes lacks a state-aliasing protocol choice for sharing physical registers with the floating-point stack and restoring empty tags through EMMS. # pp.46-47
* pairwise_tree lacks a product-grouping choice for the adjacent-pair reduction performed by PMADDWD. # pp.44, 48
* saturating_clamp lacks signedness and wraparound-versus-saturation choices exposed by the packed add/subtract instruction variants. # pp.43-44

## open_questions
* The paper does not identify the multiplier, adder, carry-isolation, saturation-detection, or clamp-selection circuits used in the Pentium implementation.
* The paper does not state a semiconductor technology node, die-area increment, power, energy, or clock frequency.
* The paper describes PMADDWD instruction semantics but does not establish whether its internal product reduction uses a binary tree, carry-save tree, or another physical topology.
