# mixed_precision_cascade_fma: proposed changes to the space

* choice `operation_shape: {exsdotp, exvsum, vsum}` — a fused two-product-plus-accumulator operation, and expanding or non-expanding three-term addition reuse the same datapath [bertaccini_2022]
* choice `simd_parallelism: {4x_8_to_16, 2x_16_to_32}` — packed operations per cycle through one wide FPU interface [bertaccini_2022]
* choice `alignment_anchor: {product, larger_operand}` — the product-anchored organization hides the alignment shifter behind the multiplier at the cost of a ~3q-bit register [brunie_2011]
* choice `auxiliary_operations` (narrow-format FMA and wide-format addition modes) — supported with minor multiplexing and exponent changes plus an extra rounding module [brunie_2011]
* independent multiplication-input and accumulator/output format choices with the relation q >= 2p + 2 recorded — the family is defined by a format pair rather than one width [brunie_2017, muller_2018__s07]
* choice `accumulator_left_offset_bits: 2` — placing the accumulator two bits to the left of the carry-save product makes the accumulation non-overflowing and reduces its alignment to a right shift [zhang_2018]
