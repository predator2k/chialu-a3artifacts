# approximate_functional: proposed changes to the space

* `method` values `log_subtract_uncorrected` and `incremental_taylor_series` — plain Mitchell division has no correction, and SAADI's power-series reciprocal is a specific recurrence rather than generic quasi-convergence [mitchell1962, behroozi2019, melchert2019]
* `method` value for quotient-surface linear curve fitting with `curve_region_shape: {square, triangular}` — HSD/FPD partition the quotient surface and fit it linearly [jiang2017]
* a slot for the shared multiplier that generates reciprocal powers and the final product, with a choice `multiplier_implementation: {exact, partial_product_truncated}` — SAADI shares one n-bit multiplier and TruncApp_AM perforates partial products [behroozi2019, melchert2019, vahdat2017, vahdat2017b]
* a slot for the reduced-width exact core divider with `core_implementation: {combinational, sequential}` — DAXD/AAXD make the core architecture designer-selectable (array, sequential, high-radix) [hashemi2016, jiang2019]
* slots for SEERAD's rounding/index logic, constant shift-add multiplier and quotient barrel shifter [zendegani2016]
* design-time choices `accuracy_level: Int[1..4]`, `divisor_group_count: {1, 2, 4, 8}` and a per-group `(L, D)` rounding tuple — SEERAD's four levels are four synthesized structures that `runtime_quality_scaling` cannot represent [zendegani2016]
* choices `normalized_width_n: Int[4..16:4]` and `reciprocal_order_t: Int[1..n-1]` — design-time width and runtime series order jointly define SAADI's accuracy/energy range [behroozi2019, melchert2019]
* choices `compensation_implementation: shift_add_lut` and `pipeline_mode: {iterative_shared, replicated_mac_pipeline}` — SAADI-EC selects a per-t shift for Q+Q/2^s and SAADI-EC-P replicates the multiply-accumulate stage for II=1 [melchert2019]
* choices `correction_term` and `truncation_bits_t` — INZeD subtracts a constant 2^-5 + 2^-8 and truncates logarithm-fraction bits for its INZeD-t variants [saadat2019]
* choice `overflow_correction: or_gate_saturation` — AAXD ORs the overflow bit into every retained quotient bit [jiang2019]
* choice `reciprocal_generation: invert_fraction_and_prepend_one` — TruncApp derives the reciprocal by bit inversion rather than a LUT [vahdat2017b]
* choice `operation_set: {division, division_and_square_root}` — the same logarithm-approximate and adaptive-approximation units also implement square root [mallasen_2022, jiang2019]
