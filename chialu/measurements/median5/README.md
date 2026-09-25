# 2026-09-24 synthesis re-measurement

`results/<design>.json` stores a separately timed `repeats1` compatibility measurement and the
complete `repeats5` measurement. Area (µm²) and delay (ps) are independent medians of base,
`permute -S 11`, `23`, `37`, and `53`, inserted after the resolved descriptor's `strash`.
A failed or timed-out mapping invalidates the aggregate; partial statistics are diagnostic.
Cells belong to `cells_run_index`, the run closest to median area, breaking ties by index.

Every receipt includes the exact ABC script, seed, repeat index, status, seconds, RTL/checkpoint,
liberty and executable hashes, versions, effort, clock, top and options. `artifacts/*.gz` contains
content-addressed RTL, RTLIL, liberty, Yosys scripts, complete logs and stderr; SHA-256 covers
uncompressed bytes. Keep this directory with the records. Absolute paths describe the measurement
host; `--artifacts` relocates all blobs by hash. Never garbage-collect blobs still referenced by an
archive, cache, dataset, seed, profile or database row. On a cluster set `CHIALU_SYNTH_RECORDS` to a
persistent shared directory, or archive each worker's store with its results.

Replay one run (exit status 0 means exact equality of status, area, delay and cells):

```bash
python -m chialu.synth_records measurements/median5/results/int_subword_alu.json \
  --run 2 --artifacts measurements/median5/artifacts
```

The CLI accepts a `synth_ppa` result, an individual run receipt, or a baseline wrapper (default
`repeats5`, override with `--measurement repeats1`). Tool drift and artifact corruption are rejected; failed
or timed-out runs are retained, but their timing-dependent failure may not replay identically.

`remeasure.py jobs.json --out results --workers 6` runs the saved RTL jobs locally, without models
or Ray. Paths in the job manifests identify read-only source RTL; each input is also archived by
hash. `rtl/` holds the additional target seeds rendered from their bound baseline declarations.
`parallel.json` measures the three ALUs with `CHIALU_SYNTH_JOBS=4`; the metric is unchanged.
The node reserves at least that many EDA slots (and synth_unit reserves outer workers times that
count). Default internal concurrency is one, suitable for a pool already parallelizing designs.

Search graphs request `repeats: 5`; pipeline and surrogate CLIs accept `--synth-repeats`, synthdb
build/resynth and reference builders accept `--repeats`. Old single-run datasets cannot be resumed
as five-run datasets. Synthesis DB row identity includes repeats and seeds; queries prefer five-run
rows, warning when only the legacy DB is available (`CHIALU_DB_FLOW=strict` refuses the fallback;
`CHIALU_SYNTH_DB_REPEATS=1` explicitly selects legacy rows).

Attribution is diagnostic: a separate base mapping preserves hierarchy and unit-port names. Its
receipt is `report_run.attribution_run`; its area, cells and critical paths are not the metric
median. Both preparatory and diagnostic mappings retain inputs and logs. Per-unit `synth_unit`
measurements use five runs and retain their receipts in the attribution entries.
