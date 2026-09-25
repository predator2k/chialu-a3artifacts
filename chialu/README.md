# chiALU

chiALU is an ADIR domain library for arithmetic units. It registers
three unit-class templates (an ALU, a vector SFU, a vector dot-product
accumulator), the microarchitecture families of the literature as their
searched variables, generators for the behavioral seed, the residue
checker and the verification files, CHIA nodes for the gates and the
synthesis, sharing plans as seeds, and the knowledge base the agent
reads. A run file binds the variables, wires the nodes, and states the
constraints and the goal; ADIR (the submodule under `third_party/adir`)
binds it, evaluates every candidate on the derived graph, and hands the
search to a backend.

Every unit chiALU generates in this version is single-cycle and
combinational: one operation per vector, no registers, and the
synthesis metrics are the combinational delay and area. Registered and
multi-cycle units (a fixed latency, a variable latency, the iterative
reuse of a datapath) are a later version. The families whose defining
structure needs cycles, and the entries that are methods or
system-level kernels rather than a unit's structure, are deferred:
`docs/deferred-families.md` records them with their reasons, and their
cards live under `legacy/knowledge/deferred/`, outside the knowledge
path a run hands the agent.

## Layout

```
third_party/adir/   ADIR, a git submodule: variables and binding times,
                    artifacts and the declaration block, the evaluation
                    graph over CHIA nodes, constraints and the goal, the
                    archive, the backend binding, the `adir` command;
                    docs/design.md is its specification
chialu/             the chiALU domain library (a python package)
  domain.py         registers the templates, the priors and the tactic
                    sources; `module: chialu.<Template>` in a run file
                    finds them
  modules/          the three templates: ALU (y = op(a, b) over modes),
                    VecSFU (vecC = sfu(vecA)), VecDotAcc (D = A.B + C);
                    common.py (the shared option variables), generators.py
                    (seed, checker, verification files, sharing-plan seeds)
  spaces/           14 family-space files transcribed from the knowledge
                    base (adders, multipliers, dividers, FP, FMA/dot, SFU,
                    checkers, decimal, redundant/online, approximate,
                    shift/SIMD, DSP/posit); adir.spaces.Space compiles them
                    to conditional variables
  eda.py            the CHIA nodes: lint, conformance, fault, equivalence,
                    yosys_stat, synth_unit, synth_ppa (a run file names
                    them as chialu.eda.<node>)
  review.py         the declaration review node (chialu.review.claude |
                    codex | opencode): a model reads every module with a
                    declared family and says whether the text realizes it
  lines.py          the declaration line kinds STRUCTURE and MOVE
  plans.py          the sharing plans a seed may follow (baseline,
                    packed_banks, per_position, dedicated_speed, fused_fma)
  priors.py         the structure-area prior and the tactic sources
  prompts.py        the prompt sources (the interface, the structure table) ADIR's
                    composer renders; chiALU writes no prompt text
  papers.py         the bibliography and the paper presets
  targets/          derive.py (the verify spec, seed and checker from the
                    bindings), bundles.py (the verification files), rtl/
                    (the SystemVerilog generators: alu_seed.py with one
                    emitter per format family, dot_seed.py, sfu_seed.py,
                    alu_checker.py, dot_checker.py, residue.py, and
                    structures.py, the seed's structure manifest)
  knowledge/        arch/<domain>/<family>.md (one doc per family) and
                    arch/<domain>/<family>/<variant>.md; bib/ (handle ->
                    citation); notes/; pdf/; extract/; moves/
  verify/           the golden verification layer: formats, exact reference
                    ops, stimulus plans, error and fault-detection models,
                    SV testbench generation; the selftests
ml/                 the PPA surrogate (train / check / warm) over the archive records
ops/                VM helpers (vmctl.sh, hostctl.sh, vm_recover.sh)
pdk/                PDK descriptors (pdk/<name>.yaml) and the liberty files
run/                one run per subfolder (gitignored)
docs/               formats-and-options.md (the data-format and unit-option
                    spec), families-spaces-cards.md (what a family, a
                    space, a card and the corpus pipeline are),
                    deferred-families.md, future-work.md, slot-audit.md,
                    evaluation-plan.md, work-plan.md; the target run
                    files live in targets/
```

## The templates in a run file

Every variable of a template is bound in the run file at one of the
binding times it admits:

* `fixed`: the specification (a mode set, an op, an option, a checker
  modulus);
* `runtime`: a provisioned set a port selects among (`modes`, `ops`,
  `rounding`, `check_en`);
* `search`: a decision the candidate declares (`core.family`, the family
  and choices of every physical structure of the seed,
  `core.<kind>.<index>.<choice>`).

The elaboration creates the structure-indexed variables from the seed's
manifest, one index per (mode, kind) since the lanes of a mode are
replicas and share their decisions, so a run file binds them by pattern:
`core.*: {search: all}` opens every structure, `core.adder.*.family:
{search: [...]}` narrows the adders, `core.adder.m1.family` the adder of
mode 1. `clock_ps` is the synthesis timing target: the mapper optimizes
the area under it, the synthesis nodes read `vars.clock_ps`, and the
run file bounds the delay by it as a soft constraint (a violation is
infeasible and kept with its measurements) while the goal is the Pareto
front of area and delay under that target. A checked unit binds
`checker.family`, the pins the family's generator reads
(`checker.modulus`, `checker.moduli_count`, `checker.A`,
`checker.replica_width_bits`, ...) and the comparator slot
`checker.comparator.family` (the plain compare, a two-rail tree, a
k-out-of-2k checker or a majority voter). A seed
declares its plan in `VAR` lines and its structures in `STRUCTURE`
lines (with `group=` for a shared datapath); chiALU's line-kind check
verifies the structure table against the manifest. The block lists
decisions alone: a `VAR` line stands where a value departs from its
default (the first family of a kind, the first member of a choice), so
the baseline seed declares nothing, and a family declared for one
member of a group reaches the group's other members of that kind
(`chialu.lines.normalize_declaration`).

A sharing plan is data (`chialu/plans.py`): the four named plans render
through `partition`, and a plan in the plan grammar (`PLAN_DOC`: shared
groups with members, a family and pins, per-structure and unit-level
families) renders through `plan_seed`. `sharing_schemes` enumerates
every sharing plan the seed realizes, and the pipeline's numeric stage
searches the families under the schemes it keeps (`docs/glossary.md`
names the parts). A group is how a plan says that several structures
are one physical datapath: the binary integer lanes on one
lane-partitioned adder, twin-precision matrix or gate row, an adder
with its lane's comparator, the float adders in the integer adders'
bank, and a float kind's structures across two formats or more on one
datapath per lane position at the union geometry of their modes (the
seed widens every float mode of the unit to it and muxes the operands
by the mode, so one fp16, bf16 and fp8 adder become one x26e16s11
adder per lane).
A candidate that regroups structures in its `STRUCTURE` lines, or
declares another family or family choice, is re-rendered through
`replan`: the top and the changed units are the seed's, a unit whose
members and families are unchanged keeps its text, and so does a unit
whose region the candidate edited itself.

The seed realizes a declared family by construction where the family
library has a module for it (`chialu/targets/rtl/families`): the
adder, comparator, shifter and bit-count families are parametric
SystemVerilog (`adder.sv`, `shifter.sv`, `comparator.sv`, `logic.sv`), and the
prefix families come from a prefix-graph generator (`prefix.py`: the
named topologies, Harris' (l, f, t) points, Knowles fanout vectors,
Roy's index sequences, PrefixRL's node moves with legalization, an
arrival-driven construction; the graph's levels, size, fanout and wire
tracks; an unrolled adder module with the Ling and compound variants).
The multiplier families (`mul.py`: the AND array with Baugh-Wooley,
radix-4 and radix-8 Booth, the carry-save array, recursive Karatsuba;
Dadda, Wallace or 4:2 reductions; the final adder from the adder
library or the arrival-driven prefix graph of the tree's column
depths) are generated per width and signedness the same way, and so
are the other combinational multiplier families (`mul_ext.py`:
behavioral_star, the folded squarers with the quarter-square product,
truncated fixed-width and logarithmic Mitchell multipliers with their
correction ladders, the inexact-compressor, underdesigned-block and
DRUM-window multipliers, segmented grids over library merge adders,
redundant-binary trees with their converters), the end-around-carry
adders (modulo 2^W - 1 for the ones'-complement modes, 2^W + 1 and a
generic modulus; two-pass, cyclic or select recirculation), the
truncated adders and the block-composed carry-skip / select /
increment adders whose blocks are another library adder
(`adder_ext.py`), the logic gate row (`logic.sv`), and the
approximate-unit families of an ALU under `accuracy: approximate`
(`approx.py`: speculative segmented and lower-part-approximate adders,
the accuracy-configurable adder at a static operating mode, the
correction ladder of truncated multipliers, DRUM windows, RoBA operand
rounding, the logarithmic ladder, row perforation, the inexact 4:2
compressor styles, approximate Booth encoders, and dividers with
inexact recurrence cells or reciprocal, window, logarithmic and short
Goldschmidt estimates; the approx_method families are methodology and
have no module). The unit-level sharing families live in the seed's
unit modules (`subword.py`): a twin-precision multiplier is one gated
partial-product matrix over the unit's lane packings, the
partitioned_carry_chain subword family one lane-partitioned adder whose
carries are cut at the selected packing's boundaries, and wide_gate_row
one gate row over the whole word; the lanes read their slices through
the unit's shared buses. The posit unit families (`posit.py`) are the
decoders and encoders of a posit mode (the regime by a leading-zero
counter and a shifter or by a masked two-stage decode, in sign-magnitude
or two's-complement form, with the PLAM logarithmic fraction under an
approximate contract), the unit's X operators and the boundary
converters of posit_ieee_interop. The core
families whose datapath keeps a redundant or residue form
(`redundant.py`) give the integer lanes of a `redundant_internal` core
the representation slot's adder (generalized signed-digit sets with
the carry-free or limited-carry rule and the on-the-fly or
carry-propagate exit conversion, hybrid signed-digit runs, the
carry-save datapath through one compressor level) and the lanes of an
`rns_internal` core the channels slot's adder, multiplier and
comparator (forward converters by chunk tables, segmented sums,
periodic folding or a modular-MAC chain; channel adders per modulus
form with the diminished-one option; channel multipliers by table,
folded rows, Booth rows or the estimated-quotient recurrence; reverse
converters by CRT, mixed radix, New CRT-I and II; comparators by
mixed-radix digits, the CRT fraction estimate or the diagonal
function); the on-line families are exceptions.
The decimal families of a BCD ALU (`decimal.py`) are the direct BCD
adder (8421 or excess-3 digits, the +6 correction before or after the
digit sum or direct decimal carry logic, ripple, digit-group or full
lookahead carries, tens' or nines' complement subtraction, the digit
adder from the binary library), the speculative adder (+6 speculated
over one binary carry network, late correction or dual-path select),
the redundant-digit adder (Svoboda, RBCD, maximally redundant or
overloaded digit sets, carry-free two-step addition, carry-propagate or
on-the-fly conversion), the multioperand adder (decimal 3:2 and 4:2
levels or binary column sums converted at the root), the parallel
decimal multiplier (recoded multiplier digits, precomputed multiples or
digit-product tables, 8421 / 4221 / 5211 / excess-3 / signed internal
codes, decimal or binary reduction trees), the decimal digit recurrence
(comparison against the multiples, the radix-2 x radix-5 split, the
redundant sets after prescaling) and the decimal Newton divider over a
seed table. The special-function families of the SFU (`sfu.py`) are
generated per function and format as a fixed-point netlist that
evaluates in Python and renders SystemVerilog, so the generator measures
the module's error against the reference before it emits it: value
tables (direct, compressed), bipartite, symmetric table addition,
multipartite and add-table-add lookups, piecewise-linear evaluators with
uniform, nonuniform or power-of-two segments and multiplierless slopes,
residual-coded and region-dependent tables, piecewise and single
polynomials over Horner, Estrin, parallel-monomial, factored,
coefficient-adapted, shift-add or FMA datapaths with uniform, nonuniform,
hierarchical, power-of-two or range-addressable segmentation, rational
approximations over the divider library, table-plus-polynomial and
table-factor-refinement schemes, the GPU quadratic interpolator, the
logarithmic converters, unrolled CORDIC and redundant high-radix CORDIC,
digit-recurrence exp/log, Newton-Raphson and Goldschmidt reciprocals,
the activation-function lines and softmax/layernorm over the lanes, with
Cody-Waite, Payne-Hanek, modular or table-augmented range reduction;
the module header carries the measured error at the pins (the default
segment and degree pins of the polynomial families miss the one-ulp
budget by design). The time-shared multiplier, the microcoded sequence,
the folded CORDIC and the digit-serial activation are sequential:
exceptions at the choice level. The
dot-accumulate families of the vector dot unit (`dot.py`) are generated
per mode geometry on the engine's X format (raw operands for an integer
mode): the accumulator families share one construction (the products
by the multiplier component, an alignment into the exact frame or into
a window at the largest exponent, a per-level tree, a coarse/fine
two-stage shift, the pairwise exponent differences reused or a sorting
network with realignment lines, two's complement or dual positive and
negative reductions, a chain, a binary tree of library adders or a
carry-save tree with a library CPA, the normalization by a count or an
anticipator), the FMA lineage realizes d = c + a * b for a one-element
mode (the addend aligned in parallel with the multiplier, end-around-
carry, dual-adder or complement negation, the reduced-latency
pre-normalization with the rounding fused into a compound adder, the
multipath close/far selection, the bridge of the library's fp
multiplier and adder, the mixed-precision cascade), the long and
streaming accumulators take their one-operation form, the block
families serve block operand modes, and the tensor-core, bf16 and fp8
datapaths round their partial sums or chunks through the library
rounder; a module whose pins round a partial result names the contract
it meets, and the cascade styles of a one-element mode are the
sequential contract, which the seed instantiates as such. A block
family on a scalar mode and an FMA family on a multi-element mode under
the fused contract are exceptions of the mode. The loop-carried
streaming approaches, the bit-serial MAC, the on-line families, the
time-shared and streaming core families (`merged_mul_div`,
`online_msdf_core`), the FPGA DSP slice's own organization
(`dsp_block_space`) and the decimal floating-point families
(`decimal_misc_space`) are deferred with the single-cycle scope
(`docs/deferred-families.md`). The
float families (`fp.py`, on the engine's X format: the unpacker, the
significand adders single_path / two_path / delay_optimized_unified /
low_power_gated with their alignment, leading-zero and normalization
sub-slots, the significand multipliers with the rounding fused into the
reduction or not, the comparators, the rounders by increment, compound
adder, injection or flagged prefix, the converters) and the dividers
(`div.py`: the restoring and nonrestoring arrays, SRT radix 2 and
radix-4 stages with a generated quotient-digit selection table checked
for containment at generation or comparators against its thresholds,
the on-line MSDF recurrence, Newton-Raphson, Goldschmidt, a
table-indexed polynomial, the prescaled and Svoboda-Tung recurrences
over seven seed-table families whose error bounds size the iteration,
the back-multiplied remainder or the exclusion-zone precision as the
final rounding, and the square roots by the restoring recurrence or the
rsqrt iteration) are generated for the engine geometry, with the
significand divider and square root wrapped on X. An
integer lane module instantiates the library module of the declared
family and reads its result and flags off it, a float lane module its
adder, multiplier, divider, square root, comparator, rounder and
unpacker; the modules used follow the generated ones. The family menu marks such families `[library]`;
the rest stay behavioral in the seed, for the rewrite; the choices whose
structure is sequential (the software trap on subnormals, the bit-serial
MAC, the time-shared SFU evaluators) left the spaces with the single-cycle
scope (`docs/deferred-families.md`). The library's
selftest (`python3 -m chialu.targets.rtl.families.selftest`) runs every
module, every emitted prefix adder, multiplier, divider and square root
against a behavioral reference under Verilator, and the float
harness (`python3 -m chialu.targets.rtl.families.fptest`) every float
module against the engine at fp16, bf16 and fp8e4m3; the prefix tool's command line
(`python3 -m chialu.targets.rtl.families.prefix --width 32 --graph
harris:l1f1 --report`) serves a rewrite.

The synthesis database (`chialu/synthdb.py`, `python3 -m chialu.synthdb
build|status|query|verify|merge`) holds one row per measured design
point of a family, in five parts: `point` (the complete binding: the
kind, the family, every design choice with its default written out, and
every slot recursively with the family bound there and its own choices
and slots; `point_id` hashes it), `geometry` (the width, and the format,
function or signedness the point is measured at: a float kind names its
format, since fp16 and bf16 are both 16 bits and share nothing of their
datapath, and every point of such a kind is measured at every format of
its width the run files build), `flow` (the PDK,
the liberty hash, the effort, ABC's clock target, the tool hash),
`result` (status, area, cells, the post-mapping delay, seconds, detail)
and `provenance` (the generated text's hash, the module, the date, the
build's sampling tags). The key is the flow, the geometry and the point
id. The build samples every family at its baseline and one point per
choice value and per alternative slot family, since the cross product
of the slots does not fit a database; the row records the whole point,
so a model over the rows needs no knowledge of that policy, and a point
measured elsewhere fits the same table. A build is incremental by the
generated text's hash, and one synthesis serves every point whose text
hashes the same. `prune` drops a row that leaves a slot unbound,
`slots` reports what each slot buys (the members that map to a netlist
of their own, and the delay from the fastest to the slowest), and
`status`, `query`, `verify`, `merge` and `fetch` are the other
subcommands. The `chialu_timing` PromptSource shows the
solution role the fastest variant per family at the run's
clock with its delay and area, interpolating a width the database lacks
on the kind's own law; `python3 -m chialu.prune run.yaml --threshold
0.10` drops the families whose fastest variant exceeds the clock by more
than the threshold from the run file's family domains (a family slightly
over stays, as does one the database lacks), so a user narrows one run's
options and starts several runs side by side. `python3 -m chialu.profile
--target targets/fp_alu.yaml` says where a seed's own delay goes, by
synthesizing the cone feeding each internal wire of its top module.
The pipeline's calibrate stage reads that profile twice: for the glue
the top adds around the structures (the OR of a mode's unit buses, the
mode mux, the flag map), which the estimate adds per mode, and for the
factor a (kind, family) costs where it stands against the same module
synthesized alone, which is what its database row is — a unit that
overlaps its producer is cheaper in place than its row says, and one
scale for the whole design cannot tell one kind from another.

The prompt of a round is ADIR's composer's; chiALU supplies data
through four PromptSources (`chialu_interface`, `chialu_families`, the
family menu per kind with its cards, `chialu_structures`, the
structure table with the region in focus expanded, and
`chialu_timing`) and the `focus_map` from a program's unit modules to
their variables. The
program reaches the agent as a file path inside the call's own
directory under `<run>/agent`, where the knowledge base and the call's
programs are linked; every prompt and reply is logged under the run's
`prompts/`.
A checked ALU states its checking per data format and op in a `check`
block (docs/checker-spec-plan.md): rules over (format, op) pairs with a
detection bound, the checker families and pins in play, and a fallback
for an op the code does not cover; the search chooses one family per
rule under `check.<rule>.*`, `chialu.eda.checker_gen` regenerates the
checker from a candidate's declaration, and the fault node measures
each rule group at the output seam and at the internal nets its units
declare. `python3 -m chialu.checkers select --formats int16 --ops
add,sub,mul_wide --random-alias 5e-2 --single-bit 1.0 --pdk nangate45`
lists the points that meet a bound, cheapest first from the database's
`checker` kind; `explain`, `floor` and `emit` are the other
subcommands. The `check_en` + `checker.*` spelling remains as the
one-rule form.
A declared family is a label until the text realizes it, and no gate
can check that mechanically, so the run files add the review node
(`chialu.review.<agent>`): a model reads each module the block declares
a family for, with the family's card, and answers per module; the
constraint `review.agree >= 1.0` makes an unfulfilled declaration an
infeasible candidate.
`python3 -m chialu.verify.domain_selftest` binds the smallest run file (the
`RUN` record in that module), renders the four sharing-plan seeds and a
discovered plan, runs them and a replanned candidate through the graph
in ADIR's local executor, and checks the prompt sizes.

## The knowledge pipeline

The unit of registration is the MICROARCHITECTURE rather than the
paper. The family name keys three places: the structural definition in
`chialu/spaces` (families x choices x slots, the machine authority), one
description file per family under `chialu/knowledge/arch/<domain>/
<family>.md` (mechanism, trade-offs, and a `## references` list of paper
handles; `python3 -m chialu.archdocs` lints coverage), and the searched
variables of a run file. Below the family sits the VARIANT level: a
named pin into one design choice (Kogge-Stone is `parallel_prefix` with
`topology: kogge_stone`), documented at `arch/<domain>/<family>/
<variant>.md` with a front matter `family:` + `pin:` that the lint
checks against the spaces. 197 families and 332 variants are in the
knowledge path; 44 families and 96 variants are deferred under
`legacy/knowledge/deferred/` (`docs/deferred-families.md`). All were
documented from the corpus.

Papers survive in two roles. The per-domain bibliographies in
`legacy/knowledge/bib/` are the authoritative handle -> citation record
and key the collected PDFs through `legacy/knowledge/pdf/handles.json` (the corpus sits outside the agent's knowledge base, which holds the cards alone).
`chialu/papers.py` keeps a small curated table of famous named designs
(the RS/6000 LZA, the TPU-v1 MAC, ...), each an `adir.Preset` a run
file applies at a slot as `<path>: {preset: <handle>}`.

Filling the family docs from the corpus is a map-reduce owned by
`chialu/extract.py` (`inventory`, `prompt <handle>`, `run`, `segment`,
`triage`, `run-books`); the methodology is written up in
`legacy/knowledge/extract/README.md`. The corpus tooling's files
(`legacy/knowledge/{bib,extract,notes}`) sit outside the knowledge path
a run file hands the agent (`chialu/knowledge`: the family cards, the
move library and the PDFs).

## Verification

`chialu/verify` covers every variable combination of the three unit
classes from the functional variables alone (docs/formats-and-options.md):
modes over every format family of the grammar, exact references for
every op and option, corner/directed/random stimulus with a
reproducibility freeze, accuracy budgets for approximate units and the
SFU, checker contracts (false alarms, single-bit coverage, alias rate)
at the core/checker seam, and testbenches for combinational,
fixed-latency and iterative units. The generated checker realizes ten
families (`checker.family`): residue, inverse_residue and
multi_residue predict the result's residue from the operands (mod M,
as the complement M - r, or under two or three low-cost moduli),
rns_redundant adds redundant moduli whose disagreement locates the
faulty channel, an_code runs the checker's own replica on operands
premultiplied by A and checks divisibility, parity_prediction_adder
and berger predict the result's parity or ones count from the addends
and a carry replica, parity_prediction_multiplier predicts the product
parity from the partial-product rows and the replica reduction's
carries, reduced_precision compares a narrow replica within its
uncertainty, duplication compares a reference copy bit for bit (three
copies under a majority voter); the comparator slot
(`checker.comparator.family`) realizes the final compare as a two-rail
tree, a k-out-of-2k checker over the pair word or a voter; the ops a
family does not cover are duplicated, and the fault gate's alias bound
follows the family's escape probability, the single-bit floor of the
narrow replicas and the mask count. The nodes in `chialu/eda.py` rebuild
the judges from the `spec.json` the verification files carry, so a
verdict needs nothing but the files.

```
python3 -m chialu.verify.selftest           # 30 specs over the three classes, EDA-free
python3 -m chialu.verify.formats_selftest   # the format grammar and families
python3 -m chialu.verify.domain_selftest    # a checked ALU through ADIR: bind, seeds, and (with EDA tools) the gates and synthesis
python3 -m chialu.verify.smoke_eda          # 20 generated seeds and checkers through verilator/the model
python3 -m chialu.verify.alu_matrix         # 76 ALU instances (every variable dimension) through ADIR: golden, checker, error model, mutants, load errors
python3 -m chialu.archdocs                  # the knowledge lint
python3 -m chialu.targets.rtl.families.coverage  # the generators against the spaces: family, slot, pin, choice, component, name, menu
python3 -m unittest discover -s third_party/adir/tests   # ADIR over its toy domain
```

## Setup

Python 3.10 or newer.

1. `git submodule update --init` and `pip install -e third_party/adir`,
   then `pip install -r requirements.txt`. The verify layer, the domain
   library and the knowledge tools need only pyyaml and mpmath.
2. EDA tools on the machine that evaluates candidates: verilator 11+,
   yosys 0.23+ (with its ABC), the yosys frontend. Liberty files are read from
   `pdk/<descriptor path>` or fetched on first use into `~/pdk`.
3. The loop runtime: CHIA (`pip install -e <your chia clone>`) with a
   ray version it accepts, and SkyDiscover for the LLM backends. Without
   them, ADIR's local executor runs every node in-process, which is what
   the selftests use.
4. Model access is an agent CLI's: `search.models` in the run file
   names `claude`, `codex` or `opencode` and the model, and the call runs
   on the worker that holds the CLI's login (`<agent>_creds`).

## Running

```
E=targets/int_subword_alu.yaml      # or any run file whose module is a chialu template
export THIS_MACHINE=<the EDA host's address>
adir check   $E                     # bind-time checks; problem.md, space.json, graph.json, evaluator.py, skydiscover.yaml under the run dir
chia up      $E                     # the cluster (the cluster keys of the same file; CHIA ignores `adir:`)
adir seeds   $E                     # the sharing-plan seeds through the graph on the cluster (--local: in this process)
adir run     $E --iterations 20     # the search; `chia job submit -- adir run $E` runs it as a ray job
adir status  $E
adir report  $E
```

`adir check` writes the run directory the run file names; every
candidate's record goes to `archive.path` under it (a shared
`results_db.jsonl` is what `ml/surrogate.py` reads). The model is an
agent CLI (`agent: claude | codex | opencode` in the run file) on a
worker with its login. An opencode role takes one setting more than
a claude or codex one, its provider: the run files say `provider:
openrouter` and `model: z-ai/glm-5.3-flash` (`PROVIDER` and `MODEL` in
`targets/make_targets.py`), which ADIR joins into opencode's
`provider/model` and hands to opencode with `small_model` set to the
same id, so opencode's own session-title and summary calls stay on it
(otherwise they go to a provider default, `google/gemini-3.8-flash` on
OpenRouter). opencode reaches the provider with the key of its
credential store (`opencode auth login`, or
`~/.local/share/opencode/auth.json`). `third_party/adir/examples/synth_recipe` and
`synth_recipe_grid` are two smaller runs over one ALU block with the
same tools. The
`ops/hostctl.sh` script deploys this repository to the LAN EDA host
over its bare repositories (`~/chiALU.git`, `~/adir.git`) and launches
runs there in tmux.
