# online_pipeline_composition: proposed changes to the space

* component slots for the network's stages (aligned sum-of-squares, square root, division, on-the-fly conversion) — the rotation-factor unit is a specific chain of on-line operators and the family has nowhere to name them [ercegovac_lang_1988]
* choice `initiation_interval: Int` — recursive networks are sized by ceil(n/II) multioperation modules [ercegovac_2004#s01]
* choice `communication_width_digits: Int[1..N]` — inter-operator bandwidth B in digits per variable sets the bandwidth-limited speedup [ercegovac_1984]
* choice `operand_interface: {parallel, byte_serial_input_online_output}` — inputs may load byte-serially and results are delivered in both bit-parallel and on-line forms [ercegovac_lang_1988]
