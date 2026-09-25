# compound_adder_select: proposed changes to the space

* sum_plus_2 candidate for the directed modes via a half-adder row above the far-path adder [oberman_1996]
* rounding_algorithm {QTF, YZ} and post_normalization_position {before_round_selection, after_round_selection} [even_2000]
* far_round_precompute plus_1_plus_2_three_results [lutz_2019]
* overflow_preshift Bool so the combined add/round input stays below 11.XXX [srinivasan_2013]
* per-precision parallel incrementers and multiplexers (24/53/113-bit fractions) [gerwig_2004]
* rounding table / prediction-scheme derivation per mode for multipliers [quach_2004]
