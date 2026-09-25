# csa_reduction_tree: proposed changes to the space

* half-adder insertion, arrival-aware and wire-aware placement, tree folding, embedded CSAs and crossing elimination choices [bewick1994#s05, bewick1994#s06]
* regular_array versus tree organization and hybrid tree/array configurations [nicolaidis_duarte_1999, bewick1994#s07]
* reuse choice {combinational, time_reused} — a pipelined subset of the tree cycled over the multiplier [wallace1964, anderson1967, thornton_1970]
* heterogeneous full-adder cell selection under TDM [yehjen2000]
* free_input_use {aligned_addend, denormal_correction_row, none} for (7,3) or 3:2 trees with spare inputs [hokenek_cook_1990, montoye_1990, gerwig_2004, schwarz_2005]
* counter primitives beyond the enum: (3,2)+(2,2) mixes and four-input/two-output accumulation structures [wires1999, goldschmidt_1964]
* lane_partition choice (off-diagonal reset, separated corner placement) for multi-precision trees [kaul_2012, chong_2009]
* globally optimized PPRT construction as a geometry value [stelling1998]
* serial (5,3)-counter slice for the squarer reduction slot [ienne1994]
* `geometry` values `array`, `double_array`, `zm` and `os` — the generator fixes the tree topology alongside the reduction element, and each topology trades delay against track count and wire length [galal_2013]
* choice `delay_balanced_interconnect: Bool` — routing the early outputs of one level to the next level's slow inputs and its late outputs to that level's carry-in costs 1.5 CSA delays per two levels rather than 2 [galal_2013]
* choice `layout_informed_placement: Bool` — relative X/Y coordinates encoded in the instance names drive the back-end placer and change the ranking of the tree topologies [galal_2013]
