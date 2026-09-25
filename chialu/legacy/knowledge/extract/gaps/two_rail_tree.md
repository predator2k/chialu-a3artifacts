# two_rail_tree: proposed changes to the space

* choice `realization_form: {sum_of_products, product_of_sums, merged_alternating_levels}` — the majority-function gate organization sets gate count, levels, fan-in and the size of the diagnostic test set [anderson_metze_1973]
* choice `input_partition: {equal_halves}` — direct k-out-of-2k checking is self-testing only when both input groups hold k bits [anderson_metze_1973]
* a translator slot (`translator_front_end: {none, code_disjoint}`) — arbitrary m-out-of-n codes are checked through a totally self-checking code-disjoint translator to k-out-of-2k [anderson_metze_1973]
* choice `parity_output_reuse: Bool` — the checker outputs double as predicted-parity or decoded-signal parity signals when the tree is embedded [nicolaidis_2003, nicolaidis_duarte_1999]
* `input_code` value `m_out_of_n` as a checker vocabulary item outside the morphic-cell mechanism — the m-out-of-n checker constructions are not two-rail trees [marouf_friedman_1978, anderson_metze_1973]
* comparator slots elsewhere (`an_code`, `inverse_residue`, `carry_select`, `time_redundancy`, `duplication`, `multi_residue`) admit only `two_rail_tree` — the documents use a modulo-15 checksum equality test, an ordinary equality comparator, XOR comparison with a metastability detector, a majority voter and a syndrome decoder/corrector [avizienis_1973, johnson_1988, ernst_2003, townsend_2003, rao_1970, vasudevan_2007]
