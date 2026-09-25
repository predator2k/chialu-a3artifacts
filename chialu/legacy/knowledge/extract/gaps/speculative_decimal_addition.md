# speculative_decimal_addition: proposed changes to the space

* choice `subtraction_style: decimal_end_around_carry` — the z196 adder evaluates the effective-subtract magnitude without first comparing operands [carlough_2011]
* choice `subtraction_correction: plus_or_minus_6` — subtraction precomputes uncorrected and -6-corrected candidates [schwarz_2002]
* choice `digit_code_path: {bcd8421, bcd5211_to_bcd5421_excess3_to_bcd5211}` — an excess-3 internal code makes decimal carries equal binary carries at digit positions [vazquez_2007]
* choices `operand_representation: sign_magnitude`, `pre_correction_structure: binary_3_2_csa_with_conditional_bias`, `rounding_implementation: direct_mode_conditions` — the sign-magnitude adder folds complementing and +6 into a carry-save pre-correction and implements one rounding condition per mode [vazquez_2009]
* choice `injection_encoding` (rounding-mode/sign-dependent digit pair at R/S) — the injected value defines which cases become truncation [wang_2009, wang_2007b]
* `carry_network` annotations for a sparse prefix tree of valency 4 with conditional digit sums and for a compound adder emitting S and S+2 — neither output shape is named by the existing adder families [vazquez_2007, vazquez_2009]
