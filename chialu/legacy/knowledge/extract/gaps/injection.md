# injection: proposed changes to the space

* injected constant, overflow correction and RNE tie repair as declared choices [even_2000]
* injection_timing {during_reduction, after_reduction} [even_2000, santoro_1989]
* fixed-location injection with bidirectional prenormalization for subnormals [lutz_2011]
* overflow_candidate_generation dual_cpa [oberman_favor_1999]
* result_binades_for_rounding Int — rounding bounded to significands in [1,4) on the R-path [seidel_2001]
* preset biased rounding (slightly toward zero) as a non-IEEE mode value [thornton_1970]
* choice `rounding_points: 2` — the injection is applied at a first and a second rounding point in parallel, the second used when digits 0 to 36 carry a mantissa overflow [lichtenau_2016]
* choice `injection_hole_width` — the width a 2-to-2 CSA compression of the operands frees for the injection term, one bit for binary and four bits for decimal [lichtenau_2016]
* choice `radix_shared_injection_values: precomputed_per_radix` — per-radix injection values, with the binary round, guard and sticky bits mapped onto the padded high digits, let one datapath round both radices without added critical-path delay [lichtenau_2016]
* a `round` slot on the fp adder families — the injection rounder the z13 adder is built around, and Path 2's A+B / A+B+2 compound-adder rounding with fill bits, have nowhere to be recorded [lichtenau_2016, naini_2001]
