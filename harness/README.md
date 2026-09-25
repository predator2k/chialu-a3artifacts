# harness

The directory holds the two scripts that run chiALU's evaluator outside the
ADIR search: the TestFloat harness (`testfloat_harness.py`, the plan's
section 3) and the plain agent loop (`plain_loop.py`, the plan's section 4,
Table A's "plain agent loop" row). Both take the chiALU checkout through
`PYTHONPATH=<chialu>:<chialu>/third_party/adir`.

## plain_loop.py

`plain_loop.py` runs one agent CLI against one unit for a fixed number of
model calls: each call hands the agent the current best program, the
evaluator's verdict on it and on the last candidate, and the instruction to
write the complete new program; the loop evaluates what the agent wrote with
chiALU's own evaluator functions and records the candidate in the shape of
ADIR's archive. Nothing of ADIR reaches the agent: no prompt composition, no
declaration block, no archive context, no plans, no knowledge cards and no
review.

```
PYTHONPATH=$CHIALU:$CHIALU/third_party/adir python3 harness/plain_loop.py targets/eval/fp_alu_cmp.yaml \
    --calls 20 --out run/fp_alu_cmp.plain.r1       # opencode, openrouter, deepseek-v4.1-flash, effort high by default
```

The run file is resolved as given, else relative to the chiALU tree on
`PYTHONPATH`, so the command above runs from this repository with the
chiALU checkout elsewhere.

### Options

| Option | Default | Meaning |
| --- | --- | --- |
| `run_file` | | the ADIR run file whose seed, verify bundle, top module, PDK, clock and effort the loop takes |
| `--agent` | `opencode` | `opencode`, `claude`, `codex`, or `none`, which evaluates the seed alone |
| `--provider` | `openrouter` | opencode's provider id; the model id is joined as `<provider>/<model>` |
| `--model` | `deepseek/deepseek-v4.1-flash` | the model id |
| `--effort` | `high` | the reasoning effort: opencode `--variant`, claude `--effort`, codex `reasoning_effort` |
| `--calls` | `20` | the budget in model invocations, one candidate each; a stalled invocation counts. With `--resume`, the run's total |
| `--resume` | off | continue the run under `--out`: the seed and every call with an `evaluation.json` are read back, a call cut short is removed (its directory and archive line) and done again, and the loop runs to `--calls` in all. Without it an existing `results_db.jsonl` is refused |
| `--out` | | the run directory |
| `--seed` | the run file's baseline seed | a hand seed; a file under `baselines/fpnew/` is the FPnew wrapper, joined with the CVFPU sources of `files.txt` by that directory's `build.py` |
| `--fpnew-point` | `MERGED` | the FPnew design point of a `baselines/fpnew/` seed |
| `--clock-ps` | the run file's `vars.clock_ps` | the synthesis timing target |
| `--timeout-s` | `1200` | one attempt's limit, the run files' `timeout_s`; an attempt that reaches it is recorded as `stalled` |
| `--stages` | `lint,conformance,fault,stat,synth` | the evaluator stages to run; `fault` runs where the run file has a fault node (int_subword_alu: the default checker from `checker_gen`, the run file's `fault.*` constraints as hard rows); a Mac without `read_slang` runs `conformance` alone |
| `--no-synth-report` | off | `CHIALU_SYNTH_REPORT=0`: no critical path, summary, paths or area by hierarchy as feedback |
| `--synth-infeasible` | off | synthesize a candidate that fails conformance too; its numbers are recorded, its feasibility is not changed |
| `--verilator-jobs` | the environment's `CHIALU_VERILATOR_JOBS` | the compilers of one conformance build |
| `--evaluate FILE` | | run the evaluator on one program and print the JSON result; no agent |

The script sets `CHIALU_SYNTH_REPORT` itself from `--no-synth-report`, so
the shell's value does not apply. The report texts are feedback by default
because chiALU's row receives the same texts (`synth_ppa.summary`,
`synth_ppa.critical_path`, `synth_ppa.paths`, `synth_ppa.area_by_hierarchy`
in the run file's `feedback` list).

### Loading

* `adir.instance.load` binds the run file with `run_dir_override` set to
  `<out>/adir_scratch`, so the chiALU tree is not written.
* `adir.seeds.seed_programs` renders the baseline seed. The program text ADIR
  hands its backends carries `ADIR-MEMBER` markers, `EVOLVE-BLOCK` markers
  and the declaration block (`ADIR-DECL` to `ADIR-END`, the `VAR` and
  `STRUCTURE` lines). `plain_rtl` removes those lines, which are comments, so
  the RTL is the text chiALU's evaluator synthesizes and the agent sees no
  declaration.
* The verify bundle is `inst.artifacts["verify_bundle"].texts`; the top
  module, the PDK, the effort and the synthesis timeout are the `synth_ppa`
  node's inputs; the clock is the `clock_ps` binding.
* A hand seed (`--seed`) is read as the complete program after the same
  stripping, except a file under `baselines/fpnew/`, which is joined with the
  CVFPU sources first (`build.py`'s `joined`).

### Evaluator

The evaluator nodes are the run file's, called as plain functions through
`adir.registry.underlying`, in the run file's gating:

| Stage | Node | Runs when |
| --- | --- | --- |
| lint | `chialu.eda.lint` | always |
| conformance | `chialu.eda.conformance` on the verify bundle | always |
| stat | `chialu.eda.yosys_stat` on the top | always |
| synth | `chialu.eda.synth_ppa` (PDK, clock, effort and timeout of the run file) | `conformance.pass` and `yosys_stat.cells <= k * seed.yosys_stat.cells`, where `k` is the factor of the run file's own screen (`2.0` in `fp_alu_cmp.yaml`) |

The run file's `synth_unit` node and `review` node have no counterpart:
both read the declaration, which the plain loop does not have. The
constraints are the run file's that apply without a declaration:
`lint.ok == true` (hard), `conformance.pass == true` (hard) and
`synth_ppa.abc_delay_ps <= vars.clock_ps` (soft, so a violation is
infeasible and its measurements are kept). `adir.metrics.feasibility` and
`adir.metrics.combined_score` compute the feasibility and the score from
those rows under the run file's goal (`ratio_to_seed`, `infeasible: slack`),
so the score column means the same in both archives.

### The agent call

* `adir.backends.skydiscover.AgentLLM` builds the CHIA agent node from the
  spec `{agent, provider, model, effort, timeout_s}`, which is the
  construction chiALU's solution calls use (`AgentLLM._make`): the same
  model id, the same `--variant`/`--effort`/`reasoning_effort`, the same
  timeout per attempt, the working directory of the call as the agent's
  directory, the shell, the web and every path outside it denied.
* `retries` is 1, so one invocation is one attempt. The run files set 2,
  which makes one ADIR call up to two attempts; the plan's protocol counts
  every attempt, and the plain loop's `--calls` counts attempts.
* The one departure from the flow's permission set is `edit`: the agent
  may edit files inside the call directory (opencode `edit: allow`; claude
  without `Edit`, `Write`, `MultiEdit` in `--disallowedTools`; codex
  `--sandbox workspace-write`), because the row's definition has the agent
  write the program. The flow's calls return the program in the reply.
* The claude and codex paths are written and not exercised: the EDA host
  holds the opencode login alone.
* Without CHIA (`chia.models.*`) the script stops before the first call;
  the Mac runs `--agent none` and `--evaluate` alone.

### The prompt

The system text names the role and the tools. The user text holds, in this
order, and the same for every call:

* the task: reduce area and delay at the clock target on the PDK, keep the
  module name, the ports and the exact behavior; the goal is the (area,
  delay) front;
* the unit as the run file binds it: the modes, the ops, the rounding
  modes, the flags, the conformance vectors;
* the files of the call directory: `program.sv` (the parent, unchanged),
  `candidate.sv` (a copy the agent edits in place), `feedback/*.txt` (the
  parent's evaluator texts) and `feedback/last/*.txt` (the last
  candidate's);
* the evaluator: the four stages and the two screens;
* the results so far: the seed's verdict and numbers, the best so far, the
  last candidate (the failing gate's detail, or area, delay and cells), the
  feasible front, the critical path of the parent;
* the reply: edit `candidate.sv`, then summarize the change.

The program reaches the agent as a file rather than inline, as it does in
chiALU's row (`context.programs: 1`), and the agent edits a copy in place
rather than rewriting 250 KB of text. Where the agent leaves `candidate.sv`
unchanged and its reply holds a fenced block with the top module, that block
is the candidate; where neither exists, the call is recorded as
`no_program`.

### Output layout

| Path | Content |
| --- | --- |
| `<out>/target.json` | the run file, the top, the PDK, the clock, the effort, the seed's name and hash, the agent spec, the budget, the stages, the unit and evaluator hashes |
| `<out>/seed/program.sv`, `evaluation.json`, `seed_values.json` | the seed's text and record; `seed_values.json` as ADIR's `seeds/seed_values.json` |
| `<out>/call_<k>/prompt.md` | `# System`, `# User`, `# Reply`, as ADIR's `prompts/*.md` |
| `<out>/call_<k>/program.sv`, `candidate.sv`, `feedback/` | the parent, the agent's program, the feedback files |
| `<out>/call_<k>/reply.md`, `transcript.md`, `usage.json`, `call.json` | the final reply (the reply so far for a stalled call), the session transcript from `opencode export`, the token counts, the call's status, wall time, session id, stderr and whether the session data was recovered |
| `<out>/call_<k>/evaluation.json` | the candidate's record |
| `<out>/programs/<candidate_id>.sv` | every program, as ADIR's `programs/` |
| `<out>/results_db.jsonl` | one record per candidate, the seed first |
| `<out>/best.sv` | the best feasible program so far |
| `<out>/summary.json` | the counters and the summary below |
| `<out>/run.log` | one line per event |

### The record

Every record carries the fields of `adir.evaluate.evaluate_candidate`'s
record, with these values:

| Field | ADIR's archive | The plain loop |
| --- | --- | --- |
| `run`, `candidate_id`, `parent_id`, `seed_name`, `is_seed` | the run name, `seed:<name>` or a 12-hex id, the parent's id | the same |
| `iteration` | the backend's iteration | the call index; `null` for the seed |
| `unit_id`, `space_hash`, `evaluator_hash` | the instance hashes | the same instance hashes |
| `search_hash` | the search section's hash | the hash of the loop's agent spec, budget and stages |
| `model`, `operator`, `prompt_config`, `tactic_id`, `instruction_id` | the composer's sidecar | the model id, `plain_loop`, `{agent, provider, effort, loop: plain}`, `null`, `null` |
| `declarations` | the VAR lines and STRUCTURE lines | `{vars: {}, lines: [], verified: null}` |
| `constraints` | one row per run-file constraint | the three rows above, in ADIR's row shape |
| `measurements` | `{node: {value, node_hash}}` | the same, `node_hash` `null` |
| `skipped` | `{node: "when ... is False"}` | the same text for `synth_ppa`; `stage off` for a stage `--stages` omits |
| `hard_fail`, `feasible`, `goal_values`, `fidelity_level`, `score` | from `adir.metrics` | from the same functions |
| `touched`, `sub`, `decision` | the composer's | `[]`, `[]`, `pending` |
| `source_sha256`, `source_path` | the program | the same |
| `cost.seconds`, `cost.node_calls`, `cost.cache_hits` | the evaluation | the same, `cache_hits` 0 |
| `cost.synth_seconds` | absent (in `measurements.synth_ppa.value.seconds`) | added: `synth_ppa.seconds` or 0 |
| `cost.llm_calls`, `cost.llm_wall_s`, `cost.stalled`, `cost.input_tokens`, `cost.output_tokens`, `cost.reasoning_tokens`, `cost.cache_read`, `cost.cache_write`, `cost.cost_usd`, `cost.num_turns` | absent (run totals in `summary.json`) | added per candidate, from the CLI's usage |
| `feedback`, `stderr` | the run file's feedback expressions | the same expressions the loop has (`conformance.detail`, `synth_ppa.*`) |
| `call`, `status`, `session_id` | absent | added: the call index (0 for the seed), `ok`/`stalled`/`failed`/`no_program`, the agent session |

Table A reads `feasible`, `goal_values[0]` (area), `goal_values[1]`
(delay), `measurements.synth_ppa.value.cells`, `call`, `cost.synth_seconds`
and `cost.*_tokens` from both archives; the chiALU runs give the call index
through their `prompts/` and the tokens through `summary.json`.

`summary.json` carries ADIR's counters under ADIR's names (`llm_calls`,
`llm_calls.solution`, `llm_failures`, `input_tokens`, `output_tokens`,
`reasoning_tokens`, `cost_microusd`) and the loop's summary: `calls`,
`candidates`, `feasible`, `feasible_fraction`, `stalled`, `failed`,
`no_program`, `best_area_um2`, `min_delay_ps`, `best`, `front` (the
feasible non-dominated records over area and delay, by
`adir.archive.Archive.front`), `seed`, `synth_seconds`, `eval_seconds`,
`agent_seconds` and `wall_seconds`.

### Budget accounting

* One call is one CLI invocation with one attempt of `--timeout-s`.
* An attempt that reaches the limit is recorded with `status: stalled` and
  counts toward `--calls`. Where the agent edited `candidate.sv` before the
  limit, that program is evaluated and recorded under the stalled status;
  where it did not, the record has no measurements and score 0.
* The CHIA node returns no session, reply or usage for a timed-out attempt.
  For opencode the loop recovers them from the session store
  (`opencode session list --format json` names the session by the call
  directory, `opencode export` gives its messages, and the node's own
  parser gives the reply so far, the token counts and the transcript), so
  a stalled call's tokens enter its record; `call.json` marks such a call
  with `recovered: true`. The claude and codex nodes have no such store,
  so their stalled calls carry no tokens.
* An attempt the CLI refuses (an authentication or rate-limit error) is
  `failed` and counts as well.
* The seed's evaluation costs no call, as ADIR's seeds stage costs none.
* The parent of the next call is the feasible record with the highest
  score, the later one on a tie, else the seed. The seed is the parent
  while no feasible candidate exists, so a seed that fails the gate (the
  FPnew wrapper fails 16 corner vectors of the `uf_after_round` class)
  stays the parent until a candidate passes.

### Parity with chiALU's row

| Element | Shared | Not shared |
| --- | --- | --- |
| the seed | the same rendered baseline, without ADIR's comment lines | |
| the evaluator | the same node functions, PDK, clock, effort, timeouts, gating and constraints | `synth_unit` and `review` (both need the declaration) |
| the model | the same `AgentLLM` construction, model id, provider, effort, timeout | `retries` 1 rather than 2; `edit` allowed inside the call directory |
| the budget | one invocation per call, stalled ones counted | |
| the feedback | the same evaluator texts as files | the review's verdicts and `synth_unit`'s attribution |
| the record | ADIR's fields and score rule | `declarations` empty; `call`, `status` and the per-call cost added |

### Local dry mode

The Mac's yosys lacks `read_slang`, so lint, stat and synth run on the EDA
host alone; Verilator runs on both. `--agent none --stages conformance`
evaluates the seed's conformance locally, and `--evaluate FILE --stages
conformance` does the same for any program. The FPnew seed joins locally
once `3rdparty/cvfpu` is checked out with its nested submodules
(`git submodule update --init --recursive --depth 1 3rdparty/cvfpu`).
