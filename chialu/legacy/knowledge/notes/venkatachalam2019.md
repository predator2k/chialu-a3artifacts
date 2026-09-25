---
handle: venkatachalam2019
citation: S. Venkatachalam, E. Adams, H. J. Lee, S.-B. Ko, "Design and Analysis of Area and Power Efficient Approximate Booth Multipliers", IEEE Transactions on Computers, vol. 68, no. 11, pp. 1697-1703, 2019
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [int16]
authority: incremental
pages_read: 1-8 / 8
---

## summary
The paper proposes three approximate signed 16-bit radix-4 Booth multipliers that simplify partial-product generation and accumulation. ABM-M1 emphasizes accuracy, ABM-M2 emphasizes area/power reduction, and ABM-M3 spans both regions through an approximation factor m. The designs are evaluated in TSMC 65 nm and in image transformation/matrix multiplication/FIR filtering.

## families
### approximate_booth  (role: proposes)
mechanism: ABM-M1 replaces ±2A partial products with ±1A through PPG-2S, whose output depends on negi and zeroi. All partial products with significance below m use PPG-2S, while remaining products use the exact generator. Each correction term is ORed with a partial product in its column to reduce the Dadda matrix depth. # p.3-p.4
choices:
  radix: 4   # p.2
  approx_encoder_columns: {4, 8, 12, 16}   # p.3
  encoder: PPG-2S [outside domain]   # p.3-p.4
new_choices:
  replacement_geometry: rectangular — columns with significance below m are approximated   # p.2-p.4
  correction_term_handling: or_into_partial_product — correction terms reduce matrix height   # p.4
slots:
  none
parameters: signed 16×16-bit multiplication; m={4,8,12,16}; eight partial-product rows; exact Dadda accumulation with 4-2 compressors/full-adders/half-adders   # p.2-p.5
results:
| metric | value | unit | technology / device | baseline | condition | page |
| MRED | 0.011 × 10^-2 | dimensionless | TSMC 65 nm / 2019 | exact multiplication | m=4 | p.5 |
| NMED | 5.079 × 10^-6 | dimensionless | TSMC 65 nm / 2019 | exact multiplication | m=4 | p.5 |
| area | 3578 | µm² | TSMC 65 nm / 2019 | exact radix-8 | m=4 | p.6 |
| power | 1.3 | mW | TSMC 65 nm / 2019 | exact radix-8 | m=4 | p.6 |
| APP | 4651 (-13%) | µm² ns | TSMC 65 nm / 2019 | exact radix-8: 5351 | m=4 | p.6 |
| MRED | 0.012 × 10^-2 | dimensionless | TSMC 65 nm / 2019 | exact multiplication | m=8 | p.5 |
| NMED | 5.089 × 10^-6 | dimensionless | TSMC 65 nm / 2019 | exact multiplication | m=8 | p.5 |
| area | 3419 | µm² | TSMC 65 nm / 2019 | exact radix-8 | m=8 | p.6 |
| power | 1.2 | mW | TSMC 65 nm / 2019 | exact radix-8 | m=8 | p.6 |
| APP | 4103 (-23%) | µm² ns | TSMC 65 nm / 2019 | exact radix-8: 5351 | m=8 | p.6 |
| MRED | 0.016 × 10^-2 | dimensionless | TSMC 65 nm / 2019 | exact multiplication | m=12 | p.5 |
| NMED | 5.491 × 10^-6 | dimensionless | TSMC 65 nm / 2019 | exact multiplication | m=12 | p.5 |
| area | 3218 | µm² | TSMC 65 nm / 2019 | exact radix-8 | m=12 | p.6 |
| power | 1.2 | mW | TSMC 65 nm / 2019 | exact radix-8 | m=12 | p.6 |
| APP | 3862 (-28%) | µm² ns | TSMC 65 nm / 2019 | exact radix-8: 5351 | m=12 | p.6 |
| MRED | 0.079 × 10^-2 | dimensionless | TSMC 65 nm / 2019 | exact multiplication | m=16 | p.5 |
| NMED | 20.800 × 10^-6 | dimensionless | TSMC 65 nm / 2019 | exact multiplication | m=16 | p.5 |
| area | 3160 | µm² | TSMC 65 nm / 2019 | exact radix-8 | m=16 | p.6 |
| power | 1.1 | mW | TSMC 65 nm / 2019 | exact radix-8 | m=16 | p.6 |
| APP | 3476 (-35%) | µm² ns | TSMC 65 nm / 2019 | exact radix-8: 5351 | m=16 | p.6 |
| image PSNR | 101 | dB | ModelSim / 2019 | exact image | m=8 | p.7 |
| image PSNR | 83 | dB | ModelSim / 2019 | exact image | m=16 | p.7 |
| matrix MRED | 0.308 × 10^-3 | dimensionless | ModelSim / 2019 | exact multiplier | m=8 | p.7 |
| matrix NMED | 0.51 × 10^-5 | dimensionless | ModelSim / 2019 | exact multiplier | m=8 | p.7 |
| matrix MRED | 0.337 × 10^-3 | dimensionless | ModelSim / 2019 | exact multiplier | m=16 | p.7 |
| matrix NMED | 1.006 × 10^-5 | dimensionless | ModelSim / 2019 | exact multiplier | m=16 | p.7 |
| FIR MSE | 2.546 × 10^-9 | dimensionless | ModelSim / 2019 | exact multiplier | m=8 | p.8 |
| FIR MSE | 6.328 × 10^-8 | dimensionless | ModelSim / 2019 | exact multiplier | m=16 | p.8 |
errors_and_checks: PPG-2S changes 4 of 32 truth-table entries and has partial-product error ±1 for the affected ±2A cases; no compensation circuit is used. Overall accuracy is measured by MRED/NMED from one million uniformly distributed signed input pairs.   # p.4-p.5
conditions: Increasing m gradually reduces APP with relatively little accuracy deterioration, so ABM-M1 targets applications that cannot tolerate significant error. Hardware results use 1 V/25 °C and a uniform 1.2 ns timing constraint.   # p.5-p.6, p.8
evidence: §3.1, Table 2, Figures 3-5, Tables 3-6, Figure 9.

### approximate_booth  (role: proposes)
mechanism: ABM-M2 replaces the m least-significant exact partial-product generators in every row with one PPG-2S. The m least-significant multiplicand bits are summed, thresholded at m/2, and consolidated into one bit that drives PPG-2S with negi and zeroi. This diagonal replacement removes more matrix elements than ABM-M1 for the same m. # p.4-p.5
choices:
  radix: 4   # p.2
  approx_encoder_columns: {2, 4, 6, 8}   # p.3
  encoder: PPG-2S [outside domain]   # p.4
new_choices:
  replacement_geometry: diagonal — m generators in each row are consolidated into one generator   # p.2, p.4-p.5
  multiplicand_consolidation: sum_threshold — output is one when asum ≥ m/2   # p.4
slots:
  none
parameters: signed 16×16-bit multiplication; m={2,4,6,8}; exact Dadda accumulation with 4-2 compressors/full-adders/half-adders   # p.2-p.5
results:
| metric | value | unit | technology / device | baseline | condition | page |
| MRED | 0.040 × 10^-2 | dimensionless | TSMC 65 nm / 2019 | exact multiplication | m=2 | p.5 |
| NMED | 15.250 × 10^-6 | dimensionless | TSMC 65 nm / 2019 | exact multiplication | m=2 | p.5 |
| area | 3148 | µm² | TSMC 65 nm / 2019 | exact radix-8 | m=2 | p.6 |
| power | 1.1 | mW | TSMC 65 nm / 2019 | exact radix-8 | m=2 | p.6 |
| APP | 3463 (-35%) | µm² ns | TSMC 65 nm / 2019 | exact radix-8: 5351 | m=2 | p.6 |
| MRED | 0.165 × 10^-2 | dimensionless | TSMC 65 nm / 2019 | exact multiplication | m=4 | p.5 |
| NMED | 64.626 × 10^-6 | dimensionless | TSMC 65 nm / 2019 | exact multiplication | m=4 | p.5 |
| area | 2797 | µm² | TSMC 65 nm / 2019 | exact radix-8 | m=4 | p.6 |
| power | 1.0 | mW | TSMC 65 nm / 2019 | exact radix-8 | m=4 | p.6 |
| APP | 2797 (-48%) | µm² ns | TSMC 65 nm / 2019 | exact radix-8: 5351 | m=4 | p.6 |
| MRED | 0.663 × 10^-2 | dimensionless | TSMC 65 nm / 2019 | exact multiplication | m=6 | p.5 |
| NMED | 266.100 × 10^-6 | dimensionless | TSMC 65 nm / 2019 | exact multiplication | m=6 | p.5 |
| area | 2333 | µm² | TSMC 65 nm / 2019 | exact radix-8 | m=6 | p.6 |
| power | 0.8 | mW | TSMC 65 nm / 2019 | exact radix-8 | m=6 | p.6 |
| APP | 1866 (-65%) | µm² ns | TSMC 65 nm / 2019 | exact radix-8: 5351 | m=6 | p.6 |
| MRED | 2.689 × 10^-2 | dimensionless | TSMC 65 nm / 2019 | exact multiplication | m=8 | p.5 |
| NMED | 1087.270 × 10^-6 | dimensionless | TSMC 65 nm / 2019 | exact multiplication | m=8 | p.5 |
| area | 2015 | µm² | TSMC 65 nm / 2019 | exact radix-8 | m=8 | p.6 |
| power | 0.7 | mW | TSMC 65 nm / 2019 | exact radix-8 | m=8 | p.6 |
| APP | 1411 (-74%) | µm² ns | TSMC 65 nm / 2019 | exact radix-8: 5351 | m=8 | p.6 |
| image PSNR | 73 | dB | ModelSim / 2019 | exact image | m=4 | p.7 |
| image PSNR | 49 | dB | ModelSim / 2019 | exact image | m=8 | p.7 |
| matrix MRED | 3.274 × 10^-3 | dimensionless | ModelSim / 2019 | exact multiplier | m=4 | p.7 |
| matrix NMED | 6.074 × 10^-5 | dimensionless | ModelSim / 2019 | exact multiplier | m=4 | p.7 |
| matrix MRED | 51.774 × 10^-3 | dimensionless | ModelSim / 2019 | exact multiplier | m=8 | p.7 |
| matrix NMED | 97.726 × 10^-5 | dimensionless | ModelSim / 2019 | exact multiplier | m=8 | p.7 |
| FIR MSE | 1.044 × 10^-6 | dimensionless | ModelSim / 2019 | exact multiplier | m=4 | p.8 |
| FIR MSE | 2.673 × 10^-4 | dimensionless | ModelSim / 2019 | exact multiplier | m=8 | p.8 |
errors_and_checks: No formal accuracy bound or correction circuit is reported; MRED/NMED are estimated from one million uniformly distributed signed input pairs.   # p.5
conditions: ABM-M2 has the largest error among the proposed models and the largest APP reduction, so the paper identifies it for applications that tolerate higher error. Hardware results use 1 V/25 °C and a uniform 1.2 ns timing constraint.   # p.5-p.6, p.8
evidence: §3.2, Equation 4, Figure 6, Tables 3-6, Figure 9.

### approximate_booth  (role: proposes)
mechanism: ABM-M3 reduces all partial products with significance below m to one approximate product per row. The relevant multiplicand bits are ORed, and PPG-1S combines that value with zeroi. Correction terms remain unapproximated, which improves low-m accuracy relative to ABM-M1. # p.4-p.6
choices:
  radix: 4   # p.2
  approx_encoder_columns: {4, 8, 12, 16}   # p.3
  encoder: PPG-1S [outside domain]   # p.4-p.5
new_choices:
  replacement_geometry: rectangular_row_reduction — low-significance products become one product per row   # p.4-p.5
  multiplicand_consolidation: or_reduction — relevant multiplicand bits drive PPG-1S   # p.4-p.5
  correction_term_handling: preserve_exact — correction terms are not approximated   # p.6
slots:
  none
parameters: signed 16×16-bit multiplication; m={4,8,12,16}; exact Dadda accumulation with 4-2 compressors/full-adders/half-adders   # p.2-p.5
results:
| metric | value | unit | technology / device | baseline | condition | page |
| MRED | 0.00007 × 10^-2 | dimensionless | TSMC 65 nm / 2019 | exact multiplication | m=4 | p.5 |
| NMED | 0.005 × 10^-6 | dimensionless | TSMC 65 nm / 2019 | exact multiplication | m=4 | p.5 |
| area | 3747 | µm² | TSMC 65 nm / 2019 | exact radix-8 | m=4 | p.6 |
| power | 1.3 | mW | TSMC 65 nm / 2019 | exact radix-8 | m=4 | p.6 |
| APP | 4871 (-9%) | µm² ns | TSMC 65 nm / 2019 | exact radix-8: 5351 | m=4 | p.6 |
| MRED | 0.001 × 10^-2 | dimensionless | TSMC 65 nm / 2019 | exact multiplication | m=8 | p.5 |
| NMED | 0.106 × 10^-6 | dimensionless | TSMC 65 nm / 2019 | exact multiplication | m=8 | p.5 |
| area | 3563 | µm² | TSMC 65 nm / 2019 | exact radix-8 | m=8 | p.6 |
| power | 1.3 | mW | TSMC 65 nm / 2019 | exact radix-8 | m=8 | p.6 |
| APP | 4632 (-13%) | µm² ns | TSMC 65 nm / 2019 | exact radix-8: 5351 | m=8 | p.6 |
| MRED | 0.020 × 10^-2 | dimensionless | TSMC 65 nm / 2019 | exact multiplication | m=12 | p.5 |
| NMED | 2.002 × 10^-6 | dimensionless | TSMC 65 nm / 2019 | exact multiplication | m=12 | p.5 |
| area | 2669 | µm² | TSMC 65 nm / 2019 | exact radix-8 | m=12 | p.6 |
| power | 1.0 | mW | TSMC 65 nm / 2019 | exact radix-8 | m=12 | p.6 |
| APP | 2669 (-50%) | µm² ns | TSMC 65 nm / 2019 | exact radix-8: 5351 | m=12 | p.6 |
| MRED | 0.340 × 10^-2 | dimensionless | TSMC 65 nm / 2019 | exact multiplication | m=16 | p.5 |
| NMED | 36.150 × 10^-6 | dimensionless | TSMC 65 nm / 2019 | exact multiplication | m=16 | p.5 |
| area | 1830 | µm² | TSMC 65 nm / 2019 | exact radix-8 | m=16 | p.6 |
| power | 0.7 | mW | TSMC 65 nm / 2019 | exact radix-8 | m=16 | p.6 |
| APP | 1281 (-76%) | µm² ns | TSMC 65 nm / 2019 | exact radix-8: 5351 | m=16 | p.6 |
| image PSNR | 112 | dB | ModelSim / 2019 | exact image | m=8 | p.7 |
| image PSNR | 81 | dB | ModelSim / 2019 | exact image | m=16 | p.7 |
| matrix MRED | 0.004 × 10^-3 | dimensionless | ModelSim / 2019 | exact multiplier | m=8 | p.7 |
| matrix NMED | 0.005 × 10^-5 | dimensionless | ModelSim / 2019 | exact multiplier | m=8 | p.7 |
| matrix MRED | 1.186 × 10^-3 | dimensionless | ModelSim / 2019 | exact multiplier | m=16 | p.7 |
| matrix NMED | 1.747 × 10^-5 | dimensionless | ModelSim / 2019 | exact multiplier | m=16 | p.7 |
| FIR MSE | 3.570 × 10^-12 | dimensionless | ModelSim / 2019 | exact multiplier | m=8 | p.8 |
| FIR MSE | 2.391 × 10^-7 | dimensionless | ModelSim / 2019 | exact multiplier | m=16 | p.8 |
errors_and_checks: No formal accuracy bound or correction circuit is reported; MRED/NMED are estimated from one million uniformly distributed signed input pairs.   # p.5
conditions: ABM-M3 has high accuracy at low m, while accuracy falls below ABM-M1 as m increases and APP improves. Hardware results use 1 V/25 °C and a uniform 1.2 ns timing constraint.   # p.5-p.6, p.8
evidence: §3.3, Figures 7-8, Tables 3-6, Figure 9.

## new_families
none

## space_gaps
* approximate_booth.encoder lacks PPG-2S and PPG-1S, which simplify Booth generation by selecting subsets of negi/twoi/zeroi.   # p.3-p.5
* approximate_booth lacks a replacement_geometry choice for rectangular column replacement versus diagonal per-row consolidation.   # p.2-p.5
* approximate_booth lacks a reduction-tree slot or choice for the exact Dadda tree used after approximate generation.   # p.2, p.5
* approximate_booth lacks correction_term_handling, which distinguishes OR-combined correction terms from preserved exact correction terms.   # p.4, p.6

## open_questions
* Page 2 says ABM-M1/ABM-M2 use negi and twoi, while Equation 3/Figure 4/Table 2 use negi and zeroi; the detailed circuit evidence supports negi and zeroi.
* Table 4 labels APP with `µm² ns`, although its numerical values equal area multiplied by power; the printed unit is retained.
