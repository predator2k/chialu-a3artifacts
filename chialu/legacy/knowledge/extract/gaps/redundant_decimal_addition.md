# redundant_decimal_addition: proposed changes to the space

* choice `digit_encoding: {five_bit_3x_mod31, four_bit_twos_complement, eight_bit_bsd_vector}` — the same digit set admits several codes and the code decides negation and slice logic [svoboda_1969, gorgin_2009, nikmehr_2006]
* choice `transfer_form: {single_signed_transfer, independent_add_and_subtract}` — Svoboda's positions emit separate +1 and -1 transfers that may coexist [svoboda_1969]
* choice `position_sum_form: twos_complement_carry_save` — DSSD avoids an initial carry-propagating position addition [gorgin_2009]
* choice `implementation: {direct_table_pla, binary_adders_with_correction_plas}` and a slot for the fixed-width binary digit adder (a 4-bit carry_lookahead in the RBCD design) [shirazi_1989]
* `digit_set` value [-8, 7] and separate input/output digit sets — the FMA adder accepts [-8, 7] and [-9, 9] and emits [-8, 7] [han_2016]
* choice `correction_schedule: deferred_to_next_iteration_and_cleanup` — the overloaded accumulator applies +6 one iteration late and cleans up on exit [kenney_2004]
* `final_conversion` value for Svoboda's repeated-addition filter that adds until no digit equals 5 [svoboda_1969]
* let `parallel_decimal_multiplication.reduction_tree` and `iterative_decimal_multiplication.accumulator` name this family — both designs reduce or accumulate in redundant decimal digits [gorgin_2009, kenney_2004]
