# Table B: the dot-product unit

Table B compares chiALU's dot unit with the hand-designed units that compute
the same function, one row set per mode of TransDot's dot-product (DP) path,
as `3rdparty/chialu/docs/evaluation-plan.md` section 4 freezes it. Every row
below is measured through one flow: `chialu.eda.lint`, the conformance gate of
the seed's own bundle, `baselines/ulp_error.py` and `chialu.eda.synth_ppa` at
nangate45, medium effort (`sweeps/tableb.py`). The method rows (chiALU, the
generic backends, the plain loop) are the search's job and are not in this
file.

## The row sets

| row set | seed | function | contract of the seed | reference rows |
| --- | --- | --- | --- | --- |
| fp16 | `targets/eval/vec_dot_acc_cmp_fp16.yaml` (+ `.free_best_of_n`, `.free_beam_search`, `.free_adaevolve`) | two fp16 products + an fp32 addend into fp32 | `fused` (the exact 281-bit frame) | TransDot DP (`baselines/transdot/transdot_dot_core_fp16.sv`), TransDot no-DP FMA cascade (`baselines/transdot_no_dp/transdot_no_dp_dot_core_fp16.sv`), HardFloat MulAddRecFN cascade (`baselines/hardfloat_dot/`, two terms) |
| fp8 | `targets/eval/vec_dot_acc_cmp_fp8.yaml` (+ the three `free_*` copies) | four fp8e5m2 products + an fp32 addend into fp32 | `fused` (the exact frame; the row is exact, ulp 0) | TransDot DP (`baselines/transdot/transdot_dot_core_fp8.sv`), TransDot no-DP FMA cascade (`.../transdot_no_dp_dot_core_fp8.sv`), HardFloat MulAddRecFN cascade (four terms) |

The chiALU points beside the seeds: `vec_dot_acc_cmp_<row>_td.yaml` binds
TransDot's DP slot choices at the exact frame and `_tdw` adds
`core.window_bits: 76`, TransDot's `3p + 4` reduction word.

## The columns

* **area um2, delay ps, cells**: `synth_ppa` (yosys `read_slang`, ABC `&nf`
  with the buffering tail) at the run files' 40,000 ps target; `&nf` gives one
  point per design whatever the target (plan, section 3).
* **conformance (fused)**: the seed's bundle at `verify.n_random` 3000 beside
  the corner set (3,156 fp16 vectors, 3,153 fp8 vectors) against the fused
  reference, with the mismatch classes.
* **contract**: `fused` (one rounding of the exact dot product),
  `sequential` (every product rounded to fp32, then c and the products added
  one at a time with a rounding each), `window` (a reduction word that drops
  bits without a sticky).
* **max ulp, mean ulp**: the error of the packed fp32 result against the fused
  reference in ulp of the reference's binade, over the numeric vectors (an
  exact vector counts 0). The ulp of a normal reference is 2^(e - 23) for its
  binade exponent e; a zero or subnormal reference takes the smallest
  subnormal's spacing, 2^-149; a special result (a NaN or an infinity on
  either side) is a class rather than an error; two zeros of different sign
  are the `zero_sign` class with error 0. A correctly rounded design scores 0
  on every vector. `ulp_error.py` also reports the error against the exact
  rational dot product in the ulp of the exact value's binade (`vs the exact
  value`), where a correctly rounded design scores at most 0.5.
* **exact**: the fraction of vectors whose packed result equals the fused
  reference's bit for bit (a NaN counts when both are NaN).
* **exact vs sequential**: the same fraction against the sequential
  reference, which is the contract statement of an FMA cascade.

## The rows (nangate45, medium effort, 2026-09-19)

| row set | design | contract | area um2 | delay ps | cells | conformance (fused) | max ulp | mean ulp | exact | exact vs sequential |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| fp16 | TransDot DP | fused, out of a 76-bit window | 6,045.9 | 6,621.1 | 5,270 | FAIL 160 of 3,156: 2 `value`, 158 `nan_expected` | 1.0 | 0.0007 | 94.93% | 91.92% |
| fp16 | TransDot no-DP FMA cascade | sequential | 8,052.4 | 9,802.5 | 6,950 | FAIL 96 of 3,156: 96 `value` | 6.0 | 0.0326 | 96.96% | 99.97% (1 `zero_sign`) |
| fp16 | HardFloat MulAddRecFN cascade | sequential | 7,797.0 | 8,821.6 | 6,726 | FAIL 96 of 3,156: 96 `value` | 6.0 | 0.0326 | 96.96% | 99.97% (1 `zero_sign`) |
| fp16 | chiALU seed, the slot defaults (`vec_dot_acc_cmp_fp16.yaml`) | fused, exact frame | 15,771.9 | 9,639.6 | 14,037 | PASS | 0 | 0 | 100.00% | 96.93% |
| fp16 | chiALU, TransDot's slots (`_td`) | fused, exact frame | 21,925.8 | 12,047.4 | 19,267 | PASS | 0 | 0 | 100.00% | 96.93% |
| fp16 | chiALU, TransDot's slots and 76-bit window (`_tdw`) | fused, 76-bit window with a sticky | 11,484.0 | 10,834.0 | 10,377 | PASS | 0 | 0 | 100.00% | 96.93% |
| fp8 | TransDot DP | window | 4,969.1 | 6,662.4 | 4,326 | FAIL 1,621 of 3,153: 1,092 `value`, 409 `nan_expected`, 120 `inf_expected` | 83,886,080 | 384,882 | 48.59% | 48.02% |
| fp8 | TransDot no-DP FMA cascade | sequential | 11,764.9 | 19,360.0 | 9,912 | FAIL 87 of 3,153: 87 `value` | 8,388,608 | 5,362.6 | 97.24% | 99.90% (3 `zero_sign`) |
| fp8 | HardFloat MulAddRecFN cascade | sequential | 11,009.2 | 16,153.3 | 9,487 | FAIL 87 of 3,153: 87 `value` | 8,388,608 | 5,362.6 | 97.24% | 99.90% (3 `zero_sign`) |
| fp8 | chiALU seed, the slot defaults (`vec_dot_acc_cmp_fp8.yaml`) | fused, exact frame | 13,284.6 | 7,942.3 | 10,908 | PASS | 0 | 0 | 100.00% | 97.21% |
| fp8 | chiALU, TransDot's slots (`_td`) | fused, exact frame | 25,735.0 | 11,740.1 | 22,588 | PASS | 0 | 0 | 100.00% | 97.21% |
| fp8 | chiALU, TransDot's slots and 76-bit window (`_tdw`) | fused, 76-bit window with a sticky | 12,400.9 | 10,704.9 | 11,217 | PASS | 0 | 0 | 100.00% | 97.21% |

The library modules the chiALU seeds render: `fam_dot_pairwise_tree_n2_s11c24_a281lm149`
(fp16 defaults), `fam_dot_pairwise_tree_n4_s3c24_a281lm149` (fp8 defaults),
`fam_dot_multi_term_fused_dot_n2_s11c24_a281lm149` (fp16 `_td` and `_tdw`; the `_tdw`
reduction word is 76 bits) and `fam_dot_multi_term_fused_dot_n4_s3c24_a281lm149`
(fp8 `_td` and `_tdw`). chiALU's `_tdw` keeps a sticky of everything below the
76-bit word, so it is exact on both rows out of TransDot's own window width,
at 1.9 (fp16) and 2.5 (fp8) times TransDot DP's area.

The chiALU numbers here are measured at chiALU aa4a73e (branch `table-b`) in
the same run as the reference rows. `docs/coverage-gap-plan.md` of chiALU
records the fp16 seed at 16,880.9 um2 / 9,952.9 ps, the `_td` point at
21,609.8 / 11,062.2 and the `_tdw` point at 11,393.3 / 10,719.5 on 2026-09-18,
before the rounder change of aa4a73e; the table carries the later numbers.

## The contract statements

* **TransDot DP, fp16**: the two `value` vectors hold a negative product
  shifted out of the 36-bit alignment word entirely (a difference of 37
  binades or more) with no sticky bit, so the rounder sees an exact tie and
  rounds to even, one ulp above the correctly rounded result (a=[63605, 10768]
  b=[58433, 41092] c=0xc0000000: fused 0x4c17ada7, got 0x4c17ada8). The 158
  `nan_expected` vectors are the upper-lane special drop below.
* **TransDot DP, fp8**: the four products align in a 24-bit lane word with 14
  guard bits and no sticky; lanes 2 and 3 clamp their shift at 16 where the
  word needs 22 to flush, and lanes 0 and 1 carry a 6-bit shift amount into a
  5-bit shifter. The errors are gross: the histogram of the 1,092 `value`
  vectors is 47 in (0.5, 1], 41 in (1, 2], 29 in (2, 4], 32 in (4, 8], 17 in
  (8, 16], 97 in (16, 64], 556 in (64, 1024] and 273 above 1,024 ulp; the worst
  vector (a=[208, 108, 129, 230] b=[113, 59, 57, 220] c=0xc77418f2) gives
  0xc70618f2 where the fused result is 0x45cf3870, 83,886,080 ulp.
* **The upper-lane special drop (TransDot DP, both modes)**: only lane 0's
  operands and the fp32 addend reach the special-case detection, so a NaN or an
  infinity in a lane above the first yields a number: 158 of 3,156 fp16
  vectors, 529 of 3,153 fp8 vectors. The rows state it; it stays out of the ulp
  statistics and does not count against the fused contract of the fp16 row.
* **The FMA cascades (TransDot no-DP and HardFloat)**: both are bit-exact
  against chiALU's sequential reference on every vector but the `zero_sign`
  class (an exact cancellation gives +0 under IEEE 754, where the sequential
  reference keeps the chain's first term's sign: 1 fp16 vector, 3 fp8
  vectors), and they agree with each other on every vector. Against the fused
  reference their 96 (fp16) and 87 (fp8) `value` vectors are the double
  rounding of the sequential contract: 93 of the 96 fp16 vectors and 77 of the
  87 fp8 vectors lie in (0.5, 1] ulp; the fp8 vectors above 1,024 ulp (3) are
  exact cancellations whose fused result is tiny (a=[62, 190, 61, 191]
  b=[189, 191, 189, 190] c=0xbfe80001: fused 0xb4000000 = -2^-23, the cascade
  0, a whole binade of the result, 2^23 ulp).

## The commands

On the EDA host, with the chiALU worktree `table-b` at `~/scratch/tableb_tree`
and this tree at `~/chialu-verification/snapshots/a3eval-tableb` (the fork's
`transdot_fp4_fp8_fp16_fp32_fma.sv` patched once by
`baselines/transdot/tdot_comb.py`):

```
export CHIALU=$HOME/scratch/tableb_tree
export PYTHONPATH=$CHIALU:$CHIALU/third_party/adir CHIALU_SYNTH_REPORT=0 CHIALU_VERILATOR_JOBS=3
RUNS=$HOME/chialu-verification/runs/a3eval/tableb
python3 baselines/transdot/build_dp.py --row fp16 fp8 --no-synth --out $RUNS/transdot_dp
python3 baselines/transdot_no_dp/build.py --no-synth --out $RUNS/transdot_no_dp
SBT=$HOME/tools/sbt/bin/sbt bash baselines/hardfloat_dot/build.sh $RUNS/hardfloat_dot
python3 sweeps/tableb.py --out $RUNS --n-random 3000 --clock 40000
python3 sweeps/tableb.py --out $RUNS --table --details
```

`sweeps/tableb.py` writes one JSON per (design, row) under `$RUNS`; the copies
of this run are under `tables/table_b/`. One design alone:

```
python3 baselines/ulp_error.py --target $CHIALU/targets/eval/vec_dot_acc_cmp_fp16.yaml \
    --rtl $RUNS/transdot_dp/transdot_dp_dot_core_fp16.sv --n-random 3000
```
