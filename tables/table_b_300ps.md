# Table B at the least-delay mapping (clock_ps 300), 2026-09-24 (median of five)

`python3 sweeps/tableb.py --out runs/tableb300 --clock 300` after the reference builds (`baselines/transdot/tdot_comb.py` first for TransDot's DP core). TransDot rows (2026-09-25): re-measured after TransDot's upstream fixes (pncel/develop `cd3d062`: FP8 DP alignment, DP NaN/Inf lanes, UF tininess index, SIMD staging) at the median of 3 (base, 11, 23), conformance and ULP re-run; receipts in chiALU `measurements/transdot_fix/`. Before: DP fp16 6,482.4 / 5,249.9, FAIL 160 (158 `nan_expected`, 2 `value`); DP fp8 5,209.6 / 5,032.3, FAIL 1621 (1,092 `value`, 409 `nan_expected`, 120 `inf_expected`); no-DP fp16 8,314.9 / 7,366.2, fp8 13,802.7 / 14,418.2 (median of 5). Now DP fp16 fails on 2 one-ulp `value` vectors and DP fp8 on 591 `value` vectors (the window contract). Supersedes the single-run table, retained in `frozen/2026-09-23/tableb/`. Synthesis receipts and all runs are in `measurements/median5/`; conformance and ULP evidence are unchanged.

| design | row | contract | area um2 | delay ps | cells | conformance (fused) | max ulp | mean ulp | exact | exact vs sequential |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| chialu_seed | fp16 | fused (exact frame) | 18,033.5 | 7,513.0 | 14,840 | PASS | 0.0 | 0.0000 | 100.00% | 96.93% |
| chialu_seed | fp8 | fused (exact frame) | 15,994.0 | 6,877.0 | 13,159 | PASS | 0.0 | 0.0000 | 100.00% | 97.21% |
| chialu_td | fp16 | fused (exact frame, TransDot's slots) | 24,003.0 | 9,036.3 | 19,554 | PASS | 0.0 | 0.0000 | 100.00% | 96.93% |
| chialu_td | fp8 | fused (exact frame, TransDot's slots) | 27,312.6 | 9,540.0 | 23,274 | PASS | 0.0 | 0.0000 | 100.00% | 97.21% |
| chialu_tdw | fp16 | fused (TransDot's slots and window) | 12,619.3 | 8,766.3 | 10,064 | PASS | 0.0 | 0.0000 | 100.00% | 96.93% |
| chialu_tdw | fp8 | fused (TransDot's slots and window) | 12,997.3 | 8,458.7 | 10,880 | PASS | 0.0 | 0.0000 | 100.00% | 97.21% |
| hardfloat_dot | fp16 | sequential | 8,302.7 | 7,302.1 | 6,804 | FAIL 96 of 3156 | 6.0 | 0.0326 | 96.96% | 99.97% |
| hardfloat_dot | fp8 | sequential | 11,617.8 | 13,436.5 | 9,142 | FAIL 87 of 3153 | 8388608.0 | 5362.6397 | 97.24% | 99.90% |
| transdot_dp | fp16 | fused (fp16, out of a 76-bit window) / window (fp8) | 6,417.5 | 5,024.8 | 5,301 | FAIL 2 of 3156 | 1.0 | 0.0006 | 99.94% | 96.93% |
| transdot_dp | fp8 | fused (fp16, out of a 76-bit window) / window (fp8) | 5,030.1 | 5,243.9 | 4,225 | FAIL 591 of 3153 | 393056.0 | 125.3863 | 81.26% | 80.72% |
| transdot_no_dp | fp16 | sequential | 8,391.0 | 7,514.9 | 6,673 | FAIL 96 of 3156 | 6.0 | 0.0326 | 96.96% | 99.97% |
| transdot_no_dp | fp8 | sequential | 13,697.1 | 14,637.2 | 9,928 | FAIL 87 of 3153 | 8388608.0 | 5362.6397 | 97.24% | 99.90% |

## 2026-09-24: median-of-five re-measurement

The current synthesis metric is the independent median of five ABC mappings: base, then
`permute -S 11/23/37/53` after `strash`, Nangate45, medium effort, clock 300 ps for evaluation
targets and references. All requested mappings must succeed; failures invalidate the fitness
while retaining every run. The other target baselines use the clock recorded in their target.

| Design | single area / delay | median area / delay |
| --- | ---: | ---: |
| int_subword_alu | 5,743.472 / 1,735.74 | 5,720.596 / 1,782.62 |
| fp_alu_cmp | 7,283.612 / 4,318.54 | 7,283.612 / 4,420.99 |
| fp_alu_cmp_hf | 6,350.218 / 4,365.67 | 6,463.002 / 4,520.69 |
| fpnew_fpnew_merged_alu_core | 4,873.652 / 3,705.08 | 4,833.752 / 3,575.36 |
| fpnew_fpnew_parallel_alu_core | 6,163.486 / 3,681.84 | 6,194.076 / 3,705.05 |
| transdot_transdot_merged_alu_core | 4,503.114 / 4,013.49 | 4,609.248 / 3,923.53 (pre-fix RTL; 2026-09-25 median of 3: 4,503.114 / 3,966.73) |
| hardfloat_alu_core | 5,419.484 / 2,800.75 | 5,420.548 / 2,800.75 |

All 31 baselines/reference designs, including both Table B slot/window variants, are in
[the complete single/per-run/median table](../measurements/median5/BASELINES.md).
Each linked JSON retains area, delay, cells, status, seconds, seeds, exact scripts, RTL/checkpoint,
liberty and tool identities, plus complete log references. [Cost measurements](../measurements/median5/COST.md)
cover repeats 1/5 and internal concurrency. Attribution reports describe a separate recorded
name-kept base mapping; metric cells identify the area-median representative run.

Earlier dated numbers in this document are historical single-synthesis results. Do not compare
legacy front/seed/surrogate measurements with these medians without re-measuring them. The 9,704
integer labels and 16,446-row structure DB were not rebuilt here; they remain a lead-run task.
