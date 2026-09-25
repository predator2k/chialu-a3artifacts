# reduced_precision: proposed changes to the space

* split `replica_width_bits` into total checker width and retained mantissa width, and admit values such as 7 and the even mantissa lengths 4 to 14 — the papers tune the mantissa length while the sign/exponent fields stay full width, and 7 is outside the current range [eibl_2009, seetharam_2013]
* choice `comparison_adjustment: {two_lsb_difference, fixed_tolerance}` with a tolerance value — the two-bit difference mapping and the allowed base-10 difference of 7 fix the error bound and coverage and are not expressed by `bound_type` alone [eibl_2009, seetharam_2013]
* choice `unchecked_case_policy` covering unlike-sign operands with exponent difference zero or one and infinity/NaN/denormal operands — both floating-point checkers gate the check off in these cases [eibl_2009, seetharam_2013]
* choice `checker_rounding: {omitted, kept}` — removing the checker rounder cuts replica area because the tolerated compare difference subsumes rounding [eibl_2009]
* choice `decision_threshold_rule: maximum_error_free_difference` — the threshold is derived from the replica truncation error so that an error-free main output never raises an alarm [shim_2004]
* choice `operating_point_search: joint_VOSF_and_replica_precision` — the replica precision and the voltage-overscaling factor are searched jointly under a noise-power bound [shim_2004]
* slot `protected_datapath` for MAC/FIR/FFT structures replicated at reduced precision, including an RNS FIR — the DSP form protects a whole filter or butterfly rather than one adder or multiplier [shim_2004, chang_2015]
