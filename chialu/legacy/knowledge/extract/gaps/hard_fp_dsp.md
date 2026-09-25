# hard_fp_dsp: proposed changes to the space

* `fp_format` values `fp64` and a dual-fp32 lane composition — several evaluated blocks are double precision, though the standalone fp64 FPU tiles are island-style tiles rather than logic inside a DSP slice and may deserve their own family [beauchamp_2006, beauchamp_2008, chong_2009, ho_2009]
* `fp_format` values for the Agilex `HP`, `bfloat16` and `bfloat16+` reduced-precision modes, which `fp16_fp32` and `bf16_fp32` collapse [pasca_2023]
* choice `ieee_feature_subset` (subnormal handling, flags, supported rounding modes) with `subnormal_behavior: flush_input_and_output` — the hardened modes omit IEEE features to limit area, and the omission is a design decision [boutros_2021, pasca_2023, langhammer_2015b]
* choice `fixed_point_cohabitation: unified_overlay` and `fp_adder_integration: separate_malleable_unit` — the FP multiplier reuses the 27x27 fixed-point pipeline while the FP adder shares no arithmetic logic [langhammer_2015, langhammer_2015b]
* choice `subnormal_resource_sharing: {none, direct, fp_adder_reconfigured_as_multiplier_handler}` — configuration-time sharing gives adder or multiplier subnormal handling at about 1 percent block area but not both at once, direct support costs about 4 percent of the arithmetic area [langhammer_2015, langhammer_2015b]
