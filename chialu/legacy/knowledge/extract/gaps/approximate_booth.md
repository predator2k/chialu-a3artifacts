# approximate_booth: proposed changes to the space

* slots `reduction_tree` (exact Wallace/Dadda or `approximate_compressor_tree`) and `final_adder` — every design fixes a reduction tree and a final adder that the family cannot name [ansari2018, jiang2016, liu2017, venkatachalam2019]
* choice `approximate_reduction_columns` distinct from `approx_encoder_columns` — approximate compressors in the LSB columns are chosen independently of encoder approximation [ansari2018]
* `encoder` values `approximate_recoding_adder` (ARA8, ARA8-2C, ARA8-2R), `PPG-2S` and `PPG-1S` — the radix-8 3Y adder and the simplified radix-4 generators are encoder structures of their own [jiang2016, venkatachalam2019]
* choices `partial_product_truncation_bits: {0, 9, 15}` and `truncation_compensation: {none, add_1_at_bit_17}` — the ABM2 variants truncate low partial-product bits with a constant bias [jiang2016]
* `approx_encoder_columns` domain extended to 2N — the radix-4 designs evaluate p up to 2N and beyond 16 for 16- and 32-bit operands [liu2017]
* choice `regular_partial_product_array` (ignored highest-row Neg term) — dropping the term changes error and removes a reduction stage independently [liu2017]
* choices `replacement_geometry: {rectangular, diagonal, rectangular_row_reduction}` and `multiplicand_consolidation: {sum_threshold, or_reduction}` — column replacement versus per-row consolidation sets the error/APP trade [venkatachalam2019]
* choice `correction_term_handling: {or_into_partial_product, preserve_exact}` — ORing correction terms into products reduces matrix height, preserving them improves low-m accuracy [venkatachalam2019]
* choice `encoder_error_polarity: {magnitude_reducing_only, bidirectional}` — R4ABE1 and R4ABE2 differ in whether errors can cancel during reduction [liu2017]
* choice `compensation_estimator: {booth_zero_signals, binary_threshold, sorting_network, probabilistic_bias, none}` — fixed-width designs estimate the discarded-column carry by different methods [jiang2017]
