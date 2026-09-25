# recursive_karatsuba: proposed changes to the space

* choice `partition_count: Int[2..15]` — the thesis implements direct 3/4/5/6/7/15-part decompositions beyond two-way recursion [pasca_2011]
* choices `tile_dimensions` and a gcd-based `rectangular_alignment` condition — rectangular base multipliers pair subproducts only at aligned weights [kumm2018]
* `base_multiplier` as a component slot admitting `dsp48_style_slice` — the concrete architecture depends on the block's multiplier and pre-adder structure [kumm2018]
* choice `difference_form: {subtractive, additive}` — the FPGA forms precompute X_i - X_j rather than sums to fit signed multipliers, and flipping the difference product to (A1 - A2)(B2 - B1) makes the recombination an addition that reuses an existing (4,2) compressor [pasca_2011, zhang_2018]
* `split_kind` value for a two-way split into unequal parts — the 11-bit mantissa splits into a 3-bit high part and an 8-bit low part [zhang_2018]
