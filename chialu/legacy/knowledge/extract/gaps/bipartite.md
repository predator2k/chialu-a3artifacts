# bipartite: proposed changes to the space

* choices `input_partition: n0/n1/n2` with unequal subword sizes and `table_word_widths: p0/p1` — the split determines both table dimensions and the error bound [muller_1999, muller_2016#s05, schulte_1997, schulte_1999]
* choice `guard_bits: Int` (2 or 3 in the shipped constructions) — controls coefficient-rounding error and word widths [schulte_1997, schulte_1999, muller_2016#s05]
* an output-combiner slot `{carry_propagate_adder, booth_encoder}` — the redundant pair either resolves to two's complement or feeds a multiplier directly [schulte_1997, schulte_1999]
* choice `coefficient_selection: {closed_form_two_term_taylor, midpoint_expansion}` — the symmetric variant derives its coefficients from a centered expansion [schulte_1999, muller_2016#s05]
* an accuracy-contract choice `{faithful_one_ulp, bounded_absolute}` — SBTM ships faithful rounding, the textbook bound is absolute [schulte_1997, muller_2016#s05]
* an input-subword-count choice shared with multipartite — more than three subwords is the multipartite generalization [muller_1999, dedinechin_2005]
