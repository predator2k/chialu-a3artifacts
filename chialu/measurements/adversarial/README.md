# Adversarial RTL evidence

See ../../REPORT.md (Chinese). All scripts run from the repository root after:

```sh
source measurements/adversarial/env.sh
```

`baseline.tar.gz` preserves the original 2,100 plans/declarations, selected cases,
original lint/conformance results, failing RTL, frozen target specifications and
vector hashes, official CLI receipts, and supplemental controls. It deliberately
omits Verilator builds and large regenerable vector files. `evidence_manifest.json`
records tool versions and each archived file's SHA-256.

To inspect without overwriting current scratch data:

```sh
mkdir -p measurements/adversarial/scratch/archived
tar -xzf measurements/adversarial/baseline.tar.gz -C measurements/adversarial/scratch/archived
```

To generate a new deterministic campaign (this overwrites that target's scratch
plans/RTL, so preserve the archive first):

```sh
python measurements/adversarial/hunt.py int --jobs 2
python measurements/adversarial/hunt.py int --phase evaluate --jobs 2
```

Use `fp` or `hf` for the other targets. The sharing-token parser was corrected
after the initial selection; the archive retains the exact original selection.
The final `sharing_coverage.json` and supplemental plan lists record the added
cases that close the actual sharing pairs.

To replay a saved plan with the current generator and original target vectors:

```sh
python measurements/adversarial/replay.py hf --names c00354 --label local_replay --jobs 1
python measurements/adversarial/cli_replay.py local_cli c00354 --kind hf
python -m adir.cli seeds targets/eval/fp_alu_cmp_hf.adversarial.yaml --local --run-dir measurements/adversarial/scratch/local_cli
```

`cli_replay.py` retains the original declaration/lint/conformance constraints;
it removes unrelated synthesis, fault and review nodes from this local numeric
check. No oracle, checker, stimulus or acceptance threshold is weakened.

The smaller decimal/checker/grouped/Booth/SFU/FMA probes and pytest regressions
rebuild their own fixtures. `fma_probe.py` obtains the pre-fix function from Git
without checking out or editing another tree. The compatibility scripts likewise
replace only the relevant Python function in memory and compare full emitted
RTL. `impact.py` and `recorded_impact.py` read historical data without changing it;
their counts describe vulnerable generated paths, not measured failure rates.
`area_probe.py` calls the underlying local synthesis function with `repeats=1`.

```sh
pytest -q tests/test_adversarial_rtl.py tests/test_mul_elaboration.py --basetemp measurements/adversarial/scratch/pytest_replay
```
