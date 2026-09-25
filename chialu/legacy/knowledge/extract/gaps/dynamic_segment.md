# dynamic_segment: proposed changes to the space

* extend `segment_width` domain to 1..n (or at least 3..16 by 1) — DRUM defines k from 1 to n and evaluates k = 3, and the logarithmic variant evaluates t = 3 through 12 [hashemi2015, yin2021]
* `core_multiplier` slot should admit multiplier families (a Wallace tree, `behavioral_star`, `logarithmic`) rather than adder families — every reported design instantiates a small accurate or logarithmic multiplier as the segment core [hashemi2015, narayanamoorthy2015, vahdat2019, yin2021]
* slot for the barrel shifter that restores the reduced product's position [hashemi2015]
* choice `sign_handling: {unsigned_direct, twos_complement_prepostprocess, approximate_absolute_then_sign_restore}` — signed operation wraps the unsigned core in conversion or approximate-absolute-value logic with measurable overhead [hashemi2015, vahdat2019]
* choice `possible_start_positions: {2, 3}` — distinguishes two-position SSM from three-position ESSM under `static_msb_or_lsb` [narayanamoorthy2015]
* choice `fixed_coefficient_preprocessing: Bool` — a stored coefficient's segment and selection bit remove one OR gate and one multiplexer [narayanamoorthy2015]
* separate `truncation_width_t` and `rounding_width_h` choices for the rounded form — TOSAM's two retained widths are independently meaningful and `segment_width` cannot express both [vahdat2019]
