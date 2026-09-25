# decimal_fma: proposed changes to the space

* slots `significand_adder` (admitting `bcd_direct_addition` and a shared [-6,6] redundant `final_adder`), `leading_zero_anticipator` (admitting `decimal_leading_zero_anticipator`), `pre_alignment`, `post_alignment` and `rounder` — every reported design names these as architectural sub-modules and the family exposes only the multiplier tree [akkas_2011, han_2016, wahba_2017, samy_2010]
* choice for preferred quantum-exponent handling — exact results target min(Q(a)+Q(b), Q(c)) and inexact results the least possible exponent, which the datapath must implement [muller_2018#s07]
* choice `rounding_directions: {five_ieee, five_ieee_plus_two_java}` and a terminal rounding mechanism (truncated-or-incremented select, or rounding in parallel with redundant conversion) — the rounder is a design decision with two reported mechanisms [samy_2010, wahba_2017, akkas_2011]
* choice `operation_set: {fma_only, fma_add_subtract_multiply}` — an operation selector lets the merged tree serve multiplication and addition too [samy_2010]
* choice `pipeline_depth` (combinational, four, seven, or one to ten stages) — reported designs span the range and area is nonmonotonic in depth [samy_2010, akkas_2011, wahba_2017]
* choice `alignment_datapath: {bidirectional_2p, width_4p, width_3p_plus_1}` — the addend alignment width and direction differ between the cascade and merged designs [akkas_2011, samy_2010, wahba_2017]
* choice `internal_digit_set: {bcd8421, sd_minus8_to_7, sd_minus6_to_6}` under `internal_encoding` — the redundant designs use different digit sets with different adders [han_2016, wahba_2017]
* choices `multiplier_reduction: column_wise_mixed_binary_bcd`, `normalization_count_encoding: base_3_binary_mode` and `rounding_timing: parallel_with_redundant_conversion` — mechanisms specific to the combined binary/decimal unit [wahba_2017]
* a decimal floating-point multiplication family distinct from `decimal_fma` [hickmann_2007]
