# new-family review: checker

Input: `run/extract/reduce/newfam_checker.md` (30 proposals; `m_out_of_n_checker` and `standby_replacement_recovery` each appear twice under different handles and are told apart by handle below). Registry: `chialu/spaces/checker_spaces.py` (`checker_space`, `two_rail_space`); neighbouring domains checked: `redundant_spaces.py`, `adder_spaces.py`, `mul_spaces.py`, `fma_dot_spaces.py`, and `div_spaces.py` for the divider slot. No neighbouring domain carries a recovery, sparing, storage-code or constant-weight-checker family. The prior-pass gap files under `knowledge/extract/gaps/` are cited where they already list a value. Nothing under `chialu/spaces` changes in this pass; a human applies every line.

## absorbed

* `unordered_constant_weight_code -> two_rail_tree.input_code=m_out_of_n / two_rail` — the m-out-of-n code (exactly m ones, n!/((n-m)!m!) codewords, every single and unidirectional multiple error detected) and the k-pair two-rail code are the code definitions behind the two existing `input_code` values; its `k_out_of_2k` and `one_out_of_n` specializations become `m_out_of_n_checker.code_class` below. [lala_2001#s03]

## new values

8 proposals, 17 lines.

* `self_checking_datapath += choice input_structuring: {none, distance_cover, m_out_of_n, unate_logic}` — bidirectional-error-free logic: the input code is chosen so bidirectionally adjacent cubes lie at distance 2 or more, or the circuit is realized unate (inverter-free) so the inversion parity from every fault site to every affected output is consistent and a single stuck-at fault yields only a single-bit or a unidirectional multibit error, which is the property `berger` and `m_out_of_n_checker` require of the checked unit; the registry analogue is `parity_prediction_multiplier.fault_secure_structuring`; the minimum-bit encoding search is NP-hard (a Boolean-cover problem) and is not registered. `berger` is the alternative host. [lala_2001#s04]
* `self_checking_datapath += choice output_structuring: {none, ordered_codes, graph_cover}` — the output side of the same discipline: ordered output codes, or a graph-embedding cover found by exhaustive search for the smallest m. [lala_2001#s04]
* `berger += choice construction: {berger, bose_lin_method1, bose_lin_method2, borden}` — t-unidirectional error detecting codes: Bose-Lin derives 2, 3 or 4 check bits from the zero count (multiplicity 2, 3, 6; method 1 reaches 2^(c-2) + c - 2), method 2 maps the high bits into 2-out-of-4 codewords (5 + 2^(c-4) + c - 4 at c >= 5), Borden restricts codeword weight modulo t+1 and is nonseparable. `check_field=modulo_reduced` already names the method-1 field, so the human decides which choice carries it; `borden` has no check field and may be excluded as nonseparable (the `an_code` precedent). [lala_2001#s03]
* `berger.construction += berger_burst, bose_burst, blaum_burst` — burst-unidirectional codes distribute the check bits through the information word: the Berger form costs b + log2(k/b) bits for random bursts of length b plus arbitrary unidirectional errors, and Blaum's construction reaches burst capacity 9/19/41 bits against Bose's 8/16/32 at r = 4/5/6. [lala_2001#s03]
* `berger += choice burst_type: {random, unidirectional}` — the burst class the construction targets; meaningful only under the three burst values. [lala_2001#s03]
* `self_checking_datapath.encoding += m_out_of_n_output, berger_output, modified_berger_output, mod3_residue_output` — a self-checking PLA: the outputs are code-encoded so stuck-at, bridging and contact faults on cross-points and product lines produce unidirectional non-code outputs (the two-rail form is the existing `two_rail_full`; `modified_berger` is already listed in `gaps/berger.md`); the mod-3 value adds 2 output lines and belongs to the non-concurrent variant. A PLA is control logic rather than an arithmetic unit, so the human may reject the three PLA lines as out of scope. [lala_2001#s04]
* `self_checking_datapath += choice product_activation: {unrestricted, exactly_one}` — PLA only: at most one product term active per input keeps product-line faults unidirectional. [lala_2001#s04]
* `self_checking_datapath += choice auxiliary_check: {none, alternate_product_xor_trees}` — two EX-OR trees fed by alternate product terms, combined with mod-3 output residues, cover all single PLA faults (the trees cover the product terms, the residue covers the sum lines). [lala_2001#s04]
* `time_redundancy.transform += self_dual` — alternating logic: a self-dual complement is combined with the functional output parity into a self-dual function, the complemented input pattern is applied in the next period and must give the complemented response; 100% time redundancy against the 33% average area of an independently implemented parity predictor. The family doc already describes alternating logic and `gaps/time_redundancy.md` lists this value. [lala_2001#s04]
* `time_redundancy += choice complement_synthesis: {optimal, arbitrary_self_dual}` — how the self-dual complement is synthesized; only under `transform=self_dual`. [lala_2001#s04]
* `duplication.comparison_point += register_file_ecc_read` — SwapCodes: the original instruction writes the data, the shadow writes only the destination register's ECC check bits, and the register file's ECC check on the next read is the comparator, so a single pipeline error cannot corrupt both halves of the codeword (Swap-ECC: 21% mean slowdown on a P100, 11% worst-case energy). `notes/sullivan_2018.md` asks for the same value on `residue`. [sullivan_2018]
* `duplication += choice organization: {swap_ecc, swap_predict}` — Swap-ECC duplicates every eligible arithmetic instruction; Swap-Predict skips duplication for moves, fixed-point add/sub and multiply/MAD (`predicted_operations`) and lets a separate predictor generate the check bits (16% and 15% mean slowdown, 33% dynamic instruction bloat, 74% worst case on lavaMD). The predictor is the check-bit generalization of `parity_prediction_adder` / `parity_prediction_multiplier`, and the note's `space_gaps` asks for a predictor slot, which the human may open instead of this choice. [sullivan_2018]
* `duplication += choice storage_correction: {detection_only, sec_dp, sec_ded_dp}` — the register ECC decoder distinguishes a storage error, which it corrects, from a compute error, which it only detects, so a compute error is never miscorrected. [sullivan_2018]
* `duplication += choice voter_replication: {single, triple}` — TMR: the mechanism itself (three identical modules, two-out-of-three majority) is `duplication.replication=3` with mutation `promote_compare_to_vote`, and lyons_vanderkulk_1962 is already in `papers`; the proposal adds one voter in the original arrangement or three voters in the analysed configuration. `gaps/duplication.md` proposes the `decision_mechanism=majority_vote` choice and the `majority_voter` comparator value that these three lines presuppose. [lyons_vanderkulk_1962]
* `duplication += choice voter_placement: {per_driven_module_input, shared_source_output, omitted}` — for a high-fanout interconnection the voter sits at each driven module's input (M-unit), once at the shared source output, or is omitted (Q-unit, direct connection); an untriplicated N-unit is `replication=1` for that module; per-input voting can lose to shared or omitted voting when fanout is high. [lyons_vanderkulk_1962]
* `duplication += choice module_granularity: {whole_computer, modular_partition}` — whole-computer TMR loses to the simplex machine beyond its MTF; partitioning into trios whose operating interval is short against their MTF gives 0.95 reliability at 60 modules with perfect voters, and imperfect voters (0.999) fix an optimum near m = 1000 (0.988) at about 6x the nonredundant size. The analytical and Monte Carlo reliability models are analysis and are not registered. [lyons_vanderkulk_1962]
* `two_rail_tree += choice fail_safe_lockout: {none, irreversible_until_reset}` — ultimate fail-safe logic: after a detectable unsafe error a translator or a presettable state element with output gates forces the checker output to a predetermined safe value (00 in the worked design, against the unsafe 11) and holds it until reset; `safe_value: {all_zeros, all_ones, application_defined}` and `realization: {translator, state_element_and_output_gates}` are its sub-choices. `checkpoint_retry_recovery.hard_failure_action` is the alternative host at core level. [lala_2001#s04]

## new families

Five families from 19 proposals. The two recovery families and the storage-code family are core-level and storage mechanisms; the `checker_spaces.py` docstring names "lockstep duplication + checkpoint retry at core level" as shipping practice, and `gaps/duplication.md` asks for `recovery_policy` and `standby_spares` on `duplication`, so the registry already reaches for this vocabulary. Their scope is the first open decision at the end.

### checkpoint_retry_recovery

Merged proposals: `checkpoint_retry_recovery` [file_webb2007#s01], `checkpointed_hardware_recovery` [slegel_1999], `instruction_retry_recovery` [maruyama_2010], `pipeline_flush_retry` [kalla_2010]. The transient leg of the two STAR proposals (stop, reset powered units, resume from a stored rollback address) is the `checkpoint_store=program_rollback_address` value here; the STAR proposals themselves are counted under `standby_sparing`.

* name: `checkpoint_retry_recovery`
* domain: checker. Proposed placement is a new `recovery_space()` in `checker_spaces.py` beside `two_rail_space()`, opened by the detection families as a `recovery` slot the way `cmp_slot` is opened; the alternative is a candidate of `checker_space()`. The family must not open a `checker_space()` slot of its own (recursion).
* doc: `detection-triggered re-execution from saved state: an ECC-protected checkpoint of the architected state (R-unit) or the speculative pipeline's own flush/refetch path replays the faulting instruction; a retry threshold hands persistent errors to check-stop, a machine-check interrupt or a spare core`
* execution_style: `variable_iteration` (retry repeats until success or a threshold)
* gap it closes: `duplication.comparison_point=checkpoint_commit` and the mutation `add_checkpoint_rollback` name a checkpoint without a structure to land on, and the recovery in every commercial instance is triggered by parity, residue or ECC detection rather than by duplication, so hanging it on `duplication` would misplace three of the four sources.
* design choices:
  * `checkpoint_store: EnumChoice(("dedicated_recovery_unit_ecc", "speculative_pipeline_resources", "program_rollback_address"))` — the R-unit holds the full architected state under ECC [slegel_1999, file_webb2007#s01]; Power7 uses the speculative execution resources and branch redirect and has no recovery unit [kalla_2010]; STAR resumes from a stored rollback address [avizienis_gilley_1971]
  * `retry_scope: EnumChoice(("single_instruction_alone", "flush_refetch_reexecute", "core_retry_from_checkpoint"))` — cancel all in-flight instructions and execute the faulting one alone [maruyama_2010]; flush, refetch and reexecute the affected instructions [kalla_2010]; precise core retry from the checkpoint [file_webb2007#s01, slegel_1999]
  * `state_repair: EnumChoice(("none", "ecc_read_correct_rewrite"))` — the frozen checkpoint is read through ECC, corrected and rewritten into the shadow state before restart [slegel_1999]
  * `restart: EnumChoice(("serialization_interrupt", "branch_redirect", "resume_in_place"))` — G5 restarts by a serialization interrupt [slegel_1999]; Power7 by branch redirect [kalla_2010]; Sparc64 VIIIfx resumes normal execution once the retried instruction commits [maruyama_2010]
  * `retry_policy: EnumChoice(("single_attempt", "repeat_to_threshold"))` — a second error before successful completion check-stops the G5 [slegel_1999]; Sparc64 VIIIfx repeats until success or a threshold [maruyama_2010]; the threshold value is not given, so no `IntRange` is proposed
  * `hard_failure_action: EnumChoice(("check_stop", "software_interrupt", "machine_check_software_recovery", "core_sparing", "thread_migration"))` — check-stop [slegel_1999]; interrupt to software after the threshold [maruyama_2010]; precise software recovery through the machine-check architecture and dynamic transparent core sparing [file_webb2007#s01]; suspend the threads and resume them on another core [kalla_2010]; the last two values cross to `standby_sparing`
* component slots: none in the snippet. If `block_code_ecc` is registered, a `checkpoint_code` slot admitting it carries the R-unit's ECC.
* mutations: `add_dedicated_recovery_unit`, `fold_retry_into_speculative_flush`, `single_step_faulting_instruction`, `raise_retry_threshold`, `escalate_to_core_sparing`, `demote_to_check_stop`
* handles: slegel_1999 [landmark], maruyama_2010 [landmark], kalla_2010 [landmark], file_webb2007#s01 [slides]; the rollback leg from avizienis_gilley_1971 [landmark]
* evidence strength: 4 merged proposals, 4 sources plus the STAR leg; no textbook or thesis block (lala_2001's checkpoint-placement material appears only in `gaps/time_redundancy.md`, not as a proposal). Results: G5 recovery "essentially 100%" of transient processor errors at several thousand cycles; z6 "almost all" hardware errors; Sparc64 VIIIfx any single-bit register or ALU error when a retry succeeds before the threshold; Power7 reports none.
* snippet (new `recovery_space()` in `checker_spaces.py`, or `checker_space()`):

```python
        Architecture(
            "checkpoint_retry_recovery",
            papers=("slegel_1999", "file_webb2007", "maruyama_2010",
                    "kalla_2010", "avizienis_gilley_1971"),
            execution_style="variable_iteration",
            design_choices={
                "checkpoint_store": EnumChoice(
                    ("dedicated_recovery_unit_ecc",
                     "speculative_pipeline_resources",
                     "program_rollback_address")),
                "retry_scope": EnumChoice(("single_instruction_alone",
                                           "flush_refetch_reexecute",
                                           "core_retry_from_checkpoint")),
                "state_repair": EnumChoice(("none",
                                            "ecc_read_correct_rewrite")),
                "restart": EnumChoice(("serialization_interrupt",
                                       "branch_redirect",
                                       "resume_in_place")),
                "retry_policy": EnumChoice(("single_attempt",
                                            "repeat_to_threshold")),
                "hard_failure_action": EnumChoice(
                    ("check_stop", "software_interrupt",
                     "machine_check_software_recovery",
                     "core_sparing", "thread_migration"))},
            mutations=("add_dedicated_recovery_unit",
                       "fold_retry_into_speculative_flush",
                       "single_step_faulting_instruction",
                       "raise_retry_threshold",
                       "escalate_to_core_sparing",
                       "demote_to_check_stop"),
            doc="detection-triggered re-execution from saved state: an "
                "ECC-protected checkpoint of the architected state "
                "(R-unit) or the speculative pipeline's own flush/refetch "
                "path replays the faulting instruction; a retry threshold "
                "hands persistent errors to check-stop, a machine-check "
                "interrupt or a spare core"),
```

* human decisions: (1) `recovery_space()` slot versus `checker_space()` candidate versus `duplication.recovery_policy` from `gaps/duplication.md`; (2) whether `checkpoint_retry_recovery` and `standby_sparing` are one family `retry_and_sparing_recovery`, since STAR, z6 and Power7 chain retry and replacement (the two-family form keeps each choice set single-purpose); (3) `execution_style`, since the retry loop is not an arithmetic iteration.

### standby_sparing

Merged proposals: `standby_reconfiguration` [lala_2001#s07], `standby_replacement_recovery` [avizienis_1971], `standby_replacement_recovery` [avizienis_gilley_1971], `hybrid_modular_standby` [lala_2001#s07]. The two STAR proposals describe one paper (see the avizienis_1971 note status under open decisions). The core-sparing leg of file_webb2007#s01 and the thread migration of kalla_2010 are instances, counted under `checkpoint_retry_recovery`.

* name: `standby_sparing`
* domain: checker, in the same `recovery_space()` as `checkpoint_retry_recovery`
* doc: `a failed module is switched out for a spare: cold (unpowered, bus-isolated, zero outputs) or hot spares, detection by self-checking codes, periodic test, watchdog or NMR disagreement, retry first to separate transient from permanent faults; STAR TARP, hybrid (N,S) TMR-plus-spares, z6 core sparing`
* execution_style: feed_forward (default, omitted)
* gap it closes: `duplication` models concurrent replicas and comparison only; dormant spares, a replacement threshold and a switching network have no home, and `gaps/duplication.md` asks for `standby_spares` and `post_fault_mode=replace_with_spare`.
* design choices:
  * `active_modules: IntRange(1, 5)` — 1 is the standby scheme where only one module operates [lala_2001#s07]; 3 or more is the hybrid scheme whose voted TMR/NMR core masks faults while disagreement detectors identify the failed module, tolerating floor((N-1)/2) simultaneous core faults [lala_2001#s07]; the upper bound is not given by a proposal
  * `spares: IntRange(0, 5)` — S spares give R = 1 - (1 - R_m)^(S+1) under perfect detection and switchover, and five or fewer is best for missions below one-tenth of the simplex mean life [lala_2001#s07]; STAR is evaluated at S = 2 and 3 [avizienis_1971, avizienis_gilley_1971]; 0 spares is the hybrid core after exhaustion, which continues as plain TMR
  * `spare_state: EnumChoice(("cold_unpowered", "hot_powered"))` — cold or hot standby [lala_2001#s07]; STAR's unpowered spares stay bus-connected through isolation circuits and produce only zero outputs [avizienis_1971, avizienis_gilley_1971]
  * `detection: EnumChoice(("self_checking_codes", "periodic_test", "watchdog_timer", "disagreement_detector"))` — periodic testing, self-checking logic or a watchdog [lala_2001#s07]; coded words and status monitors [avizienis_1971]; disagreement detectors on the voted core [lala_2001#s07]
  * `retry_before_replace: BoolChoice()` — retry distinguishes a temporary from a permanent fault before reconfiguration [lala_2001#s07]; STAR's rollback-then-replacement sequence [avizienis_gilley_1971]; the hybrid scheme's `retry` [lala_2001#s07]
  * `replacement_threshold: IntRange(1, 4)` — repeated indications attributed to one unit cause its replacement [avizienis_1971]; the STAR tables evaluate K = 1 and K = infinity, so the range is a placeholder
  * `switch: EnumChoice(("power_switching", "information_line_switching", "rotary_iterative_cell"))` — STAR powers units off and on [avizienis_gilley_1971]; the hybrid switching network is a rotary iterative cell [lala_2001#s07]
* component slots: none. The voted core of the hybrid scheme is `duplication` with `replication=3` and the vote, but a `checker_space()` slot from inside a space that checker families open would recurse; the snippet carries no slot and the doc names the composition.
* mutations: `add_spare`, `unpower_spares`, `add_retry_before_replacement`, `vote_active_modules`, `raise_replacement_threshold`, `switch_by_power_not_lines`
* handles: lala_2001#s07 [textbook, two blocks], avizienis_gilley_1971 [landmark], avizienis_1971 [landmark; note status `mismatch`, the pdf is the STAR paper]; instances file_webb2007#s01 [slides], kalla_2010 [landmark]
* evidence strength: 4 merged proposals from 3 sources, 1 textbook block; the reliability formula and STAR's mission-duration table (12.5 years at reliability 0.9 with S = 3, K = infinity against 0.7 years for MM'69) are the only numbers; no area or delay result.
* snippet (same space as `checkpoint_retry_recovery`):

```python
        Architecture(
            "standby_sparing",
            papers=("lala_2001", "avizienis_gilley_1971", "avizienis_1971",
                    "file_webb2007", "kalla_2010"),
            design_choices={
                "active_modules": IntRange(1, 5),
                "spares": IntRange(0, 5),
                "spare_state": EnumChoice(("cold_unpowered",
                                           "hot_powered")),
                "detection": EnumChoice(("self_checking_codes",
                                         "periodic_test",
                                         "watchdog_timer",
                                         "disagreement_detector")),
                "retry_before_replace": BoolChoice(),
                "replacement_threshold": IntRange(1, 4),
                "switch": EnumChoice(("power_switching",
                                      "information_line_switching",
                                      "rotary_iterative_cell"))},
            mutations=("add_spare", "unpower_spares",
                       "add_retry_before_replacement",
                       "vote_active_modules",
                       "raise_replacement_threshold",
                       "switch_by_power_not_lines"),
            doc="a failed module is switched out for a spare: cold "
                "(unpowered, bus-isolated, zero outputs) or hot spares, "
                "detection by self-checking codes, periodic test, "
                "watchdog or NMR disagreement, retry first to separate "
                "transient from permanent faults; STAR TARP, hybrid "
                "(N,S) TMR-plus-spares, z6 core sparing"),
```

* human decisions: (1) the three `IntRange` bounds are placeholders where noted; (2) `avizienis_1971` must be re-keyed before it enters a `papers=` tuple, because the handle is already cited under `residue` for the arithmetic-error-codes paper while its note reads the STAR paper; (3) whether a core-level sparing scheme belongs in a registry of arithmetic-unit microarchitectures.

### block_code_ecc

Merged proposals: `parity_block_code` [lala_2001#s03], `hamming_secded_code` [lala_2001#s03], `hsiao_secded_code` [lala_2001#s03], `cyclic_block_code` [lala_2001#s03], `reed_solomon_block_code` [lala_2001#s03], `error_correcting_information_redundancy` [lala_2001#s07], `parity_protection` [carlough_2011]. Every one is a systematic code on a stored or transmitted word, regenerated and compared or syndrome-decoded, rather than a code that commutes with arithmetic.

* name: `block_code_ecc`
* domain: checker (no storage domain exists). Proposed placement is a new `storage_code_space()` in `checker_spaces.py`, which `checkpoint_retry_recovery` opens as `checkpoint_code` and which `duplication.comparison_point=register_file_ecc_read` refers to; the alternative is a candidate of `checker_space()`.
* doc: `systematic block code on a stored or transmitted word: parity, Hamming/Hsiao SEC-DED, cyclic or Reed-Solomon check bits regenerated and compared, or decoded to a syndrome that locates the bit; protects the state around the arithmetic (register file, checkpoint array, bus, control) rather than the arithmetic`
* execution_style: feed_forward (default, omitted)
* gap it closes: `notes/file_webb2007__s01.md` records "the checker vocabulary lacks general ECC/parity/state-checking families"; the R-unit checkpoint, the SwapCodes register file and the z196 accelerator interfaces all rely on such a code and none is instantiable.
* design choices:
  * `code: EnumChoice(("parity", "hamming", "hsiao", "horizontal_vertical_parity", "majority_logic_decodable", "cyclic", "reed_solomon"))` — one parity bit [lala_2001#s03]; matrix columns encode bit positions, 2^c >= k + c + 1 [lala_2001#s03]; odd-weight minimum columns with balanced rows, the (12, 8) example [lala_2001#s03]; the memory-system code list [lala_2001#s07]; D(X) shifted by n-k and divided by G(X), n-k check bits [lala_2001#s03]; (n, k) over GF(2^m), length 2^m - 1, the (255, 239) example [lala_2001#s03]
  * `capability: EnumChoice(("detect", "sec", "sec_ded", "t_symbol_correct"))` — parity detects odd multiplicities; distance 3 SEC becomes distance 4 SEC-DED with a whole-word parity bit; RS corrects t symbols at minimum distance 2t + 1 [lala_2001#s03]
  * `parity_grouping: EnumChoice(("whole_word", "per_byte", "overlapping_blocks"))` — one EX-OR tree, bytewise parity, or overlapping blocks that locate a single erroneous bit [lala_2001#s03]; 8-bit parity on every accelerator input and output signal is `per_byte` [carlough_2011]
  * `parity_sense: EnumChoice(("odd", "even"))` [lala_2001#s03]
  * `symbol_width_bits: IntRange(1, 8)` — the m of GF(2^m); 1 for every binary code [lala_2001#s03]
  * `protected_structure: EnumChoice(("memory", "register_file", "checkpoint_state", "interface_signals", "control_state", "state_machine"))` — memory and state-machine assignments at minimum distance 3 [lala_2001#s07]; interface signals and nonduplicated control state [carlough_2011]; the R-unit checkpoint [slegel_1999, file_webb2007#s01]; the register file [sullivan_2018]
  * `multi_error_extension: EnumChoice(("none", "chip_spares", "orthogonal_latin_square_address_skew"))` [lala_2001#s07]
  * `periodic_checking: BoolChoice()` [lala_2001#s07]
* component slots: none; the encoder and syndrome trees are XOR trees below the registry's granularity, and a syndrome decoder is not a two-rail compare.
* mutations: `add_overall_parity_for_double_detect`, `swap_hamming_for_hsiao_odd_weight`, `group_parity_per_byte`, `widen_symbols_to_reed_solomon`, `add_periodic_checking`, `add_chip_spares`
* handles: lala_2001#s03 [textbook, five blocks], lala_2001#s07 [textbook], carlough_2011 [landmark, one paragraph]; instances slegel_1999, file_webb2007#s01, sullivan_2018
* evidence strength: 7 proposals from 3 sources, 2 textbook blocks, 1 landmark instance without results; the numbers are check-bit counts only (Hamming word-length increase 62.5% at k = 8 down to 12.5% at k = 64; a (12, 8) Hsiao code; a (255, 239) RS code at m = 8, t = 8). No arithmetic-unit area or delay figure supports the family.
* snippet (new `storage_code_space()`, or `checker_space()`):

```python
        Architecture(
            "block_code_ecc",
            papers=("lala_2001", "carlough_2011", "slegel_1999",
                    "file_webb2007", "sullivan_2018"),
            design_choices={
                "code": EnumChoice(("parity", "hamming", "hsiao",
                                    "horizontal_vertical_parity",
                                    "majority_logic_decodable",
                                    "cyclic", "reed_solomon")),
                "capability": EnumChoice(("detect", "sec", "sec_ded",
                                          "t_symbol_correct")),
                "parity_grouping": EnumChoice(("whole_word", "per_byte",
                                               "overlapping_blocks")),
                "parity_sense": EnumChoice(("odd", "even")),
                "symbol_width_bits": IntRange(1, 8),
                "protected_structure": EnumChoice(
                    ("memory", "register_file", "checkpoint_state",
                     "interface_signals", "control_state",
                     "state_machine")),
                "multi_error_extension": EnumChoice(
                    ("none", "chip_spares",
                     "orthogonal_latin_square_address_skew")),
                "periodic_checking": BoolChoice()},
            mutations=("add_overall_parity_for_double_detect",
                       "swap_hamming_for_hsiao_odd_weight",
                       "group_parity_per_byte",
                       "widen_symbols_to_reed_solomon",
                       "add_periodic_checking", "add_chip_spares"),
            doc="systematic block code on a stored or transmitted word: "
                "parity, Hamming/Hsiao SEC-DED, cyclic or Reed-Solomon "
                "check bits regenerated and compared, or decoded to a "
                "syndrome that locates the bit; protects the state around "
                "the arithmetic (register file, checkpoint array, bus, "
                "control) rather than the arithmetic"),
```

* human decisions: (1) scope: if storage codes are outside an arithmetic-unit registry, all seven proposals move to `rejected` with the reason "storage/transmission code, no arithmetic datapath" and the count line becomes new families 4 (from 12), rejected 9; (2) `protected_structure` as a choice versus as the context of the opening slot; (3) `code` mixes binary and symbol codes, so `symbol_width_bits` is meaningful only under `reed_solomon`.

### m_out_of_n_checker

Merged proposals: `m_out_of_n_checker` [lala_2001#s05], `m_out_of_n_checker` [marouf_friedman_1978], `one_hot_validity_checker` [richards_1955#s09] (the 1-out-of-n case, required when a component-reduced biquinary adder can raise three outputs after a fault). The absorbed `unordered_constant_weight_code` [lala_2001#s03] is the code these checkers validate.

* name: `m_out_of_n_checker`
* domain: checker, a second candidate of `two_rail_space()` beside `two_rail_tree`, so every `comparator` slot admits it
* doc: `constant-weight code checker: two majority-predicate subcircuits over balanced input groups map m-out-of-n code words to 01/10 and non-code words to 00/11, via a 1-out-of-Z to 2-out-of-4 translator for arbitrary m, n; not a morphic-cell tree`
* execution_style: feed_forward (default, omitted)
* gap it closes: `two_rail_tree.input_code=m_out_of_n` exists as a pinned variant (`arch/checker/two_rail_tree/m_out_of_n.md`), but `tree_arity` and `embedded` do not apply to a majority-predicate network, and `gaps/two_rail_tree.md` states that "the m-out-of-n checker constructions are not two-rail trees" and asks for a translator front end and a realization-form choice; both proposals name the two-rail family only as the terminating stage.
* design choices:
  * `code_class: EnumChoice(("k_out_of_2k", "arbitrary_m_out_of_n", "one_out_of_n"))` — the applicability classes [lala_2001#s05]; 1-out-of-n for any number of lines [richards_1955#s09]; any m-out-of-n through the partition procedures [marouf_friedman_1978]
  * `realization: EnumChoice(("two_level_and_or", "multilevel_unate", "cellular_threshold_array", "translator_cascade", "pass_transistor_cells", "inverter_free_pla"))` — two-level (2^k test words, gate count 2k^2 - 2k + 2 at depth k for Smith, 2k^2 - k + 1 at depth 2k - 1 for Reddy), cellular threshold arrays (2k test words), translator cascades (9 and 7 test words for 2-out-of-6 and 2-out-of-5), pass-transistor cells (3 NAND + 3 NOR per 2-out-of-4 cell), inverter-free PLAs [lala_2001#s05]; two-level or multilevel unate majority functions [marouf_friedman_1978]
  * `partitioning: EnumChoice(("balanced", "balanced_recursive", "complement_dual"))` — balanced input sets, recursive partition for n > 4m, and dualization for m > n/2 to the (n-m)-out-of-n code [marouf_friedman_1978]
  * `intermediate_code: EnumChoice(("none", "one_out_of_4", "one_out_of_5", "one_out_of_6", "one_out_of_E"))` — the 1-out-of-Z code the majority stage emits before the totally self-checking translator to 2-out-of-4; `none` is the direct k-out-of-2k form; the proposal's single-valued `output_translation` is implied by any value other than `none` [marouf_friedman_1978]
  * `deep_case_delay_style: EnumChoice(("recursive", "flattened_nine_level"))` — 4 + 3k gate levels with k = ceil(log2(n/m)) - 1 for the recursive n > 4m construction, or 9 levels flattened [marouf_friedman_1978]
  * `gate_polarity: EnumChoice(("positive_unate_and_or", "inverting_nand_nor"))` — only the positive-unate form keeps coverage of multiple unidirectional faults [marouf_friedman_1978]
  * m and n (`target_weight`, `code_length`) are instance parameters like `width`, not choices
* component slots: none in the snippet. The construction terminates in a two-rail pair check; a `two_rail_space()` slot from inside `two_rail_space()` recurses, so the final 2-out-of-4 check is named by `intermediate_code`, or the human defines a `two_rail_tree`-only sub-space for a `final_checker` slot.
* mutations: `swap_realization`, `recurse_input_partition`, `flatten_recursive_case`, `dualize_for_complement_weight`, `insert_code_translator`, `collapse_to_two_rail_tree` (crosses to `two_rail_tree` when the inputs are complementary pairs)
* handles: lala_2001#s05 [textbook], marouf_friedman_1978 [incremental], richards_1955#s09 [textbook]; anderson_metze_1973 is taken from `two_rail_tree.papers` and the variant doc rather than from a proposal
* evidence strength: 3 merged proposals plus the absorbed code definition, 2 textbook blocks and 1 incremental paper; lala_2001#s05 gives abstract gate, level and test-set counts, marouf_friedman_1978 gives 46-97% logic-complexity saving and 75-97% gate-input saving against Anderson for m = 3..6 and a 172-word test set out of 1820 at m = 4, n = 16; no synthesis-era area figure.
* snippet (insert into `two_rail_space()` after `two_rail_tree`):

```python
        Architecture(
            "m_out_of_n_checker",
            papers=("anderson_metze_1973", "marouf_friedman_1978",
                    "lala_2001", "richards_1955"),
            design_choices={
                "code_class": EnumChoice(("k_out_of_2k",
                                          "arbitrary_m_out_of_n",
                                          "one_out_of_n")),
                "realization": EnumChoice(("two_level_and_or",
                                           "multilevel_unate",
                                           "cellular_threshold_array",
                                           "translator_cascade",
                                           "pass_transistor_cells",
                                           "inverter_free_pla")),
                "partitioning": EnumChoice(("balanced",
                                            "balanced_recursive",
                                            "complement_dual")),
                "intermediate_code": EnumChoice(("none", "one_out_of_4",
                                                 "one_out_of_5",
                                                 "one_out_of_6",
                                                 "one_out_of_E")),
                "deep_case_delay_style": EnumChoice(
                    ("recursive", "flattened_nine_level")),
                "gate_polarity": EnumChoice(("positive_unate_and_or",
                                             "inverting_nand_nor"))},
            mutations=("swap_realization", "recurse_input_partition",
                       "flatten_recursive_case",
                       "dualize_for_complement_weight",
                       "insert_code_translator",
                       "collapse_to_two_rail_tree"),
            doc="constant-weight code checker: two majority-predicate "
                "subcircuits over balanced input groups map m-out-of-n "
                "code words to 01/10 and non-code words to 00/11, via a "
                "1-out-of-Z to 2-out-of-4 translator for arbitrary m, n; "
                "not a morphic-cell tree"),
```

* human decisions: (1) family versus the "prefer new values" alternative of adding `realization`, `partitioning` and `gate_polarity` to `two_rail_tree` under `input_code=m_out_of_n`; the family is chosen because the gap file and both proposals say the structure is not a tree, but the alternative keeps `two_rail_space()` at one candidate; (2) if the family is registered, `arch/checker/two_rail_tree/m_out_of_n.md` becomes this family's doc and `two_rail_tree.input_code` either drops `m_out_of_n` or keeps it for the translator-fed case; (3) the `final_checker` slot recursion.

### parity_prediction_divider

Single proposal: `parity_prediction_divider` [nicolaidis_1997].

* name: `parity_prediction_divider`
* domain: checker, in `checker_space()` beside `parity_prediction_multiplier`
* doc: `nonrestoring CAS array rebuilt from redundant-carry cells; carries that fan out to several cells are cut-safe routed or duplicated and two-rail checked; quotient and remainder parities predicted from partial carry and input parities`
* execution_style: feed_forward (the array is combinational, like `parity_prediction_multiplier`)
* gap it closes: the registry has parity prediction for the adder and the multiplier and nothing for a divider; a divider's carries feed several cells, which the multiplier's cellular fault-secureness proof does not cover, and the quotient and remainder need separate parity equations.
* design choices:
  * `interconnect_protection: EnumChoice(("cut_safe_routing", "duplicated_two_rail"))` — a carry feeding several cells is routed so a cut affects an odd number of sum paths, or is carried as a normal/redundant pair checked by a double-rail checker [nicolaidis_1997]
  * `replica_cell_style: EnumChoice(("independent_outputs", "shared_propagate"))` — Figure 3 / type 1 against Figure 4 / type 2 carry-replica logic, the name `notes/nicolaidis_1997.md` gives the cell pair and `gaps/parity_prediction_adder.md` already proposes for the adder; type 2 halves the area overhead (35-37% against 60-66%) and raises the delay overhead (23-37% against 10-28%) [nicolaidis_1997]
  * `primary_input_checking: BoolChoice()` — whether primary-input faults are covered [nicolaidis_1997]
  * the proposal's `fanout_class: {odd_cell, even_cell}` is a property of each cell's position in the array rather than a designer's choice and is folded into the doc
* component slots:
  * `comparator: two_rail_space()` — as every checker family
  * `array: div_space()` — the protected divider; `restoring_nonrestoring.style=nonrestoring` is the closest candidate, but `div_space()` families are `fixed_iteration` and the unrolled CAS array has no entry there (add `div_space` to the `arith_spaces` import in `checker_spaces.py`)
* mutations: `swap_interconnect_protection`, `swap_replica_cell_style`, `add_primary_input_check`, `upgrade_to_residue`
* handles: nicolaidis_1997 [landmark]
* evidence strength: 1 proposal, 1 landmark paper, no textbook or thesis block; the ES2 1.0-µm table covers 4x4 to 32x32 (area overhead 34.88-65.56%, delay overhead 10.53-36.59%); the note flags the 4x4 type-1 secure-area entry (1.02 mm2 against a 0.06 mm2 baseline and 59.97% overhead) as a print inconsistency. A single-paper family is the weakest of the five.
* snippet (insert after `parity_prediction_multiplier` in `checker_space()`):

```python
        Architecture(
            "parity_prediction_divider",
            papers=("nicolaidis_1997",),
            design_choices={
                "interconnect_protection": EnumChoice(
                    ("cut_safe_routing", "duplicated_two_rail")),
                "replica_cell_style": EnumChoice(("independent_outputs",
                                                  "shared_propagate")),
                "primary_input_checking": BoolChoice()},
            components=dict(cmp_slot, array=div_space()),
            mutations=("swap_interconnect_protection",
                       "swap_replica_cell_style",
                       "add_primary_input_check",
                       "upgrade_to_residue"),
            doc="nonrestoring CAS array rebuilt from redundant-carry "
                "cells; carries that fan out to several cells are "
                "cut-safe routed or duplicated and two-rail checked; "
                "quotient and remainder parities predicted from partial "
                "carry and input parities"),
```

* human decisions: (1) family versus `parity_prediction_multiplier += choice unit: {multiplier, divider}`, which keeps one family but leaves `recoding` and `check_depth` meaningless for the divider; (2) the `array` slot has no unrolled nonrestoring candidate in `div_space()`.

## rejected

* `invalid_opcode_detector` [burks1946] — an OR of the decoder outputs of the unused 6-bit operation codes into an indication is a control-decoder validity trap with single-valued choices and no arithmetic datapath; burks1946 stays cited under `duplication` for the accumulator compare.
* `multiplexed_restorative_logic` [von_neumann_1956#s01] — N-line bundles (N of 14,000 to 20,000) with executive and restoring organs and randomizing permutations are a probabilistic-logic construction at N times the lines and 3N times the organs, with no implemented datapath; the majority organ it contains is the `majority_voter` comparator value proposed in `gaps/duplication.md`, and von_neumann_1956 stays cited under `duplication` for the triplication analysis.

## open decisions

* Scope of the recovery and storage families. `checkpoint_retry_recovery`, `standby_sparing` and `block_code_ecc` are core-level and storage mechanisms rather than arithmetic-unit checkers. The registry already names checkpoint retry in the `checker_spaces.py` docstring and in `duplication` (`comparison_point=checkpoint_commit`, mutation `add_checkpoint_rollback`), and `gaps/duplication.md` asks for `recovery_policy` and `standby_spares`. The alternatives are new values on `duplication` for the two recovery families and rejection of the seven storage-code proposals.
* Placement of the recovery families: a `recovery_space()` opened as a `recovery` slot by every checker family (the `cmp_slot` pattern) discloses recovery to the agent for any detector, while a `checker_space()` candidate treats recovery as a checker. Neither recovery family may open a `checker_space()` slot, because that recurses.
* `avizienis_1971` and `avizienis_gilley_1971` are one paper. `notes/avizienis_1971.md` records `status: mismatch` with the STAR paper as `actual_citation`, while the bundle's citation and `residue.papers` refer to "Arithmetic Error Codes: Cost and Effectiveness Studies". The handle needs re-keying before the `standby_sparing` snippet's `papers=` tuple is applied; `avizienis_gilley_1971` alone is safe.
* `m_out_of_n_checker` versus new values on `two_rail_tree.input_code=m_out_of_n` is the one new-family call that the "prefer new values" rule argues against; the variant doc `two_rail_tree/m_out_of_n.md` moves with the mechanism if the family is registered.
* The `fail_safe_lockout`, `voter_replication`, `voter_placement` and `module_granularity` lines presuppose the `majority_voter` comparator value and the `decision_mechanism` choice from `gaps/duplication.md`; without those, the TMR lines have no vote to attach to.
* The three PLA lines under `self_checking_datapath` register a control-logic structure; the human may reject them as out of scope, which would move `self_checking_pla` to `rejected`.
* `swapped_codeword_duplication`'s `organization=swap_predict` describes a check-bit predictor rather than a replica; the note asks for a predictor slot, which would make Swap-Predict a `duplication` instance whose `comparator` is the register-file ECC and whose shadow is `parity_prediction_adder` or `parity_prediction_multiplier` generalized to ECC check bits.
* `berger.construction=bose_lin_method1` duplicates `berger.check_field=modulo_reduced`; one of the two names must carry the t-UED field.
* The `IntRange` bounds in `standby_sparing` (`active_modules` 1..5, `spares` 0..5, `replacement_threshold` 1..4) are supported only at the low end (1 module, "five or fewer" spares, K = 1); the upper bounds are placeholders.

absorbed 1, new values 8, new families 5 (from 19 proposals), rejected 2
