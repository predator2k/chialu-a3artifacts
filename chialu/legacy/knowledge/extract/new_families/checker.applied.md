# checker plan: applied record

Plan: `new_families/checker.md`. File edited: `chialu/spaces/checker_spaces.py`
only. Docs written: `arch/checker/m_out_of_n_checker.md` with variants
`m_out_of_n_checker/{k_out_of_2k,arbitrary_m_out_of_n,one_out_of_n}.md`,
`arch/checker/majority_voter.md`, `extract/gaps/m_out_of_n_checker.md`
and `extract/gaps/majority_voter.md` (both `none`). Doc moved:
`arch/checker/two_rail_tree/m_out_of_n.md` became
`arch/checker/m_out_of_n_checker/k_out_of_2k.md`. Rulings applied
without re-opening: core-level recovery and storage codes stay out
(fallback values on `duplication` where the plan names them), the PLA
and fail-safe lines are in scope, `m_out_of_n_checker` is registered,
`parity_prediction_divider` is deferred, `check_field` carries the
t-UED field.

## applied

* `self_checking_datapath`: choice `input_structuring: {none, distance_cover, m_out_of_n, unate_logic}` added; papers += lala_2001.
* `self_checking_datapath`: choice `output_structuring: {none, ordered_codes, graph_cover}` added.
* `berger`: choice `construction: {berger, bose_lin_method2, borden, berger_burst, bose_burst, blaum_burst}` added. `bose_lin_method1` is omitted because `check_field=modulo_reduced` already names its field (ruling: keep `check_field`), so Bose-Lin method 1 is `construction=berger` with `check_field=modulo_reduced`. `borden` is kept as the line says, although it is nonseparable and has no check field (lala_2001 already in papers).
* `berger.construction` += `berger_burst, bose_burst, blaum_burst` (folded into the choice above).
* `berger`: choice `burst_type: {random, unidirectional}` added; meaningful only under the three burst values.
* `self_checking_datapath.encoding` += `m_out_of_n_output, berger_output, modified_berger_output, mod3_residue_output` (the PLA lines are applied; the ruling excludes nothing in this group).
* `self_checking_datapath`: choice `product_activation: {unrestricted, exactly_one}` added.
* `self_checking_datapath`: choice `auxiliary_check: {none, alternate_product_xor_trees}` added.
* `time_redundancy.transform` += `self_dual`; papers += lala_2001. No variant doc was written for the new value (the instruction's variant rule covers new families); `time_redundancy/self_dual.md` would complete the `transform` variant set from the lala_2001#s04 block.
* `time_redundancy`: choice `complement_synthesis: {optimal, arbitrary_self_dual}` added; only under `transform=self_dual`.
* `duplication.comparison_point` += `register_file_ecc_read` (sullivan_2018 already in papers).
* `duplication`: choice `organization: {swap_ecc, swap_predict}` added. The predictor slot the note asks for is not opened.
* `duplication`: choice `storage_correction: {detection_only, sec_dp, sec_ded_dp}` added.
* `duplication`: choice `voter_replication: {single, triple}` added (lyons_vanderkulk_1962 already in papers).
* `duplication`: choice `voter_placement: {per_driven_module_input, shared_source_output, omitted}` added.
* `duplication`: choice `module_granularity: {whole_computer, modular_partition}` added.
* `two_rail_tree`: choices `fail_safe_lockout: {none, irreversible_until_reset}`, `safe_value: {all_zeros, all_ones, application_defined}` and `realization: {translator, state_element_and_output_gates}` added with the names the line gives (lala_2001 already in papers).
* `majority_voter` (the comparator value the TMR and fail-safe lines presuppose): new candidate of `two_rail_space()` after `m_out_of_n_checker`, so every `comparator` slot admits it. Choices `inputs: IntRange(3, 7, 2)` (3 is TMR, a wider odd N is the NMR core of lala_2001#s07's hybrid scheme; the upper bound 7 is a placeholder) and `disagreement_indication: Bool` (the modified voter that names the outvoted module); mutations `widen_vote_to_nmr`, `add_disagreement_detector`, `demote_vote_to_compare`; papers von_neumann_1956, lyons_vanderkulk_1962, lala_2001. The gap file's `decision_mechanism: {majority_vote, output_match}` is not added, because the comparator slot's family (`two_rail_tree` against `majority_voter`) already carries that distinction and `promote_compare_to_vote` exists. Doc: `arch/checker/majority_voter.md` (three references from the bundle's citations); gap file `none`; no variant doc.
* `duplication`: the `checkpoint_retry_recovery` fallback. The family is not added (scope ruling); the plan's named fallback from `gaps/duplication.md` is applied as choice `recovery_policy: {stop_clock, correct_flush_restart, reset_restore_resume, checkpoint_freeze_ecc_repair, check_stop}`; papers += burks1946, check_slegel_1999, schwarz_2002 (austin_1999 and slegel_1999 already). Caveat: the retry scope of maruyama_2010 (single instruction alone) and kalla_2010 (flush/refetch through speculative resources) is not a value of the gap's enum, and those two handles are not added because their recovery is triggered by parity/ECC rather than by duplication.
* `duplication`: the `standby_sparing` fallback. The family is not added (scope ruling); the gap file's `standby_spares` and `post_fault_mode` are applied as `standby_spares: IntRange(0, 5)` (five or fewer spares per lala_2001#s07; STAR at S = 2 and 3; the upper bound is a placeholder) and `post_fault_mode: {remain_replicated, simplex, replace_with_spare}`; papers += lala_2001, avizienis_gilley_1971 (the STAR handle; `avizienis_1971` stays the arithmetic-codes paper under `residue`). `replication` stays `IntRange(2, 3)`; the gap's NMR widening is not a named fallback.
* new family `m_out_of_n_checker` inserted into `two_rail_space()` after `two_rail_tree`, snippet as in the plan (choices `code_class` / `realization` / `partitioning` / `intermediate_code` / `deep_case_delay_style` / `gate_polarity`, six mutations, papers anderson_metze_1973, marouf_friedman_1978, lala_2001, richards_1955; no component slot, since a `two_rail_space()` slot from inside `two_rail_space()` recurses). `two_rail_tree.input_code` keeps `m_out_of_n` for the translator-fed case. Docs: `arch/checker/m_out_of_n_checker.md` (references lala_2001, marouf_friedman_1978, richards_1955, copied from the bundle; anderson_metze_1973 is not in the bundle's citations and is not cited there); gap file `none`. Variant docs, one per `code_class` value, each pinned by a proposal block and named as a distinct checker: `k_out_of_2k.md` is the moved `two_rail_tree/m_out_of_n.md` (Anderson-Metze; front matter, title and the closing sentence adapted, references kept), `arbitrary_m_out_of_n.md` from marouf_friedman_1978, `one_out_of_n.md` from richards_1955#s09. The `realization` values are circuit forms and get no variant doc.
* Module docstring bumped to rev 8 and `two_rail_space()`'s docstring names the two added candidates.

Absorbed (`unordered_constant_weight_code`) and rejected entries (`invalid_opcode_detector`, `multiplexed_restorative_logic`) needed no change.

## skipped

* new family `checkpoint_retry_recovery` — ruling: core-level recovery stays out; the `recovery_policy` fallback is applied (see applied). No `recovery_space()` and no `recovery` slot were opened.
* new family `standby_sparing` — ruling: core-level sparing stays out; the `standby_spares` / `post_fault_mode` fallback is applied (see applied).
* new family `block_code_ecc` (seven storage-code proposals) — ruling: storage/transmission codes have no arithmetic datapath and stay out; no fallback is named, so nothing is added.
* `berger.construction += bose_lin_method1` — duplicate of `check_field=modulo_reduced`; ruling keeps `check_field`.
* `notes/sullivan_2018.md`'s request for `register_file_ecc_read` on `residue` — not a plan line; the value is applied on `duplication` only.

## deferred (other file)

* new family `parity_prediction_divider` [nicolaidis_1997] — ruling: one incremental paper does not carry a family. Its snippet also needs `div_space()` from `div_spaces.py` as the `array` slot, and that space has no unrolled nonrestoring CAS-array candidate, so the slot cannot be filled from `checker_spaces.py` alone. The alternative the plan names is `parity_prediction_multiplier += choice unit: {multiplier, divider}`.

applied 21 (17 new-value lines, 1 presupposed comparator family, 2 fallback applications, 1 new family), skipped 5 (3 families, 1 duplicate value, 1 note request), deferred 1

## checks

* `_all_spaces()` returns 36 spaces.
* `python3 -m chialu.archdocs`: `197 docs for 222 families; 25 undocumented; 402 variant docs`, no ORPHAN / BAD REF / BAD VARIANT line. The 25 undocumented families belong to other appliers' concurrent additions; `m_out_of_n_checker` and `majority_voter` are documented. The baseline `ORPHAN comparator_digit_selection` line is gone (another applier registered the family).
* `python3 -m chialu.extract vocab` renders.
* `kb_section_mul16()` renders.
* Every handle in a `papers=` tuple of `checker_spaces.py` resolves in `PAPER_DB`; `nicolaidis_1999` in `time_redundancy` is still a valid handle and was left in place.
* Doc shape: `m_out_of_n_checker.md` first paragraph 643 characters, 346 words after it, 3 references; `majority_voter.md` 497 characters, 271 words, 3 references; the three variant docs are 293 to 458 characters and 104 to 142 words with 2 references each.
