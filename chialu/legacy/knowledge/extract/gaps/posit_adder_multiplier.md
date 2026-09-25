# posit_adder_multiplier: proposed changes to the space

* a fraction-multiplier slot accepting the multiplier families (`booth_recoded_parallel` and the rest) plus a DSP-mapping choice — every posit multiplier contains an integer significand multiplier that `sig_datapath`, which admits only adder families, cannot name [chaurasiya_2018, jaiswal_2018, murillo_2020, podobas_2018, zhang_2020]
* extend `es_bits` beyond 3 and add a runtime-switched es set — reported formats use es of 4, 6, 7 and 10, the generators accept arbitrary es, and PERI switches es at run time [gustafson_2017, jaiswal_2018, jaiswal_2019, tiwari_2021]
* choice `word_size_bits` (total format width) — n is an independent generator parameter in every design [jaiswal_2019, podobas_2018, chaurasiya_2018]
* choice `rounding: {round_to_zero, round_to_nearest_even}` — truncating and correctly rounding designs coexist and differ in cost and accuracy [jaiswal_2018, chaurasiya_2018, murillo_2020, murillo_2022]
* choice `operation: {add_subtract, multiply}` — the generators emit separately generated units [podobas_2018, murillo_2020]
* `regime_decode` value `integrated_lzoc_shift` and a regime-decoder slot that `lzd_cell_tree` could fill — the single leading-zero-or-one counter with shifter is a distinct decoder [murillo_2020, podobas_2018]
* choices for the decode/custom-FP/encode operator structure, output-only rounding, intermediate-format field sizing and round/sticky preservation — the standalone-operator structure and the PIF widths set the internal cost [dedinechin_2019b, uguen_2019]
* choices for fused accumulation format, encoder/decoder placement and exception-hardware removal — the training datapath decodes posit<8,1> into a small float, accumulates in a wider float, and places codecs inside or outside the array [lu_2021, gustafson_2017]
* choice `mantissa_region_granularity_bits` for regime-gated multiplier regions — gating unused fraction regions saves 16 to 22 percent power at 4 percent area [zhang_2020]
* a fused posit MAC generator family alongside `posit_adder_multiplier` and `posit_quire_mac` [zhang_2019]
