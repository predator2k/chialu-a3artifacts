# priority_encoder: proposed changes to the space

* `output_form` value `one_hot_only` — the reported encoders assert exactly one output without a binary-encoding stage [delgado_frias_2000, wang_2000, huang_wang2003]
* choice `circuit_style: {static, dynamic_pass_transistor, np_domino_parallel, np_domino_series_low_power}` — every reported design is dynamic and the parallel versus series evaluation network sets speed against power [delgado_frias_2000, wang_2000]
* choice `race_rescue: {none, lookahead_controlled_pmos_correction}` — series-connected dynamic gates need a correction circuit for the cascaded n-type race [wang_2000]
* choice `priority_policy: {fixed_wired, configurable}` — the reported priority changes only through wiring [delgado_frias_2000]
