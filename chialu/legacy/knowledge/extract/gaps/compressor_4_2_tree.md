# compressor_4_2_tree: proposed changes to the space

* reduction_block / wiring_regularization / block_customization choices — recurring 7-row subblocks, recurring wire shifters and boundary-block variants are the paper's principal design axes [goto1992]
* logic_decomposition {xor_xnor_mux, ...}, xor_xnor_cell and logic_style {dpl, hybrid} beyond the three circuit_style values [chang2004]
* tree_shape and cell_feedthrough_lines choices — Wallace-shaped 4:2 tree with two feedthrough lines per cell [mori1991]
* critical_path_gate_stages Int — the three-stage pass-transistor compressor versus the four-stage full-adder construction [ohkubo1995]
* reduction_schedule mixed_4_2_and_3_2 and late-row bypass of the first level — production FMAs mix compressor kinds across cycle boundaries and route denormal-correction rows late [trong_2007, eisen_2007]
* serial (5,3)-counter slice for the squarer reduction slot [ienne1994]
* direct comparison of 3:2, 4:2, 9:2 and short-CPA reduction trees as compressor_kind evidence [oklobdzija1995]
