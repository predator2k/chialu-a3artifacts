# lower_part_approximate: proposed changes to the space

* extend `lower_width` to every integer from 1 upward (or add a forward-path partition) — the reported configurations use 1 to 12 approximate bits, and the multiples-of-four domain excludes most of them [almurib2016, gupta2013, gupta2011, mahdiani2010, pashaeifar2018, venkatesan2011]
* `carry_to_upper` values for the lower cell's own ripple carry-out (exact or approximate), for an operand bit or a carry-alive OR as forecast, and for a duplicated operand bit — the mirror, InXA, MAA3, RCPFA-I/III and 2-bit XOR designs feed the boundary this way rather than through an AND or nothing [almurib2016, gupta2013, gupta2011, liu2018, pashaeifar2018, jiang2016]
* `cell_variant` sub-choice under `lower_cell` — AMA1 to AMA5, AXA1 to AXA3, InXA1 to InXA3 and RCPFA-I to III have distinct truth tables and error means that one enum value cannot separate [gupta2013, gupta2011, liang2013, yang2013, almurib2016, pashaeifar2018]
* `lower_cell` values `set_one_soa` and a 2-bit XOR cell (Cout = y_i, S_i+1 = y_i+1) — the set-to-one lower part compensates Mitchell multiplication and the 2-bit cell builds the 3Y multiple of a radix-8 Booth multiplier [liu2018, jiang2016]
* choice `error_handling: {none, partial_compensation, full_recovery}` for the most significant approximate cell — local correction changes the mean error distance at some delay and power [jiang2016]
* `significance_weighted_allocation` Bool — different approximate-bit counts per output group according to output significance is a separate decision in DCT and FIR blocks [gupta2013]
* a standalone approximate full-adder-cell family or component slot — the AXA cells are specified without fixing the lower width, boundary carry or upper adder [yang2013]
* `approximate_compressor_tree.cpa` and the logarithmic family's `log_adder` slot admitting `lower_part_approximate` — the demonstrated multipliers use an approximate lower-part adder in those roles [gupta2013, liu2018]
