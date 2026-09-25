# funnel: proposed changes to the space

* `window_mux_radix` mixed sequences such as 2-2-2-2-2, 2-4-4 and 4-8 — the evaluated networks mix valencies across stages [huntzicker_2008]
* `amount_preprocess` value `ones_complement_for_left` — the documented design complements the amount for left shifts to select window 31-k [huntzicker_2008]
* choices `multiplexer_circuit: {ganged_tristate, pass_transistor, fanout_splitting}`, `floorplan: {naive_7_row, folded_11_row, compact_folded_8_row, folded_overhang}`, `control_arrival: {simultaneous, shift_type_early}`, `operation_subset: {all_five, shifts_only, right_rotate_only}` — circuit style, floorplan, control arrival and supported operations change the energy-delay curve [huntzicker_2008]
