# new-family review: sfu

Source: `run/extract/reduce/newfam_sfu.md` (27 proposals). Vocabulary checked
against `chialu/spaces/sfu_spaces.py` (families of `sfu_approx_space`, the
`range_reduction_space`, `poly_datapath_space` and `segment_space` slots, the
`SHARINGS` choice), the neighbouring domains (`div_spaces.py`, `fp_spaces.py`,
`redundant_spaces.py`, `dsp_posit_spaces.py`, `approx_spaces.py`) and the sfu
gap files under `knowledge/extract/gaps/`. Nothing in `chialu/spaces` changes
here; every line below is an instruction to the human who applies it.

Two bundle facts affect the reading:
* The bundle's "existing families" list omits `multipartite`, `newton_raphson`
  and `goldschmidt`, which `sfu_spaces.py` does define. The space file is taken
  as authoritative, so those three count as existing.
* The note for `detrey_2007` records `status: mismatch`: its cited title is the
  log/exp paper, but the extracted content (pp.29-34, the Virtex-II Table 1) is
  the FPL 2007 trigonometric paper that `detrey_2007b` also covers. The two
  proposals `dual_sine_cosine (detrey_2007)` and
  `shared_dual_trigonometric (detrey_2007b)` therefore describe one paper.
  Handles are kept as given.

## absorbed

* `bit_merge_linear (delgado_frias_2000b) -> sigmoid_tanh_pwl.approximation=bit_level_mapping` — Scheme-3 shifts the input by the power-of-two slope and merges the non-overlapping constant by per-bit set/reset/invert from a segment table, which is a direct Boolean mapping of shifted input bits with no adder (delgado_frias_2000b is in `papers`; its Scheme-2 is `shift_add_powers_of_two`); a value `shift_bit_merge` is the alternative if the shift-then-merge form must be searchable apart from the truth-table mapping.
* `coarse_fine_cordic (meher_2009) -> redundant_high_radix_cordic.coarse_fine_hybrid=True` — coarse rotations by ROM lookup plus add or by shift-add, then fine rotations whose directions are explicit in the radix-2 angle, is that Boolean plus mutation `split_coarse_table_fine_rotation` (meher_2009 is cited under `cordic`); the coarse implementation (`rom_lookup_add` versus `shift_add`) is not exposed and stays a doc detail.
* `composite_log_multiply_exp_power_root (vazquez_2013) -> digit_recurrence_exp_log` (mutation `compose_log_then_exp_for_powering`) — the family doc narrates the overlapped log, left-to-right multiply and exp datapath with its 100 tau / 5964 FA figures, and vazquez_2013 is in `papers`; the borrow-save overlap is `digit_set=signed_redundant`, and root extraction through the reciprocal prescale plus the LRCF multiplier slot are already listed in `gaps/digit_recurrence_exp_log.md` (`operation_set: qth_root`, `stage_composition: overlapped_log_lrcf_exp`).
* `dual_sine_cosine (detrey_2007) -> lut_plus_poly.sharing=shared_range_reduction` (the `multi_fn` choice) — one argument reducer feeds two HOTBM evaluators, then octant/sign reconstruction and exception handling; detrey_2007 is in `lut_plus_poly.papers`. The input-scaling and dual-path sub-choices become the two `range_reduction` lines below; fixed-point output and embedded-multiplier mapping are FPGA target options the registry does not model.
* `shared_dual_trigonometric (detrey_2007b) -> lut_plus_poly.sharing=shared_range_reduction` — the same paper and datapath as the previous line (803 slices / 69 ns at (5,10) dual sin/cos, 18-stage fp32 pipeline at 100 MHz).
* `shared_sincos (muller_2016#s13) -> sfu_approx_space.sharing in {shared_range_reduction, shared_evaluator}` — `shared_stage=range_reduction` is `shared_range_reduction`, and `reduced_argument_evaluation` or `both` is `shared_evaluator`; the HP-UX Itanium instance is a software library rather than a unit.

## new values

* `digit_recurrence_exp_log += choice termination: {iterate_to_full_precision, linear_extrapolation}` — Chen's cotransformation stops once the residual mu is small and finishes with an add and an abbreviated multiply, so ratio costs T (one conventional multiply time) and inverse square root 1.25T; the family doc already narrates this and chen_1972 is in `papers`, so absorbed is defensible, and `gaps/digit_recurrence_exp_log.md` lists the same as `termination_method: linear_extrapolation` [chen_1972]
* `digit_recurrence_exp_log += choice index_advance: {sequential, leading_bit_skip}` — the iteration index m jumps to the leading significant bit of |x - x_w| (leading-zero or leading-one detection by direction) instead of advancing by one, giving N/4 expected iterations (6.2 for N=24 ratio, 6.5 for inverse square root) and an N/2-word table for exp/log; under this value the family runs variable-iteration; the ratio and inverse-square-root uses of the same apparatus (no y-table update) have no div-domain home, which the human decides [chen_1972]
* `digit_recurrence_exp_log += choice state_domain: {real, complex_bkm}` — BKM: E_{n+1} = E_n (1 + d_n 2^-n) and L_{n+1} = L_n - ln(1 + d_n 2^-n) on complex states with the nine-value digit alphabet {0, +-1, +-i, +-1+-i}, so multiplying by d_n is a few additions; E-mode drives L to zero (exp; sin/cos from L_1 = i theta at +-2^-n), L-mode drives E to one (log on [0.5, 1.3]); real and imaginary digits are selected independently from 3-4 fractional residual bits and no scale factor arises; the source also states radix 10 and high-radix generalizations; bajard_1994 is in `papers`, the doc names BKM, and `gaps/digit_recurrence_exp_log.md` lists the same axis as `arithmetic_domain: complex` with `operation_mode` [muller_2016#s09]
* `redundant_high_radix_cordic.scale_handling += differential_constant_scale` — DCORDIC: temporary variables whose signs differentially encode the CORDIC variables, so redundant online arithmetic emits most-significant digits first and successive stages overlap with a one-digit skew, in rotation and vectoring, at the accuracy and convergence of conventional CORDIC; the family already cites dawid_1996 (its defining paper) and `gaps/redundant_high_radix_cordic.md` lists this value and a `mode` choice from it; the proposal names `redundant_cordic` (redundant domain) as closest, which is the alternative home [meher_2009]
* `sigmoid_tanh_pwl.approximation += step_sum` — a hidden-layer sigmoid becomes a comparator-selected sum of h steps whose subdivision points minimize the square-integral norm and are rounded to powers of two with little norm change, so weighted inputs need shifts rather than multipliers; an output-layer unit collapses to one threshold step after learning; alippi_1991 is in `papers` for its piecewise-linear integer-grid form, which is `shift_add_powers_of_two` [alippi_1991]
* `softmax_layernorm.exp_evaluation += group_lookup_table` — x = x1 + x2 + x3 and exp(x) = exp(x1) exp(x2) exp(x3), each component addressing a table grouped in 4-bit units, 25-bit fraction with all three tables, zero to two multipliers; about 5 correct decimals against 2-3 for the fixed two-multiplier baseline on Virtex-5; du_2019 is in `papers` and `gaps/softmax_layernorm.md` lists the same value [du_2019]
* `softmax_layernorm += choice lut_group_gating: {fixed, input_proximity}` — enable signals activate zero to three of the group tables sequentially by the input's proximity, trading multiplier and table activity against accuracy [du_2019]
* `newton_raphson += choice termination: {fixed_steps, monotone_non_decrease}` (the sfu family) — the Heron form x_{i+1} = floor((x_i + floor(n / x_i)) / 2) from x_0 = 2^ceil(bits/2) stops when x_{i+1} >= x_i and returns floor(sqrt(n)) exactly, at most four iterations for any INT32; each step is one integer divide, one add and one shift, so the step needs a divider rather than the multiply-only reciprocal form, and execution becomes variable-iteration; kim_2021 is cited under `transformer_activation_lut`, and `gaps/softmax_layernorm.md` lists the same as `layernorm_sqrt: integer_newton_recurrence` [kim_2021]
* `div.seed_table_space += magic_constant_bit_seed` (the `seed` slot of `newton_raphson`/`goldschmidt`) — the positive float is reinterpreted as integer I_x and I_y0 = R - floor(I_x / 2) with a format-specific constant R reinterprets to a piecewise-linear inverse-square-root seed with no table; R is chosen by zeroth-error minimax, correction-aware minimax or floating-point experiment (0x5F200000 versus experimental 0x5F200011 for fp32), subnormals are scaled into the normal range first; 0.65017e-3 maximum relative error after one modified correction against 1.75124e-3 for the original seed plus standard correction; `gaps/newton_raphson.md` line 8 names this seed value [walczyk_2021]. Paste into `seed_table_space` (the `common` table widths do not apply; only `function=recip_sqrt` does):

```python
        Architecture("magic_constant_bit_seed", papers=("walczyk_2021",),
                     design_choices={
                         "function": EnumChoice(("recip_sqrt",)),
                         "floating_format": EnumChoice(("fp32", "fp64",
                                                        "fp128")),
                         "magic_constant_selection": EnumChoice(
                             ("zeroth_error_minimax",
                              "correction_aware_minimax",
                              "floating_point_experimental")),
                         "subnormal_handling": EnumChoice(
                             ("normal_only", "scale_to_normal"))},
                     mutations=("retune_magic_constant_for_correction",
                                "add_subnormal_prescale"),
                     doc="I_y0 = R - (I_x >> 1) on the reinterpreted "
                         "float: a table-free piecewise-linear rsqrt "
                         "seed; R minimax-tuned per format"),
```

* `poly_datapath_space += coefficient_adapted` (the `evaluator` slot of `single_poly`, `piecewise_poly`, `lut_plus_poly`, `mixed_degree`) — the polynomial is transformed once into parameters c, alpha_i and beta_i and evaluated as y = x + c, w = y^2, then a nested sequence of (w - alpha_i) factors, at most ceil(n/2) + 2 multiplications and n additions for degree n (6 against Horner's 8 at degree 8), paid by solving nonlinear coefficient equations offline; a rearranged feed-forward evaluator beside `horner`/`estrin`/`factored`, so a slot value rather than a family [muller_2016#s04]. Paste into `poly_datapath_space`:

```python
        Architecture("coefficient_adapted",
                     papers=("muller_2016",),
                     doc="coefficients pre-transformed to c, alpha_i, "
                         "beta_i: y = x + c, w = y^2, nested (w - alpha_i) "
                         "factors; ceil(n/2)+2 multiplies for degree n "
                         "(6 vs Horner's 8 at degree 8)"),
```

* `SHARINGS += microcoded_fpu_sequence` (the `sharing` choice of every `sfu_approx_space` family under `multi_fn`) — a transcendental instruction is a RISC instruction sequence stored in a code ROM and dispatched, up to four operations at a time and completing out of order, onto the existing pipelined floating-point unit; multiprecision values span several of fifteen 41-bit registers scheduled by a compiler; maximum error below 1 ulp on the K5; the sharing level beyond `fully_shared_rom_evaluator` (no dedicated datapath at all); `gaps/lut_plus_poly.md` already lists the K5's degree-9 Taylor form and on-the-fly coefficient generation from this handle [lynch_1995]
* `range_reduction += choice argument_scaling: {radian, pi_scaled}` — sin(pi x)/cos(pi x) variants split x into integer and fractional parts with no multiplication by 2/pi (363 against 803 slices at (5,10) dual sin/cos on Virtex-II); derived from the absorbed dual sin/cos proposals [detrey_2007, detrey_2007b]
* `range_reduction += choice path_structure: {single, dual_close_far}` — a close path derives fixed-point Y from floating-point (Ey, My) for x < 1/2, while a far path derives (Ey, My) from Y through an LZC and a shifter; `gaps/range_reduction.md` line 12 lists this value from both handles; derived from the absorbed `shared_dual_trigonometric` proposal [detrey_2007b]

The nine proposals in this section are chen_1972, muller_2016#s09 (BKM),
meher_2009 (differential CORDIC), alippi_1991, du_2019, kim_2021,
walczyk_2021, muller_2016#s04 (coefficient adaptation) and lynch_1995. The two
`range_reduction` lines carry no proposal of their own. The two sub-space
candidates (`magic_constant_bit_seed`, `coefficient_adapted`) sit here rather
than under new families because a slot's candidate list behaves as one
choice and the rules prefer new values when the call is close.

## new families

### add_table_add

Merged proposals: `add_table_lookup_add` (wong_1995), `addition_table_addition`
(dedinechin_2005). The literature's name is ATA (Add-Table lookup-Add in
wong_1995; Addition-Table-Addition in dedinechin_2005), and
`gaps/lut_plus_poly.md` line 17 asks for this family under the alias
`add_table_lookup_add`.

* name: `add_table_add`
* domain: sfu (a table family of `sfu_approx_space`, beside `bipartite`, `stam` and `multipartite`)
* doc: `ATA: adders before and after the lookup; X splits into A and B, banks read f(A), f(A+B), f(A-B) in parallel and a central-difference combination of the readouts gives the value with no coefficient multiplier; parallel banks buy the shortest post-lookup path (22 tau, 1.57 multiply times) at 868 Kbit per function, one reused table costs 5x the time at 16 Kbit`
* execution_style: feed_forward (default of `_f`)
* gap it closes: `bipartite`/`stam`/`multipartite` decompose into parallel offset tables added after the lookup; no family adds before the lookup or combines the readouts as differences, which dedinechin_2005 states is why ATA is not a multipartite method.
* design choices:
  * `truncation_order: IntRange(1, 4)` — first order looks up f(A) and f(A+B) and adds a shifted difference to f(A) (two lookups); second order looks up f(A), f(A+B), f(A-B) and applies centered-difference formulas (three lookups, seven additions); wong_1995's O(h^5) truncated-Taylor expression rewritten as central differences is the top of the range, and the proposal does not state its order, so the human fixes the upper bound [dedinechin_2005, wong_1995]
  * `table_bank_count: IntRange(2, 6)` — two, three, or the six parallel banks of wong_1995 [wong_1995, dedinechin_2005]
  * `input_chunk_bits: IntRange(4, 8)` — wong_1995 fixes 6; the range is the reviewer's [wong_1995]
  * `table_access: EnumChoice(("parallel_banks", "dual_port", "sequential_reuse"))` — parallel banks, dual-port tables, or one table read sequentially (about 16 Kbit, 5x slower than six-bank ATA) [dedinechin_2005]
  * `final_reduction: EnumChoice(("adder_chain", "multioperand_tree"))` — subtract/shift/add chain for first order, or a Wallace-tree multioperand adder over the six fixed-point readouts [wong_1995, dedinechin_2005]
  * `offset_partitioning: EnumChoice(("none", "split_subwords"))` [dedinechin_2005]
  * `symmetry: BoolChoice()` [dedinechin_2005]
* component slots:
  * `range_reducer: range_reduction_space()` — each function is applied after restricting or transforming the operand into the table range; full-range sine/cosine need pi to well over 100 bits [wong_1995]
  * `address_adder: cpa_space()` — the parallel adders that form A+B and A-B (carry-lookahead in wong_1995's schematic, topology unstated)
  * `final_adder: adder_tree_space()` — `csa_tree` is the Wallace multioperand form; both slots import from `chialu.spaces.arith_spaces`, which `sfu_spaces.py` does not yet import
* mutations: `raise_truncation_order`, `lower_truncation_order`, `serialize_table_access`, `parallelize_table_banks`, `split_offset_subwords`, `fold_symmetry`, `replace_adder_chain_with_multioperand_tree`, `drop_pre_lookup_adders` (crosses to `multipartite`)
* handles: wong_1995 [incremental], dedinechin_2005 [landmark]
* evidence strength: 2 proposals, 2 papers (1 landmark), no textbook block; wong_1995 gives estimated (not fabricated) figures: 16 tau logic plus 6 tau lookup, 1.6 multiply times for reciprocal and square root, 3.5 for arc tangent, 868 352 bits per function and about 14.2 Mbit for seven, about 3000 gates; maximum absolute error at most 0.5 ulp (2^-24) over restricted ranges by exhaustive 24-bit check, explicitly without a correct-rounding guarantee; dedinechin_2005 supplies the order-1/order-2 operation counts and the sequential 16 Kbit variant.
* snippet (insert after `multipartite` in `sfu_approx_space`; add `from chialu.spaces.arith_spaces import adder_tree_space, cpa_space` at the top):

```python
        _f("add_table_add",
           {"truncation_order": IntRange(1, 4),
            "table_bank_count": IntRange(2, 6),
            "input_chunk_bits": IntRange(4, 8),
            "table_access": EnumChoice(("parallel_banks", "dual_port",
                                        "sequential_reuse")),
            "final_reduction": EnumChoice(("adder_chain",
                                           "multioperand_tree")),
            "offset_partitioning": EnumChoice(("none", "split_subwords")),
            "symmetry": BoolChoice()},
           components=dict(rr, address_adder=cpa_space(),
                           final_adder=adder_tree_space()),
           papers=("wong_1995", "dedinechin_2005"),
           doc="ATA: adders before and after the lookup; banks read "
               "f(A), f(A+B), f(A-B) in parallel and a central-difference "
               "combination gives the value with no coefficient "
               "multiplier; parallel banks buy 22 tau at 868 Kbit per "
               "function, one reused table costs 5x at 16 Kbit",
           mutations=("raise_truncation_order", "lower_truncation_order",
                      "serialize_table_access", "parallelize_table_banks",
                      "split_offset_subwords", "fold_symmetry",
                      "replace_adder_chain_with_multioperand_tree",
                      "drop_pre_lookup_adders")),
```

* human decisions: (1) the upper bound of `truncation_order`; (2) the seven-function set of wong_1995 is served by per-function table sets, which the `multi_fn` `sharing` choice covers, so no `function_set` choice is added; (3) `gaps/multipartite.md` line 9 proposes `approximation_order: {1, 2}` on `multipartite` from muller_1999, which is a different (post-lookup) order axis and must not be conflated with this family's.

### table_factor_refinement

Merged proposals: `successive_table_reduction` (muller_2016#s05),
`table_residual_refinement_sfu` (wong_1994). The literature calls it the
Wong-Goto rectangular-multiplier method; the name here describes the
mechanism. `mul.md` absorbed the multiplier itself as
`lut_plus_poly.multiplier_shape=rectangular`; this family is the algorithm
around that multiplier.

* name: `table_factor_refinement`
* domain: sfu
* doc: `residual driven to 0 or 1 by 1-3 stages, each a table-selected short factor (8-11 bits) applied by a rectangular multiplier (16x56 at double, about half a full multiply time), then a short Taylor or table tail; log reuses the reciprocal's factors, exp multiplies tabulated exponentials of the argument's fields, atan2 and sin/cos rotate by tabulated complex factors; one unified rectangular-multiplier datapath serves six functions at 3.7-7.1 multiply times with 0.5 ulp proofs (Wong-Goto)`
* execution_style: feed_forward (the stages are a fixed unrolled sequence; the unified hardware of wong_1994 Fig. 8 time-shares them across functions, and the proposals do not say whether one function's stages are unrolled or looped, so the human confirms)
* gap it closes: `lut_plus_poly` selects coefficients for one local polynomial; `digit_recurrence_exp_log` normalizes multiplicatively over ln(1 +- 2^-i) constants at radix 2-16 with shift-add steps; nothing covers a 2-3 stage normalization by whole table-derived factors through rectangular multipliers with residual propagation and a Taylor tail, nor the division / reciprocal-square-root / atan2 / sine-cosine coverage of the same hardware.
* design choices:
  * `factor_bits: IntRange(8, 11)` — width of the extracted residual chunk and of the tabulated correction factor [wong_1994, muller_2016#s05]
  * `residual_stages: IntRange(1, 3)` — the K1/K2/K3 factor stages of the logarithm [muller_2016#s05]
  * `terminal_correction: EnumChoice(("truncated_taylor", "table_square"))` — the final residual treatment [wong_1994]
  * `tail_degree: IntRange(1, 4)` — degree of the terminal series [muller_2016#s05]
  * `multiplier_shape: EnumChoice(("rectangular", "full_square"))` — the same value names as `lut_plus_poly.multiplier_shape` [muller_2016#s05, wong_1994]
  * `rectangular_multiplier_count: IntRange(1, 2)` — peak specialized-multiplier need, function-dependent [wong_1994]
  * `function_set: EnumChoice(("division", "logarithm", "reciprocal_square_root", "exponential", "atan2", "sine_cosine"))` [wong_1994]
  * `unified_hardware: BoolChoice()` — one shared datapath for all functions [wong_1994]
* component slots:
  * `range_reducer: range_reduction_space()` — reduced argument in [0, pi/2) for sine/cosine, prespecified-base logarithm range
  * `tail_evaluator: poly_datapath_space()` — the truncated Taylor tail
* mutations: `add_refinement_stage`, `remove_refinement_stage`, `widen_factor_bits`, `narrow_factor_bits`, `replace_taylor_tail_with_table`, `share_reciprocal_factors_with_logarithm`, `unify_function_datapaths`, `narrow_rectangular_multiplier`, `collapse_to_single_stage` (crosses to `lut_plus_poly` with `multiplier_shape=rectangular`)
* handles: wong_1994 [landmark], muller_2016#s05 [textbook]
* evidence strength: 2 proposals, 1 landmark paper and 1 textbook block; wong_1994 gives analytical latencies in full-multiply units (division 3.68, logarithm 4.56, reciprocal square root 5.25, exponential 3.69, ATAN2 7.06, sine and cosine 6.5 or 5.5 for one), about 1 Mbit of tables for all functions, and 0.5 ulp proofs per function; muller_2016#s05 gives the 16x56 multiplier at slightly over half a full multiply time and a logarithm error within 1 ulp when the 56-bit intermediate is rounded to 53 bits.
* snippet (insert after `lut_plus_poly` in `sfu_approx_space`):

```python
        _f("table_factor_refinement",
           {"factor_bits": IntRange(8, 11),
            "residual_stages": IntRange(1, 3),
            "terminal_correction": EnumChoice(("truncated_taylor",
                                               "table_square")),
            "tail_degree": IntRange(1, 4),
            "multiplier_shape": EnumChoice(("rectangular", "full_square")),
            "rectangular_multiplier_count": IntRange(1, 2),
            "function_set": EnumChoice(("division", "logarithm",
                                        "reciprocal_square_root",
                                        "exponential", "atan2",
                                        "sine_cosine")),
            "unified_hardware": BoolChoice()},
           components=dict(rr, tail_evaluator=poly_datapath_space()),
           papers=("wong_1994", "muller_2016"),
           doc="residual driven to 0 or 1 by 1-3 stages of table-selected "
               "short factors through rectangular multipliers (16x56 at "
               "double), then a Taylor or table tail; one datapath serves "
               "six functions at 3.7-7.1 multiply times with 0.5 ulp "
               "proofs (Wong-Goto)",
           mutations=("add_refinement_stage", "remove_refinement_stage",
                      "widen_factor_bits", "narrow_factor_bits",
                      "replace_taylor_tail_with_table",
                      "share_reciprocal_factors_with_logarithm",
                      "unify_function_datapaths",
                      "narrow_rectangular_multiplier",
                      "collapse_to_single_stage")),
```

* human decisions: (1) the alternative is `digit_recurrence_exp_log.radix` extended to 256-2048 plus a `terminal_correction` choice (`gaps/digit_recurrence_exp_log.md` line 3 already proposes radices up to 1024 from other handles), which keeps one family but loses division, reciprocal square root, atan2 and sine/cosine and the rectangular-multiplier structure; the exp/log subset is close enough that this is a real fork; (2) `execution_style` for the unified hardware; (3) `function_set` overlaps the `multi_fn` `sharing` choice and `gpu_multifunction_interpolator.function_set`, so one convention should be picked.

### rational_approximation

Merged proposals: `rational_approximation` (muller_2016#s13),
`rational_approximation` (muller_2018#s10), `rational_function_approximation`
(muller_2016#s04). `gaps/single_poly.md` line 6 lists `symmetry_form` from
muller_2016#s13, which this family carries for the rational case.

* name: `rational_approximation`
* domain: sfu
* doc: `P(x)/Q(x) over the reduced domain, odd forms x P(x^2)/Q(x^2) where the function allows, one divide at the end; degree 5/5 beats a degree-25 polynomial for sqrt on [1/4, 1] and degree 3/4 beats degree 13 for tan at 8 against 14 operations, so it wins where a divider exists and the polynomial degree would explode; Cyrix FastMath evaluates flat nonzero R(x) in fixed point over up to five subintervals`
* execution_style: feed_forward (default of `_f`)
* gap it closes: `single_poly` and `piecewise_poly` have no denominator and no divider; the alternating-extrema construction, the equivalent-form sensitivity and the division cost have no home.
* design choices:
  * `numerator_degree: IntRange(1, 8)` — reported degrees 3 and 5; the bound mirrors `single_poly.degree` [muller_2016#s04, muller_2016#s13, muller_2018#s10]
  * `denominator_degree: IntRange(1, 8)` — reported degrees 4 and 5 [muller_2016#s04, muller_2016#s13, muller_2018#s10]
  * `symmetry_form: EnumChoice(("unrestricted", "odd"))` — g Q(g^2) or x P(x^2)/Q(x^2) halves the multiplications [muller_2016#s13]
  * `segments: IntRange(1, 8)` — arctangent uses five distinct rational approximations over five subintervals [muller_2016#s13]
  * `construction: EnumChoice(("minimax_remez", "pade", "orthogonal"))` [muller_2016#s04]
  * `objective_norm: EnumChoice(("absolute_minimax", "relative_minimax"))` [muller_2018#s10]
  * `expression_form: EnumChoice(("direct_fraction", "decomposed", "factored"))` — algebraically equivalent forms differ in finite-precision error (worst case 0.31e-14, 0.12e-14, 0.15e-14 over 500 000 points) [muller_2016#s04]
  * `evaluation_format: EnumChoice(("fixed_point", "floating_point"))` — flat, nonzero R(x) permits accurate fixed-point evaluation [muller_2016#s13]
* component slots:
  * `range_reducer: range_reduction_space()`
  * `numerator: poly_datapath_space()` and `denominator: poly_datapath_space()` — the two polynomials; `shared_multiplier` in either slot time-shares one multiplier
  * `divider: div_space()` — imported from `chialu.spaces.arith_spaces` as `fp_spaces.py` does; the division cost is the family's defining trade
  * `segmenter: segment_space()` — meaningful when `segments > 1`
* mutations: `raise_denominator_degree`, `lower_denominator_degree`, `move_degree_between_numerator_and_denominator`, `fold_odd_symmetry`, `split_domain_into_segments`, `refactor_expression_form`, `switch_construction`, `collapse_to_polynomial` (denominator degree 0 crosses to `single_poly`)
* handles: muller_2016#s13 [textbook], muller_2018#s10 [textbook], muller_2016#s04 [textbook]
* evidence strength: 3 proposals, 3 textbook blocks from 2 books, no paper in the bundle; the only hardware instance is Cyrix FastMath (muller_2016#s13) with no numbers; muller_2016#s04 gives the approximation-error and operation-count comparisons and the finite-precision spread across equivalent forms; muller_2018#s10 states the alternation result and no implementation.
* snippet (insert after `single_poly` in `sfu_approx_space`; add `div_space` to the `arith_spaces` import):

```python
        _f("rational_approximation",
           {"numerator_degree": IntRange(1, 8),
            "denominator_degree": IntRange(1, 8),
            "symmetry_form": EnumChoice(("unrestricted", "odd")),
            "segments": IntRange(1, 8),
            "construction": EnumChoice(("minimax_remez", "pade",
                                        "orthogonal")),
            "objective_norm": EnumChoice(("absolute_minimax",
                                          "relative_minimax")),
            "expression_form": EnumChoice(("direct_fraction", "decomposed",
                                           "factored")),
            "evaluation_format": EnumChoice(("fixed_point",
                                             "floating_point"))},
           components=dict(rr, numerator=poly_datapath_space(),
                           denominator=poly_datapath_space(),
                           divider=div_space(), segmenter=segment_space()),
           papers=("muller_2016", "muller_2018"),
           doc="P(x)/Q(x) over the reduced domain, odd forms where the "
               "function allows, one divide at the end; 5/5 beats a "
               "degree-25 polynomial for sqrt and 3/4 beats degree 13 for "
               "tan at 8 vs 14 operations (Cyrix FastMath in fixed point)",
           mutations=("raise_denominator_degree",
                      "lower_denominator_degree",
                      "move_degree_between_numerator_and_denominator",
                      "fold_odd_symmetry", "split_domain_into_segments",
                      "refactor_expression_form", "switch_construction",
                      "collapse_to_polynomial")),
```

* human decisions: (1) the `divider` slot pulls the whole div knowledge base into sfu, which is the precedent set by `fp_spaces.py`; (2) whether `numerator` and `denominator` are two slots or one shared evaluator; (3) `symmetry_form` duplicates the `single_poly` gap-file proposal, so the value names should agree.

### e_method

Single proposal: `e_method` (muller_2016#s04). Not merged with anything.

* name: `e_method`
* domain: sfu (an iterative evaluator; see the human decisions for its placement)
* doc: `polynomial evaluation as a linear system solved one signed digit per step: w(j) = 2 (w(j-1) - A d(j-1)), digits selected from the exact or truncated residual, an adder row per coefficient and no multiplier; converges only inside the admissible bounds (xi = (1 + Delta)/2, alpha <= (1 - Delta)/4; x <= 1/8 and |p_i| <= 3/4 at Delta = 1/2)`
* execution_style: fixed_iteration
* gap it closes: every `poly_datapath_space` candidate is a feed-forward multiplier arrangement; no evaluator emits the value digit-serially by a redundant recurrence.
* design choices:
  * `digit_selection: EnumChoice(("exact_residual", "approximated_residual"))` [muller_2016#s04]
  * `residual_estimate: EnumChoice(("round_to_nearest", "truncation"))` — meaningful under `approximated_residual` [muller_2016#s04]
  * `iterations: IntRange(8, 64)` — one signed digit per step, so the count is the target precision; the range mirrors `cordic.iterations` and the source states only convergence
  * radix is fixed at 2 in the source, so no `radix` choice is added
* component slots: none (the residual adders are the datapath)
* mutations: `switch_to_approximated_residual`, `switch_truncation_to_rounding`, `unfold_iterations_into_pipeline`, `rescale_coefficients_into_admissible_bounds`
* handles: muller_2016#s04 [textbook]
* evidence strength: 1 proposal, 1 textbook block, no paper and no implementation numbers in the bundle; only the admissible-bound conditions and one example domain are reported; the thinnest family in this plan.
* snippet (insert after `goldschmidt` in `sfu_approx_space`):

```python
        _f("e_method",
           {"digit_selection": EnumChoice(("exact_residual",
                                           "approximated_residual")),
            "residual_estimate": EnumChoice(("round_to_nearest",
                                             "truncation")),
            "iterations": IntRange(8, 64)},
           papers=("muller_2016",),
           iterative=True,
           doc="polynomial evaluation as a linear system solved one "
               "signed digit per step, w(j) = 2(w(j-1) - A d(j-1)); an "
               "adder row per coefficient, no multiplier; converges only "
               "inside the admissible bounds (x <= 1/8, |p_i| <= 3/4)",
           mutations=("switch_to_approximated_residual",
                      "switch_truncation_to_rounding",
                      "unfold_iterations_into_pipeline",
                      "rescale_coefficients_into_admissible_bounds")),
```

* human decisions: (1) top-level family versus a candidate of `poly_datapath_space` with `execution_style="fixed_iteration"` (that sub-space holds only feed-forward candidates today, and the module docstring's II contract excludes iterative families rather than banning them); (2) `redundant.online_arithmetic_unit` is the MSDF neighbour, and a value there is the third option; (3) whether one textbook block is enough evidence to register at all.

## rejected

* `neural_network_transcendental_approximator (mittal2016)` — one survey paragraph on Eldridge et al.; the network topology, weight precision and neuron datapath beyond "three-stage multiply-accumulate pipeline" are unstated, so the family cannot be defined from the bundle. This is a real vocabulary gap (no trained-MLP approximator family exists) and should be revisited when the primary paper enters the notes.
* `reciprocal_approximation_instruction (maruyama_2010)` — an ISA-level instruction whose algorithm and accuracy are unstated (`implementation_method: UNKNOWN`); the hardware behind it is a `div.seed_table_space` candidate, and `gaps/newton_raphson.md` line 8 already lists an opaque ISA-provided seed value.
* `series_function_evaluation (richards_1955#s11)` — a programmed loop over series terms, a software technique with no datapath beyond the term count; the fixed-term hardware form is `single_poly.basis=taylor`, and `gaps/single_poly.md` line 11 lists `execution: programmed` for this handle.
* `table_makers_dilemma_search (pasca_2011#s13)` — an offline exhaustive-search accelerator (Remez polynomial per subinterval, tabulated differences in a fixed-point adder pipeline, midpoint detector, credit-based dispatch, 38.5 hours for one binary64 exponent on 256 cores) that produces the worst cases `correct_rounding_strategy.worst_case_knowledge` consumes; an analysis method rather than a function-evaluation datapath; `gaps/correct_rounding_strategy.md` line 6 lists `hardness_search: fpga_tabulated_differences` as the value if the provenance must be searchable.

absorbed 6, new values 9, new families 4 (from 8 proposals), rejected 4
