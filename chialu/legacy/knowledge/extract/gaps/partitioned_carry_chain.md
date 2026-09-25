# partitioned_carry_chain: proposed changes to the space

* choices packing_policy {both_operands_narrow, one_operand_narrow_with_replay} and compatibility_rule (same_operation) — dynamic operand packing admits one narrow operand speculatively and replays at full width when a carry crosses the lane. [brooks_1999]
* choice partitioned_structures {reduction_tree, final_cpa} — mode-dependent carry kills also partition a CSA reduction tree, which the family currently covers only for the carry-propagate adder. [danysh_2005]
* choices lane_width_bits and lane_count (or lane_widths {8, 16, 32, 64}) — the 2 x 16-bit and 4 x 16-bit configurations and the ILLIAC IV byte/32-bit/64-bit partitions are indistinguishable without them. [lee_1995, davis_1969]
* choice arithmetic_mode {modulo, signed_saturation, unsigned_saturation} — packed add/subtract variants select the result behavior on subword overflow. [lee_1996]
* choice boundary_carry_injection — packed subtraction inserts a carry at the lane boundary in addition to killing the crossing carry. [sjalander2009]
* choice partition_count (full-width versus dual-size) — the dual-size adder performs one full-width or two independent additions at an arbitrary cut. [zimmermann1997__s06]
