# reduced_latency_fma: proposed changes to the space

* choice `datapath_organization: {single, close_far_double}` — the CLOSE/FAR split separates full alignment from full normalization so one full-length shift lies on each path [bruguera_2005]
* choice for overlapping exponent and shift-count generation with multiplication or alignment [bruguera_2005]
* choices `lza_shift_overlap: msb_first_shift_encoding` and `prefix_levels_anticipated: Int` — the shifter starts on the LZA's leading bits and part of the prefix adder is computed before normalization [lang_2004]
* a sign/complement-handling choice for the conditional two's-complement treatment around the CSA and normalization stages [lang_2004]
* choices `sign_detection_source: {separate_unit, lza_result}` and `overflow_preshift: Bool` — LZA-derived sign removes the sum/sign stage, and the combined round/add stage requires a pre-shift of 11.xxx results [srinivasan_2013]
