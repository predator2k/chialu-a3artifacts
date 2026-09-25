# Demo plan

This plan decides what is built and run for the demo so that the whole
chain (sharing schemes by enumeration, database search, seed
generation, adaevolve rewriting) runs end to end on a real target and the first version of
the main comparison table of `docs/evaluation-plan.md` exists, and it
names what is deferred. The seed generator is narrowed to the families
and widths the two demo targets instantiate; every other family stays
in the library but is neither fixed nor re-verified for the demo.

## What the demo shows

1. **The chain on `int_subword_alu`**: the sharing schemes the seed
   realizes are enumerated and priced, the database search returns a
   front of family/pin declarations under the kept schemes, the generator renders each as a multi-file
   seed, adaevolve rewrites the units under the conformance, fault and
   synthesis gates. This target passes every gate today (conformance,
   fault, synthesis) and is the one where datapath sharing is real.
2. **The main comparison on `targets/eval/fp_alu_cmp.yaml`** (fp16,
   bf16, 2 x fp8e5m2; fadd, fsub, fmul, fmin, fmax, fcmp; four runtime
   rounding modes): chiALU against generic code evolution (ADIR's
   `best_of_n` and `beam_search` backends with the prompt sources
   emptied and the free operator) and a plain agent loop, under one
   model and one call budget, with the four plan seeds as tier 2 and
   one FPnew design point as a reference row if time allows.

Deferred to after the demo: Table B (the dot seed maps to 36.7 ns and
its families' sweeps are incomplete), the second FPnew design point,
HardFloat (needs the sbt flow) and TransDot, the experiment that starts
from FPnew's RTL, the TestFloat harness, the ablations beyond the
two-by-two, the RTLScout pair, asap7, and every family outside the scope
below.

## Generator scope for the demo

The two targets instantiate these kinds at these widths (from
`chialu/synth/seed_widths.json` and the fp_alu_cmp modes):

| Kind | Families kept in scope | Widths |
| --- | --- | --- |
| fp_adder | single_path, two_path, delay_optimized_unified, low_power_gated | fp16, bf16, fp8e5m2 |
| fp_multiplier | sig_mul_then_round, round_fused_in_reduction | same |
| fp_fma | separate_multiplier_and_adder (the two slots above), classic_fma, reduced_latency_fma, multipath_fma, bridge_fma (`bridge_reuse` and `monolithic_fused`; the cascade is refused), each fused family `dedicated_per_mode` or `shared_across_formats` | same |
| fp_comparator | integer_compare_on_bits, dedicated_magnitude_comparator | same |
| rounder, unpacker | dedicated_per_op, shared_per_lane, shared_across_formats; per_unit_unpack, shared_per_lane, shared_across_formats | same |
| adder, multiplier, shifter, bitcount, comparator, logic | every family with a module, as the units of int_subword_alu and as the sub-slots of the float families | 8, 16 (int_subword_alu); the significand widths of fp16/bf16/fp8 (11 to 3 bits plus guard) |
| subword | partitioned_carry_chain, replicated_lanes | int_subword_alu |
| checker | residue (int_subword_alu; `check_en: false` in the comparison target) | 8, 16 |

Out of scope for the demo: converters, posit, block/MX, BCD, RNS and
redundant cores, the approximate families, dividers and square roots,
SFU, dot, the nine other checker families.

Work on the generator is limited to what these kinds need:

* the open findings of the coverage sweeps in these kinds: the CPA
  sub-slot menus offering `hybrid_arrival_driven` and
  `approximate_truncated` where no module exists (drop them from the
  sub-slot spaces rather than implement them), and the width-bound
  choices (`chunk_width_bits`, `levels`, `chain_segment_length`) filtered
  by width in `synthdb.points` and the space domains;
* the per-variant golden run for these kinds and widths alone
  (`families.selftest --cases space --kinds ... --widths ...`), the
  curated case lists of the same kinds;
* the fp_alu seed's Verilator model, which exits with a segmentation
  fault at start (also the posit, mixed_cvt, dot and sfu seeds, and the
  block seed under the per-campaign bench). The fix is required for
  the search runs; the fallback for tier 2 is Verilator with the target's
  vectors.

## The chain

### Stage 1: sharing schemes

The realizable groups are the rules of `validate_partition` (binary
adders under the partitioned carry chain, twin multipliers, gate rows,
rounder/unpacker across formats, a float arithmetic kind across
formats on one datapath per lane position at the union geometry of its
modes, an adder with its lane's comparator or its lane's gates, the
float adders in the integer adders' bank, a fused multiply-add's
adder and multiplier), so the sharing schemes are a closed set:
`chialu.plans.sharing_schemes` enumerates them (per integer kind none,
all, per mode, per lane, or every set partition; per float unit
nothing, the stages, the arithmetic, or both), the estimate node
prices each at the default families, and the non-dominated ones go to
the numeric stage. No model is asked; the former discover role is
gone from the chain.

### Stage 2: database and numeric search

* The database is built on the host for the kinds and widths of the
  scope (`python3 -m chialu.synthdb build --seeds --kinds ...`), effort
  medium, at the seeds' own widths plus 8/16/32. Nothing else is built.
* A new node `chialu.eda.estimate` maps a declaration block to an area
  and a delay from the rows: per structure of the manifest the row of
  its declared family and pins at its width (interpolated on the kind's
  law where the width is absent), shared units counted once per plan,
  the glue the top adds around the structures (the OR of a mode's unit
  buses, the mode mux, the flag map) measured once per target by
  `chialu.profile` on the baseline seed and added per mode, each row
  taken at the factor its (kind, family) costs in place rather than
  alone (`chialu.profile.context_factors`, from the same profile: the
  increment a unit's buses add over the wires their driver reads,
  against that module synthesized alone), and what none of them
  explains calibrated once from the baseline's measured area and delay
  against its row sums. It is the objective of a
  numeric run file (`targets/eval/<target>.numeric.yaml`: evaluate graph
  of `declaration` and `estimate`, the goal's Pareto over the two
  estimates), run under ADIR's `nsga2` and `smac` backends locally.
* `chialu.front_seeds` writes the front's declarations as plans into
  the adaevolve run's `discovered.json`, fastest point first. They are
  the run's seeds: the search run file lists none of its own
  (`seeds.generated: []`), so the baseline program and the named plans
  are what the front is measured against rather than what the search
  starts from, and the first (fastest, largest) point is the score
  reference and the `seed.*` the area screens read.

### Stage 3: multi-file seeds

The core artifact becomes an ADIR family artifact: `members` from an
index set the elaboration provides, one member per slotted structure
(`m0.l0.adder`, ...) plus `packages`, `top` and `library`; the seed
generator returns `{member: text}`, a shared unit's module lives in the
file of its group's first member and the other members' files carry
the pointer. Each member is one evolve region, so `focus_map` maps a
file to that structure's variables directly. ADIR already assembles
and splits members (`artifacts.assemble_program`, `split_program`);
what is added is the call directory writing one file per member and
rejoining them after the agent's edit, and the chialu nodes accepting
the member dictionary (joined in member order) as `rtl_text`. The
declaration block stays in `packages`.

### Stage 4: adaevolve and the comparison methods

The run files keep `search.backend: adaevolve` through SkyDiscover on
the host cluster. The demo budget is small (`iterations: 5`, 20 model
calls per run) on int_subword_alu first, then fp_alu_cmp;
`parallel_nodes` stays 6 and `CHIALU_VERILATOR_JOBS=2`. A driver
`chialu.pipeline` runs the four stages in order on one run file and
writes one directory per stage under `<run>/pipeline/`.

The comparison methods reuse the same run file and evaluator:
`fp_alu_cmp.free.yaml` per generic backend (`best_of_n`,
`beam_search`; SkyDiscover's `evox` lacks a prompt file, and the
`openevolve` and `shinkaevolve` backends need packages the host lacks; `prompts.sources: []`, `knowledge_depth: path` on an
empty directory, `operator: [free]`, `seeds.generated: [baseline]`),
and `eval/plain_loop/` with the script that hands one
agent CLI the seed, the evaluator command and the metrics for the same
number of calls and logs the transcript.

## Evaluation deliverables

* `targets/eval/fp_alu_cmp.yaml` from `targets/make_targets.py` with
  the bindings of the evaluation plan's section 2 (`fp8e5m2`,
  `minmax_nan: number`, `check_en: false`, the four rounding modes),
  its `*.free.yaml` copies and the plain-loop script.
* Tier 2: the four plan seeds synthesized at four clock targets.
* The method rows at the demo budget: chiALU, the generic backends,
  the plain loop, one run each on fp_alu_cmp (and on int_subword_alu
  as the chain's own demonstration).
* `eval/baselines/fpnew/`, if time allows: the `fpnew_top` wrapper for
  one design point (Width 16, FP16, FP16ALT, FP8, ADDMUL MERGED and
  NONCOMP, `PipeRegs` 0), its the yosys frontend file list, and the conformance run
  through the target's verify bundle with the mismatch classes recorded.
* `eval/tables/table_a.md` and the area-delay figure, produced by a
  script from the run archives: the methods as rows, the tier-2 seeds
  and the reference row at the foot.

## Order of work

Each step names the coding work and the host jobs that run beside it.

1. The Verilator segmentation fault (valgrind on the cached model), the
   fault-site scanner fix verified, `PLAN_DOC` cut, the fp_alu_cmp
   target rendered and conforming. Host: the sweeps stopped; the
   database build for the scope's kinds started.
2. The multi-file artifact (ADIR call directory, chialu members, node
   inputs); `domain_selftest` and `adir seeds --local` on
   int_subword_alu. Host: the database build; the space-mode golden run
   for the scope's kinds.
3. `chialu.eda.estimate`, the numeric run file, `nsga2`/`smac` on
   int_subword_alu, `chialu.front_seeds`, `chialu.pipeline`. Host:
   tier 2 of fp_alu_cmp at four clocks.
4. The pipeline end to end on int_subword_alu on the cluster, with the
   fixes that needs; the `*.free.yaml` copies and the plain-loop script,
   first run on int_subword_alu at the demo budget.
5. The method rows on fp_alu_cmp at the demo budget: chiALU, the
   generic backends, the plain loop. Host: those runs.
6. The table and figure script; a second seed per method if the budget
   allows; the FPnew wrapper if time allows; buffer for cluster or agent
   failures.
7. A rehearsal of the demo from a clean run directory; the report.

## State

Done on the host, in the order of the steps:

* Step 1: the Verilator failures traced to `OBJCACHE=ccache` (ccache 3.7
  leaves Verilator's freshly made precompiled header out of the object
  hash, so a design's runtime objects came from another design's build;
  models died at start or ended at time 0); no object cache by default,
  ccache admitted with `include_file_mtime,include_file_ctime` in its
  sloppiness, and a model that dies, exits without output or ends
  without a dump reruns under Verilator. The fault scanner takes
  module-scope nets alone (block_alu's fault gate passes).
  `PLAN_DOC` names the realizable groups. `targets/eval/fp_alu_cmp.yaml`
  renders and passes conformance (26,136 vectors, bit-exact, 16 s under
  Verilator).
* Step 2: the core artifact is a family of one file per structure;
  `domain_selftest` passes its 51 checks on it; the database rows are
  `point`, `geometry`, `flow`, `result`, `provenance`; the demo's kinds
  are rebuilt under that schema (4742 rows, 13 kinds) and committed.
* Step 3: `chialu.eda.estimate`, the numeric run files, `front_seeds`
  and `chialu.pipeline` with a `calibrate` stage: the baseline's
  synthesis over its estimate sets the estimate's `area_scale` and
  `delay_scale` (int_subword_alu x0.939 and x1.676), since the raw sums
  ranked the float baseline infeasible at a target it meets. On
  `int_subword_alu` every plan seed is feasible (baseline 5544.5 um2 /
  1949 ps, packed_banks 3811.2 / 2568, per_position 5491.6 / 1949,
  dedicated_speed 4070.1 / 2106). The front plans now carry the point's
  families and choices per structure (the first version mapped none)
  and are repaired when the seed refuses a value the numeric space
  admits. The first repaired front seeds found two flow defects, both
  fixed: an exact unit's spaces admitted the algorithm-level families
  (a truncated multiplier reached the int16 flags and the fp16
  significand product), and a seed above 400 KB joined skipped the yosys frontend
  and failed yosys on a package import (the bound is per module now).
  The reruns then found two rounder defects (a count tree's modular
  final adder taken raw, a masked shifter's bound wrapping at a
  full-width shift), both fixed; fp_alu_cmp's front now has three of
  four points through every gate, two of them (7165.2 um2 / 5660 ps,
  7171.6 / 5460) better than every hand plan on both axes, against the
  baseline's 6838.6 / 7032 and dedicated_speed's 7782.6 / 6895.
* Step 3 (seeds): the search starts from the baseline and the numeric
  front alone; the hand plans are reference rows of the tables.
* Step 3 (sharing): the numeric stage now enumerates the sharing
  schemes the seed realizes, prices them at the default families, keeps
  the non-dominated ones and searches the families under each; the
  front's plans carry their scheme's groups. The discover role is
  removed from the chain (the enumeration covers its job). On int_subword_alu the first such run
  produced a point (adders and gate rows shared on a parallel-prefix
  bank, separate Booth multipliers) at 3837.3 um2 / 2042 ps that beats
  `dedicated_speed` on both axes.
* Step 4 (feedback): `synth_ppa` returns the critical path, the latest
  endpoints and the area per unit of every candidate; the composer
  hands the long texts to the agent as files under `feedback/` in the
  call directory, the card `knowledge/flow/synthesis_reports.md` says
  how to read them, and the `critical_path` tactic quotes the path.
* Step 4 (prompts): every run file samples an `ambition` variant per
  round (conservative, moderate, aggressive) beside the operator, and
  the composer's Conduct rules forbid a "nothing further to gain"
  answer (the user's rule of 2026-09-16).
* Step 4 (part): the run files of the generic backends
  (`*.free_<backend>.yaml`), the plain agent loop
  (`eval/plain_loop/loop.py`) and the table script
  (`eval/tables/make_table.py`) exist; the fp_alu_cmp plan seeds
  measure 6838.6 um2 / 7032 ps at the 8 ns target (the three plans
  render one design, since a float unit shares nothing under them) and
  `dedicated_speed` 7782.6 / 6895 after the fused multiplier's RNE tie
  fix (it had failed 9 fp8e5m2 fmul vectors on the underflow flag).

* Step 4 (model stages, smoke): with opencode on OpenRouter's GLM 5.3
  Flash the chain ran on int_subword_alu in three passes. In the latest
  pass the calibrated numeric stage searched under four enumerated
  schemes, the seeds stage measured the baseline, the two front plans
  (3844.2 um2 / 2463 ps, 3837.3 / 2042) and one plan of the discover
  role that was still present, and one adaevolve iteration produced a
  child through every gate: 4071.9 um2 / 2105.4 ps from the baseline's
  5544.5 / 1949.2, by VAR lines alone (a shared Ling bank, Booth
  multipliers, a shared gate row); the solution call took 1,070 s of
  its 1,200 s budget under the 60,000-character prompt, where the
  earlier passes' calls had timed out under 72,000 characters. The
  plain loop measured its seed and one turn in an earlier pass. Of the
  generic backends the host's SkyDiscover runs, `beam_search`'s one
  iteration produced a child through every gate in 803 s (4019.0 um2 /
  1970.4 ps, adders `parallel_prefix` and multipliers
  `booth_recoded_parallel`, score 0.989) and `best_of_n`'s one call
  ran out both attempts of its 1,200 s budget, so it recorded no child.
  Faults found and fixed on the way are in the worklog (the review
  over member dictionaries and its text order, the discover order, the
  plain loop's seed record, the stale Ray address on the host,
  opencode's title-call model, the backend database on a second run,
  the sidecar taken by the wrong evaluation).
* Step 4 (prompt as files): the solution prompt carries the task, the
  goal, the conduct, the block's form, the parent's score line, the
  program's regions, the focus, the operator, the ambition, the tactic
  and an index of the call directory's files; every long section is a
  file there (`context/`, `feedback/`), the knowledge base a copy the
  agent lists itself, and opencode may read nothing outside the
  directory. On int_subword_alu the prompt fell from 60,048 to 9,869
  characters, and the iteration under it produced a child through
  every gate (4019.0 um2 / 1970.4 ps) in 1,342 s.

Open: the full-budget runs of the methods, the tier-2 clock sweep and
the tables from real archives.

## Risks and their fallbacks

* A Verilator model dies or ends silent for a reason other than the
  ccache one found. Fallback: the conformance node reruns such a model's
  bench under Verilator with the target's own vectors; the candidate cost
  then rises to minutes on fp_alu_cmp, and the demo budget shrinks.
* The cluster or the agent CLIs fail on the day. Fallback: `adir run
  --local` with the numeric backends and the tier-2 seeds still shows
  stages 1 to 3; the adaevolve stage and the method rows are shown from
  the run archives of earlier successful runs.
* A generic backend behaves differently under SkyDiscover than
  adaevolve (prompt format, diff mode). The run files pin `diff_mode`
  and `max_solution_bytes` alike, and a backend that cannot run in time
  is reported as not run rather than approximated.
* The database build does not finish for the multipliers' points.
  Fallback: `estimate` returns "unknown" for a structure without rows
  and the numeric search treats it as the seed's value.
* the yosys frontend rejects a CVFPU construct, if the FPnew row is attempted. The
  patch lives in the wrapper directory, and the row states it.
* The estimate's fidelity is poor beyond what the baseline's scales
  correct. It is reported against the tier-2 measurements as a table of
  its own; the front it produces is still a set of seeds the adaevolve
  run improves on, and the ablation "database off" is the control.
