---
handle: krithivasan2003
citation: S. Krithivasan, M. J. Schulte, "Multiplier Architectures for Media Processing", 37th Asilomar Conference on Signals, Systems and Computers, pp. 2193-2197, 2003
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU, VEC_DOT_ACC]
formats: [uint8, int8, uint16, int16, uint32, int32]
authority: incremental
pages_read: 2193-2197 / 5
---

## summary
The paper proposes a non-Booth subword-parallel tree multiplier that performs one 32 x 32-bit, two 16 x 16-bit, or four 8 x 8-bit multiplications. The multiplier supports unsigned/two's-complement operands and reuses one counter tree/carry-propagate adder across all subword sizes. A unified multioperand-adder extension supports subword sums/dot products and an optional accumulator.

## families
### twin_precision_subword  (role: proposes)
mechanism: The multiplier maps each active subword product onto a nonoverlapping region of one 32-bit partial-product matrix. Operand-derived control signals set partial-product bits outside the active regions to zero before counter-tree reduction. Conditional partial-product inversions, inserted `1` bits, and conditional product-bit inversions support unsigned/two's-complement operation. The mapping implicitly prevents carries from overflowing into higher-order subword products, so the design needs no boundary carry detection/suppression and reuses the same parallel-counter tree and final carry-propagate adder in every mode.
choices:
  partition: halves_and_quarters [outside domain]   # p.2194
  base_scheme: combined_unsigned_twos_complement_non_booth [outside domain]   # pp.2193-2195
  per_lane_signed: false   # pp.2194-2195
new_choices:
  partial_product_partitioning: zero_inactive_matrix_regions — selects products by zeroing partial-product regions outside each active subword multiplication   # pp.2194-2195
slots:
  lane_cpa: carry_lookahead   # p.2195
parameters: 32-bit operands; one 32 x 32-bit, two 16 x 16-bit, or four 8 x 8-bit products; unsigned/two's-complement formats; `sw8`/`sw16` mode controls   # p.2194
results:
| metric | value | unit | technology / device | baseline | condition | page |
| area | 0.117 | mm² | LSI Logic G11 0.11 micron CMOS standard cell library; 2003 | Tree Multiplier, 0.108 mm² | 32-bit combined subword-parallel multiplier; delay-optimized; maximum fan-out 4; 2.5 V; 25° C | p.2197 |
| delay | 2.96 | ns | LSI Logic G11 0.11 micron CMOS standard cell library; 2003 | Tree Multiplier, 2.68 ns | 32-bit combined subword-parallel multiplier; delay-optimized; maximum fan-out 4; 2.5 V; 25° C | p.2197 |
| area overhead | 8.3% more | area | LSI Logic G11 0.11 micron CMOS standard cell library; 2003 | conventional tree multiplier | one 32 x 32-bit, two 16 x 16-bit, or four 8 x 8-bit operations | p.2195 |
| delay overhead | 10.4% more | delay | LSI Logic G11 0.11 micron CMOS standard cell library; 2003 | conventional tree multiplier | one 32 x 32-bit, two 16 x 16-bit, or four 8 x 8-bit operations | p.2195 |
errors_and_checks: Exact unsigned/two's-complement multiplication is the intended contract; extensive simulation is reported, but no numerical error metric/fault checker is reported.   # pp.2194-2195
conditions: The partitioning technique applies to partial-product matrices that are not Booth encoded.   # p.2197
  The same counter tree/carry-propagate adder serves all supported subword sizes because inactive partial products are zeroed.   # pp.2194, 2197
  The technique eliminates hardware for detecting/suppressing carries across subword boundaries.   # p.2195
  The 32-bit design adds one 2-input OR gate/two inverters, 84 2-input AND gates, 58 2-input XOR gates/two 2-input AND gates, four 2-input XOR gates, and six full adders relative to the conventional combined multiplier.   # p.2195
evidence: §III, Figs. 2-4, pp.2194-2196; §V, Table I, pp.2195-2197

### integer_mac  (role: extends)
mechanism: A subword multioperand adder sums the multiplier's result subwords and an optional accumulator. The integrated organization treats the 32-bit and 16-bit modes as concatenations of 16-bit entries, which permits one adder organization to support the 8-bit/16-bit/32-bit modes. In the 8-bit mode, the adder combines four 16-bit products and an optional 64-bit accumulator, which supports vector dot products and multiply-accumulate operations.
choices:
  array_style: simd_packed_dot   # pp.2193, 2195
  accumulator_width_bits: 64 [outside domain]   # p.2195
new_choices:
  none
slots:
  mul: twin_precision_subword [partition=halves_and_quarters [outside domain]]   # p.2195
parameters: four 16-bit products for 8-bit subwords; two 32-bit products for 16-bit subwords; one 64-bit product for 32-bit operands; optional 64-bit accumulator   # p.2195
results:
| metric | value | unit | technology / device | baseline | condition | page |
| architecture-only result | UNKNOWN | UNKNOWN | UNKNOWN; 2003 | UNKNOWN | No separate area/delay result is reported for the multioperand-adder extension | p.2195 |
errors_and_checks: Exact subword summation/MAC is intended; no numerical error metric/fault checker is reported.   # p.2195
conditions: The adder requires additional hardware to handle unsigned/two's-complement operands correctly, but the hardware is not quantified.   # p.2195
evidence: §IV, Fig. 5, pp.2195-2196

## new_families
none

## space_gaps
* `twin_precision_subword.partition` lacks a value for one design that supports both half-width and quarter-width partitions.   # p.2194
* `twin_precision_subword.base_scheme` lacks the combined unsigned/two's-complement non-Booth partial-product matrix used here.   # pp.2193-2195
* `twin_precision_subword` lacks a choice for partitioning by zeroing inactive partial-product-matrix regions through operand predecode.   # pp.2194-2195
* `integer_mac.accumulator_width_bits` excludes the reported 64-bit accumulator.   # p.2195

## open_questions
* The paper uses one signedness control `t` and does not state that individual active subwords can independently select unsigned/two's-complement interpretation.
* The paper does not provide enough structure for the subword multioperand adder to assign its reduction slot.
* The paper identifies the final adder as a high-speed carry-lookahead adder but does not report its group size/levels/intergroup-carry organization.
