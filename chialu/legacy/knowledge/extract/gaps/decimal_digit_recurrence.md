# decimal_digit_recurrence: proposed changes to the space

* `digit_select` slot fillers beyond `qds_table`: repeated-subtraction count, nine or ten comparison multiples with sign detection, arithmetic constant comparison, and direct most-significant-digit extraction after prescaling — most of the shipped decimal dividers select without a table [richards_1955#s10, busaba_2001, meggitt_1962, nikmehr_2006, vazquez_2007, eisen_2007, schwarz_2007]
* choice `quotient_selection: {repeated_subtraction, alternating_add_subtract, easy_multiple_sequence, nine_parallel_compares, trial_digit_table}` with `trial_digit_correction: {none, add_or_subtract_divisor}` — the textbook enumerates five determination procedures [richards_1955#s10]
* `quotient_digit_set` value `maximally_redundant_m9_p9` — the carry-free signed-digit recurrence requires it [nikmehr_2006]
* choice `recurrence_style: {restoring, nonrestoring}` — restoring repeated subtraction and nonrestoring prescaled recurrences are both shipped [schwarz_2002, schwarz_2007, busaba_2001]
* choice `partial_remainder_candidates: {one, two}` — PA/PB recurrences obtain multiples 6 to 9 from stored multiples 1 to 5 [schwarz_2007, schwarz_2009, carlough_2011]
* choice `quotient_accumulation: decimal_on_the_fly_correction` and a slot for signed-digit quotient conversion and rounding [schwarz_2007, lang_2007b, nikmehr_2006]
* choices `internal_digit_code: {excess_three, bcd5211, dssd_8bit_bsd}`, `residual_representation: {nonredundant_10s_complement, decimal_signed_digit, binary_carry_save_msds}` and `ms_slice_representation: radix2_twos_complement` — the designs differ in operand coding and residual form [robertson_1958, vazquez_2007, gorgin_2009, nikmehr_2006, lang_2007]
* choices `multiple_generation: shared_doubling_quintupling` and `multiple_storage: divisor_only` — Robertson forms 2d and 5d on demand from one permuted circuit [robertson_1958]
* choice `redundant_io: Bool` — the fully redundant divider keeps dividend, divisor, quotient and remainders in DSSD form [gorgin_2009]
* choice `control_placement: {hardware_loop, millicode_loop}` — G5/G6 iterate a one-digit hardware assist from millicode [check_slegel_1999, slegel_1999]
* choice `selection_estimate_truncation: {decimal_digit, binary_bit}` — selection estimates may end at any binary position inside a digit [vazquez_2007]
