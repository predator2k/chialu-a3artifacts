# mx_microscaling_dot: proposed changes to the space

* `element_type` values `mx4`, `mx6`, `mx9`, or explicit choices `mantissa_bits_m: {2, 4, 7}`, `global_scale_bits_d1`, `microexponent_bits_d2` and `sub_block_size_k2` — the two-level formats are defined by these widths and sharing granularities, which the current element enum cannot express [rouhani_2023a]
* slot or choice for the block reduction pipeline (`reduction_precision_f` fixed-point width after block reduction, then FP32 accumulation) — the reduction/accumulation chain is the datapath the paper describes and the `reduction` slot names only tree shapes [rouhani_2023a]
* choice `shared_scale_axis: {reduction_dimension, row, column}` — the axis whose k elements share the scale is operational and affects transposition and storage [rouhani_2023b]
* choice `conversion_rounding: {round_half_to_nearest_even, round_half_away_from_zero}` — inference and training use different rounding during scalar-to-MX conversion [rouhani_2023b]
* choice `conversion_recipe: {algorithm_1, implementation_defined}` — the OCP semantics permit recipes beyond the reference algorithm [rouhani_2023b]
