# Registration review of the literature's new-family proposals

The map pass over the corpus proposed 289 microarchitectures the
registry lacked (`## new_families` blocks in `knowledge/notes/`). One
review per domain, from `run/extract/reduce/newfam_<domain>.md`
against the domain's space file, sorts every proposal into absorbed
(already a family, choice value or variant), new value (a paste-ready
choice or value on an existing family), new family (a paste-ready
`Architecture(...)` snippet), or rejected. Nothing in `chialu/spaces`
was changed; each plan is applied by hand.

| domain | absorbed | new values | new families (from proposals) | rejected |
| --- | --- | --- | --- | --- |
| adder | 3 | 18 | 2 (5) | 2 |
| mul | 14 | 12 | 3 (7) | 0 |
| div | 5 | 10 | 4 (6) | 0 |
| fp | 4 | 13 | 3 (11) | 2 |
| dot | 3 | 13 | 0 (0) | 2 |
| shift | 5 | 9 | 1 (2) | 3 |
| checker | 1 | 8 | 5 (19) | 2 |
| sfu | 6 | 9 | 4 (8) | 4 |
| decimal | 7 | 11 | 4 (12) | 2 |
| redundant | 1 | 12 | 1 (4) | 1 |
| approx | 4 | 7 | 0 (0) | 2 |
| dsp | 4 | 2 | 1 (4) | 1 |
| other | 0 | 3 | 2 (2) | 5 |
| total | 57 | 127 | 30 (80) | 26 |

## New families proposed

adder: digit_serial_adder, counter_accumulator. mul: direct_pp_parallel,
tiled_cpa_reduction_tree, constant_multiplier. div:
comparator_digit_selection, arithmetic_estimate_selection,
continued_product_division, direct_polynomial. fp: partitioned_fpu,
internal_format_datapath, sig_sqrt_then_round. shift: butterfly_network.
checker: checkpoint_retry_recovery, standby_sparing, block_code_ecc,
m_out_of_n_checker, parity_prediction_divider. sfu: add_table_add,
table_factor_refinement, rational_approximation, e_method. decimal:
bid_fp_addition, decimal_fp_multiplication, redundant_decimal_conversion,
decimal_counter_accumulator. redundant: rns_forward_converter. dsp:
embedded_fpu_block. other: gray_code_converter (shift), dda_integrator
(dot).

## Decisions that cut across plans

* **Scope of the registry.** Four questions recur: FPU-level
  organization (`partitioned_fpu`, needs an `fpu_spaces.py`);
  core-level recovery and storage codes (`checkpoint_retry_recovery`,
  `standby_sparing`, `block_code_ecc`); pulse-counting accumulators
  from the 1946–1955 books (`counter_accumulator`,
  `decimal_counter_accumulator`, `dda_integrator`); and the FPGA-mapping
  ruling in `dsp_posit_spaces.py` (virtual operand packing,
  `constant_multiplier`'s KCM half, `pasca_2023`). Each plan states the
  fallback if the answer is no.
* **No ALU-core space.** Several proposals are ALU-level structures
  (Mead-Conway carry-in/conditional operation, the retimed XOR-merged
  ALU, an `operation: {add_only, subtract_only, add_subtract}` choice
  spanning every CPA family). They are parked on adder families; a
  core-level family in `modules/binary_alu.py` is the alternative.
* **Handle re-keying (done 2026-09-02).** The mismatched handles the plans cite were re-keyed: duplicates of an existing handle were dropped from `handles.json` and their notes parked in `notes/_rekey/` (avizienis_1971, detrey_2007, han2013, kantabutra1993, lang_2007, langhammer_2015, leon2018, mazahir2017a, nicolaidis_1999, oberman_1999, sklansky1960, vahdat2017, zhu2010); files that were another work got new handles (dadda_1983, hokenek_cook_1990, hunter_1994, montuschi_2001, abdelhamid_2017, huang_2011, kornerup_2014, bund_2019, gudovskiy_2017, rangeetha_2019, beuchat_2009, vergos_2001); oberman_1998 was split (fp_add) / oberman_1998b (dividers, the SRT-tables paper); vazquez_2007 was remapped to vazquez_2007b; wang_2007 and wang_2007b were swapped; the spelling pairs were unified on macsorley1961, beaumont_smith1999, anderson1967, burks1946. A plan line that names a retired handle is applied under the new one.
* **Shared leaf spaces.** `carry_select.block_adder += parallel_prefix`
  widens `block_adder_space`, which five slots reuse;
  `butterfly_network` enters the fp alignment shifter slots through
  `arith_spaces.shifter_space`; `direct_pp_parallel` versus a
  `reduction` slot on `carry_save_array`.
* **Duplicates across plans.** dot and fp both propose
  `multi_term_fused_dot.term_source`, the pairwise alignment value,
  `lza.input_count` and `fp_add_space.dependent_result_forwarding`;
  `counter_accumulator` (adder) and `decimal_counter_accumulator`
  (decimal) are one family with a radix choice; `differential` scale
  handling is proposed on both CORDIC families. Apply each once.
