# prefix_comparator: proposed changes to the space

* choice activity_policy with value terminate_lower_significance_comparisons — lower-significance bus positions are forced to zero after the most-significant unequal bit, which is the source of the activity reduction. [abdel_hafeez2013]
* choice result_encoding with value dual_N_bit_buses_plus_OR_scans — separate left/right buses encode greater-than/less-than with LR=00 as equality, resolved by final OR trees. [abdel_hafeez2013]
* slot priority_encoder (value multilevel_lookahead_mdm) — the comparator instantiates a multilevel-lookahead priority encoder fused with operand-bit selection in the magnitude decision module. [huang_wang2003]
* choice circuit_style with values static/dynamic (dynamic_modl) — serial dynamic CMOS and multiple-output domino logic are an explicit design axis of the MDM. [huang_wang2003]
* choice pipeline_partition with value two_stage_half_cycle — latch-based stages execute delay-balanced portions in opposite halves of one clock cycle. [huang_wang2003]
* structure value pairwise_half_adder_sum_plus_zero_reduction (equality) — corresponding bits are compared with sum-only half adders and reduced by an AND condition without subtraction. [richards_1955__s11]
* structure value borrow_only_subtracter (magnitude) — a magnitude-only circuit reproduces the borrow portion of a subtracter without difference bits. [richards_1955__s11]
* choice equality_source with value whole_word_propagate — equality is taken from the existing whole-word propagate of a prefix adder without the sum path. [zimmermann1997__s06]
