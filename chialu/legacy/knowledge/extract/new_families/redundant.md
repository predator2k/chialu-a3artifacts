# new-family review: redundant

Source bundle: `run/extract/reduce/newfam_redundant.md` (18 proposals). Registry read:
`chialu/spaces/redundant_spaces.py` plus the family lists of `adder_spaces.py`,
`mul_spaces.py`, `div_spaces.py`, `sfu_spaces.py` and `checker_spaces.py`. Notes consulted:
`notes/noll_1991.md` (the modulo multiplier), `notes/saporito_2020.md` (the ECC unit),
`notes/jenkins_leon_1977.md` (the correction adder and encoder), `notes/irwin_owens_1987.md`
(the min/max primitive), `notes/piestrak_1994.md` (residue generator and MOMA),
`notes/chang_2015.md`, `notes/jullien_1978.md`, `notes/kawamura_2000.md` (forward
conversion), `notes/salamat_2018.md` (MAGIC NOR), `notes/muller_2016__s08.md` (differential
CORDIC), `notes/ercegovac_2004__s01.md` (composite online units). Variant docs read:
`arch/redundant/generalized_signed_digit/on_the_fly.md`,
`arch/redundant/rns_channel_arithmetic/csa_with_periodic_folding.md`,
`arch/redundant/rns_dnn_accelerator/approximate_in_rns.md`,
`arch/sfu/redundant_high_radix_cordic.md`.

Handle notes for the human:
* `ercegovac_1987` is the on-the-fly conversion paper in the bundle. `div_spaces.py` cites
  `ercegovac_1987` on `digit_recurrence_sqrt_combined`, whose `on_the_fly_conversion` choice
  makes that the same paper, but nothing confirms it; `redundant_spaces.py` does not cite the
  handle, only the `generalized_signed_digit` docs do.
* `ercegovac_1992` and `saporito_2020` are cited by no space file today; `watson_hastings_1966`
  is cited only by `checker_spaces.py`; `muller_2016` and `dawid_1996` only by `sfu_spaces.py`.
* `piestrak_1994` has note status `mismatch`: the document header says 1991 with an unknown
  venue, and the bundle's citation says IEEE TC 1994. The bundle handle is kept below.
* Chapter handles (`muller_2016#s08`, `ercegovac_2004#s01`) are kept as given in prose; the
  `papers=` tuple in the snippet uses base keys, which is the style of `redundant_spaces.py`.
* The bundle's `carry_save_modulo_multiplier` and `periodic_eac_multioperand_modular_adder`
  come from papers already cited by the families that receive their values (`noll_1991` on
  `carry_save_datapath`, `piestrak_1994` on `rns_channel_arithmetic`).

## absorbed

* on_the_fly_redundant_conversion -> generalized_signed_digit.final_conversion=on_the_fly — the variant doc describes exactly the two conditional forms Q[k] and QM[k] = Q[k] - r^-k, the select-append-load step with no carry propagation and the two-logic-level step cost, and cites `ercegovac_1987`; the same mechanism is `div_spaces.digit_recurrence_sqrt_combined.on_the_fly_conversion=True`, `redundant_binary_multiplier.rbnb_converter=on_the_fly` and the `append_on_the_fly_conversion` mutation of `redundant_cordic`. The proposal's `input_radix` is the family's `radix` choice [ercegovac_1987].

## new values

* rns_channel_arithmetic.multiplier_reduction += iterative_carry_save_msd_estimate — sequential partial-product modulo additions keep the partial remainder in carry-save form, 4 or 5 leading digits estimate the remainder and select the modulus multiple, so the per-iteration carry chain is the inspected prefix rather than the word (30 MHz worst case independent of word length, 0.05 mm²/bit in 1.5 um CMOS); the final carry propagation after the last iteration overlaps the next operation. `mul_spaces.sequential_shift_add` with `accumulator_form=carry_save` is the other possible host, and a `carry_save_modular_multiplier` family is the alternative; by the prefer-new-values rule the value is proposed [noll_1991]  (from carry_save_modulo_multiplier)
* rns_channel_arithmetic += choice remainder_estimate_digits: Int[4..5:1] — leading carry-save digits inspected by the iterative reduction above. The proposal's `iteration_mapping` {serial_reuse, unrolled_pipeline} is the existing `retime_tree_into_pipeline` mutation of `carry_save_datapath`, and its `overflow_correction` is the note's sign-position full adder that corrects carry overflow, which the note lists as a `carry_save_datapath` gap (`+= choice carry_overflow_correction: Bool`, one paper) [noll_1991]
* redundant_cordic.scale_factor_fix += differential — the same ±1 directions as conventional CORDIC are recovered by propagating absolute residuals: each stage subtracts its stored elementary angle in radix-2 signed-digit arithmetic without carry propagation, derives the next absolute residual and reads the direction from its sign, so the constant scale factor survives with no zero digit, at an online delay of 1 digit time per stage and an initial sign delay of up to the word length; the digit-pipelined form ends in an on-the-fly conversion (`append_on_the_fly_conversion`), and the hyperbolic extension is direct [muller_2016#s08]  (from differential_cordic)
* sfu_spaces.redundant_high_radix_cordic.scale_handling += differential — the same value for the sfu twin: `dawid_1996` is already a family paper there and the family doc describes the differential form in prose (3.5N+1 full-adder delays with N stages), but neither enum carries it [muller_2016#s08]
* adder_spaces.end_around_carry.modulus += generic_p_correction — an L-bit two's-complement adder followed by logic that detects forbidden output states or overflow and adds the fixed constant C_L = 2^L - p, which the paper calls a generalized end-around carry hard-wired with the adder. `end_around_carry` sits in `cpa_space`, so the value gives `rns_channel_arithmetic.modulus_form=generic`, whose doc already names "a general modular correction", a member in its `modular_adder` slot. Evidence is one paper with no results table [jenkins_leon_1977]  (from generalized_modular_correction_adder)
* generalized_signed_digit += choice negation: {transfer_free, two_valued_transfer} — unary sign change on an asymmetric digit set as a borrow-free position-wise step: transfer t(i+1) and interim v(i) = -y(i) + r t(i+1), then n(i) = v(i) - t(i); the transfer disappears exactly when alpha = beta mod (r-1) and otherwise two transfer values selected by a comparison constant suffice. The value follows from the digit set, so the registry may record it as a constraint on `radix`/`redundancy` rather than a free choice [parhami_1993]  (from gsd_negation)
* generalized_signed_digit += choice overflow_detection: {outgoing_transfer_only, real_overflow_scan} — a nonzero outgoing transfer is only apparent overflow; a right-to-left scan (Algorithm 10) decides whether a k-digit representation still exists [parhami_1993]  (from gsd_overflow_handling)
* generalized_signed_digit += choice overflow_recovery: {guard_digit, software_exception, correction_scan} — the non-real-overflow result is rewritten into k digits by a correction scan whose transfer magnitude is bounded by 1 + floor((rho-1)/r) and which may stop as soon as its transfer becomes zero, or the hardware keeps a guard digit, or defers to software [parhami_1993]  (from gsd_overflow_handling)
* generalized_signed_digit += choice zero_sign_scan: {sequential, transfer_skip, transfer_lookahead} — zero detection scans right to left propagating a transfer and a divisibility flag, sign detection a positive/zero/negative state, and Algorithm 9 combines both in one three-valued state; transfer-skip and transfer-lookahead accelerate the scan as carry-skip and carry-lookahead do. The family doc's "sign, zero and overflow tests need separate scans" gets its choice. A `gsd_support_functions` family merging this line with the negation and overflow lines is the alternative; by the prefer-new-values rule the choices are proposed [parhami_1993]  (from gsd_zero_sign_detection)
* rns_scaling_comparison.method += macrocoefficient_k_k_minus_1 — for a four-modulus K, K-1 set with m1*m2 = m3*m4 + 1, paired macrocoefficients (the gamma/delta or the beta/epsilon route) are extracted by two-residue and four-residue base extension from fixed memories, with specialized multipliers as the slower realization, and serve base extension, chopped scaling, sign/magnitude comparison and mixed-radix conversion [watson_hastings_1966]  (from macrocoefficient_residue_interaction)
* rns_scaling_comparison.operation += fractional_multiply, iterative_divide_sqrt — the same macrocoefficients drive fractional multiplication and an iterated multiply/halve/compare division and square root that finishes in [log2 M]+1 or fewer iterations [watson_hastings_1966]
* rns_dnn_accelerator += choice computation_substrate: {cmos_logic, memristor_magic_nor} — rows of a memristor array hold operands, intermediates and results, wordline voltages execute column-parallel MAGIC NOR steps, a full adder takes four NOR steps for the carry and three NOT plus five NOR for the sum, so an N-bit add costs 12N+1 cycles and a modulo 2^t-1 or 2^t channel add 2(12t+1) cycles (2(12t+13) for 2^t+1), against the CMOS row-stationary accelerator of `samimi_2020`. The proposal's `pipeline_partition` (RNS add, square table, carry-save accumulator) is the family mechanism already, and the family doc already contrasts "the in-memory design" with the CMOS one in prose; the NOR-step counts are circuit-level and belong in the doc. Rejecting the substrate as a circuit trick is the alternative reading [salamat_2018]  (from magic_nor_in_memory_arithmetic)
* generalized_signed_digit += choice otf_rounding_sign_source: {exact_remainder_sign, none, estimated_b_msb} — the on_the_fly variant already keeps the third form QP[k] and selects among Q, QM and QP for rounding, so the three-form mechanism is absorbed; the new axis is where the selection reads the remainder sign: the exact sign and zero test (Method 1, error (1/2)r^-n, IEEE round to nearest, jam to even on ties), no remainder inspection (Method 2, selection from p(n+1) alone, unbiased error bounded by ±2^-n at radix 2), or a sign estimate from the b most significant remainder bits (Method 3, bound r^-n(2^-1 + 2^-b), under 1% error difference and one short cycle instead of about four for b = 8, with an imprecise flag). The exact sign detector (existing CPA, carry-skip or carry-lookahead network) is a `cpa_space` slot filler [ercegovac_1992]  (from on_the_fly_rounding)
* online_arithmetic_unit.digit_set += overredundant — a composite unit may emit a digit set wider than maximally redundant (digits 0 through 8 from the sum-of-three-squares unit) that the successor recurrence accepts directly [ercegovac_2004#s01]  (from online_composite_multioperation)
* online_arithmetic_unit += choice merged_operations: {single, sum_of_squares, multiply_add, normalization} — several dependent operations are derived into one residual recurrence sharing the carry-save reduction and appending hardware, instead of composed as separate modules: sum of three squares at online delay 0 against 7 cycles for three multipliers and two adders, and composite sum-of-squares plus square root (3-D vector magnitude) at delay 5 against 11. An `online_composite_unit` family is the alternative; by the prefer-new-values rule the choices are proposed, and `online_pipeline_composition` keeps the module-level composition [ercegovac_2004#s01]
* online_arithmetic_unit += choice residual_reduction: {3_2, 4_2, 5_2} — the compressor of the residual recurrence, [5:2] for the three-square composite; `carry_save_datapath.compressor` has no 5_2 value and the online family's `residual_form=carry_save` names no width [ercegovac_2004#s01]
* adder_spaces.prefix_comparator.structure += msdf_signed_digit_fsm — a five-state finite-state machine consumes aligned signed digits most-significant first, keeps enough ordering state for redundant representations, and emits with latency 1 digit a numerically equivalent digit stream for the smaller (or, in the dual machine, the larger) operand, 350 lambda by 350 lambda in double-metal CMOS; the sibling of the existing `msb_first_prefix` scan for digit-serial redundant inputs. A free-form member of `online_space` (`free_form_allowed=True`) is the alternative; by the prefer-new-values rule the value is proposed [irwin_owens_1987]  (from online_signed_digit_comparator)
* adder_spaces.prefix_comparator.function += min_max_select — the output is the selected operand's digit stream rather than an ordering flag [irwin_owens_1987]
* rns_channel_arithmetic += choice multioperand_adder: {none, periodic_csa_tree, periodic_csa_register} — k residue operands modulo an odd A are partitioned into equal binary-weight columns, full-adder carry-save stages reduce the k*a bits with carries wrapping after q = min(P(A), m) positions, where P(A) is the period of 2^j mod A and m encodes the largest unreduced operand sum, and a cyclic adder reduces the rest; the tree form is combinational (8-operand mod 25: 32 FAs + 2 HAs, 7 delta + d(ROM)) and the register form reuses one CSA stage with a carry-save register (7 FAs + 14-bit register, 11 delta + d(ROM)). The same engine over the bit columns of one binary word is the residue generator, which the new `rns_forward_converter` family below carries as `implementation=periodic_csa_moma`; merging this proposal into that family with an operand-source choice is the alternative [piestrak_1994]  (from periodic_eac_multioperand_modular_adder)
* rns_channel_arithmetic += choice moma_final_converter: {rom, pla} — the remaining P(A)+1 or fewer weighted bits after the cyclic adder are mapped to the residue by a ROM (256 x 5 for 8 operands mod 25) or a PLA (5-input for 4 operands mod 5) [piestrak_1994]

## new families

One family from 4 proposals. The family is the missing symmetric partner of
`rns_reverse_converter`: the `jenkins_leon_1977` and `chang_2015` notes both list the
absent forward-converter slot on `rns_dsp_datapath`/`rns_dnn_accelerator`/
`rns_montgomery_crypto` as a space gap, and `rns_dnn_accelerator`'s doc already says
activations are "forward-converted once" with no family behind the phrase.

### rns_forward_converter

Merged from: binary_to_rns_converter (jullien_1978), rns_forward_encoder
(jenkins_leon_1977), rns_forward_converter (chang_2015), radix_to_rns_converter
(kawamura_2000). All four describe binary-to-residue conversion computed channel by
channel; they differ only in what evaluates the 2^j mod m contributions and how the
contributions are summed. The `piestrak_1994` residue generator (the note's `residue`
block: periodic end-around carry-save tree with a ROM/PLA final converter, 32-bit
generator mod 9 in 25 FAs + 1 HA, 9 delta, 128 x 4 ROM) is the memoryless member and is
cited as supporting evidence; its multioperand adder stays under new values.

* domain: redundant (`rns_space`, beside `rns_reverse_converter`)
* doc: "binary or radix-2^r word to residues, channel by channel: chunk tables of 2^j mod m summed by modular adders, a periodic end-around carry-save tree for memoryless channels, or the channel MACs of a crypto datapath in n steps; the entry tax paired with rns_reverse_converter"
* execution_style: feed_forward (default, omitted in the snippet as `rns_reverse_converter` does; the `channel_modular_mac` value runs n steps on n Rowers, which `rns_reverse_converter` also absorbs for the Cox-Rower reverse conversion)
* mechanism: Each residue is computed independently. A chunk of input bits addresses a table of its residue contribution, one 8K ROM per modulus converting a 10-bit word in one lookup cycle, and a wider word is split into chunks whose contributions are summed by modular adders (20 bits in two equal parts: 3N ROMs, two lookup cycles). Bitwise tables of 2^j mod p_i feed modular adders; segmenting the input bits across several ROMs stores partial sums and reduces the encoder to one modular addition per residue at more ROM (t = 7, two 4-bit segments: 2L ROMs of 16 words). A memoryless channel partitions the bits into P(A) weight classes, reduces them in a carry-save tree whose carries wrap after P(A) positions, and finishes in a cyclic adder plus ROM/PLA, avoiding exponential ROM growth. A crypto datapath computes x[m_i] = sum_j x(j) * (2^rj mod m_i) with precomputed constants on its n parallel Rower multiplier-accumulators in n steps (n² modular multiplications). For two's-complement input the chunk holding the sign bit is treated as signed.
* choices (each with the proposals that give evidence):
  * `implementation: {rom_per_chunk, segmented_rom_modular_add, periodic_csa_moma, channel_modular_mac}` [jullien_1978 single ROM; jenkins_leon_1977 bitwise tables and segmented ROMs; chang_2015 rom/memoryless_moma/carry_save; piestrak_1994; kawamura_2000]
  * `chunk_bits: Int[1..64:1]` — 1 is bitwise; 4 (jenkins_leon_1977), 10 and 20 (jullien_1978), the radix digit width r (kawamura_2000, `radix_digit_width_bits` Int[1..64:1])
  * `modulus_class: {generic, pow2_plus_minus_k, pow2}` [chang_2015 arbitrary/restricted 2^n ± k/special power of two; piestrak_1994 arbitrary odd A]
  * `moduli_count: Int[3..64:1]` [jenkins_leon_1977 five moduli; kawamura_2000 `residue_channels` Int[1..64:1], 33 channels; lower bound matched to `rns_reverse_converter.moduli_count`]
  * `signed_input: Bool` [jullien_1978]
  * `final_reduction: {modular_adder, rom, pla}` [jenkins_leon_1977 modular adders; piestrak_1994 ROM/PLA]
  * `chang_2015`'s `moduli_selection: {fixed, heuristic_range_driven}` is a system-level moduli-set decision, so it becomes the `co_select_moduli_set_with_converter` mutation that `rns_reverse_converter` already has rather than a choice.
* slots: `modular_adder: cpa_space` (with `end_around_carry` for 2^n ± 1 and, after the new value above, `generic_p_correction` for generic moduli), `column_reducer: adder_tree_space` (`csa_tree` for the periodic tree; `adder_tree_space` comes from `chialu.spaces.arith_spaces`, an added import)
* mutations: split_word_into_chunks, segment_rom_into_partial_sums, replace_rom_with_periodic_csa, fold_csa_tree_into_register_stage, reuse_channel_mac_for_conversion, co_select_moduli_set_with_converter
* handles: jullien_1978, jenkins_leon_1977, chang_2015, kawamura_2000, piestrak_1994
* evidence: 4 proposals from 4 papers; 3 landmark (jullien_1978, jenkins_leon_1977, kawamura_2000), 1 survey (chang_2015), plus 1 incremental supporting block (piestrak_1994); no textbook or thesis block. Quantified results: jullien_1978 one lookup cycle for 10 bits, two for 20 bits split; jenkins_leon_1977 one modular addition per residue with 2L 16-word ROMs; kawamura_2000 n steps on n Rowers; piestrak_1994 9 delta for a 32-bit generator mod 9.
* thin choices (one paper each, droppable): `signed_input`, `final_reduction`.

```python
        Architecture(
            "rns_forward_converter",
            papers=("jenkins_leon_1977", "jullien_1978", "piestrak_1994",
                    "kawamura_2000", "chang_2015"),
            design_choices={
                "implementation": EnumChoice(("rom_per_chunk",
                                              "segmented_rom_modular_add",
                                              "periodic_csa_moma",
                                              "channel_modular_mac")),
                "chunk_bits": IntRange(1, 64),
                "modulus_class": EnumChoice(("generic", "pow2_plus_minus_k",
                                             "pow2")),
                "moduli_count": IntRange(3, 64),
                "signed_input": BoolChoice(),
                "final_reduction": EnumChoice(("modular_adder", "rom",
                                               "pla"))},
            components={"modular_adder": cpa_space(),
                        "column_reducer": adder_tree_space()},
            mutations=("split_word_into_chunks",
                       "segment_rom_into_partial_sums",
                       "replace_rom_with_periodic_csa",
                       "fold_csa_tree_into_register_stage",
                       "reuse_channel_mac_for_conversion",
                       "co_select_moduli_set_with_converter"),
            doc="binary or radix-2^r word to residues, channel by "
                "channel: chunk tables of 2^j mod m summed by modular "
                "adders, a periodic end-around carry-save tree for "
                "memoryless channels, or the channel MACs of a crypto "
                "datapath in n steps; the entry tax paired with "
                "rns_reverse_converter"),
```

The import line of `redundant_spaces.py` becomes
`from chialu.spaces.arith_spaces import adder_tree_space, cpa_space`.

## rejected

* ecc_modulo_arithmetic_engine — an execution-unit and firmware-ISA description (16 registers of 521 bits, 64-bit cache transfers, non-speculative issue, firmware-selected P256/P384/P521/X255-19/X448 or custom moduli) with no arithmetic datapath structure; the note's own open question records that the paper does not disclose the modulo-multiply reduction algorithm, so nothing distinguishes it from a register file in front of an unspecified modular multiplier [saporito_2020].

absorbed 1, new values 12, new families 1 (from 4 proposals), rejected 1
