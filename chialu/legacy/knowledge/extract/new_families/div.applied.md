# applied: div

Plan `new_families/div.md` applied to `chialu/spaces/div_spaces.py`
(the only space file edited). Retired handles were applied under their
re-keyed names: `oberman_1998` (SRT tables) as `oberman_1998b`, which
`qds_table.papers` already carried, and `vazquez_2007` as
`vazquez_2007b`. `macsorley1961` is the bibliography spelling.
Evidence rule: a new family is applied with two or more papers or a
textbook/thesis block; a single-paper family is deferred.

## applied

* `qds_table += residual_input {redundant_direct, short_cpa, full_cpa}` — papers unchanged (`oberman_1998b` present)
* `qds_table += assimilator_bits Int[4..12]`
* `qds_table += digit_encoding {gray, line, choose_highest, unencoded}`
* `qds_table += folding {none, signed_magnitude, t_bit_converter}`
* `comparator_digit_selection` family added to `qds_space` after `qds_table`, papers `burgess_2007, nikmehr_2006, vazquez_2007b, avizienis_1961`, slot `comparator_adder: cpa_space()`; docs written: `arch/div/comparator_digit_selection.md.pending` (the finished family doc, parked outside the lint glob; see the lint note; references burgess_2007, nikmehr_2006, avizienis_1961, since the vazquez_2007 citation line in the bundle is the mismatched multiplier paper and is not cited), `extract/gaps/comparator_digit_selection.md` (none)
* `poly_seed += slope_encoding {plain, booth_radix8_decoded}`
* `poly_seed += tail_bits Int[4..16]`
* `poly_seed += exponent_parity_tables Bool`
* `poly_seed.papers += trong_2007`
* `operand_modification_multiply += seed_synthesis {modified_operand_product, boolean_partial_product_rows}`; papers += `oberman_1997`; variant doc `operand_modification_multiply/boolean_partial_product_rows.md`
* `operand_modification_multiply += multiplier_array {plain_53_row, booth_27_row}`
* `back_multiply_remainder += residual_operation {quotient_times_divisor, candidate_square}`; papers += `pasca_2011`; variant doc `back_multiply_remainder/candidate_square.md`
* `back_multiply_remainder += product_bits {full, low_bits_sufficient}`
* `restoring_nonrestoring += divisor_multiple_set {one, half_one_two, three_quarters_one_three_halves}`; papers += `bloch_1959` (`macsorley1961` present); variant doc `restoring_nonrestoring/three_quarters_one_three_halves.md`
* `restoring_nonrestoring += shift_policy {zeros_only, zeros_and_ones}`
* `restoring_nonrestoring += multiple_selection {coded_single_adder, double_adder, optimum}`
* `restoring_nonrestoring += shifter_limit {4, 6, 8, none}` (members 4, 6, 8 are ints, `none` a string, as the plan line gives them)
* `srt_radix2.residual_form += signed_digit`; papers += `kuninobu_1987`; variant doc `srt_radix2/signed_digit.md`
* `srt_radix2 += implementation_topology {reused_clocked_stage, combinatorial_array}`; variant doc `srt_radix2/combinatorial_array.md`
* `srt_radix2 += quotient_conversion {separate_positive_negative, serial_msd_borrow_scan, on_the_fly}` (`robertson_1958` present)
* `srt_high_radix += quotient_conversion {separate_positive_negative, serial_msd_borrow_scan, on_the_fly}`; papers += `robertson_1958`; variant doc `srt_high_radix/serial_msd_borrow_scan.md` (the Robertson block names srt_high_radix as closest, so the variant doc sits there once; the bare name resolves)
* `srt_high_radix += residual_form {irredundant, carry_save, signed_digit}`; papers += `avizienis_1961`; variant doc `srt_high_radix/signed_digit.md`
* `newton_raphson += iteration_order Int[2..3]`; papers += `richards_1955` (chapter handle cited by parent)
* `self_timed_variable_latency.mechanism += result_cache`; papers += `oberman_1997`; variant doc `self_timed_variable_latency/result_cache.md`
* `self_timed_variable_latency += cached_value {quotient, reciprocal}`
* `self_timed_variable_latency += cache_associativity {direct_mapped, fully_associative}`
* `direct_polynomial` family added to `div_space` after `goldschmidt` (feed_forward, no `**it`), papers `muller_2018, pasca_2011, flynn_1970`, slots `approximator: sfu_approx_space()` (import added from `sfu_spaces`, which imports only `adir`, so no cycle), `final_mul: mul_space(width)`, `final_round: mult_final_round_space()`; docs written: `arch/div/direct_polynomial.md`, `extract/gaps/direct_polynomial.md` (none)
* module docstring gains one sentence each for `direct_polynomial` and `comparator_digit_selection`; the `qds_space` docstring names the comparator route

Totals: 25 new-value lines applied, 2 families applied, 8 variant docs, 2 family docs, 2 gap files.

## skipped

* `arithmetic_estimate_selection` — deferred: one paper (atkins_1968), no textbook or thesis block.
* `continued_product_division` — deferred: one paper (ercegovac_1973), no textbook or thesis block.
* `newton_raphson.initial_approximation_interval` — the plan rules it a convergence condition rather than a design choice.
* `srt_high_radix` `repeated_add_subtract` selection form (avizienis_1961) — the plan rules its data-dependent step count out.
* `comparator_digit_selection.constant_validation` — the plan's human decision (3); no proposal supports it.
* The absorbed lines' `papers` additions `oberman_1997 -> poly_seed.papers` and `flynn_1970 -> goldschmidt.papers` — absorbed entries are "nothing to do"; `bloch_1959` entered `restoring_nonrestoring.papers` through the `divisor_multiple_set` line, and `tocher_1958`/`kornerup_2005` were already present.
* Widening `digit_recurrence_sqrt_combined.on_the_fly_conversion` to the `quotient_conversion` enum — a suggestion in the plan's closing paragraph without a paste-ready line.
* Moving the decimal-only values (`estimate_cut=decimal_digit`, the sign-magnitude/BCD-5211 output) to `decimal_digit_recurrence` — the plan's human decision (2); the plan's placement in the shared `qds_space` is kept.
* The result-cache lines were applied despite the plan's note that the cache sits at execution-unit level: the instruction applies every remaining new value, and the FPU-level ruling covers `partitioned_fpu`-style organization rather than a cache in front of one divider.
* Variant docs were not written for pinned values that are parameter settings rather than named structures: `poly_seed.slope_encoding=booth_radix8_decoded`, `back_multiply_remainder.product_bits=low_bits_sufficient`, `restoring_nonrestoring.shift_policy=zeros_and_ones`, the `qds_table` encodings and folding (the oberman_1998 block is a mismatch handle and `qds_table` has no family doc of its own), and the per-paper values of `comparator_digit_selection`.

## deferred (other file)

* "`candidate_guard_bits=1` is `quotient_candidates=2`; the `selection_test` choice in `gaps/back_multiply_remainder.md` gains `midpoint_square_compare`" — targets a gap file.
* "the alternative is `sfu.digit_recurrence_exp_log += choice result_recurrence: {constant_sum, continued_product}` plus the same `execution_organization`" — sfu_spaces.py alternative for the deferred `continued_product_division`.
* "(2) if the family is taken, the sfu family gains the mutation `compose_with_division` or the two families share a doc cross-reference" — sfu_spaces.py, conditional on the deferred family.

## lint note

`qds_space()` is not in `chialu.papers._all_spaces()`, and
`archdocs._all_families` walks top-level candidates only, so `qds_table`
has never been counted by the lint and a doc at
`arch/div/comparator_digit_selection.md` lints as ORPHAN (confirmed by a
run with the doc in place). The finished doc is parked as
`arch/div/comparator_digit_selection.md.pending`, which neither the lint
nor `kb_prompt.load_family_docs` globs; until it is activated the
`digit_select` slots render the family from its one-line `doc` and its
`papers`. Activation is two steps outside this plan's file scope:
register `div_spaces.qds_space()` in `_all_spaces()` (papers.py), which
also makes the lint report `qds_table` as undocumented until it has a
doc, then `mv` the `.pending` file to `comparator_digit_selection.md`.
