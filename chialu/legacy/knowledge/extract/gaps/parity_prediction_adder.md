# parity_prediction_adder: proposed changes to the space

* choice `half_sum_check: Bool` — the grouped predictor reaches complete single-gate coverage only with a check of input parity and half-sum signals [langdon_tang_1970]
* choice `parity_predictor_input: {operand_parity, internal_group_signals}` — group parity can be predicted from generate/transmit and half-sum signals without operand parity bits [langdon_tang_1970]
* choice `checked_signal: {sum_outputs, carries}` — distinguishes double-rail checking of the carries from double-rail checking of the sum outputs [nicolaidis_1993]
* `carry_scheme` value separating checked partial carry replication from conventional unchecked carry duplication — the two differ in fault security and in sharing [nicolaidis_2003]
* choice `replica_cell_style: {independent_outputs, shared_propagate}` — the compact replica cell shares P only under a stated fault condition [nicolaidis_1997]
* `comparator` slot annotation for an embedded two-rail checker (input_code two_rail, embedded true) that also emits carry parity [nicolaidis_2003, nicolaidis_1993]
* a base-b generalization (`error_combination_operation: digitwise_modulo_b`) or a decimal variant with the corrective-6 effect folded into the prediction — the parity relation holds digitwise in any base and the decimal redundancy-bit adder predates the binary one [garner_1966, richards_1955__s09]
* choice `parity_convention` (redundancy bit 1 for even) — polarity of the check bit differs between sources [richards_1955__s09]
