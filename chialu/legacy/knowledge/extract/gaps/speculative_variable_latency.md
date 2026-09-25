# speculative_variable_latency: proposed changes to the space

* `base_adder` slot admitting `parallel_prefix` (Han-Carlson, Brent-Kung), `segmented_carry_speculative` (the ACA) and `fpga_carry_chain` — the speculative designs on record build on a pruned Han-Carlson graph, a Brent-Kung BLC datapath, an ACA, and a split FPGA carry chain rather than on the three admitted bases [esposito2015, nowick1996, verma2008, metzgen_2004]
* choice `detection_precision: {necessary_only, necessary_and_sufficient}` — a coarse or conservative detector aborts correct results and raises average latency, a precise one lowers the error probability [esposito2015, nowick1996]
* abort-network parameters (propagate literals per product, kill-augmentation bits, per-product local late enables, number of matched delays) — the nine detector variants trade detection area against early-completion rate [nowick1996]
* choice `carry_values_tracked: {ones_only, both}` with a completion-encoding choice (dual-line carry/no-carry) — tracking both 0 and 1 carries raises the average maximum sequence from 4.6 to 5.6 stages and fixes the completion condition [gilchrist1955, richards_1955, macsorley1961]
* explicit non-speculative self-timed mode — the completion adders wait for completion without predicting or correcting a result [gilchrist1955]
* completion-gate implementation choice (cascaded two-input, unit-delay multiple-input, log-depth multiple-input) and a dependent-carry speed ratio — both change the independent-dependent carry adder's time and efficiency substantially [sklansky1960b]
* recovery-adder slot for the n/k-bit `carry_lookahead` network — the VLSA corrects with a separate lookahead over the block carries [verma2008]
* choice `boundary_carry_prediction` — the split FPGA adder predicts the carry between halves and needs generalized prediction because subtraction often yields a 1 [metzgen_2004]
