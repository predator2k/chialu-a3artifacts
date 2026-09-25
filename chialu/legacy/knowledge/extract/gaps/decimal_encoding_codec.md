# decimal_encoding_codec: proposed changes to the space

* `significand_encoding` values `packed_bcd`, `zoned`, `two_out_of_five`, and the 4-bit 0001-1001/1010 digit code, with a `conversion_pair: zoned_packed` — the z900 unit packs and unpacks up to 32 digits between zoned and packed, and the 1959 comparison translates between 5-bit and 4-bit digit codes [busaba_2001, buchholz_1959]
* choice `codec_implementation: {lookup_table, boolean_logic}` with invalid-code signaling — DPD compression and expansion are specified as either a software table or hardware gates, and a table translation can map an invalid input to an out-of-range code [cowlishaw_2002, buchholz_1959]
* choices `block_digits: {2, 3}` and a parity-behaviour flag for Chen-Ho — the two-digit mapping preserves BCD parity while the three-digit mapping does not [chen_ho_1975]
* `codec_placement` value at the arithmetic-unit/memory interface with expanded BCD kept inside the unit — the Chen-Ho paper places compression at the memory boundary [chen_ho_1975]
* split `codec_placement` into input expansion and output compression placements, with `output_codec_placement: before_result_register` — the POWER6 divider expands at two operand registers and compresses before the result register [schwarz_2007]
* choice `internal_arithmetic_encoding: {bcd8421, excess_3, redundant_signed_digit}` distinct from the interchange encoding — DPD inputs are paired with BCD, excess-3, or redundant internal digit encodings [wang_2007b, thompson_2004, han_2016]
* choice `implementation_domain: software_binary_integer` for BID — the BID library keeps coefficient arithmetic in binary-integer software rather than decimal hardware [cornea_2009]
* codec slot for this family in `commercial_decimal_fpu` — DPD decode and result encode are explicit milli-ops in the z9 execution path [duale_2007]
