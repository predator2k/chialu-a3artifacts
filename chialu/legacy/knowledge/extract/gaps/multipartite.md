# multipartite: proposed changes to the space

* choices for the input decomposition D (subword count, unequal subword widths, per-table slope-address width) — the decomposition, not only the table count, sets the stored bits, and the bipartite/STAM families share the gap [dedinechin_2005, muller_1999]
* an adder-tree or output-form slot covering carry-propagated and redundant outputs — the final carry-propagate stage may be omitted when a multiplier consumes the result [dedinechin_2005]
* a monotonicity-enforcement choice (right-edge slopes, increased table precision) — faithful rounding bounds but does not remove interval-boundary nonmonotonicity [dedinechin_2005]
* choice `hierarchy_levels` — HMP recursively decomposes the initial-value table and evaluates two levels [hsiao_2017]
* choice `error_optimization: {separate_error_budgets, joint_exhaustive_check}` — partitions and guard bits selected by exhaustive verification of the combined error [hsiao_2017]
* choice `initial_table_decomposition: {none, lossless_downsample_difference}` — splitting TI into TI_new and TI_diff shrinks storage without adding adder height [hsiao_2017]
* extend the `tables` domain beyond 6 and add `approximation_order: {1, 2}` — the order-2 construction uses eight table terms and a different addressing scheme [muller_1999]
