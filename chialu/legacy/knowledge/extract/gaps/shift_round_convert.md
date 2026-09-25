# shift_round_convert: proposed changes to the space

* `rounding_modes` values for the four IEEE-754-1985 modes, the 8087's unbiased nearest plus three directed modes, and the posit RNE-plus-RTZ pair — the shipped conversion units implement mode sets between rz_only and five_modes [diefendorff_2000, palmer_1980, tiwari_2021]
* choices `inbound_conversion: {exact}` and `destination_precision: {24_bit, 53_bit, 64_bit}` — the 8087 converts every memory operand to temporary real without rounding error and rounds results to a control-word precision independent of the operands [palmer_1980]
* choice `vector_width_mismatch_handling: lower_or_upper_vector_part` — narrowing and widening vector conversions that do not fill one register select a source half [mach_2020]
* choice `operation_set` naming which conversions share the unit (int-to-fp, fp-to-int, fp32/fp64 casts) — the PA7100 folds all of them into the FALU [asprey_1993]
* a `subnormal` slot or choice with a flush-to-zero value — the packed conversions flush subnormal inputs and results [oberman_favor_1999]
* choice `subnormal_operand_representation: architected_pattern_plus_dirty_flag` — the register file holds the exact architected bit pattern and a per-register dirty flag replaces the implied bit, against the earlier 65-bit intermediate format that carried the implied integer bit [boersma_2011]
