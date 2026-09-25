# ling_prefix: proposed changes to the space

* `sum_recovery` value for true-carry recovery followed by a Shannon-expanded output stage — the 64-bit modified Ling adder recovers the carry from H and an inclusive-OR propagate before the output stage rather than selecting or XOR-correcting [bewick1994]
* `sum_recovery` value `complementing_signal` (or a choice distinguishing complementing-signal from carry-signal propagation) — the 1966 adder propagates a complementing pulse that inverts preliminary sum bits instead of a carry [ling1966]
* `topology` value `ladner_fischer` — it is implemented and measured as a Ling-adder topology [dimitrakopoulos2005]
* choice for independently selecting the even-tree and odd-tree topologies, plus preprocessing pair generation (from G/P or direct from inputs) and carry-input integration (increment stage or extra preprocessing bit) — the parity-tree Ling adder exposes these as separate decisions [dimitrakopoulos2005]
* choice `pseudo_carry_generation: {from_generate_propagate, direct_operand_expansion}` and a `circuit_style` value for dual-rail dynamic CMOS — direct H4 expansion in one fan-in-4 dynamic gate depends on the circuit style [naffziger1996]
* fan-in/fan-out constraint choice — uniform loading of four is a defining implementation condition of the original design [ling1981]
* choices `group_propagate_form: shifted_product_I` and `mixed_signal_polarity: positive_H_negative_I` — the ECL implementation shifts the I indices and mixes polarities in the first lookahead layer [bewick1994]
* `bitwise_merge` Bool — integration of bitwise operations into the first pseudo-carry stage is a separate decision in the 65-nm designs [zeydel2010]
* `low_product_zero_detection` Bool — the 106-bit multiplier final adder reports whether its low 40 bits are exactly zero instead of emitting them [bewick1994]
