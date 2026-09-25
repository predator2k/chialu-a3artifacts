# sfu plan: applied record

Plan: `new_families/sfu.md`. File edited: `chialu/spaces/sfu_spaces.py`
only. Docs written: `arch/sfu/add_table_add.md`,
`arch/sfu/rational_approximation.md`, `arch/sfu/table_factor_refinement.md`,
`arch/sfu/coefficient_adapted.md`, and the four matching
`extract/gaps/<family>.md` files (each `none`). Rulings applied without
re-opening: no FPU-level, core-level or pulse-counting family, the
FPGA-mapping ruling, no ALU-level line on an adder family, plan lines for
other files deferred. Retired handles were applied under their re-keyed
names (`detrey_2007` as `detrey_2007b`); the `detrey_2007` handle that
`lut_plus_poly.papers` already carries still resolves and is left alone.

## applied

New values (12 lines):

* `digit_recurrence_exp_log += choice termination: {iterate_to_full_precision, linear_extrapolation}` (chen_1972 already in papers).
* `digit_recurrence_exp_log += choice index_advance: {sequential, leading_bit_skip}` (chen_1972 already). Caveat: `execution_style` stays `fixed_iteration`; the plan's note that the value runs variable-iteration is a doc fact, and the div-domain home of the ratio / inverse-square-root uses of the same apparatus stays the human's decision.
* `digit_recurrence_exp_log += choice state_domain: {real, complex_bkm}`; papers += muller_2016 (bajard_1994 already).
* `redundant_high_radix_cordic.scale_handling += differential_constant_scale`; papers += meher_2009 (dawid_1996 already). Applied once, here, per the README's duplicate rule; the redundant plan's `redundant_cordic` alternative is not applied.
* `sigmoid_tanh_pwl.approximation += step_sum` (alippi_1991 already).
* `softmax_layernorm.exp_evaluation += group_lookup_table` (du_2019 already).
* `softmax_layernorm += choice lut_group_gating: {fixed, input_proximity}`.
* `newton_raphson += choice termination: {fixed_steps, monotone_non_decrease}`; papers = (kim_2021,), since the family carried none. `execution_style` stays `fixed_iteration`.
* `poly_datapath_space += coefficient_adapted`, inserted after `factored`, papers muller_2016, snippet as in the plan. The slot candidate counts as a family for the lint, so it has a doc, `arch/sfu/coefficient_adapted.md` (one reference, the bundle has no other), and `extract/gaps/coefficient_adapted.md` = none.
* `SHARINGS += microcoded_fpu_sequence` (every family under `multi_fn`). The choice belongs to no single family, so lynch_1995 is added to `lut_plus_poly.papers`, which is the proposal's closest family and the one whose gap file already carries the K5 lines.
* `range_reduction += choice argument_scaling: {radian, pi_scaled}`; papers += detrey_2007b (the line's detrey_2007 is the retired handle, re-keyed to the same paper).
* `range_reduction += choice path_structure: {single, dual_close_far}` (detrey_2007b, added above).

New families (3):

* `add_table_add` inserted after `multipartite` in `sfu_approx_space`, snippet as in the plan: seven choices, slots `range_reducer`, `address_adder: cpa_space()`, `final_adder: adder_tree_space()`, papers wong_1995, dedinechin_2005, feed-forward. `adder_tree_space` and `cpa_space` are imported from `chialu.spaces.arith_spaces`. Docs: `arch/sfu/add_table_add.md` (two references, the bundle has no more), `extract/gaps/add_table_add.md` = none. No variant doc: the values wong_1995 pins (six parallel banks, Wallace-tree reduction) are parameter settings and a slot pick rather than named structures of this family.
* `rational_approximation` inserted after `single_poly`, snippet as in the plan: eight choices, slots `range_reducer`, `numerator` / `denominator: poly_datapath_space()`, `divider: div_space()`, `segmenter: segment_space()`, papers muller_2016, muller_2018, feed-forward. `div_space` is imported from `arith_spaces`. The divider slot needed a re-entrancy guard, `_divider_slot()` in `sfu_spaces.py`: `div_space()` builds `direct_polynomial.approximator = sfu_approx_space()`, which would build `div_space()` again without end, so the slot is opened once per construction and the copy of the family nested inside a divider carries no divider slot. Docs: `arch/sfu/rational_approximation.md` (two references), `extract/gaps/rational_approximation.md` = none. No variant doc: no block pins one enum value as a named structure (the Cyrix odd form is a parameter form).
* `table_factor_refinement` inserted after `lut_plus_poly`, snippet as in the plan: eight choices, slots `range_reducer`, `tail_evaluator: poly_datapath_space()`, papers wong_1994, muller_2016, feed-forward (the plan's execution-style question is settled as feed-forward: the stages are a fixed unrolled sequence, and the unified hardware time-shares them across functions). Docs: `arch/sfu/table_factor_refinement.md` (two references), `extract/gaps/table_factor_refinement.md` = none. No variant doc: `multiplier_shape=rectangular` is the family's defining mechanism rather than a variant of it, and a bare `rectangular` variant name already exists under `lut_plus_poly`.

Import cycle: `arith_spaces` has no top-level `chialu` import (its `cpa_space` / `div_space` delegate through lazy imports), so `import chialu.spaces.sfu_spaces` and `import chialu.spaces.div_spaces` both succeed in either order.

Absorbed entries (six) and rejected entries (four) needed no change.

## skipped

* new family `e_method` — deferred, not applied, per instruction: one textbook block (muller_2016#s04), and the placement is unresolved between a top-level family of `sfu_approx_space`, a `poly_datapath_space` candidate with `execution_style="fixed_iteration"`, and a value of `redundant.online_arithmetic_unit`. The plan's snippet (after `goldschmidt`) is ready when the placement is decided.

## deferred (other file)

* `div.seed_table_space += magic_constant_bit_seed` (the `seed` slot of `newton_raphson` / `goldschmidt`) — `seed_table_space` is defined in `chialu/spaces/div_spaces.py`, so the line is a div-file line; the plan carries the paste-ready `Architecture("magic_constant_bit_seed", ...)` snippet (walczyk_2021; `function=recip_sqrt` only, format-specific constant R, subnormal prescale), and `gaps/newton_raphson.md` line 8 names the same seed value.

applied 15 (12 new-value lines, 3 families), skipped 1 (`e_method`, deferred), deferred 1

## checks

* `_all_spaces()` returns 36 spaces; construction takes 1.17 s against 0.7 s before, because every `sfu_approx_space()` now builds one `div_space()` and every `div_space()` builds one nested `sfu_approx_space()`.
* `python3 -m chialu.archdocs`: `201 docs for 229 families; 28 undocumented; 402 variant docs` at the last run (other plans were being applied concurrently, so the family total moved between runs), no ORPHAN / BAD REF / BAD VARIANT line; none of `add_table_add`, `rational_approximation`, `table_factor_refinement`, `coefficient_adapted` is listed under `--strict` (the undocumented families are slot-only families of other domains).
* `python3 -m chialu.extract vocab` renders.
* `kb_section_exp2()` renders: 177533 chars against 88839 before, because the `divider` slot of `rational_approximation` renders the div families (with their summaries and variants) at depth 1 under the sfu space. Dropping the slot, or filtering it in `kb_section_exp2`, halves the exp2 prompt again.
* Every handle in a `papers=` tuple of `sfu_spaces.py` resolves in `PAPER_DB`.
* Doc shape: first paragraphs 653 / 696 / 595 / 391 characters; the following paragraphs 311 / 322 / 251 / 164 words; references 2 / 2 / 2 / 1.
