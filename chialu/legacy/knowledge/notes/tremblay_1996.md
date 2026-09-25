---
handle: tremblay_1996
citation: M. Tremblay, J. M. O'Connor, V. Narayanan, L. He, "VIS Speeds New Media Processing", IEEE Micro, vol. 16, no. 4, pp. 10-20, 1996
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU, VEC_DOT_ACC, other]
formats: [uint8, int16, int32, fixed8, fixed16, fixed32]
authority: landmark
pages_read: 11 / 11
---

## summary
VIS adds packed fixed-point arithmetic, conversion, comparison, alignment, masking, multiplication, and sum-of-absolute-differences instructions to UltraSPARC. A 64-bit datapath operates on eight 8-bit, four 16-bit, or two 32-bit components, while specialized instructions handle multimedia boundary and addressing costs. Measured convolution, dot-product, motion-estimation, and trilinear-interpolation kernels run from more than two to 7.5 times as fast as corresponding C implementations.

## families
### replicated_lanes  (role: instantiates)
mechanism: VIS stores packed operands in the floating-point register file and applies arithmetic/logical operations to independent 8-, 16-, or 32-bit components. Partitioned add/subtract instructions process four 16-bit or two 32-bit lanes. Four 8x16-bit multiplier subunits process four products concurrently, while fpmerge interleaves two sets of four 8-bit values.
choices:
  register_file: fp_shared   # p.11
  rearrangement: mix_permute   # pp.12-13
new_choices:
  none
slots:
  none
parameters: 64-bit packed datapath; 8x8-bit, 4x16-bit, or 2x32-bit components; four 8x16-bit multiplier subunits; add/subtract latency/throughput 1/1 cycles   # pp.10-12
results:
| metric | value | unit | technology / device | baseline | condition | page |
| add/subtract latency/throughput | 1/1 | cycles | UltraSPARC (node UNKNOWN), 1996 | none | four 16-bit or two 32-bit lanes | p.11 |
| VIS implementation area | 3 | % of UltraSPARC I die | UltraSPARC I (node UNKNOWN), 1995 | UltraSPARC I die | first VIS implementation | p.12 |
| convolution cycles/pixel, C / VIS | 43.64 / 8.29 | cycles/pixel | UltraSPARC-based system (node UNKNOWN), 1996 | optimized C | 256x256 image, 3x3 separable kernel | p.17 |
| convolution cycles/pixel, C / VIS | 42.77 / 8.23 | cycles/pixel | UltraSPARC-based system (node UNKNOWN), 1996 | optimized C | 512x512 image, 3x3 separable kernel | p.17 |
| convolution cycles/pixel, C / VIS | 79.05 / 15.10 | cycles/pixel | UltraSPARC-based system (node UNKNOWN), 1996 | optimized C | 1,024x1,024 image, 3x3 separable kernel | p.17 |
| aligned dot-product speedup | 7.5 | times | UltraSPARC-based system (node UNKNOWN), 1996 | C, 8,212 cycles | N=1,024; VIS uses 1,098 cycles | pp.17-18 |
| unaligned dot-product cycles, C / VIS | 8,243 / 3,671 | cycles | UltraSPARC-based system (node UNKNOWN), 1996 | C | N=1,024 | pp.17-18 |
errors_and_checks: none
conditions: SIMD speedup depends on algorithms operating on short integer/fixed-point components and can be limited by boundary handling. The dot-product result improves from more than two times for unaligned data to 7.5 times for 8-byte-aligned data. Minimizing loads/stores is critical to convolution speedup.   # pp.10, 16-18
evidence: Table 1; Figures 2-4 and 8-11; Table 2, pp.11-18

### funnel  (role: instantiates)
mechanism: faligndata concatenates two 64-bit floating-point registers and extracts an eight-byte window at an offset previously placed in the graphics status register by alignaddr.
choices:
  input_forming: two_register_pair   # p.13
  amount_preprocess: none   # p.13
new_choices:
  none
slots:
  none
parameters: 64-bit output window; three-bit byte offset; alignaddr and faligndata latency/throughput 1/1 cycles each   # pp.11, 13
results:
| metric | value | unit | technology / device | baseline | condition | page |
| alignaddr latency/throughput | 1/1 | cycles | UltraSPARC (node UNKNOWN), 1996 | none | aligned-access setup | p.11 |
| faligndata latency/throughput | 1/1 | cycles | UltraSPARC (node UNKNOWN), 1996 | none | unaligned-data extraction | p.11 |
errors_and_checks: none
conditions: alignaddr/faligndata emulate an unaligned 64-bit load from two aligned loads.   # p.13
evidence: Table 1 and address-handling-instructions section, pp.11, 13

### vector_lane_masking  (role: instantiates)
mechanism: Pixel comparisons and edge instructions generate per-component masks in an integer register. Partial-store instructions use the mask to update selected 8-, 16-, or 32-bit components while preserving unselected memory locations.
choices:
  mask_storage: integer_register [outside domain]   # pp.13-14
  masked_write: merge_preserve_old   # pp.13-14
new_choices:
  none
slots:
  none
parameters: masks for 8-, 16-, and 32-bit components; comparisons cover four 16-bit or two 32-bit pairs; partial-store latency/throughput 1/1 cycles   # pp.11, 13-14
results:
| metric | value | unit | technology / device | baseline | condition | page |
| compare latency/throughput | 1/1 | cycles | UltraSPARC (node UNKNOWN), 1996 | none | four 16-bit or two 32-bit comparisons | p.11 |
| partial-store latency/throughput | 1/1 | cycles | UltraSPARC (node UNKNOWN), 1996 | none | mask-selected lane writes | p.11 |
errors_and_checks: none
conditions: Edge-generated masks remove branchy boundary code, and unselected memory locations remain unchanged.   # pp.13-14
evidence: Table 1 and address/memory-access sections, pp.11, 13-14

## new_families
### partitioned_mixed_width_multiplier  (domain: mul: integer multipliers, closest: twin_precision_subword, why_not: twin_precision_subword assumes one matrix partitioned into same-width products, while VIS specifies four 8x16-bit subunits and multi-instruction 16x16 composition)
mechanism: Four 8x16-bit multiplier subunits compute pairwise or distributed products. Instructions select corresponding 16-bit operands or one shared 16-bit operand. Separate signed-upper and unsigned-lower products combine with a partitioned add to synthesize 16x16-bit products with either 16- or 32-bit results.
choices:
  lane_shape: {8x16}   # p.12
  lane_count: {4}   # p.12
  result_form: {upper_16_bits, composed_32_bits}   # pp.12, 17
  full_width_composition: {three_instruction_sequence}   # pp.12, 17
results:
| metric | value | unit | technology / device | baseline | condition | page |
| multiply latency/throughput | 3/1 | cycles | UltraSPARC (node UNKNOWN), 1996 | none | partitioned 8x16 instruction | p.11 |
| multiplier-array size reduction | 50 | % | UltraSPARC (node UNKNOWN), 1996 | full 16x16-bit subunits | four 8x16-bit subunits | p.12 |
evidence: Table 1; partitioned-multiply discussion; Figures 3, 4, and 11, pp.11-13, 17-18

### simd_sum_absolute_differences  (domain: dot: dot-product / FMA / MAC, closest: integer_mac, why_not: the operation accumulates absolute differences rather than products)
mechanism: pdist computes absolute differences between eight corresponding 8-bit components in two 64-bit registers and accumulates their sum into an accumulator. A 16x16-pixel comparison uses 32 pdist instructions.
choices:
  lane_count: {8}   # pp.14, 18
  element_width_bits: {8}   # pp.14, 18
  accumulation: {sum_of_absolute_differences}   # pp.14, 18
results:
| metric | value | unit | technology / device | baseline | condition | page |
| pdist latency/throughput | 3/1 | cycles | UltraSPARC (node UNKNOWN), 1996 | none | eight 8-bit pairs | p.11 |
| motion-estimation cycles, C / VIS | 2,429 / 441 | cycles | UltraSPARC-based system (node UNKNOWN), 1996 | C | two 16x16-pixel blocks | p.18 |
| motion-estimation speedup | 5.5 | times | UltraSPARC-based system (node UNKNOWN), 1996 | C | two 16x16-pixel blocks | p.18 |
evidence: Table 1; Figure 7; Figure 12 and accompanying measurements, pp.11, 14, 18

### blocked_3d_address_generator  (domain: shift: shifters, closest: funnel, why_not: the array instruction reorders packed x/y/z coordinate bits into a blocked-byte memory offset rather than selecting a data window)
mechanism: The array instruction accepts three fixed-point coordinates packed into one 64-bit integer register, discards fractional bits, and reorders integer bits into a blocked-byte offset. The layout groups voxels into 4x4x2 bricks so neighboring x/y/z samples occupy fewer cache lines.
choices:
  coordinate_form: {packed_xyz_fixed_point}   # pp.14, 19
  block_shape: {4x4x2}   # p.14
  component_width_bits: {8, 16, 32}   # pp.11, 13-14
results:
| metric | value | unit | technology / device | baseline | condition | page |
| average cache lines, conventional / blocked | 4-1/8 / 2-1/8 | cache lines/interpolation | UltraSPARC-based system (node UNKNOWN), 1996 | linear volume layout | 16-bit voxels, trilinear neighborhood | p.19 |
| trilinear cycles, C / VIS | 296 / 138 | cycles/interpolation | UltraSPARC-based system (node UNKNOWN), 1996 | typical C | blocked-byte layout | p.19 |
| optimized VIS loop | 40 | cycles/interpolation | UltraSPARC-based system (node UNKNOWN), 1996 | none | hand-coded/pipelined loop | p.19 |
evidence: Figures 5, 6, and 13-15; array-instruction and trilinear-interpolation sections, pp.13-19

## space_gaps
* vector_lane_masking.mask_storage lacks the document's integer-register mask value.   # pp.13-14
* The vocabulary lacks a mixed-width partitioned multiplier whose four 8x16-bit products compose 16x16-bit results through multiple instructions.   # pp.12, 17
* The vocabulary lacks a SIMD sum-of-absolute-differences accumulator for motion estimation.   # pp.14, 18
* The vocabulary lacks a packed-coordinate blocked-byte address generator for 3D neighborhoods.   # pp.14, 19

## open_questions
* The article states that hardware implementation is described elsewhere, so the adder carry-boundary mechanism, multiplier reduction structure, saturation circuitry, and physical pipeline implementation remain unspecified.   # p.10
* The benchmark system is identified only as UltraSPARC-based, so its exact processor revision and technology node are unknown.   # p.16
