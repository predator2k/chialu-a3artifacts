# An L1D hint table written by the search, scored against the per-PC oracle

PF-LLM (Xu et al., ASPLOS '26) fine-tunes a 0.5B model to read the assembly
around every load PC and emit an 8-bit hint: which member of an L1D
prefetcher ensemble may prefetch for that load, at what degree, and which
member must not see its demand request. The hints sit in a table in main
memory; a small on-chip buffer caches them.

This example keeps that hardware and replaces the model. The search writes a
**program** that reads a binary's disassembly and fills the table -- the same
decision, written down as an analysis instead of distilled into weights.

## What a candidate is read against

The paper has no public artifact (no code, no weights, no hint tables, no
badge), so its tables cannot be run on these binaries and it cannot be a
baseline. A candidate is read instead against two references that one sweep
-- every (member, degree) pair on every workload -- gives for free:

* `baseline` -- no prefetching at all. The floor.
* `best_single` -- the strongest one-size-fits-all choice per workload.
  Beating it is the whole reason to decide per load PC rather than once per
  program.

What is reported is what was measured: geomean IPC, total cycles, and DRAM
read traffic. The goal is `geomean(dev.ipc)`.

DRAM traffic is compared **per workload against `best_single`**, not against
no prefetching and not on summed totals. Against no prefetching every
prefetcher looks profligate, because fetching early is what a prefetcher
does; and the sweep covers four workloads while a candidate is scored on
three, so a summed total would compare different sets of programs.

An earlier version assembled the sweep's per-PC argmin into a table and
called it an upper bound. It is not one. Those choices are measured in runs
where a single member served every load, and composing them changes the
interference in the L1D and what every member trains on: per workload the
assembled table already sat at or below `best_single` (-0.06%, 0.00%,
-7.21%), and the first search candidate scored 0.689 geomean IPC against its
0.672. It is gone.

## Layout

```
run.yaml        the instance: 4 searched hardware parameters, 14 nodes
task.md         what the agent is asked to do
setup.sh        ChampSim + Pin + benchmarks + traces, from nothing
seeds/hintgen.py  the seed: next_line for every load, and the plumbing
lmhint/         the hardware, fixed
  subprefetchers.h  the ensemble; train() and issue() are separate, which
                    is what makes the hint's filter field mean anything
  lmhint.{h,cc}     the PHT loader, the PHB, the router, the multiplexer,
                    the orchestrator, and per-PC miss counting
bench/          four C benchmarks, each mixing several access patterns
pfllm/          the domain library: template, nodes, ChampSim runner,
                disassembly, hint encoding, candidate harness, knowledge
```

## Running

```
ROOT=/data/scratch ./setup.sh          # prints the variables to export
adir check  run.yaml
adir seeds  run.yaml --local           # the sweep, the oracle, the seed
adir run    run.yaml --local
```

`PFLLM_WORKERS` sets how many ChampSim processes run at once. It is read
from the environment rather than passed as a node input on purpose: a node
input is part of the cache key, so tuning parallelism would discard every
measurement taken at another width.

## Caveats worth knowing before trusting a number

* **The simulated window decides whether there is a problem at all.** At
  2M warmup and 8M instructions, `bfs` and `pr` execute two distinct load
  PCs each; at 5M and 20M, `bfs` executes 230. GAP's BFS alternates
  top-down and bottom-up phases and a short window sits inside one. Use the
  paper's shape -- tens of millions of warmup instructions and hundreds of
  millions simulated -- or the per-PC decision the whole design is about is
  not in the measurement.
* **Three workloads scored, one held out.** `heldout` is simulated at report
  time only and is the single number no candidate was optimized for. Report
  it apart from the dev geomean.
* **Only the binary's PCs get hints.** Dynamically linked library code is at
  an address the disassembly does not cover, so those loads run the reserved
  policy. On `bfs` they are 10.5% of accesses and 0.7% of misses. Static
  linking, or tracing under `setarch -R` and disassembling the mapped
  libraries, closes this.
* **The ensemble is seven members, not the paper's twelve.** They are
  faithful in mechanism but are not the Table 2 implementations. Dropping in
  CMU-SAFARI/Pythia's `prefetcher/` (MIT, all twelve) behind the `SubPF`
  interface is the upgrade path.
* **The dev set is what the search fits.** Three workloads are scored
  against over every iteration; `heldout` is simulated at report time only
  and is the one number no candidate was optimized for. Report them apart.
