One run per subdirectory, named by the run file's `adir.run_dir`.
`adir check <run file>` writes contract.json, problem.md, space.json,
graph.json, evaluator.py and skydiscover.yaml here; `adir seeds` and
`adir run` add seeds/, programs/, prompts/, verify/, the node cache and
the archive (`archive.path`, results_db.jsonl by default); `adir report`
writes summary.json and report.md. `ml/surrogate.py` reads one or more
of these archives. Everything here is gitignored except this README.
