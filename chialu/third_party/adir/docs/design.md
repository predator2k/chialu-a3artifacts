# ADIR design

ADIR is the task layer of an agentic hardware-design search. It describes
what is designed, which quantities the specification fixes and which the
search decides, which CHIA nodes measure a candidate, what a candidate
must satisfy, what a score means, and how every candidate is recorded,
and it hands that description to a search backend as a problem text, an
evaluator and a seed set. Execution belongs to CHIA. Search belongs to
SkyDiscover. Domain content, which is templates, generators, nodes,
knowledge and operator text, belongs to a domain library such as chiALU,
registered in Python under names a yaml file uses. One yaml file carries
the CHIA cluster and the ADIR instance, so `chia up <file>` and `adir run
<file>` read the same file.

## Division of responsibility

| Layer | Owns | Does not own |
| --- | --- | --- |
| CHIA | clusters and logical workers, the node catalog (`@ChiaFunction`s and node types such as gem5 and hammer_vlsi), LLM and agent backends, MCP tools, cache and bypass, database nodes, profiling | the description of the task |
| SkyDiscover | the loop (sample, generate, evaluate, add), the program archive, the search algorithms (AdaEvolve, EvoX, GEPA, OpenEvolve), diff application, checkpoints | what a candidate must satisfy, what a score means, what the model reads |
| ADIR | the pack, variables and their binding times, the evaluation graph derived from the goal and the constraints over node outputs, the score rule, the declaration block, the seed slot, the prompt composer (the skeleton, the slots, the operator sections, the variants, the instructions), the candidate record, the registration API | scheduling, model transport, search algorithms, measurement tools |
| domain library | templates with variables, generators, seed generators, `@ChiaFunction` nodes, presets, knowledge cards, move menus, plan and structure tables (PromptSources), tactic sources, tools, priors | operator and prompt text; anything above |
| the instance (the run file) | the bindings, the artifacts, the nodes, the constraints and the goal, the task file (`task.md`), the variant space and the instruction settings | prompt text beyond the task file |

The rules of the design:

* The search strategy (which candidate to mutate next) is the
  backend's. ADIR supplies the evaluator, the seeds and the records,
  and composes every prompt the solution model reads, and never a
  driver.
* Users and domain libraries write no prompt text. The composer owns
  the skeleton; content comes from the yaml objects, the archive, and
  authored markdown (the task file, the knowledge cards).
* A quantity is a variable, which is an input to elaboration bound at one
  of three binding times, or a metric, which is an output of a CHIA node
  that a constraint bounds or a goal optimizes. Nothing is both.
* The goal and every constraint are expressions over metrics, and the
  set of nodes that runs for a candidate is derived from them. ADIR
  registers no metric, engine, target or workload vocabulary of its own.
* Hard constraints are never scalarized. A scalar score, where a backend
  needs one, follows a declared rule; multi-objective search goes through
  a backend that supports it.
* A prior (a surrogate, a ranking) orders choices and never gates.

---

## 1 The pack

### 1.1 One file

The file has two parts at the top level:

* the CHIA cluster keys, passed through verbatim: `cluster_name`,
  `provider`, `auth`, `available_node_types`, `aws_nodes`,
  `head_start_ray_commands`, `worker_start_ray_commands`, `cache`,
  `bypass`;
* one `adir:` key holding the instance (section 13 lists every field).

`chia up <file>` reads the cluster keys and ignores `adir:`. `adir`
reads `adir:` and also reads `available_node_types` to check that every
resource a node or a model role needs is provided by some worker type.
Where a CHIA release rejects an unknown top-level key, `adir cluster
<file>` writes the cluster part alone to `<run>/cluster.yaml`.

The directory of the run file is on the import path, so `module:`
and a node name resolve a domain library that lives beside the file
(`examples/synth_recipe/chirecipe/`) as well as an installed one;
the cluster connection hands the same path to the workers.

```yaml
cluster_name: chialu_alu
provider:
  head_ip: ${THIS_MACHINE}
auth:
  ssh_user: ${USER}
available_node_types:
  eda:
    resources:
      eda: 8
    num_workers: 1
    compatible_ips: ["${THIS_MACHINE}"]
  evolver:
    resources:
      evolver: 1
    num_workers: 1
    compatible_ips: ["${THIS_MACHINE}"]
cache:
  synth_ppa:
    cache: true
adir:
  module: chialu.ALU
  variables:
    ...
```

Block style is required for the keys under `adir:`; a short record
(`{count: 1, format: fp32}`, `{min: 2, max: 16, step: 2}`) may be a flow
mapping, and a flow mapping inside a scalar list (`["${THIS_MACHINE}"]`)
is CHIA's own form and is passed through.

Everything with behavior lives outside the file: the variables and their
domains, the generators, the seed generator, the presets and the
knowledge root in the domain library the `module` key names, and the
nodes in CHIA's catalog or in the domain library. The file selects among
registered names, binds values and wires node inputs.

### 1.2 Commands

| Command | Effect |
| --- | --- |
| `adir check <file>` | bind-time checks (section 12.2); renders `problem.md`, `evaluator.py`, `space.json`, `graph.json`, the operator templates and the SkyDiscover config into `<run>/`; no cluster needed |
| `adir cluster <file>` | writes the cluster part alone to `<run>/cluster.yaml` |
| `chia up <file>` | brings the cluster up (CHIA reads the cluster keys and ignores `adir:`) |
| `adir seeds <file>` | generates the seed set, evaluates every seed on the cluster when one is up (else in this process; `--local` forces that), writes `<run>/seeds/` with results |
| `adir run <file>` | joins the cluster, runs the seeds when `<run>/seeds/` is absent, then the search; `--iterations N` overrides `search.iterations`, `--resume` continues from the last checkpoint; `chia job submit -- adir run <file>` runs the same as a ray job |
| `adir status <file>`, `adir stop <file>` | progress and graceful stop from another terminal |
| `adir report <file>` | runs the report-only nodes for the front, writes the evidence bundle and the report (section 10.4) |

### 1.3 The run directory

`adir.run_dir` names the directory (default `run/<instance>_<timestamp>`).
It holds:

* `contract.json`: the resolved instance with every hash (section 2.1);
* `space.json`: the bound feature model (section 3);
* `graph.json`: the derived evaluation graph (section 6.3);
* `problem.md`: the rendered problem text (section 7.2);
* `evaluator.py`: the evaluator entry the backend calls (section 9.4);
* `skydiscover.yaml`: the generated backend config (section 9.2), and
  `prompt_templates/`: the backend-side templates the composer parses;
* `seeds/<name>/`: each seed's program and record, and
  `seeds/seed_values.json`, the first seed's measurements;
* `programs/`: every evaluated program by candidate id, which the
  composer reads back as the parent or a context program;
* `prompt_sample.md`: a composed user message for the first seed;
* `instructions.jsonl`: the instruction rows (section 9.5);
* `cache/`: node outputs by content key, and `chia_cache/`: CHIA's
  cache actor's files when the run file has a `cache:` section;
* `chia_eval_log.jsonl`: one line per evaluation (iteration, id, score,
  parent, template and tactic ids, seconds);
* `calls/<stamp>-<id>.json`: one sidecar per solution call in flight (its prompt config, tactic, instruction, parent and directory), taken by the evaluator of that call's program: the client marks the sidecar when the model answers, and the evaluator takes the newest answered one (a call in flight has produced no program, an older answered call whose program never reached the evaluator stays until it expires); a call that fails or answers nothing removes its own; `last_prompt.json` is a copy of the newest
  (section 7.4);
* `results_db.jsonl` or the database node's table: the candidate
  records (section 10);
* `skydiscover/`: the backend's logs, database, `checkpoints/` (the
  resume point) and `best/`;
* `summary.json` (the call counter, the stop reason, the run's
  bounds), `report.md` and `evidence/`.

---

## 2 The instance

An instance is one template of a domain library, bound under the
variables, the artifacts, the nodes, the constraints, the goal and the
search binding of one run.

### 2.1 Identity and hashes

`contract.json` records:

* `unit_id`: sha256 over the template name and every `fixed` and
  `runtime` binding. Two files that bind one template identically share
  archive rows; a searched variable's value is a per-row field
  (`decl.<variable>`, section 9.4), so a comparison that spans a run
  which fixed a variable and a run which searched it is a query over
  `unit_id` and that field.
* `space_hash`: sha256 over `space.json`, which is every variable with
  its domain, its condition, its binding time and, for `search`, its
  narrowed domain.
* `artifact_hashes`: sha256 of every artifact's text, generated or
  supplied.
* `evaluator_hash`: sha256 over the resolved `evaluate` block, and
  `node_hashes`, one per node instance over its node identity and its
  literal inputs.
* `knowledge_hash`: the disclosed knowledge.
* `search_hash`: the generated backend config, the operator templates
  and the prompt templates.
* `model_hashes`: model identifiers and effort per role.
* `pins`: the outputs of pinned nodes as computed on the seed (section
  6.6).

A row in the archive carries `unit_id`, `space_hash`, `evaluator_hash`
and `search_hash`, and every measurement carries the hash of the node
that produced it, so a comparison across runs is a comparison of rows
with equal hashes on the axes held fixed.

### 2.2 Bind order

1. Load the yaml, resolve `${VAR}` from the environment, reject unknown
   keys.
2. Resolve the template through the domain library. Check every
   binding: the binding time is admitted, the value is in the domain,
   the condition holds where the binding time is `fixed`. Expand indexed
   families and presets. Elaborate under the `fixed` and `runtime`
   bindings (ports, submodule tree, index sets created by elaboration,
   dependent domains). Write `space.json`.
3. Materialize artifacts (generators run; files are read and hashed).
   Parse each seed's declaration block and check it against the variable
   table (section 5.3).
4. Resolve every node instance: the node exists in CHIA's catalog or the
   domain library, every input key is a parameter of the node, every
   reference resolves (section 6.2). Derive the evaluation graph from
   the goal, the constraints, `feedback` and `report` (section 6.3);
   check it is acyclic, that every referenced output is one the node
   documents where the node documents its outputs, that no `report_only`
   output is referenced outside `report`, and that every node's
   resources are provided by some worker type. Write `graph.json`.
5. Check the required constraints (section 4.4), every model role has a
   provider, every tool an agentic backend names is registered.
6. Render `problem.md`, the operator templates, `evaluator.py`, the
   seeds and `skydiscover.yaml`; write `contract.json`.

Every step fails with the yaml path of the offending key.

---

## 3 Variables

A variable is a named quantity of a template whose value the template
author does not fix. The template declares each variable with a domain,
the binding times it admits, an optional condition on another variable,
an optional condition per member on a sibling variable, and an optional
index set. The variables with their conditions form a feature model,
which is the term of software product-line engineering for a tree of
choices with cross-tree conditions (Kang et al., FODA, 1990; Czarnecki,
Helsen and Eisenecker, *Staged Configuration Using Feature Models*, SPLC
2004). ADIR exports the bound model in ConfigSpace's JSON form as
`<run>/space.json`.

### 3.1 Domains

| Kind | Domain |
| --- | --- |
| `bool` | false, true |
| `int_range` | lo to hi by step |
| `enum` | a finite set of library objects (formats, rounding modes, ISA names, code definitions, family names) |
| `set` | subsets of a base `enum` |

A composite value is an indexed family of scalar variables (section
3.5) rather than a struct-valued domain.

### 3.2 Binding times

Every variable is bound at exactly one of three binding times. The term
follows Czarnecki and Eisenecker, *Generative Programming* (2000), where
a feature is bound at a stage of configuration and later stages bind
what earlier ones left open. The instance chooses the binding time among
those the template admits.

| Binding time | Who binds | yaml form | Meaning |
| --- | --- | --- | --- |
| `fixed` | the instance | `fixed: <member>` | part of the specification of the unit; the design carries no selection logic for it |
| `search` | the search, once per candidate | `search: all`, `search: [<member>, ...]`, `search: {min, max, step}` | a decision variable of the run; the candidate declares the value it binds (section 3.7) |
| `runtime` | the deployed hardware, per operation | `runtime: [<member>, ...]` or `runtime: all` | a provisioned set; the generated interface carries a selection port over the set, and hardware pays only for the set |

The admitted set is the template author's statement of what kind of
quantity the variable is:

| Kind of quantity | Admits | Example |
| --- | --- | --- |
| what the unit must do | `fixed`, and `runtime` where the interface selects it | the op set of an ALU, an ISA, a code definition, a format set |
| how the unit is built | `fixed`, `search` | a cache's way count or size, an adder's family, a prefix topology, a checker's modulus |
| how much the unit may cost | none: a budget is a metric (section 4), bounded by a constraint or optimized by the goal | a delay bound, an area budget |

Rules:

* `search` binds one member per candidate. The provisioned set of a
  `runtime` binding is always the instance's.
* `runtime` with one member is rejected with the hint to write `fixed`
  with that member.
* Every variable whose condition can hold under the bindings is bound.
  The loader has no defaults, so the file is the complete record.
* A binding creates obligations the generators discharge: a provisioned
  coefficient set ships its precomputed tables, a run-time selectable
  check enable gates the check per operation.
* How a provisioned set is exercised during evaluation (the workload
  selecting through the port, an oracle that measures every member and
  reports the best, a policy program supplied as an artifact and applied
  by the consuming node) is an input of that node rather than a property
  of the binding, so it enters `evaluator_hash` and never `unit_id`.

### 3.3 Binding form

A subword ALU of chiALU:

```yaml
variables:
  ops:                                  # admits fixed, runtime
    runtime: [add, min, mul, fadd, fmin, fmul]
  modes:
    runtime:
      - {count: 1, format: fp32}
      - {count: 2, format: fp16}
      - {count: 1, format: int16}
  accuracy:                             # admits fixed
    fixed: exact
  rounding:                             # admits fixed, runtime; fixed here, no port
    fixed: RNE
  check_en:
    fixed: true
  checker.family:                       # admits fixed, search
    fixed: residue
  checker.modulus:                      # exists iff checker.family = residue
    fixed: 15
  core.adder.family:
    search: [parallel_prefix, carry_lookahead, sparse_prefix_hybrid]
  core.adder.topology:                  # exists iff core.adder.family = parallel_prefix
    fixed: kogge_stone
  core.multiplier.family:
    search: all
  core.subword:
    search: [partitioned_carry_chain, replicated_lanes]
```

A cache:

```yaml
variables:
  line_bytes:
    fixed: 64
  size_kb:
    search: [16, 32, 64, 128]
  ways:
    search: {min: 2, max: 16, step: 2}
  replacement:
    fixed: lru
```

Under `search`, `all` opens the template's whole domain; a list or a
range narrows it, and the narrowed domain is what the problem text
discloses and the declaration check accepts.

### 3.4 Conditional variables

A template declares a condition as `when: (<parent>, <member or
members>)`. The variable is active when the parent's value satisfies
the condition.

| Parent's binding time | Rule for the child |
| --- | --- |
| `fixed` | the child is bound iff it is active; a binding on an inactive child is an error |
| `search` | the child is bound, since it is active in some candidates; its binding applies to every candidate in which it is active, and a `search` binding on the child extends the candidate's decision |
| `runtime` | the child is active when any provisioned member satisfies the condition, and its binding applies to those members |

Conditions are resolved in template order; a cycle is rejected at
registration.

A member condition conditions one member rather than the variable:
`member_when: {<member>: (<sibling>, <allowed members>[, <doc>])}`. The
member stays in the domain, and it is admissible while the sibling holds
one of the allowed members. The sibling is any variable of the template
(a choice of the same family, a choice of another slot, a static
option), written as a template name whose `*` `expand` replaces with the
member's own index. At least one member of the domain stays
unconditioned, so a member condition never empties a domain and a
default always exists; a condition on every member is an existence
condition, which is `when`. The sibling comes before the member in the
variable order, as a parent does, and a cycle is rejected at load. The
sibling's state decides the member:

| Sibling's state | The conditioned member |
| --- | --- |
| `fixed` to `v` | admissible iff `v` is allowed |
| `runtime` over provisioned members | admissible iff every provisioned member is allowed, since the member is built once and serves every run-time selection |
| `search`, decided (a declared value, or the default under the same rule) | admissible iff the decided value is allowed |
| `search`, undecided (the loader, before any candidate) | admissible; the search may still choose an allowed sibling value |
| absent (inactive under its parent, or the index has no such variable) | inadmissible, as a child of an absent parent is inactive |

The loader rejects a `fixed` value or a `runtime` member the bound
siblings exclude; a `search` binding is never checked at load, since
its members are decided per candidate. The default of a conditioned
variable under decided values is the first admissible member, in domain
order (`Bindings.default_of`); the domain's own default is unchanged.
The declaration check (section 5.3), the composer (section 7), the
numeric backends (section 9.2) and the space hash (section 3.5) read
the conditions.

### 3.5 Indexed families

`indexed_by` yields one variable per index value (per format, per
function slot, per program site, per physical structure of a seed).
Elaboration may create the index set (a binary scan producing
`site.<n>`, a seed generator producing `m1.l0`), in which case the yaml
binds the family by pattern before the members exist. A `search`
binding on a family makes every member a decision of its own.

A `*` in a binding's name stands for the index of an indexed variable,
and a pattern over the index narrows the members it binds; a trailing
`*` binds every variable below a prefix, active or not. The most
specific binding wins: an exact name, then an index pattern, then a
trailing-star prefix; a longer pattern beats a shorter one within a
rank. A binding on an inactive variable is an error only under an exact
name, so a prefix pattern may cover variables a fixed parent switches
off.

```yaml
variables:
  core.*:                        # every variable under core, active or not
    search: all
  core.adder.*.family:           # every adder structure
    search: [ripple_carry, parallel_prefix]
  core.adder.m1.*.family:        # the adders of mode 1
    search: [parallel_prefix]
  core.adder.m3.l0.family:       # one structure
    fixed: parallel_prefix
```

A domain library narrows the compiled variables after the fact under
the bound contract, with three fields the loader honors:

* `Enum.excluded` holds the (member, reason) pairs a check removed. The
  member is outside the domain, and the loader, the declaration check
  and `narrow` report the reason beside `outside`, so a binding of a
  removed member names the rule that removed it.
* `Variable.index_domains` maps an index value to the domain that
  index's member takes, where a per-index condition narrows one index
  of a template and not another; `expand` applies it.
* `Variable.search_domain` is the domain a `search` binding narrows
  within, where it is narrower than the domain a `fixed` binding admits
  (a numeric choice a run file may fix but a search never varies).

The space hash covers all three and `member_when` (the sibling and the
allowed members, not the doc), each joining a template's entry only
where the template carries it, so a narrowed or conditioned space is a
new one and an instance without them keeps its hash. `Family.behavior`
classifies a family as `neutral`, `conditional` (with `requires` and
`evidence`) or `selector` for the domain library's checks.

`Space.variables(prefix, times, indexed_by, when, max_depth)` compiles a
family space to variables; `max_depth` stops the recursion into the
component slots (0: the space's own family and choices, 1: also the
slots those open), so a domain may bound the variable count of a deep
space and leave the deeper slots to the text.

The variables stay templates. The loader binds lazily: at load it
materializes the roots and the variables active under each binding's
default view (a fixed value, a search domain's default, every member
of a runtime set), plus every exact-name binding of the run file; any
other variable of the tree (`VariableTree`) is bound when a
declaration, a lookup or a prompt names it, its parents first. A
block that declares a family therefore opens that family's choices
and slots on demand (`Bindings.activate`), and a unit whose full
expansion would run to a million variables loads in seconds with a
few hundred bound. `space.json` holds the full expansion for a numeric
backend, which searches it, and the materialized set for an LLM
backend.

### 3.6 Presets

A domain registers named presets, which are sets of `fixed` bindings
under a path (a paper's design, a vendor's configuration). A mapping
with a `preset` key at a path that is not itself a variable expands
before validation; a preset binding that conflicts with an explicit one
is an error.

```yaml
variables:
  core.adder:
    preset: rs6000_lza
```

### 3.7 How a searched variable reaches a candidate

* The problem text lists every `search` variable with its domain and
  its condition, a conditioned member with its condition (`in_datapath
  (when `core.fp_fma.*.family` is one of [...])`), a nested choice under
  the choice that opens it, together with the coupling statements the
  template supplies (a change of the sharing plan invalidates the family
  choices below it; a family change invalidates the moves applied under
  it), written as a taxonomy rather than a search order. The operator
  section marks a member the parent's decided values exclude.
* The candidate's declaration block carries one `VAR <name>=<member>`
  line per decision that departs from its default (section 5.2). The declaration check
  materializes the block's variables and the ones its values open
  (section 3.5), then validates membership in the narrowed domain and
  activity under the candidate's other declarations.
* A node reads a declared value through the `decl.<variable>` input
  reference or an expression over it (section 6.2): a simulator node
  receives it as its configuration (a cache's way count into gem5), a
  generator node writes the configuration or netlist the value implies
  and hands the text on as an output, a synthesis node reads nothing. A
  generator that depends on a searched variable is therefore a node in
  the graph rather than a bind-time artifact. Whether the candidate's
  text agrees with its declaration is the domain's own check (chiALU
  checks a declared family against the structure it finds), and the
  record marks what was checked.
* Every declared value is recorded as `decl.<name>` (section 9.4), so a
  search strategy and a report stratify by it.

---

## 4 Metrics, constraints, goal

### 4.1 Metric names

A metric is an output of a node instance, named `<node>.<output>`, where
`<node>` is the instance name under `evaluate.nodes` and `<output>` is a
key of the dict the node returns, with further dots for nested keys
(`synth_ppa.area_um2`, `conformance.pass`, `gem5.ipc.605_mcf`,
`hammer.timing.wns_ps`). The unit and the meaning are the node's, as its
documentation states them. No metric is registered anywhere else.

ADIR reserves these names in expressions and input references:

| Name | Meaning |
| --- | --- |
| `decl.<variable>` and the domain's declaration keys | the candidate's declarations |
| `vars.<variable>`, `vars.<variable>.<field>` | a `fixed` or `runtime` binding, or a field of the library object it names |
| `seed.<node>.<output>` | the seed's value of a metric |
| `goal`, `goal.<level>` | the candidate's own objective value, or its value at one fidelity level (`when` conditions only, section 6.4) |
| `archive.<node>.<output>`, `archive.goal.<level>` | the values of a metric, or of a level's objective, over the candidates evaluated so far (`when` conditions only, section 6.4) |
| `candidate`, `candidate.<path>`, `candidate.<path>.<member>`, `candidate.touched`, `artifacts.<path>` | texts (section 6.2) |
| `combined_score` | the score rule's output |
| `error` | present, as 0.0, only on a hard failure |

### 4.2 Values

A value is a number, a boolean, a string, a list or a mapping, as the
node returns it, or an interval record `{mean, lo, hi, n}` from a node
that repeats a measurement (a hardware node, a randomized simulator).
Every value carries a provenance: node name, node hash, and whatever
the node reports about its tools (`synth_ppa.pdk`). Rules:

* Two interval values are compared by interval dominance, and a
  candidate promoted to the front on an interval is re-measured on fresh
  repetitions before the promotion stands.
* A value a node did not produce (the node failed, was skipped by a
  `when` condition, or was cancelled by a hard failure) is `UNDECIDED`,
  which never satisfies a constraint.

### 4.3 Constraints

```yaml
constraints:
  - metric: declaration.ok
    eq: true
    hard: true
  - metric: conformance.pass
    eq: true
    hard: true
  - metric: fault.alias_rate
    le: 0.07
    hard: true
  - metric: synth_ppa.abc_delay_ps
    le: 1000
  - metric: accounting.bytes
    le: 65536
    hard: true
    satisfies: storage_bound
```

* A row is `{metric | expr, le | ge | eq, hard?, satisfies?}`. The left
  side is a metric name or an expression (section 4.5); the right side is
  a literal or an expression, so `le: 1.2 * seed.synth_ppa.area_um2` is a
  relative bound.
* Hard constraints gate: a failing hard constraint stops the evaluation
  and yields `error`. The order of the hard rows is the order in which
  their nodes are scheduled where the data edges leave it free, so the
  yaml lists cheap checks first. A hard verdict is never traded against
  a measurement.
* Soft constraints define feasibility. `UNDECIDED` is infeasible.
* A check that closes a known way of gaming the goal (a semantic tap
  check, a checker-isolation netlist rule, a traffic bound) is a node
  with a hard constraint like any other; the hard-constraint list in
  `contract.json` is the record of which checks were active, so a run
  without one is visibly weaker.

### 4.4 Required constraints

A template declares, per member of a variable, a named requirement that
the instance must discharge with a constraint, because that member
removes an intrinsic check (`accuracy: approximate` removes bit-exactness
and requires `error_bound`). A constraint row discharges a requirement
with `satisfies: <name>`. The loader rejects an instance that leaves a
requirement open.

### 4.5 Goal

```yaml
goal:
  minimize: synth_ppa.area_um2
```

```yaml
goal:
  minimize: synth_ppa.area_um2 * synth_ppa.abc_delay_ps
```

```yaml
goal:
  maximize: geomean(gem5.ipc)
```

```yaml
goal:
  pareto:
    - minimize: synth_ppa.area_um2
    - minimize: synth_ppa.abc_delay_ps
```

An expression is built from metric names, numeric literals, `+`, `-`,
`*`, `/`, `log`, `max`, `min`, and the aggregates `geomean`, `mean`,
`sum`, `min`, `max`, `quantile(list, q)` and `wmean(list, weights)` over
a list-valued or mapping-valued output (the per-benchmark IPCs a
simulator node returns, the per-member outputs of a mapped node), where
`weights` is a mapping-valued literal or a `vars.<variable>.<field>`
reference. An operator between two mappings with equal keys, or between
a mapping and a number, applies member-wise, so a curve divided by a
curve is a curve. A Pareto goal lists directed expressions. A budget appears
either as a constraint row or as an objective, which is the
epsilon-constraint duality of multi-objective optimization (Haimes et
al., 1971).

Feasible-first selection holds regardless of the backend: any feasible
candidate beats any infeasible one, and among feasible ones the goal
decides. This is the constraint-domination rule of Deb (2000).

A goal with fidelity levels replaces the single objective with an
ordered list of directed expressions, cheap to expensive:

```yaml
goal:
  fidelity:
    - minimize: kernel_model.cycles        # analytical model, seconds
    - minimize: kernel_curve.cycles        # kernel-level simulation, minutes
    - maximize: fs.throughput              # full-system simulation, hours
```

* The last level is the level of record: the front and `best/` are
  computed on it.
* A candidate holds values at the levels its nodes reached. Which
  candidates reach a higher level is decided by `when` conditions on
  that level's nodes (section 6.4), so promotion is part of the graph.
* Feasibility at a level is judged on the constraints whose metrics
  that level produces; a constraint over a higher level's metric is
  deferred rather than `UNDECIDED` for a candidate below that level.
* The seeds are evaluated at every level.
* The record carries `fidelity_level`, and the report carries the rank
  correlation between adjacent levels over the candidates measured at
  both, which is the evidence that a lower level ranks like the level of
  record.

This is multi-fidelity optimization as the hyperparameter literature
uses the term (Li et al., Hyperband, 2018).

### 4.6 The score rule

Backends that need a scalar receive `combined_score` from a declared
rule under `goal.score`:

| Rule | `combined_score` |
| --- | --- |
| `ratio_to_seed` (default) | feasible: seed objective over candidate objective for minimize, candidate over seed for maximize; the seed scores 1.0. Infeasible under a soft constraint: 0, or the slack score below. Hard failure: 0. |
| `slack` | `infeasible: slack` gives an infeasible candidate `0.5 * (1 - normalized distance to feasibility)`, strictly below every feasible score; for a candidate a `when` condition screened out (section 6.4), the distance is measured on that condition |
| `weighted` | a declared weighted sum over normalized expressions; discouraged, kept for comparisons with prior work |
| `pareto` | no scalar; the backend's own Pareto mode receives `goal.pareto` as `pareto_objectives` with `higher_is_better`; `combined_score` is still emitted by `ratio_to_seed` on the first expression as the fallback the backend logs |

`ratio_to_seed` makes a backend's stagnation threshold read in the
goal's units: an improvement threshold of 0.01 is one percent of the
seed's objective.

Under `goal.fidelity`, `combined_score` is the score rule on the highest
level at which the candidate has a value, and the seed scores 1.0 at
every level. A backend that ranks on `combined_score` alone therefore
compares an estimate with a measurement, which is the accepted
approximation of multi-fidelity search; the context builder shows
`fidelity_level` beside the score, and a strategy that reads
`Program.metrics` can stratify by it.

---

## 5 Artifacts and the declaration block

### 5.1 Artifacts

`artifacts:` maps a module path to one artifact.

| Key | Values | Meaning |
| --- | --- | --- |
| `role` | `seed`, `fixed`, `baseline`, `input` | seed: candidate 0, the search mutates it (AGENT modules only); fixed: used verbatim, outside the mutable set (GENERATED modules are always fixed); baseline: measured and disclosed, never deployed; input: a fixed program, trace, benchmark set or binary the design acts on |
| `kind` | `text`, `repo` | text: one source file the backend rewrites (diff mode); repo: a checkout the agentic backend edits, whose solution is a diff against `base_rev` |
| `source` | `generated`, `file`, `checkout` | generated: the template's registered generator writes it; file: read from `file`; checkout: `path` at `base_rev` |
| `language` | a string the domain registers | fixes the comment syntax of the declaration block |
| `evolve` | list of module names, file names or globs | the mutable subset; everything else is emitted outside the `EVOLVE-BLOCK` markers, or is outside the diff for a repo |
| `members` or `indexed_by` | a list of names, or an index set of the template | a family: one text per member (a kernel per shape class, a pragma set per site, a trace per co-runner), each generated or read on its own |
| `declaration_member` | a member name | the member that carries the `VAR` lines of a seed family (default the first) |
| `declaration_file` | a path inside a repo artifact | where a repo candidate keeps its declaration block (default `.adir/declaration.txt`) |

Rules:

* No role bypasses the evaluator: a fixed or seed artifact passes the
  hard constraints as a candidate would.
* A GENERATED module rejects user text.
* The mutable set is exactly the `evolve` list of the seed artifacts. The
  binding emits `EVOLVE-BLOCK-START`/`END` around it, so the backend's
  diff mode cannot touch checkers, wrappers or inputs. For a repo, a diff
  hunk outside the `evolve` globs fails the static check `evolve_bounds`
  (section 6.7).
* A seed family is presented to a diff-mode backend as one program with
  one `EVOLVE-BLOCK` per member and split back at evaluation; every
  member is independently mutable, and the record lists the members a
  candidate changed relative to its parent under `touched`.
* `input` artifacts are immutable; a candidate that changes one, or a
  member of one, fails the static check `input_immutable` before any
  node runs. An `input` family with `source: generated` is produced by
  the template's generator once per member (GEMM shapes over a grid,
  co-runner traces from a mix preset).

### 5.2 The declaration block

Every seed and every candidate carries a declaration block in the
artifact's comment syntax, at the top of the mutable region (of the
member `declaration_member` names, for a family) or in
`declaration_file`; a member of a family may carry domain lines of its
own:

```
// ADIR-DECL v1
// VAR core.adder.m1.l0.family=parallel_prefix
// VAR core.adder.m1.l0.topology=kogge_stone
// VAR core.subword.family=partitioned_carry_chain
// STRUCTURE m1.l0.adder kind=adder mode=1 lane=0 width=16 format=int16 ops=add,min group=int_add
// MOVE compare_via_subtract_sign on=m1.l0.comparator
// ADIR-END
```

The block lists decisions, not the whole binding. A `VAR` line
appears where a value departs from its default, which is the first
member of a finite domain or the low end of a range (`Domain.default`);
an active searched variable without a line stands at its default, and a
seed that takes every default declares nothing. A template's
`normalize_declaration(ctx, decl)` completes the block by the domain's
rules before the check reads it: chiALU's copies what any member of a
shared group declares to the group's other members of the same kind, so
one family line per group suffices. The check and the nodes see the
completed values under `decl.<name>`; the record and the prompt keep
the lines as written.

| Line | Defined by | Meaning |
| --- | --- | --- |
| `VAR <variable>=<member>` | ADIR | the candidate's binding of one active searched variable, where it departs from the default |
| any other kind | the domain, through a registered line kind with a parser and a check | a domain declaration; chiALU registers `STRUCTURE` (one physical structure and the shared datapath that realizes it) and `MOVE` (a rewrite applied from its move library); each becomes a `decl.<key>` metric as its parser says |

A language without a structural vocabulary (a prefetcher in C++, a
Chisel tree) carries `VAR` lines and whatever line kinds its domain
registers.

### 5.3 The declaration check

The declaration check is the node `adir.declaration`, which ADIR ships
and which is always the first node of the graph. Its outputs are `ok`,
`detail`, and one `decl.<key>` per declaration.

| Check | On failure |
| --- | --- |
| the block is present and well-formed | `declaration.ok` is false; nothing else runs |
| every `VAR` names an active searched variable and every value is in the narrowed domain; an active variable without a line takes its default (`defaulted` lists them, `detail` counts them) | as above |
| every declared or fixed member is admissible under the block's other values (section 3.4): a rejected line reads `VAR core.unpacker.m0.denormal_handling='in_datapath': 'in_datapath' is admissible when core.fp_fma.m0.family is one of [...]; it is 'separate_multiplier_and_adder' (...)`; an undeclared variable whose first member the values exclude takes the first admissible one, and `defaulted_under` names it with the sibling and its value | as above |
| every domain line passes its registered check | as the domain's check says |
| a line kind is neither `VAR` nor registered | as above |

A declaration is a declaration. The record marks what a check verified;
a value no check verifies (a family label without a structural check) is
recorded as declared and is a prior for the reader and a field for the
strategy, never a verified fact.

---

## 6 The evaluator

### 6.1 Nodes

A node is a CHIA node: a `@ChiaFunction` of a domain library
(`chialu.eda.synth_ppa`, `chialu.eda.conformance_bundle`) or a node type
CHIA ships (gem5, hammer_vlsi). A node takes keyword inputs and returns
a dict of outputs; its resources, its cache and its bypass are CHIA's.
ADIR ships two nodes: `adir.declaration` (section 5.3) and
`adir.instance` (section 6.9).

`evaluate.nodes.<name>` instantiates a node under a name:

```yaml
evaluate:
  nodes:
    declaration:
      node: adir.declaration
    conformance:
      node: chialu.eda.conformance_bundle
      inputs:
        rtl_text: candidate
        files: artifacts.verify_bundle
    fault:
      node: chialu.eda.fault_bundle
      inputs:
        rtl_text: candidate
        files: artifacts.verify_bundle
        checker_rtl: artifacts.checker
    synth_unit:
      node: chialu.eda.synth_unit
      inputs:
        rtl_text: candidate
        structures: decl.STRUCTURE
        pdk: nangate45
        clock_ps: 1000
        effort: medium
    synth_ppa:
      node: chialu.eda.synth_ppa
      inputs:
        rtl_text: candidate
        top: alu_core
        pdk: nangate45
        clock_ps: 1000
        effort: medium
        timeout_s: 1200
      when:
        - conformance.pass
        - synth_unit.area_um2 le 1.2 * seed.synth_unit.area_um2
  feedback: [conformance.detail, synth_ppa.detail, synth_ppa.critical_path]
```

| Key | Meaning |
| --- | --- |
| `node` | the node's name in CHIA's catalog or the domain library |
| `inputs` | keyword inputs: expressions over references and literals (section 6.2); every key is a parameter of the node |
| `map_over` | parameters mapped over lists; one run per element of the product (section 6.8) |
| `when` | conditions over metrics; the node runs only when all hold (section 6.4) |
| `report_only` | the node runs at report time for the front only (section 6.5) |
| `pin` | the node's outputs are computed on the seed and reused (section 6.6) |
| `resources` | an override of the node's resource request, passed to CHIA |

Two instances of one node under different names are two nodes (a
`gem5_train` and a `gem5_heldout` with different benchmark lists; a
`synth_fast` and a `synth_full` with different efforts), and their
outputs are distinct metrics with distinct hashes.

### 6.2 Inputs

An input is an expression in the language of section 4.5 over the
references below and literals; a bare literal or a bare reference is the
degenerate expression, and a quoted string
(`"'openrouter/deepseek/deepseek-v4.1-flash'"` in yaml) is a literal
whatever it contains. The value of the expression, rather than its
text, enters the node's input set, its node hash and CHIA's cache key,
so a node whose inputs are a projection of the declarations (a
scratchpad capacity computed from a size, a way count and a converted
way count) is cached under the projection, and two candidates that
agree on the projection share the run. `adir check` type-checks every
expression against the domains of the variables and the documented
outputs it references.

| Reference | Value |
| --- | --- |
| `candidate` | the assembled text of the unit: the seed artifacts with the candidate's mutable region, plus the fixed artifacts |
| `candidate.<path>` | the candidate's text of one artifact path; for a family, the mapping of member texts |
| `candidate.<path>.<member>` | one member's text |
| `candidate.touched` | the members whose text the candidate changed against its parent, before any replan (the evaluator entry computes them); `[]` for a seed. A node that judges the agent's own writing reads these alone |
| `artifacts.<path>`, `artifacts.<path>.<member>` | the text of a fixed, baseline or input artifact, or of one of its members |
| `<node>.<output>` | a data edge from another node instance; a mapped output arrives as a mapping |
| `seed.<node>.<output>` | the seed's value of a metric, for relative conditions and bounds |
| `goal`, `goal.<level>` | the candidate's own objective value, or its value at one fidelity level; legal in `when` only |
| `archive.<node>.<output>`, `archive.goal.<level>` | the list of a metric's values, or of a level's objective values, over the candidates evaluated so far; legal in `when` only |
| `decl.<variable>` or `decl.<key>` | the candidate's declared value; for the root of an indexed family (`decl.site`), the mapping of its members' values |
| `vars.<variable>`, `vars.<variable>.<field>` | a `fixed` or `runtime` binding; for an `enum` member that is a library object, one of its fields (`vars.mix.weights`), which the domain defines and `unit_id` hashes with the member |
| anything else | a literal, passed as is |

### 6.3 The derived graph

The nodes that run for a candidate are exactly those whose outputs the
goal, the constraints, `feedback` or a `when` condition reference, plus
their transitive inputs. A node instance nothing references never runs.
`graph.json` records the graph.

Scheduling:

* data edges fix a partial order, and `adir.declaration` precedes
  everything;
* among nodes the data edges leave unordered, the nodes of hard
  constraints run in the order of the constraint rows, and every other
  node runs after them, so a hard failure cancels the expensive nodes;
* a failing hard constraint cancels every node not yet started; the
  candidate's record holds what was measured, plus `error` and the
  failing node's `detail` as `stderr` (section 9.4);
* a node whose inputs include an `UNDECIDED` value is skipped, and its
  outputs are `UNDECIDED`;
* a mapped node (section 6.8) is one run per member, each scheduled and
  cached on its own;
* nodes with no unmet dependency run concurrently within `parallel`
  (section 9.6); CHIA schedules them on the workers whose resources
  they request.

### 6.4 Conditional nodes

`when` lists conditions of the form `<expr> le | ge | eq <expr>` or a
bare boolean metric. The node runs only when every condition holds
under the values already produced; otherwise its outputs are
`UNDECIDED`. This is how a cheap node screens an expensive one, which is
cascade evaluation as OpenEvolve and AlphaEvolve use the term: a
synthesis of the touched structures screens the full synthesis, a
quick simulation on one benchmark screens the suite. A candidate whose
goal metric is `UNDECIDED` because a `when` held it back is infeasible
and scores by the score rule's infeasible branch, unless the goal has
fidelity levels (section 4.5), in which case the candidate keeps the
level it reached.

A condition may compare against the run's archive through
`archive.<node>.<output>`, which is the list of that metric's values
over the candidates evaluated so far, with `quantile`; under fidelity
levels, `goal.<level>` and `archive.goal.<level>` compare the level's
objective the same way (`goal.1 ge quantile(archive.goal.1, 0.8)` for a
maximized level):

```yaml
kernel_curve:
  node: gem5_kernel
  map_over:
    sp_capacity_kb: [64, 128, 256, 512, 1024, 2048]
  inputs:
    binary: build.binary
    sp_banks: decl.sp.banks
  when:
    - conformance.pass
    - kernel_model.cycles le quantile(archive.kernel_model.cycles, 0.2)
```

The candidate reaches the expensive node when it ranks in the top fifth
of what the cheaper node has measured by then. That is asynchronous
successive halving (Li et al., 2018): a promotion decided at evaluation
time from the candidates seen so far, without waiting for a rung to fill
and without updating any record in place. While the archive holds only
the seeds, the seeds' values are the distribution.

### 6.5 Report-only nodes

`report_only: true` marks a node that runs once, for the members of the
front, at `adir report`. Its outputs may appear under `report` only; a
reference from the goal, a constraint, `feedback`, a `when` condition or
a tactic source fails the static check `report_only_isolation` at bind
time. Held-out benchmarks are a report-only simulator instance:

```yaml
evaluate:
  nodes:
    gem5_train:
      node: gem5
      inputs:
        config: artifacts.champsim_config
        prefetcher: candidate
        benchmarks: [602.gcc_s-734B, 605.mcf_s-472B, 623.xalancbmk_s-10B]
        warmup_instructions: 5000000
        simulation_instructions: 25000000
    gem5_heldout:
      node: gem5
      inputs:
        config: artifacts.champsim_config
        prefetcher: candidate
        benchmarks: [619.lbm_s-4268B, 620.omnetpp_s-874B]
        warmup_instructions: 5000000
        simulation_instructions: 25000000
      report_only: true
  report: [gem5_heldout.ipc]
```

### 6.6 Pinned nodes

`pin: true` marks a node whose outputs are computed once, on the seed,
after the hard constraints that bound them pass, and recorded under
`pins` in `contract.json` (an algorithm model's coefficient table, a
golden program, a vector set). Every later evaluation receives the
pinned outputs rather than recomputing them, and a consumer that embeds
a pin's hash refuses on mismatch. A candidate whose declarations change
an input of a pinned node (a `decl.*` reference in its `inputs`)
recomputes the node and re-passes its constraints before any other node
runs.

### 6.7 Static checks

Three checks need no node and run before the graph:

| Check | Fails when |
| --- | --- |
| `input_immutable` | a candidate changes an `input` artifact or a member of one |
| `evolve_bounds` | the text outside the mutable set differs from every seed's and from the parent's (a parent the template re-rendered for a new plan carries a fixed part of its own, which its children inherit; a re-rendered candidate itself passes) |
| `report_only_isolation` | a `report_only` output is referenced outside `report` (checked at bind time) |

### 6.8 Mapped nodes

`map_over` maps one or more parameters of a node to lists. The node
runs once per element of the Cartesian product, and each output becomes
a mapping keyed by the member:

```yaml
kernel_curve:
  node: gem5_kernel
  map_over:
    sp_capacity_kb: [64, 128, 256, 512, 1024, 2048]
  inputs:
    binary: build.binary
    shapes: artifacts.shapes
    sp_banks: decl.sp.banks
  when: [conformance.pass]
# outputs: kernel_curve.cycles.64, kernel_curve.cycles.128, ...
```

Rules:

* A `map_over` key is a parameter of the node and does not also appear
  under `inputs`. A value is a literal list or a list-valued expression.
* Each member is one run with its own hash, provenance and cache entry,
  so a grid characterized once for a text is looked up by every later
  candidate that reaches any subset of it.
* `when` applies to the node as a whole.
* The aggregates of section 4.5 apply to a mapped output, and a
  downstream node may take the whole mapping as one input (a partition
  node over a curve of cycles against capacity).
* `map_over` composes with `pin` and `report_only`.

The form is the map combinator of workflow languages (Snakemake
wildcards, Airflow task mapping).

### 6.9 Sub-instance nodes

`adir.instance` runs another ADIR file as a node, which is how a
bilevel search is written as a graph rather than as a driver: the outer
instance decides the hardware, the inner one the software, and an inner
run repeats only when an outer change reaches it.

```yaml
kernel_opt:
  node: adir.instance
  inputs:
    file: sub/cacheflex_kernel.yaml
    bindings:
      l2.sp_capacity_kb: decl.l2.size_kb / decl.l2.ways * decl.l2.sp_ways
      sp.banks: decl.sp.banks
    budget: {iterations: 60, wall_hours: 2}
# outputs: kernel_opt.best.<metric>, kernel_opt.best.sha256, kernel_opt.front,
#          kernel_opt.iterations, kernel_opt.cost
```

Rules:

* `bindings` maps inner `fixed` variables to expressions over the outer
  candidate. The inner file's `search` variables are disjoint from the
  outer's, and a name in both is rejected.
* The node's inputs are the values of `bindings` and the inner file's
  `space_hash`, `evaluator_hash` and `search_hash`, so an inner run is
  cached under them: an outer candidate that projects onto bindings
  already solved is a cache hit.
* The inner run's directory is `<run>/sub/<hash>/`; its archive is
  linked from the outer record under `sub`, and its best candidate's
  hash is an outer measurement with provenance.
* The inner run's budget counters are charged to the outer run.
* The inner file's cluster keys are ignored; the inner run uses the
  outer cluster.

---

## 7 The prompt composer

The composer owns every prompt the solution model reads: the section
order, the wording, the response format, the declaration-block and
EVOLVE-BLOCK rules. Users and domain libraries write no prompt text.

### 7.1 Inputs

| Source | Content | Where it lands |
| --- | --- | --- |
| the yaml objects | the template and variable docs, the `fixed` and `runtime` bindings, the searched variables with their domains and conditions, the constraints, the goal, the score rule, the node schedule, the seeds' declarations and baselines | the system text |
| the evaluation and the archive | the parent (its declaration block, its metrics, its program text, its feedback artifacts), the context programs, the previous attempts, a tactic, a prior table, the backend's own notes (retry error, paradigm, sibling context) | the user message |
| authored markdown | the instance's task file (`task: {context: task.md}`) and the domain's knowledge cards under `knowledge: <path>` | the task slot; the knowledge slot names the path |
| domain data | PromptSources the library registers and the run file selects (`search.prompts.sources`): an interface (static), a structure table, a plan table, a move menu (per round) | the domain slots |

### 7.2 The skeleton

The system text (`problem.md`, the same every round) holds these slots
in this order:

| Slot | Content |
| --- | --- |
| `role` | who the model is: the run file's `role.file` text or `role.script` rendering; first, so every call's system text starts with the same bytes (no title: a template name is not what the model needs first, and a changing prefix defeats the prompt cache) |
| `conduct` | the rules of a round (second, before the task) |
| `task` | the task statement: the discover role's brief when it exists, else `task.script` rendered from the instance, else the `task.context` file |
| `unit` | the `fixed` and `runtime` bindings in words, the elaboration's info; a fixed binding the elaboration names under `info["prompt_omit"]` (an option that does not apply to the bound unit) is counted rather than listed |
| `decisions` | the searched variables: an indexed family is one line with its instance count, a family root lists its members, and the choices a member opens are named under it with their domain sizes |
| `domain_static` | the static PromptSources |
| `rules` | the constraints (hard or soft), the goal, the score rule, the nodes in schedule order with their `when` conditions |
| `format` | the declaration block and the EVOLVE-BLOCK rule |
| `knowledge` | the knowledge base path and how to use it |
| `seeds` | each seed's declarations, the difference of its domain lines from the first seed's, goal, score and feasibility |

The user message of every round holds these slots in this order:

| Slot | Content |
| --- | --- |
| `current` | the parent: its score line, the program file in the call's directory (section 7.7) with its mutable regions, the region in focus, and the index of the round's files (`context/parent.md` with the declaration block and the metrics, the per-round sources, the feedback artifacts to `feedback_depth`, the context programs and their `.md`, the members) |
| `context` | `context_programs` other evaluated candidates, each to `show`: the declaration block, the metrics, the text |
| `history` | the backend's previous-attempts summary |
| `domain` | the per-round PromptSources (off under `show_plan_table: false`) |
| `operator` | the operator section of `operator` (section 8.2) |
| `tactic` | one tactic (section 9.5) |
| `guidance` | the instruction in force (section 9.5) |
| `backend` | the backend's own notes, their headings one level down: a retry's error and failed response, AdaEvolve's paradigm guidance and sibling context; the knowledge card index under `knowledge_depth: index` |
| `response` | the response format: SEARCH/REPLACE blocks under `diff_mode`, the complete program otherwise |

The skeleton is immutable: no knob, instruction, PromptSource or
override changes a slot's position or wording; they fill slots.

### 7.3 Per-role composition

| Role | What the model receives |
| --- | --- |
| `solution` | the composed system text and user message; the backend's rendering is parsed for the parent's id, the context ids, the previous attempts and the backend's notes, and discarded otherwise |
| `guide` | the system text and the backend's own request (AdaEvolve's paradigm generator, EvoX's summaries) |
| `strategy` | the reflection prompt of instruction evolution (section 9.5) |
| `discover` | the system text, the domain's per-round sources with no parent (the structure table), the template's plan grammar (`plan_doc`) and the ask for N plans in one json block; section 8.1 |
| `summary` | the system text and the backend's request, passed through |

### 7.4 The prompt config

The knobs of the composer, their admitted values and their defaults:

| Knob | Values | Default |
| --- | --- | --- |
| `operator` | `structural`, `local`, `free` | sampled over the three |
| `show` | `path`, `declarations_metrics`, `declarations_only`, `full` | `search.context.show`, else `path`: the current program is named by its file (`<run>/programs/<id>.<ext>`, with its region names) for the agent to read, and a context program by its declarations, metrics and file; `declarations_metrics` and `declarations_only` name the current program by its file too and show a context program by its declarations (and metrics) without its file; `full` inlines every text, which for a structure-rich domain runs to hundreds of thousands of characters |
| `context_programs` | a non-negative integer | `search.context.programs` |
| `feedback_depth` | `none`, `summary`, `full`, `files` | `full`; `summary` cuts a text artifact to 400 characters at a line end and replaces a table artifact longer than that by its entry count, `full` cuts at 4000 (the whole text goes to `feedback/<key>.txt` of the call directory above the cap), `files` writes every artifact whole to that file and inlines one index line each |
| `member_focus` | `none`, `one`, `all` | `none`: the structural decisions list the first 24 active variables; under `one` a region of the program is drawn (a family's member, else a region `evolve` names), preferring the regions the template's `focus_map(ctx, parent)` ties to variables, and the operator, the structural decisions and the PromptSources (`render(..., focus=<region>)`) address that region alone; under `all` every structure's family and the choices the parent declares are listed and the undeclared choices counted |
| `show_plan_table` | a boolean | `true` |
| `knowledge_depth` | `path`, `index`, `cards` | `path`: the system text names the `knowledge/` copy of the call directory with one line on its layout (the card count, the top-level directories, the domains under `arch/`), and the agent lists it and reads what it needs; `index` lists the 40 nearest cards and `cards` inlines up to 16,000 characters, both ranked by the region in focus's variables, then the parent's declared values, then every searched member |
| `decisions` | `kinds`, `families`, `choices` | `kinds`: one line per top-level decision, an indexed family with its instance count and its members, the choices and nested slots under a member counted (they stand at their defaults, their cards name them); `families` adds the nested roots; `choices` names every choice under every member; both are cut at 400 lines with the count of the rest |

`search.prompts.variants` maps knobs to value lists; one combination
is sampled per iteration (`sample: uniform` or a UCB over the child
improvement each combination produced in the last `window` records).
The sampled combination, the tactic id and the instruction id form the
iteration's `prompt_config`, recorded in the candidate record and in
`chia_eval_log.jsonl`. `adir seeds` writes `prompt_sample.md`, a
composed user message for the first seed, so the composition can be
read before a run.

### 7.5 Knowledge

```yaml
knowledge: chialu/knowledge     # a directory of markdown cards
```

The system text names the directory as the agent sees it, `knowledge`
inside the call's directory (section 7.7), and tells the model to read
the cards it needs. `knowledge_depth: path`, the default, names the
directory alone; `index` lists the card files; `cards` inlines the
cards into the user message, the ones named by the parent's declared
values and the searched members first, up to 16,000 characters. The knowledge root's layout is the
domain's, and a lint the domain supplies checks that every member of a
searched domain has a card.

### 7.6 The role and the task

```yaml
role:
  file: prompts/role.md          # who the model is; or `script: <path>.py` / `module:function`
task:
  context: task.md               # beside the run file: the author's statement, or the brief's input
  script: ../chialu/task.py      # or: a script that renders the statement from the bound instance
  author: discover               # optional: the discover role writes the brief the rounds carry
```

The role is the system text's first section: the run file names a
markdown file or a script, and the text opens every call identically.
The task is the statement of the problem, the system text's third
section after the conduct. `task.context` is a file the author wrote;
`task.script` is a Python file defining `render(instance) -> str` (or
`module:function`), rendered once per instance from its bindings,
elaboration, goal and constraints, so a new target needs no hand-written
statement; a leading `# heading` line of either text is dropped, since
the section has its own. Both hashes are in `contract.json`.

Under `task.author: discover` the slot carries a brief the discover
role writes instead: one call before the seeds, from the system text's
facts, the domain's structure table and the author's own notes, into
`<run>/task_brief.md`, with the exchange in `task_brief_prompt.md`; a
later `adir seeds` reads the file rather than asking again. A brief,
whoever writes it, follows this outline, one short paragraph per
heading:

```
    ## Objective                                what is minimized, under which bound, on which library
    ## The unit                                 the modes, the ops, the lanes, the fixed conventions that matter
    ## What varies                              the structures, the families per kind, the sharing plan, the choices
    ## What the evaluation rewards and rejects  the gates in order, the soft bound, the score rule
    ## Pitfalls                                 what fails conformance or the checker, what inflates area or delay
    ## Where to start                           where the area and the delay sit in the seed, the first moves
```

### 7.7 The agent's directory

Every model call runs in, and is pointed at, a directory of its own,
`<run>/agent/<stamp>-<id>-<parent or role>/`. The rest of the run
directory, with its archive, logs and every candidate, is not named to
it, and nothing in the directory is a link: every file the agent can
read is the call's own copy. The directory holds:

* `knowledge/`, a copy of the knowledge base
* `program<ext>`, a copy of the parent's program (a solution call), and
  `members/<name><ext>`, one file per member of a family program
* `context/<id><ext>`, a copy of each context program the round names,
  and `context/<id>.md`, its declaration block and metrics
* `context/parent.md`, the parent's declaration block, its metrics per
  node and its unsatisfied constraints
* `context/unit.md`, `context/decisions.md`, `context/seeds.md`: the
  unit's fixed and run-time options, the decisions open to the agent,
  the seeds table
* `context/<source>.md`, one file per PromptSource the run file names
  (static or per round)
* `feedback/<key>.txt`, the parent's feedback artifacts (every one
  under `feedback_depth: files`, the ones above the cap otherwise)

The prompt inlines what the agent needs to act without reading: the
task, the metrics, constraints and goal, the conduct, the declaration
block's form, the parent's score line, the program file's name and its
mutable regions, the region in focus, the operator, the ambition, the
tactic and the response form. Everything else is a file, and the
prompt carries an index of the files, one line each with the path
relative to the directory, the size and what it holds: the system text
indexes the static files under "Files of this call", the user message
names the directory and indexes the round's files under "Current
program". Without a call directory (`problem.md`, the discover role)
the same sections render inline.

The claude node gets the directory as `--add-dir`, the codex and
opencode nodes as their working directory; opencode's
`external_directory` permission is denied, so its file tools stay
inside (a read outside is refused with the rule quoted), `edit`, `bash`
and `webfetch` are denied, and `doom_loop` is denied so a tool call
repeated three times with the same input fails at once rather than
waiting for an answer no one gives. The copies are byte-identical to
the run's files, so a SEARCH block matched against the copied program
matches the program the evaluator applies it to.

---

## 8 Seeds, operators, priors

### 8.1 Seeds

```yaml
search:
  seeds:
    generated: [baseline, packed_banks, per_position, dedicated_speed]
    files: [seeds/stride.cc, seeds/best_offset.cc]
    discover: 0                    # ask the discover model for N further plans before the run
    rank:
      prior: structure_area        # a registered prior (section 8.3)
      top: 3
```

* `generated` lists names the template's seed generator accepts; the
  names and their meaning are the domain's (chiALU's names are sharing
  plans over the open structures, each rendered into a `VAR` set and a
  `STRUCTURE` table).
* `discover: N` asks the `discover` model role, once before the seeds
  (or a mapping `{count: N, sharing_only: true, keep_families: [...]}`,
  under which the role names sharing alone, the `shared` groups and the
  `components`, no pin and no family but one a kind of sharing itself
  needs, and the numeric stage chooses the rest)
  run, for N further plans. The prompt is the system text, the
  per-round PromptSources with no parent (chiALU's structure table),
  the template's `plan_doc` (the plan grammar as data: chiALU's names
  shared groups with members, a family and pins, per-structure and
  unit-level families) and the request for one json block of named
  plans. Each plan goes through the template's `plan_seed(ctx, name,
  plan)`, which renders it as a seed or raises; the plans kept are
  written to `<run>/discovered.json` with the rejections and run as
  seeds after the listed ones, under their names. A second `adir
  seeds` reads the file rather than asking again. `rank.top` keeps
  the top N of every seed, the discovered ones included, so it is set
  to the seed count where every plan is to run.
* Every seed carries a declaration block, is evaluated on the full graph
  and enters the archive before iteration 1. The first seed's values are
  what `seed.<node>.<output>` refers to, so the listed seeds come first.
* Seeds carry the large structural variety; the operators carry the
  small steps. A candidate may still change the plan: when its
  declaration regroups structures, the template's `replan(ctx, decl,
  parent_decl)` re-renders the affected regions from the declaration
  (chiALU renders the behavioral seed of the new partition, the top and
  the regrouped units fresh) and names the regions whose text the
  parent keeps; the candidate's `VAR` lines stay. The record carries
  `replanned`. `search.replan: false` turns the hook off for an ablation: a candidate keeps the text the model wrote, so a changed declaration must be realized by that text.

### 8.2 Operator sections

The composer renders one operator section per iteration, chosen by the
`operator` knob. The three labels are EvoX's:

| Label | Rendered from |
| --- | --- |
| `structural` | the parent's active decisions (declared, or at their defaults) with their alternatives, the parent's value marked; under `member_focus: one` the decisions of the region in focus alone, named as the region to change; and the registered prior's predicted goal per alternative where a prior exists |
| `local` | the instruction to keep every declaration and rewrite within the region from the feedback, the region in focus alone under `member_focus: one`; the domain's data (move menus, plan tables) comes through PromptSources and tactic sources |
| `free` | the request to improve the candidate with the block kept consistent |

A domain supplies data rather than text: it registers a `PromptSource`
(name and renderer, the shape of a `TacticSource`) for a move menu, a
plan table or a structure table, and the run file selects sources by
name under `search.prompts.sources`.

```yaml
search:
  operators:
    override: prompts/operator.md    # the escape hatch: one file replaces every operator section
```

The override is a file beside the run file; `{parent_declarations}` in
it is filled. It is not the default.

### 8.3 Priors

A domain may register a prior, which is a function from a declaration
set to a predicted objective with an interval (a structure-grain area
surrogate, a table of measured families). Its uses are listed under
`search.seeds.rank` and in the `structural` template. Rules:

* A prior never gates and never replaces a measurement in a row.
* An analytical model (a tiling model, a miss-rate estimator, a
  gate-count estimate) is a node whose output is a low-fidelity
  measurement rather than a prior: as a node it screens through `when`
  and ranks as a fidelity level, and a prior can do neither.
* A request outside the prior's range returns a wide interval, and the
  consumer treats a wide interval as no prior.
* The report carries the prior's predicted-versus-measured table and
  the rank correlation over evaluated candidates.
* Training data and models are the domain's (chiALU's `ml/`).

---

## 9 The search binding

### 9.1 Backend inputs

ADIR gives SkyDiscover four inputs and reads the results back through
its own evaluator entry.

| Input | SkyDiscover entry | ADIR source |
| --- | --- | --- |
| problem text | `prompt.system_message`, the file `problem.md` | section 7.2 |
| evaluator | `evaluator.py` with `evaluate(program_path)` | sections 6 and 9.3 |
| seeds | the first seed's program is `initial_program`; every seed of `adir seeds` is added to the backend's database before iteration 1 with its record's metrics and feedback, one seed per island under AdaEvolve; the backend's own evaluation of `initial_program` at start (a program handed over from `<run>/seeds/` itself) gets that seed's record back rather than a second archive row, and takes no call's sidecar | section 8.1 |
| config | `skydiscover.yaml`, a SkyDiscover config file: `Config.from_yaml` loads it and `skydiscover-run` accepts it unchanged | section 9.2 |
| records (out) | the archive and `chia_eval_log.jsonl`; the backend's own database, logs, checkpoints and best program under `<run>/skydiscover/` | section 10 |

### 9.2 Backends and the generated config

```yaml
search:
  backend: adaevolve         # adaevolve | evox | topk | beam_search | best_of_n | openevolve | gepa | shinkaevolve | random | grid
  iterations: 200
  parallel: 3
  parallel_nodes: 6          # nodes with no unmet dependency run at once, up to this many
  eval_timeout_s: 3600       # one candidate through the whole graph
  database:                  # backend-specific keys, passed through
    use_migration: true
    diversity_strategy: metric
  diff_mode: true
  max_solution_bytes: 400000
  retries: 2                 # error retries with the failing node's detail as feedback
  budget:
    wall_hours: 24
    node_runs: 1500
    llm_calls: 600
  stop:
    plateau_iterations: 60
```

`adir check` writes `skydiscover.yaml` from these keys:

| ADIR key | SkyDiscover key |
| --- | --- |
| `backend` | `search.type`; `openevolve`, `gepa` and `shinkaevolve` need their packages |
| `iterations` | `max_iterations`; `adir run --iterations N` overrides it for one run |
| `parallel` | `evaluator.parallel_evaluations` |
| `retries` | `search.database.max_error_retries` under AdaEvolve |
| `diff_mode`, `max_solution_bytes` | `diff_based_generation`, `max_solution_length` |
| the seed artifact's language | `language`, `file_suffix` |
| `database` | `search.database.*`, after `db_path`, `num_islands` (the seed count) and, under a Pareto goal, `pareto_objectives: [goal.1, ...]`, `higher_is_better` and `fitness_key: combined_score` |
| `context.programs` | `search.num_inspirations` |
| `eval_timeout_s` | `evaluator.timeout` (default 3600); `cascade_evaluation` is off and `max_retries` is 0, since ADIR's record is the retry convention |
| `models.solution`, `models.guide`, `models.evaluator` | `llm.models`, `llm.guide_models`, `llm.evaluator_models`; another role goes to `guide_models` when no guide is given |
| `models.<role>.model`, `weight`, `effort`, `timeout_s` | the entry's `name`, `weight`, `reasoning_effort`, `timeout`; `init_client` is ADIR's, so the entry's own client is never built |
| `llm_timeout_s`, `max_tokens` | `llm.timeout`, `llm.max_tokens` |
| `models.<role>.max_output_tokens` (opencode) | no entry: the call's `OPENCODE_EXPERIMENTAL_OUTPUT_TOKEN_MAX` (default 262144), which opencode's own 32000 cap on output, reasoning included, would otherwise hold |
| `checkpoint_interval` | `checkpoint_interval` (default 5) |
| the backend | `prompt.template` (`evox` under EvoX, else `default`) and `prompt.template_dir: <run>/prompt_templates`, which holds ADIR's `diff_user.txt` and `full_rewrite_user.txt` |

The generated file is hashed into `search_hash` and never edited by
hand. `operators`, `prompts`, `tactics`, `instructions`, `budget`,
`stop`, `context.show` and `tools` have no SkyDiscover entry; they stay
in `contract.json` and act through the model client (section 9.5) and
the watcher of the run (section 9.6).

Backend notes:

* AdaEvolve: islands, UCB, migration and paradigm breakthroughs are the
  backend's; `num_islands` is the number of seeds, one seed per island,
  so the islands start apart.
* EvoX: the co-evolution manager evolves a search strategy beside the
  solution; the `guide` role is its summary model. With
  `search.operators: domain` the run file sets
  `database.auto_generate_variation_operators: false`, and the rendered
  templates are the operator set. The skydiscover 0.1.0 wheel does not
  ship `search/evox/config`, so EvoX runs only from a build that does.
* `claude_code`: an agentic CLI editing a `repo` artifact with the tools
  under `search.tools`. The yaml binds; `adir run` does not start it in
  this version.
* `random` and `grid`, and any optimizer that reads `space.json` and
  returns a declaration: a numeric backend never sees text. The
  candidate is a declaration block alone, so the evaluator entry, the
  graph, the constraints, the score rule and the record are unchanged;
  every artifact is `fixed`, `baseline` or `input`, every text a
  searched variable implies is a node output, and a `seed` artifact
  fails at bind time. The seeds' declarations are the initial design.
  `smac` runs SMAC3's hyperparameter-optimization facade over the
  ConfigSpace built from `space.json` (categoricals for finite domains,
  integers and floats otherwise, `InCondition` for a conditional whose
  parent is searched, a forbidden conjunction of the member and the
  sibling's disallowed values for a member condition); `nsga2` runs
  pymoo's NSGA-II over the same space as mixed variables with the
  feasibility as an inequality constraint. Every backend's assignment
  passes one pruning: a conditional child stays only under its parent's
  value, and a member the assignment's other values exclude is repaired
  to the first admissible member; `random` draws a conditioned member
  among the admissible ones from the start. The cost is the negated score, or the goal values in
  minimize form under a Pareto goal. `adir run --backend <name>`
  overrides the backend for one run. Backend keys pass through under
  `search.numeric` (`seed`, `initial_design_size`, `population`).

### 9.3 The model clients

`search.models.<role>` names one model per role as an agent CLI and
its model:

```yaml
models:
  solution: {agent: opencode, provider: openrouter, model: z-ai/glm-5.3-flash, timeout_s: 1800}
  guide:    {agent: claude,   model: claude-opus-5, effort: high}
```

`agent` is one of `claude`, `codex` and `opencode`; the model name is
the CLI's own. opencode takes one setting more than the other two:
`provider`, its provider id (`openrouter`, `anthropic`, `google-vertex`,
...), joined with `model` into opencode's `provider/model` (a `model`
that already carries the provider is taken as is); opencode resolves
the pair through its configuration and stored credentials. `small_model`
names the model opencode uses for its own session-title and summary
calls; it defaults to the role's model, so no call leaves it (without
the setting opencode picks a provider default, which showed up as
`google/gemini-3.8-flash` calls on OpenRouter). ADIR hands both to
opencode through `OPENCODE_CONFIG_CONTENT`, which opencode merges over
its configuration files. `timeout_s` bounds one attempt of a call
(default 1200) and `retries` the attempts (default 2): a provider
stream that never completes is repeated once rather than waited for.
ADIR reaches the CLI through
its CHIA model node (`chia.models.claude.ClaudeCodeLLM`,
`chia.models.codex.CodexLLM`, `chia.models.opencode.OpenCodeLLM`): each
call builds the node with the system message and dispatches its
`prompt` through ray to the worker that holds the resource
`<agent>_creds`, which the bind-time check requires of a worker type;
without a cluster the node runs in-process, so the CLI and its login
are the head's. The three nodes run with reading allowed and editing
denied, since the reply is a diff the evaluator applies:

* the claude node runs `claude --print --bare` with `--effort`, the
  editing tools disallowed and `--add-dir` on the agent's directory
* the codex node runs `codex exec` in a read-only sandbox with the
  agent's directory as `work_dir` (the sandbox limits writes, not reads)
* the opencode node runs `opencode run --agent chia` with `--variant`
  from `effort`, the `edit`, `bash`, `webfetch` and `external_directory`
  permissions denied, and the agent's directory as its directory

`work_dir` replaces the agent's directory (section 7.7) as the directory a node runs in.
There is no raw endpoint client: a model behind an OpenAI-compatible
endpoint is reached through opencode's provider configuration. The
agent's client sits behind ADIR's, which composes the solution model's
prompt (section 7), writes the call's sidecar under `calls/`, and counts the call and
the node's reported usage (`input_tokens`, `output_tokens`,
`reasoning_tokens`, `cost_microusd`) into `summary.json`.

### 9.4 The evaluator entry

`evaluator.py` exposes `evaluate(program_path)`. It runs the static
checks, extraction and assembly with the fixed artifacts, then the
derived graph through CHIA, appends the record to the archive and
returns SkyDiscover's `EvaluationResult` (the metrics and the
artifacts below). On a hard failure the metrics carry `error` and
`error_message`, which is the backend's retry convention: the next
prompt shows the failing node's detail.

Metrics:

| Key | Type | Content |
| --- | --- | --- |
| `<node>.<output>` | number | every produced output that is a number, a boolean (as 0 or 1) or an interval (its mean), nested keys flattened with dots |
| `goal.<n>` | number | the goal value at level n |
| `combined_score` | number | the score rule |
| `feasible`, `fidelity_level` | number | the record's fields |
| `candidate_id` | string | the record's id; the backend renders it in the prompt, so the model client finds the parent record |
| `error`, `error_message` | 0.0, string | present only on a hard failure |

Artifacts, which the backend injects into the next prompt:

| Key | Content |
| --- | --- |
| each entry of `evaluate.feedback` | the named node output, rendered as text |
| `declarations` | the candidate's declaration block |
| `stderr` | the failing node's `detail` on a hard failure |

The declarations and the short string outputs are in the record
(section 10.1); SkyDiscover has no metadata channel from an evaluator.

### 9.5 Context, tactics and instructions

The composer renders the context programs per the `show` knob:

| `show` | A context program is shown as |
| --- | --- |
| `declarations_metrics` | its declaration block and its metrics |
| `declarations_only` | its declaration block |
| `full` | its declaration block, its metrics and its program text |

Three mechanisms act in the composer and are logged into the record,
so that their effect is measurable from the archive:

| Mechanism | Setting | Logged as |
| --- | --- | --- |
| variant sampling: one knob combination per iteration (section 7.4) | `search.prompts.variants`, `sample`, `window` | `prompt_config` |
| tactic injection: one tactic per iteration from the sources named, the source chosen by a UCB over child improvement in the last `window` records | `search.tactics` | `tactic_id` (`<source>:<index>`) |
| instruction evolution: the `guidance` slot | `search.instructions` | `instruction_id` |

ADIR ships two tactic sources: `unexplored_values` (members of searched
domains no evaluated candidate has stood at, a candidate's values being
its completed declaration, so an undeclared decision counts as its
default) and `worst_constraint` (the soft constraint with the least
slack in the parent); a domain registers more (chiALU:
`critical_path`, `moves`). The tactic is drawn after the operator and
the focus of the round: under the `local` operator a source that
proposes declaration values (`unexplored_values`) is left out, since
the operator keeps every declaration, and under `member_focus: one`
`unexplored_values` addresses the variables of the region in focus
alone. The parent is the record whose id the backend's rendering
carries. AdaEvolve's paradigm breakthroughs are the backend's own
mechanism and are left on.

```yaml
search:
  prompts:
    variants:
      operator: [structural, local, free]
      ambition: [conservative, moderate, aggressive]
      member_focus: [none, one]
      feedback_depth: [summary, full]
    sample: ucb
    window: 40
    sources: [chialu_interface, chialu_structures]
  tactics:
    sources: [unexplored_values, critical_path, moves]
    select: ucb
    window: 20
  instructions:
    enabled: true
    slot: guidance                 # the only evolved slot
    seed: "Prefer changes that shorten the critical path."
    propose: {role: strategy, every: 10, from: [feedback, declarations, metrics]}
    select: ucb
    window: 40
    max_chars: 1200
```

Instruction evolution edits only the `guidance` slot. Each instruction
is a row of `<run>/instructions.jsonl` with its id, its origin
iteration and its source (`seed` or `proposed`); its cumulative child
improvement is read from the records that carry its id. Each iteration
one instruction, or none, is chosen (`select: ucb` over child
improvement in the last `window` records, or `uniform`). Every
`propose.every` evaluated candidates the `propose.role` model receives
the reflective mutation prompt of GEPA: the task, the instruction with
the best improvement so far, and the recent parent-child pairs with
what `from` names (the declarations, the metrics, the feedback
artifacts) and their score deltas; the guidance it returns, cut to
`max_chars`, becomes a new row. The used instruction is logged as
`instruction_id`.

### 9.6 Parallelism, resume, budget

* SkyDiscover's built-in managers run the iterations one at a time in
  this version; `parallel` sets the evaluator concurrency those
  managers do not use. Within one evaluation the nodes with no unmet
  dependency run at once on `parallel_nodes` threads (default 8); a
  hard failure cancels the nodes not yet started and drops the results
  of the running ones.
* Resume is the backend's checkpoint plus CHIA's cache: `adir run
  --resume` loads the newest `<run>/skydiscover/checkpoints/
  checkpoint_<n>`; a node's inputs are content, and the content key is
  the call's `_chia_tag`, so a re-evaluation is a cache hit for every
  node the run file marks `cache: true`.
* A database a previous run left at the backend's `db_path`
  (`<run>/skydiscover/db`) is renamed to `db.<stamp>` before the
  controller is built, whether or not the run resumes: SkyDiscover's
  AdaEvolveDatabase loads a database found at `db_path` inside its base
  constructor, before its own attributes exist, and fails in
  `get_best_program`; a fresh run repopulates the database from the
  seeds and a resumed run from its checkpoint.
* A watcher thread checks every 5 seconds: the `stop` file (`adir
  stop`), `budget.wall_hours`, `budget.llm_calls` (counted by the model
  client into `summary.json`), `budget.node_runs` (the node calls
  summed over the records), and `stop.plateau_iterations` (no
  improvement of the best score over the last N records). Each ends
  the run after the current iteration and writes `stopped_by` into
  `summary.json`. `output_tokens` and `cost_usd` are not counted, since
  the CLI nodes do not report them.

---

## 10 Records and reports

### 10.1 The candidate record

One record per evaluated candidate, written by the evaluator entry and
mirrored into `Program.metadata`:

| Field | Content |
| --- | --- |
| `run`, `iteration`, `candidate_id`, `parent_id` | identity and lineage |
| `unit_id`, `space_hash`, `evaluator_hash`, `search_hash` | the comparison axes |
| `model`, `role`, `effort` | which model produced the candidate |
| `operator`, `prompt_config`, `tactic_id`, `instruction_id`, `seed_id` | the prompt provenance: the knob combination, the tactic and the instruction of the iteration (section 7.4) |
| `declarations` | the parsed declaration block, with what each check verified |
| `constraints` | every constraint with its result (satisfied, violated with slack, `UNDECIDED`) |
| `measurements` | every produced output with its node hash and provenance, less the outputs a node declares `transient` (a compiled binary, a netlist: the graph carries them, the record keeps their size) |
| `skipped` | the nodes a `when` condition or a hard failure kept from running |
| `fidelity_level` | the highest level of `goal.fidelity` the candidate has a value at |
| `touched` | the members or files the candidate changed relative to its parent |
| `sub` | the archives of the sub-instance runs the candidate's graph invoked |
| `score` | `combined_score` and the rule |
| `source_sha256`, `source_path` | the text or the diff |
| `cost` | tokens and dollars of the call, node seconds |
| `decision` | accepted into the front, rejected with reason, retried |

### 10.2 Storage

`archive.store` is `jsonl` (a file under the run directory and an
optional shared `results_db.jsonl`) or `sqlite` (a CHIA database node,
one table per record kind, queryable by an agent tool when
`archive.query_tool: true`).

### 10.3 Comparison

Front, best and near-front are computed from records with equal hashes
on the fixed axes. A comparison across models, backends or prompt
mechanisms holds `unit_id`, `space_hash` and `evaluator_hash` fixed and
varies the rest; a comparison of one metric across runs holds that
metric's node hash fixed.

### 10.4 Reports

The report is generated from the records: the best feasible candidate or
the front with the selection trace; per-constraint results; measurements
with provenance; constraint slack; the `report` outputs for the front;
per-seed summaries, per-declaration summaries and per-member summaries;
the rank correlation between adjacent fidelity levels; template and
tactic effect tables; cost per role and per node, with sub-instance runs
itemized; the pins; every registered prior's predicted-versus-measured
table. Nothing in the report is hand-written.

---

## 11 Trust rules

* The mutable set is the `evolve` list of seed artifacts; everything else
  is outside the markers by construction.
* A pinned output changes only through its own node.
* GENERATED modules come from trusted generators; the agent never edits
  them.
* Hard constraints never enter the score except as zero.
* Which nodes run, and in which order, is derived from the goal and the
  constraints, never chosen by the agent.
* The hard-constraint list is recorded; a run states which checks were
  active.
* A declaration is a declaration; the record marks what was checked.
* Report-only outputs are unseen by the search.
* A prior is a prior.
* The prompt skeleton is immutable; instruction evolution writes only
  the `guidance` slot; the composed prompt config of every iteration is
  recorded; `search_hash` covers the composer version, the skeleton,
  the variant space, the instruction settings and an override.
* Every report claim traces to a record.

---

## 12 The registration API

### 12.1 Objects

Nodes are CHIA's: a domain library adds one by writing a
`@ChiaFunction` that takes keyword inputs and returns a dict, and
documents its outputs. ADIR registers the objects below.

| Object | Registered by | Carries |
| --- | --- | --- |
| `Template` | the domain | name, variables, `elaborate(bindings) -> Elaboration`, generators per generated artifact, a seed generator, line kinds, presets, requirements; the optional hooks `normalize_declaration(ctx, decl)` (section 5.2), `focus_map(ctx, parent) -> {region: [variables]}` (section 7.4), `plan_doc`, `plan_seed(ctx, name, plan)` and `replan(ctx, decl, parent_decl)` (section 8.1) |
| `Variable` | inside a template | name, domain, admitted binding times, `when`, `member_when` (a sibling and its allowed members per conditioned member), `indexed_by`, `requires` (requirement names per member), doc |
| `Preset` | the domain | name, path, the `fixed` bindings it expands to |
| `LineKind` | the domain | line name, parser, check |
| `Prior` | the domain | name, `predict(declarations) -> (value, lo, hi)` |
| `TacticSource` | the domain (two by ADIR) | name and the renderer over `space.json`, the graph and the archive |
| `PromptSource` | the domain | name, `render(instance, archive, parent_record, focus=None) -> markdown` (`focus` is the region in focus, for a renderer that accepts it), `static` (rendered once into the system text, or per round with the parent); data for the composer's domain slots (section 7.1) |
| `Tool` | the domain | an MCP tool for agentic backends: `{name, node, work_dir, timeout_seconds}` |

```python
from adir import (Template, Variable, Bool, IntRange, Enum, Set,
                  Preset, LineKind, Prior)

ALU = Template(
    name="chialu.ALU",
    variables=[
        Variable("ops", Set(OPS), binding_times={"fixed", "runtime"}),
        Variable("modes", Set(MODES), binding_times={"fixed", "runtime"}),
        Variable("accuracy", Enum(["exact", "approximate"]), binding_times={"fixed"},
                 requires={"approximate": ["error_bound"]}),
        Variable("checker.family", Enum(CHECKER_FAMILIES), binding_times={"fixed", "search"}),
        Variable("checker.modulus", Enum([3, 7, 15, 31]), binding_times={"fixed", "search"},
                 when=("checker.family", "residue")),
        Variable("core.adder.family", Enum(ADDER_FAMILIES), binding_times={"fixed", "search"},
                 indexed_by=SEED_STRUCTURES("adder")),
        Variable("core.adder.topology", Enum(PREFIX_TOPOLOGIES), binding_times={"fixed", "search"},
                 when=("core.adder.family", "parallel_prefix"),
                 indexed_by=SEED_STRUCTURES("adder")),
    ],
    elaborate=elaborate_alu,
    generators={"checker": gen_checker, "verify_bundle": gen_verify_bundle},
    seed_generator=gen_seed,                  # (instance, name) -> text with a declaration block
    line_kinds=[LineKind("STRUCTURE", parse_structure, check_structure),
                LineKind("MOVE", parse_move, check_move)],
    presets={"rs6000_lza": Preset("core.adder", {...})},
)
```

```python
from adir import PromptSource

PromptSource("chialu_interface", render_interface, static=True)   # into the system text
PromptSource("chialu_structures", render_structure_table)         # per round, with the parent
```

```python
from chia.base.ChiaFunction import ChiaFunction

@ChiaFunction(resources={"eda": 1.0})
def synth_ppa(rtl_text: str, top: str, pdk: str, clock_ps: int,
              effort: str = "medium", timeout_s: int = 1200) -> dict:
    """Outputs: ok, area_um2, cells, abc_delay_ps, seconds, pdk,
    clock_ps, detail, critical_path."""
    ...
```

Under `search.models.<role>.provider: chia`, the binding registers an
LLM adapter that dispatches each call to the named worker through
`chia_remote`, so CLI-based agents and provider credentials stay on
their workers.

### 12.2 Bind-time checks

`adir check` fails on:

* an unbound active variable, a binding time the variable does not
  admit, a value outside the domain, a `runtime` list with one member, a
  binding on an inactive child of a `fixed` parent, a preset conflict;
* an artifact on the wrong module (seed on a GENERATED module, user text
  on a GENERATED module), a missing file, an `evolve` name not in the
  artifact;
* a seed whose declaration block fails the declaration check;
* a node not in CHIA's catalog or the domain library, an input key that
  is not a parameter of the node, a reference that does not resolve, an
  expression that does not type-check against the domains and outputs
  it references, a cycle in the graph, a referenced output the node
  documents as absent, a node whose resources no worker type provides;
* a `map_over` key that is not a parameter of the node or that also
  appears under `inputs`;
* an `archive.*` or `goal.*` reference outside a `when` condition;
* a `report_only` output referenced outside `report`, or under a
  fidelity level;
* under a numeric backend, a `seed` artifact;
* a sub-instance whose `search` variables collide with the outer's, or
  whose `bindings` name an inner variable that is not `fixed`;
* a requirement left open;
* a model role without a provider, a provider without credentials on its
  worker;
* a variant knob the composer does not have, or a value it does not
  admit; more than 256 knob combinations;
* `instructions.enabled` without the `propose.role` model role under
  `search.models`, or an evolved slot other than `guidance`;
* `search.operators` that is not a mapping, or an override file that
  does not exist;
* a `knowledge` value that is not a directory, a `task.context` file
  that does not exist;
* a preset, prior, tactic source, prompt source or tool the library
  does not register.

---

## 13 The yaml reference

Every key lives under `adir:` unless stated. Unknown keys are errors.
Block style is required.

### 13.1 Top level of `adir:`

| Key | Required | Meaning |
| --- | --- | --- |
| `module` | yes | `<library>.<Template>` |
| `run_dir` | no | the run directory |
| `variables` | yes | section 3 |
| `artifacts` | yes | section 5.1 |
| `evaluate` | yes | section 6 |
| `constraints` | no | section 4.3 |
| `goal` | yes | sections 4.5 and 4.6 |
| `knowledge` | no | section 7.5: the knowledge base directory |
| `task` | no | section 7.6: `context`, the task file, or `script`, its generator |
| `role` | no | section 7.6: `file` or `script`, the role text |
| `search` | yes | sections 8 and 9 |
| `archive` | no | section 10.2 |

### 13.2 `evaluate`

| Key | Meaning |
| --- | --- |
| `nodes.<name>.node` | the node's name in CHIA's catalog or the domain library |
| `nodes.<name>.inputs` | keyword inputs: expressions over references and literals (section 6.2) |
| `nodes.<name>.map_over` | parameters mapped over lists (section 6.8) |
| `nodes.<name>.when` | conditions over metrics, including archive quantiles (section 6.4) |
| `nodes.<name>.report_only` | runs at report time for the front only (section 6.5) |
| `nodes.<name>.pin` | computed on the seed and reused (section 6.6) |
| `nodes.<name>.resources` | a resource override passed to CHIA |
| `feedback` | node outputs injected into the next prompt as artifacts |
| `report` | node outputs computed for the front at report time |

### 13.3 `search`

| Key | Meaning |
| --- | --- |
| `backend` | section 9.2; an LLM backend or a numeric one over `space.json` |
| `iterations`, `parallel`, `parallel_nodes`, `retries`, `diff_mode`, `max_solution_bytes`, `eval_timeout_s`, `llm_timeout_s`, `max_tokens`, `checkpoint_interval` | loop shape (section 9.2) |
| `database` | backend keys passed through |
| `numeric` | numeric-backend keys passed through |
| `seeds` | section 8.1 |
| `operators` | `override: <file>`, the escape hatch of section 8.2 |
| `context` | `programs`, `show` (`declarations_metrics`, `declarations_only`, `full`); the defaults of the composer knobs |
| `prompts` | `variants` (knob to value list), `sample` (`uniform`, `ucb`), `window`, `sources` (PromptSource names), `log` (default true: every prompt of every role, with the reply appended, under `<run>/prompts/`; the discover and task-brief exchanges in `discover_prompt.md` and `task_brief_prompt.md`); sections 7.4 and 9.5 |
| `task` | `context` (a markdown file, the task text), `author` (`discover`: the discover role writes the brief); section 7.6 |
| `tactics` | `sources`, `select`, `window`; section 9.5 |
| `instructions` | `enabled`, `slot`, `seed`, `propose` (`role`, `every`, `from`), `select`, `window`, `max_chars`; section 9.5 |
| `models.<role>` | `agent` (`claude`, `codex` or `opencode`), `model` (the CLI's model name), `effort`, `weight`, `timeout_s`, `work_dir`; roles are `solution` (required under an LLM backend), `guide` (AdaEvolve paradigms, EvoX summaries), `strategy` (instruction proposals), `evaluator` (LLM feedback), `discover` (seed plans from a model, usable under any backend); section 9.3 |
| `tools` | for agentic backends: a list of registered tools |
| `budget`, `stop` | counters (`wall_hours`, `node_runs`, `llm_calls`; `output_tokens` and `cost_usd` are accepted and not counted) and stop rules (`plateau_iterations`; `target_value` is accepted and not applied); section 9.6 |

### 13.4 `archive`

| Key | Meaning |
| --- | --- |
| `store` | `jsonl` or `sqlite` |
| `path` | the file or the database locator |
| `shared` | an additional shared archive rows are appended to |
| `query_tool` | expose the archive as an agent tool |
| `keep_transcripts` | store prompts and responses |
| `report` | `front_only: true` |

---

## 14 Examples

`examples/` at the repository root holds one directory per task, each with the single
`run.yaml` and a README that walks through the file and shows how the
task reaches the backend through the three inputs:

| Directory | Task | What it exercises |
| --- | --- | --- |
| `prefetcher_champsim` | L2 data prefetcher in C++ on a simulator node | a searched storage budget, a train instance and a report-only held-out instance of the simulator node, an accounting node under a hard constraint, prompt-only knowledge |
| `boom_timing_opt` | BOOM critical-path optimization in Chisel | repo artifact, agentic backend with tools, a soft IPC constraint from a Verilator node beside a hammer_vlsi node, a sub-block synthesis screening the full one |
| `ldpc_decoder` | LDPC decoder RTL | algorithm-level searched variables feeding a pinned channel-simulation node, a domain metric namespace, EvoX |
| `synth_recipe` | a Yosys/ABC script for one RTL block | a domain library beside the run file (`chirecipe/`), file seeds, a whole-file EVOLVE region, an ABC equivalence check as a hard constraint, a task file, Gemini through opencode's Vertex provider |
| `synth_recipe_grid` | the same block under `grid` | a numeric backend: the recipe text is a node output of the declaration, no seed artifact |
| `gemm_cache_kernel` | four C GEMM kernels under cachegrind | a seed family with members, the BUFFER and TILE line kinds, a plan-table PromptSource, a cheap-to-expensive constraint chain |
| `cacheflex_kernel` | the CacheFlex artifact's SPM GEMM loop nest | a domain library over an external checkout, a build through the artifact's encoder, a QEMU check, a gem5 cell as the measurement, `kc` and `mc` searched beside the text |

The other directories of `examples/` hold run files in the same form
for a scratchpad design space, a tiling heuristic, an accelerator
mapping, a core-parameter search, HLS pragmas, analog sizing and
congestion control; each names the nodes, constraints and goal it
needs, and binds once its domain library exists.

---

## 15 Open questions

* Whether the composer's `structural` section or a backend's own
  operator generator produces better steps on artifacts with a
  structural vocabulary; the archive's `prompt_config` makes the
  comparison a query.
* Whether instruction evolution pays for itself on evaluations that cost
  minutes.
* A batched emission mode for indexed decisions (a per-site table with
  thousands of entries) as one solution.
* Attribution of a system-level metric to a declaration (IPC credit per
  component through single-component reversion runs).
