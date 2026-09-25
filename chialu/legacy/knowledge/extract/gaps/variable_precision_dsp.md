# variable_precision_dsp: proposed changes to the space

* `native_widths` values `9_18_36` (Stratix II) and `9_12_18_36` (Stratix III/IV half-DSP) — the shipped width sets do not match any current value [kuon_2007, pasca_2011#s03]
* choice `multiplier_adder_mode: {independent, two_multiplier_adder, four_multiplier_adder}` — the block's adder tree selects independent products or summed products [pasca_2011#s03]
* choice `block_partition: {whole_dsp, two_half_dsp}` — Stratix III/IV split the block into independently usable halves that cascade into neighbours [pasca_2011#s03]
* choice `native_operation_formats: {int9, int4}` — low-precision MAC modes added without changing the routing interface [boutros_2021]
