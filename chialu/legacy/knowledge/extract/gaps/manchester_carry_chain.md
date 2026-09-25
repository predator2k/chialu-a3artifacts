# manchester_carry_chain: proposed changes to the space

* choice `buffer_combination: {inverter, NAND_gate}` — the block-output element that restores the carry and merges the bypass changes the carry-skip delay against the buffer delay [chan_schlag1990]
* value for a conflict-free bypass-and-adding scheme under `variable_skip` or a new `bypass_scheme` choice — the 108-b tree-multiplier CPA uses a bypass the current Bool cannot classify [goto1992]
* extend `chain_segment_length` domain beyond 8 — the original junction-transistor chain restores the carry level only after ten stages [kilburn1959]
* `circuit_style` value for saturated junction-transistor bilateral switches — historical technology of the origin paper, outside the current domain [kilburn1959]
* choice `predischarge_level: {VDD, VSS}` (or a precharge-phase choice) — predischarging the dynamic chain to VSS removes the VDD-Vt threshold delay, and precharge timing is a distinct design decision [dobberpuhl_1992, mead_conway1980__s06]
* choice `group_term_inputs: {generate_propagate, ling_h_i}` — a distributed Manchester gate can consume Ling pseudo-generate/propagate terms directly from the operands [naffziger1996]
* `self_checking_datapath` base-ALU slot admitting `manchester_carry_chain` (with `ripple_carry`, `carry_lookahead`) — fault behavior and required modifications differ per base adder [lo_1992]
