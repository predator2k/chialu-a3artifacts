# binary_decimal_conversion: proposed changes to the space

* independent binary-chunk and decimal-chunk widths — the processor converters are asymmetric (12 bits to 4 digits, 3 digits to 10 bits) so one `digits_per_step` cannot describe both directions [busaba_2001, schwarz_2002, carlough_2011]
* `structure` values `parallel_table_lookup_add`, `iterative_encoded_doubler_and_compressor`, `iterative_chunked` and a custom iterative-array style — the IBM converters use table lookup plus an adder, encoded decimal doublers with a 6:2 compressor, and chunked iteration that the enumeration does not name [schwarz_2002, busaba_2001, carlough_2011, saporito_2020, schmookler_1972]
* choice `test_shift_fusion: {separate_test_and_shift, fused_test_shift}` — fusing the correction into the shift halves the operation count per binary bit [couleur_1958]
* choice `input_loading: {serial, parallel}` with disable gating — parallel loading needs per-decade disable gates to prevent premature correction [couleur_1958]
* an input-code choice covering binary/reflected binary/binary-coded octal sources — Gray-code input needs a serial front-end converter [couleur_1958]
* choice `digit_code: {bcd8421, 1-2-4-5, biquinary}` and `polarity_alternation: Bool` — cell complexity and delay differ per digit code, and alternating true/complementary cells avoid per-cell inverters [nicoud_1971]
* choice `procedure: {repeated_radix_divide_or_multiply, sequential_power_subtraction, digitwise_radix_accumulation, repeated_positional_addition}` and `number_class: {integer, fraction}` — the chapter classifies four procedures whose round-off exposure differs, and fractions change recurrence order [richards_1955#s11]
* choices `intermediate_radix: {10, 100, 1000}`, `carry_save_front_end: Bool`, `overflow_decoder_radix: {10, 100_then_10}`, `exact_integer_compensation: Bool` — the multiply form's digits per operation, decoder latency and exactness depend on them [schmookler_1968]
* a converter slot in `decimal_multioperand_addition` accepting `binary_decimal_conversion` — binary-to-decimal conversion is a defining stage of the mixed binary/BCD reduction [dadda_2007]
* choice `format_repacking: zoned_and_packed` — hardware PACK/UNPACK conversion between zoned and packed decimal formats accompanies CVB/CVD [check_slegel_1999]
