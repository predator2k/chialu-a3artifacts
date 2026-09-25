# srt_radix2: proposed changes to the space

* `residual_form` value `signed_digit` (borrow-save) — the truncation analysis treats borrow-save beside carry-save, with unbiased selection bounds [burgess_1995]
* choice `overlap_scheme: {none, quotient_selection, remainder_formation, quotient_and_remainder, hybrid}` — which consecutive-stage operations are computed speculatively [harris_1997]
* choice `circuit_style: {static_cmos_standard_cell, skew_tolerant_dual_rail_domino}` for `srt_radix2` and `srt_high_radix` — the compared implementations differ by 1.7x speed and 1.6x area [harris_1997]
* choices `double_pumped` and quotient bits per main clock — the Pentium 4 divider retires two radix-2 bits per clock [hinton_2001]
* `digit_select` values beyond `qds_table` (short ripple adder compared against -0.25; explicit selection equations with a force-next-digit flag) [noll_1991, williams_1991]
* choice `implementation_topology: {reused_clocked_stage, combinatorial_array}` — the unrolled array implements one spatial stage per quotient bit [zuras1986]
* choices `quotient_digit_set` redundancy class and `qds_input_architecture: {redundant_inputs, assimilated_remainder}` with remainder/divisor truncation parameters (t, f, b, w) — selection complexity follows from these [oberman_1997, burgess_1995]
