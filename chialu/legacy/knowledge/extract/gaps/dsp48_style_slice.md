# dsp48_style_slice: proposed changes to the space

* recursive_karatsuba.base_multiplier as a component slot that can name dsp48_style_slice, plus an unsigned_tile_shape choice (16x24) — the Karatsuba tiling depends on the block's multiplier/pre-adder structure [kumm2018]
* virtual multiplier-lane packing choice (shared_operand_packing, one weight with two 8-bit activations, packed additions) with a correction_placement value external_post_accumulation — distinct from native simd_partition of the ALU [lee_2019, nguyen_2017, roorda_2022, sommer_2022]
* cascade_shift {none, shift_right_17} and pipeline_register_levels Int[0..4:1] — the fixed PCIN alignment and internal register depth are block parameters [pasca_2011__s03]
* alu_adder slot value for the hard three-operand adder — the current slot forces an unsupported carry-propagate microarchitecture onto it [pasca_2011__s03]
* simd_partition values for 4/8/18/48-bit modes, with semi_2d_forwarding and an embedded fifo_register_file — PIR-DSP's decomposable MAC and forwarding [rasoulinezhad_2019]
* coefficient_storage embedded_bank — read-only filter coefficients stored inside the block [boutros_2021]
