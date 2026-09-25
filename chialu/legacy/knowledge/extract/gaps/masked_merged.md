# masked_merged: proposed changes to the space

* `merge_style` value for a rotate-then-AND mask whose signed-right-shift extension comes from the adder unit, with a `sign_extension_source` choice, as in the two-cycle FPGA ALU [metzgen_2004]
* choice `arithmetic_fill: {zero, sign}` so the mask's fill selection is explicit [huntzicker_2008]
* a choice for sharing the merge network between rotation and addition, which removes the adder-versus-rotator result mux in the POWER fixed-point unit [silberman_1998]
* a `cycles: {1, 2}` or schedule choice for the two-cycle form that builds the mask and partially rotates in the first cycle and reuses the rotator in the second [metzgen_2004]
