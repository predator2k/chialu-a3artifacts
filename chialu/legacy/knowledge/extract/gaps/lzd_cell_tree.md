# lzd_cell_tree: proposed changes to the space

* `block_primitive` value `carry_merge` and choices `organization: {independent_count_trees, shared_carry_propagate}`, `circuit_style: {static_cmos, dynamic_cmos}`, and `dynamic_rail_style: {full_dual_rail, hybrid_single_dual_rail}` — the carry-lookahead counter's energy-delay points are set by these [dimitrakopoulos_2008]
* `formulation` value `prefix_or_monotonic` — converting to a zeros-then-ones string and encoding its transition is a third formulation [muller_2018]
* choice `detection_target: {leading_zero, leading_one, both}` — the same generator builds an LOD with a different two-bit cell, and a posit decoder serves both by operand inversion [jaiswal_2018, podobas_2018]
* choice `group_radix: {2, 4, 8}` as a value of `block_primitive` — 8-bit initial groups are used as well as pairs and nibbles [schmookler_2001]
* choices `layout_shape: {regular, rectangular_stage_resized}` and `level_circuit_style: {pass_transistor_multiplexer_cmos, wired_or_ecl_tree}` — physical organization changes delay according to output load, and the ECL tree combines four groups per level [oklobdzija_1994]
* `count_tree: conditional_adder_tree` and a regime-decoder slot in `posit_adder_multiplier` that this family fills — the posit regime decoder combines 4-bit chunk counts through an adder tree [podobas_2018]
