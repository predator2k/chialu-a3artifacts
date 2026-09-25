# rns_dsp_datapath: proposed changes to the space

* a reduction/accumulator slot per channel admitting `carry_save_datapath` — the transpose FIR stage keeps its multiply-accumulate in a modulo carry-save tree [conway_nelson_2004]
* choice `filter_structure: {transpose, direct}` — each transpose stage combines its product terms with the preceding stage's carry-save value [conway_nelson_2004]
* `input_encoder` / `output_decoder` slots admitting `rns_forward_encoder` and `rns_reverse_converter`, with the encoder placed before or after the delay memories [jenkins_leon_1977]
* choice `modulus_cost_objective: stage_area_delay_product` — the modulus set is chosen by exhaustive per-modulus area-delay costing for the required dynamic range [conway_nelson_2004]
