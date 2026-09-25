# new-family review: div

Source: `run/extract/reduce/newfam_div.md` (21 proposals). Vocabulary checked
against `chialu/spaces/div_spaces.py` (`div_space`, `qds_space`,
`seed_table_space`, `mult_final_round_space`), the neighbouring domains
(`fp_spaces.py`, `sfu_spaces.py`, `redundant_spaces.py`, `decimal_spaces.py`,
`approx_spaces.py`), the div gap files under `knowledge/extract/gaps/` and the
sibling plan `new_families/fp.md` (which registers `sig_sqrt_then_round` from
the same muller_2018#s07 chapter). Nothing in `chialu/spaces` changes here;
every line is an instruction to the human who applies it. Where a gap file
already names a choice, the same name is used below.

Three handles carry a mismatch the human must settle before pasting:
* `oberman_1998`: the proposals file cites the FP-addition paper (TCS 1998);
  the note has `status: mismatch` with `actual_citation` = "Minimizing the
  Complexity of SRT Tables" (TVLSI 1998). `bib/dividers.md` already lists the
  SRT-tables title under this handle while `bib/fp_add.md` lists the
  FP-addition title, so two works share one handle.
* `vazquez_2007`: the citation is the decimal-multiplier paper; the note has
  `status: mismatch` with `actual_citation` = "A Radix-10 SRT Divider Based on
  Alternative BCD Codings", which `decimal_spaces.py` cites as `vazquez_2007b`
  under `decimal_digit_recurrence`.
* `macsorley1961` (note, `bib/multipliers.md`) versus `macsorley1961`
  (`restoring_nonrestoring.papers`, `bib/dividers.md`): one paper, two
  handles. The lines below keep `macsorley1961` as given.

## absorbed

* `linear_reciprocal_seed (oberman_1997) -> poly_seed.degree=1` — two coefficient tables C0/C1 indexed by the leading divisor bits and one multiply/add (-C1 b + C0, 2k+2 bits from m = 2k+3 index bits) are a degree-1 polynomial seed; the "modified" form that replaces the multiply/add with one multiplication of a bit-modified operand (2.5k bits) is `operand_modification_multiply`, whose doc names the linear approximation as the sibling it replaces. oberman_1997 goes into `poly_seed.papers`.
* `minimal_weight_signed_digit_division (tocher_1958) -> srt_radix2.quotient_prediction=True` — quotient digits in {-1, 0, 1} with the residual shifted until its magnitude exceeds half the divisor is the family's founding recurrence (tocher_1958 is already in `papers`, and the doc's "zero digits skip work" is this rule); the trebling adder plus four adder-subtractors that evaluate candidate residuals in parallel and select by inspected sign digits, for 2 or 3 digits per cycle, is the speculative-branch quotient prediction the family doc describes ("three speculative carry-propagate branches per stage"). A `digits_per_cycle` count is not added because `gaps/srt_radix2.md` already proposes `overlap_scheme` (harris_1997) for it.
* `qds_table (kornerup_2005) -> qds_table` — the proposal asks for a family for a component that already is one: the `(u, t)` index-width pair is `divisor_truncation_bits`/`residual_truncation_bits`, the corrected Δ tests that decide `t` against `t+1` are `table_generation=script_generated` with `exhaustive_pd_region_check=True`, and kornerup_2005 is already in `papers`.
* `series_expansion_division (flynn_1970) -> goldschmidt` — the factored product a(1-x)(1+x^2)(1+x^4)... with sequential factors is the Goldschmidt sequence (D_i = 1 - x^(2^i), F_i = 2 - D_i, two multiplies per precision doubling); flynn_1970 is cited only under `newton_raphson`, so it is added to `goldschmidt.papers`. The expanded series evaluated as one expression is a polynomial in x and is an instance of `direct_polynomial` below; the iteration-for-iteration equivalence with Newton-Raphson at x_0 = 1 is already in the `newton_raphson` doc.
* `string_skipping_multiple_division (bloch_1959) -> restoring_nonrestoring.shift_over_zeros=True` — skipping strings of quotient ones and zeros with the multiples {1, 3/4, 3/2} of a normalized divisor (48 bits in 13 cycles, 3.7 bits per subtraction on Stretch) is the shift-over-zeros nonrestoring divider whose family doc already names the 0.75D/1.0D/1.5D set; the set itself becomes the `divisor_multiple_set` value `three_quarters_one_three_halves` under new values (macsorley1961). bloch_1959 goes into `restoring_nonrestoring.papers`; the overlap of mantissa division with exponent arithmetic is scheduling, not datapath.

## new values

* `self_timed_variable_latency.mechanism += result_cache` — a quotient or reciprocal cache probed when division issues: a hit supplies the stored value and halts the divider, a miss runs the divider and fills the entry (about 160 bits per double-precision quotient entry, about 108 per reciprocal entry); the family doc already calls the cache "the survey's fifth route" and `gaps/self_timed_variable_latency.md` lists the value [oberman_1997]
* `self_timed_variable_latency += choice cached_value: {quotient, reciprocal}` — a quotient cache keys on both operands, a reciprocal cache on the divisor alone and needs the final multiply [oberman_1997]
* `self_timed_variable_latency += choice cache_associativity: {direct_mapped, fully_associative}` [oberman_1997]
* `newton_raphson += choice iteration_order: IntRange(2, 3)` — the third-order recurrence b' = b[3(1 - xb) + (xb)^2] (the chapter writes the constants in binary as 11 and 10) triples the correct digits per step against doubling; the mutation `use_higher_order_iteration` exists without a choice to land on, and `gaps/newton_raphson.md` lists `iteration_order` from flynn_1970 and richards_1955#s11. The proposal's `initial_approximation_interval` (0, 2/x) is the convergence condition rather than a design choice and is not registered [richards_1955#s06]
* `poly_seed += choice slope_encoding: {plain, booth_radix8_decoded}` — the slope table stores C1 already radix-8 Booth-decoded so the segment multiplier is a small radix-8 array [trong_2007]
* `poly_seed += choice tail_bits: IntRange(4, 16)` — the operand bits below the segment index that enter the linear multiplier: 11 in POWER6 after a 6-bit index (64 segments), for slightly more than 14 bits in 3 cycles [trong_2007]
* `poly_seed += choice exponent_parity_tables: Bool` — separate reciprocal-square-root tables for even and odd exponents, three tables with the reciprocal one [trong_2007]
* `poly_seed.papers += trong_2007` — the POWER6 seed is `poly_seed` at `degree=1`, `input_bits=6`, `output_bits` about 14. `gaps/goldschmidt.md` proposes a separate `linear_pwl_reciprocal_seed` seed family for the same paper; new values are preferred per the rules because `degree=1` already exists and the sfu domain carries the general PWL machinery in `sfu.pwl` [trong_2007]
* `operand_modification_multiply += choice seed_synthesis: {modified_operand_product, boolean_partial_product_rows}` — Boolean functions of the operand bits placed as partial-product rows so that the multiplier tree sums directly to the reciprocal approximation: 484 elements in 18 columns of a 53-row array give 12.0 bits minimum (15.2 average) at 39 times less area than a 12-bit ROM; 175 elements in a Booth array give 9.2 bits [oberman_1997]
* `operand_modification_multiply += choice multiplier_array: {plain_53_row, booth_27_row}` — which array the rows are back-solved for; the proposal's `reuse_existing_multiplier: Bool` is the `multiplier_source` choice `gaps/operand_modification_multiply.md` already proposes from ito_1997. New values are preferred over a `partial_product_array_seed` family because the only source is one survey section, at the cost of the family name reading loosely; the human may promote it [oberman_1997]
* `qds_table += choice residual_input: {redundant_direct, short_cpa, full_cpa}` — the table indexes the redundant residual bits directly, a short assimilated estimate, or a fully assimilated residual [oberman_1998]
* `qds_table += choice assimilator_bits: IntRange(4, 12)` — width of the carry-assimilating adder in front of the table [oberman_1998]
* `qds_table += choice digit_encoding: {gray, line, choose_highest, unencoded}` — Gray or line encoding lets logic minimization pick any allowed digit inside an overlap region, with an explicit decoder outside the table [oberman_1998]
* `qds_table += choice folding: {none, signed_magnitude, t_bit_converter}` — P-D plot symmetry folded into half a table plus external logic; `gaps/srt_high_radix.md` lists `table_encoding` for the same paper on the divider, but the choices belong on the table family [oberman_1998]
* `srt_radix2.residual_form += signed_digit` — every partial remainder in {-1, 0, 1} digits, the next remainder from a redundant binary add/subtract cell, the digit from the sign of the three most significant digits; `gaps/srt_radix2.md` lists the same value (borrow-save) from burgess_1995 [kuninobu_1987]
* `srt_radix2 += choice implementation_topology: {reused_clocked_stage, combinatorial_array}` — n unrolled selection/remainder cells ending in one redundant-to-binary converter: 396 gate delays and 110k transistors for 64 bits against 938 and 120k for the SRT array; the gap file lists the choice from zuras1986. kuninobu_1987 goes into `srt_radix2.papers` (it is cited only under `redundant_binary_multiplier`) [kuninobu_1987]
* `srt_radix2 += choice quotient_conversion: {separate_positive_negative, serial_msd_borrow_scan, on_the_fly}` — Robertson's post-recurrence conversion scans the redundant digits from the most significant end: a negative digit is increased by the radix and one is borrowed from the next more-significant digit, and a zero digit takes the sign of the next nonzero digit from the divisor and partial-remainder signs (or from an attached sign), so the borrow propagates through zero runs; the terminal overflow is settled by a quotient-register add or by decrementing the LSD and adding the divisor to the remainder. The other two values are the Pentium accumulation (`gaps/srt_high_radix.md`, `quotient_accumulation`) and the OTF converter of `digit_recurrence_sqrt_combined` [robertson_1958]
* `srt_high_radix += choice quotient_conversion: {separate_positive_negative, serial_msd_borrow_scan, on_the_fly}` — same choice; neither SRT family records how the redundant quotient becomes conventional [robertson_1958]
* `srt_high_radix += choice residual_form: {irredundant, carry_save, signed_digit}` — signed-digit partial remainders p(j+1) = r p(j) - d q(j+1) at any radix; the redundant quotient digits make an inexact comparison on the first three or four residual digits sufficient, which is `qds_table.residual_truncation_bits` rather than a new choice; `gaps/srt_high_radix.md` lists the choice as `borrow_save_signed_digit`. The `parallel_multiple_compare` selection option (added comparators and divisor-multiple generators select the digit in one addition cycle) is a supporting source of `comparator_digit_selection` below; the `repeated_add_subtract` form (add or subtract the divisor after each shift until the range test passes) has a data-dependent step count and is not registered. avizienis_1961 goes into `srt_high_radix.papers` [avizienis_1961]
* `back_multiply_remainder += choice residual_operation: {quotient_times_divisor, candidate_square}` — for the square root the residual is x - r^2 for the faithful candidate r at wF+1 bits; r is either representable at wF or a midpoint, and only at a midpoint does the comparison of r^2 with x choose between truncation and the +2^-(wF+1) correction. `candidate_guard_bits=1` is `quotient_candidates=2`; the `selection_test` choice in `gaps/back_multiply_remainder.md` gains `midpoint_square_compare` [pasca_2011#s09]
* `back_multiply_remainder += choice product_bits: {full, low_bits_sufficient}` — only the square-product bits that decide the comparison are computed; on a Virtex-4 the correct-rounding step costs 2 to 5 DSPs and 4 to 13 cycles over the faithful (8,23) unit. pasca_2011 goes into `back_multiply_remainder.papers` [pasca_2011#s09]
* `restoring_nonrestoring += choice divisor_multiple_set: {one, half_one_two, three_quarters_one_three_halves}` — the choice `gaps/restoring_nonrestoring.md` proposes from freiman_1961, with the three sets MacSorley evaluates: 2.54 bits per cycle (one multiple, five-bit divisor decode), 2.74 (1/2, 1, 2 coded), 3.57 (3/4, 1, 3/2 optimum) [macsorley1961, bloch_1959]
* `restoring_nonrestoring += choice shift_policy: {zeros_only, zeros_and_ones}` — shift across quotient zeros only, or across runs of either value by adding the true/complement divisor to the true/complement partial dividend and decoding the leading equal bits [macsorley1961]
* `restoring_nonrestoring += choice multiple_selection: {coded_single_adder, double_adder, optimum}` — the multiple chosen by a decode of leading bits through one adder, by two parallel trial additions, or by the optimum rule (2.82 against 2.74 for 1/2, 1, 2; 3.51 against 3.57 for 3/4, 1, 3/2) [macsorley1961]
* `restoring_nonrestoring += choice shifter_limit: {4, 6, 8, none}` — the maximum shift per cycle: methods 1-8 give 1.86 to 3.82 bits per cycle unlimited and 1.76 to 3.08 at limit 4 [macsorley1961]

The Robertson conversion choice is placed on both SRT families because neither carries one; `digit_recurrence_sqrt_combined.on_the_fly_conversion` is the same decision as a Bool and could be widened to the same enum. The result-cache lines follow the family doc, but the oberman_1997 note's open question stands: the cache sits in front of the divider at execution-unit level, and the human may keep it out of `div_space`.

## new families

### comparator_digit_selection

Merged proposals: `comparator_digit_selection` (burgess_2007),
`comparison_multiple_qds` (nikmehr_2006), `constant_comparison_qds`
(vazquez_2007). The `parallel_multiple_compare` option of
`signed_digit_robertson_division` (avizienis_1961, under new values) is the
same mechanism at arbitrary radix and is cited as support.

* name: `comparator_digit_selection`
* domain: div; a second candidate of `qds_space`, so it fills `digit_select` in `srt_radix2`, `srt_high_radix`, `digit_recurrence_sqrt_combined`, `self_timed_variable_latency` and `decimal.decimal_digit_recurrence`
* doc: `digit from parallel comparators of a short residual estimate against selection constants (m_k or divisor multiples) rather than a stored table; the sign vector is a one-hot digit that can preselect speculative residuals (VFP11, decimal SRT)`
* execution_style: feed_forward (default, omitted; `qds_table` declares none either, the host recurrence carries the iteration)
* gap it closes: `qds_space` has one candidate with `free_form_allowed=False`, so no comparator-based selection is instantiable; `gaps/srt_radix2.md`, `gaps/srt_high_radix.md` (`sign_and_threshold_comparisons`) and `gaps/digit_recurrence_sqrt_combined.md` (parallel-comparator one-hot selection, burgess_2007) all list "`digit_select` values beyond `qds_table`", and the vazquez_2007 note asks for a constant-comparison filler of `decimal_digit_recurrence.digit_select`.
* design choices:
  * `comparator_count: IntRange(2, 18)` — four for radix-4 minimal redundancy (VFP11), nine with symmetry or eighteen direct (nikmehr), ten for m(-4) through m(5) (vazquez) [burgess_2007, nikmehr_2006, vazquez_2007]
  * `comparison_bits: IntRange(4, 16)` — the top eight remainder bits (VFP11) or four decimal digits (nikmehr) enter each comparator [burgess_2007, nikmehr_2006]
  * `estimate_cut: EnumChoice(("binary_bit", "decimal_digit"))` — the residual estimate truncated at any binary position inside a digit or at a digit boundary [vazquez_2007]
  * `residual_input: EnumChoice(("assimilated_estimate", "redundant_two_word"))` — nonredundant assimilated MSBs with one carry-propagate on the critical path (VFP11), or a two-word estimate reduced by a 3:2 carry-save stage inside each comparator (vazquez) [burgess_2007, vazquez_2007]
  * `constant_source: EnumChoice(("hardwired", "registers_at_init", "rom"))` — constants hardwired, generated arithmetically as divisor multiples (nine positive and nine 9's-complement multiples, or m(-4)..m(5)) in an initialization cycle and held in registers, or read from a ROM [burgess_2007, nikmehr_2006, vazquez_2007]
  * `symmetry_folding: BoolChoice()` — magnitude selection over nine comparisons plus a sign instead of eighteen comparisons [nikmehr_2006]
  * `output_encoding: EnumChoice(("binary", "one_hot", "zero_one_hot", "sign_magnitude"))` — the coder output: one-hot drives the candidate mux, sign-magnitude (with |q| one-hot and a BCD-5211 copy) serves the decimal recurrences [burgess_2007, nikmehr_2006, vazquez_2007]
  * `speculative_candidate_residuals: BoolChoice()` — five candidate remainders/roots computed in parallel and selected by the one-hot digit with no further carry-propagate on the path (15.4 FO4 on the comparator path against 16.0 for the F_k path) [burgess_2007]
* component slots:
  * `comparator_adder: cpa_space()` — each comparator is a short subtractor with a sign detector (in the decimal design a 3:2 reduction, BCD recoding, a prefix carry network and the sign detector)
* mutations: `replace_table_with_comparators` (crosses from `qds_table`), `fold_comparators_by_symmetry`, `hardwire_selection_constants`, `add_candidate_residual_preselection`, `widen_comparison_estimate`, `move_pr_sign_detection_off_critical_path` (nikmehr's duplicated partial-remainder sign detectors outside the iteration)
* handles: burgess_2007 [incremental], nikmehr_2006 [incremental], vazquez_2007 [incremental; note status mismatch, content is the ICCD divider cited as vazquez_2007b], avizienis_1961 [landmark, the parallel-comparator option]
* evidence strength: 3 merged proposals plus 1 landmark support, 4 papers, no textbook or thesis block; implementation numbers from all three incremental papers (15.4 FO4 comparator path for the VFP11 macrocell; 2.33 ns recurrence and 1332 FO4 decimal128 latency in 0.18 um against 1733/3772 FO4 for Wang-Schulte; 3200 NAND2 and 22.3 FO4 for the ten-comparator selection function)
* snippet (insert after `qds_table` in `qds_space`):

```python
        Architecture(
            "comparator_digit_selection",
            papers=("burgess_2007", "nikmehr_2006", "vazquez_2007",
                    "avizienis_1961"),
            design_choices={
                "comparator_count": IntRange(2, 18),
                "comparison_bits": IntRange(4, 16),
                "estimate_cut": EnumChoice(("binary_bit", "decimal_digit")),
                "residual_input": EnumChoice(("assimilated_estimate",
                                              "redundant_two_word")),
                "constant_source": EnumChoice(("hardwired",
                                               "registers_at_init", "rom")),
                "symmetry_folding": BoolChoice(),
                "output_encoding": EnumChoice(("binary", "one_hot",
                                               "zero_one_hot",
                                               "sign_magnitude")),
                "speculative_candidate_residuals": BoolChoice(),
            },
            components={"comparator_adder": cpa_space()},
            mutations=("replace_table_with_comparators",
                       "fold_comparators_by_symmetry",
                       "hardwire_selection_constants",
                       "add_candidate_residual_preselection",
                       "widen_comparison_estimate",
                       "move_pr_sign_detection_off_critical_path"),
            doc="digit from parallel comparators of a short residual "
                "estimate against selection constants (m_k or divisor "
                "multiples) rather than a stored table; the sign vector "
                "is a one-hot digit that can preselect speculative "
                "residuals (VFP11, decimal SRT)"),
```

* human decisions: (1) the vazquez_2007 handle, per the header; (2) whether the decimal-only values (`estimate_cut=decimal_digit`, the BCD-5211 output) stay in the shared `qds_space` or move to `decimal_digit_recurrence` as `gaps/decimal_digit_recurrence.md` would have them; (3) the `qds_table` doc's rule that a selection table is "regenerated from constraints and checked exhaustively" has no counterpart here, and the human may want a `constant_validation` choice mirroring `exhaustive_pd_region_check`, which no proposal supports.

### arithmetic_estimate_selection

From `limited_precision_arithmetic_qds` (atkins_1968). Not merged.

* name: `arithmetic_estimate_selection`
* domain: div; a third candidate of `qds_space`
* doc: `digit = round(truncated residual / truncated divisor) from an auxiliary limited-precision arithmetic unit (exponent-ALU divide or approximate-reciprocal multiply); the uncertainty rectangle Δp x Δd must lie inside one selection region`
* execution_style: feed_forward (default, omitted)
* gap it closes: `gaps/srt_high_radix.md` names `arithmetic_approximation` as a `digit_select` value beyond `qds_table` without a family to carry it; the approximate-reciprocal form applied to the divisor instead of the residual is `prescaled_very_high_radix`, which is a divider rather than a selection component.
* design choices:
  * `operation: EnumChoice(("exponent_alu_division", "approximate_reciprocal_multiply"))` — the paper's two implementations: divide the truncated shifted residual by the truncated divisor on the exponent arithmetic unit, or multiply it by an approximate reciprocal, then round to an integer digit [atkins_1968]
  * `residual_estimate_bits: IntRange(4, 16)` — N_p by the three cost cases: 4k+3, 2k+5 or 2k+4 for r = 2^(2k) and n = 2/3 (r-1) [atkins_1968]
  * `divisor_estimate_bits: IntRange(3, 16)` — N_d: 2k+3, 2k+4 or 2k+5 in the same cases [atkins_1968]
  * `residual_input: EnumChoice(("redundant", "assimilated"))` — the partial-remainder form the estimate is cut from [atkins_1968]
  * `quotient_rounding` has the single evidenced value `round_to_integer` and is folded into the doc rather than declared.
* component slots: none, matching `qds_table`; the auxiliary unit is named by `operation` (the exponent ALU is reused, the reciprocal multiply is a small multiplier that `mul_space` could fill if `qds_space` gained a width parameter)
* mutations: `replace_table_with_estimate_arithmetic` (crosses from `qds_table`), `widen_estimates`, `reuse_exponent_alu`, `replace_division_with_reciprocal_multiply`
* handles: atkins_1968 [landmark]
* evidence strength: 1 proposal, 1 landmark paper; the abstract cost model only (Table II inspection widths, no implementation, no technology). The weakest of the four families on evidence; it is kept separate from `comparator_digit_selection` because its choices (estimate widths of an arithmetic unit) do not overlap with comparator constants, and the "prefer new values" rule has no host, since `qds_space` has no family whose choice this could be.
* snippet (insert after `comparator_digit_selection` in `qds_space`):

```python
        Architecture(
            "arithmetic_estimate_selection",
            papers=("atkins_1968",),
            design_choices={
                "operation": EnumChoice(("exponent_alu_division",
                                         "approximate_reciprocal_multiply")),
                "residual_estimate_bits": IntRange(4, 16),
                "divisor_estimate_bits": IntRange(3, 16),
                "residual_input": EnumChoice(("redundant", "assimilated")),
            },
            mutations=("replace_table_with_estimate_arithmetic",
                       "widen_estimates", "reuse_exponent_alu",
                       "replace_division_with_reciprocal_multiply"),
            doc="digit = round(truncated residual / truncated divisor) "
                "from an auxiliary limited-precision arithmetic unit "
                "(exponent-ALU divide or approximate-reciprocal multiply); "
                "the uncertainty rectangle dp x dd must lie inside one "
                "selection region"),
```

* human decisions: (1) separate family, as here, or a `method` value inside `comparator_digit_selection`; (2) atkins_1968 already sits in `qds_table.papers` and `srt_high_radix.papers` and stays there, since the same paper founds the P-D feasibility regions.

### continued_product_division

From `continued_product_division` (ercegovac_1973). Not merged.

* name: `continued_product_division`
* domain: div (`div_space`); a fourth lineage beside digit recurrence, functional iteration and table-driven seeds
* doc: `multiplicative normalization: digits S_k drive X * prod(1 + S_k r^-k) toward 1 with shift-and-add factors while Q(k+1) = Q(k)(1 + S_k r^-k) accumulates the quotient; no full multiplier, no selection table (radix 16, digits -10..10)`
* execution_style: fixed_iteration
* gap it closes: no `div_space` family forms the quotient as a continued product of digit-selected factors. `goldschmidt` multiplies by full-width factors 2 - D_i, `svoboda_tung` and the SRT families subtract digit multiples, and `sfu.digit_recurrence_exp_log` (which already cites ercegovac_1973) runs the same normalization for exp/log but its doc forms only "the result from the same continued-product factors" for the exponential; the ercegovac_1973 note lists "the divider vocabulary lacks the continued-product division mechanism defined by Algorithm D" as a gap.
* design choices:
  * `radix: EnumChoice((2, 16))` — the paper's radix-16 algorithm (four result bits per step) against the radix-2 baseline it estimates hardware and performance for [ercegovac_1973]
  * `execution_organization: EnumChoice(("separate_units", "overlapped_pipeline"))` — normalization and result evaluation on two units, or overlapped in one split, pipelined arithmetic unit [ercegovac_1973]
  * the digit set (symmetric redundant -10..10, redundancy ratio 4/3), the result recurrence (continued product) and the selection (rounding of the scaled residual prefix) each have a single evidenced value and are folded into the doc rather than declared.
* component slots:
  * `factor_adder: cpa_space()` — the multiplication by (1 + S_k r^-k) is a shift plus an addition of the multiple S_k X
  * `shifter: shifter_space()` — the variable shift by k digit positions (the note names `barrel_mux_tree` as the filler; `shifter_space` is in `arith_spaces`)
* mutations: `raise_radix`, `overlap_normalization_with_result_evaluation`, `share_unit_with_log_exp` (crosses to `sfu.digit_recurrence_exp_log`), `adopt_redundant_digit_set`
* handles: ercegovac_1973 [incremental]
* evidence strength: 1 proposal, 1 paper, no textbook or thesis block, no implementation numbers (relative error |δ| = |ε(m+1)| and hardware estimates without a technology). The weakest family on placement: the alternative is `sfu.digit_recurrence_exp_log += choice result_recurrence: {constant_sum, continued_product}` plus the same `execution_organization`, which keeps one normalization engine, but leaves division unreachable from `fp_div_space.sig_div_then_round.sig_div`, which is `div_space()`.
* snippet (insert after `svoboda_tung` in `div_space`; `shifter_space` needs importing from `arith_spaces`):

```python
        Architecture(
            "continued_product_division",
            papers=("ercegovac_1973",), **it,
            design_choices={
                "radix": EnumChoice((2, 16)),
                "execution_organization": EnumChoice(("separate_units",
                                                      "overlapped_pipeline"))},
            components={"factor_adder": cpa_space(),
                        "shifter": shifter_space()},
            mutations=("raise_radix",
                       "overlap_normalization_with_result_evaluation",
                       "share_unit_with_log_exp",
                       "adopt_redundant_digit_set"),
            doc="multiplicative normalization: digits S_k drive "
                "X*prod(1+S_k r^-k) toward 1 with shift-and-add factors "
                "while Q(k+1) = Q(k)(1+S_k r^-k) accumulates the quotient; "
                "no full multiplier, no selection table (radix 16, "
                "digits -10..10)"),
```

* human decisions: (1) this family versus the two choices on `sfu.digit_recurrence_exp_log`; (2) if the family is taken, the sfu family gains the mutation `compose_with_division` or the two families share a doc cross-reference.

### direct_polynomial

From `polynomial_significand_approximation` (muller_2018#s07). Not merged;
the single-expression form of `series_expansion_division` (flynn_1970,
absorbed) and the square-root unit behind `sqrt_square_compare_rounding`
(pasca_2011#s09, new values) are instances.

* name: `direct_polynomial`
* domain: div (`div_space`)
* doc: `1/y, x/y or sqrt(x) from a table-indexed polynomial evaluated to working precision with no refinement loop (or at most one), then a remainder-based correct-rounding step; the only feed-forward divider beside an unrolled array`
* execution_style: feed_forward
* gap it closes: `poly_seed` stops at degree 2 and exists only to seed an iteration, `newton_raphson.iterations` starts at 1, and `new_families/fp.md` records for `sig_sqrt_then_round` that "polynomial approximation has no `div_space` filler"; the muller_2018#s07 note lists "the vocabulary lacks the chapter's direct polynomial division/square-root algorithm family" as a gap.
* design choices:
  * `target: EnumChoice(("reciprocal", "ratio", "square_root"))` — which function the polynomial approximates; `ratio` folds the dividend into the final multiply [muller_2018#s07]
  * `composition: EnumChoice(("polynomial_only", "polynomial_plus_iteration"))` — the chapter's "optionally combined with functional iteration"; at degree at most 2 the combined form is `newton_raphson` with `seed=poly_seed` (pineiro_2002), so the value here covers the case where the polynomial supplies most of the precision [muller_2018#s07]
  * the polynomial degree and segmentation live in the `approximator` slot (`sfu.lut_plus_poly.degree` 1..5, `sfu.piecewise_poly.degree` 1..4) and are not repeated here.
* component slots:
  * `approximator: sfu_approx_space()` — `lut_plus_poly`, `piecewise_poly` or `single_poly` (`sfu_spaces` imports nothing from `chialu.spaces`, so `div_spaces` can import it without a cycle)
  * `final_mul: mul_space(width)` — the dividend times reciprocal product for `target=ratio`, and the r^2 or q*b product the rounding step needs
  * `final_round: mult_final_round_space()` — remainder or equivalent evidence for correct rounding; for square root with `residual_operation=candidate_square` (new values above)
* mutations: `raise_polynomial_degree`, `add_one_refinement_iteration` (crosses to `newton_raphson`), `replace_remainder_with_exclusion_proof`, `share_evaluator_between_targets`
* handles: muller_2018#s07 [textbook]; pasca_2011#s09 [thesis] for the square-root instance (its DSP-based faithful unit plus the square-compare rounding, whose note asks `lut_plus_poly` for exponent-parity breakpoints); flynn_1970 [survey] for the expanded-series form
* evidence strength: 1 proposal, 1 textbook block (abstract: "sufficiently accurately", correct rounding needs a remainder or equivalent evidence, pp.276-278) plus 1 thesis block by instance with Virtex-4 numbers only for the rounding step (2 to 5 DSPs, 4 to 13 cycles over faithful), plus the survey's series form. The "prefer new values" route would be `newton_raphson.iterations: IntRange(0, 3)` with `poly_seed.degree` widened; the family route is taken because the execution style changes from `fixed_iteration` to `feed_forward`, which is what the II contract distinguishes.
* snippet (insert after `goldschmidt` in `div_space`; `sfu_approx_space` needs importing from `sfu_spaces`):

```python
        Architecture(
            "direct_polynomial",
            papers=("muller_2018", "pasca_2011", "flynn_1970"),
            design_choices={
                "target": EnumChoice(("reciprocal", "ratio", "square_root")),
                "composition": EnumChoice(("polynomial_only",
                                           "polynomial_plus_iteration"))},
            components={"approximator": sfu_approx_space(),
                        "final_mul": mul_space(width),
                        "final_round": mult_final_round_space()},
            mutations=("raise_polynomial_degree",
                       "add_one_refinement_iteration",
                       "replace_remainder_with_exclusion_proof",
                       "share_evaluator_between_targets"),
            doc="1/y, x/y or sqrt(x) from a table-indexed polynomial "
                "evaluated to working precision with no refinement loop "
                "(or at most one), then a remainder-based correct-rounding "
                "step; the only feed-forward divider beside an unrolled "
                "array"),
```

* human decisions: (1) this family versus widening `newton_raphson.iterations` to 0; (2) whether `approximator` should admit the whole `sfu_approx_space` or a narrowed candidate list (the activation and CORDIC families in it make no sense here); (3) chapter handles are cited by parent (`muller_2018`, `pasca_2011`) in `papers`, as `fp.md` does.

## rejected

* none — every proposal describes a datapath structure that exists, extends an existing choice, or founds one of the four families above. Two items inside otherwise-accepted proposals are non-structural and are noted on their own lines rather than rejected as whole proposals: the overlap of mantissa division with exponent arithmetic in `string_skipping_multiple_division` (bloch_1959) is scheduling, and the convergence interval in `higher_order_reciprocal_iteration` (richards_1955#s06) is a precondition.

absorbed 5, new values 10, new families 4 (from 6 proposals), rejected 0
