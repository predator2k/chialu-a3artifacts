# parity_prediction_multiplier: proposed changes to the space

* choice `replica_cell_style: {type_1_independent, type_2_shared_propagate}` — independent redundant-carry generation versus shared-propagate cells decides area overhead (about 75-80 percent against about 47 percent) and worst-case parity delay [nicolaidis_1997]
* choice `partial_product_parity_source: {dedicated_row_predictors, reused_decoder_checker_outputs}` — the reduced-cost Booth construction derives decoded-line parities from the double-rail checker instead of separate row-parity circuits [nicolaidis_duarte_1999, nicolaidis_1999]
* a `final_adder` slot — a ripple final adder keeps the cellular proof, a carry-lookahead adder needs redundant carries and a double-rail checker, and a Kogge-Stone adder moves the residue-versus-parity crossover from 16x16 to 32x32 [nicolaidis_1997, nicolaidis_duarte_1999]
