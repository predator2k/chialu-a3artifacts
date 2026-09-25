---
handle: hashemi2016
citation: S. Hashemi, R. I. Bahar, S. Reda, "A Low-Power Dynamic Divider for Approximate Applications", 53rd Design Automation Conference (DAC), 2016
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [unsigned_integer, signed_integer]
authority: incremental
pages_read: 6 / 6
---

## summary
The document proposes a configurable approximate divider that dynamically selects leading operand bits, divides the reduced operands with a smaller accurate divider, and shifts the quotient into position (pp.2–3). A 65-nm implementation reports configurable accuracy/area/power/delay tradeoffs and evaluates change detection/JPEG compression/foreground extraction applications (pp.4–6).

## families
### approximate_functional  (role: proposes)
mechanism: Leading-one detectors locate the most significant `1` of each operand. Multiplexers select that bit and the next `k−1` bits, while lower bits are truncated. A smaller accurate core divider divides the selected windows, and a barrel shifter restores the quotient position from the operand-leading-position difference. Operands whose leading `1` lies within the lowest `k` bits pass without truncation. The core divider can use a designer-selected architecture; experiments use a conventional array divider. (pp.2–3)
choices:
  method: dynamic_segment_exact_core   # pp.2–3
  segment_or_lut_width: k = 2..n; evaluated at 4, 6, 8, 10, 12 [outside domain]   # p.4
new_choices:
  none
slots:
  none
parameters: dividend width `n`; divisor width `n/2`; selected dividend range `k`; selected divisor range `k/2`; evaluated sizes 16/8, 24/12, and 32/16 bits; evaluated `k = 4, 6, 8, 10, 12`; standalone simulations use two sets of ten-million random vectors   # pp.2–5
results:
| metric | value | unit | technology / device | baseline | condition | page |
| Max. ED | 64 | quotient units | industrial 65-nm standard-cell / 2016 | accurate divider | n=16, k=4 | p.4 |
| Average Abs Error | 13.57 | % | industrial 65-nm standard-cell / 2016 | accurate divider | n=16, k=4 | p.4 |
| Error Bias | -1.78 | % | industrial 65-nm standard-cell / 2016 | accurate divider | n=16, k=4 | p.4 |
| Standard Deviation | 17.16 | % | industrial 65-nm standard-cell / 2016 | accurate divider | n=16, k=4 | p.4 |
| Max. ED | 44 | quotient units | industrial 65-nm standard-cell / 2016 | accurate divider | n=16, k=6 | p.4 |
| Average Abs Error | 6.37 | % | industrial 65-nm standard-cell / 2016 | accurate divider | n=16, k=6 | p.4 |
| Error Bias | -1.49 | % | industrial 65-nm standard-cell / 2016 | accurate divider | n=16, k=6 | p.4 |
| Standard Deviation | 8.55 | % | industrial 65-nm standard-cell / 2016 | accurate divider | n=16, k=6 | p.4 |
| Max. ED | 26 | quotient units | industrial 65-nm standard-cell / 2016 | accurate divider | n=16, k=8 | p.4 |
| Average Abs Error | 3.08 | % | industrial 65-nm standard-cell / 2016 | accurate divider | n=16, k=8 | p.4 |
| Error Bias | -0.93 | % | industrial 65-nm standard-cell / 2016 | accurate divider | n=16, k=8 | p.4 |
| Standard Deviation | 4.60 | % | industrial 65-nm standard-cell / 2016 | accurate divider | n=16, k=8 | p.4 |
| Max. ED | 13 | quotient units | industrial 65-nm standard-cell / 2016 | accurate divider | n=16, k=10 | p.4 |
| Average Abs Error | 1.42 | % | industrial 65-nm standard-cell / 2016 | accurate divider | n=16, k=10 | p.4 |
| Error Bias | -0.48 | % | industrial 65-nm standard-cell / 2016 | accurate divider | n=16, k=10 | p.4 |
| Standard Deviation | 2.56 | % | industrial 65-nm standard-cell / 2016 | accurate divider | n=16, k=10 | p.4 |
| Max. ED | 6 | quotient units | industrial 65-nm standard-cell / 2016 | accurate divider | n=16, k=12 | p.4 |
| Average Abs Error | 0.59 | % | industrial 65-nm standard-cell / 2016 | accurate divider | n=16, k=12 | p.4 |
| Error Bias | -0.23 | % | industrial 65-nm standard-cell / 2016 | accurate divider | n=16, k=12 | p.4 |
| Standard Deviation | 1.50 | % | industrial 65-nm standard-cell / 2016 | accurate divider | n=16, k=12 | p.4 |
| Average Abs Error | 3.03 | % | industrial 65-nm standard-cell / 2016 | accurate divider | n=16, k=8 | p.4 |
| Average Abs Error | 3.09 | % | industrial 65-nm standard-cell / 2016 | accurate divider | n=24, k=8 | p.4 |
| Average Abs Error | 3.09 | % | industrial 65-nm standard-cell / 2016 | accurate divider | n=32, k=8 | p.4 |
| Area saving | 66.08 | % | industrial 65-nm standard-cell / 2016 | accurate divider | n=16, k=4 | p.4 |
| Power saving | 90.04 | % | industrial 65-nm standard-cell / 2016 | accurate divider | n=16, k=4 | p.4 |
| Area saving | 41.85 | % | industrial 65-nm standard-cell / 2016 | accurate divider | n=16, k=8 | p.4 |
| Power saving | 70.81 | % | industrial 65-nm standard-cell / 2016 | accurate divider | n=16, k=8 | p.4 |
| Area saving | 75.80 | % | industrial 65-nm standard-cell / 2016 | accurate divider | n=32, k=8 | p.4 |
| Power saving | 93.17 | % | industrial 65-nm standard-cell / 2016 | accurate divider | n=32, k=8 | p.4 |
| Accurate delay | 8.39 | ns | industrial 65-nm standard-cell / 2016 | accurate divider | 16/8 bits, k=6 | p.5 |
| Approximate delay | 4.75 | ns | industrial 65-nm standard-cell / 2016 | accurate divider | 16/8 bits, k=6; 1.77× speedup | p.5 |
| Accurate delay | 17.33 | ns | industrial 65-nm standard-cell / 2016 | accurate divider | 24/12 bits, k=6 | p.5 |
| Approximate delay | 5.26 | ns | industrial 65-nm standard-cell / 2016 | accurate divider | 24/12 bits, k=6; 3.29× speedup | p.5 |
| Accurate delay | 29.60 | ns | industrial 65-nm standard-cell / 2016 | accurate divider | 32/16 bits, k=6 | p.5 |
| Approximate delay | 5.74 | ns | industrial 65-nm standard-cell / 2016 | accurate divider | 32/16 bits, k=6; 5.16× speedup | p.5 |
| PSNR | 28.87 | dB | industrial 65-nm standard-cell / 2016 | accurate application output | change detection, k=8 | p.5 |
| Area saving | 40.51 | % | industrial 65-nm standard-cell / 2016 | accurate implementation | change detection | p.5 |
| Power saving | 75.86 | % | industrial 65-nm standard-cell / 2016 | accurate implementation | change detection | p.5 |
| Delay reduction | 2.84× | ratio | industrial 65-nm standard-cell / 2016 | accurate implementation | change detection | p.5 |
| PSNR | 24.82 | dB | industrial 65-nm standard-cell / 2016 | accurate application output | JPEG compression, 16/8 bits, k=8 | p.6 |
| Area saving | 14.63 | % | industrial 65-nm standard-cell / 2016 | accurate implementation | JPEG compression | p.6 |
| Power saving | 29.23 | % | industrial 65-nm standard-cell / 2016 | accurate implementation | JPEG compression | p.6 |
| Delay reduction | 1.52× | ratio | industrial 65-nm standard-cell / 2016 | accurate implementation | JPEG compression | p.6 |
| PSNR | 23.96 | dB | industrial 65-nm standard-cell / 2016 | accurate application output | foreground extraction, k=8 | p.6 |
| Area saving | 18.30 | % | industrial 65-nm standard-cell / 2016 | accurate implementation | foreground extraction | p.6 |
| Power saving | 64.02 | % | industrial 65-nm standard-cell / 2016 | accurate implementation | foreground extraction | p.6 |
| Delay reduction | 2.44× | ratio | industrial 65-nm standard-cell / 2016 | accurate implementation | foreground extraction | p.6 |
errors_and_checks: `RE = (Acc − App)/Acc` and `ED = |App − Acc|`; truncating both operands permits underestimation or overestimation and partial error cancellation. More than 99.5% of relative errors lie within a 15% bound for n=16, k=8. No fault-detection mechanism is reported.   # pp.2,4
conditions: The design targets error-resilient applications with small bounded-error tolerance and frequent division. Benefits increase with operand width because steering logic grows as `O(n log n)` while the core arithmetic grows as `O(k²)` with `k << n`. Signed division requires magnitude preprocessing and conditional output negation.   # pp.3,5
evidence: §3; Figures 1–4; §4.1; Tables 1–3; Figures 5–8; §4.2; Tables 4–6; Figures 9–11.

## new_families
none

## space_gaps
* `approximate_functional` lacks a slot for the smaller accurate core divider, although the paper makes its architecture designer-selectable and evaluates a conventional array divider.   # pp.2–3
* `error_analysis_quality.metric` lacks relative error/error distance/error bias/standard deviation, which the paper uses to characterize divider accuracy.   # p.4

## open_questions
* Table 1 reports 3.08% average absolute error for n=16, k=8, while Table 2 reports 3.03% for the same stated configuration.   # p.4
* Figure 7 labels the higher series as total power savings, while the accompanying prose calls the lower 42%/62%/76% series power savings.   # p.4
