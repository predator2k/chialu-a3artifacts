# Slot audit of the family library

This audit is superseded. `python3 -m chialu.targets.rtl.families.coverage`
answers the same questions mechanically and runs as a check, and every
finding recorded here was fixed under item 3 of `docs/work-plan.md`; the
document stays as the record of what the audit found and how each class
was resolved. A finding of the tool is the current statement.

This audit records, for every family generator, how each internal
component of a library kind is realized, and which slots the family
spaces declare that no generator reads. It was taken on 2026-09-12,
before the deferral of the 21 families (`docs/deferred-families.md`);
the `SEQUENTIAL_*` tables it names in section 3 were removed the same
day where their families were deferred. Part 2 (slot domains against
the realized families, and reachability) follows in a later section.

Legend for the realization class:

* **A**: a library module instance whose family comes from a slot pin
  (`<slot>.family`) the space declares;
* **B**: a library module instance with a hard-coded family (no pin read,
  or a pin the space never declares);
* **C-reason**: behavioral text (`<<`, `*`, `+`, a `for` loop, a
  `function`) with a documented reason in the code;
* **C-no-slot**: behavioral text with no slot and no reason.

Pin keys reach a generator as the full dotted path relative to the
structure (`chialu/modules/generators.py:140-182`, `walk()` at lines
171-181: `pins[child.name[len(base)+1:]] = v`), so a slot nested one
level deeper in the space arrives as `parent.child.family`, and a
generator that reads only `child.family` never sees it.

## 1. The table

### fp.py (spaces: `fp_spaces.py`, `misc_spaces.py`)

| family / group | component (what it does, width class) | class | slot pin read | evidence |
|---|---|---|---|---|
| `unpack_sv` (per_unit_unpack, shared_per_lane, shared_across_formats) | subnormal LZC, SW bits (11-24) | **B** | `lzc.family` read but `unpacker_space` declares no components | fp.py:237; misc_spaces.py:74-97 |
| same | subnormal normalizing left shift, SW bits | **B** | `shifter.family`, undeclared by the space | fp.py:239 |
| `add_sv` all four families | significand adder, IW = XW+1 (27-53) | **A** | `sig_adder.family` + `sig_adder.*` | fp.py:272-273, 395; fp_spaces.py:233 |
| same, `ones_complement_end_around` | compound adder, IW | **B** (family hard-coded `compound_flagged_prefix`, topology from `sig_adder.topology`) | partial | fp.py:388 |
| same | align right shifter, IW | **A** | `align.shifter.family` / `far_align.shifter.family` | fp.py:268, 361; fp_spaces.py:99,108 |
| same | align sticky mask `~({IW{1'b1}} << amt)`, IW bits | **C-no-slot** | none | fp.py:371 |
| same, `sticky_method=trailing_zero_compare` | trailing-zero counter, IW | **B** (hard-coded `trailing_zero`) | none | fp.py:367 |
| same | LZA indicator string, IW (generate block) | **C-no-slot** (the anticipator itself has no library kind; its encoder does) | none | fp.py:416-426 |
| same | LZ counter on result / indicator, XW | **A** for `two_path` / `delay_optimized_unified`; **B** for `single_path` / `low_power_gated` | `near_lz.counter.family`; `norm.lz.*` never read | fp.py:274-277, 429, 433 |
| same | normalize left shifter, XW | **A** | `norm.shifter.family` / `close_norm.shifter.family` | fp.py:280, 441-444 |
| same, `norm_fam=coarse_fine` | `(src_lz / cg) * cg` and `src_lz % cg`, clog2(XW) bits | **C-no-slot** (a divide and modulo by a non-power-of-two `coarse_granularity`) | none | fp.py:439-440 |
| same | exponent difference `$signed(ea)-$signed(eb)`, EW+1 (9-19) | **C-no-slot** | none (`exponent_space` declares no components) | fp.py:322-326; fp_spaces.py:185-204 |
| `mul_sv` both families | significand multiplier, SW x SW | **A** | `sig_mul.family` + `sig_mul.*` | fp.py:512-513, 528; fp_spaces.py:426,437 |
| `round_fused_in_reduction` | product LZC, PW = 2 SW (22-48) | **B** (hard-coded `lzd_cell_tree`) | none | fp.py:544 |
| same | injection shifts `1 << (drop-1)`, `(1<<drop)-1`, `p >> dropnc`, PW+1 | **C-no-slot** | none | fp.py:552-553, 559, 570-573 |
| same | injection adder `{1'b0,p} + inj`, PW+1 | **C-no-slot** | none | fp.py:555 |
| same | correction `pr0 - lsb1`, `keepn + upn`, PW+1 | **C-no-slot** | none | fp.py:560, 576 |
| `fma_sv` (classic_fma, reduced_latency_fma, multipath_fma: the fp_fma slot's fused families) | the fused datapath `dot._fma_sv` at one element: significand multiplier SW x SW, the addend alignment over the 2S + Sc + 3 + G window, the window adder, the leading-zero unit, the normalize shifter | **A** | `multiplier.family` + `multiplier.*`, `align.*`, `lza.*`, `cpa.*`, `norm_shifter.*` | fp.py `fma_sv`; dot.py `_fma_sv`; fp_spaces.py `_fma_tail` |
| `fma_sv` (bridge_fma, `bridge_reuse`) | `mul_sv` (sig_mul_then_round, the `multiplier` slot as its `sig_mul`) and the single-path `add_sv` at twice the significand width (`align`, `lza`, `cpa`, `norm_shifter` as its `align`, `lz`, `sig_adder`, `norm.shifter`), composed by `dot._bridge_sv` | **A** | the same pins | fp.py `fma_sv`; dot.py `_bridge_sv` |
| same | the operand roles under the op code `fop` (fadd as `1 * xa + xb`, fmul as `xa * xb + 0`, the fused ops fmadd, fmsub, fnmsub, fnmadd as `xa * xb + xc` with the negations folded into the signs of xa and xc) and the specials in the engine's order | **C-no-slot** (muxes on X) | none | fp.py `fma_sv`, `FMA_OP_CODES` |
| same | the exponent path (the alignment distance, the result exponent) | **C-no-slot** | none: the family declares no exponent slot (the classic_fma card says the exponent path is behavioral) | dot.py `_fma_sv` |
| `cmp_sv` `integer_compare_on_bits` | integer comparator, EW+XW+1 (69-71) | **A** by the pin, but `fp_cmp_space` declares no components, so effectively **B** | `comparator.family` | fp.py:622; fp_spaces.py:346-361 |
| `cmp_sv` `dedicated_magnitude_comparator` | significand comparator, XW+1 | **B** (hard-coded `prefix_comparator`) | `structure` only | fp.py:631 |
| `round_sv` (dedicated_per_op / shared_per_lane / shared_across_formats) | normalizer LZC, XW | **B** | `counter.family`, undeclared (`rounder_space` has no components) | fp.py:668, 694; misc_spaces.py:42-71 |
| same | normalize + right shift, XW and XW+1 | **B** | `shifter.family`, undeclared | fp.py:669, 697, 710 |
| same, `increment_adder` | incrementer, XW+1 | **B** | `incrementer.family`, undeclared | fp.py:758 |
| same, `compound_adder_select` / `flagged_prefix` | compound adder, XW+1 | **B** (family hard-coded `compound_flagged_prefix`; only `compound_adder.topology` read) | partial; the `rounding_space.compound_adder` slot (fp_spaces.py:165) is a full `cpa_space`, ignored | fp.py:737-740 |
| same | `restmask = ~({XW+1{1'b1}} << sha)`, `halfv = 1 << (sha-1)`, XW+1 | **C-no-slot** | none | fp.py:711, 713 |
| same | `fint = rest >> (sht-sb)` / `rest << (sb-sht)`, XW+sb+1 | **C-no-slot** | none | fp.py:718 |
| same, `injection` | `sum_i = sigw_i + inj` (XW+2) and `magi = sum_i >> sha` | **C-no-slot** | none | fp.py:750-751 |
| same | `keepn + upn` (carry_n test), `mags = keep + upr`, `code` add/sub, CW = W+EW+1 | **C-no-slot** | none | fp.py:731, 754, 765 |
| `div_sv` `sig_div_then_round` | significand divider, XW to XW+1 | **A** | `sig_div.family` + `sig_div.*` | fp.py:826-831; fp_spaces.py:449 |
| same | operand-normalize LZC + shifter, XW | **B** | `norm.lzc.family`, `norm.shifter.family`, undeclared by `fp_div_space` | fp.py:804-808 |
| `sqrt_sv` `sig_sqrt_then_round` | square root, Q = XW+1 | **A** | `sig_sqrt.family` + `sig_sqrt.*` | fp.py:874-883; fp_spaces.py:458 |
| same | `rad = mm << 2K` (constant), `root >> 1/2` | C (constant shifts) | none | fp.py:893, 904 |
| library fallbacks used by every helper | lzc: a `for` loop; shift: `<<` / `>>`; adder: `+`; mul: `*`; cmp: `<`; incr: `+` | **C-no-slot** (hit when the named family has no module) | none | fp.py:173, 187, 397, 529, 624, 743, 762 |

### div.py (space: `div_spaces.py`)

| family | component | class | slot pin | evidence |
|---|---|---|---|---|
| all families | divisor-normalize LZC, D bits (24-53) | **B** | `norm.lzc.family`, undeclared (no div family declares `norm`) | div.py:175-177 |
| all families | divisor-normalize left shift `b << lzs`, D bits | **C-no-slot** | none | div.py:179 |
| all families | dividend scaling `{D'b0, ax} << lzs`, NW = N+S+D bits (up to about 160) | **C-no-slot** | none | div.py:290, 405, 489, 783 |
| all families | remainder de-scale `rf[D-1:0] >> lzs`, D bits | **C-no-slot** | none | div.py:327, 463, 534 |
| `restoring_nonrestoring` | per-stage trial subtractor, RW = D+1, Q stages | **A** | `residual_adder.family` + `residual_adder.*` | div.py:213, 232, 247; div_spaces.py:203 |
| `restoring_nonrestoring` (nonrestoring) | final restore `r_Q + bx`, RW bits | **C-no-slot** (the `residual_adder` slot exists but is not used here) | none | div.py:238 |
| `srt_radix2` | digit selection (comparisons on a YI-bit estimate) | **C-no-slot**: the declared `digit_select: qds_space()` slot is never read by `_srt2_sv` | none | div.py:307-308; div_spaces.py:221 |
| `srt_radix2`, `residual_form=twos_complement_cpa` | per-stage assimilating CPA `wsh + wch`, RW bits, Q stages | **C-no-slot** | none | div.py:302, 311 |
| `srt_radix2` | final assimilation `ws_Q + wc_Q`, correction `wf +- dnx`, `qq_Q + 1`, `qp_v - qm_v`, RW / Q bits | **C-no-slot** | none | div.py:317, 322, 324-325 |
| `srt_high_radix` | QDS table / thresholds | **A** | `digit_select.family`, `digit_select.divisor_truncation_bits`, `.residual_truncation_bits` | div.py:381-384; div_spaces.py:241 |
| `srt_high_radix`, `comparator_digit_selection` | the four threshold comparators per stage | **C-no-slot**: the qds family's `comparator_adder: cpa_space()` slot (div_spaces.py:72) is never read | none | div.py:435 |
| `srt_high_radix` | `idx = (dt - ND) * NY + yi`, final `wf = ws + wc`, `rf = wf + dnx` | **C-no-slot** | none | div.py:441, 458, 461 |
| `online_msdf` | per-stage `v_j = (w_j <<< 1) + xterm - qd_j` and `w +- dk`, RW = LF+3 bits, Q stages | **C-no-slot** | none (the family declares no components) | div.py:514, 517 |
| `newton_raphson`, `goldschmidt`, `direct_polynomial`, `prescaled_very_high_radix`, `svoboda_tung` | iteration / prescale / back-multiply multipliers, XWd = F+2 (60-110 bits) | **A** when `iter_mult.family` / `final_mul.family` / `prescaler.family` is declared; **C-reason** otherwise | `iter_mult.family`, `final_mul.family`, `prescaler.family`, `mul.*` | div.py:765-767, 822-856, 880, 890, 1011-1043; `umul` at div.py:124-136 |
| same | the `umul` fallback reason | C-reason (section 3) | none | div.py:128 |
| `newton_raphson` / `goldschmidt` / `direct_polynomial` / `prescaled` | seed table | **A** | `seed.family` / `approximator.family`, `seed.input_bits`, `seed.tables`, `seed.degree` | div.py:760-763, 785-787; div_spaces.py:255,279,296 |
| `direct_polynomial` | its `approximator` slot is an `sfu_approx_space`, but div.py reads `approximator.family` as a seed-table name and falls back to `poly_seed` when it is not in `SEED_FAMILIES` | slot / kind mismatch | none | div.py:760-762; div_spaces.py:314 |
| `svoboda_tung` | reads `seed.family` although the space declares no `seed` slot | undeclared slot | none | div.py:760; div_spaces.py:266 |
| functional families | `f_k = 2 - dxf`, `e_k`, `g_k`, `x_{k+1}` adders, XWd bits per step | **C-no-slot** | none | div.py:824-847 |
| functional families | quotient shift `px >> (F+D-S-lzs)`, PW = N+XWd bits (110-160) | **C-no-slot** | none | div.py:884, 887 |
| functional families | back-multiply correction `rr = ax - qb`, `rr +- bs`, `q1 +- 1/2`, RC bits | **C-no-slot** | none | div.py:892, 900-904 |
| `prescaled_very_high_radix` / `svoboda_tung` | `w_j >>> pos`, `dig_j * dsx`, `w_j - qd_j`, `qacc <<< kb`, WR bits per step | **C-no-slot** | none | div.py:867-874 |
| `sqrt_sv` non-functional (`digit_recurrence_sqrt_combined`, restoring) | per-root-bit comparator `in >= trial` and subtractor `in - trial`, RW = Q+2, Q stages | **C-no-slot**: the declared `digit_select: qds_space()` slot is ignored | none | div.py:941-942; div_spaces.py:335 |
| `sqrt_sv` non-functional | radicand LZC, 2Q bits | **B** (hard-coded `lzd_cell_tree`) | none | div.py:968 |
| `sqrt_sv` non-functional | `xn = x << {sh,1'b0}`, 2Q bits | **C-no-slot** | none | div.py:972 |
| `sqrt_sv` functional | root correction `xs - e2s`, `est +- 1/2`, `d0 +- (ests<<<1)`, EW2 = 2Q+4 | **C-no-slot** | none | div.py:1029-1044 |

### dot.py (space: `fma_dot_spaces.py`)

Frame widths (`chialu/targets/rtl/dot_seed.py:67-83`): fp16 x fp32 into
fp32 with n = 4 gives AW = 281; fp32 x fp32 into fp32 with n = 4 gives
AW = 561; bf16 x fp32 into fp32 with n = 8 gives AW = 530; fp8e4m3 x
fp16 into fp16 with n = 4 gives AW = 55.

| family / group | component | class | slot pin | evidence |
|---|---|---|---|---|
| `pairwise_tree` | significand multiplier, S x S | **A** (default `behavioral_star`, the operator) | `mul.family` + `mul.*` | dot.py:1563, 608-609, 192-207; fma_dot_spaces.py:33 |
| `pairwise_tree` | reduction tree + root CPA, AW bits | **A** | `accum.family`, `accum.compressor`, `accum.final_cpa.*` / `accum.cpa.*` | dot.py:1568, 247-258, 294-342; fma_dot_spaces.py:34 |
| `pairwise_tree` | alignment `<<` into the frame, AW = 281-561 bits per term | **C-no-slot** (`cfg["shifter"] = None`: the family declares no `align` slot) | `align.shifter.family` read but never declared | dot.py:1564, 359, 673, 103-118 |
| `pairwise_tree` | `lzc_<AW>` behavioral function, AW = 281-561 bits | **C-no-slot** (`cfg["lz"]` counter = `None`) | `lza.counter.family` read but never declared | dot.py:1565-1566, 404, 121-134 |
| `pairwise_tree` | normalize `<<` after the count, AW bits: `_sh(m, None, ...)` unconditionally | **C-no-slot** | none (family forced to `None`) | dot.py:399, 407, 457, 465 |
| `pairwise_tree` | term right shift `ext >> ar` inside `_place` | **C-no-slot** (always the operator, even with a shifter declared) | none | dot.py:363 |
| `fused_csa` | partial-product matrix + compressor tree | C (structural netlist, by design) | `compressor` | dot.py:1577, 634-654, 1037-1078 |
| `fused_csa` | root CPA, AW / Wi bits | **A** | `final_cpa.family` | dot.py:1578; fma_dot_spaces.py:40 |
| `fused_csa` | alignment of the carry-save rows into the frame, AW bits | **C-no-slot** | none | dot.py:648-652 |
| `integer_mac` | product multiplier, W x W or sub-multipliers | **A** | `mul.family` | dot.py:1563, 1088, 990; fma_dot_spaces.py:60 |
| `integer_mac` | reduction tree + CPA, Wi bits | **A** | `reduction.family`, `reduction.final_cpa.*` | dot.py:1586, 1102-1106; fma_dot_spaces.py:61 |
| `integer_mac` (`composable_submultiplier`) | partial-product sums `" + ".join(rows)`, 2W bits | **C-no-slot** | none | dot.py:995-997 |
| `integer_mac` and every integer mode | result LZC over AW, hard-coded to the behavioral function (`lzc_fam = None`) | **C-no-slot** | none: `_acc_int_sv` passes `None` literally | dot.py:1029 |
| `multi_precision_simd_fma` | twin-precision gated matrix | **B** (hard-coded `subword.twin_precision_sv`) | `multiplier.*` forwarded as its pins | dot.py:1611, 593-604 |
| `multi_precision_simd_fma` | reduction CPA | **A** | `cpa.family` | dot.py:1610; fma_dot_spaces.py:152 (`_fp_tail`) |
| `fused_two_term_dot`, `multi_term_fused_dot`, `bf16_fma_datapath`, `fp8_training_datapath`, `kulisch`, `streaming`, `tensor_core`, block families | reduction / chain adders, Wn or AW bits | **A** where `cpa.family` / `reduction.family` is declared; **B** (`ripple_carry`) otherwise, the `_cpa_of` default | `cpa.family`, `reduction.family`, `final_cpa`, `accum` | dot.py:220-227 (`return "ripple_carry", {}`), 1610, 1623, 1634, 1657, 1671, 1686, 1695, 1713, 1727 |
| `bf16_fma_datapath`, `fp8_training_datapath` | their space declares only `mul`: no `cpa` slot exists, so the reduction adder is always **B** = ripple_carry over Wn | none | fma_dot_spaces.py:313, 333; dot.py:1713, 1727 |
| `multi_term_fused_dot` (per_level) | per-node alignment `$signed(v) >>> a`, sticky mask `~({Wn{1'b1}} << a)`, Wn bits per node | **C-no-slot** | none | dot.py:700-703 |
| `multi_term_fused_dot` (max / pairwise_diff / sorted) | window right shift, Wn bits | **A** if `align.shifter.family` is declared and Wn <= 128; **C-reason** above 128 | `align.shifter.family` | dot.py:779, 111-118 |
| `multi_term_fused_dot` (two_stage) | coarse + fine alignment, AW bits | as above; AW > 128 gives **C-reason** | `align.shifter.family` | dot.py:667-668 |
| `multi_term_fused_dot`, dual sign | `pmn`, `nmp` (Wn+1 subtractors), `~magr + 1` | **C-no-slot** | none | dot.py:824-828 |
| `kulisch_long_accumulator` | segment carry chain `kr_j = s + cin`, per segment of B = 16/32 over Wk = 512-4288 bits | **C-no-slot** | none | dot.py:880-885 |
| `kulisch_long_accumulator` | deferred-carry wide add, Wk bits | **A** | `cpa.family` | dot.py:874; fma_dot_spaces.py:222 |
| `kulisch_long_accumulator` | LZC + normalize over Wk (512-4288 bits): no `lza` slot declared | **C-no-slot** | none | dot.py:1565-1566, 404-407 |
| `tensor_core_mixed_precision_mac`, `fp8_training_datapath` (chunks) | the partial-sum rounder | **B**: `_round_trip` hard-codes `fp.round_sv(c, g, "dedicated_per_op", {}, tokens)` and `fp.unpack_sv(c, g, "per_unit_unpack", {})` with empty pins | none | dot.py:494-495 |
| `tensor_core` (`pairwise_sequential`) | re-entry shift `ux << dsh` / `ux >> dn`, Wn bits | **C-no-slot** | none | dot.py:938 |
| every family | `_frame_of_window` `sx <<< dl` / `sx >>> dlp`, W2 = max(Wn, AW) bits | **C-no-slot** | none | dot.py:482 |
| `classic_fma`, `reduced_latency_fma`, `multipath_fma` | significand multiplier, S x S | **A** (default `behavioral_star`) | `multiplier.family` | dot.py:1121-1122, 1173; fma_dot_spaces.py:80 |
| same | window adder, IW = Wn+1 (60-140) | **A** | `cpa.family` (via `_cpa_of`) | dot.py:1124, 1226-1244; fma_dot_spaces.py:24 |
| same | addend-normalize LZC (Sc bits) and shift | **A** | `lza.counter.family`, `align.shifter.family` | dot.py:1125-1126, 1182-1184 |
| same | alignment shifter, Wn bits | **A** if Wn <= 128, else **C-reason** | `align.shifter.family` | dot.py:1204, 111-118 |
| same | alignment sticky mask `~({Wn{1'b1}} << amt)` | **C-no-slot** | none | dot.py:1205 |
| same, `end_around_carry` | carry-back incrementer, IW | **B** (hard-coded `prefix_and_incrementer`) | none | dot.py:1247 |
| same | result LZC / LZA encoder, Wn bits | **A** | `lza.counter.family` / `lza.encoder.family` | dot.py:1126, 454, 462 |
| same | normalize shift, Wn bits: `_sh(m, None, ...)` | **C-no-slot** | none | dot.py:457, 465 |
| `reduced_latency_fma` fused rounding | low CPA (LWl) | **A** | `cpa.family` | dot.py:1311 |
| same | high compound adder (HWl) | **B** (hard-coded `compound_flagged_prefix`, topology from `cpa.topology`) | partial | dot.py:1322 |
| same | two incrementers (HWl, HWl-1) | **B** (hard-coded `prefix_and_incrementer`) | none | dot.py:1327, 1358 |
| `bridge_fma`, `mixed_precision_cascade_fma` | fp multiplier + fp adder | **A** (pins forwarded) | `multiplier.*`, `align.*`, `cpa.*`, `lza.*` | dot.py:1465-1482; fma_dot_spaces.py:125,141 |
| same, cascade | product rounder | **B** (`_round_trip`, hard-coded `dedicated_per_op`) | the declared `round` slot is ignored | dot.py:1509, 494 |
| same, `out == "acc"` | frame placement with `shifter=None` | **C-no-slot** | none | dot.py:1528 |
| every FMA-lineage family | the `round: rounding_space()` slot of `_fp_tail()` | never read anywhere in dot.py | none | fma_dot_spaces.py:22-24 |

### sfu.py (space: `sfu_spaces.py`)

sfu.py builds every module from one fixed-point netlist class `Net`,
whose primitives render directly to SystemVerilog operators. The divider
is the only library-kind component with a slot.

| family / group | component | class | slot pin | evidence |
|---|---|---|---|---|
| every family | every multiply (coefficient products, Horner / Estrin / monomial terms, squares), a.w x b.w | **C-no-slot**: no multiplier slot exists anywhere in sfu.py | none | sfu.py:244-248 (`sv = f"{a.name} * {b.name}"`), used at 1124-1362 |
| every family | every add / sub (accumulations, range reduction, reconstruction) | **C-no-slot** | none | sfu.py:232-242 |
| every family | every variable shift (`shlv` / `shrv`) | **C-no-slot** | none | sfu.py:284-294; call sites 938, 946, 967, 1013, 1144, 1164, 1438, 1456, 1489, 1495, 1526, 1580, 1704, 1710, 1951-1954, 2005-2044, 2091, 2247-2261, 2975, 3289-3311, 3616-3620, 3718-3734 |
| every family | every leading-zero count: a recursive-doubling mux tree of `Net` primitives, never the library LZC | **C-no-slot** | none | sfu.py:389-403 |
| `rational_approximation` | the final divide | **A** when `divider.family` is declared, **C-no-slot** otherwise (a note is recorded) | `divider.family` + `divider.*` | sfu.py:2716-2730; sfu_spaces.py:250 (`_divider_slot()`) |
| `softmax_layernorm`, `normalization_division=true_divider` | per-lane divider | **B** (hard-coded default `restoring_nonrestoring`; `softmax_layernorm` declares no `divider` slot) | `divider.family` read, undeclared | sfu.py:3664-3675; sfu_spaces.py:470-487 |
| `add_table_add` | its declared `address_adder: cpa_space()` and `final_adder: adder_tree_space()` slots are never read; the ATA adders are `Net.add` | ignored slots | none | sfu_spaces.py:175-176 |
| `piecewise_poly`, `single_poly`, `lut_plus_poly`, `mixed_degree`, `gpu_multifunction_interpolator`, `region_dependent`, `pwl*`, `sigmoid_tanh_pwl`, `transformer_activation_lut` | `evaluator` / `segmenter` / `quadratic_core` / `tail_evaluator` slots | **A**, but these are evaluator topologies rather than library kinds | `evaluator.family`, `segmenter.family`, `numerator.family`, `denominator.family`, `quadratic_core.family` | sfu.py:2633-2634, 3839-3863 |

### posit.py (space: `dsp_posit_spaces.py`)

| family | component | class | slot pin | evidence |
|---|---|---|---|---|
| `posit_adder_multiplier` (`regime_decode=lzc_plus_shifter`) | regime LZC, BW = n-1 bits (7-31) | **B**: module-level constant `LZC_FAMILY = "lzd_cell_tree"` | none | posit.py:73, 158 |
| same | regime shifter, BW bits | **B**: `SHIFTER_FAMILY = "barrel_mux_tree"` | none | posit.py:74, 162 |
| same (`two_stage_masked_decode`) | prefix-or thermometer + and-or matrix | **C-reason** (the family is the shifterless decode; docstring lines 15-18) | none | posit.py:165-178 |
| both decode families | sign-magnitude negation incrementer, n bits | **B** (`prefix_and_incrementer`) | none | posit.py:88-99, 149, 196 |
| encoder | normalizer LZC + shift, XW bits | **B** | none | posit.py:245, 248 |
| encoder | regime word `~({RW{1'b1}} >> (kabs+1))` and `1 << (RW-1-kabs)`, RW = n+es+XW+2 bits (60-90) | **C-no-slot** | none | posit.py:279 |
| encoder | field shift below the regime, RW bits | **B** | none | posit.py:281 |
| encoder | rounding increment, n bits | **B** | none | posit.py:289, 303 |
| `plam_sv` | operand LZC + normalize shift, XW bits (x2) | **B** | none | posit.py:331, 333 |
| `plam_sv` | Mitchell fraction adder `{1'b0,a_f} + {1'b0,b_f}`, XW bits | **C-no-slot** | none | posit.py:337 |
| `cvt_sv` to a float target | the float rounder | **B** (hard-coded `dedicated_per_op`, empty pins) | none | posit.py:370 |
| `posit_adder_multiplier` | the declared `sig_datapath: cpa_space()` slot is consumed by the seed rather than posit.py | **A**, in `alu_float.py` | `sig_datapath.*` mapped to `sig_adder.*` | alu_float.py:95-107; dsp_posit_spaces.py:149 |
| `posit_adder_multiplier` | the unit's exact multiplier | **B**: `self._fp_module("fp_multiplier", ("sig_mul_then_round", {}))` with empty pins, so `sig_mul.family` defaults to `direct_pp_parallel`; the space declares no multiplier slot | none | alu_float.py:110; fp.py:512 |
| `posit_adder_multiplier` | `sig_div: div_space()` | **A** through `fp.div_sv` / `fp.sqrt_sv` | `sig_div.*` | posit.py docstring 36-37; dsp_posit_spaces.py:150 |

### decimal.py (space: `decimal_spaces.py`)

| family | component | class | slot pin | evidence |
|---|---|---|---|---|
| `bcd_direct_addition` | 4-bit digit adders | **A** | `digit_adder.family` + `digit_adder.*` | decimal.py:320, 198-203; decimal_spaces.py:42 |
| same | digit generate / propagate sums `a_i + b_i` (5 bits) | **C-no-slot** (negligible) | none | decimal.py:285 |
| same | the group / full lookahead network | C (structural, by design) | `carry_scheme` | decimal.py:297-313 |
| `speculative_decimal_addition` | word-level binary carry network, 4D bits | **A** | `carry_network.family` + `carry_network.*` | decimal.py:420; decimal_spaces.py:58 |
| `redundant_decimal_addition` | exit assimilator | **A** by the pin, but `assimilator.family` is undeclared by the space (the family has no `components`) | `assimilator.family` | decimal.py:396 |
| `decimal_multioperand_addition` | root decimal CPA over the digits | **A** | `root_adder.family` + `root_adder.*` | decimal.py:638, 616-631; decimal_spaces.py:94-95 |
| same | reduction tree | **A** | `reduction_tree.family` | decimal.py:836; decimal_spaces.py:94 |
| `parallel_decimal_multiplication` | multiples 3x / 7x / 9x, one decimal add each | **A** | `final_adder.*` via `_bcd_adder_inst` | decimal.py:825-827, 753-770 |
| same | reduction tree + final adder | **A** | `reduction_tree.family`, `final_adder.family` | decimal.py:1128, 1132; decimal_spaces.py:141-142 |
| `decimal_digit_recurrence` (nonredundant) | per-stage comparisons `t >= mult[k]` and residual subtractions, 4(D+1) bits, D stages | **C-no-slot**; the declared `digit_select: qds_space()` slot is never read | none | decimal.py:1247-1253; decimal_spaces.py:169 |
| `decimal_newton` | reciprocal seed ROM | **C-no-slot**; the declared `seed: seed_table_space()` slot is never read (only the `seed_digits` choice) | none | decimal.py:1354, 1385-1395; decimal_spaces.py:183 |
| `decimal_newton` | iteration multipliers (b x, x u, a x, q b), (D+XD) digits | **A** when `multiplier.*` pins name choices, else **C-reason** | `multiplier.*`, an undeclared slot | decimal.py:1400-1409, 1212-1222, 1444-1451 |
| `decimal_newton` | `2 - t` and the correction adds | **A** (a generated decimal adder, default `ripple_carry` digit adders, so **B**) | `family` default in `_bcd_adder_inst` | decimal.py:757, 1404, 1424-1431 |
| `decimal_newton` | `ye = y >> {sh, 2'b00}`, 4(D+XD) bits (140-200) | **C-no-slot** | none | decimal.py:1416, 1421 |
| dividers | `bn = src << {k, 2'b00}` (digit normalize), 4D bits | **C-no-slot** | none | decimal.py:1157 |
| `decimal_newton` | `final_round` | **A** | `final_round.family` | decimal.py:1357; decimal_spaces.py:184 |

### redundant.py (space: `redundant_spaces.py`)

| family | component | class | slot pin | evidence |
|---|---|---|---|---|
| `generalized_signed_digit` | exit-conversion CPA, TW = (N+1)k+1 | **A** | `cpa.family` + `cpa.*` | redundant.py:238, 150-163 |
| same | position sums `p - t*r` per digit, tw = k+3 | **C-no-slot** | none | redundant.py:288 |
| `hybrid_signed_digit` | per-run binary adders (2 per run, L bits) | **A** | `binary_run_adder.family` | redundant.py:335, 384-385; redundant_spaces.py:59 |
| same | exit conversion P-N, TW = W+1 | **A** | `cpa.family` | redundant.py:338, 407 |
| same | run decrement `s0 - L'd1`, L bits per run | **C-no-slot** | none | redundant.py:369 |
| `carry_save_datapath` | assimilator, W+1 | **A** | `assimilator.family` | redundant.py:396; redundant_spaces.py:77 |
| same | the 3:2 / 4:2 / 5:3 / 7:3 level | C (structural, by design) | `compressor` | redundant.py:407-426 |
| `redundant_binary_multiplier` | final converter | **A** | `final_converter.family` (read in mul_ext.py) | mul_ext.py:771; redundant_spaces.py:95 |
| `rns_channel_arithmetic` | per-channel modular adder | **A** | `modular_adder.family` + `modular_adder.*` | redundant.py:982, 671; redundant_spaces.py:212 |
| same | generic modular multiplier `a * b`, n bits | **C-no-slot** (no multiplier slot in `rns_channel_arithmetic`) | none | redundant.py:726 |
| same (`booth_modular`) | row sum `" + ".join(rows)`, sw bits | **C-no-slot** | none | redundant.py:699 |
| same | `qm = q * mod`, tw bits | **C-no-slot** | none | redundant.py:719 |
| same | conditional subtract `(t >= mod) ? (t - mod) : t`, ow+1 | **C-no-slot** | none | redundant.py:672 |
| `rns_forward_converter` | chunk-table Horner / CSA folding | C (structural) | `implementation`, `chunk_bits`, `final_reduction` | redundant.py:975-979 |
| `rns_forward_converter` | its declared `column_reducer: adder_tree_space()` slot is never read | ignored slot | none | redundant_spaces.py:250 |
| `rns_reverse_converter` | CRT / MRC recombination sums | **C-no-slot** | none | redundant.py:655-665 |

### mul.py (space: `mul_spaces.py`)

| family | component | class | slot pin | evidence |
|---|---|---|---|---|
| `direct_pp_parallel`, `booth_recoded_parallel`, `carry_save_array` | final CPA, 2W bits | **A** | `reduction.cpa.adder.family` (+ `.adder.*`); `hybrid_arrival_driven` builds the arrival prefix graph | mul.py:351-381; mul_spaces.py:65, 21 |
| same | `assign p = row_s + row_c` fallback when the family has no module | **C-no-slot** | none | mul.py:377 |
| `booth_recoded_parallel` radix 8 | hard multiple `a3 = a_ext + {a_ext, 1'b0}`, n1+2 bits | **C-no-slot** (the `hard_multiple_gen` choice names `cpa_precompute` / `specialized_3m_cpa`, but no adder slot exists) | none | mul.py:433; mul_spaces.py:123-126 |
| `recursive_karatsuba` | three base multipliers | **B**: family chosen from the `base_multiplier` choice, hard-mapped | `base_multiplier` (a choice, not a slot) | mul.py:447, 461-465 |
| same | `asum` / `bsum` (m+1), `mid` two subtractions (2m+2), `mag` two adds (2W), `-mag` | **C-no-slot** (the family declares no components) | none | mul.py:480-490; mul_spaces.py:226-239 |

### mul_ext.py

| family | component | class | slot pin | evidence |
|---|---|---|---|---|
| `behavioral_star` | `p = a * b` | **C-reason** (the family's definition) | none | mul_ext.py:2-3; mul_spaces.py:114-115 |
| `squarer` (`divide_and_conquer`) | cross-product multiplier, max(h, hi_w) bits | **A** by the pin; `cross.family` is undeclared (the space declares only `reduction`) | `cross.family` | mul_ext.py:202-204; mul_spaces.py:305 |
| `squarer` | reduction + final CPA | **A** | `reduction.*`, `cpa.adder.*` | mul_ext.py via `final_add` |
| `truncated_fixed_width` | kept tree + final CPA | **A** | `kept_tree.family`, `kept_tree.geometry`, `kept_tree.cpa.adder.*` | mul_ext.py:290, 630-633; mul_spaces.py:255 |
| `logarithmic_mitchell` | leading-one detectors (2), n bits | **A** by the pin; `lod.family` is undeclared (the space declares only `antilog_shifter`) | `lod.family` | mul_ext.py:363, 371-372; mul_spaces.py:273 |
| same | operand normalize `v << lz`, n bits (2) | **C-no-slot** | none | mul_ext.py:374 |
| same | log-domain adder `fx + fy`, F+1 / F+2 bits; `kx + ky + c` | **C-no-slot** | none | mul_ext.py:386, 394-396 |
| same | antilog shift, PW = 2n+MW bits | **A** | `antilog_shifter.family` | mul_ext.py:364, 403-405 |
| `segmented_grid` | per-segment products | **A** by the pin; `segment.family` is undeclared | `segment.family` | mul_ext.py:643, 660; mul_spaces.py:342 |
| same | merge adders (cpa / shift_add_tree), PW = 2W+2 | **A** | `merge_adder.family` + `merge_adder.*` | mul_ext.py:644, 691-696 |
| same (`carry_save_tree`) | root CPA | **A** (family forwarded as `cpa.adder.family`) | `merge_adder.family` | mul_ext.py:682 |
| `redundant_binary_multiplier` | final converter, N = 2W+2 | **A** | `final_converter.family` | mul_ext.py:771 |

### adder_ext.py (space: `adder_spaces.py`)

| family | component | class | slot pin | evidence |
|---|---|---|---|---|
| `end_around_carry` (`two_pass_prefix`) | second-pass incrementer, W bits | **B** (hard-coded `prefix_and_incrementer`) | none (the space declares no components) | adder_ext.py:205; adder_spaces.py:325-341 |
| `approximate_truncated` | exact upper adder, W-k | **A** | `upper_adder.family` + `upper_adder.*` | adder_ext.py:217, 246; adder_spaces.py:374 |
| same (`segmented_subadders` / `speculative_segments`) | lower sub-adder, k bits | **A** (reuses `upper_adder.family`) | `upper_adder.family` | adder_ext.py:232, 240 |
| same | speculation window sum `al[k-1:k-win] + bl[...]`, win+1 <= 5 bits | **C-no-slot** (negligible) | none | adder_ext.py:243 |
| same | correction incrementer, U bits | **B** | none | adder_ext.py:252 |
| `carry_skip` / `carry_select` / `carry_increment` | block adders, B bits, ceil(W/B) blocks | **A** | `block_adder.family` + `block_adder.*` | adder_ext.py:266, 283-297; adder_spaces.py:209, 229, 258 |
| `carry_increment` | per-block incrementer, n bits | **B** (hard-coded `prefix_and_incrementer`): the declared `increment_stage: incrementer_space()` slot is ignored | none | adder_ext.py:294; adder_spaces.py:258-259 |
| `sparse_prefix_hybrid` (realized in adder.sv) | sum blocks | **B** (`SUM_SELECT` parameter only): the declared `sum_block: block_adder_space()` slot is ignored | `sum_block_style` only | families/__init__.py:261-263; adder_spaces.py:280 |

### approx.py (space: `approx_spaces.py`)

| family | component | class | slot pin | evidence |
|---|---|---|---|---|
| `segmented_carry_speculative` | sub-adders, k bits, ceil(W/k) blocks | **A** | `sub_adder.family` + `sub_adder.*` | approx.py:76, 100-116; approx_spaces.py:42 |
| same | correction incrementer, n bits | **B** (hard-coded `prefix_and_incrementer`) | none | approx.py:123 |
| same | window sum `wsum{bi}`, repair `s{bi} - 1'b1` | **C-no-slot** | none | approx.py:88, 125 |
| `lower_part_approximate` | exact upper adder, W-k | **A** | `upper_adder.family` | approx.py:142; approx_spaces.py:58 |
| `accuracy_configurable` | staged sub-adders | **A** | `sub_adder.family` | approx.py (staged path) |
| `truncated_fixed_width` (approximate) | kept tree + CPA | **A** | pins remapped to `kept_tree.*` | approx.py:232-241 |
| `dynamic_segment` | leading-one detectors (2), w bits | **B** (hard-coded `lzd_cell_tree`) | none | approx.py:266 |
| same | operand shifts `am << lza`, `pwe >> leftm` / `<< leftm`, SW = 2w+2seg+2 bits | **C-no-slot** | none | approx.py:270, 290 |
| same | window product, seg bits | mismatch: read as `core_multiplier.family` fed to `m.mul`, but the space declares `core_multiplier: cpa_space()`; a cpa family name yields `mul_module` None and the `*` operator | `core_multiplier.family` | approx.py:286; approx_spaces.py:114 |
| same | `pz0 + (1 << (leftm-1))` round-and-correct, 2w bits | **C-no-slot** | none | approx.py:294 |
| `operand_rounding` | leading-one detectors, w bits | **B** | none | approx.py:322 |
| same | `ksum = kra + krb`, RoBA shift-adds, PW = 2w+2 | **C-no-slot** | none | approx.py:329 onward |
| `logarithmic` | mantissa adder in the log domain | **C-no-slot**: the declared `log_adder: cpa_space()` slot is never read; only a `mantissa_adder` choice is | none | approx.py:373; approx_spaces.py:139 |
| `pp_perforation`, `approximate_compressor_tree`, `approximate_booth` | final CPA, 2w bits | path mismatch: `final_add(nl, cols, pins, "cpa")` reads `cpa.adder.family`, but the space declares `cpa: cpa_space()`, so the planner emits `cpa.family`, which lands in `cpa_family` and is discarded unless it is `hybrid_arrival_driven`; the result is silently `parallel_prefix` | `cpa.family` | approx.py:478, 541, 594; mul.py:364-365; approx_spaces.py:176 |
| `approximate_recurrence` | per-stage exact subtractor `sh + nb + 1`, RW = D+1, (Q-depth) stages | **C-no-slot** (the family declares no components) | none | approx.py:668 |
| same | inexact cell rows | C (the family's definition) | `cell`, `replaced_depth` | approx.py:651-666 |
| `approximate_functional` | operand LZC, N bits | **B** (hard-coded `lzd_cell_tree`) | none | approx.py:695 |
| same | `an = a << lza`, N bits; the reciprocal-multiply products | **C-no-slot** | none | approx.py:697 onward |

### subword.py (spaces: `mul_spaces.py`, `shift_simd_spaces.py`)

| family | component | class | slot pin | evidence |
|---|---|---|---|---|
| `twin_precision_subword` | lane-partitioned final CPAs, per segment of the 2W-bit row pair | **A**, default **B** = `ripple_carry` | `lane_cpa.family` + `lane_cpa.*` | subword.py:168-169, 184-190; mul_spaces.py:319 |
| same | the gated partial-product matrix and lane-kill carries | C (the family's definition) | `partition`, `base_scheme` | subword.py:120-155 |
| same (`per_lane_signed=False`) | per-lane negations `-a[...]`, `-pu[...]` | **C-no-slot** | none | subword.py:73-75 |
| `partitioned_carry_chain` | per-lane segment adders, `fine` bits, L lanes | **A**, default **B** = `ripple_carry` | `base_adder.family` + `base_adder.*` | subword.py:205-206, 237-249; shift_simd_spaces.py:220 |
| same | the `saturation: saturation_space()` slot | never read by subword.py (the seed applies saturation) | none | shift_simd_spaces.py:221 |

### alu_checker.py (space: `checker_spaces.py`)

| family | component | class | slot pin | evidence |
|---|---|---|---|---|
| all families | final compare of coded words / duplicated outputs | **A** (checker-local modules, not the shared library) | `spec["comparator"]["family"]`: `direct_compare` / `two_rail_tree` / `m_out_of_n_checker` / `majority_voter` | alu_checker.py:200-212, 527-552; checker_spaces.py:100 `cmp_slot` |
| `direct_compare` | `(lhs) != (rhs)`, word width | **C-reason** (the family is the word equality) | none | alu_checker.py:552 |
| `residue`, `inverse_residue`, `multi_residue`, `rns_redundant` | residue generator, 2^a-1 moduli | C (folding adder tree of `+`): the declared `generator_style` choice (`csa_tree` / `modular_ripple` / `lut`) is never read | none | residue.py:14-43; checker_spaces.py:112-113 |
| same | generic-modulus residue `x % M`, `width` bits | **C-no-slot** | none | residue.py:46-53 |
| same | prediction arithmetic `(ra * rb) % M`, `(... + ...) % M`, `% M` reductions, KW = 6-10 bits | **C-no-slot** | none | alu_checker.py:621-648 |
| `an_code` | AN multiplies `Ak * ext(aL)`, KW = 2 lw + abits + 3 bits, and the divisibility test `pred % Ak` | **C-no-slot** | none | alu_checker.py:674-695 |
| `parity_prediction_adder` | the replica carry chain | **C-no-slot**: the declared `carry_replica: cpa_space()` slot is never read | none | checker_spaces.py:193; alu_checker.py:39 (docstring only) |
| `parity_prediction_multiplier` | replica row reduction | **C-no-slot** | none | alu_checker.py:698-738 |
| `berger` | ones-count arithmetic | **C-no-slot** | none | alu_checker.py (berger path) |
| `reduced_precision` | narrow replica add / mul, R bits | **C-no-slot** | none | alu_checker.py:739-800 |
| `duplication` | the pruned reference copy | **A** (the seed's own module, which carries its own families) | none | alu_checker.py:416-423 |

### dot_checker.py

| family | component | class | slot pin | evidence |
|---|---|---|---|---|
| `residue` (the only family allowed: `checkers.py:17-20`) | residue generators, `wab` and `wd` bits | C (folding tree of `+`), generic modulus `x % M` | none | dot_checker.py:67; residue.py:46-53 |
| same | per-product `(ra * rb) % M`, the sum `(... + ...) % M`, KW = k+2 bits, n products | **C-no-slot** | none | dot_checker.py:120-138 |
| same | `pd = d - c`, wd bits | **C-no-slot** | none | dot_checker.py:128 |
| same | the final compare `!=`: no comparator slot is read at all | **C-no-slot**; the `comparator` slot `checker_space()` declares is ignored by the dot checker | none | dot_checker.py:97, 139; checker_spaces.py:100 |
| `duplication` / SR window | reference copies + `!=` | **A** for the copy, **C-no-slot** for the compare | none | dot_checker.py:58-61, 97 |

## 2. The C-no-slot cases by likely timing impact

Tier 1, hundreds of bits on the critical path of every dot operation:

1. dot.py normalize shifter, AW = 281-561 bits (up to 4288 for a quire): `_sh(m, None, ...)` passes `None` unconditionally, so no declared shifter family can reach it (dot.py:399, 407, 457, 465).
2. dot.py leading-zero counter over AW = 281-561 bits as the behavioral function `lzc_<W>`: `cfg["lz"]` counter is `None` for every accumulator family whose space declares no `lza` slot (`pairwise_tree`, `fused_csa`, `integer_mac`, `kulisch_long_accumulator`, `streaming_accurate_accumulator`, the block families, `tensor_core`) (dot.py:1565-1566, 121-134, 404).
3. dot.py integer path LZC, hard-coded `None` regardless of the run file: `_to_x(m, "o", "acc_i", AW, lo, g, "lzc_after_add", None)` (dot.py:1029).
4. dot.py alignment `<<` into the frame, AW bits per term: `_place` with `shifter = None` for every family without an `align` slot (dot.py:359, 673, 648-652).
5. dot.py `_frame_of_window` `<<<` / `>>>` over W2 = max(Wn, AW) (dot.py:482).
6. dot.py `_cpa_of` default `ripple_carry` (dot.py:227): a hard-coded ripple adder across AW = 281-561 bits whenever the family declares no `cpa` / `accum` / `reduction` slot (`bf16_fma_datapath`, `fp8_training_datapath`) or the run file names none.
7. dot.py kulisch segment carry chain `kr_j = s + cin` over Wk = 512-4288 bits (dot.py:880-885).

Tier 2, 60-200 bits, repeated per stage or per iteration:

8. div.py dividend scaling `{D'b0, ax} << lzs`, NW = N+S+D (130-160 bits) (div.py:290, 405, 489, 783).
9. div.py quotient de-scale `px >> (F+D-S-lzs)`, PW = N+XWd (110-170 bits) (div.py:884, 887).
10. div.py functional iteration adders (`2 - dx`, `e`, `g`) at XWd = 60-110 bits per step (div.py:824-847).
11. div.py SRT per-stage assimilating CPA and final assimilation, RW = D+3, Q stages (div.py:302, 311, 317).
12. div.py back-multiply correction `ax - qb`, `rr +- bs`, RC = 110-140 bits (div.py:892, 900-904).
13. div.py restoring-sqrt comparator + subtractor per root bit (RW = Q+2, Q stages) (div.py:941-942).
14. decimal.py `ye = y >> {sh, 2'b00}`, 4(D+XD) = 140-200 bits (decimal.py:1416, 1421).
15. sfu.py every `shlv` / `shrv` and every `mul` at F = 30-60 fraction bits, several per polynomial evaluation (sfu.py:244-248, 284-294).
16. sfu.py every leading-zero count as a recursive-doubling mux tree of `Net` primitives (sfu.py:389-403).

Tier 3, significand width (26-53 bits), once per operation:

17. fp.py rounder `restmask`, `halfv`, `fint` variable shifts at XW+1 / XW+sb+1 (fp.py:711, 713, 718).
18. fp.py align sticky mask `~({IW{1'b1}} << amt)`, IW = XW+1 (fp.py:371).
19. fp.py injection rounder `sum_i` (XW+2) and `magi = sum_i >> sha` (fp.py:750-751).
20. fp.py `round_fused_in_reduction` injection shifts and adders at PW+1 = 2 SW+1 (fp.py:552-576).
21. posit.py regime word `~({RW{1'b1}} >> (kabs+1))` / `1 << (RW-1-kabs)`, RW = 60-90 (posit.py:279).
22. mul.py Karatsuba `mid` / `mag` adders at 2W and the `asum` / `bsum` at m+1 (mul.py:480-490).
23. mul_ext.py Mitchell operand normalize `v << lz` (n) and log adder `fx + fy` (F+1) (mul_ext.py:374, 386).
24. redundant.py generic modular multiplier `a * b` (n bits) and the Booth row sum (redundant.py:726, 699).
25. div.py divisor normalize `b << lzs` and remainder `rf >> lzs`, D bits (div.py:179, 327).
26. fp.py `coarse_fine` `(src_lz / cg) * cg` and `% cg`, a real divider when `coarse_granularity` is not a power of two (fp.py:439-440).

Tier 4, narrow, low impact:

27. fp.py exponent path `ea - eb` at EW+1 (fp.py:322); fp.py `e = a_e + b_e` (fp.py:530).
28. alu_checker.py / dot_checker.py residue arithmetic at KW = 6-10 bits (alu_checker.py:621-648; dot_checker.py:120-138) and `residue.py:50` `x % M`.
29. decimal.py digit `a_i + b_i` at 5 bits (decimal.py:285); adder_ext.py `wsum` at <= 5 bits (adder_ext.py:243); redundant.py run decrement (redundant.py:369).

### Slots the spaces declare that the generator ignores

| space : family | slot declared | what the generator does instead | evidence |
|---|---|---|---|
| `fp_spaces.norm_space` (every family) : `single_path`, `low_power_gated` | `norm.lz` (an `lza_space`, with its own `counter` / `encoder`) | fp.py greps only `near_lz.family` / `lz.family`; `norm.lz.family` never matches and defaults to `lzc_after_add` + `lzd_cell_tree` | fp_spaces.py:124-125, 134-135; fp.py:274-277 |
| `fp_spaces.rounding_space` : `compound_adder_select` | `compound_adder` (a full `cpa_space`) | fp.py hard-codes `compound_flagged_prefix`, reads only `compound_adder.topology` | fp_spaces.py:165; fp.py:737-740 |
| `fp_spaces.align_space` (both families) | `mux_radix`, `swap_before_shift` choices | never read | fp_spaces.py:89-90 |
| `fma_dot_spaces._fp_tail()` : every FMA-lineage family | `round` (a `rounding_space`) | never read anywhere in dot.py; `_round_trip` hard-codes `dedicated_per_op` with empty pins | fma_dot_spaces.py:24; dot.py:494 |
| `div_spaces.div_space` : `srt_radix2` | `digit_select` (a `qds_space`) | `_srt2_sv` reads none of it; the digit is a bare comparison | div_spaces.py:221; div.py:307-308 |
| `div_spaces.div_space` : `digit_recurrence_sqrt_combined` | `digit_select` | routed to `restoring_sv` / `sqrt_sv`, which read `residual_adder.family` or nothing | div_spaces.py:335; div.py:1059, 941-942 |
| `div_spaces.qds_space` : `comparator_digit_selection` | `comparator_adder` (a `cpa_space`) | the four thresholds are `y_i >= th` comparisons | div_spaces.py:72; div.py:435 |
| `div_spaces.div_space` : `direct_polynomial` | `approximator` is an `sfu_approx_space` | div.py reads `approximator.family` as a seed-table name and discards anything not in `SEED_FAMILIES` | div_spaces.py:314; div.py:760-762 |
| `sfu_spaces.sfu_approx_space` : `add_table_add` | `address_adder` (`cpa_space`), `final_adder` (`adder_tree_space`) | never read; the ATA adders are `Net.add` | sfu_spaces.py:175-176 |
| `decimal_spaces.decimal_div_space` : `decimal_digit_recurrence` | `digit_select` (`qds_space`) | never read; the digits are `t >= mult[k]` | decimal_spaces.py:169; decimal.py:1247 |
| `decimal_spaces.decimal_div_space` : `decimal_newton` | `seed` (`seed_table_space`) | never read; the seed is a fixed ROM over the leading digits | decimal_spaces.py:183; decimal.py:1385-1395 |
| `redundant_spaces.rns_space` : `rns_forward_converter` | `column_reducer` (`adder_tree_space`) | never read anywhere in `chialu/targets` | redundant_spaces.py:250 |
| `adder_spaces.cpa_space` : `carry_increment` | `increment_stage` (`incrementer_space`) | `prefix_and_incrementer` hard-coded | adder_spaces.py:258-259; adder_ext.py:294 |
| `adder_spaces.cpa_space` : `sparse_prefix_hybrid` | `sum_block` (`block_adder_space`) | `fam_adder_sparse_prefix_hybrid` takes only `W`, `SP`, `SUM_SELECT` | adder_spaces.py:280; families/__init__.py:261-263 |
| `approx_spaces` : `logarithmic` | `log_adder` (`cpa_space`) | never read; only a `mantissa_adder` choice | approx_spaces.py:139; approx.py:373 |
| `approx_spaces` : `dynamic_segment` | `core_multiplier` declared as a `cpa_space` but read as a multiplier family | a cpa family name makes `mul_module` return None, the `*` operator | approx_spaces.py:114; approx.py:286 |
| `approx_spaces` : `approximate_compressor_tree`, `pp_perforation`, `approximate_booth` | `cpa` (a `cpa_space`, pin path `cpa.family`) | `final_add` reads `cpa.adder.family`; `cpa.family` lands in the unused `cpa_family` variable | approx_spaces.py:176; mul.py:364-365 |
| `shift_simd_spaces.shifter_space` : `masked_merged` | `rotator` (`rotator_space`) | `fam_shift_masked_merged` takes only `W` | shift_simd_spaces.py:76; families/__init__.py:427 |
| `shift_simd_spaces.shifter_space` : `butterfly_network` | `prefix_popcount` (`bitcount_space`), `lrotc_rotator` (`rotator_space`) | `fam_shift_butterfly_network` takes only `W` | shift_simd_spaces.py:95-96; families/__init__.py:431 |
| `shift_simd_spaces.bitcount_space` : `popcount_counter_tree` | `final_adder` (`cpa_space`) | `fam_count_popcount_counter_tree` takes only `W`, `SHAPE` | shift_simd_spaces.py:135; families/__init__.py:449 |
| `shift_simd_spaces.subword_space` : `partitioned_carry_chain` | `saturation` (`saturation_space`) | not read by subword.py (the seed applies saturation) | shift_simd_spaces.py:221 |
| `checker_spaces.checker_space` : `parity_prediction_adder` | `carry_replica` (`cpa_space`) | never read; the replica chain is `+` | checker_spaces.py:193 |
| `checker_spaces.checker_space` : every family, under the dot unit | `comparator` (`two_rail_space`) | dot_checker.py compares with `!=` and reads no comparator | checker_spaces.py:100; dot_checker.py:97, 139 |
| `checker_spaces.checker_space` : `residue` | the `generator_style` choice (`csa_tree` / `modular_ripple` / `lut`) | residue.py always builds the folding tree | checker_spaces.py:112-113; residue.py:14-43 |
| `dsp_posit_spaces.posit_unit_space` : `posit_adder_multiplier` | no multiplier slot exists, and the seed hands `fp.mul_sv` empty pins | the significand multiplier is always `direct_pp_parallel` | alu_float.py:110; fp.py:512 |

Slots a generator reads but no space declares (they work only when a
run file names them by hand): `lzc.family`, `shifter.family` (fp
unpacker, fp.py:237, 239); `counter.family`, `shifter.family`,
`incrementer.family`, `round.family` (fp rounder, fp.py:664-669, 758);
`norm.lzc.family`, `norm.shifter.family` (fp div / sqrt, fp.py:804, 807;
div.py:175); `seed.family` on `svoboda_tung` (div.py:760); `lod.family`
(mul_ext.py:363); `cross.family` (mul_ext.py:202); `exact.family`
(mul_ext.py:472); `segment.family` (mul_ext.py:643); `assimilator.family`
on `redundant_decimal_addition` (decimal.py:396); `multiplier.*` on the
decimal dividers (decimal.py:1447); `divider.family` on
`softmax_layernorm` (sfu.py:3664).

## 3. Helper constants that cap library use

| constant | value | location | reason, quoted |
|---|---|---|---|
| `SHIFTER_LIBRARY_MAX` | 128 | dot.py:100 | Module docstring (dot.py:58-63): "The alignment shifter of a datapath wider than SHIFTER_LIBRARY_MAX bits is the language's shift even when declared, since the mux-tree netlist over the seed's exact frame costs verilator more than the conformance budget; the module comment records the substitution, and synthesis builds the same mux tree from the operator." Helper `_sh` (dot.py:103-110) repeats it. Enforced at dot.py:111; the note is appended to the module comment at dot.py:113-116. |
| `_lz` behavioral-function fallback (no constant; the guard is `if fam:`) | none | dot.py:121-134 | "out = the leading-zero count of src (width.bit_length() bits) through the library counter when a family is declared, else a function with a loop (a procedural block with a break re-triggers under the yosys frontend)." This documents the form of the fallback (a `function` rather than `always_comb`), not a reason for having no slot. |
| `MAX_ACC_BITS` | 4096 | dot_seed.py:22 | A hard error rather than a library cap: "derived seed: the exact accumulator of mode {mi} needs {AW} bits (> {MAX_ACC_BITS}); use loop.seed_policy: file" (dot_seed.py:104-106). It bounds how wide the C-no-slot shifters and LZCs above can get. |
| `PATTERN_MAX_BITS` | 12 | sfu.py:100 | "a value table's widest format (4096 entries)"; docstring (sfu.py:66): "The value tables (direct_lut, compressed_lut) serve formats of at most PATTERN_MAX_BITS bits." Caps the table families, not library instances. |
| `PROFILE_BITS` | 60 | sfu.py:101 | "the working precision of the real-valued reference in mpmath (bits)": generation time only. |
| `div.Mod.umul` multiplier fallback (the guard is `if not fam or fam == "behavioral_star"`) | none | div.py:124-136 | "out (xw + yw bits) = x * y unsigned, through the library multiplier of the declared family at the common width (the narrower operand zero-extended), or the operator when no family is declared for the multiplier component (its netlist would dominate the module)." The module header records it (div.py:909, 1048). |
| `decimal._beh_mul_fn` / `_mul_inst` fallback (the guard is `if not pins`) | none | decimal.py:1186-1222 | `_beh_mul_fn` (1187-1190): "A behavioral decimal product function (DA x DB digits): the digit products summed per column, the columns carried; the structure is left to synthesis, as the operator is for the binary functional dividers whose multiplier component is undeclared." `_mul_inst` (1213-1217): "else the behavioral decimal product (the netlist of a partial-product tree per multiply would dominate the divider and its simulation)." |
| RNS product-table budget (the guard is `if 2 * ow <= 10`) | 10 index bits (1024 entries) | redundant.py:682-686 | Emitted comment: "channel {tag}: a {2*ow}-bit product table exceeds the table budget; the folding tree stands in". |

There is no analogue of `SHIFTER_LIBRARY_MAX` for the leading-zero
counter, the adder or the multiplier in dot.py: the LZC and the normalize
shift at AW bits are unconditional (`_sh(m, None, ...)`, `lzc_fam =
None`) rather than width-gated, so they are C-no-slot rather than
C-with-reason.

## 4. Slot domains against the realized families, and reachability

This part was taken the same day as sections 1 to 3, also before the
deferral: rows on speculative_variable_latency, digit_serial_adder,
sequential_shift_add, iterative_reuse, self_timed_variable_latency and
iterative_decimal_multiplication are moot since then, and the
`approximator` slot's domain is 25 SFU families rather than 26.

Method: every space factory in `chialu/spaces/*.py` was imported and
`Family.components` walked recursively (the compiler in
`third_party/adir/adir/spaces.py:91-105` turns a slot into
`<prefix>.<slot>.family` over the union of the sub-space's families);
every `"<slot>.family"` pin read in `chialu/targets/rtl/families/` was
matched against the declared slot. Counts: 250 distinct (family, slot)
declaration sites, 89 distinct slot names, 33 distinct slot domains;
139 distinct realized family names (about 144 (kind, family) pairs; the
count of 155 also counts `has_module("comparator", <adder family>)` for
the subtractor path and the `fp_sqrt` kind).

### 4.1 The slot domains

| id | space | n | members |
|----|-------|---|---------|
| D0 | `cpa_space()` | 17 | ripple_carry, manchester_carry_chain, carry_lookahead, carry_skip, carry_select, conditional_sum, carry_increment, parallel_prefix, sparse_prefix_hybrid, ling_prefix, compound_flagged_prefix, end_around_carry, speculative_variable_latency, approximate_truncated, prefix_synthesis_nonuniform_arrival, fpga_carry_chain, digit_serial_adder |
| D1 | `mul_space(w)` | 15 | behavioral_star, booth_recoded_parallel, direct_pp_parallel, carry_save_array, sequential_shift_add, serial_serial_parallel, iterative_reuse, recursive_karatsuba, truncated_fixed_width, logarithmic_mitchell, approximate_compressor, squarer, twin_precision_subword, segmented_grid, redundant_binary_multiplier |
| D2 | `rounding_space()` | 4 | increment_adder, compound_adder_select, injection, flagged_prefix |
| D3 | `block_adder_space()` | 4 | ripple_carry, manchester_carry_chain, carry_lookahead, parallel_prefix |
| D4 | `align_space()` | 2 | full_align, bounded_align |
| D5 | `lza_space()` | 2 | lza, lzc_after_add |
| D6 | `adder_tree_space()` | 3 | linear_chain, binary_tree, csa_tree |
| D7 | `reduction_space()` | 3 | csa_reduction_tree, compressor_4_2_tree, tiled_cpa_reduction_tree |
| D8 | `two_rail_space()` | 3 | two_rail_tree, m_out_of_n_checker, majority_voter |
| D9 | `qds_space()` | 2 | qds_table, comparator_digit_selection |
| D10 | `exponent_space()` | 1 | exponent_path |
| D11 | `subnormal_space()` | 3 | full_hardware, trap_to_software, flush_to_zero_mode |
| D12 | `segment_space()` | 5 | uniform_high_bit_decode, nonuniform, hierarchical, power_of_two, ralut |
| D13 | `seed_table_space()` | 7 | monolithic_rom, bipartite_rom, symmetric_bipartite, multipartite, operand_modification_multiply, poly_seed, magic_constant_bit_seed |
| D14 | `poly_datapath_space()` | 8 | horner, estrin, parallel_monomial, factored, coefficient_adapted, shift_add_coeff, shared_multiplier, fma_based |
| D15 | `mult_final_round_space()` | 3 | back_multiply_remainder, exclusion_zone_proof, extra_precision_quotient |
| D16 | `shifter_space()` | 5 | barrel_mux_tree, funnel, masked_merged, butterfly_network, fpga_mapped |
| D17 | `range_reduction_space()` | 1 | range_reduction |
| D18 | `final_cpa_space()` | 2 | uniform, hybrid_arrival_driven |
| D19 | `norm_space()` | 2 | coarse_fine, single_barrel |
| D20 | `rotator_space()` | 1 | barrel_mux_tree |
| D21 | `div_space()` | 11 | restoring_nonrestoring, srt_radix2, srt_high_radix, prescaled_very_high_radix, svoboda_tung, newton_raphson, goldschmidt, direct_polynomial, digit_recurrence_sqrt_combined, online_msdf, self_timed_variable_latency |
| D22 | `decimal_mul_space()` | 2 | iterative_decimal_multiplication, parallel_decimal_multiplication |
| D23 | `lzc_space()` | 2 | recursive_doubling_lzd, prefix_lzc |
| D24 | `incrementer_space()` | 1 | prefix_and_incrementer |
| D25 | `sfu_approx_space()` | 26 | direct_lut to softmax_layernorm (25 realized + correct_rounding_strategy) |
| D26 | `bitcount_space()` | 4 | popcount_counter_tree, lzd_cell_tree, trailing_zero, priority_encoder |
| D27 | `decimal_adder_space()` | 4 | bcd_direct_addition, speculative_decimal_addition, redundant_decimal_addition, decimal_multioperand_addition |
| D28 | `decimal_div_space()` | 2 | decimal_digit_recurrence, decimal_newton |
| D29 | `fp_add_space()` | 5 | single_path, two_path, delay_optimized_unified, variable_latency, low_power_gated |
| D30 | `fp_mul_space()` | 2 | sig_mul_then_round, round_fused_in_reduction |
| D31 | `fp_div_space()` | 2 | sig_div_then_round, sig_sqrt_then_round |
| D32 | `saturation_space()` | 1 | saturating_clamp |
| D33 | `fp_fma_space(w)` | 5 | separate_multiplier_and_adder, classic_fma, reduced_latency_fma, multipath_fma, bridge_fma |

Verdict key: OK = the generator reads `<slot>.family` and instantiates
every realizable member; IGNORED = the slot is declared and the family
never read; NARROWED = the helper accepts only part of the domain;
MISTYPED = the slot's space is not the space the generator consumes.

### 4.2 Slot to families, per space

adder_spaces.py:

| file:line | family.slot | domain | consumer | verdict |
|---|---|---|---|---|
| adder_spaces.py:209 | carry_skip.block_adder | D3 | `__init__.py:241` to `adder_ext.block_adder_sv` (adder_ext.py:264-296), `Mod.adder` to `FAM.adder_module` (adder_ext.py:70-83) | OK (all 4; the helper would accept 15) |
| :229 | carry_select.block_adder | D3 | same | OK |
| :258 | carry_increment.block_adder | D3 | same | OK |
| :259 | carry_increment.increment_stage | D24 | none | IGNORED: `adder.sv:241` `fam_adder_carry_increment #(W,B,INTER)` has no incrementer port; the block path hard-codes `m.incr("prefix_and_incrementer", {"structure": "prefix_and_tree"}, ...)` at adder_ext.py:291 |
| :280 | sparse_prefix_hybrid.sum_block | D3 | none | IGNORED: `__init__.py:261-263` maps only `log2_sparsity` and `sum_block_style` into `adder.sv:294` `fam_adder_sparse_prefix_hybrid #(W,SP,SUM_SELECT)` |
| :374 | approximate_truncated.upper_adder | D3 | adder_ext.py:217 `upper_adder.family` | OK, but the helper accepts all 15, so D3 is an artificial narrowing |

arith_spaces.py / mul_spaces.py:

| file:line | family.slot | domain | consumer | verdict |
|---|---|---|---|---|
| arith_spaces.py:29 | binary_tree.cpa | D0 | dot.py:247-258 `_tree_of` to `_cpa_of` to `_add` to `FAM.adder_module` | OK (15 of 17) |
| arith_spaces.py:34 | csa_tree.final_cpa | D0 | same | OK |
| (linear_chain declares no slot) | | | dot.py:257 falls back to the parent's `cpa` / `final_cpa` pins | undeclared-pin path |
| mul_spaces.py:21 | uniform.adder | D0 | mul.py:365-381 `final_add` | OK |
| :38 | hybrid_arrival_driven.region_adder | D0 | none | IGNORED: mul.py:368-374 builds an arrival-driven prefix graph; `region_count`, `region_adder_mix`, `arrival_model`, `boundary_search` are dead too |
| :65 | csa_reduction_tree.cpa | D18 | mul.py:422 `final_add(..., "reduction.cpa")` | OK |
| :83 | compressor_4_2_tree.cpa | D18 | same | OK if reached (see `reduction` below) |
| :99 / :100 | tiled_cpa_reduction_tree.tile_adder / .cpa | D0 / D18 | none | IGNORED (the family itself is unreachable) |
| :132 / :152 | booth_recoded_parallel / direct_pp_parallel `.reduction` | D7 | mul.py:417-419 | NARROWED to 1 of 3: `reduction.family` is never read; only `reduction.geometry` and `reduction.counter_kind`; `compressor_4_2_tree` and `tiled_cpa_reduction_tree` cannot be selected |
| :133 / :153 | `.hard_multiple_adder` | D0 | none | IGNORED: mul.py:401 reads `hard_multiple_gen` only |
| :172 | carry_save_array.cpa | D18 | mul.py:414 | OK |
| :255 | truncated_fixed_width.kept_tree | D7 | mul_ext.py:341 | NARROWED: only `compressor_4_2_tree` is distinguished (counter `4_2`); `tiled_cpa_reduction_tree` becomes dadda / 3:2 |
| :273 | logarithmic_mitchell.antilog_shifter | D16 | mul_ext.py:364 | OK; plus an undeclared `lod.family` (lzc) at mul_ext.py:363 |
| :305 | squarer.reduction | D7 | mul_ext.py:236 | NARROWED (geometry / counter only) |
| :319 | twin_precision_subword.lane_cpa | D0 | subword.py:168 | OK |
| :342 | segmented_grid.merge_adder | D0 | mul_ext.py:644 | OK; plus an undeclared `segment.family` (sub-multiplier) at mul_ext.py:643 |
| (recursive_karatsuba declares no slot) | | | mul_ext.py:472 reads `exact.family`, mul_ext.py:202 reads `cross.family` | UNDECLARED SLOTS |

`mul.py:317-322 reduce()` also swallows enum members: `geometry` in
{reduced_area, tdm_arrival_driven} falls through to dadda; `counter_kind`
in {5_2, 7_3} falls through to 3:2 (dot.py:275 has a 7:3 reducer).

div_spaces.py:

| file:line | family.slot | domain | consumer | verdict |
|---|---|---|---|---|
| div_spaces.py:72 | comparator_digit_selection.comparator_adder | D0 | none | IGNORED (no `comparator_adder` pin anywhere) |
| :203 | restoring_nonrestoring.residual_adder | D0 | div.py:213 | OK |
| :221 / :241 / :335 | srt_radix2 / srt_high_radix / digit_recurrence_sqrt_combined `.digit_select` | D9 | div.py:381 | OK for srt_high_radix; the other two never read it (section 1) |
| :254 | prescaled_very_high_radix.prescaler | D1 | div.py:763 (`mul_key="prescaler."`) to `Mod.umul` to `FAM.mul_module` (div.py:124-136) | OK (11 of 15) |
| :255 / :279 / :296 | `.seed` | D13 | div.py:758-760 | OK (7 of 7; `operand_modification_multiply` rejected for rsqrt at div.py:950, documented) |
| :266 | svoboda_tung.prescaler | D1 | div.py:763 | OK |
| :280 / :297 | newton_raphson / goldschmidt `.iter_mult` | D1 | div.py:764 | OK |
| :281 / :298 / :316 | `.final_round` | D15 | div.py:769 | OK (3 of 3) |
| :314 | direct_polynomial.approximator | D25 | div.py:758-760: `seed_fam = _pin(pins, "seed.family", _pin(pins, "approximator.family", default))`, then `if seed_fam not in SEED_FAMILIES: seed_fam = default_seed` | MISTYPED and REJECTING: the slot is declared over `sfu_approx_space()` but resolved against `SEED_FAMILIES` (div.py:43-44, 7 members); 22 of the 25 SFU families are silently replaced by `poly_seed`; the survivors survive by name collision with the seed space |
| :315 | direct_polynomial.final_mul | D1 | div.py:763 | OK |
| (none) | | | div.py:173 reads an undeclared `norm.lzc.family`; div.py:677 and :714 read an undeclared `mul.family` inside the seed tables | UNDECLARED SLOTS |

fp_spaces.py:

| file:line | family.slot | domain | consumer | verdict |
|---|---|---|---|---|
| fp_spaces.py:69 | lza.encoder | D23 (2) | fp.py:276 (`lz.counter/encoder.family`, default `lzd_cell_tree`), dot.py:1126 | DOMAIN SMALLER THAN ITS OWN DEFAULT (gap 3 below) |
| :79 | lzc_after_add.counter | D23 | same | same |
| :99 / :108 | full_align / bounded_align `.shifter` | D16 | fp.py:268 to fp.py:177-189 `_shift` | OK; `butterfly_network` silently degraded to `barrel_mux_tree` at non-power-of-two widths (fp.py:183-184) |
| :124 / :134 | coarse_fine / single_barrel `.shifter` | D16 | fp.py:279 | OK |
| :124 / :134 | `.lz` | D5 | fp.py:274-275 | OK |
| :165 | compound_adder_select.compound_adder | D0 | none | IGNORED (fp.py:734-743 uses the flagged / compound path inline) |
| :233 (`_fp_add_common_components`) | `*.sig_adder` | D0 | fp.py:272 | OK |
| :234 | `*.round` | D2 | none | IGNORED by `add_sv`: rounding lives in `round_sv`, which reads the pin as `round.family` (fp.py:664) under the rounder slot, whose space (`misc_spaces.rounder_space`) declares no `round` slot |
| :235 | `*.exp` | D10 | fp.py:271 (`exp.dual_direction_subtract`) | OK (1 family) |
| :236 | `*.subnormal` | D11 | fp.py:281 reads `subnormal.internal_representation` only | IGNORED family: `trap_to_software` and `flush_to_zero_mode` produce identical RTL |
| :259 / :278 / :301 / :320 / :337 | the fp-add families' align / far_align / norm / close_norm / near_lz | D4 / D19 / D5 | fp.py:266-280, used at :347, :435 | OK |
| :386 | shift_round_convert.shift_unit / .round / .lz | D4 / D2 / D23 | none | ALL IGNORED: `__init__.py:357` calls `fp.round_sv(fmt, geom, "dedicated_per_op", ...)` for the kind `converter`; the declared family is discarded |
| :406 | internal_format_datapath.core_add / core_mul / core_div / round | D29 / D30 / D31 / D2 | none | ALL IGNORED (same line) |
| :426 / :437 | sig_mul_then_round / round_fused_in_reduction `.sig_mul` | D1 | fp.py:511 | OK (12 of 15) |
| :449 / :458 | sig_div_then_round.sig_div / sig_sqrt_then_round.sig_sqrt | D21 | fp.py:826, :874 to `div.div_sv` / `sqrt_sv` | OK (10 of 11) |

fma_dot_spaces.py (`_fp_tail()` at lines 22-24 opens `align`, `lza`,
`cpa`, `round` on all seven FMA / dot families at lines 80, 94, 109,
125, 141, 152, 166, 196):

| slot | domain | consumer | verdict |
|---|---|---|---|
| `*.mul` / `*.multiplier` (:33, 60, 80, 94, 109, 125, 141, 152, 166, 196, 258, 277, 294, 313, 333) | D1 | dot.py:192-208 `_inst_mul` to `FAM.mul_module` | OK (11 of 15: `behavioral_star` is the operator by definition, `twin_precision_subword` behavioral) |
| `*.accum` / `*.reduction` (:33, 60, 197, 259, 278, 295) | D6 | dot.py:247-258 `_tree_of` + dot.py:300-342 `_sum_words` | OK (3 of 3, compressors 3:2 / 4:2 / 7:3) |
| `*.cpa` / `*.final_cpa` (:40, 222, 240 + `_fp_tail`) | D0 | dot.py:220-225 `_cpa_of` to `_add` | OK (15 of 17) |
| `*.lza` | D5 | dot.py:1125, :1565 | OK |
| `*.align` | D4 | dot.py:1123, :1564 read only `align.shifter.family` | IGNORED family: `full_align` and `bounded_align` are never distinguished; the alignment policy comes from the family's own choices (dot.py:1569, :1584) |
| `*.round` | D2 | none | IGNORED: `round.family` is read nowhere in dot.py; the FMA-via-add forwarding list at dot.py:1469-1470 omits it |
| the shifter behind `align.shifter` | D16 | dot.py:103-118 `_sh` | NARROWED by width: above `SHIFTER_LIBRARY_MAX = 128` (dot.py:100) the declared family is replaced by the language's shift, recorded in the module comment (dot.py:113-116) |

sfu_spaces.py:

| file:line | family.slot | domain | consumer | verdict |
|---|---|---|---|---|
| sfu_spaces.py:175 | add_table_add.range_reducer | D17 | sfu.py:2137-2139 (choices) | OK (1 family) |
| :175 | add_table_add.address_adder | D0 | none | IGNORED |
| :176 | add_table_add.final_adder | D6 | none | IGNORED |
| :196, 209, 219, 272, 309, 316, 442, 458 | `*.segmenter` | D12 | sfu.py:2634, :3839; `_SEGMENTERS` (sfu.py:832) = all 5 | OK |
| :219, 235, 272, 316 | `*.evaluator` | D14 | sfu.py:3840; `_EVALUATORS` (sfu.py:830-831) = 7 | NARROWED 7 of 8: `shared_multiplier` rejected (documented, sfu.py:92); `coefficient_adapted` outside degrees 3 to 4 and `fma_based` are replaced by Horner with a note (sfu.py:1202-1203) |
| :250 | rational_approximation.numerator / .denominator | D14 | sfu.py:2633 | same |
| :250 | rational_approximation.divider | D21 | sfu.py:2716-2725 to `FAM.div_module` | OK (10 of 11) |
| :293 | table_factor_refinement.tail_evaluator | D14 | none | IGNORED |
| :328 | gpu_multifunction_interpolator.quadratic_core | D14 | sfu.py:3863 | OK |
| (softmax_layernorm, sfu_spaces.py:466) | | | sfu.py:3664 reads `divider.family` | UNDECLARED SLOT: the family has a `normalization_division` choice but no `divider` component |

decimal_spaces.py:

| file:line | family.slot | domain | consumer | verdict |
|---|---|---|---|---|
| decimal_spaces.py:42 | bcd_direct_addition.digit_adder | D0 | decimal.py:320 | OK |
| :58 | speculative_decimal_addition.carry_network | D0 | decimal.py:420 | OK |
| :94 / :95 | decimal_multioperand_addition.reduction_tree / .root_adder | D6 / D0 | decimal.py:836, :839 | OK |
| :141 / :142 | parallel_decimal_multiplication.reduction_tree / .final_adder | D6 / D0 | decimal.py:1128, :1133 | OK (3 of 3 trees) |
| :169 | decimal_digit_recurrence.digit_select | D9 | none | IGNORED: `digit_select` appears nowhere in decimal.py |
| :183 | decimal_newton.seed | D13 | none | IGNORED: decimal.py:1354 reads `seed_digits` only |
| :184 | decimal_newton.final_round | D15 | decimal.py:1357 | OK |
| :209, 230, 248, 267, 268, 325, 344, 358, 359, 360 | the slots of decimal_fp_addition, bid_fp_addition, decimal_fma, decimal_fp_multiplication, redundant_decimal_conversion, decimal_cordic, commercial_decimal_fpu | D27 / D1 / D22 / D0 / D13 / D28 | none | NO GENERATOR for these `decimal_misc_space` families (decimal_spaces.py:193-365); they are not in `DECIMAL_FAMILIES` (decimal.py:83-86) and not in any `core_slots` kind (chialu/modules/alu.py:98-156) |

redundant_spaces.py:

| file:line | family.slot | domain | consumer | verdict |
|---|---|---|---|---|
| redundant_spaces.py:59 | hybrid_signed_digit.binary_run_adder | D0 | redundant.py:335 | OK |
| :77 | carry_save_datapath.assimilator | D0 | redundant.py:396 | OK |
| :95 | redundant_binary_multiplier.final_converter | D0 | mul_ext.py:771 | OK |
| :212 | rns_channel_arithmetic.modular_adder | D0 | redundant.py:982 | OK |
| :249 | rns_forward_converter.modular_adder | D0 | redundant.py:982 | OK |
| :250 | rns_forward_converter.column_reducer | D6 | none | IGNORED |
| (generalized_signed_digit, :19-50, declares no components) | | | redundant.py:238 reads `cpa.family` / `cpa.*` | UNDECLARED SLOT; `chialu/characterize.py:185` pins `"cpa.family": "parallel_prefix"` for the `sd_adder` kind, so the database exercises a variable the space never declares |
| (hybrid_signed_digit) | | | redundant.py:338 reads `cpa.family` | UNDECLARED SLOT |

shift_simd_spaces.py, approx_spaces.py, dsp_posit_spaces.py, checker_spaces.py:

| file:line | family.slot | domain | consumer | verdict |
|---|---|---|---|---|
| shift_simd_spaces.py:76 | masked_merged.rotator | D20 | none | IGNORED (`fam_shift_masked_merged` is fixed) |
| :95 / :96 | butterfly_network.prefix_popcount / .lrotc_rotator | D26 / D20 | none | IGNORED (`fam_shift_butterfly_network #(W)` only) |
| :135 | popcount_counter_tree.final_adder | D0 | none | IGNORED: `__init__.py:447-449` maps only `tree_shape` |
| :220 | partitioned_carry_chain.base_adder | D0 | subword.py:205 | OK |
| :221 | partitioned_carry_chain.saturation | D32 | none | IGNORED |
| approx_spaces.py:42 | segmented_carry_speculative.sub_adder | D0 | approx.py:76 | OK |
| :58 | lower_part_approximate.upper_adder | D0 | approx.py:142 | OK |
| :114 | dynamic_segment.core_multiplier | D0 (`cpa_space`) | approx.py:286: `m.mul(_pin(pins, "core_multiplier.family", "direct_pp_parallel"), ...)` | MISTYPED: declared over the adder space, consumed as a multiplier, default `direct_pp_parallel` not in D0 |
| :139 | logarithmic.log_adder | D0 | none | IGNORED |
| :176 | approximate_compressor_tree.cpa | D0 | approx.py (`cpa.` prefix) | OK by the pin, path mismatch per section 1 |
| dsp_posit_spaces.py:40, 41, 55, 98, 116, 117, 118 | the slots of dsp48_style_slice, variable_precision_dsp, multiprecision_block_proposal, embedded_fpu_block | D1 / D0 / D16 | none | NO GENERATOR: there is no `families/dsp.py`, and `dsp_block_space()` is not in `core_slots` |
| :149 / :150 | posit_adder_multiplier.sig_datapath / .sig_div | D0 / D21 | none in posit.py | posit.py reads no `*.family` pin; `LZC_FAMILY = "lzd_cell_tree"`, `SHIFTER_FAMILY = "barrel_mux_tree"` (posit.py:73-74, used at :158, 162, 245, 248, 281, 331, 333); the seed consumes `sig_datapath.*` in alu_float.py:95-107 and `sig_div.*` through `fp.div_sv` (section 1) |
| checker_spaces.py:115, 128, 141, 153, 178, 193, 207, 232, 266, 290 | `*.comparator` | D8 | alu_checker.py:200-212 `comparator_of`, common.py:192 | DOMAIN SMALLER THAN THE REALIZED SET: `COMPARATORS` (alu_checker.py:158) = direct_compare, two_rail_tree, m_out_of_n_checker, majority_voter; `direct_compare` is not a family of `two_rail_space()` and is the default |
| :193 | parity_prediction_adder.carry_replica | D0 | none | IGNORED |
| (rns_redundant :157, reduced_precision :297) | | | | no comparator slot at all, against the module docstring at checker_spaces.py:10-12 ("every family opens a comparator slot") |

### 4.3 Families to slots

Reachability was computed by walking every unit-level slot space
(`chialu/modules/alu.py:98-156` `core_slots`, `:159-181`
`core_families`, `chialu/modules/dot.py:76`, `chialu/modules/sfu.py:74`)
plus all component slots transitively. No realized family is
unreachable: every one of the 139 names is in at least one space and
reachable from at least one `core.*` variable.

| kind (`characterize.py:28-30`) | realized families | slots that admit them | unit variable |
|---|---|---|---|
| adder (18) | 15 exact (`cpa_space`) | 61 slot sites over D0 + 14 over D3 (D3 admits only 4 of the 15) | `core.adder` (exact / bcd) |
| | 3 approximate: segmented_carry_speculative, lower_part_approximate, accuracy_configurable | none | `core.adder` only under `accuracy: approximate` |
| multiplier (18) | 12 in `mul_space` | 32 slot sites over D1 (`mul`, `multiplier`, `sig_mul`, `iter_mult`, `prescaler`, `final_mul`, `binary_multiplier`) | `core.multiplier` |
| | twin_precision_subword | D1 sites, but `mul_module` returns None (`__init__.py:280`, documented at :111-112) | `core.multiplier` + the unit level (alu_seed.py:529) |
| | 6 approximate: dynamic_segment, operand_rounding, logarithmic, pp_perforation, approximate_compressor_tree, approximate_booth | none | `core.multiplier` only under approximate |
| divider (12) | 10 in `div_space` | 4 slot sites over D21: `sig_div`, `sig_sqrt` (fp_spaces.py:449, 458), `divider` (sfu_spaces.py:252), `sig_div` (dsp_posit_spaces.py:150) | `core.divider` |
| | 2 approximate: approximate_recurrence, approximate_functional | none | `core.divider` only under approximate |
| shifter (5) | all 5 | 7 sites over D16 (`shifter` x4, `antilog_shifter`) | `core.shifter` |
| bitcount (6) | popcount_counter_tree, lzd_cell_tree, trailing_zero, priority_encoder | 2 sites over D26 (`prefix_popcount`, ignored) | `core.bitcount` |
| | recursive_doubling_lzd, prefix_lzc | 3 sites over D23 (`encoder`, `counter`, `lz`) | none (no `core.lzc` kind) |
| comparator (1 + 15 adders) | prefix_comparator | the `comparator` pin in fp.py:622 (undeclared) | `core.comparator` |
| fp_adder (4) | single_path, two_path, delay_optimized_unified, low_power_gated | `core_add` (fp_spaces.py:406, ignored) | `core.fp_adder` |
| fp_multiplier (2) | | `core_mul` (:407, ignored) | `core.fp_multiplier` |
| fp_fma (4 + 1) | classic_fma, reduced_latency_fma, multipath_fma, bridge_fma (`fma_sv`; the bridge composes `mul_sv` and `add_sv` through dot.py `_bridge_sv`; one module serves fadd, fsub, fmul and the fused ops fmadd, fmsub, fnmsub, fnmadd under `fop`); separate_multiplier_and_adder has no module, since the fp_adder's and the fp_multiplier's own realize it (the fused ops under `fma_contract: sequential` through the two, the product rounded and read back between them) | none (D33 is the ALU's slot alone) | `core.fp_fma`; a fused family makes the mode's `core.fp_adder` and `core.fp_multiplier` variables inactive |
| fp_divider / fp_sqrt (2) | | `core_div` (:408, ignored) | `core.fp_divider` |
| fp_comparator (2) | | none | `core.fp_comparator` |
| rounder (3) / unpacker (3) | | none | `core.rounder`, `core.unpacker` |
| converter (2) | | none | `core.converter`, but the family is discarded (`__init__.py:357`) |
| logic (3) | lane_replicated_gates, wide_gate_row | none | `core.logic` |
| | alu_pg_fused | none | `core.logic`: `has_module` says True (:129), `logic_module` returns None (:471-473); the family is realized in the lane module's adder (alu_int.py) rather than as a library module |
| subword (2) | partitioned_carry_chain, replicated_lanes | none | `core.subword` (only when the mode set has several modes) |
| incrementer (1) | prefix_and_incrementer | `increment_stage` (adder_spaces.py:259), ignored | none: no `core.incrementer` kind, not in `KINDS` |
| bcd_adder (4) / bcd_multiplier (1) / bcd_divider (2) | | `significand_adder`, `multiplier`, `divider`, `multiplier_tree`, `significand_multiplier` (decimal_spaces.py:209, 248, 267, 358-360), no generator | `core.adder/multiplier/divider` under a BCD mode |
| posit_unit (2) | posit_adder_multiplier, posit_ieee_interop | none | `core.posit_unit` |
| dot core (18) | | none | `core.family` of `chialu.VecDotAcc` (chialu/modules/dot.py:76) |
| sfu core (25) | | `approximator` (div_spaces.py:314), which rejects 22 of them | `core.family` of `chialu.VecSFU` (chialu/modules/sfu.py:74) |
| representation (4) | generalized_signed_digit, hybrid_signed_digit, carry_save_datapath | none | `core.family = redundant_internal` then `core.representation` (alu.py:171) |
| | redundant_binary_multiplier | 1 site (mul_space via mul_spaces.py:345) | same; routed to `mul_module` at alu_int.py:271-291, `representation_adder_sv` raises (redundant.py:458-459) |
| channels (4) | | none | `core.family = rns_internal` then `core.channels` (alu.py:174) |

`rns_internal` (alu.py:174-176) opens only `channels` and drops every
structure slot, so under an RNS core no adder, multiplier, shifter or fp
family is selectable.

### 4.4 The `design_choices` enums against the variant cards

671 markdown files under `chialu/knowledge/arch/` before the deferral,
436 with `family:` and `pin:` front matter, parsed against the enum of
the family in that domain's space.

* Cards whose pin value is not in the enum: none (two cards under
  `carry_save_datapath/` quote the value `"3_2"`, cosmetic). Cards
  whose `pin:` key is not a choice of the family: none. Cards whose
  `family:` is not in the domain's space: none. Families without a
  card: none.
* Enum coverage: 429 of 1919 enum members (22%) have a card. 138 choices
  are carded in part; the largest gaps:

| domain | family | choice | carded / total | uncarded |
|---|---|---|---|---|
| adder | compound_flagged_prefix | topology | 1/7 | sklansky, brent_kung, ladner_fischer, han_carlson, knowles_mixed, harris |
| adder | carry_select | block_sizing | 1/5 | uniform, delay_balanced_dp, delay_matched_doubling, equal_power_sized |
| approx | approximate_recurrence | cell | 1/5 | exact, axsc1, axsc2, axsc3 |
| shift | butterfly_network | network | 1/4 | butterfly, inverse_butterfly, butterfly_two_inverse |
| shift | popcount_counter_tree | counter_primitive | 1/4 | compressor_4_2, counter_7_3, lut_rom |
| shift | funnel | input_forming | 1/4 | duplicate_for_rotate, sign_extend, zero_fill |
| redundant | rns_channel_arithmetic | modulus_form | 1/4 | pow2_minus_1, pow2, generic |
| redundant | redundant_decimal_conversion | borrow_network | 1/4 | digitwise_constant, ripple, carry_lookahead |
| approx | approximate_compressor_tree | error_recovery | 1/4 | none, or_based, compensation_module |
| approx | dynamic_segment | unbiasing | 1/4 | none, lsb_set_to_one, round_and_correct |
| approx | pp_perforation | correction | 1/4 | none, constant, probabilistic_compensation |
| adder | approximate_truncated | lower_scheme | 1/4 | or_gates, segmented_subadders, speculative_segments |
| adder | end_around_carry | topology | 3/7 | brent_kung, han_carlson, knowles_mixed, harris |
| mul | logarithmic_mitchell | correction_scheme | 1/4 | none, combet_error_terms, nearest_one_rounding |
| dot | multi_term_fused_dot | alignment_strategy | 4/6 | per_level, two_stage_coarse_fine |
| sfu | sigmoid_tanh_pwl | approximation | 4/6 | pwl_segments, step_sum |
| sfu | cordic | coordinate_set | 2/4 | linear, hyperbolic |
| dsp | posit_adder_multiplier | regime_decode | 1/2 | two_stage_masked_decode |
| fp | low_power_gated | lz_logic_style | 1/3 | full_lza, low_power_lzc |
| mul | approximate_compressor | technique | 2/4 | approximate_compressor, dynamic_segment |
| div | srt_high_radix | residual_form / quotient_conversion | 1/3 each | irredundant, carry_save / separate_positive_negative, on_the_fly |
| adder | prefix_comparator | structure | 3/5 | msdf_digit_serial_fsm, msdf_signed_digit_fsm |

* Choices of a carded family with zero cards and three or more members:
  96, among them `parallel_prefix.node_style / flag_outputs /
  zero_detect`, `parallel_prefix` and
  `prefix_synthesis_nonuniform_arrival.arrival_profile` (one of the few
  pins `__init__.py:191-198` consumes), `ling_prefix.propagated_function`,
  `prefix_comparator.function`, `prefix_and_incrementer.topology`,
  `booth_recoded_parallel.booth_radix` (the generator rejects 16 at
  mul.py:397-398), `truncated_fixed_width.output_rounding`,
  `twin_precision_subword.partition`, `srt_high_radix.radix`,
  `svoboda_tung.radix`, every pin of `generalized_signed_digit` (the
  pins `characterize.py:184-192` sweeps),
  `carry_save_datapath.assimilation_point`, `online_arithmetic_unit.radix`,
  `barrel_mux_tree.stage_radix`, `funnel.window_mux_radix`,
  `rns_forward_converter.final_reduction / modulus_class`,
  `mx_microscaling_dot.element_type`,
  `kulisch_long_accumulator.carry_resolution`, `piecewise_poly /
  single_poly / lut_plus_poly.coeff_encoding`,
  `redundant_high_radix_cordic.scale_handling`, `residue.modulus`,
  `berger.construction`, `m_out_of_n_checker.realization`.

The direction of the gap is uniform: the enums are never narrower than
the cards; the cards cover 22% of the declared choice space. This check
cannot show a choice missing from both (the banded far-path alignment of
the dot accumulators is such a case): that needs a per-slot review
against the literature.

### 4.5 The gaps, ranked by the design freedom lost

1. **`direct_polynomial.approximator`** is declared over
   `sfu_approx_space()` (25 families) and resolved against
   `SEED_FAMILIES` (7): div_spaces.py:314 opens the slot; div.py:758-760
   and :949-951 read `approximator.family` as a seed-table family and
   rewrite anything unrecognized to `poly_seed` / `monolithic_rom`
   without a note. The fix is to narrow the slot to `seed_table_space()`
   or to route it through `sfu.sfu_sv` the way
   `rational_approximation.divider` routes through `FAM.div_module`.
2. **The approximate families are a disjoint island**: no component slot
   reaches any of the 11 realized approximate families. `approx_adder_space`
   (3), `approx_mul_space` (6), `approx_div_space` (2) are only the
   top-level space of `core.adder / multiplier / divider` under
   `accuracy: approximate` (alu.py:109-116), while 32 `mul_space`, 61
   `cpa_space` and 4 `div_space` slot sites exist. An FMA's multiplier,
   a divider's `iter_mult` or an FP multiplier's `sig_mul` can never be
   `dynamic_segment` / `pp_perforation` / `approximate_booth` although
   `FAM.mul_module` builds them (`__init__.py:286-289`). The asymmetry is
   one-way: the approximate families do open `cpa_space` sub-slots.
3. **`lzc_space()` has 2 families, `lzc_module` realizes 4, and the
   generators' default is one of the 2 it excludes**: fp_spaces.py:18-36
   = {recursive_doubling_lzd, prefix_lzc}; `__init__.py:453-461`
   realizes lzd_cell_tree, recursive_doubling_lzd, prefix_lzc,
   priority_encoder; fp.py:237, :276, :804, div.py:173 and mul_ext.py:363
   default the pin to `lzd_cell_tree`, outside the declared domain. A
   binding of `...lza.encoder.family` to either legal value changes the
   RTL away from the built default and cannot express the default.
4. **`reduction.family` is never read by mul.py**: 2 of the 3
   `reduction_space()` families are unreachable through the multiplier's
   `reduction` slot (mul_spaces.py:132, 152, 305; mul.py:417-419 reads
   only geometry and counter_kind); `tiled_cpa_reduction_tree` and its
   `tile_adder` slot are dead in the whole library.
5. **The `converter` kind discards its declared family**:
   `__init__.py:357` `fp.round_sv(fmt, geom, family if kind == "rounder"
   else "dedicated_per_op", ...)`; `shift_round_convert` and
   `internal_format_datapath` produce the identical module, and their 7
   declared slots (`shift_unit`, `round`, `lz`, `core_add`, `core_mul`,
   `core_div`, `round`) are dead.
6. **The posit unit declares two slots and hard-codes what they would
   control**: dsp_posit_spaces.py:149-150 opens `sig_datapath: cpa_space()`
   and `sig_div: div_space()`; posit.py reads no `*.family` pin; its LZC
   and shifter are module constants. (The seed does consume `sig_datapath`
   for the significand adder, alu_float.py:95-107.)
7. **Undeclared slots the generators consume**: `generalized_signed_digit`
   and `hybrid_signed_digit` read `cpa.family` with no `components`
   (redundant.py:238, :338), and `characterize.py:185` sweeps
   `cpa.family` for the `sd_adder` kind, so the database characterizes an
   axis the planner never sees. Same class: mul_ext.py:202 `cross.family`,
   :363 `lod.family`, :472 `exact.family`, :643 `segment.family`;
   div.py:173 `norm.lzc.family`, :677 / :714 `mul.family`; fp.py:237
   `lzc.family`, :622 `comparator.family`, :758 `incrementer.family`;
   sfu.py:3664 `divider.family`. Eleven in total.
8. **`decimal_digit_recurrence.digit_select` and `decimal_newton.seed`**
   are declared and never read (decimal_spaces.py:169, :183); both
   families are realized, so the 2- and 7-way domains are inert.
9. **`has_module("logic", "alu_pg_fused")` is True while `logic_module`
   returns None** (`__init__.py:129`, :471-473): the family is realized
   inside the lane module (the and / xor / or as the adder's generate and
   propagate) rather than as a library module, so the `[library]` mark
   holds by construction but not by the mechanism the menu implies.
10. **`block_adder_space()` (4) is the domain of 7 slots whose helper
    accepts 15** (adder_spaces.py:209, 229, 258, 280, 374); the docstring
    at adder_spaces.py:9-11 justifies the narrowing by recursion
    termination, but `parallel_prefix` is already in the leaf set and opens
    nothing, so the narrowing costs 11 realized families at 7 sites.
11. **The `checker.comparator` slot's realized domain contains a value that
    is not a family**: `COMPARATORS` (alu_checker.py:158) has
    `direct_compare`, which `two_rail_space()` (checker_spaces.py:27-96)
    lacks, and it is the default; `common.py:150-203` builds `checker.*` by
    hand rather than from `checker_space().variables(...)`, so
    `rns_redundant` / `reduced_precision` open no comparator slot against
    the docstring at checker_spaces.py:10-12, and
    `parity_prediction_adder.carry_replica` (:193) is inert.
12. **`dynamic_segment.core_multiplier`** is declared over the adder space
    (approx_spaces.py:114) and consumed as a multiplier (approx.py:286)
    with a default outside the declared domain.
13. **Slots whose family is declared, read nowhere, and whose choices carry
    the behavior instead**: `*.align` on all 7 dot / FMA families (only
    `align.shifter.family` is read), `*.round` on the same 7 plus
    `fp_add_space`'s 5 (fp_spaces.py:234), `*.subnormal` on 9 sites
    (fp.py:281 reads only `subnormal.internal_representation`): 14 D2
    sites + 14 D4 sites + 9 D11 sites of dead family variables.
14. **Fully inert slots** (declared, no consumer, family realized):
    `hard_multiple_adder`, `region_adder`, `tile_adder`, `sum_block`,
    `increment_stage`, `compound_adder`, `comparator_adder`,
    `column_reducer`, `address_adder`, `final_adder` (ATA), `tail_evaluator`,
    `rotator`, `prefix_popcount`, `lrotc_rotator`, `final_adder` (popcount),
    `saturation`, `log_adder`, `carry_replica`: 17 slot names at about 25
    sites. `prefix_and_incrementer` is the one realized family whose only
    route into the space is one of these (`increment_stage`); it has no
    `core.<kind>` variable and is absent from `characterize.KINDS`, so it is
    realized, used by fp.py:758 and adder_ext.py:291, and unreachable by any
    binding.
15. **Whole spaces with no generator and no unit slot**: `dsp_block_space()`
    (dsp_posit_spaces.py:21-128) and `decimal_misc_space()`
    (decimal_spaces.py:193-365); `online_space()` is reachable (alu.py:177-179)
    and realizes nothing. Nothing in the code distinguishes them from the
    realizable spaces except the missing `[library]` tag (prompts.py:153).
16. **`fam_fp_add_*` and `fam_fp_mul_*` module names omit their slot
    families** (fp.py:265, :510), against fp.py:828 / :876 / :670, which embed
    the component family. Two structures of the same family with different
    `align` / `sig_adder` / `near_lz` pins render two texts under one name
    and `dedupe_modules` (mul.py:495-505) keeps the first: a wrong-RTL
    path unless the seed passes a distinct `name`.
17. **`SHIFTER_LIBRARY_MAX = 128`** (dot.py:100, :111-117) replaces a
    declared shifter family with behavioral text on the wide accumulator
    frames, which are the geometries where the choice matters most; the
    substitution is recorded in the module comment.
18. **Choice-level narrowing inside otherwise OK slots**: mul.py:397-398
    rejects `booth_radix: 16`; mul.py:319-321 swallows `geometry:
    reduced_area / tdm_arrival_driven` and `counter_kind: 5_2 / 7_3`;
    `__init__.py:231-232` uses only `group_size` and `intergroup_carry` of
    `carry_lookahead`'s 5 choices; `__init__.py:254-255` hard-codes `B=4`
    for `carry_select` and ignores `block_sizing` / `select_source`;
    `__init__.py:262-263` ignores `sparse_prefix_hybrid.tree_topology` and
    `.valency`; sfu.py:1202-1203 replaces `coefficient_adapted` outside
    degrees 3 to 4 (and `fma_based` always) by Horner; `comparator_module`
    (`__init__.py:438-440`) returns None for `structure` in
    {msdf_digit_serial_fsm, msdf_signed_digit_fsm}.
