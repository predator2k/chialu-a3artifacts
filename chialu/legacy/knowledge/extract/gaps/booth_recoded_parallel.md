# booth_recoded_parallel: proposed changes to the space

* `hard_multiple_gen` values for the +-5 and +-7 multiples of radix-16 Booth — the generator leaves those multiples to standard synthesis, and the domain names only the 3x forms [galal_2013]
* choice `booth_mux_gate_style: {plain, xnor_on_multiplicand_shared}` — moving the mux XNOR onto the multiplicand and sharing the term with the neighbouring mux cuts 0.5 CSA gate delay at no extra area [galal_2013]
* choice `array_extent` or `multiply_array_passes` with `multiplier_operand_split_bits`, `first_pass_feedback` and `deferred_hot_one` — a significand array narrower than the operand is iterated over several passes, with the pass's sum and carry fed back into free tree inputs and the last row's hot one deferred to the next pass [jessani_1996, jessani_1998]
* `sign_extension` value for a reduced left-edge banded matrix — the encoded rows are 57 bits for pp0 and 56 bits for pp1 through pp26 rather than one extension pattern per row [jessani_1998]
* a reduction-tree parameter for row capacity against rows used — the tree admits 16 partial products per cycle while 14 are used [jessani_1998]
* choice `multiplier_bits_per_cycle` — a looping quad-precision multiplier recodes 18 multiplier bits per cycle into 9 partial products and retires 18 bits of the carry-save vectors per cycle [lichtenau_2016]
* choices `array_alignment_side: {csa_output_shift, multiplicand_diagonal}` and `column_duplication` — the inter-level alignment shifts are applied to the diagonally routed multiplicand instead of the CSA outputs, and duplicated columns remove one cross-array route [naini_2001]
* `sign_extension` value for hot-1 encoding of negative partial products, and a `full_adder_path_ordering` choice — the hot-1 form embeds the extension so the most significant row is non-negative, and each stage's carry is routed to the next stage's slowest input [oh_2006]
* choice `operand_embedding: sign_extended_shared_int_fp` — one 25-bit multiplier serves fractions, signed integers and unsigned integers by the sign bits prepended to the operand [oh_2006]
* choice `signedness_control` for run-time signedness selection — one control signal switches a shared partial-product generate logic between unsigned and signed rows [zhang_2018]
