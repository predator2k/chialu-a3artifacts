# ADIR

ADIR is the task layer of an agentic hardware-design search. A domain
library registers a template: variables with the binding times they
admit (`fixed`, `search`, `runtime`), generators, a seed generator, the
declaration lines its candidates carry, and presets. One yaml file
binds the variables, wires CHIA nodes into an evaluation graph, and
states constraints and a goal over the nodes' outputs. ADIR derives
which nodes run, checks and records every candidate, and hands the task
to a search backend (SkyDiscover for the LLM backends, an optimizer
over `space.json` for the numeric ones).

`docs/design.md` is the specification; `examples/` holds one run
file per task.

## Layout

```
adir/
  domains.py       Bool, Range, Enum, Set, Struct
  variables.py     Variable, Binding, bind_variables, space_json
  spaces.py        Family, Space: a family space compiled to variables
  registry.py      Template, Elaboration, Preset, LineKind, Prior, TacticSource, Tool, node
  declaration.py   the declaration block and its check (adir.declaration)
  expr.py          the expression language, intervals, aggregates, conditions
  artifacts.py     artifacts, members, EVOLVE regions, the backend program
  nodes.py         node resolution, the local executor and its cache
  graph.py         node instances, references, the derived graph, when, map_over, pins
  metrics.py       constraints, the goal, fidelity levels, the score rule
  archive.py       jsonl and sqlite records, archive.* values, the front
  instance.py      the bind order, hashes, contract.json
  evaluate.py      one candidate: static checks, declaration, graph, constraints, score, record
  evaluate_entry.py  evaluate(program_path) for a backend
  seeds.py         seed programs and their evaluation
  problem.py       problem.md and the operator templates
  subinstance.py   adir.instance
  report.py        summary.json and report.md
  backends/        skydiscover.py, numeric.py (random, grid; smac and nsga2 adapters)
  cli.py           adir check | cluster | seeds | run | status | stop | report
tests/             a toy domain and the tests over it
```

## Use

```
pip install -e .
adir check   run.yaml      # bind-time checks; problem.md, space.json, graph.json, evaluator.py, skydiscover.yaml
adir seeds   run.yaml      # generate and evaluate the seeds
adir run     run.yaml      # the search (SkyDiscover, or a numeric backend)
adir report  run.yaml      # report-only nodes for the front, summary.json, report.md
python -m unittest discover -s tests
```

A domain library is a Python package whose `<library>.domain` module
(or the package itself) constructs `adir.Template` objects; the yaml's
`module: <library>.<Template>` finds them. Nodes are functions that take
keyword inputs and return a dict; `adir.node(outputs=[...],
resources={...})` documents them and wraps them as CHIA functions when
CHIA is importable.
