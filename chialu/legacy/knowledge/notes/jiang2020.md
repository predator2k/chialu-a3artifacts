---
handle: jiang2020
citation: H. Jiang, F. J. H. Santiago, H. Mo, L. Liu, J. Han, "Approximate Arithmetic Circuits: A Survey, Characterization, and Recent Applications", Proceedings of the IEEE, vol. 108, no. 12, pp. 2108-2135, 2020
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU, VEC_DOT_ACC]
formats: [uint16, int16, uint16/uint8]
authority: survey
pages_read: 28 / 28
---

## summary
The survey classifies and evaluates approximate adders/multipliers/dividers using error simulation, ST 28-nm CMOS synthesis, image processing, and an MTCNN. The comparisons show that error magnitude/bias and application structure matter alongside delay/power/area. Accumulative computations tolerate more multiplier approximation than adder approximation because single-sided addition errors accumulate.

## families
### segmented_carry_speculative  (role: compares)
mechanism: Speculative adders predict each carry from only the previous k bits. Segmented adders divide an n-bit addition into parallel subadders with independent, predicted, or selected carry inputs; overlapping input windows and variable-width segments trade hardware for accuracy. Carry-select variants compute alternative sums/carries and select one using propagate/generate signals or a short predictor. # pp.5-7
choices:
  sub_adder_width: 3 to 8 bits in evaluated configurations # p.8
  prediction_window: 2 to 8 bits in evaluated configurations # p.8
  carry_in_scheme: constant_zero; propagate_window; carry_select_speculation; carry_cut_back # pp.5-7
  correction: none; error_reduction_stage # pp.5-7
new_choices:
  segment_overlap: none or overlapping bits — controls carry-prediction inputs shared by neighboring segments # p.5
slots:
  sub_adder: carry_lookahead # p.7
parameters: 16-bit adders; critical path O(log(k)); ten million uniformly distributed input combinations # pp.5-8
results:
| metric | value | unit | technology / device | baseline | condition | page |
| ER | 0.5% to 35% | probability | UNKNOWN / 2020 | accurate adder | most evaluated configurations | p.7 |
| ER | <0.5% | probability | UNKNOWN / 2020 | accurate adder | GeAr R4_P8 and CSA with k > 3 | p.7 |
errors_and_checks: ER/MRED/NMED are evaluated; carry omission commonly produces single-sided errors and large error bias. # pp.4,23
conditions: CSA suits high-accuracy use, while ESA is hardware-efficient when high error is tolerated. Speculative ACA has high power and error magnitude. # pp.7-9
evidence: §III-B-C; Figs. 1-8; Table 1 # pp.5-9

### lower_part_approximate  (role: compares)
mechanism: An accurate upper adder processes the MSBs while approximate full-adder cells process l LSBs. LOA replaces each lower cell with an OR gate and supplies the upper adder from an AND-generated carry; TruA discards lower precision. # p.7
choices:
  lower_width: 4 or 8 bits among reported LOA configurations [outside domain for 3, 7, and 9 bits] # pp.18-20
  lower_cell: or_gate; truncate_constant # p.7
  carry_to_upper: msb_and; none # p.7
slots:
  upper_adder: carry_lookahead # pp.7,18
parameters: 16-bit adders; 3 to 9 approximate/truncated LSBs in circuit evaluation # p.8
results:
| metric | value | unit | technology / device | baseline | condition | page |
| PDP reduction | 69% | percent | ST 28-nm CMOS / 2020 | accurate image-sharpening implementation | LOA-9 with ALM-SOA; PSNR 30 to 35 dB | p.20 |
errors_and_checks: LOA/TruA have high ER, low MRED, and biased errors; TruA ER is close to 100%. # pp.7,23
conditions: LOA/TruA provide strong PDP-MRED tradeoffs when frequent small errors are acceptable, but biased addition errors degrade cascaded matrix computations. # pp.7,21,23
evidence: §III-B4-C; Table 1; §VI-A-B # pp.7-9,18-23

### accuracy_configurable  (role: analyzes)
mechanism: ACAA changes subadder width at runtime; GeAr varies the number of overlapped carry-prediction bits; GDA selects accurate or approximate carries by control signals; dual-quality compressors switch exact/approximate multiplier modes using power gating. # pp.5-6,11
choices:
  reconfig_grain: subadder_select; carry_chain_switch # pp.5-6
  error_detection: true # p.6
  power_gate_unused: true # p.11
new_choices:
  overlap_width: runtime-selected prediction-window width — changes accuracy and hardware activation # p.5
slots:
  none
parameters: GeAr configurations R4_P8, R6_P4, R4_P4, and R2_P4 # p.8
results: none
errors_and_checks: Accuracy is configured through carry reach or exact/approximate compressor selection; no universal error bound is reported. # pp.5-6,11
conditions: GDA delay varies with the control-selected carry path. # p.6
evidence: §III-B2-B3; §IV-B3 # pp.5-6,11

### pp_perforation  (role: compares)
mechanism: BAM removes carry-save cells across horizontal/vertical regions of an array multiplier. PPAM omits consecutive partial-product rows that need not begin at the LSB. Truncated multipliers instead discard operand LSBs. # p.10
choices:
  perforated_rows: 0 to 8 # pp.10-12
  cell: exact_and # p.10
  correction: none # p.10
new_choices:
  perforation_geometry: horizontal_vertical_region or consecutive_rows — identifies which PP hardware is omitted # p.10
slots:
  none
parameters: 16 × 16 unsigned multipliers; BAM configurations omit 11 to 22 LSB-side positions # p.12
results: none
errors_and_checks: Most evaluated approximate multipliers have ER close to 100%; truncation preserves variable MRED/NMED according to the removed width. # pp.11,23
conditions: PPAM has the shortest delay at large error; BAM has low power at medium accuracy. # pp.12-13
evidence: §IV-B2-C; Figs. 11-13; Table 2 # pp.10-13

### dynamic_segment  (role: compares)
mechanism: DRUM selects k operand bits beginning at each leading “1,” sets the selected LSB to “1” when lower bits are discarded, multiplies the two k-bit segments exactly, and restores scale with a barrel shifter. ETM/SSM use static operand partitions. # p.10
choices:
  segment_width: 6 to 10 bits # p.12
  segment_select: static_msb_or_lsb; dynamic_leading_one # pp.10,12
  unbiasing: lsb_set_to_one # p.10
  runtime_width_scaling: true # p.10
slots:
  core_multiplier: behavioral_star # p.10
parameters: 16 × 16 inputs; exact 6 × 6 to 10 × 10 DRUM core # p.12
results: none
errors_and_checks: DRUM produces unbiased errors and is more accurate than ETM/SSM because its selected bits follow the leading “1.” # p.10
conditions: Unbiased errors suit accumulative operations, but leading-one detection/multiplexing/barrel shifting increase complexity. # p.10
evidence: §IV-B2-C; Figs. 11-13 # pp.10-13

### logarithmic  (role: compares)
mechanism: Mitchell multiplication represents each operand as 2^k(1+x), approximates log2(1+x) by x, adds logarithms, and applies a piecewise antilogarithm. Later designs add segment correction, iterative residual correction, truncated converters, or exact/approximate mantissa adders. # pp.11-12
choices:
  base: mitchell # p.11
  correction: none; piecewise_terms; iterative_residual # pp.11-12
  iterations: 1 to 2 # pp.11-12
  mantissa_adder: exact; truncated; set_one_soa # p.11
slots:
  log_adder: approximate_truncated # p.11
parameters: 16 × 16 unsigned multiplication; ALM-SOA, ILM-EA, ILM-AA, and two-stage corrected variants # pp.11-12
results:
| metric | value | unit | technology / device | baseline | condition | page |
| PDP reduction | 69% | percent | ST 28-nm CMOS / 2020 | accurate image-sharpening implementation | ALM-SOA with LOA-9; PSNR 30 to 35 dB | p.20 |
errors_and_checks: Basic logarithmic designs have low accuracy; two-stage correction can produce low, unbiased average error. # pp.11-12
conditions: Logarithmic designs offer high speed/low power at low accuracy; ALM-SOA/TAM1 provide useful application-level energy tradeoffs. # pp.12-13,20
evidence: §IV-B4-C; Figs. 11-13; Table 2 # pp.11-13

### approximate_compressor_tree  (role: compares)
mechanism: Approximate counters/adders/4:2 compressors simplify partial-product reduction. Encoded propagate/generate inputs reduce compressor error probability; HOCM assigns one compressor per column and mixes exact/approximate stages with lower-half truncation. # pp.10-11
choices:
  error_recovery: none; or_based; configurable_recovery # pp.10-11
  dual_quality_runtime: true # p.11
slots:
  cpa: carry_lookahead # p.9
parameters: 16 × 16 multipliers; HOCM 1StepFull, 1StepTrunc, 2StepFull, and 2StepTrunc # p.12
results:
| metric | value | unit | technology / device | baseline | condition | page |
| counter ER | 0.39% | probability | UNKNOWN / 2020 | exact 4:2 counter | all four PP inputs equal 1 | p.10 |
| ICM ER | 5.45% | probability | UNKNOWN / 2020 | exact multiplier | 16 × 16 constructed from inaccurate-counter 4 × 4 blocks | p.11 |
errors_and_checks: Approximate compressors introduce deterministic arithmetic errors; configurable recovery accumulates error bits with OR gates/adders. # pp.10-11
conditions: HOCM 1StepTrunc gives the reported best power-accuracy tradeoff; 1StepFull is on the delay-optimized PDP/MRED frontier. # pp.12-13
evidence: §IV-B3-C; Figs. 11-13; Table 2 # pp.10-13

### truncated_fixed_width  (role: compares)
mechanism: Fixed-width Booth multipliers discard the lower half of radix-4 partial products and estimate the omitted contribution using Booth-encoder outputs, sorting networks, multiplicand bits, adaptive retained columns, or probability-derived bias. # pp.13-14
choices:
  kept_guard_columns: 0 to 8 # pp.13-14
  correction: none; data_dependent; variable_stat # pp.13-14
  target: multiplier # p.13
slots:
  none
parameters: 16 × 16 signed input; 16-bit output; radix-4 BM04/BM07/BM11/BM15/PEBM and radix-8 ABM2 # pp.13-15
results: none
errors_and_checks: BM11 makes truncation errors symmetric around zero, reducing bias/MSE; PEBM derives compensation from probability analysis. # p.14
conditions: BM07/BM11 are accurate but slow; PEBM balances PDP/accuracy; ABM2 offers moderate accuracy with high speed/power efficiency. # pp.14-15
evidence: §IV-D-E; Figs. 14-17; Table 3 # pp.13-15

### approximate_recurrence  (role: compares)
mechanism: AXDr replaces exact subtractor cells in vertical/horizontal/square/triangle regions of restoring arrays. High-radix variants use inexact signed-digit addition with replacement, truncation, and compensation. # p.16
choices:
  replaced_depth: 8 to 11 # p.17
  cell: axsc1; axsc2; axsc3 # pp.16-17
  radix: 2; 4 [high-radix designs also discussed] # p.16
  adaptive_pruning: false # p.16
new_choices:
  replacement_region: vertical, horizontal, square, or triangle — locates approximate cells in the array # p.16
slots:
  none
parameters: 16/8 unsigned integer division; exhaustive valid-input simulation # p.17
results: none
errors_and_checks: Accuracy varies with cell type/replacement depth; AXDr1/AXDr3 can be accurate but slow. # pp.17-18
conditions: Triangle replacement gives the selected tradeoff; cell-replacement dividers consume more delay/energy than adaptive or functional designs. # pp.17-18
evidence: §V-B1-C; Figs. 19-20; Table 4 # pp.16-18

### approximate_functional  (role: compares)
mechanism: SEERAD rounds the divisor to 2^(K+L)/D and replaces division with multiplication/shifting/table lookup. INZeD subtracts approximate binary logarithms and applies a corrected antilogarithm. DAXD/AAXD prune operands around leading “1” positions and use a reduced-width exact restoring divider; AAXD adds error correction. # pp.16-17
choices:
  method: divisor_round_pow2_lut; dynamic_segment_exact_core; log_subtract_corrected # pp.16-17
  segment_or_lut_width: 3 to 12 # p.17
  bias_correction: true # p.16
  runtime_quality_scaling: true # pp.16-17
new_choices:
  reduced_divider_width: 8, 10, or 12 dividend bits — controls pruning quality/hardware # p.17
slots:
  none
parameters: 16/8 unsigned division; SEERAD levels 1 to 4; INZeD truncates 0, 2, 3, or 4 subtractor LSBs # p.17
results: none
errors_and_checks: INZeD targets near-zero error bias; AAXD correction limits maximum ED. # p.16
conditions: AAXD serves high-accuracy/high-performance cases; INZeD has the best moderate-accuracy efficiency; SEERAD-1 serves high-error-tolerance cases. # pp.17-18
evidence: §V-B2-B4-C; Figs. 19-20; Table 4 # pp.16-18

### error_analysis_quality  (role: analyzes)
mechanism: The survey evaluates approximate circuits through exhaustive or Monte Carlo comparison against accurate results. It defines ER, ED, RED, MED, MRED, NMED, MSE, RMSE, average error/error bias, normalized average error, and normalized worst-case error. # p.4
choices:
  metric: er; med; nmed; mred; wce # p.4
  model: exhaustive_sim; monte_carlo # pp.4,7,17
  composition_across_blocks: true # pp.18-24
new_choices:
  error_bias: mean signed value of M′−M — measures whether errors accumulate in one direction # p.4
slots:
  none
parameters: ten million random inputs for adders/multipliers; exhaustive valid inputs for 16/8 dividers # pp.7,17
results: none
errors_and_checks: Circuit metrics are delay/power/area/PDP/ADP/EDP; synthesis uses Synopsys DC 2011.09 and PrimeTime-PX, ST 28-nm CMOS, 1.0 V, and 25 °C. # p.4
conditions: A fair comparison requires identical process/library/voltage/temperature/optimization settings. MRED/error bias better predict accumulative-application quality than ER alone. # pp.4,23-24
evidence: §II-B; §VII # pp.4,23-24

## new_families
none

## space_gaps
* `error_analysis_quality.metric` lacks `error_bias`, `mse`, and `rmse`, which the survey treats as distinct error measures. # p.4
* `segmented_carry_speculative` lacks segment-overlap width and carry-selection logic choices needed to distinguish ACAA/GeAr/SCSA/CCA/CSA/GCSA/BCSA. # pp.5-7
* `pp_perforation` lacks a perforation-geometry choice for horizontal/vertical cell removal versus omitted PP rows. # p.10
* `approximate_recurrence` lacks a replacement-region choice for vertical/horizontal/square/triangle array regions. # p.16

## open_questions
* Exact delay/power/area/PDP coordinates in Figs. 6-8, 11-13, 15-17, and 19-20 are not printed in the supplied text and must not be inferred from plots.
* Several named designs use parameter labels whose mapping to vocabulary widths is incomplete, including BAM truncation counts, HOCM stage allocation, and fixed-width Booth TPmajor size.
