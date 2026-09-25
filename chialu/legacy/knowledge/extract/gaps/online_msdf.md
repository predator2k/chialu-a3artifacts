# online_msdf: proposed changes to the space

* choice `dividend_form: {online, bit_parallel}` — a bit-parallel dividend cuts the online delay from 4 to 3 [ercegovac_lang_1988]
* choice `quotient_selection_width: Int` and `estimate_fraction_bits: Int` — the leading nonredundant digits and estimate precision used for selection (four digits in JANUS, three fractional bits in the textbook) [guyot_1989, ercegovac_2004#s01, ercegovac_lang_1988]
* `radix` domain extended to 10 and an arbitrary-radix derivation — the original paper derives radix-r with p-digit sets and K=2/3 [trivedi_1977]
* choices `operand_representation: {nonredundant, symmetric_redundant}` and `quotient_digit_set` redundancy — both decide selection feasibility and carry-free updates [trivedi_1977]
* a `digit_select` slot with `qds_table` — the textbook implementation selects from a table that the structure section does not expose [ercegovac_2004#s01]
