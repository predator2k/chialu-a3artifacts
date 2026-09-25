# Evaluation plan

Current PPA baselines: [2026-09-24 median-of-five re-measurement](#2026-09-24-median-of-five-re-measurement). Earlier dated tables retain their historical flow.

This plan decides how chiALU is compared with other LLM-driven RTL
optimization under one budget, which is the main comparison, with
itself under ablation, and with hand-designed open-source units, which
serve as reference points and as starting designs rather than as
competitors. Every unit that enters a table runs the same synthesis
flow at the same synthesis target (each design's least-delay mapping,
section 3) and the same conformance gate.

## 0. The numerical behavior of every reference design is modeled first

No area or delay of a reference design or of a starting design enters
a table before its numerical
behavior is established and written down as a bit-exact reference in
the verify layer, so that both units are asked for the same function.
A unit that rounds once per operation and a unit that truncates partial
sums into a window are different functions, and the smaller one is not
the better design.

What is modeled, per reference design and per operation:

* the rounding contract: one rounding of the exact result, a rounding
  per stage (which stages, in which order), or a window with truncation
  and a sticky bit (its width, its anchor, how the sticky enters the
  rounding);
* the rounding modes implemented and how the mode is selected;
* subnormal handling: full support, flush on input, flush on output,
  and the tininess rule (before or after rounding);
* NaN and infinity conventions: the payload delivered, signaling NaN
  treatment, NaN propagation in min and max, the zero-sign rules, and
  the fp8 encodings (IEEE-like E5M2 against OCP E4M3 without infinities);
* the flags reported, the condition that raises each, and their scope:
  one word per result or one word for the whole operation;
* integer results: wrap or saturate;
* for a dot product: the accumulation contract (exact sum, cascade of
  FMAs with a rounding each, or a window), the treatment of an addend far
  larger or far smaller than the products, and the element order when
  rounding is per stage.

How it is established:

1. From the RTL and the documentation, the contract of each operation
   is written as a candidate reference in the terms of
   `docs/formats-and-options.md` (`rounding`, `daz_in`, `ftz_out`,
   `tininess`, `nan_payload`, `minmax_nan`, `dot_contract`, ...).
2. The reference design runs the corner and random vectors of the verify bundle
   against that reference in differential simulation; every mismatch is
   classified (subnormals, NaN payload, flags, rounding, window) until
   the reference reproduces the design bit for bit or the residual
   classes are listed.
3. A behavior our options do not express is added to the spec and the
   verify layer before the comparison (for example `dot_contract:
   window` with `window_bits` and the sticky rule, if TransDot's DP mode
   turns out to be windowed), or the row is excluded with a statement.
   `flag_scope` is the option this step added for FPnew, which reports
   one status for a vectorial op where chiALU reported one word per
   result.
4. The comparison target binds the options that reproduce the reference design,
   so chiALU is asked for the same function, and one conformance gate
   judges both units.

Where two contracts cannot be made equal, both numbers appear with the
contract named and an accuracy column, which is the maximum error in ulp
of the destination format over the vectors, rather than in one column.
The fused contract with an fp32 addend forces an exact frame of 281 bits,
which no commercial tensor core implements, so Table B in particular is
meaningless until TransDot's DP contract is pinned.

## 1. Reference designs

Three open-source units are the reference designs: the points that say
what a hand-designed unit of the same function costs, and the starting
designs of section 4's second experiment. The user named them; the
comparison configurations below match the unit classes chiALU serves.

| Reference design | Source | Language / license | What it covers | Comparison configuration |
| --- | --- | --- | --- | --- |
| Berkeley HardFloat | github.com/ucb-bar/berkeley-hardfloat | Chisel / BSD-3 | `AddRecFN`, `MulRecFN`, `MulAddRecFN`, `CompareRecFN`, conversions; any (expWidth, sigWidth); combinational; all five IEEE rounding modes; tininess before or after rounding; subnormals; five exception flags | one module per (format, op) with `recFNFromFN` / `fNFromRecFN` at the boundary; fp16 = (5, 11), bf16 = (8, 8), fp8e5m2 = (5, 3); a second design point shares add and mul in one `MulAddRecFN` per format |
| FPnew / CVFPU | github.com/openhwgroup/cvfpu (develop) | SystemVerilog / Solderpad | FP32/FP64/FP16/FP8 (E5M2)/FP16ALT (bf16); op groups ADDMUL, DIVSQRT, NONCOMP, CONV; packed SIMD for formats narrower than `Width`; `PipeRegs` 0 is combinational; `UnitTypes` PARALLEL or MERGED per format; `minimumNumber` / `maximumNumber` min and max; subnormals | `Width` 16, `EnableVectors` 1, `EnableNanBox` 0, `FpFmtMask` {FP16, FP16ALT, FP8}, `IntFmtMask` 0, ADDMUL and NONCOMP enabled, DIVSQRT and CONV disabled, `PipeRegs` 0; two design points: ADDMUL MERGED and ADDMUL PARALLEL (NONCOMP is PARALLEL only) |
| TransDot | github.com/pncel/TransDot (develop) | SystemVerilog / Apache-2.0 | FPnew extended with a transprecision dot-product mode: 2-term FP16, 4-term FP8, 8-term FP4 accumulated into FP32, plus SIMD FMA in the same datapath; formats FP32, FP16, BF16, FP8 E4M3, FP8 E5M2, FP4; `NumPipeRegs` defaults to 0; the FP4 path is an exact quarter-unit dot product; the paper's numbers are TSMC 28 nm Genus at 1 GHz with three pipeline registers | `transdot_fp4_fp8_fp16_fp32_fma` with `NumPipeRegs` 0 and `FpFmtConfig` limited to the formats of the comparison mode; the no-DP variant (`transdot_no_dp/`) is the FPnew-class SIMD FMA point |

Facts the configurations rest on:

* CVFPU's package declares five formats (`NUM_FP_FORMATS = 5`) and no
  E4M3; TransDot's fork adds E4M3 and FP4. chiALU's `fp8e4m3` is the OCP
  encoding without infinities, so no reference design matches it bit for bit.
  The comparison targets use `fp8e5m2`, whose encoding is IEEE-like and
  is CVFPU's FP8 and HardFloat's (5, 3).
* FPnew implements min and max as `minimumNumber` / `maximumNumber`.
  chiALU's `minmax_nan: number` is that rule; the targets bind it.
* FPnew's CMP returns one relation per operation (LE, LT or EQ selected
  by the rounding-mode field); chiALU's `fcmp` returns the three bits
  {gt, eq, lt} at once. The FPnew wrapper drives CMP with EQ and LT and
  derives gt, which costs FPnew nothing in hardware because the NONCOMP
  slice computes the relations together; the report states the asymmetry.
* HardFloat has no min/max module; its wrapper builds min and max from
  `CompareRecFN` and a mux, and the report lists that mux as wrapper cost.
* Both reference designs implement every rounding mode in hardware. The
  comparison targets provision `rounding: runtime: [RNE, RTZ, RDN, RUP]`
  so chiALU does not gain from a two-mode datapath.
* The generated checker is a separate artifact and `alu_core` /
  `dot_core` are synthesized alone, so the checker's area never enters
  the comparison. The comparison targets still bind `check_en: false`
  to keep the fault gate out of the loop.

## 2. Comparison targets

Three run files under `targets/eval/` are the comparison points. They
copy the existing targets and change only the variables below. Each
reference design is measured against a chiALU unit of its own function:
`fp_alu_cmp.yaml` is FPnew's and TransDot's (FPnew PARALLEL is bit-exact
against it, MERGED and TransDot differ in 24 underflow flags of a
subnormal fmul), and `fp_alu_cmp_hf.yaml` is HardFloat's. HardFloat's
wrapper has no fp8 adder, so `fp_alu_cmp_hf.yaml` is `fp_alu_cmp.yaml`
with the fp8e5m2 mode restricted to `fmul, fmin, fmax, fcmp` (a mode's
own `ops`), and HardFloat is bit-exact against it over 380,140 vectors
(2026-09-23). A reference measured against a unit whose function it
lacks is not a comparison, which is why the HardFloat row does not stand
against `fp_alu_cmp`.

| Variable | `fp_alu_cmp.yaml` | `vec_dot_acc_cmp.yaml` |
| --- | --- | --- |
| `modes` | `{count: 1, fp16}`, `{count: 1, bf16}`, `{count: 2, fp8e5m2}`; in `fp_alu_cmp_hf.yaml` the fp8e5m2 mode carries `ops: [fmul, fmin, fmax, fcmp]` | `{elements: 2, fp16 -> fp32, c fp32}`, `{elements: 4, fp8e5m2 -> fp32, c fp32}`; the existing `4 x fp16 -> fp32` and `4 x int8 -> int32` modes stay in a third file for the internal tiers, since no named reference design serves them |
| `ops` | `fadd, fsub, fmul, fmin, fmax, fcmp` | not applicable (`accumulate: true`) |
| `rounding` | `runtime: [RNE, RTZ, RDN, RUP]` | `fixed: RNE` |
| `minmax_nan` | `number` | unchanged |
| `daz_in`, `ftz_out`, `tininess` | `false`, `false`, `after` | same |
| `flags` | `[invalid, overflow, underflow, inexact]` | `[]` |
| `flag_scope` | `per_operation`: one flag word for the whole operation, which is FPnew's one status per vectorial op | not applicable |
| `dot_contract` | not applicable | `fused` in the mixed file and in both one-mode seeds of Table B (`vec_dot_acc_cmp_fp16.yaml`, `vec_dot_acc_cmp_fp8.yaml`); TransDot's two-term fp16 DP mode meets it and its four-term fp8e5m2 mode does not (section 8's risks), so the fp8 row set carries the accuracy column of section 4; the two FMA cascades (TransDot's no-DP FMA, HardFloat's `MulAddRecFN`) are measured under the `sequential` contract of the same seeds' references, which `baselines/ulp_error.py` computes beside the fused one |
| `check_en` | `false` | `false` |
| `clock_ps` | 300 ps, the least-delay mapping of section 3 (`min_delay` in `targets/make_targets.py`) | the same 300 ps (re-measured 2026-09-23) |
| `core.*` | `search: all` | `search: all` |

The interface of the rendered seed is the interface every wrapper
presents: `alu_core(a[15:0], b[15:0], op[2:0], mode[1:0],
rounding_sel[1:0], y[15:0], flags[3:0])` and `dot_core(a[31:0], b[31:0],
c[31:0], mode, d[31:0])`. The ALU's flag word is four bits rather than
eight because `flag_scope: per_operation` reports one word for the whole
operation. The wrappers live in
`eval/baselines/<name>/` beside a script that regenerates them:

* `hardfloat/`: a Chisel module per design point instantiating the
  HardFloat cores with the format parameters, emitted to Verilog by the
  repository's sbt flow;
* `fpnew/`: an `fpnew_top` instance per design point, the op and mode
  decode, and the CVFPU file list;
* `transdot/`: an instance of the DP FMA per mode set and the same
  decode; `transdot_dot_core_fp16.sv` and `transdot_dot_core_fp8.sv` are
  the one-mode DP wrappers of Table B;
* `transdot_no_dp/`: TransDot's no-DP SIMD FMA
  (`transdot_fp16_fp32_fma_simd`) chained per term into fp32, the
  sequential-contract reference row of Table B from TransDot;
* `hardfloat_dot/`: HardFloat's `MulAddRecFN` on fp32 chained per term,
  the elements widened exactly through `RecFNToRecFN`, emitted by the
  repository's sbt flow.

Every wrapper is synthesized twice: with the decode and boundary
conversion (the number that enters the tables) and bare (the reference
design's own cost, reported in a column of its own), so the wrapper overhead is
visible rather than argued about.

## 3. Flow, clocks and metrics

* **Scope**: every unit compared is combinational, since chiALU's units
  are single-cycle in this version (README, `docs/deferred-families.md`);
  a reference design enters the tables in its register-free configuration.
* **Synthesis**: `chialu.eda.synth_ppa` (yosys through `read_slang`,
  then ABC under the PDK's liberty with the buffering tail
  `buffer;upsize -D;dnsize -D`), `effort: medium`, one run per design at
  the least-delay target below. nangate45
  is the primary PDK; asap7 repeats the fp16 rows for the RTLScout
  comparison of section 5. sky130hd is not used here.
No number measured before 2026-09-17 belongs in a table with one
measured after it. The mapper gained the buffering tail and yosys gained
the slang frontend that day, which moved area and delay on every design,
so the synthesis database, the tier-2 sweep and the reference designs'
numbers were all deleted rather than carried forward.

* **One mapping per design, for its least delay** (revised 2026-09-23).
  ABC's `&nf -D` is inert in this build (the medium script maps the
  `int_subword_alu` baseline identically at D = 1 and D = 1,000,000), so
  the target reaches the netlist only through the one buffering pass
  `buffer; upsize -D; dnsize -D`. That pass does not track a clock: it
  switches between two mappings. The tier-2 sweep showed it on every
  seed: `fp_alu_cmp`'s baseline mapped to 7,283.6 um2 / 4,319 ps at
  2,800, 3,500 and 4,200 ps alike and to 6,991.0 / 5,226 ps at 7,000 ps,
  and even the tight mapping missed the tight targets it was given. A
  sweep of clock targets therefore measures the threshold, not an
  area-delay curve, so the ALU comparison targets synthesize at one
  target below any design's reach, 300 ps (`MIN_DELAY_PS` in
  `targets/make_targets.py`): every design maps for its least delay, the
  buffering is the single pass above (no iterative buffering), and area
  is reported beside the delay rather than optimized under a clock. The
  constraints that compared a delay to `clock_ps` are gone; the search's
  Pareto front stays over area and delay. The reference designs' numbers
  are the same mapping (their tight-target column). There is no d_min
  and no clock grid. The classic mapper (`map -D`, `CHIALU_ABC_FLOW=map`)
  does respond to its target, but it is two to three times slower on the
  dot seed and is not the flow of the tables. Table B's dot targets and
  its reference rows follow the same rule; the table was re-measured at
  300 ps on 2026-09-23 (chialu-a3eval `tables/table_b_300ps.md`), its
  contracts unchanged.
* **Metrics**: `area_um2`, `delay_ps` (ABC's post-mapping delay),
  `cells`. Power is out of scope until an OpenSTA step exists in the
  flow, and no reference number from another flow (TransDot's Genus 28 nm
  figures, Ten-Four's Design Compiler ASAP7 figures) is placed in a table
  next to ours.
* **Conformance**: every reference wrapper runs through the target's own
  `verify_bundle` with `verify.n_random` raised to 20000 and the corner
  set of the format grammar. Verilator is the one simulator, and it reads
  the generated SystemVerilog and each wrapper as written. A wrapper that fails the gate is reported
  with the failing class (subnormals, NaN payload, flags) rather than
  silently dropped. In the other direction chiALU's fp16 units run the
  Berkeley TestFloat level-1 vectors for `f16_add`, `f16_mul`, `f16_eq`,
  `f16_lt` and `f16_le` under the four rounding modes through a small
  Verilator harness; bf16 and fp8 have no TestFloat vectors and rest on
  our reference alone.

## 4. The main comparison: LLM-driven optimization under one budget

Every method in this section optimizes the same unit from the same
starting program through the same evaluator (the target's graph:
declaration, lint, conformance, synthesis at the least-delay target) under
the same model and the same number of model calls. The rows of Table A
are methods; the reference designs of section 1 stand at the foot of
the table and as points in the figure.

| Row | Method | Shares with chiALU | Lacks |
| --- | --- | --- | --- |
| chiALU | the run file of section 2 in full: the enumerated sharing schemes and the database search under them, the database timing source, the knowledge cards, structured declarations with replan, the review gate | everything | |
| generic code evolution | ADIR's `best_of_n`, `beam_search` and `adaevolve` backends (SkyDiscover's `evox` search type fails on a prompt file its package lacks; the `openevolve` and `shinkaevolve` backends need their own packages, which the host lacks) with `prompts.sources: []`, `knowledge_depth: path` on an empty directory, `operator: [free]`, `replan: false`, `discover: 0`, over a plain program: the baseline as the generator renders it with its declaration block emptied and every library annotation (the structure, unit, library and hierarchy manifests, the `structure core.<slot>` lines, the region markers) removed (`targets/seeds/<target>.baseline.sv`, `targets/make_plain_seeds.py`), the whole text one region (`evolve: ["*"]`), and the graph without the review and the per-unit synthesis, which read a declaration; the prompt names no decision, no declaration block and no library option (`prompts.declarations: false`, `prompts.omit_vars`), no plan from `discovered.json` enters (`seeds.discovered: false`), and the fault gate's checker is the frozen one: the AlphaEvolve-style rewrite of the same program. The plain programs measure what the baselines do (int 5,743.5 / 1,735.7 with the fault gate, fp 7,283.6 / 4,318.5, hf 6,350.2 / 4,365.7); Table B's generic rows start from the dot seeds' plain programs the same way | the baseline program (chiALU starts from its numeric front instead, which is part of its method), the evaluator and its gates, the model, the iterations | the library, the plans, the database, the cards, the review |
| plain agent loop | one agent CLI (opencode on the same model) given the same plain program, the evaluator command and the metrics, asked to improve the unit for 20 calls, one attempt and one candidate each (the same `targets/seeds` program as the generic rows), without ADIR (`harness/plain_loop.py`; the fault gate of `int_subword_alu` included) | the seed, the evaluator and its gates, the model, the iterations | every ADIR mechanism, the archive and the prompt composition included |
| RTLScout | its own fp16 `fpmul_f16` and `fpadd_f16` problems (section 5) under our conformance gate | the model, the call count | the multi-format unit |

Table A has two halves, one per ALU target, and every method row runs
on both: `fp_alu_cmp` with FPnew (MERGED and PARALLEL) and TransDot's
ALU-class point at its foot, `fp_alu_cmp_hf` with HardFloat at its foot.
`int_subword_alu` is the integer control, with no reference design.
Table A's columns for a method row: the hypervolume of the (area,
delay) front in one fixed box per half, from the origin to 1.2 times the
baseline's area and delay (`eval/tables/make_table.py --box-factor`), so
the box does not move with the rows' results and a point outside it
scores nothing, the
best area, the least delay, the feasible fraction, the model calls to
95% of the final hypervolume, synthesis minutes and tokens, every design
at its least-delay mapping. The reference rows carry area, delay,
cells, wrapper overhead and the conformance verdict at the same mapping;
the no-model rows (tier 2: the baseline seed, the numeric stage's front
seeds and the `chialu.prune --best delay` point, with the library
realizing every structure and no model in the loop) carry the same
columns as the references.

A second experiment starts every method from a hand design instead of
a generated seed: FPnew's PARALLEL point behind the target's interface
is the seed program (bit-exact against `fp_alu_cmp`; the MERGED point
fails 24 underflow flags and would start infeasible), the declarations
are empty, every file of the design (the wrapper and every CVFPU source
it pulls in, joined into one text) is open to the rewrite, and chiALU
runs in its free operator with the knowledge cards and the timing
source, against the generic backends and the plain loop
under the same budget (`fp_alu_cmp.hand_<variant>.yaml`, the plain loop
`--seed ... --fpnew-point PARALLEL`). The hand design has no structures
behind it, so these runs evaluate the whole `alu_core` as one region
(lint, conformance, the gate-count screen, synthesis) without the review
and the per-unit synthesis, which read a declaration; the seed measures
6,163.5 um2 / 3,681.8 ps. This is the problem shape of
RTLScout and of AlphaEvolve's circuit work, and it shows whether the
method improves a design people already use.

Table B, the dot-product unit, is frozen on the per-mode contract of
TransDot's DP path (section 8), so it carries one row set per DP mode,
and each row set has the method rows of Table A over its own seed. The
seed's own delay is a starting point rather than a prerequisite, and the
gap between chiALU's unit and the TransDot configuration that computes
the same function is what a row reports.

* **The fp16 row set** computes two fp16 products with an fp32 addend
  into fp32 under the fused contract, one rounding of the exact dot
  product, which is TransDot's own function in this mode. Its seed is
  `targets/eval/vec_dot_acc_cmp_fp16.yaml` (the slot defaults, the exact
  281-bit frame) with the three `free_*` copies as the generic-evolution
  controls. `vec_dot_acc_cmp_fp16_td.yaml` binds TransDot's slot choices
  and `_tdw` adds its 76-bit window; both stand in the table as chiALU
  points rather than as method rows.
* **The fp8e5m2 row set** computes four fp8e5m2 products with an fp32
  addend into fp32. TransDot's accumulation in this mode is windowed
  rather than exact (section 8 gives the mechanism), so every design in
  the set states its contract (`fused`, `sequential`, `window`) and the
  set carries the accuracy column below beside area and delay. Its seed
  is `targets/eval/vec_dot_acc_cmp_fp8.yaml` (the options of the fp16
  file on the fp8 mode; the slot defaults keep the exact frame, so
  chiALU's row is exact and its ulp column is 0) with its three `free_*`
  copies; `vec_dot_acc_cmp_fp8_td.yaml` and `_tdw` are the TransDot-slot
  points.

The reference rows of each set are combinational and each stands behind
the seed's `dot_core(a[31:0], b[31:0], c[31:0], d[31:0])` (chialu-a3eval,
`baselines/`):

* TransDot's DP mode (`transdot/transdot_dot_core_fp16.sv`,
  `transdot/transdot_dot_core_fp8.sv`): the fork's
  `transdot_fp4_fp8_fp16_fp32_fma` at `NumPipeRegs` 0 under the
  `COMBINATIONAL` patch, driven at `TDOT_DP_FMADD` with `FpFmtConfig`
  limited to FP32 and the mode's format; contract `fused` out of a
  76-bit window for fp16, `window` for fp8.
* TransDot's no-DP SIMD FMA (`transdot_no_dp/`): the fork's
  `transdot_fp16_fp32_fma_simd` (the ADDMUL unit of its `fpnew_top` under
  `SIMD_ENABLE`) chained per term, each stage fp16 x fp16 + fp32 or
  fp8e5m2 x fp8e5m2 + fp32 into fp32; contract `sequential`.
* HardFloat's FMA cascade (`hardfloat_dot/`): `MulAddRecFN` on fp32
  chained per term, the elements widened exactly through `RecFNToRecFN`;
  contract `sequential`.

An fp16 or fp8 product is exact in fp32, so a cascade of fused
multiply-adds computes chiALU's `sequential` contract (each product
rounded to `format_d`, then c and the products added in element order
with a rounding each), and both cascades are bit-exact against that
reference on every vector but the zero-sign class below.

The columns of a Table B row:

* area, delay and cells at nangate45, medium effort, from
  `chialu.eda.synth_ppa` at the run files' 40,000 ps target (`&nf` gives
  one point per design whatever the target, section 3);
* the conformance verdict against the fused reference over the seed's
  bundle at `verify.n_random` 3000 beside the corner set (3,156 fp16 and
  3,153 fp8 vectors), with the mismatch classes;
* the contract;
* the accuracy column: the maximum and the mean error of the packed
  `format_d` result against the fused reference, in ulp of the
  reference's binade, over the same vectors. `baselines/ulp_error.py`
  states the definition: the ulp of a normal reference is 2^(e - 23) for
  its binade exponent e, a zero or subnormal reference takes the smallest
  subnormal's spacing 2^-149, a special result is a class rather than an
  error, and a correctly rounded design scores 0 on every vector (the
  tool also reports the error against the exact rational value, where
  such a design scores at most 0.5).

Two differences are stated on rows rather than counted as mismatches
(section 7's rule):

* TransDot drops a special value in a lane above the first, in both DP
  modes: only lane 0's operands and the addend reach its special-case
  detection, so a NaN or an infinity in an upper lane yields a number
  (158 of the 3,156 fp16 vectors, 529 of the 3,153 fp8 vectors). Those
  vectors form the `nan_expected` and `inf_expected` classes of
  TransDot's rows, stay out of the ulp statistics, and do not count
  against the fused contract of its fp16 row.
* The cascades give +0 for an exact cancellation, as IEEE 754 does under
  RNE, where chiALU's sequential reference keeps the chain's first term's
  sign (1 fp16 vector, 3 fp8 vectors): the `zero_sign` class.

The reference rows and the chiALU points at the least-delay mapping (300 ps),
measured on 2026-09-23 (`sweeps/tableb.py --clock 300` of chialu-a3eval;
`tables/table_b_300ps.md` there holds the rows and `tables/table_b.md` the
2026-09-19 table at 40,000 ps with the commands, the histograms and the
worst vectors; the conformance and ulp columns are the same in both):

| row set | design | contract | area um2 | delay ps | cells | conformance (fused) | max ulp | mean ulp |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| fp16 | TransDot DP | fused (76-bit window) | 6,341.7 | 5,445.8 | 5,270 | 160 of 3,156: 2 value, 158 upper-lane specials | 1 | 0.0007 |
| fp16 | TransDot no-DP FMA cascade | sequential | 8,612.3 | 7,966.3 | 6,950 | 96 of 3,156 | 6 | 0.0326 |
| fp16 | HardFloat MulAddRecFN cascade | sequential | 8,106.6 | 7,302.1 | 6,726 | 96 of 3,156 | 6 | 0.0326 |
| fp16 | chiALU seed, the slot defaults | fused | 17,285.2 | 7,892.0 | 13,959 | bit-exact | 0 | 0 |
| fp16 | chiALU, TransDot's slots (`_td`) | fused | 22,692.7 | 9,680.0 | 19,445 | bit-exact | 0 | 0 |
| fp16 | chiALU, TransDot's slots and 76-bit window (`_tdw`) | fused | 12,619.3 | 8,851.7 | 10,064 | bit-exact | 0 | 0 |
| fp8 | TransDot DP | window | 5,417.1 | 5,142.2 | 4,326 | 1,621 of 3,153: 1,092 value, 529 upper-lane specials | 8.4 x 10^7 | 3.8 x 10^5 |
| fp8 | TransDot no-DP FMA cascade | sequential | 13,564.4 | 15,360.7 | 9,912 | 87 of 3,153 | 8.4 x 10^6 | 5,363 |
| fp8 | HardFloat MulAddRecFN cascade | sequential | 11,578.4 | 13,593.3 | 9,487 | 87 of 3,153 | 8.4 x 10^6 | 5,363 |
| fp8 | chiALU seed, the slot defaults | fused | 17,591.4 | 7,732.2 | 13,724 | bit-exact | 0 | 0 |
| fp8 | chiALU, TransDot's slots (`_td`) | fused | 37,789.8 | 11,925.6 | 30,703 | bit-exact | 0 | 0 |
| fp8 | chiALU, TransDot's slots and 76-bit window (`_tdw`) | fused | 12,997.3 | 8,702.7 | 10,880 | bit-exact | 0 | 0 |

The cascades' worst vectors are exact cancellations: the fp8 maximum is
a sum whose fused result is -2^-23 and whose sequential chain rounds the
remainder away to zero, a whole binade of the result (2^23 ulp). The
chiALU fp16 seed measured 16,880.9 um2 / 9,952.9 ps on 2026-09-18
(section 8, item 1) and 15,771.9 / 9,639.6 on 2026-09-19 at aa4a73e; the
table carries the later number, measured in the same run as the
reference rows.

Figure 1 plots area against delay for Tables A and B: the fronts of the
methods as markers, the reference designs and the tier-2 seeds as
points, one panel per PDK.

## 5. Prior LLM-driven RTL optimization

RTLScout (Huawei, BSD-3-Clause-Clear, github.com/huawei-csl/rtlscout)
is the one open system whose benchmark is a floating-point unit:
`fpmul_f16` and `fpadd_f16` with subnormals, ASAP7, yosys and OpenROAD,
Claude Opus 4.6, 30 agent steps per run and six runs; its `fpmul_f16`
starting point is 84 to 121 um2 and 1458 to 1618 ps depending on the
README and the paper, and its result is 79 um2 at 891 ps.

* **Same problem, both systems**: a chiALU ALU with one fp16 mode and
  the op set `{fmul}` and one with `{fadd, fsub}` on asap7 at their clock
  targets (900, 1200, 1700 ps); RTLScout's starting designs and their
  testbench are run through our conformance gate first so both sides
  are judged by one reference. Both systems run under the same model and
  the same number of model calls; RTLScout's phase 3 sweep counts as
  node runs.
* **Same framework, generic search**: the generic code evolution row of
  section 4, which is the control for every claim about the structured
  search.
* **Not compared in a table**: AlphaEvolve's TPU circuit (no artifact),
  Alpha-RTL's C910 leading-zero anticipator (sky130, a sub-block of an
  adder; a candidate for a later note through the LZA sub-slot of
  `fp.py`), and the spec-to-RTL frameworks on RTLLM and VerilogEval
  (COEVO, POET, REvolution, EvolVE, VeriOpt, LLM-VeriPPA), whose task is
  generation from a specification rather than optimization of a unit.

## 6. Ablations

Each ablation removes one practice from the full configuration of the
comparison targets. The switch column names the run-file key.

| Practice | Switch | Measure that shows the effect |
| --- | --- | --- |
| The library realizes a declared family by construction | `realization: {fixed: behavioral}`: the seed renders every structure as behavioral text and the menu drops `[library]` (the review then judges the text alone). Its control is `nofront_replicated` (int_subword_alu) or `nofront` (fp_alu_cmp): the baseline alone with the library on, and on the integer target the same replicated subword layout behavioral has to take, so the pair differs in the library alone | feasible fraction, `review.agree`, model calls to reach the tier-2 front |
| Knowledge cards in the prompt | `knowledge_depth: cards` / `index` / `path`; a fourth level with an empty knowledge directory and `chialu_families` removed from `prompts.sources` | distribution of declared families, hypervolume |
| The synthesis database as the timing model | `chialu_timing` removed from `prompts.sources`; `chialu.prune --threshold 0.10` applied or not | the least delay reached, model calls to the final hypervolume |
| The sharing schemes and the numeric front as seeds | `--schemes 0` (the unshared structure set alone), and `seeds.generated: [baseline]` with no front at all (what the run file carried before the numeric stage) | hypervolume, distinct plans on the front |
| Structured declarations and replan | `opfree`: `operator: [free]` and `search.replan: false`, so a `VAR` line the model still writes re-renders nothing; `noreplan`: the structured operators kept and `search.replan: false` alone (chialu.ALU only: the dot unit has no replan) | fraction of family-changing candidates that pass conformance |
| The review node | the review node, its feedback and its `review.dissent` constraint all removed, so the run spends no review calls and the model sees no verdicts | fraction of declared families the text does not realize, and whether the search exploits it |
| The gate-level screens | the `when` conditions of `synth_unit` (`yosys_stat.cells le 2.0 x seed`) and `synth_ppa` (`synth_unit.area_um2 le 1.2 x seed`) removed | synthesis minutes per feasible candidate |
| Prompt operators and tactics | one `operator` value at a time; `tactics.sources: []`; `member_focus: none` | improvement per model call |

The core of the study is a two-by-two: library on or off, and the model
on or off. Library on and model off is the `smac` or `random` backend
over the declared space; library off and model on is the generic code
evolution row of section 4; both off is tier 2's seed. A fourth point needs no
search at all: `python3 -m chialu.prune <run.yaml> --best delay --out
<run>.best.yaml` fixes every structure to the database's fastest family
at that structure's width, with the pins of the row that won, so tier 2
carries a no-model reference the searched runs are measured against.

The run files are `targets/<target>.abl_<key>.yaml`
(`make_targets.ABLATIONS`): `behavioral` and its control
`nofront_replicated`; `cards`, `index` and
`noknowledge`; `notiming`; `nofront` (with `chialu.pipeline --schemes 0`
for the sharing half); `opfree` and `noreplan`; `noreview`;
`noscreens`; `opstructural`, `oplocal` and `nofocus`. Four points follow
from the targets rather than the plan. The library off cannot render the
numeric front's plans (a lane-partitioned adder and a unit shared across
formats are library constructions), so `behavioral` starts from the
baseline with the replicated subword layout and is compared with
`nofront_replicated` on the integer target and `nofront` on the float
one, the baseline with the library on. The dot unit's ablations run on
`vec_dot_acc_cmp_fp16`, Table B's fp16 row set, so each pairs with that
row set's chiALU runs (the same run file, the same seeds); the dot unit
has no realization switch, no replan and no timing source, so
`behavioral`, `noreplan` and `notiming` do not apply to it. `tactics.sources` is already empty in the full
configuration, so that half of the last practice has no run. The prune
half of the timing practice needs a new criterion: `chialu.prune`
removes a family by its delay against the clock, and at a 300 ps clock
that removes every family.

Run counts: the first five practices on all three comparison targets
(the ALU, the dot unit, and `int_subword_alu` as the integer control),
three repetitions each; the last three on `fp_alu_cmp` alone, two
repetitions. Every run has the budget of section 4, and every curve is
plotted against model calls rather than iterations.

## 7. Metrics and statistics

* **Hypervolume** of the (area, delay) front in the fixed box of its
  table half, 1.2 times the baseline's area and delay (section 4), every
  design at its least-delay mapping.
* **Best area**, **least delay** and the best area-delay product.
* **Gate attrition**: the fraction of candidates that fail lint,
  conformance, fault and review, per run (the ALU targets carry no
  timing constraint).
* **Sample efficiency**: model calls to reach 95% of the run's final
  hypervolume.
* **Cost**: node runs, synthesis minutes, tokens.
* **Scale**: variables materialized, `VAR` lines per seed, load time and
  prompt size with and without lazy binding; measured as
  485 of 659,310 variables and 0 to 12 `VAR` lines per seed for
  mixed_cvt_alu, against about 1,000 lines before lazy binding.

Three repetitions per configuration, each with its own random seed
(`adir run --seed k`, `chialu.pipeline --search-seed k`, k = 1, 2, 3:
SkyDiscover's database and ADIR's composer draw from it; before this
every repetition drew from 42), in a run directory of its own
(`run/<name>.r<k>`); `make_table.py` takes a method label once per
repetition and prints each repetition's row and the mean and sample
standard deviation. Every difference between configurations is paired
by target and repetition (the plain loop has no seed of its own; its
repetitions differ by the model's sampling alone).

The budget, set from the measured call times:

* **Model** (decided 2026-09-23): opencode on openrouter's
  `deepseek/deepseek-v4.1-flash` at effort `high` for every method row,
  every ablation and both sides of the RTLScout pair, which every run
  file names (`targets/make_targets.py`). A call may output the model's
  whole limit, 943,718 tokens (`max_output_tokens` on the solution, guide
  and review calls). The cap comes out of the 1,048,576-token context:
  openrouter refuses input and `max_tokens` beyond it, and opencode
  compacts a session at the context less the cap, about 105k tokens (786k
  at 262,144, the one number to change if sessions compact early).
* **Resuming and extending**: every run checkpoints each iteration.
  `chialu.pipeline <file> --run-dir <dir> --resume --search-iterations N`
  (or `adir run <file> --resume --iterations N`) continues from the last
  checkpoint to N iterations in all, so the same command finishes a
  stopped run and a larger N extends a finished one; the composer's draws
  continue rather than replay. The plain loop takes `--resume --calls N`
  the same way: a call counts once its `evaluation.json` exists, and a
  call cut short is done again.
* **What a run keeps**: every candidate's program and record
  (`results_db.jsonl`, `programs/`), every prompt and reply
  (`prompts/`), every agent call's directory with the agent's transcript
  (`agent/<stamp>-<id>-<role>/transcript.md`; a review's calls under
  `agent/review-<stamp>-<hash>/`, one `transcript*.md` per call), and one
  line per model call in `llm_calls.jsonl`, the review's included: role,
  model, effort, output cap, wall time, success, session id, and the
  tokens (input, output, reasoning, cache) and cost the CLI reports; a
  call that stalls at its time limit has them read back from opencode's
  session store. The review's rows are also inside its record
  (`review.llm_calls`). `make_table.py` sums them per row (model calls,
  tokens, cost, agent hours). The
  plain loop keeps the same under `call_<k>/` (prompt, reply,
  transcript, usage, evaluation).
* **Synthesis reports**: every run file sets `synth_ppa`'s `report: true`
  and the environment `CHIALU_SYNTH_REPORT=1`, so every method gets the
  critical path, the worst paths and the area by hierarchy as feedback.
* **Verification strength**: `verify.n_random` is 20000 in every run
  file, the count the reference designs are judged at (fp_alu_cmp
  427,964 vectors, int_subword_alu 1,274,226, vec_dot_acc_cmp_fp16
  20,156). Measured on the baselines against 300: fp_alu_cmp's
  simulation goes from 4 to 12 s a candidate and int_subword_alu's from
  1 to 5 s; the dot unit's 44 s is the model's compile either way. The
  bundle is built once per run. A candidate's synthesis takes minutes and
  its model call longer, so the evaluation time barely moves.
* **Iterations per run** (decided 2026-09-23): 20 for every row, one
  candidate per iteration and one attempt per model call for every method
  (`search.attempts: 1`: SkyDiscover's default manager otherwise re-prompts
  up to three times within an iteration and adaevolve twice; `retries: 1`
  on every model role and the review, as the plain loop's single attempt): 20 search iterations of chiALU, of the
  generic backends and of every ablation, 20 calls of the plain loop.
  The model calls an iteration spends differ by method (chiALU's guide
  calls and reviews on top of the solution call) and are reported beside
  it rather than equalized. The budget stops (`budget.llm_calls` 2000,
  `wall_hours` 48) sit where only a hung run reaches them. One iteration
  costs at most two solution calls, two guide calls and two reviews; the
  review spends at most `chialu.review.MAX_CALLS` = 3 calls per candidate
  whatever the modules it declares. Before the bound the review spent eleven calls and
  1,054 s of a candidate's 1,073 s evaluation, which made the per-run
  cost a count of the candidate's modules rather than a constant.
* **Parallelism**: `parallel: 2` within a run; <host>'s worker admits
  100 concurrent opencode calls (`opencode_creds`), so up to 50 runs are
  in flight, and the synthesis of those runs spreads over <host>'s 124
  and <host>'s 84 `eda` slots.
* **Scale**: about 35 configurations across sections 4 to 6 (the method
  rows run on both ALU targets) at three repetitions is about 105 runs
  of 20 iterations each.

The risk this budget carries is the solution call that does not
complete: of the eight attempts of the two measured iterations, six ran
out the 1,200 s limit after 17 to 23 agent steps of 12 to 17 minutes and
a stalled step, and one call answered per iteration. A timed-out attempt
is a model invocation, so it counts against the budget under the
protocol above. The first full-budget run reports the completion rate
per configuration, and a rate near the measured one multiplies the wall
time by about four.

The protocol that makes the method rows comparable:

* one model for every method in a table, chosen at the time of the
  experiment;
* one budget in model calls, where a call is one model invocation
  whatever the system (an RTLScout agent step, a generation's calls of
  the generic backends, one turn of the plain loop), with node runs
  and synthesis minutes reported beside it;
* one evaluator and one set of gates for every method and for the
  reference designs;
* one seed program per target, given to every method unchanged;
* every curve plotted against model calls rather than iterations;
* every prompt and reply logged (ADIR's `prompts/`, the plain loop's
  transcript, RTLScout's own logs), so a run is auditable;
* the contract differences of a reference design stated on its row
  (section 0) rather than absorbed into a single number.

## 8. Order of work and prerequisites

0. Model the numerical behavior of every reference design (section 0)
   and freeze the option bindings of the comparison targets from it.
   Frozen for FPnew and HardFloat, whose contract is the binding of
   `fp_alu_cmp.yaml`: `minmax_nan: number`, `tininess: after`,
   `nan_payload: canonical`, `daz_in` and `ftz_out` false, the IEEE rule
   that a signalling NaN operand alone raises invalid, and
   `flag_scope: per_operation`, which is the option this modelling added
   for FPnew's one status per vectorial op. Frozen for TransDot too: its
   DP mode is register-free under the `COMBINATIONAL` patch of the risk
   entry below, the fp16 mode meets the fused contract out of a 76-bit
   window and the fp8e5m2 mode is windowed, and section 4 freezes Table B
   on that per-mode contract.
1. Profile the seeds' critical paths. The `vec_dot_acc_cmp` seed maps to
   10,612.0 ps and 26,433.5 um2 at nangate45, against the 17,077.1 ps and
   64,007.3 um2 it mapped to before the two changes below.

   The path is not the products and it is not the frame's carry
   propagation. Measured alone at nangate45, the 281-bit prefix adder
   (`fam_prefix_sklansky_w281`) maps to 1,718.6 ps and 2,212.6 um2, while
   the 281-bit leading-zero anticipator (`fam_dot_lza_w281`) maps to
   7,197.1 ps and 35,180.1 um2 over 27,809 cells, which is over half the
   dot module's own 57,060.5 um2. Two changes follow from that, both in
   `_acc_tail` of `chialu/spaces/fma_dot_spaces.py`:

   * the `lza` slot of the accumulator families takes `lzc_after_add` as
     its default rather than the anticipator, since an anticipator that
     runs beside a 1.7 ns adder and costs 7.2 ns buys nothing at this
     width; the search reaches the anticipator by naming it;
   * the accumulator families gain a `round` component, so the one
     rounding of the dot contract is the library's rounder rather than
     the engine's behavioral `pack_d`.

   Isolated, the rounder alone gives 15,567.1 ps and 66,186.4 um2 over
   53,312 cells, so the count after the add carries the delay and most of
   the area. The seed also synthesizes in 66 s rather than 318 s.

   What separates the seed from TransDot is not a component choice. The
   one-mode fp16 targets `vec_dot_acc_cmp_fp16.yaml` and
   `vec_dot_acc_cmp_fp16_td.yaml` measure it: chiALU's slot defaults give
   9,952.9 ps and 16,880.9 um2, chiALU bound to TransDot's own slot
   choices gives 11,062.2 and 21,609.8, and TransDot gives 6,621.1 and
   6,045.9. Binding TransDot's components without its window makes the
   unit worse, because the difference is the frame: chiALU keeps the
   exact 281 bits whenever the contract is correctly rounded, while
   TransDot is correctly rounded out of 76. `core.window_bits` closes
   that gap: `vec_dot_acc_cmp_fp16_tdw.yaml` binds TransDot's choices
   with a 76-bit window and gives 10,719.5 ps and 11,393.3 um2, exact on
   3,156 vectors where TransDot has 2 mismatches.
   `docs/coverage-gap-plan.md` records the gap, the fix and where the
   remaining area sits.

   The cut profile of the seed as it stands localizes what is left. The
   unpacked operands stand at 232 ps and the special-case code at 317 ps.
   The library dot module's own output is 7,312 ps, the library rounder's
   word is 8,928 ps, and the unit's `d` is 10,400 ps, so the module
   carries 70% of the path and the rounding and the mode's output mux
   carry the rest. Inside the module the 281-bit prefix adder is
   1,718.6 ps of the 7,312, so the alignment shifters, the reduction tree
   and the normalization hold the remaining 5.6 ns; those are the slots a
   declared family reaches next.

   The database's dot rows (27,000 to 56,000 um2, 45 to
   114 ns) predate item 4 and are rebuilt with the dense build. The
   `fp_alu` seed's 6.8 ns was profiled by cut synthesis
   (`chialu/profile.py`, `docs/work-plan.md` item 4): the behavioral
   significand add adds 4.0 ns and the behavioral rounder 3.6 ns, while
   the mode decode, the operand select and the flag logic together stay
   under 0.3 ns, so realizing the declared float families is the whole
   of the gap to the library's 2.6 ns fp16 adder.
2. Write `targets/eval/fp_alu_cmp.yaml` and `vec_dot_acc_cmp.yaml`
   through `targets/make_targets.py`, and check that `fp8e5m2` and
   `minmax_nan: number` render and conform. Write the generic-evolution
   copies of each (`*.free_<backend>.yaml`: one per backend, the sources
   emptied, the free operator, the baseline seed alone) and the
   plain-loop script, which take the same evaluator. Done: both run files
   render, lint and conform, and `int_subword_alu`, `fp_alu_cmp` and
   `vec_dot_acc_cmp` each carry the three backend copies
   (`FREE_TARGETS` in `targets/make_targets.py`), which is the set of
   three comparison targets section 6 runs the first five ablations on.
   The plain-loop script is `harness/plain_loop.py` of chialu-a3eval
   (commit `ebb9b70`): it loads the run file as the flow does, strips
   ADIR's markers and declaration block from the baseline seed, judges
   every candidate with `chialu.eda.lint`, `conformance`, `yosys_stat`
   and `synth_ppa` under the run file's gating, invokes the agent through
   the flow's `AgentLLM` construction with one attempt per call, and
   writes records in the archive's shape; its smoke test on `fp_alu_cmp`
   answered two of two calls (1,200.6 s and 658.1 s; 7,175.1 um2 /
   5,368.8 ps and 7,031.4 / 5,422.5, both feasible, against the seed's
   6,991.0 / 5,225.6), and one call from the FPnew seed stalled at
   1,207 s. Its parity gaps against chiALU's row are in
   `harness/README.md` (edits allowed inside the call directory, one
   attempt per call, no `synth_unit` and no review gate, sub-session
   tokens not counted).
3. Run the method rows of Table A on `fp_alu_cmp` and `fp_alu_cmp_hf` at
   a small budget (chiALU, the generic backends, the plain loop) and the
   no-model rows, every design at its least-delay mapping; this is the
   first version of the table.
4. Build the FPnew wrapper (one design point) and run it through the
   conformance gate with its failing classes recorded: the first
   reference row, and the starting design of section 4's second
   experiment. The other reference designs follow. Done for FPnew's
   ADDMUL MERGED point and for HardFloat. FPnew agrees with the
   comparison target's reference on every result value and on every flag
   but 24 of 427,964 vectors, which are `fmul` of a subnormal by a number
   near one where FPnew's `uf_after_round` raises underflow under neither
   IEEE tininess rule. HardFloat agrees bit for bit on every op it
   implements; its `AddRecFN` and `MulAddRecFN` do not elaborate for
   (5, 3), so the fp8 lanes of `fadd` and `fsub` return zero and that gap
   is stated on its row rather than counted as a mismatch.
5. The two switches (`realization: behavioral`; `search.replan: false`)
   and the TestFloat harness exist (chialu-a3eval, `harness/`).
6. Run the full budget: three repetitions of the method rows, the
   ablations, the RTLScout pair, the second experiment; Table B's method
   rows on the two frozen row sets of section 4, whose reference rows
   are measured.

Risks and how each is handled:

* CVFPU and TransDot are read by yosys-slang (`read_slang`), as every
  other design in the flow is; the yosys frontend left the flow on 2026-09-17. slang is
  stricter than the yosys frontend about a select whose range lies outside its operand,
  which TransDot's multi-format code carries in branches a generate
  condition never takes: `read_slang -Wno-range-oob -Wno-index-oob`
  elaborates and flattens it where the yosys frontend plus yosys could not. A
  suppression is recorded in the wrapper directory, never in the
  reference design, and the netlist it produces passes the conformance
  gate before its numbers enter a table.
* TransDot's DP path carries a pipeline register the parameter does not
  remove, which the wrapper of `baselines/transdot/transdot_dot_core.sv`
  measured: `transdot_fp4_fp8_fp16_fp32_fma` at `NumPipeRegs` 0 holds an
  unconditional `always_ff @(posedge clk_i)` stage between the exponent
  datapath and the adder (`exponent_product_qq`,
  `exponent_difference_qq`, `tentative_exponent_qq`, `addend_shamt_qq`,
  `tentative_sign_qq`, `effective_subtraction_qq`,
  `result_is_special_qq` and their SIMD and fp8 copies), and the
  `COMBINATIONAL` define bypasses the registers of
  `transdot_decomp_multiplier` and `transdot_decomp_addend_datapath`
  alone. Driven with a tied clock the unit answers zero; with
  `COMBINATIONAL` it answers the value of the stage before the register.
  `baselines/transdot/tdot_comb.py` closes that: the three blocks now
  stand under `` `ifdef COMBINATIONAL ``, which is the define the
  repository already uses for the multiplier's and the addend datapath's
  registers, so `NumPipeRegs` 0 is a register-free configuration and the
  DP point enters Table B beside the combinational units. The patch is
  recorded in the wrapper directory and the file without the define
  behaves as before. Driven combinationally the unit answers exactly what
  it answers at one cycle of latency, which is how the patch was checked.

  The contract that run pins, over 6,309 vectors of
  `vec_dot_acc_cmp`, differs by mode. The two-term fp16 mode meets the
  fused contract: 2 of about 3,150 vectors differ in a value, so one
  rounding of the exact dot product is what it computes. The four-term
  fp8e5m2 mode does not: 1,113 of about 3,150 differ, so its accumulation
  is windowed and its row needs the `window` contract of section 0 step 3
  with an accuracy column. Both modes drop a special value in a lane
  above the first: 570 vectors where the reference delivers a NaN and 112
  where it delivers an infinity get a number instead, always with the
  special in an upper lane.

  The one-mode wrappers of Table B (`transdot_dot_core_fp16.sv`,
  `transdot_dot_core_fp8.sv`) and the fork's sources give the mechanism.
  The DP reduction happens inside `transdot_decomp_multiplier`: each
  lane's exact product is aligned to the largest product exponent by a
  plain right shift in a lane word with no sticky bit (a 36-bit word with
  12 guard bits below the 22-bit fp16 product; a 24-bit word with 14
  guard bits below the 6-bit E5M2 product), the aligned lanes are summed
  exactly in 50 bits, and the sum enters the 76-bit (`3p + 4`) FMA window,
  where the fp32 addend is aligned with a 24-bit sticky. In the fp16 mode
  a product truncated below its lane word sits at least 34 bits below the
  sum's leading bit, so the lost sticky can only turn a value just below a
  rounding midpoint into a tie: the two vectors that differ hold a
  negative product shifted out of the word entirely (a difference of 37
  binades or more), which the rounder sees as an exact tie and rounds to
  even, one ulp above the correctly rounded result. In the fp8 mode the
  lost bits land inside the fp32 significand: lanes 2 and 3 clamp their
  shift at 16 where the lane word needs 22 to flush, so a product more
  than 16 binades below the anchor enters 2^(d - 16) times too large;
  lanes 0 and 1 carry a 6-bit shift amount into a 5-bit shifter, so a
  difference of 32 to 37 binades aliases to 0 to 5; and no lane has a
  sticky. The errors are gross rather than rounding-level (over 3,153
  vectors of the one-mode target the maximum is 8.4 x 10^7 ulp and the
  mean 3.8 x 10^5), so the fp8 row carries the `window` contract with the
  accuracy column rather than a mismatch count. The special-value drop
  has one origin in both modes: only lane 0's operands and the addend
  reach the special-case detection (`result_d_fp = simd_enable ? ... :
  result_d_normal`), and an upper lane's NaN or infinity enters the
  datapath as a finite significand under an all-ones exponent, which can
  also capture the anchor exponent and shift the other lanes out. Section
  4 states that difference on TransDot's rows.
* fp8 in the reference designs is E5M2 only, so the fp8 lanes of Table A carry
  no E4M3 row; E4M3 stays inside the ablations.
* RTLScout's license (BSD-3-Clause-Clear) permits the runs; its results
  depend on Claude Opus 4.6, so both systems run under one model chosen
  at the time of the experiment.
* The search budget dominates cost, and section 7 fixes it: about
  21,000 model calls before the RTLScout pair, whose wall time the
  completion rate of the solution call multiplies.

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
| transdot_transdot_merged_alu_core | 4,503.114 / 4,013.49 | 4,609.248 / 3,923.53 |
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

## 2026-09-24 reference hand seeds on DeepSeek

The three `fp_alu_cmp_{fpnew,hardfloat,transdot}.hand_adaevolve.yaml`
files use the same free-rewrite experiment: ADIR declarations and domain
sources off, no replan/review, one complete reference source file, history
with seven entries, and 20 iterations. Solution and guide both use
opencode's `deepseek/deepseek-flash`, high effort, at most 393,216 output
tokens. Existing `fp_alu_cmp.hand_*` files remain byte-identical.

FPnew uses PARALLEL, which passes the ordinary after-rounding contract.
MERGED's 24 failures are a real narrow-lane underflow implementation bug,
not a value difference or an alternative global tininess setting.
TransDot MERGED preserves that observable behavior under the explicit
`underflow_contract: fpnew_merged_16` option (specified in
`formats-and-options.md`). Its arithmetic source is unchanged. This row
must be labelled with that contract, rather than compared as an IEEE-after
implementation. Both its seed and a generated chiALU implementation are
checked against the independent model.

The older `fp_alu_cmp_hardfloat.yaml` architecture variant accidentally
still admitted fp8 add/sub. The generator now refreshes its mode binding
from `fp_alu_cmp_hf`, removing the absent fp8 adder's 13 pins and preserving
the other architecture pins. HardFloat's hand
run serves precisely that restricted function (380,140 gate vectors).
The new hand graphs also require successful synthesis; an evaluator
exception cannot leave a feasible seed with null area/delay.

`targets/build_hand_seeds.py` rebuilds the concatenated source packages
under the external a3eval `runs/` tree, with an empty ADIR-DECL header.
FPnew and TransDot use their builders' current wrappers, and TransDot's
duplicated status words are normalized to the target's four-bit
operation-wide interface. The obsolete wrapper lint failure is not a
reference arithmetic change. TransDot's 408 KB source requires a larger
candidate limit; its new hand target permits 600 KB.

See `REPORT.md` and `measurements/handseeds/` for measurements, hashes,
classification and offline prompt checks, plus the nine launch commands.
No search or model call is part of setup validation.

## 2026-09-25: TransDot upstream fixes, references re-verified

TransDot (a3eval `3rdparty/transdot`, branch `pncel-develop-plus-comb` = upstream
pncel/develop `cd3d062` "Fix UF tininess index, FP8 DP alignment, DP NaN/Inf lanes, SIMD
pipeline staging" + our combinational 16-bit point) replaces `7abd4c49`. Every
TransDot-derived text was rebuilt and re-measured at the current metric (median of 3
mappings: base, 11, 23; Nangate45, medium, 300 ps). Receipts: `measurements/transdot_fix/`.

* **Contract.** TransDot MERGED is now bit-exact under the standard `fp_alu_cmp` contract
  (427,964 vectors, 0 mismatches including flags; the 542,788 exhaustive fp8/boundary
  vectors of `reference_underflow_check --contract ieee` also match). The former
  `underflow_contract: fpnew_merged_16` workaround (24 flag-only mismatches, bf16/fp8e5m2
  RNE fmul underflow) is retired for TransDot: `fp_alu_cmp_transdot` is `fp_alu_cmp`'s
  contract (the fixed seed fails the old contract on exactly those 24 vectors). The option
  stays for FPnew MERGED, whose `fpnew_fma_multi.sv` still has the defect.
* **PPA** (area µm² / delay ps). Merged `alu_core`: 4,503.1 / 3,966.7 (was 4,609.2 /
  3,923.5 median-of-5; 4,503.1 / 3,923.5 over the same three seeds). Hand seed
  (`adir seeds`, feasible): 4,475.5 / 4,135.5 (was 4,543.0 / 3,816.8 median-of-5;
  4,520.1 / 3,872.0 over the same three seeds).
* **Table B (300 ps).** DP fp16: 160 → 2 mismatches (the 158 dropped-lane NaN/Inf cases
  are gone; 2 one-ulp `value` remain), 6,417.5 / 5,024.8. DP fp8: 1,621 → 591 (all `value`,
  the window contract; no `nan_expected`/`inf_expected`), 5,030.1 / 5,243.9. No-DP fp16/fp8:
  conformance unchanged (96 / 87, the sequential contract), 8,391.0 / 7,514.9 and
  13,697.1 / 14,637.2. `baselines/transdot/tdot_comb.py` still applies (the qq stage has no
  generate guard upstream either) and now accepts the enabled update line.
