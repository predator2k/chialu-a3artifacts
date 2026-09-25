# fpga_carry_chain: proposed changes to the space

* choice `chain_boundary: {crosses_cluster_boundaries, stops_at_cluster_boundary}` plus `direction` / `chain_extent` / `attachment_points_per_clb` — Xilinx chains cross CLBs vertically, Altera chains stop at the LAB, and the modeled column-wide upward chain has two entry points per CLB [pasca_2011, beauchamp_2006, beauchamp_2008]
* choice `hardened_carry_mechanism: {ripple, carry_skip, carry_lookahead}` and `arithmetic_bits_per_logic_element: {1, 2, 4}` — commercial fabrics harden more than ripple, and Agilex/Versal-class elements carry two or more arithmetic bits [boutros_2021]
* choice `cell_state_set: kill_propagate_inverse_propagate_generate` with arbitrary in-row chain breaks and one-chain-per-row placement — the configurable carry cell supports non-adder prefix functions [hauck2000]
* choice `register_control_use: {synchronous_clear_zero, synchronous_load_bypass}` — LE register controls implement ALU functions without multiplexers [metzgen_2004]
* `chain_segment_length` domain admitting 20 — the Stratix-III/-IV LAB-local chain is 20 bits [pasca_2011]
* choice `carry_access: {portable_sum_recovery, device_specific_tap}` and `generic_prefix_mapping: {general_purpose_equations, manual_MUXCY, binary_addition_transformation}` — portable code recovers prefix outputs from sums rather than tapping carries [pasca_2011, preusser2009]
* choices for FPGA granularity, dedicated-carry availability, placement pitch and routing-resource constraints — fine-grained fabrics without carry logic select architectures by regularity and routability [zimmermann1997]
