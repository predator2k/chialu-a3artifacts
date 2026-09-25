---
handle: jiang2017
citation: H. Jiang, C. Liu, L. Liu, F. Lombardi, J. Han, "A Review, Classification, and Comparative Evaluation of Approximate Arithmetic Circuits", ACM Journal on Emerging Technologies in Computing Systems, vol. 13, no. 4, 2017
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [int16, uint16, int32]
authority: survey
pages_read: 34 / 34
---

## summary
The survey classifies approximate adders/multipliers/dividers by where approximation enters their datapaths and compares error/delay/power/area using simulation and STM CMOS 28 nm synthesis (pp.2–3, 7–30). Image-sharpening implementations save up to 53% power and 58% area, while selected approximate dividers improve change detection delay by 40% at similar image quality (pp.28–30).

## families
### segmented_carry_speculative  (role: compares)
mechanism: ACA predicts each sum-bit carry from k lower bits; ESA fixes carry inputs between parallel k-bit subadders; ETAII propagates a generated carry into the next sum generator; overlapping ACAA subadders select their upper halves. SCSA/CCA duplicate carry-0/carry-1 paths, CSA/GCSA choose carries from block propagate/generate signals, CSPA uses l<k predictor bits, and CCBA cuts propagation through a controlled mux or OR gate (pp.3–6).
choices:
  carry_in_scheme: [constant_zero, propagate_window, carry_select_speculation, carry_cut_back] [outside domain]   # pp.3–6
  correction: [none, error_reduction_stage] [outside domain]   # pp.5–6
new_choices:
  overlap_width: k bits — overlap between adjacent 2k-bit ACAA subadders   # p.4
slots:
  sub_adder: carry_lookahead   # p.8
parameters: 16-bit evaluation; k=3–8 across configurations; equivalent-chain comparison uses k=4 for CSA/GCSA/ETAII/ACAA/SCSA/CCA/CSPA and k=8 for ACA/ESA   # pp.7, 9, 12
results:
| metric | value | unit | technology / device | baseline | condition | page |
| delay complexity | O(log(k)) | — | STM CMOS 28-nm; 2017 | conventional adder | speculative/segmented/carry-select classes | pp.4–6 |
errors_and_checks: ER/MED/NMED/MRED/average error are estimated from 10 million uniformly distributed inputs; ETAII/ACAA/SCSA have identical error characteristics for equal k, while CSA is most accurate among equivalent designs (pp.7–8).
conditions: Carry-select designs tend to require more power/area; segmented designs tend to save power/area; carry-prediction quality controls the error tradeoff (pp.9–12).
evidence: §2.1.1–§2.2.3; Figures 3–6 and 8–10; Tables I–II (pp.4–12).

### lower_part_approximate  (role: compares)
mechanism: LOA replaces low-order sum logic with OR gates and uses one AND gate to transfer a carry into the accurate upper part. AMA and AXA designs replace low-order full adders with approximate cells; a truncated adder supplies the lower-precision baseline (p.6).
choices:
  lower_cell: or_gate   # p.6
  carry_to_upper: msb_and   # p.6
new_choices: none
slots:
  upper_adder: carry_lookahead   # p.8
parameters: 16-bit adders; LOA lower width k=3–9 in the comparison and k=8 for the equivalent-chain comparison; LOA-16 is used in the 32-bit image-sharpening adder   # pp.7, 9, 12, 26
results:
| metric | value | unit | technology / device | baseline | condition | page |
| image-sharpening PSNR | 46.97 | dB | STM CMOS 28 nm; 2017 | accurate image | LOA-16 with TAM1-16 | p.28 |
errors_and_checks: LOA has a large ER but small MRED and the lowest average error because positive/negative errors partly cancel (pp.7–8).
conditions: LOA is power/area efficient and is suitable for accumulation when low average bias matters, but its approximate low bits produce a high ER (pp.7–12).
evidence: §2.1.4–§2.2.3 and §5.1; Figure 7; Tables I–II and VIII–IX (pp.6–12, 26–28).

### accuracy_configurable  (role: instantiates)
mechanism: ACAA uses overlapping 2k-bit subadders and selects k upper sum bits from each block. GDA selects accurate or approximate block carry inputs through runtime-controlled multiplexers; multistage compensation can repair prediction errors at added latency (pp.4–6).
choices:
  reconfig_grain: subadder_select   # pp.4, 6
  error_detection: false   # pp.4, 6
new_choices:
  compensation_latency: multistage — carry-prediction errors are compensated in more-significant segments   # p.5
slots: none
parameters: ACAA uses floor(n/k−1) overlapping 2k-bit subadders; accuracy is runtime configurable   # p.4
results:
| metric | value | unit | technology / device | baseline | condition | page |
| delay complexity | O(log(k)) | — | STM CMOS 28-nm; 2017 | accurate adder | ACAA parallel subadders | p.4 |
errors_and_checks: ACAA has the same ER/NMED/MRED as ETAII/SCSA for equal k (pp.7–9).
conditions: ACAA reduces logical depth but has a long synthesized critical path; compensation improves accuracy by trading computing efficiency for latency (pp.5, 9).
evidence: §2.1.2–§2.1.3 and §2.2; Figures 5–6; Tables I–II (pp.4–12).

### pp_perforation  (role: compares)
mechanism: UDM alters one truth-table entry of a 2×2 multiplier and composes larger multipliers from that cell while retaining an accurate reduction tree. BAM removes carry-save cells along horizontal/vertical boundaries of an array multiplier (pp.14–15).
choices:
  cell: kulkarni_2x2_inaccurate   # p.14
  correction: none   # pp.14–15
new_choices:
  vertical_broken_length: integer — number of vertically omitted array cells   # pp.15, 19
  horizontal_broken_length: integer — number of horizontally omitted array cells   # p.15
slots: none
parameters: UDM 2×2 primitive; evaluated multipliers are 16×16; BAM configurations truncate 13–21 bits in the PDP/MRED comparison   # pp.14, 18, 23
results:
| metric | value | unit | technology / device | baseline | condition | page |
| primitive error rate | 1/16 | — | UNKNOWN; 2017 | exact 2×2 multiplier | UDM cell, uniform input bits | p.14 |
errors_and_checks: UDM has relatively low ER but large NMED/MRED; BAM has moderate NMED/MRED for the equivalent configuration (pp.18–20).
conditions: BAM saves power through truncation but retains the slower array structure; UDM retains accurate accumulation and therefore has high circuit overhead (pp.21–24).
evidence: §3.1.1–§3.1.2 and §3.2; Figures 13, 18–20; Tables III and V–VI (pp.14–24).

### truncated_fixed_width  (role: compares)
mechanism: TruM truncates operand LSBs; BAM/ETM/TAM variants omit low partial-product work; fixed-width Booth designs truncate the lower product half and estimate its carry using constants/Booth signals/probability/sorting networks (pp.14–18).
choices:
  correction: [none, constant, data_dependent, variable_stat] [outside domain]   # pp.17–18
  target: multiplier   # pp.14–18
new_choices:
  truncation_location: {operand_lsb, partial_product_columns, array_cells} — location where low-order work is discarded   # pp.14–18
slots: none
parameters: 16×16 evaluation; equivalent configurations retain 16 accurate product MSBs; Booth fixed-width output equals operand width   # pp.17–20
results:
| metric | value | unit | technology / device | baseline | condition | page |
| image-sharpening PSNR | 46.97 | dB | STM CMOS 28 nm; 2017 | accurate image | TAM1-16 with LOA-16/CSA-8/ETAII-8 | p.28 |
errors_and_checks: Truncation-based multipliers usually have ER near 100%; MRED can grow when inputs are small even if NMED changes little (pp.18–22).
conditions: Truncation substantially reduces power/area when input magnitudes make discarded bits tolerable; otherwise the error can be unacceptable (p.22).
evidence: §3.1.2, §3.1.4, §3.2 and §5.1; Tables V–IX (pp.14–28).

### approximate_compressor_tree  (role: compares)
mechanism: ICM changes one 4:2 counter case; ACM uses inexact 4:2 compressors; AM1/AM2 use carry-free approximate adders and configurable error-accumulation stages, with TAM variants additionally truncating low columns (pp.15–17).
choices:
  compressor: momeni_d1_d2   # p.16
  error_recovery: [none, or_based, configurable_recovery] [outside domain]   # pp.16–17
  dual_quality_runtime: false   # pp.15–17
new_choices: none
slots:
  cpa: UNKNOWN   # p.20
parameters: 16×16 multipliers; 10 million uniformly distributed input pairs; ACM modes 3/4 and AM/TAM recovery widths are compared   # pp.18–20
results:
| metric | value | unit | technology / device | baseline | condition | page |
| ICM error rate | 5.45% | — | UNKNOWN; 2017 | exact multiplier | one approximate counter in a 4×4 submultiplier | p.18 |
errors_and_checks: Approximate-counter/compressor multipliers generally have small NMED/MRED, while ACM produces positive/negative errors and therefore a small average error (pp.18–20).
conditions: Counter/compressor approximation improves accuracy relative to many truncation schemes but generally requires more power/area (pp.22–24).
evidence: §3.1.3 and §3.2; Figures 16 and 18–20; Tables IV–VI (pp.15–24).

### approximate_booth  (role: compares)
mechanism: Fixed-width radix-4 designs truncate partial-product columns and estimate the discarded carry; BBM omits array cells without compensation. ABM2 uses an approximate recoding adder for radix-8 hard multiples plus Wallace reduction/truncation, while newer radix-4 designs simplify Booth-encoder K-maps (pp.17–18).
choices:
  radix: [4, 8] [outside domain]   # pp.17–18
  encoder: [exact, truncated_hard_multiple, abe1, abe2] [outside domain]   # pp.17–18
new_choices:
  compensation_estimator: {booth_zero_signals, binary_threshold, sorting_network, probabilistic_bias, none} — method estimating discarded-column carry/error   # pp.17–18
slots: none
parameters: 16×16 signed evaluation; fixed-width output; ABM2/BBM truncate 15 partial-product columns   # pp.18–19
results:
| metric | value | unit | technology / device | baseline | condition | page |
| error rate | close to 100% | — | STM CMOS 28 nm; 2017 | accurate Booth multiplier | evaluated approximate Booth multipliers with truncation | p.19 |
errors_and_checks: BM07/BM11 have small MRED; BM11 has the lowest average error; BBM has the largest NMED/MRED because it lacks compensation (pp.19–20).
conditions: ABM2 has the lowest PDP but moderate accuracy; BM07/BM11 improve MRED at higher PDP; PEBM has moderate PDP/MRED (pp.23–24).
evidence: §3.1.4 and §3.2; Figures 17 and 21; Tables V–VI (pp.17–24).

### approximate_recurrence  (role: compares)
mechanism: AXDnr/AXDr replace low-significance cells of unsigned nonrestoring/restoring divider arrays with simplified subtractor cells or discard those cells. DAXD detects leading ones, selects fixed-width operand windows, and uses a smaller exact array divider plus multiplexers/barrel shifting (pp.24–25).
choices:
  cell: [axsc1, axsc2, axsc3] [outside domain]   # pp.24, 29
  radix: 2   # pp.24–25
  adaptive_pruning: true   # pp.24–25
new_choices:
  replacement_shape: {vertical, horizontal, square, triangle} — region of array cells replaced by approximate subtractors   # p.24
slots: none
parameters: unsigned n/(2n); change detection uses 16/8 division, triangle depth 8, and DAXD10 uses a 10/5 exact subdivider   # pp.25, 28–29
results:
| metric | value | unit | technology / device | baseline | condition | page |
| PSNR | 40.46 | dB | STM CMOS 28 nm; 2017 | ArrayD | AXDr1 change detection | p.30 |
| delay | 3.85 | ns | STM CMOS 28 nm; 2017 | ArrayD 4.08 ns | AXDr1 | p.30 |
| power | 50.71 | uW | STM CMOS 28 nm; 2017 | ArrayD 54.29 uW | AXDr1 | p.30 |
| area | 415.5 | um2 | STM CMOS 28 nm; 2017 | ArrayD 425.8 um2 | AXDr1 | p.30 |
| PSNR | 41.71 | dB | STM CMOS 28 nm; 2017 | ArrayD | AXDr3 change detection | p.30 |
| delay | 4.58 | ns | STM CMOS 28 nm; 2017 | ArrayD 4.08 ns | AXDr3 | p.30 |
| power | 40.55 | uW | STM CMOS 28 nm; 2017 | ArrayD 54.29 uW | AXDr3 | p.30 |
| area | 376.2 | um2 | STM CMOS 28 nm; 2017 | ArrayD 425.8 um2 | AXDr3 | p.30 |
| PDP | 97.84 | fJ | STM CMOS 28 nm; 2017 | ArrayD 221.50 fJ | DAXD10 | p.30 |
| ADP | 912.9 | um2 .ns | STM CMOS 28 nm; 2017 | ArrayD 1,737.2 um2 .ns | DAXD10 | p.30 |
errors_and_checks: Accuracy varies with replacement depth/cell or DAXD subdivider width; no runtime error detection is reported (pp.24–25, 29–30).
conditions: Array approaches use less power/area but retain O(n2) borrow propagation; DAXD shortens the path by using a smaller exact divider (pp.25, 30).
evidence: §4.1.1, §4.2 and §5.2; Figure 23; Table X (pp.24–25, 28–30).

### approximate_functional  (role: compares)
mechanism: HSD approximates logarithmic division with LUTs/multipliers; FPD linearly fits quotient surfaces by square/triangular regions. SEERAD rounds the divisor to 2^(K+L/D), converts division to shift/add multiplication, and selects L/D from relevant divisor bits for multiple accuracy levels (p.25).
choices:
  method: [log_subtract_corrected, divisor_round_pow2_lut] [outside domain]   # p.25
  runtime_quality_scaling: true   # p.25
new_choices:
  curve_region_shape: {square, triangular} — quotient-surface partition used by FPD   # p.25
slots: none
parameters: 16/16 HSD/FPD error discussion; 16/8 SEERAD change detection; four SEERAD accuracy levels   # pp.25, 29
results:
| metric | value | unit | technology / device | baseline | condition | page |
| maximum relative error distance | 0.20% | — | UNKNOWN; 2017 | exact division | 16/16 HSD | p.25 |
| maximum relative error distance | 0.14% | — | UNKNOWN; 2017 | exact division | 16/16 FPD | p.25 |
| maximum relative error distance | 6.25% | — | UNKNOWN; 2017 | exact division | highest-accuracy 16/16 SEERAD | p.25 |
| PSNR | 36.61 | dB | STM CMOS 28 nm; 2017 | ArrayD | SEERAD4 change detection | p.30 |
| delay | 2.43 | ns | STM CMOS 28 nm; 2017 | ArrayD 4.08 ns | SEERAD4 | p.30 |
| power | 70.62 | uW | STM CMOS 28 nm; 2017 | ArrayD 54.29 uW | SEERAD4 | p.30 |
| PDP | 181.33 | fJ | STM CMOS 28 nm; 2017 | ArrayD 221.50 fJ | SEERAD4 | p.30 |
| area | 765.4 | um2 | STM CMOS 28 nm; 2017 | ArrayD 425.8 um2 | SEERAD4 | p.30 |
errors_and_checks: HSD/FPD report maximum relative error; SEERAD exposes four accuracy levels but no detection/correction mechanism (pp.25, 29).
conditions: Curve-fitting designs are accurate/fast but LUT-heavy; SEERAD is faster but has lower accuracy and higher area/power than array approximations (pp.25, 30).
evidence: §4.1.2–§4.2 and §5.2; Figure 23; Table X (pp.25, 29–30).

### error_analysis_quality  (role: analyzes)
mechanism: The evaluation computes ED=|M′−M|, RED=ED/M, MED, ER, NMED, MRED, and average signed error. MATLAB Monte Carlo simulation uses 10 million uniformly distributed input combinations, while synthesis measures delay/area/power/PDP/ADP under common conditions (pp.2, 7–8, 18, 20).
choices:
  metric: [er, med, nmed, mred] [outside domain]   # pp.2, 7
  model: monte_carlo   # pp.2, 7, 18
  composition_across_blocks: false   # pp.7, 18
new_choices:
  average_error: mean(M′−M) — signed bias metric for accumulative operations   # pp.2, 7
slots: none
parameters: 10 million random inputs; 16-bit adders; 16×16 multipliers; STM CMOS 28-nm, 1.0 V, 25°C; power periods 1ns for adders and 4ns for multipliers   # pp.7–8, 18, 20
results:
| metric | value | unit | technology / device | baseline | condition | page |
| delay improvement | 23% | — | STM CMOS 28 nm; 2017 | accurate image-sharpening circuit | selected approximate adder/multiplier pairs | p.28 |
| power saving | 53% | — | STM CMOS 28 nm; 2017 | accurate image-sharpening circuit | selected approximate adder/multiplier pairs | p.28 |
| area saving | 58% | — | STM CMOS 28 nm; 2017 | accurate image-sharpening circuit | selected approximate adder/multiplier pairs | p.28 |
| PDP saving | 64% | — | STM CMOS 28 nm; 2017 | accurate image-sharpening circuit | selected approximate adder/multiplier pairs | p.28 |
| ADP saving | 62% | — | STM CMOS 28 nm; 2017 | accurate image-sharpening circuit | selected approximate adder/multiplier pairs | p.28 |
errors_and_checks: The metrics quantify output error rather than hardware-fault coverage; no false-alarm/alias analysis is performed (pp.2, 7).
conditions: ER alone does not quantify magnitude, NMED/MRED can rank designs differently, and signed average error matters for accumulated bias (pp.7, 18).
evidence: §1, §2.2, §3.2, §5 and §6; Tables I–II and V–X (pp.2, 7–12, 18–30).

## new_families
none

## space_gaps
* Survey evidence requires multi-valued choice observations for a compared family, while current choice domains represent one instantiated design value (pp.3–25).
* `average_error` is absent from `error_analysis_quality.metric` despite being used to measure signed output bias (pp.2, 7).
* `approximate_recurrence.cell` lacks AXCS1/AXCS2/AXCS3, and the family lacks the vertical/horizontal/square/triangle replacement-region choice (p.24).
* `truncated_fixed_width` lacks a choice distinguishing operand truncation, partial-product-column truncation, and omitted array cells (pp.14–18).
* `approximate_functional` lacks quotient-surface linear curve fitting with square/triangular regions (p.25).

## open_questions
* Tables I, II, V, VI, and IX contain rasterized numeric cells that are not recoverable from the supplied plain text, so their per-design values must not be guessed.
* The library’s unspecified final multiplier adder cannot be mapped to a vocabulary family (p.20).
* The paper calls SCSA/CSA/CSPA/CCA/GCSA “carry select adders,” but these approximate prediction structures are distinct from the registry’s exact `carry_select` family (pp.5–6).
