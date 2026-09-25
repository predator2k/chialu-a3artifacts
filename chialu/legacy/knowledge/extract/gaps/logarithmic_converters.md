# logarithmic_converters: proposed changes to the space

* `correction` value `table_scaled_interpolation_error` — the LNS ALU corrects its linear interpolation by a stored maximum interval error that scales a template [coleman_2000]
* choices for close-subtraction transformation (range shifter) and for sharing one correction template between addition and subtraction [coleman_2000]
* choices `characteristic_extraction: {sequential_left_shift_and_count, lzd}` and `correction_execution: {sequential_shift_add, combinational}` — the original converter obtains k and applies corrections bit-serially [combet1965]
* choices `region_symmetry` and `approximated_fraction_bits` — the ROM-free converter uses two regions with inverse slopes and converts only the top nine fraction bits [juang_2009]
