# compressed_lut: proposed changes to the space

* choices `table_pairing: parallel_p_q`, per-function table sizes, and p/q entry widths — the AMD approximation unit is defined by its 1,024/2,048-entry p/q pairs with 16-bit and 7-bit entries, one pair per function [oberman_favor_1999, oberman_1999]
* choices `decomposition: representative_plus_difference`, `representative_selection: near_group_midpoint`, `compression_contract: lossless`, and `optimization_objective: minimum_total_table_bits` — the T0 decomposition is parameterized by these [hsiao_2014]
* a coefficient-table slot in `piecewise_poly` through which `compressed_lut` can supply T0 storage — the compression applies to the zero-order table of a piecewise polynomial evaluator [hsiao_2014]
