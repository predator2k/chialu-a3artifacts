# block_fp_accumulation: proposed changes to the space

* `mantissa_bits` values 12 and 16 — the HBFP design-space study evaluates 12- and 16-bit dot-product mantissas [drumond_2018]
* `block_size` values 10 and 128 — the Stratix 10 NX shares an exponent over 10-element dot products and MSFP evaluates bounding boxes up to 128 [langhammer_2021, rouhani_2020]
* choice `wide_weight_storage_bits: 16` — persistent weights keep wider mantissas for FP32 updates while forward/backward passes use narrow ones [drumond_2018]
* choices `exponent_selection_timing: before_each_dot_product` and `output_rounding: stochastic` — the maximum-exponent scan runs per conversion and block-to-float truncation uses stochastic rounding [drumond_2018]
* choices `shared_exponent_bits: 8`, `shared_exponent_selection: maximum`, `bounding_box_shape: tile_based`, `mantissa_encoding: sign_magnitude`, `conversion_placement: in_situ_hardware` — MSFP fixes the exponent width and statistic, the box shape per tensor kind, the mantissa code, and where conversion happens [rouhani_2020, langhammer_2021]
