# twin_precision_subword: proposed changes to the space

* choice `accumulation_mode: {sum_apart, sum_together}` and `scalability_levels: {1, 2}` — the array-based subword MACs either keep subword products in separate accumulators or add them into one, with one or two levels of scaling [camus2019]
* `partition` values `eighths`, a combined halves-and-quarters mode set, three-precision sets such as 32/16/8, and arbitrary unequal or more-than-two partitions — the shipped and proposed units support lane sets the halves/quarters pair cannot record [danysh_2005, krithivasan2003, manolopoulos_2016, moons2017, perri_2004, sjalander2009]
* choice `sharing_method: {shared_segmentation, shared_subtree}` — one carry-killed structure versus mode-specific subtree results selected by a final multiplexer [danysh_2005]
* `base_scheme` values for a combined unsigned/two's-complement non-Booth matrix and an unsigned array/HPM matrix — both are demonstrated before the signed Booth and Baugh-Wooley forms [krithivasan2003, sjalander2009]
* choice `partial_product_isolation: {control_gated_zeroing, zero_inactive_matrix_regions}` — unused partial products are forced to zero by gated generation or by operand predecode of inactive regions, and the off-diagonal regions of a three-precision array are zeroed the same way [sjalander_2004, sjalander2009, krithivasan2003, manolopoulos_2016]
* choice `operating_modes` or `precision_mode_set` naming the supported mode set (one N, one N/2, two N/2; 1x16b, 2x8b, 4x4b) — the mode set, not only the partition, is a design decision [sjalander_2004, moons2017]
* choice `decomposition_depth: Int[0..2]` — the FPGA DSP block applies the twin-precision split recursively [rasoulinezhad_2019]
* a reduction-tree slot for the regular-connectivity logarithmic HPM tree of 3:2 adders [sjalander2009, sjalander_2004]
* a composition value based on independent multiplier bricks rather than one partitioned matrix [sharma_2018]
* choice `lane_isolation: {zero_select_cross_quadrants, pp_shift, explicit_carry_kill, zero_padding}` — the way a Booth-recoded matrix keeps one lane's carries out of the next is a decision of its own, separate from zeroing the cross quadrants [galal_2013]
* the `multiplier` slot of `multi_precision_simd_fma` admits `twin_precision_subword` — the one-array-serves-three-precisions multiplier of that unit belongs to this family [manolopoulos_2016]
