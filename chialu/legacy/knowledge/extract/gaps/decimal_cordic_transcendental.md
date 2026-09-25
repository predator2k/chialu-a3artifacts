# decimal_cordic_transcendental: proposed changes to the space

* choices function_modes, modifier_source, and digit_processing_order for the pseudo-multiply/divide recurrence — the shared routine is specialized to log/atan/exp/tan/sqrt/square by the modifier source and by msd-first versus lsd-first digit order. [meggitt_1962]
* slot for an operation-constant ROM holding log(1+10^-j) or atan(10^-j) — the existing angle_table slot admits reciprocal-seed families rather than this constant store. [meggitt_1962]
* choices coordinate_set (unified_circular_hyperbolic), operation_mode (rotation_and_vectoring), elementary_angle_code (5221), scale_factor (constant), floating_point_start_index (variable_J), and termination (multiply_add_or_divide_add) — these distinguish the decimal CORDIC configuration and fast termination replaces about half the rotations. [vazquez_2009b]
* slot iteration_adder distinguishing carry_propagate from carry_save_datapath — the redundant version replaces the carry-propagate iteration adder with a decimal 3:2 carry-save adder. [vazquez_2009b]
* choices direction_selection (truncated_sign_estimate), sign_estimate_width (10 bits), and iteration_repetition (none) — the redundant variant selects the rotation direction from leading bits of the carry-save control coordinate and never repeats an iteration. [vazquez_2009b]
