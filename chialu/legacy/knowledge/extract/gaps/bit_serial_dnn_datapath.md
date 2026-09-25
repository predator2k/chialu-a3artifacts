# bit_serial_dnn_datapath: proposed changes to the space

* `precision_source` value combining per-value essential-bit execution with optional per-layer trimming — Pragmatic uses both, and software trimming adds 19% [albericio_2017]
* choices `essential_bit_representation: oneffset_list`, `lane_synchronization: {pallet, per_column}`, `first_stage_shift_control_bits: Int[0..4]` and `synapse_set_registers: {1, 4, 16}` — the oneffset encoding, synchronization granularity, two-stage shift width and synapse buffering set Pragmatic's performance [albericio_2017]
* choice `operand_serialization: {neuron_serial_synapse_parallel, weight_parallel_activation_bsd_serial}` and an MSDF-output choice — which operand is serialized and whether the output is itself a digit stream [judd_2016, moghaddasi_2024]
* a shifted-accumulator slot for the per-cycle reduced sums [judd_2016]
* slots for MSDF-aware ReLU and MaxPool pruning units — the nonlinear functions that terminate lanes [moghaddasi_2024]
* `pairwise_tree.mul` fillable by `bit_serial_dnn_datapath` — the PIPs feed shifted essential-bit terms into per-filter adder trees [albericio_2017]
