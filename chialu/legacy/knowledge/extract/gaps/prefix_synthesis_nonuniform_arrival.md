# prefix_synthesis_nonuniform_arrival: proposed changes to the space

* `arrival_profile` values `middle_columns_late` and `bitwise_nonuniform`, plus an `output_required_profile: {lsb_early, msb_early}` — decimal partial-product reduction delivers the middle columns last, the exhaustive search accepts arbitrary per-bit arrivals, and required times vary by output position [han2013, roy2013, zimmermann1997]
* `search_method` values `hand_optimized`, `local_transform_compress_expand` and `exhaustive_bottom_up_with_pruning` — the thesis hand-optimizes and then compresses/expands, and the DAC search enumerates graphs bottom-up with pruning [zimmermann1997, roy2013]
* constraint choices `depth_constraint`, `size_constraint`, `max_black_nodes_per_column`, `wire_length_constraint`, `size_slack_delta`, `repeatability_limit` — the synthesizers bound depth, size, per-column nodes, wire length and pruning slack [zimmermann1997, roy2013]
* choice `solution_multiplicity` and explicit prefix-node-count minimization — several minimum graphs are kept for congestion/power evaluation [roy2013]
* choices `synthesis_feedback: {physical_synthesis, analytical}`, `objective_metrics: area_delay`, `initial_graph` / `starting_graph: {serial_prefix, ripple_carry, sklansky}` — the reward source and the seed graph determine the synthesized frontier [roy2021, zimmermann1997]
* choices `topology_conversion: {ripple_carry, carry_skip, carry_select}` and `area_reduction: required_time_backward_rewiring` — prefix regions convert to generic adder structures and non-critical nodes rewire to slower parents [liu2003]
* choices `region_topology` and `group_boundaries` — the decimal multiplier assigns Ladner-Fischer, 2-bit lookahead and Han-Carlson logic to arrival groups of result digits [han2013]
