# bcd_direct_addition: proposed changes to the space

* `digit_code` values `5421` and `biquinary`, plus a `correction_value: {0_or_6, 3_or_13, add_3_or_subtract_5}` choice — the textbook adds coded adders whose correction depends on the code [richards_1955]
* a decimal carry-network slot or `carry_scheme` values `parallel_prefix` and `carry_select` — the implemented networks are Kogge-Stone trees, a quaternary-tree/carry-select hybrid, and four-digit sum/sum+1 select groups [bayrakci_2007, hickmann_2007, jaberipur_2009, vazquez_2014, eisen_2007]
* `correction_placement` values for parallel candidate selection (`presum_paths: carry_in_0_and_1`, four candidates A+B/A+B+1/A+B+6/A+B+7 or corrections 0/1/6/7) and for combined pre- and post-correction — the z900, POWER6 and divider adders select among precomputed corrections rather than placing one +6 [busaba_2001, schwarz_2002, bayrakci_2007, file_webb2007, wang_2007b]
* choice `carry_grouping: {two_digit_byte, three_digit_straddle}` — the Model 195 adder groups digits into bytes for lookahead [schmookler_1971]
* `digit_adder` slot admitting `none`, `conditional_sum` and `carry_select` — the direct decimal sum network instantiates no binary adder family, and the DFU dataflows use conditional-sum or carry-select digit cells [schmookler_1971, file_webb2007, eisen_2007]
* choices `subtraction_pre_correction: fifteens_complement` and `correction_control: flags_effective_operation_digit_carry_outs` — subtraction and flag-driven correction differ between designs [akkas_2011, thompson_2004]
* choice `input_form: {two_bcd_operands, radix_10_carry_save}` — the multiplier converters accept one BCD digit vector plus one carry-bit vector [lang_2006]
* choice `staged_final_assimilation` — the improved carry-save multiplier splits the final adder into two registered portions [erle_2003]
* choice `implementation_context: {shared_binary_decimal_adder, dedicated_decimal_adder}` — correction after binary addition versus direct sum formation [schmookler_1972]
* slots in other families admitting `bcd_direct_addition` (`decimal_fma` significand adder, `parallel_decimal_multiplication.final_adder`, `iterative_decimal_multiplication.final_adder`, `decimal_multioperand_addition.root_adder`) — every one of those designs terminates in this family [akkas_2011, erle_2009, kenney_2004, kenney_2005, lang_2006, vazquez_2014]
