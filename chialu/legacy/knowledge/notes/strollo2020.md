---
handle: strollo2020
citation: A. G. M. Strollo, E. Napoli, D. De Caro, N. Petra, G. Di Meo, "Comparison and Extension of Approximate 4-2 Compressors for Low-Power Approximate Multipliers", IEEE Transactions on Circuits and Systems I, vol. 67, no. 9, pp. 3021-3034, 2020
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [uint8, int8, uint16, int16]
authority: survey
pages_read: 3021-3034 / 3021-3034
---

## summary
The paper compares twelve approximate 4-2 compressors in signed/unsigned 8 × 8 and 16 × 16 tree multipliers and proposes a stacking-circuit-derived compressor. The paper shows that compressor selection depends on the accuracy metric, signedness, approximation extent, and input-to-pin mapping. The paper reports 28nm CMOS power/delay/area results and image-processing evaluations.

## families
### approximate_compressor_tree  (role: extends)
mechanism: Approximate 4-2 compressors replace exact compressors in a Dadda-like partial-product reduction tree that reduces the matrix to two rows. The proposed compressor derives three simplified Boolean terms from a four-input stacker and omits the lowest-probability stacker term. C-N applies approximation only to the n least-significant columns, while C-FULL applies approximation throughout the partial-product matrix. A Hybrid configuration places a low-power compressor in lower-weight columns and the Proposed compressor in higher-weight columns. Input probabilities guide pin assignment for non-input-symmetric compressors.
choices:
  approximate_columns: [8, 16, all PPM columns [outside domain]]   # pp.3024-3025
  compressor: [momeni_d1_d2, yang_inexact, akbari_dual_quality, venkatachalam_pp_alter, Lin [outside domain], Ha [outside domain], Sabetz [outside domain], Ahma [outside domain], strollo_extended]   # pp.3022-3024
  error_recovery: none   # pp.3023-3024
  dual_quality_runtime: false   # pp.3023-3024
new_choices:
  approximation_extent: {C-N, C-FULL, Hybrid} — C-N approximates the n least-significant columns, C-FULL approximates the whole matrix, and Hybrid assigns different compressors by column weight   # pp.3024, 3026
  input_pin_assignment: {probability_optimized, input_commutative} — non-symmetric compressors require probability-aware assignment of partial products to x1…x4, while Yang1 and Lin are input symmetric   # pp.3025-3026, 3033
slots:
  none
parameters: 8 × 8 and 16 × 16 signed/unsigned multipliers; C-N uses 9 approximate/8 exact compressors at 8 × 8 and 49 approximate/48 exact compressors at 16 × 16; timing constraints 500ps and 750ps; nominal supply 0.9V; toggle frequency 1GHz   # pp.3024-3025, 3028
results:
| metric | value | unit | technology / device | baseline | condition | page |
| delay reduction | up to about 50 | % | TSMC 28nm CMOS (2020) | exact multiplier | 16 × 16, C-FULL, Sabetz | p.3028 |
| power reduction | about 40 | % | TSMC 28nm CMOS (2020) | exact multiplier | 16 × 16, C-N, Sabetz | p.3029 |
| power reduction | about 80 | % | TSMC 28nm CMOS (2020) | exact multiplier | 16 × 16, C-FULL, Sabetz | p.3029 |
| power reduction | about 45 | % | TSMC 28nm CMOS (2020) | exact multiplier | 16 × 16, C-FULL, Hybrid | p.3029 |
| power reduction | 36 | % | TSMC 28nm CMOS (2020) | exact multiplier | 8 × 8, C-FULL, Hybrid | p.3028 |
| power reduction | 8.5 | % | TSMC 28nm CMOS (2020) | exact multiplier | 8 × 8, C-N, Proposed | p.3028 |
| power reduction | about 14 | % | TSMC 28nm CMOS (2020) | exact multiplier | 8 × 8, C-N, Hybrid | p.3028 |
| NMED | 1.5 × 10−5 | dimensionless | TSMC 28nm CMOS (2020) | exact products | signed 16-bit, C-N, Sabetz; about 39% power saving | p.3029 |
| power reduction | 45.3 | % | TSMC 28nm CMOS (2020) | exact multiplier | signed 16-bit, C-FULL, Hybrid; NMED about 1.1 × 10−2 | p.3029 |
| NMED | about 1.1 × 10−2 | dimensionless | TSMC 28nm CMOS (2020) | exact products | signed 16-bit, C-FULL, Hybrid; 45.3% power saving | p.3029 |
errors_and_checks: ER, NMED, MRED, NoEB, and PRED measure multiplier error. Only Yang1/Lin/Proposed achieve MRED < 0.01 for both unsigned widths under C-FULL. Signed C-FULL multipliers exhibit frequent large relative errors because complemented partial products increase input-one probability in high-weight columns.   # pp.3026-3029
conditions: Lin/Proposed/Ha/Hybrid occupy the high-precision Pareto frontier for C-N, while Ahma/Sabetz trade more accuracy for larger power reductions. Momeni/Sabetz can emit a nonzero output for all-zero inputs, which causes large relative errors for small operands. Approximate compressors should be avoided in the most-significant columns of signed partial-product matrices. Application quality varies by workload, and only Yang/Lin/Proposed/Hybrid give PSNR above 25dB in the signed Sobel test.   # pp.3026, 3029-3033
evidence: §II-B–II-D, Figs. 2-3, Table I; §III-A–III-D, Figs. 4-9, Tables II-VI; §IV, Figs. 10-12, Tables VII-IX

### error_analysis_quality  (role: analyzes)
mechanism: Exact and approximate products M and M′ define Error Distance ED = |M − M′| and Relative Error Distance RED = ED/|M| for M ≠ 0. The evaluation reports ER, NMED, MRED, NoEB, and PRED. Eight-bit multipliers are evaluated exhaustively, while 16-bit multipliers use 50 million random vectors.
choices:
  metric: [er, nmed, mred, NoEB [outside domain], PRED [outside domain]]   # p.3026
  model: [exhaustive_sim, monte_carlo]   # p.3026
new_choices:
  none
slots:
  none
parameters: exhaustive simulation for 8 × 8; 50 million random vectors for 16 × 16   # p.3026
results:
| metric | value | unit | technology / device | baseline | condition | page |
| simulation vectors | 50 million | vectors | TSMC 28nm CMOS (2020) | exact-product comparison | 16 × 16 multipliers | p.3026 |
errors_and_checks: ER is the percentage with ED > 0; NMED is mean ED divided by MaxOut; MRED is mean RED; NoEB = 2n − log2(1 + ERMS); PRED is the probability that RED exceeds 2 percent.   # p.3026
conditions: Metric ranking is not invariant; the best compressor depends on the selected error metric, approximation extent, and signedness.   # pp.3029, 3032-3033
evidence: §III-B, Tables II-V, Figs. 8-9

## new_families
none

## space_gaps
* `approximate_compressor_tree.compressor` lacks the paper’s Lin/Ha/Sabetz/Ahma topology values.   # pp.3022-3024
* `approximate_compressor_tree` lacks a choice for probability-aware input-pin assignment in non-input-symmetric compressors.   # pp.3025-3026
* `approximate_compressor_tree` lacks a choice for C-N/C-FULL/Hybrid column placement and mixed-compressor trees.   # pp.3024, 3026
* `error_analysis_quality.metric` lacks NoEB and PRED.   # p.3026

## open_questions
* The supplied transcription does not expose the numeric cells of Tables II-VI, so compressor-by-compressor error/area/delay/power values cannot be recorded without guessing.
* The final two-row carry-propagate adder topology is not identified.
