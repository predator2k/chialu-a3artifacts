# approximate_mac_nn: proposed changes to the space

* `multiplier_source` value `power_of_two_codebook` — ShiftCNN replaces each product with N shift/sign-flip terms selected from signed power-of-two codebooks without retraining [lee_1989]
* a multiplier slot fillable by an alphabet-set multiplier, and a choice `exact_zero_multiplication: Bool` — alphabet sharing is a component rather than a source label, and evolved multipliers must keep zero-operand products exact [sarwar2018, mrazek2016]
* a cross-unit DVAFS family — precision scaling by subword parallelism plus voltage and frequency applies beyond the NN-specific family [moons2017]
* `precision_scaling` value `assisted_training` and a choice `layerwise_weight_input_precision: independently_profiled` — full-precision training followed by target-width rounding, and per-layer weight/input widths [sarwar2018, moons2017]
* a design-flow choice for iterative application-quality feedback that reduces the error budget after retraining fails [mrazek2016]
* choices `approximation_assignment: per_weight_per_layer` and `systematic_error_compensation: bias_update`, and `approximation_placement: {uniform, layer_mixed}` — per-range multiplier modes with filter-bias correction, and larger alphabets only in concluding layers [tasoulas2020, sarwar2018]
