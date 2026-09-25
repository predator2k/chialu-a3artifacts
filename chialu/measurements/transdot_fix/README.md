# TransDot re-verification after the upstream fixes (2026-09-25)

TransDot at `pncel-develop-plus-comb` (upstream pncel/develop `cd3d062` + the combinational
16-bit point). Synthesis: median of 3 (base, 11, 23), Nangate45, medium, 300 ps;
`CHIALU_SYNTH_RECORDS=measurements/transdot_fix/artifacts`, so every run's RTL, scripts and
logs are archived here and replay with
`python -m chialu.synth_records <receipt> --measurement repeats3 --run N --artifacts measurements/transdot_fix/artifacts`.

* `results/transdot_transdot_merged_alu_core.json`: `remeasure.py jobs.json --repeats 3`.
* `hand_seed/`: `adir seeds targets/eval/fp_alu_cmp_transdot.hand_adaevolve.yaml --local`
  (record with the synthesis receipts, problem text, verify freeze, CLI log); `seeds.json`
  the hashes of the rebuilt hand seeds (`build_hand_seeds.py`).
* `tableb300/`: a3eval `sweeps/tableb.py --designs transdot_dp|transdot_no_dp --clock 300
  --repeats 3` rows (lint, conformance, ulp, synthesis receipts) and `classify_dot.py` classes.
* `conformance/`: a3eval `conform.py`/`classify.py` against `fp_alu_cmp_fpnew.yaml` (the
  standard contract), and the hand seed against the retired `fpnew_merged_16` contract.
* `underflow_ieee.json`: `python -m chialu.verify.reference_underflow_check --contract ieee`.

| design | area µm² / delay ps (median of 3) | runs r0 / r1 / r2 | before |
| --- | --- | --- | --- |
| merged alu_core | 4,503.114 / 3,966.73 | 4,503.1/3,966.7, 4,565.1/3,928.0, 4,335.3/4,121.1 | 4,609.248 / 3,923.53 (median of 5) |
| hand seed | 4,475.450 / 4,135.54 | 4,446.7/4,135.5, 4,475.5/4,137.7, 4,480.2/4,019.6 | 4,543.014 / 3,816.79 (median of 5) |
| Table B DP fp16 | 6,417.516 / 5,024.80 | 6,417.5/5,024.8, 6,349.2/5,021.0, 6,576.9/5,176.7 | 6,482.420 / 5,249.89 |
| Table B DP fp8 | 5,030.060 / 5,243.93 | 5,014.6/5,243.9, 5,167.3/5,174.9, 5,030.1/5,274.1 | 5,209.610 / 5,032.33 |
| Table B no-DP fp16 | 8,390.970 / 7,514.86 | 8,391.0/8,005.4, 8,331.4/7,192.8, 8,557.0/7,514.9 | 8,314.894 / 7,366.22 |
| Table B no-DP fp8 | 13,697.138 / 14,637.21 | 13,697.1/14,998.1, 14,261.6/14,637.2, 13,485.4/14,463.5 | 13,802.740 / 14,418.21 |

The earlier TransDot rows of `../median5/` measure the pre-fix RTL and are kept as history.
