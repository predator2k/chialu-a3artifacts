# csa_tree: proposed changes to the space

* carry-save-register (pipelined or accumulating) implementation rather than a combinational tree only [piestrak_1994, erle_2009, wang_2004]
* sign_resolution {single_tree, dual_reduction} — duplicated opposite-inversion trees form positive/negative candidates selected by a comparison [sohn_2016]
* reduction_optimization {area_optimized, delay_optimized} for p:2 trees [vazquez_2010]
* decimal digit code for compressor cells {bcd4221, bcd5211, xs3_odds, bcd8421_corrected} — determines whether binary 3:2 cells reduce decimal digits without correction [castellanos_2008, vazquez_2010, vazquez_2014, dadda_2007, kenney_2005]
* lane_boundary_carry_kill Bool for SIMD/packed MAC trees [danysh_2005]
