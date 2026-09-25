# nonuniform: proposed changes to the space

* `boundary_search` values `bisection`, `manual_local_linearity`, `probability_weighted_region_allocation` and `neural_network_trained` — the implementations on file place boundaries by a bisection window, by hand from local linearity, by per-region input probability, or by training [dong_2020, lee_2003, wei_2020, yu_2022]
* choices `segment_growth_factor` (two or more) and `nesting: {uniform_outer_nonuniform_inner, nonuniform_outer_uniform_inner}` — the cascade addressing exposes which boundaries are available, and uniform intervals may contain nonuniform segments [lee_2003]
* `addressing` value for a generic interval decoder — the sigmoid approximator names an input decoder without establishing a comparator-tree implementation [wei_2020]
* choice `endpoint_overlap: {allowed, disallowed}` — consecutive segments use distinct discrete endpoints in the bisection segmenter [dong_2020]
