# carry_save_array: proposed changes to the space

* choice `summation_configuration: {wallace_tree, linear_array, hybrid_tree_array}` or a reduction slot naming Wallace summation — the uniform Baugh-Wooley array is summed by several techniques and hybrids trade speed for compactness [bewick1994#s07, blankenship1974]
* choices `sign_compensation_variant: {baugh_wooley_original, pezaris_same_and_functions, inclusive_or_sign_bits}` and `highest_product_bit_formation: {formed, omitted_when_redundant}` — the two most-significant columns admit equivalent logic and the top bit may be dropped [blankenship1974]
* `cpa` admitting a spatially pipelined registered half-adder final row — the final carry is distributed across pipeline stages [hatamian1986]
* choices `partial_product_timing: skew_operands_before_generation` and `pipeline_clocking: two_phase_dynamic` — skewing operand bits before the AND gates halves the skew registers [hatamian1986]
* choices `reduction_cell: two_bit_gated_adder_with_2_bit_anticipated_carry` and `sum_propagation: sum_skip_every_four_adders`, plus a `cpa` description of the final row's horizontal internal carries with previous-row carries through sum inputs [pezaris1971]
* choice `partial_product_combination: {paired_parallel_adders, successive_addition, columnwise_half_full_adders}` — the chapter distinguishes three staged arrangements [richards_1955#s06]
* `signed_scheme` value for magnitude multiplication with conditional two's-complement product correction [schulte_2000]
* choice `partial_product_grouping: two_halves` — two concurrently reduced halves merge before long-carry propagation [thornton_1964]
* choices `partial_product_alignment: aligned_rows`, `physical_delay_model: {gate_only, extracted_wire_and_asymmetric_input}`, `counter_primitive: {full_adder, 3-2_counter}` — row alignment, physical timing in placement and the counter naming are separate decisions [bewick1994#s05, bewick1994#s06, bewick1994#s02]
* choice `partial_product_ordering: modified_bit_plane` — equal-weight partial products grouped into bit planes with pairwise coefficient bits [noll_1991]
* a multiplier-slot family for a sparse Wallace-style carry-save reduction tree — the document's tree cannot be assigned without stretching this family [srinivasan_2013]
