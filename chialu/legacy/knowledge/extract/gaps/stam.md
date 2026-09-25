# stam: proposed changes to the space

* express `tables` symbolically as m offset tables plus one table of initial values (m + 1) rather than Int[2..4] — the multipartite paper counts m TO_i tables and one TIV [dedinechin_2005]
* choices `subword_widths: {equal, different}` and `expansion_point: interval_midpoint` — the subwords may differ in width and the expansion is around the midpoint selected by the first two subwords [muller_1999]
* choice `slope_addressing: {shared_C, per_table}` — STAM's shared slope subword is the constraint the multipartite generalization relaxes [dedinechin_2005]
