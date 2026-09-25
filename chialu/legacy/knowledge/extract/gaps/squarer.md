# squarer: proposed changes to the space

* choice `output_width_policy: {full, same_as_input}` — fixed-width squarers keep the W-bit quantized result and omit the low-half hardware [cho2003]
* choice `device_mapping: {virtex4_shifted_cross_product, stratix_independent_submultipliers, virtex5_symmetric_tiling}` — DSP-specific realizations of the symmetry differ in block count and LUT cost [pasca_2011#s07]
* `reduction` value for a serial (5,3)-counter slice, plus `output_latency_cycles` and `activation_control` choices — the bit-serial squarer performs iterative local reduction rather than a tree [ienne1994]
* choices `partial_product_generator: {BPPG1, BPPG2}`, `reduction_architecture: {carry_save, Wallace_Tree}` and `sign_extension_handling: prevention_constant` — the Booth-folded designs vary the generator, the reduction and the sign handling separately [strollo2003]
* choices `truncation_columns`, `correction: {constant, variable}` and `input_truncation_bits` — truncated squarers for quadratic interpolators are parameterized by unformed columns, correction type and input bits removed [walters2005]
* a `final_adder` slot — every evaluated squarer reduces to sum/carry vectors and assimilates with a carry-lookahead or ripple adder [wires1999, yoo1997]
* choice `primitive_squarer_size` — the divide-and-conquer recursion base width sets the gate-count and critical-path trade [yoo1997]
* squarer slots in `piecewise_poly`, `gpu_multifunction_interpolator` and `poly_seed` — the quadratic evaluators list the specialized squarer as a major added component [decaro_2009, decaro_2017, oberman_2005, pineiro_2002]
