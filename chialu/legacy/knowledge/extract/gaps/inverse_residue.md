# inverse_residue: proposed changes to the space

* a generator/checker-style choice for the four-bit end-around-carry residue circuit — STAR's checker computes the whole-word residue with an end-around-carry adder rather than a two-rail compare [avizienis_1971, avizienis_gilley_1971]
* `comparator` slot values beyond `two_rail_tree` (modulo-15 checksum accumulator plus equality test) — the encoded-operand algorithms compare through an accumulated checksum [avizienis_1973]
* choice `carry_out_correction` (increment check sum modulo 2^a-1 on discarded carry) — two's-complement main arithmetic needs the discarded-carry policy, and the fault analysis of that signal is part of the coverage claim [avizienis_1973]
* choice `main_arithmetic_representation: {ones_complement, twos_complement}` — the check-processor coupling differs between the two [avizienis_1973]
* parameterized `modulus` values 2^b-1 and 2^(k+1)-1 (also for `residue`) — byte and line checks use moduli tied to byte width and byte count rather than the fixed {3, 7, 15} [avizienis_1985]
* choice `dimensionality: {one_dimensional, two_dimensional}` (also for `residue`) — superimposed byte/line residues give locating syndromes [avizienis_1985]
* choice `correction_scope: {detect_only, single_bit_and_single_line_unidirectional}` — the two-dimensional code corrects single-bit and most single-line unidirectional errors [avizienis_1985]
* ambiguity and mis-correction policy for multiple candidate lines and three-adjacent-line errors — the correction step needs a stated behaviour where syndromes are not unique [avizienis_1985]
* choice `check_location: {result, data_bus}` — STAR checks a word concurrently while it is transmitted [avizienis_gilley_1971]
