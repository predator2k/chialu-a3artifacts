# hybrid_signed_digit: proposed changes to the space

* sd_position_spacing range extended to the full word length and spacing_uniform kept as a free choice — d+1 runs from 1 to n, which Int[1..8:1] truncates [phatak_koren_1994]
* output_spacing {0, d_x, d_y} — addition may preserve or change the spacing without extra delay, so the output format is a design choice [phatak_koren_1994]
* representation_mix {single_hsd_variant, mixed_sd_hsd} — a multioperand tree can switch from signed-digit to hybrid at an intermediate level [phatak_koren_1994]
