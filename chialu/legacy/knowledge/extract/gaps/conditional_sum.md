# conditional_sum: proposed changes to the space

* choice `selection_signal_buffering: {none, cascaded_cmos, progressive}` (or a fanout class) — one select signal drives up to n/2 multiplexers, and the reported designs differ in the buffer hierarchy that absorbs that fanout [rothermel1989, montoye_1990, zimmermann1997]
* choice `conditional_cell_style: {static_gate, transmission_gate}` — `mux_style` does not record the circuit style of the duplicated sum/carry cell, which the TGCS adder also builds from transmission gates [rothermel1989]
* choice `select_signal: {carry_in, overflow_or_carry_logic}` — the compound adder A+B / A+B+1 selects by rounding-derived overflow and carry logic rather than by an input carry [santoro_1989]
* choices for unequal input-arrival profiles, linear LSB-to-MSB block-boundary synthesis, and conditional-carry/conditional-sum hybridization — the multiplier final adder places block boundaries at arbitrary bit positions from per-bit arrival times and uses conditional-sum only for the last block [yehjen2000]
* family `pyramid_carry_assimilation` — its stored-carry phased assimilation differs from conditional-sum selection [lehman_burla1961]
* `sparse_prefix_hybrid.sum_block` slot admitting `conditional_sum` — two sparse-tree designs use a conditional-sum precompute/select block that the slot domain cannot name [zeydel2010, zlatanovici2009]
