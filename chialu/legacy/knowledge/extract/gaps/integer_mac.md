# integer_mac: proposed changes to the space

* element_precision_modes {int8, int4, int2} — int2 mode doubles int4 throughput at comparable power in the decoupled inference engine [agrawal_2021]
* persistent_weight_storage, accumulator_storage bram_scratchpad and inter_tile_connection daisy_chain — the NPU keeps weights in shared register files, interleaves int32 partials through BRAM and reduces tile results in a chain [boutros_2020]
* array_style value simd_packed_mac distinct from simd_packed_dot, with a lane_mode_control global precision mode — one Booth/Wallace/CLA datapath serves 1x64 to 8x8 lanes [danysh_2005]
* element-format choice admitting FP16/bf16 systolic arrays, or a separate FP systolic family — the systolic organisation is not integer-specific [geva_2022, arora_2022]
* matrix_dimensions, stationary_operand (dataflow policy), accumulator_entries and operand_width_modes {8x8, 8x16, 16x8, 16x16} with width-dependent rate — these characterise the TPU matrix unit [jouppi_2017]
* accumulator_width_bits extended to 64 and mul partition halves_and_quarters — the subword multioperand adder sums four 16-bit products with a 64-bit accumulator [krithivasan2003]
* shared_operand / lane-pairing choice and quantization_scaling per_layer_power_of_two — performance depends on pairing output channels around one common operand [lee_2019]
* runtime_bit_composition orthogonal to array_style, and a mul slot family for bit-level composable multipliers with asymmetric input/weight widths [sharma_2018]
* a fixed-point-mode choice that bypasses the alignment shifter and the complementer of a shared floating-point path — two's complement operands need neither, so the merged unit finishes in two of its three stages [zhang_2018]
