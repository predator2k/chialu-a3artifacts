# linear_chain: proposed changes to the space

* loop_adder_form {carry_save_row, cpa} — a carry-save row in the loop with one terminal CPA versus a full adder per step [kenney_2005, eisen_2007]
* correction_speculation_span Int for decimal chains — assuming the first one or two additions need no correction removes the selection multiplexers from the critical path [kenney_2005]
* operands_per_step Int — the POWER6 DFU pairs digits so multiple generation alternates with accumulation [eisen_2007, schwarz_2009]
