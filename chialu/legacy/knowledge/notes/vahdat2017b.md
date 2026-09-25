---
handle: vahdat2017b
citation: S. Vahdat, M. Kamal, A. Afzali-Kusha, M. Pedram, Z. Navabi, "TruncApp: A Truncation-Based Approximate Divider for Energy Efficient DSP Applications", Design, Automation and Test in Europe (DATE), pp. 1635-1638, 2017
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [uint8, uint16, uint32, int32]
authority: incremental
pages_read: 1635-1638 / 4
---

## summary
TruncApp approximates division by multiplying a truncated dividend by a bit-inversion approximation of the truncated divisor’s reciprocal. TruncApp_AM further truncates partial products in the multiplication unit, reducing hardware cost with small reported accuracy loss.

## families
### approximate_functional  (role: proposes)
mechanism: TruncApp detects each operand’s leading one, retains a t-bit normalized value, approximates the divisor reciprocal by inverting its retained fractional bits and concatenating “1,” multiplies that reciprocal by the truncated dividend, shifts by kA-kB, and fixes the sign. TruncApp_AM uses a multiplier that omits selected partial products. # pp.1635-1636
choices:
  method: truncated_reciprocal_multiply   # pp.1635-1636
  segment_or_lut_width: 3, 4, or 5   # pp.1637-1638
new_choices:
  multiplier_implementation: exact | truncated_partial_products — selects TruncApp or TruncApp_AM multiplication   # p.1636
  reciprocal_generation: invert_fraction_and_prepend_one — generates the approximate reciprocal without a reciprocal table   # pp.1635-1636
slots:
  none
parameters: n-bit signed or unsigned operands; evaluated at 8, 16, and 32 bits; truncation length t; 32-bit hardware evaluation; combinational latency reported as delay   # pp.1636-1638
results:
| metric | value | unit | technology / device | baseline | condition | page |
| MeanARE / VarARE at 8, 16, 32 bits | 10.1/0.4; 9.8/0.39; 10/0.39 | % / % | UNKNOWN / 2017 | none | TruncApp(3) | p.1637 |
| MeanARE / VarARE at 8, 16, 32 bits | 4.3/0.09; 4.22/0.09; 4.2/0.09 | % / % | UNKNOWN / 2017 | none | TruncApp(4) | p.1637 |
| MeanARE / VarARE at 8, 16, 32 bits | 3.8/0.06; 3.76/0.06; 3.67/0.05 | % / % | UNKNOWN / 2017 | none | TruncApp_AM(5) | p.1637 |
| MeanARE / VarARE at 8, 16, 32 bits | 16.55/1.1; 16.25/1; 16.25/1 | % / % | UNKNOWN / 2017 | none | SEERAD(1) | p.1637 |
| MeanARE / VarARE at 8, 16, 32 bits | 9.15/0.41; 8.77/0.35; 8.77/0.36 | % / % | UNKNOWN / 2017 | none | SEERAD(2) | p.1637 |
| MeanARE / VarARE at 8, 16, 32 bits | 4.66/0.1; 4.55/0.09; 4.55/0.09 | % / % | UNKNOWN / 2017 | none | SEERAD(3) | p.1637 |
| MeanARE / VarARE at 8, 16, 32 bits | 2.42/0.03; 2.2/0.02; 2.2/0.02 | % / % | UNKNOWN / 2017 | none | SEERAD(4) | p.1637 |
| MaxRE | 12.5 | % | UNKNOWN / 2017 | exact division | all evaluated 32-bit TruncApp and TruncApp_AM configurations | p.1637 |
| MinRE | -16.67 | % | UNKNOWN / 2017 | exact division | example with t=4, n=32 | p.1637 |
| delay / power / area / energy / EDP / PDA | 0.84 / 0.56 / 1261 / 0.47 / 0.39 / 590 | ns / mW / μm2 / pJ / pJ×ns / pJ×μm2 | NanGate 45nm CMOS / 2017 | none | unsigned TruncApp(3) | p.1638 |
| delay / power / area / energy / EDP / PDA | 1.05 / 0.8 / 1483 / 0.84 / 0.88 / 1241 | ns / mW / μm2 / pJ / pJ×ns / pJ×μm2 | NanGate 45nm CMOS / 2017 | none | unsigned TruncApp(4) | p.1638 |
| delay / power / area / energy / EDP / PDA | 1.08 / 0.75 / 1491 / 0.81 / 0.88 / 1211 | ns / mW / μm2 / pJ / pJ×ns / pJ×μm2 | NanGate 45nm CMOS / 2017 | none | unsigned TruncApp_AM(5) | p.1638 |
| delay / power / area / energy / EDP / PDA | 1.08 / 1.06 / 1695 / 1.14 / 1.24 / 1940 | ns / mW / μm2 / pJ / pJ×ns / pJ×μm2 | NanGate 45nm CMOS / 2017 | none | signed TruncApp(3) | p.1638 |
| delay / power / area / energy / EDP / PDA | 1.2 / 1.53 / 2099 / 1.84 / 2.20 / 3854 | ns / mW / μm2 / pJ / pJ×ns / pJ×μm2 | NanGate 45nm CMOS / 2017 | none | signed TruncApp(4) | p.1638 |
| delay / power / area / energy / EDP / PDA | 1.26 / 1.42 / 2048 / 1.79 / 2.25 / 3664 | ns / mW / μm2 / pJ / pJ×ns / pJ×μm2 | NanGate 45nm CMOS / 2017 | none | signed TruncApp_AM(5) | p.1638 |
| area / power / energy improvement | 66 / 64 / 52 | % | NanGate 45nm CMOS / 2017 | unsigned SEERAD(3) | unsigned TruncApp_AM(5), with lower MeanARE | p.1637 |
| delay / area / energy reduction | 94.4 / 94.4 / 99.93 | % | NanGate 45nm CMOS / 2017 | exact radix-4 SRT | average unsigned proposed divider | p.1638 |
| area / energy improvement | 84 / 85 | % | NanGate 45nm CMOS / 2017 | signed SEERAD(4) | signed TruncApp_AM(5), with almost the same speed | p.1638 |
| PSNR / MSSIM | 35.7/0.94; 35/0.96; 34.5/0.98; 34.1/0.96 | dB / unitless | UNKNOWN / 2017 | exact output images | TruncApp_AM(5): Walter Cronkite; Chemical Plant close/far; Toy vehicle | p.1638 |
errors_and_checks: RE=(Papp-P)/P. The evaluation reports MinRE, positive-RE frequency, MeanARE, and VarARE; MaxRE is 12.5% for every evaluated 32-bit configuration. No runtime error detection, correction, or accuracy guarantee is reported. # p.1637
conditions: The design targets error-tolerant signal-processing and data-mining applications. # p.1635 TruncApp ignores the reciprocal value 1 when XB=1 because the paper describes that case as very unlikely. # p.1635 Increasing t improves MinRE, while accuracy is nearly independent of operand width. # p.1637 TruncApp_AM has lower MeanARE than TruncApp when t is greater than 4 because omitted partial products reduce output values. # p.1637 TruncApp(3) produces the lowest image quality among the tested TruncApp configurations. # p.1638
evidence: Equations (1)-(13), Figures 1-3, and Tables I-V, pp.1635-1638.

### pp_perforation  (role: instantiates)
mechanism: The TruncApp_AM multiplication unit omits the gray partial products shown in its dot diagram, while the remaining multiplication structure forms the product of the truncated dividend and approximate reciprocal. # p.1636
choices:
  cell: exact_and   # p.1636
  correction: none   # p.1636
new_choices:
  perforation_pattern: figure_2b_fixed_pattern — identifies omitted partial products by position rather than by a reported row count   # p.1636
slots:
  none
parameters: 2t-bit multiplication inputs; evaluated as TruncApp_AM(5) with t=5   # pp.1636-1638
results:
| metric | value | unit | technology / device | baseline | condition | page |
| multiplication-unit delay / power contribution | 39.5 / 13.8 | % / % | NanGate 45nm CMOS / 2017 | total divider delay / power | TruncApp_AM(5) | p.1638 |
errors_and_checks: The paper reports negligible accuracy loss qualitatively for the approximate multiplier and reports MeanARE/VarARE for the complete divider; it gives no isolated multiplier-error bound. # pp.1635,1637
conditions: The approximate multiplier reduces output values and improves complete-divider MeanARE relative to the exact multiplier when t is greater than 4. # p.1637
evidence: Figure 2 and its discussion, p.1636; Figures 3 and Tables II-IV, pp.1637-1638.

## new_families
none

## space_gaps
* approximate_functional lacks a multiplier implementation choice or multiplier slot for distinguishing exact multiplication from fixed partial-product perforation. # p.1636
* pp_perforation lacks a positional perforation-pattern choice for the fixed omitted-partial-product geometry in Figure 2(b). # p.1636
* approximate_functional lacks a reciprocal-generation choice for bit inversion plus concatenation rather than LUT-based reciprocal approximation. # pp.1635-1636

## open_questions
* Table III prints two signed rows labeled SEERAD(4) with different results, so the first label may be a document error that the merge pass must not correct by inference.
* Figure 2(b) identifies omitted partial products graphically but does not state a perforated-row count.
