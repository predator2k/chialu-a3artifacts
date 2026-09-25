# transformer_activation_lut: proposed changes to the space

* `operand_format` values `int32`, `fp32`, and `int18` — I-BERT kernels compute in INT32, NN-LUT is evaluated in FP32 and INT32, and GELU-MSDF uses a statically quantized 18-bit format [kim_2021, yu_2022, taghavizade_2024]
* `calibration` value for interpolating-point / L2 coefficient fitting — the i-GELU coefficients come from an interpolation-point search rather than minimax or training [kim_2021]
* choices `lut_entries: Int`, `parameter_precision: {int32, fp16, fp32}`, `input_scaling: power_of_two`, and `post_training_calibration: Bool` — the learned-table variant exposes all four [yu_2022]
* choice `quantization_policy: uniform_symmetric_static` — fixed activation scales remove runtime range calculation [kim_2021]
* choice `intermediate_width_policy` — per-signal widths narrowed from dataset statistics while one addition keeps 32 bits [taghavizade_2024]
