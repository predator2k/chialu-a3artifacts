# self_checking_datapath: proposed changes to the space

* choice `checking_property: {self_testing, fault_secure, totally_self_checking, strongly_fault_secure, code_disjoint, strongly_code_disjoint, weakly_code_disjoint}` — the code-space property fixes which fault mappings and fault sequences the unit must survive [lala_2001]
* `encoding` value `berger_check_prediction` — a datapath that emits Berger codewords from counted internal carries is a codeword-emitting unit with a different code [lo_1992]
* a base-ALU slot with `ripple_carry`, `manchester_carry_chain`, `carry_lookahead` — the fault behaviour and the required modifications differ per carry structure [lo_1992]
* choices `information_unit_partition: separate_arithmetic_and_logic`, `prediction_carry_source: internal_alu_carries`, `implemented_operations` — separating arithmetic from logic prevents bidirectional errors and the predictor observes the functional carries rather than a duplicate [lo_1992]
* choice `checking_scheme: {output_checking_parity_generation, carry_checking_parity_prediction}` — output-code checking and checked-carries-plus-predicted-parity differ in latch duplication and translator cost [nicolaidis_1993]
* choice `code_translation: {duplicated_input_latches, checker_as_parity_generator, avoided_by_parity_prediction}` — conversion between parity-coded and double-rail portions is a distinct cost [nicolaidis_1993]
* choice `check_carry_generation: ripple_slice_from_normal_predecessor` — ripple check carries driven from the normal carries avoid duplicating the fast carry block [nicolaidis_2003]
* choice `carry_duplication_scope: partial_shared_sum_logic` — sharing logic between normal carry, check carry and sum keeps fault security at lower cost [nicolaidis_2003]
* choice `checker_parity_fusion: Bool` — the two-rail checker doubles as the carry-parity generator [nicolaidis_2003, nicolaidis_1993]
* choice `adder_cell_sharing: {complete_carry_duplication, shared_propagate}` for array cells — duplicated carries may share the propagate signal with the sum [nicolaidis_duarte_1999]
* `encoding` value `biquinary_one_hot_plus_carry_no_carry` with checked output code one-of-five plus one-of-two — the decimal form checks the quinary sum lines and the complementary carry pair [richards_1955]
