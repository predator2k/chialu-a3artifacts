# chiALU / a3eval artifact (exp10)

Contents
- `chialu/` — chiALU code (git archive of chiALU 6c197d3688b88d300fc73281851ba76da00705cc) with ADIR **vendored** in `chialu/third_party/adir/` (ADIR 23a9bd31a3be60e6172e4e12b00677e87577f440). `chialu/legacy/knowledge/pdf/` (third-party papers, ~0.9 GB, copyrighted) was omitted. `3rdparty/chialu` is a symlink to `chialu/` so the harness paths work.
- `chia/` — the chia fork (17276bf1695776cff244d847f8f9c9cd1ceae46d), vendored (opencode backend, cluster tooling). Its own submodules (examples/benchmarks, riscv prebuilt) are not included.
- `harness/ baselines/ tables/ docs/ frozen/ tests/ env.sh README.a3eval.md` — a3eval evaluation harness (a3eval 9d24818c7261cb66ad99ee4b4e1ccbeedfbbbd48).
- Submodules (only these): `3rdparty/berkeley-hardfloat` (c1105e6a), `3rdparty/cvfpu` FPnew (77811635), `3rdparty/transdot` (48c9b745, fork predator2k/SafeDot branch pncel-develop-plus-comb, public; SSH URL — use `https://github.com/predator2k/SafeDot.git` for anonymous clone).
- `scripts/` — how exp10 was run (see scripts/README.md).
- `data/exp10/` — exp10 only:
  - `runs/<run>.tar.zst` — 54 run dirs incl. agent workspaces (`agent_ws/` followed) and the full opencode session exports (`sessions/*.json.gz`, **1125 sessions**, all runs match `sessions/index.json`); caches (cache/, chia_cache/, adir_scratch/, __pycache__) excluded.
  - `surrogate/surrogate3.tar.part-*` — chiALU seeds/surrogate inputs `<t>.surrogate3/{discovered.json, surrogate/report.json, surrogate/dataset.jsonl.zst, surrogate/model.pkl}` for int_subword_alu, fp_alu_cmp, fp_alu_cmp_hf. model.pkl only for fp_alu_cmp_hf (the other two embed local paths; retrain from dataset.jsonl).
  - `logs.tar.zst` (driver.log, commits.txt, completion.tsv, smoke logs, per-run stdout logs), `commits.txt`, `completion.tsv`, `smoke_check.txt`, `results_final_abs.md`, `results_interim_*.md`.
  - synthesis receipts and the structure DB (synth10_all): see follow-up commit if present (`receipts/`, `synth10_all.tar.zst*`).

## exp10 protocol
54 runs: chiALU, best_of_n, beam_search, adaevolve, plain × 3 targets (int_subword_alu, fp_alu_cmp, fp_alu_cmp_hf) × 3 reps = 45, plus hand_adaevolve starting from FPnew PARALLEL / HardFloat / TransDot × 3 = 9. LLM: DeepSeek deepseek-flash via opencode. Synthesis: yosys+ABC, Nangate45, 300 ps clock, median of 3. Planned 20 iterations; stopped at 04:31 after every run reached ≥ 13 iterations; results are truncated at 13 iterations (`results_final_abs.md`).

## Restore
```
zstd -dc data/exp10/runs/<run>.tar.zst | tar -x          # single file
cat data/exp10/surrogate/surrogate3.tar.part-* | tar -x  # split parts (plain tar)
cat X.tar.zst.part-* | zstd -dc | tar -x                 # split .zst parts
```

## Caveats
- Seeds = measured-sample Pareto front (no NSGA-II).
- Delay differences < 5 % are within synthesis noise.
- Sanitization: all text (incl. inside archives and .gz session/receipt files) had user paths → `$CHIALU_HOME`/`$A3EVAL`/`$HOME`/`$REMOTE_HOME`, IPv4 → `<HEAD_IP>`/`<IP>` (except 127.0.0.1/0.0.0.0), host names → `<host>`, e-mail addresses → `<email>` (incl. upstream author e-mails in FPnew-derived headers), test-fixture tokens → `<REDACTED>`. Some chia network unit tests therefore no longer pass as-is. Receipt file names are the pre-sanitization content hashes.
