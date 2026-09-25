# integer_compare_on_bits: proposed changes to the space

* choice `format: {ieee754, posit}` — the posit encoding compares directly as a signed integer with no NaN or negative-zero handling [gustafson_2017, tiwari_2021]
* choice `special_value_ordering` (NaR equal to itself and less than every posit) — the `nan_semantics` values only cover IEEE NaN rules [mallasen_2022, tiwari_2021]
