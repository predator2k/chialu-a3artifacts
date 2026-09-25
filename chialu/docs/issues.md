# Open issues

This document records the defects a review of chiALU found on 2026-09-17
at commit 60b04c1, and what has since been done about each one. Each
entry names the code the defect sits in, what happens because of it, and
the change that closed it.

Each entry carries the evidence behind it:

* **measured**: the behavior was reproduced against the original commit;
* **reviewed**: an area review read the code path and reported it.

and its state:

* **fixed**: the change is in and the evidence below was taken after it;
* **open**: no change yet.

The synthesis database's missing rows, the generator coverage findings
and the deferred families are recorded in `docs/work-plan.md`,
`docs/coverage-gap-plan.md` and `docs/deferred-families.md`, so this
document does not repeat them.

## No ALU run file loads

**fixed.** `chialu/modules/alu.py` declared `realization` as a fixed
variable with no entry in `binding_defaults`, so the loader rejected
every `chialu.ALU` instance with `variables.realization: unbound`. The
entry `"realization": {"fixed": "library"}` closes it, which is the value
`generators.realization_of` already returned for an unbound variable. All
18 run files under `targets/` now load. (measured)

## Gates that admit what they should reject

* **The fault campaign masks one group.** **fixed.**
  `chialu/verify/faults.py` took each fault row's vector from index 0 of
  the group's plan, so on an fp_alu-shaped spec every clean, single-bit
  and random row drove fp16 `fadd` and a checker that raised a false
  alarm on every `fmul` or every bf16 vector passed. `_stratified` now
  spreads each row class over the group's (mode, op) pairs from the
  spec's seed, and `chialu/eda.py`'s `fault_groups` keys
  `vectors_by_group` and `sites_by_group` by the pair rather than
  flattening them, so an internal site is forced while a vector its own
  unit serves is driven. Stuck rows reaching a vector their unit serves
  went from 16.2% to 100%, the grouped clean rows from 1 pair to all 18,
  and a checker that false-alarms on every `fmul` now fails where it
  passed. (reviewed)
* **An all-X fault dump passes.** **fixed.**
  `chialu/verify/harness.py` skipped every dump line that was not hex and
  `single_bit_coverage` returned 1.0 when no single-bit row was counted,
  so a checker whose `check_err` is undriven scored a clean sheet. A
  non-hex alarm is counted as a protocol failure, as the conformance
  judge already did. The generated top also no longer emits the undriven
  detect wires that made `check_err` undriven in the first place; see the
  lint entry below. (reviewed)
* **`alias_rate` does not depend on the candidate.** **fixed.**
  `alias_rate` is the seam campaign's `random_alias`, an XOR mask applied
  to `y_core` before the checker, so for a conformant core it gates the
  checker declaration rather than the candidate. The grouped campaign's
  `escape` does depend on the datapath, and it was bound by no
  constraint. The `fault` node now outputs `escape` per group and
  `escape_max` over them, and every checked run file carries
  `fault.escape_max le 0.05`. Measured on the baseline seeds:
  int_subword_alu 0.0126, mixed_cvt_alu 0.0020, posit_alu 0.0199.
  (reviewed)
* **The review parser accepts a reply that says the opposite.**
  **fixed.** `chialu/review.py:_parse` called `bool()` on the `realized`
  field, so `"realized": "false"` scored as realized, and a reply echoing
  the format template scored the first item through the positional
  fallback `rows[i]`. The parser takes JSON booleans alone, matches rows
  by module name, and gives an item no row names no verdict, which is not
  realized. A reply of `"false"` now scores false, a template echo raises,
  and a missing row leaves its item unrealized. (measured)
* **The review never sees a default family.** **fixed.**
  `chialu/review.py:_items` built its items from the candidate's VAR-line
  departures, so a structure standing at its default family was never
  reviewed and the `baseline` seed yielded no items against 24
  structures. The node takes the completed declaration as `decl.core`,
  which carries every decision the block leaves out at its default, and
  reviews those too. (reviewed)
* **`lint.ok` is a parse check.** **fixed.** `chialu/eda.py:lint` ran
  `read_verilog`, `hierarchy -check -auto-top` and `proc` and checked
  nothing else. It now appends `check -assert` and two
  `select -assert-none` lines, so a latch, a multiply driven net and an
  undriven read each fail it, and the baseline seed of all nine targets
  passes. That found a defect in the generated top: `alu_seed` declared a
  `d_<unit>` detect wire per unit and ORed them into `d_m<i>` while
  connecting the instance's port only when the detect width is non-zero,
  so with the checker off those wires were read and driven by nothing.
  A 16-bit sum assigned to a 4-bit wire still passes: catching it needs
  Verilator's width warnings, and the seeds carry 105 benign ones today
  (44 truncations and 61 expansions on int_subword_alu alone), so gating
  on them would fail every candidate. (reviewed)

## Measurements served without their flow

* **The database's rows are read without a flow check.** **fixed.**
  `rows_of` filtered on kind, status, family and effort alone and served
  rows measured under an earlier flow without saying so. It now filters
  on the flow, warning with both hashes and the count. When the filter
  would empty a kind the database has rows for, the rows are served with
  that warning rather than dropped, since an empty read turns the numeric
  stage's coverage to zero and hides the mismatch instead of reporting
  it; `CHIALU_DB_FLOW=strict` drops them. `tool_versions` also hashed
  `chialu.eda.DEFAULT_SCRIPTS` while the flow runs the PDK descriptor's
  script, so a descriptor-only edit changed every measurement and left
  the hash untouched; it reads the descriptor, and the yosys frontend
  joins the hash beside it. (measured)
* **Off-grid widths scale area linearly.** **fixed.** `at_width` scaled
  `area_um2` by `width / src` while `WIDTH_LAW` covered delay alone, so a
  22-bit product was under-priced against an adder. A point measured at
  both bracketing widths is interpolated in log-log space, which fixes
  its exponent from the data, and a point measured at one width is scaled
  by `AREA_LAW`, quadratic for the multiplier, divider and dot kinds. A
  22-bit `behavioral_star` multiplier goes from 2393 um2 to 3502 against
  its own rows of 1740 at 16 bits and 7138 at 32. (reviewed)
* **The node cache key omits the flow.** **fixed.** ADIR's key was the
  node name and the kwargs, so a changed liberty or an upgraded yosys
  served the old result. `adir.node` takes a `cache_id` callable whose
  string the key folds in, and `chialu.eda`'s synthesis and tool nodes
  name their flow through it: the liberty files, the resolved ABC script
  and the tool versions. A result whose detail names a timeout, an
  exhausted machine or a dropped connection is no longer written to the
  cache, so a transient failure does not become permanent for that text.
  (reviewed)
* **The liberty hash reads the first kilobyte.** **fixed.**
  `liberty_hash` hashed the file name, the size and the first 1024 bytes,
  so an edit past that point left the hash unchanged. It hashes whole
  files, cached on path, size and mtime. (reviewed)
* **The seed-ranking prior is inert.** **fixed.** `chialu/priors.py`
  returned `(0.0, 0.0, inf)` for every declaration with no trained model,
  and the ranker's exception path returns `inf` for every declaration
  too, so neither ordered anything. The prior prices a block from the
  synthesis database per STRUCTURE line, and ADIR's ranker hands it the
  completed declaration and every domain line rather than the VAR lines
  and one line per kind. On int_subword_alu the seven seeds score five
  distinct areas and the baseline reads 5902.5 um2 against 5544.5
  measured. (measured)

## Generated RTL that fails to compile or checks nothing

* **A residue channel can be constant.** **fixed.**
  `_mod_residue_module` sized the modulus literal to the lane width, so a
  narrow lane rendered `x % 2'd5`, which is `x % 1` and zero for every
  input. The modulo is computed in `max(width, M.bit_length())` bits, and
  width 2 mod 5 now renders `x % 3'd5`. (measured)
* **A compare below three bits emits a negative replication.** **fixed.**
  `writer.cmp_flags` is the one place the three flags become a result
  word: it zero-pads above three bits and keeps the low flags below
  three, which is the truncation the reference applies when it masks the
  compare code to the result width. An 8 x int2 unit with `cmp` renders
  27888 bytes with no negative replication and lints clean. (measured)
* **A conversion into a block target is sized without the target
  scale.** **fixed.** `engine.py` raises the significand width by the
  target's element and its scale together, which is the rule the
  source-block branch already applied. (reviewed)
* **One module text receives several names.** **fixed.** The float
  converter is named from its own content, and the integer converter
  carries the engine geometry rather than the mode prefix, which is what
  its text actually varies with. mixed_cvt_alu goes from 81 modules with
  4 duplicate definitions to 78 with 1. The one that remains is
  `fp_round/dedicated_per_op` against `fp_round/shift_round_convert`, two
  declared families whose text is coincidentally identical; merging them
  would leave the review unable to say which family a module realizes, so
  they stay apart. (reviewed)
* **Pin dictionaries are not validated at the factory entry points.**
  **fixed.** `validate_pins` raises on an unknown key and on an
  out-of-domain value at every factory entry, so `{'topolgy':
  'sklansky'}` gives "unknown pins ['topolgy']" and `{'topology':
  'not_a_topology'}` names the enum, where both used to render the
  default in silence. (reviewed)
* **Both the yosys frontend fallbacks are dead.** **fixed, by removing the need.**
  The converter returned the raw SystemVerilog when it was absent or the
  largest module passed its size cap, and yosys rejects the package
  import every seed carries, so both fallbacks produced a parse error
  that read as a candidate defect. Both now fail with the flow limit
  named. the yosys frontend itself has left the default flow: Verilator reads the
  generated SystemVerilog directly, and yosys reads it through
  `read_slang`, the yosys-slang frontend the host's yosys 0.68+36 carries
  built in. `CHIALU_FRONTEND=the yosys frontend` restores the old path. (measured)

## References that disagree with the standard and with each other

* **The SFU judge never compares the flags.** **fixed.**
  `chialu/verify/harness.py` scored a `vec_sfu` spec without a bit-exact
  budget on `y` alone, so every flag bit could be inverted on every
  vector and the unit still passed its `max_ulp` budget. Every
  provisioned output outside `RESULT_OUTPUTS` is compared bit-exactly
  whatever the numerical budget. (reviewed)
* **A pattern op is scored over lane 0 alone.** **fixed.** cmp, fcmp,
  shift and logic were scored as one unsigned integer of the result
  width, and `IntFormat.decode` masks to that width, so corruption in a
  higher lane left `max_ulp` and `mred` at zero. A pattern op scores per
  lane as exact or wrong, outside the value metrics. (reviewed)
* **`ops.py` holds a second set of float references.** **fixed.**
  `ops.py`'s `dot_ref` returned on the first special product and its
  `fp_ref` implemented min and max as minNum and rounded `fcvt` toward
  zero under RNE. `ops.py` delegates to `alu_ref` and `dot_ref`, so one
  reference exists per op. (reviewed)
* **The SFU reference drops the sign at two singular points.** **fixed,
  and it was not alone.** `sfu_ref.py` returned `+inf` for `rsqrt(-0)`,
  where IEEE 754-2019 section 9.2.1 gives `-inf`, and `+0` for
  `recip(-inf)`, where section 6.3 gives `-0`. Correcting it made
  `vec_sfu` fail conformance at four vectors by 252 ulp, which found the
  same two defects in two further copies of the same table: the sign at
  the zeros and the infinities was wrong in
  `chialu/targets/rtl/families/sfu_table.py` and in
  `sfu_control_table.py`, and the engine path in `sfu.py` hardcoded a
  positive sign for the infinity `rsqrt` returns at zero. Four
  independent implementations of these values existed, and three carried
  the bug. With all four corrected, `vec_sfu` passes. (measured)

## Stimulus that misses the hard cases

* **The corner product is sampled with replacement.** **fixed.** The
  product is kept whole rather than capped at 256 pairs by sampling with
  replacement, so which pairs survive no longer depends on the seed.
  (reviewed)
* **The documented one-ulp neighbours are absent.** **fixed.**
  `FloatFormat.corners` carries the neighbour patterns one ulp above and
  below each corner that `docs/formats-and-options.md` promises, and a
  neighbour the format cannot represent drops out. (reviewed)
* **The directed float pairs miss cancellation and the sticky
  boundary.** **fixed.** Directed families give `a - (a +- k ulp)` over
  random `a` and `k`, exponent deltas over 0 to p+4, and subnormal by
  normal products at the boundary. (reviewed)
* **The dot plan reaches no product cancellation.** **fixed.** Directed
  dot families give `a0 b0 = -(a1 b1)`, an addend at `-(sum) +- ulp`, and
  an addend exponent at the largest product's exponent plus p-1 to p+3.
  (reviewed)

The added families grow the stimulus, and the growth is uneven:
fp_alu_cmp goes from 26136 vectors to 73364, mixed_cvt_alu from 12868 to
16545, and int_subword_alu is unchanged. Conformance is a gate on every
candidate, so the float targets pay that growth on every evaluation.

## Repository hygiene

* **Most selftests are unreachable by name.** **fixed.**
  `chialu.selftests` discovers every `*_selftest.py` and runs each as
  `python3 -m <module>`, in `--jobs` at a time, with the modules that
  drive a simulator or a synthesis behind `--slow`. Its first version
  globbed `*selftest*.py`, which matches its own file, so it spawned a
  copy of itself per module and forked without bound; discovery now
  anchors on `_selftest.py`, excludes this module, and `main` refuses to
  start inside a run. (measured)
* **The paper corpus is tracked.** **open, and it stays.** The corpus is
  not to be deleted. `legacy/knowledge/pdf` holds 679 tracked PDFs of
  876 MB and no code path reads them at run time, so a clone still pays
  for them. (measured)
* **Three merged worktrees hold 2.6 GB.** **fixed.** The worktrees under
  `.claude/worktrees` carried commits that were ancestors of HEAD and no
  uncommitted work. They and their branches are removed. (measured)
* **`chialu.archdocs` exits 1.** **fixed.** It reported one undescribed
  cordic member, one unmet card claim and three variant cards outside
  their enum. The three cards moved under
  `legacy/knowledge/deferred/arch/`, the cordic card describes
  `unrolled_combinational` and says why the pipelined topology is
  deferred, and the claim lint no longer infers a family's kind from a
  component slot: a slot such as `sub_adder` names a place inside a
  family rather than a kind, and no realizer answers to it. The check
  exits 0. (measured)
* **`chialu/characterize.py` keeps a legacy CLI.** **fixed.** Its `main`,
  `row_key`, `db_path`, `load_db`, `jobs_for` and `run_job` wrote
  `chialu/synth/<pdk>.jsonl`, one level above the sharded directory
  `synthdb.load` reads, and its row key carried no flow fingerprint, so a
  rerun after a flow change found every row present and synthesized
  nothing. The command line is gone and `python3 -m chialu.synthdb build`
  is the one way to measure. (reviewed)
* **`equiv_check` reports an unproven cell as a mismatch.** **fixed.**
  The test is case-insensitive, and an undecided induction returns
  `pass: None` where a counterexample returns `pass: False`. (reviewed)
* **The task text names files a free run does not carry.** **fixed.**
  `chialu/task.py` names a context file only when the run's
  `search.prompts.sources` carries that source, so a generic-control run
  points the agent at nothing its call directory lacks. (reviewed)
* **The run files' header line names the wrong model.** **fixed.** The
  line renders from `PROVIDER` and `MODEL`. (reviewed)
* **The README's space count is stale.** **fixed.** It names 14.
  (measured)

## Two entries that need a decision rather than a fix

* **`checker.*` admits `fixed` alone.** **decided: the variables take
  `FIXED_OR_SEARCH`.** Both docstrings document `checker.*: {search:
  all}` as the one-rule spelling, so the variables admit it rather than
  the docstrings being wrong. (reviewed)
* **`dot_contract` requires a constraint that discharges nothing.**
  **decided: the requirement is dropped.** `dot_architecture`'s own
  `when` already carries the dependency, and a run file that sets
  `dot_contract: architecture` without binding `dot_architecture` still
  fails with `variables.dot_architecture: unbound`. (reviewed)

## What a later pass found

These are not defects of the reviewed commit. They were found while
clearing the prerequisites of `docs/evaluation-plan.md` and are recorded
here because each one changes a measured number.

* **The dot accumulator's default normalization was the anticipator.**
  **fixed.** `_acc_tail` in `chialu/spaces/fma_dot_spaces.py` gave the
  `lza` slot `lza_space()`, whose first family is the leading-zero
  anticipator, so every accumulator family normalized a frame of
  hundreds of bits by anticipation. Measured alone at nangate45 the
  281-bit anticipator (`fam_dot_lza_w281`) is 7,197.1 ps and
  35,180.1 um2 over 27,809 cells, while the 281-bit prefix adder it runs
  beside is 1,718.6 ps and 2,212.6 um2. The slot now takes
  `lzc_after_add` first, and `vec_dot_acc_cmp`'s baseline seed went from
  17,077.1 ps and 64,007.3 um2 to 10,612.0 ps and 26,433.5 um2.
  (measured)
* **The dot unit's one rounding was behavioral text.** **fixed.** The
  accumulator families carried no `round` component, so
  `dot_seed._library_rounder` fell through to the engine's `pack_d` for
  every one of them and the seed's final rounding was never realized by
  the library. `_acc_tail` now carries `rounding_space()`. On its own the
  change gives 15,567.1 ps and 66,186.4 um2. (measured)
* **The ALU could not express one status per operation.** **fixed.**
  FPnew reports a single status for a vectorial op and chiALU reported
  one flag word per result, which was 25,412 of FPnew's 34,261
  conformance mismatches against the comparison target. The option
  `flag_scope` (`per_result`, `per_operation`) expresses it, and under
  the comparison target's `per_operation` FPnew's mismatches fall to 24
  of 427,964. (measured)

## The target suite's own gaps

`tests/test_targets.py` globs every run file under `targets/`, which
brought two cases into it that the checks do not fit. Both are closed by
a skip rather than by a change to the flow.

* **A numeric run file's seed is a declaration.** **fixed.** The numeric
  stage's backend mutates declarations rather than text, so
  `int_subword_alu.numeric.yaml` and `eval/fp_alu_cmp.numeric.yaml` render
  a seed program that starts `ADIR-DECL v1` and carries STRUCTURE lines.
  Linting that as SystemVerilog fails at the first line. The lint,
  conformance and fault cases now skip a seed that is a declaration.
  (measured)
* **`checker_gen` is the ALU's.** **fixed.** It realizes a `check`
  block's rule table (`docs/checker-spec-plan.md`), which `vec_dot_acc`
  does not have, so the fault case failed with `unit 'vec_dot_acc' has
  no rule table` although the unit's residue checker comes from its own
  generator. The case now skips a unit that is not the ALU. (measured)
* **`flag_scope` had no loader default.** **fixed.** The option was
  declared in `chialu/modules/common.py` but absent from the ALU
  template's `binding_defaults`, so a run file that did not bind it
  failed to load with `variables.flag_scope: unbound (the loader has no
  defaults)`, which `chialu.verify.domain_selftest` builds. The entry
  `"flag_scope": {"fixed": "per_result"}` closes it, which is the same
  defect the `realization` entry at the top of this document records.
  (measured)
* **The simulation build cache never evicts.** **open.**
  `chialu.eda.SIM_BUILD_CACHE_DIR` (`~/.cache/chialu/sim_build`) keeps one
  Verilator build per (simulator, design, checker, bench) content key and
  removes none, and it reached 32 GB on the EDA host. Together with the
  selftests' retained trees it took the 327 GB filesystem to 93 %.
  (measured)
* **The selftest suite fills the disk through its own retained scratch
  trees.** **open.** Several selftests write gigabytes under `TMPDIR`
  and clean up nothing, and `tmp_path_retention_policy = failed` keeps
  the tree of every failed case, so the first failure retains gigabytes,
  the disk fills, and the remaining cases fail on `No space left on
  device`. One run of `tests/test_selftests.py -n 4` took
  `/tmp/pytest-of-host` to 39 GB and the 327 GB filesystem to 100 % at
  86 % of the cases, and the failures after that point say nothing about
  the code. `-o tmp_path_retention_policy=none` runs it to completion;
  the standing fix is for the modules that leak to remove what they
  write. (measured)
* **Four workers starve the fault campaign's Verilator build.** **open,
  and it is a setting rather than a defect.** At `-n 4` with
  `CHIALU_VERILATOR_JOBS=2` the `mixed_cvt_alu` campaign failed with
  `verilator timeout after 900s`; at `-n 3` with
  `CHIALU_VERILATOR_JOBS=4` the same case passes, and the suite is 72
  passed, 19 skipped and one xfail. The suite's own default worker count
  is the user's to pick, so the header of `tests/test_targets.py` names
  the pair that fits the 20-core host. (measured)

* **`seed_selection_selftest` fails on the integer ones' complement
  adder.** **open, pre-existing.** The selftest renders an integer mode
  whose `core.adder` selects `end_around_carry`, and `validate_pins`
  rejects the family's own `modulus_value` pin as inactive
  (`end_around_carry.modulus_value: inactive (the selected modulus is
  fixed by the word width)`), raised from `alu_int.declare_library`. The
  same failure reproduces on `be62c54` before the fused multiply-add
  change, so it belongs to the integer adder's pin schema rather than to
  the float adder. (measured, 2026-09-18)

* **The SRT dividers declared their first quotient step twice.** **fixed.**
  `_srt_sv` in `families/div.py` named the on-the-fly conversion's initial
  state `qq_0_0` / `qmm_0_0`, the same names the first digit step writes,
  so the `srt_radix2` and `srt_high_radix` significand dividers failed to
  compile (`Duplicate declaration of signal: 'qq_0_0'`). `fptest --tight`
  found it at fp16 and fp8e5m2 (the guard-round-sticky X of the rounder's
  `x_form`); whether the exact geometry rendered the same text before is
  not recorded, since no run file selects an SRT significand divider. The
  initial state is `qq_init` / `qmm_init` / `qpos_init` / `qneg_init` now,
  and neither geometry declares a name twice. (measured, 2026-09-18)

* **The fused multiply-add's anticipator left a result one position below
  the top.** **fixed.** `_complete_lza_normalize` in `families/dot.py`
  predicts the normalize shift of the fused families' window sum from a
  full adder on the final adder's operands, and it recovered the carry
  the dropped sticky lsb sends up from the magnitude's lsb equation.
  That equation gives the complement of the carry on a negated
  difference (Y - X, whose high part is `-(a + b + c0) - 1`), so a sticky
  borrow across a power of two (an addend of 1.0 against a product below
  the window) was predicted one position short, and under
  `normalize_before_add` the shifted operands wrap when they cancel, so
  the prediction was off by more. The value was right in both cases and
  the leading one sat below the top of the X; `fptest` compared packed
  values through the engine's pack, which normalizes for itself, so it
  passed, while the seed's rounder under `normalized_input` (every
  rounded op of the mode through the fused datapath) packed the
  significand at the exponent of the top position and delivered twice
  the value. The `fp_fma_alu` target's bf16 mode showed it on 80 of its
  vectors (`a = 0x1, b = -1` under RTZ: `0xbfff` for `0xbf7f`). The
  lookahead now takes the low carry from the operands' own lsbs and the
  negation flag, and the normalize-before-add path hands it the
  unshifted operands with the shift already taken as an offset, so the
  predicted shift is exact; `fptest` checks the normalization promise of
  every fused family in both roles beside the values. (measured, 2026-09-18)

* **`multipath_fma`'s zero-operand bypass did not compile under the tight
  X.** **fixed.** The five-path form declared an unused word `p_x` of the
  X's significand width holding the 2S-bit product, whose zero-extension
  is a negative replication when the guard-round-sticky X (`SW + 3` bits)
  is narrower than the product; Verilator rejected the module at fp16 and
  fp8e5m2. The one-factor sweep of the fp_fma slot (`fptest --fma-sweep
  --tight`) found it; the dead word is gone. (measured, 2026-09-18)

* **The reduced-latency FMA's fused rounding rounded to odd where the
  engine rounds away from zero.** **fixed.** `post_normalization_dual_sum`
  in `families/dot_fma_round.py` (reduced_latency_fma under
  `rounding_position: fused_with_cpa_dual_sum` without
  `normalize_before_add`) took the engine's rounding code 5, which is
  round away from zero (the checker's window copy under `FORCE_RAZ`, and
  every bench's sixth mode), as `inexact && !lsb`, which is round to odd,
  so an inexact result with an odd kept lsb stayed one ulp below the
  reference under that code. The dot bench's `fp32fma
  reduced_latency_fma rounding_position=fused_with_cpa_dual_sum` case
  failed 19 of 298 vectors on it before the fp_fma slot exposed the
  choice; the same case and the ALU's fptest pass now. (measured,
  2026-09-18)

* **The pre-normalized fused rounding left the leading one one position
  below the top.** **fixed.** Under `normalize_before_add` the fused
  rounding of `_fma_sv` delivers the kept word with its lsb at the guard
  position, so when the pre-normalization had put the leading one one
  below the window's top the X left with its leading one at bit XW-2 and
  the exponent of the top position. The value was right and the engine's
  pack normalizes for itself, so the values passed; the seed's rounder
  under `normalized_input` would have packed the wrong significand. The
  X is normalized by the kept word's own top bit now, and `fptest`
  checks the promise. (measured, 2026-09-18)

* **The rounder lane module lists the rounded ops on its own.**
  **fixed.** `alu_seed.ROUNDS` and `alu_float._rounds` both name the ops
  whose result the mode's rounder packs, and the seed's rounder lane
  module takes its op arms from the first. An op the first list missed
  (the fused multiply-add ops, when they were added) rendered without an
  error and without a warning: the producer lane module wrote the x bus,
  the rounder had no arm for the op, and `y` and the flags stayed at
  their zero default, so every such vector mismatched with 0. Both lists
  carry the fused ops now; the two lists remain two, and a kind-level
  audit of the op arms (every legal op of a mode has an arm in its
  rounder lane module) would turn the silent zero into a render error.
  (measured, 2026-09-18)
* **reduced_latency_fma with the squarer multiplier under the fused
  rounding mismatches at fp16.** **open.** The host's variant sweep of
  the fp_fma kind (2026-09-18, `step3_reduced_latency_fma`) found one
  point that fails conformance on 606 of its vectors:
  `multiplier.family: squarer` (`folding_scheme: divide_and_conquer`) with
  `rounding_position: fused_with_cpa_dual_sum`, `add_skip_for_pure_addition`,
  `lza.correction_scheme: post_norm_fine_shift` and
  `norm_shifter.family: butterfly_network` at fp16; the first mismatch is
  `fmul` of 0 by 0x3bff giving the smallest subnormal instead of 0. The
  same point's fadd vectors pass. The squarer's two-operand product (the
  quarter-square identity) or its interplay with the fused rounding's
  window is the suspect; the two other failures of that sweep were the
  approximate adder in the exact slot, which the legality rule now
  excludes before the render. (measured, 2026-09-18)
* **The producer unit dropped the sequential contract's product flags.**
  **fixed.** Under `fma_contract: sequential` the fused multiply-add
  rounds its product in the producer lane module, and the default
  partition puts the mode's rounder in a unit of its own. The producer's
  lane module writes the x bus and returns before the flag expression, so
  the product's `inexact`, `overflow` and `underflow` stayed inside it
  and 4841 of 32788 vectors of an fp16 seed with flags mismatched on the
  flag word alone. The producer writes the product's rounding flags into
  its own unit's flag bus now, which the seed ORs with the rounder unit's,
  and a NaN operand suppresses them as the reference's early return does.
  The earlier sequential conformance runs carried no `flags` list, so
  they did not see it. (measured, 2026-09-18)
* **The fault bench's build bounds a checked target's size.**
  **measured, and the target was cut to fit.** The fault campaign's
  universal bench injects one site per net of the core
  (`eda._candidate_build` reads `fault_sites.sites_by_pair`), so its
  Verilator build grows with the core's net count, and that build has
  900 s. `fp_fma_alu` with the four fused ops over two lanes of each fp8
  mode declares 9,800 nets of 95,446 bits, and its build exceeded 900 s on
  the idle host at 10 Verilator jobs (Verilator's frontend is one
  thread, so the job count does not move it). One lane per mode leaves
  the same four modes, four fused families and ten ops at 6,136 nets of
  59,129 bits, which is under the 6,644 nets of the same target before
  the fused ops; the build then takes 8 min 57 s for the whole case and
  the campaign reports escape_max 0.0 and alias 0.0. For comparison
  `mixed_cvt_alu`, whose build the suite's docstring already calls tight,
  declares 7,800 nets of 58,378 bits. (measured, 2026-09-18)
* **The rounder mismatched at fp8e4m3 under the guard-round-sticky X.**
  **fixed.** `fptest --formats fp8e4m3 --tight` failed 6 of its rounder
  benches, one per rounder family and adder, on one X:
  `x=06d68 rnd=0 ftz=0 ref=01800 lib=01868`, a value with exponent -19,
  far below the format's smallest subnormal; the reference packs +0 with
  underflow and inexact, the library rounder packed 0x68, which is 64. The
  defect came in with the tight X of `d42ed1e` (2026-09-18), whose
  `fptest --tight` runs covered fp16, bf16 and fp8e5m2 and not fp8e4m3.
  The cause: `round_sv` clamps the subnormal right shift at `XW + 1`, the
  word's width, so that the half position lands on the word's zero top
  bit and nothing rounds up; the kept-bit shifter, a barrel of `XW + 1`
  bits, has no stage for a shift of `XW + 1`, so it left the word
  unshifted (`keep = 0x68`), and the unshifted significand packed as a
  normal. The exact X never meets the case because `XW + 1 = 2 SW + 5` is
  odd; the tight X of fp8e4m3 has `XW + 1 = 8`, a power of two. The
  shifter now takes at most `XW`, which already clears the word, while
  the masks keep the full amount. (measured, 2026-09-19)

## What the flow now costs

The measurements the changes above rest on, taken on the 23 GB host
under nangate45 at medium effort on 2026-09-17:

| measurement | value |
| --- | --- |
| synthesis peak memory, vec_dot_acc seed (540 KB, 195k cells) | 8.78 GB |
| synthesis peak memory, fp_alu_cmp seed | 1.24 GB |
| synthesis peak memory, int_subword_alu seed | 0.11 GB |
| `read_slang` against the yosys frontend, four seeds | within 2.1% area, 3.6% delay |

`EDA_RESOURCE` is 2 because of the first row: a pool of `eda: 8` at a
weight of 1 would admit eight of that synthesis and run the machine out
of memory.
