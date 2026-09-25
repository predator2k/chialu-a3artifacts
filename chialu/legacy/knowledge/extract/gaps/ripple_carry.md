# ripple_carry: proposed changes to the space

* `full_adder_cell` extended with a configurable FPGA LUT/mux cell, a nine-gate AND/OR/inverter cell, DCVS / DCVS-Domino / static-differential self-checking cells, a lower-part approximate cell, and the Boolean-switch / diode / vacuum-tube / Kirchhoff realizations — the evaluated implementations name cells the current enumeration cannot express [hauck2000, townsend_2003, nicolaidis_1993, zervakis2019, richards_1955#s05]
* choice `pipeline_structure: {unpipelined, classical_chunked, alternative_chunked}` plus `shift_register_extraction: Bool` — frequency-driven FPGA pipelining registers the carry every α cells and either synchronizes inputs or propagates partial sums, with optional SRL use for the synchronization registers [pasca_2011#s06]
* choice `radix` (2, 10, or a small power of 2 or 10) — the chain stage digit is a parameter of the textbook definition [muller_2018#s08]
* choice `carry_stage_realization: {half_adder_pair_or, factored_switching, decomposed_two_half_adders, counter_accumulator}` — the physical form of the carry stage decides whether a propagated carry crosses one or two delays per order [richards_1955#s05, sklansky1960b]
* choice `timing_style: self_timed` — completion signalling turns the log2(n) average carry length into average-case latency [zimmermann1997#s03]
* choice `intercell_buffering: {none, every_other_cell}` — pass-device and transmission-gate cells need restoring buffers between alternate cells [shams2002]
* choice `fpga_cell_variant: {basic, optimized_mux_cell}` — the configurable carry cell has a basic two-mux and a shortened one-mux form [hauck2000]
* `final_cpa` / terminal-adder slots in the approximate multiplier, `serial_serial_parallel` and `squarer` families — the evaluated designs explicitly instantiate `ripple_carry` as the final adder [frustaci2020, gnanasekaran1985, yoo1997]
* `self_checking_datapath` base-ALU slot admitting `ripple_carry`, `manchester_carry_chain` and `carry_lookahead` — fault behaviour and required modifications differ per base adder [lo_1992]
* `sparse_prefix_hybrid.sum_block` value for a dual-rail conditional-sum block whose conditional carries ripple inside each 4-bit group [mathew2003]
