# multipath_fma: proposed changes to the space

* `path_select_criterion` value `exponent_difference_and_effective_subtraction` — the close path is entered only for effective subtraction in the close exponent range, so the operation sign is part of the predicate [quinnell_2007, seidel_2003]
* choice `far_path_partition: {single, addend_anchor_product_anchor}` — the three-path design splits the far path by which operand anchors the alignment [quinnell_2007]
* separate `logical_case_count` and `physical_major_paths` — five exclusive cases share two hardware paths, which `path_count` alone cannot express [seidel_2003]
* choices `variable_latency_enable: Bool` and `inactive_path_gating: {none, clock, power}` — early case selection lets faster cases retire early and lets the unused path be deactivated [seidel_2003, srinivasan_2013, quinnell_2007]
* choice `near_path_exponent_set` and `accumulate_injection_point: second_csa_stage` — the near path's exponent set and the point where the aligned addend enters the sparse multiplication tree remove a 3:2 compression stage [srinivasan_2013]
* choice `shared_completion_rounder: Bool` — both paths feed one combined sum/rounding unit [srinivasan_2013, quinnell_2007]
* a `negation_handling` choice on `multipath_fma` — the close path adds the two's complement +1 through an empty slot of its 117-bit 3:2 CSA and the far path carries the same +1 through a row of half adders, so no end-around carry adjustment is needed [manolopoulos_2016]
* choice `normalization_placement_per_path: {far_before_add, close_after_add}` — the far path normalizes before the final addition while the close path normalizes and rounds after it, which one normalize-before-add flag cannot express [manolopoulos_2016]
* choice `path_span_in_pipeline: {second_stage_only, both_paths_to_third_stage}` — the paths can split only the second stage or extend into the third [manolopoulos_2016]
* `path_select_criterion` value for a zero-operand detect — a fourth path selects the incoming mantissa when an early zero detector finds the accumulated result zero in carry-save form [vangal_2006]
* a rounding-contract choice on the FMA families — a MAF is called IEEE compatible when it delivers the result of a sequential FMPY and FADD, which the single-rounded product does not [quach_1991]
* a path-splitting-threshold choice — the exponent-difference split sits at 2 rather than 1 where the summation of the carry-save product's two vectors may overflow [quach_1991]
