# How exp10 was run

Order:
1. `source scripts/chialu-env.example.sh` (after setting `CHIALU_HOME`, `A3EVAL`, `THIS_MACHINE`; provider key in `$CHIALU_HOME/.secrets/openrouter.env`, not included).
2. `chia up scripts/cluster_head.yaml -y` (single-host Ray cluster; the original file was `cluster_<host>.yaml`).
3. `bash scripts/smoke.sh` then `python3 scripts/smoke_check.py` (3-iteration smoke test of every method).
4. `bash scripts/run.sh` (the 54 runs; sessions archived with `harness/archive_sessions.py`).
5. `python3 scripts/analyze_abs.py` (tables in `data/exp10/results_*.md`; `analyze.py` = relative variant).

Paths were sanitized: `$CHIALU_HOME` (tool/cache/workspace volume), `$A3EVAL` (this repository), `<HEAD_IP>`, `<host>`, `<user>`.
