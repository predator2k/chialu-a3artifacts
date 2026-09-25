# fused_two_term_dot: proposed changes to the space

* choice `operation_bypass: {none, addition_skip_multiplier_trees, multiplication_skip_alignment}` — forwarding multiplexers let the unit serve addition-only and multiplication-only operations at one or two multiplexer delays [saleh_2008]
* choice `product_combination: {add, subtract, add_or_subtract}` — the Fused DP selects AB+CD or AB-CD, which `second_op` does not distinguish from the simultaneous A+B/A-B outputs [swartzlander_2012]
* choice `fused_accumulator_addend: Bool` — ExSdotp adds a 2w-bit accumulator in the same unrounded datapath with magnitude sorting and an exact-zero detector [bertaccini_2022]
