# multi_term_fused_dot: proposed changes to the space

* `multiplier` slot value for an exact unrounded multiplier that emits the full 2+2wF-bit significand, and the instantiated Dadda-tree multiplier with a sum/carry output form — the fused designs consume unrounded products in carry-save form [dedinechin_2008, sohn_2016]
* `rounding_contract` value `last_bit_accurate` with an `internal_guard_bits` choice — g=3 gives last-bit accuracy for the demonstrated squared-sum datapath [dedinechin_2011]
* choices `exponent_alignment_control: direct_unsorted_difference_routing`, `sign_resolution: dual_reduction` and `normalization_position: before_main_addition` — the four-term unit routes shifts from exponent differences without sorting, duplicates CSA trees for both signs, and normalizes before the final adder [sohn_2016]
* `alignment_strategy` value `intrinsic_line_realignment` with `exponent_sorting: pairwise_weight_crossbar` — movable realignment lines select fixed regions inside the internal adder when exponent separation exceeds a threshold, and pairwise comparisons rank the products for a crossbar [tao_2013]
* choice `pipeline_target` (requested frequency) — synchronization-barrier placement and latency follow the target frequency on FPGA [dedinechin_2011]
