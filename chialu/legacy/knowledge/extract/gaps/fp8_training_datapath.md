# fp8_training_datapath: proposed changes to the space

* `format_policy` values `per_layer_e4m3_or_e5m2` (chosen from layer output statistics) and distinct unspecified forward/backward hfp8 formats [choquette_2023, agrawal_2021]
* make `accumulate_precision` selectable at runtime (fp16 or fp32 per operation) and add an accumulator layout choice such as the custom (1,6,9) fp16 [choquette_2023, wang_2018]
* choice `chunk_size: Int` — accumulation accuracy and energy depend on chunk length, with 64 used and 64 to 256 favored [wang_2018]
* choices for exponent/mantissa allocation, `forward_exponent_bias` (4 in HFP8), and format-specific special-value encoding (`E4M3_no_infinity_single_nan`, `E5M2_ieee_specials`) [micikevicius_2022, sun_2019]
* choices `scaling_granularity: {per_tensor, per_channel_weights}`, `scale_selection: per_layer_output_statistics`, `conversion_overflow: {saturate, non_saturating}`, `conversion_rounding`, and `backward_loss_scaling: auto_adjusted` — scaling and conversion policy are the family's main design decisions [micikevicius_2022, choquette_2023, sun_2019]
* choices `internal_operand_format: fp9` (unified conversion of both hfp8 formats) and `zero_multiplicand_bypass: Bool` [agrawal_2021]
* a first/last-layer and softmax-input precision policy retaining sensitive GEMMs at fp16 [wang_2018, sun_2019]
