# bridge_fma: proposed changes to the space

* choice `product_rounding: {intermediate_rounded, unrounded_single_round}` — the cascade rounds the product before the add while the bridge rounds once [chong_2009]
* choice `augend_arrival: {with_multiply, deferred_until_add_pipeline}` — the deferred augend is what lets dependent FMAs issue at add latency [lutz_2011]
* choices `unrounded_product_interface` (sign plus 11-bit exponent plus 105-bit fraction) and separate multiply/add subpipeline latencies — the inter-pipeline format and the 2+2 stage split fix the FMA and add latencies [lutz_2019]
* choices `bridge_clock_gating: Bool` and `standalone_parallel_execution: Bool` — both are explicit properties of the bridge architecture [quinnell_2007, quinnell_2008]
* split `cascade_mul_then_add` into a natively cascaded multiplier-then-adder unit and a retrofit that bridges existing separate units — the two design intents sit under one value today [galal_2011]
* a support level for IEEE denormals and the rounding-mode set on `bridge_fma`, measured at 5 to 10 percent; `tensor_core_mixed_precision_mac` has `subnormal_support` and `fp8_training_datapath` has `flush_subnormals` [galal_2011]
* `cascade_product_rounding` values `unrounded_forwarded` and `active_ieee_mode` — the generator forwards an unrounded intermediate result, while the SPARC64 unfused instructions round in the unit's active IEEE-754 mode [galal_2013, naini_2001, quach_1991]
* a rounding-contract choice on the FMA families — a MAF is called IEEE compatible when it delivers the result of a sequential FMPY and FADD, which the single-rounded bridge does not [quach_1991]
* choice `accumulation_latency_relation: half_of_mul_add` and a close/far path-gating choice on the cascade's adder — the separate pipelines let a dependent accumulate issue early and let one addition path stay unclocked [galal_2013]
