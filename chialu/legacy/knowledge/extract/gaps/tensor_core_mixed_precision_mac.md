# tensor_core_mixed_precision_mac: proposed changes to the space

* choices for the operand/accumulator/output format sets — fp16/bf16/TF32/fp64/fp8/int8/int4/int1 inputs, fp16/fp32/int32 accumulation, and fp16-or-fp32 output are the documented axes and none is recorded [choquette_2021, choquette_2023, micikevicius_2018, raihan_2019, markidis_2018, starke_2021]
* `dot_width_per_pe` value 2 (A100 binary64) and `alignment_target` value `largest_magnitude` — the probed low-precision modes align to the largest-magnitude operand rather than to the largest exponent [fasi_2021]
* accumulator-internal choices `product_handling: exact_full_precision`, `partial_sum_normalization: {final_only, after_each_addition}`, `accumulator_bottom_bits: Int`, `carry_headroom_bits: Int`, and `final_normalization_rounding` — these, not only `partial_sum_rounding`, determine the observed error [fasi_2021]
* choices `matrix_tile_shape` (4x4x4, 16x16x16, 32x8x16, 8x8x32), `matrix_update_rank: {1, 2, 4, 8}`, `accumulator_matrix_shape: {4x2, 4x4}`, `execution_decomposition` (HMMA sets and steps), `warp_core_mapping`, and `thread_granularity: {8, 32}` — the tile and its mapping onto units distinguish Volta, Turing, A100, and POWER10 [choquette_2018, markidis_2018, raihan_2019, starke_2021, choquette_2021]
* array-level choices `array_style: systolic_array`, `matrix_array_shape` (128x128), `operand_flow: lhs_stream_rhs_preloaded`, `rhs_load_transpose: Bool`, and matrix-unit/tensor-core replication counts [norrie_2021, jouppi_2023]
* choice `structured_sparsity_support: Bool` — fine-grain sparsity doubles A100 throughput [choquette_2021]
* choice `accumulator_locality: unit_local_registers` — POWER10 keeps eight 512-bit accumulators inside the unit to reduce data movement [starke_2021]
