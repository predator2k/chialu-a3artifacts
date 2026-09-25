# bf16_fma_datapath: proposed changes to the space

* choice `accumulation_structure: {chained_pair_sum_then_accumulate, fused}` — BFDOT2 adds the two products in FP25 and rounds before the fp32 accumulate, which is not a fused dot product [burgess_2019]
* choices `exception_reporting: {none, ieee_flags}` and `nan_handling: {default_nan, propagate}` — the Arm datapath drops trapped and cumulative IEEE exceptions and returns one default NaN [burgess_2019]
* `rounding_mode` value `direct_truncation` for the fp32-to-bfloat16 conversion — the training study compares round-to-nearest-even with truncation and measures the degradation [kalamkar_2019]
* `op_shape` value `matrix_dot_accumulate` covering the 2x4 by 4x2 BFMMLA operation and systolic-array matrix accumulation — both compose or extend the dot2 form into a matrix product with fp32 accumulation [lutz_2019, norrie_2021]
