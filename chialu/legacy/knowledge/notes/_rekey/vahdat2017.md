---
handle: vahdat2017
citation: S. Vahdat, M. Kamal, A. Afzali-Kusha, M. Pedram, "LETAM: A Low Energy Truncation-Based Approximate Multiplier", Computers and Electrical Engineering, vol. 63, pp. 1-17, 2017
actual_citation: S. Vahdat, M. Kamal, A. Afzali-Kusha, M. Pedram, Z. Navabi, "TruncApp: A Truncation-based Approximate Divider for Energy Efficient DSP Applications", 2017 Design, Automation & Test in Europe Conference & Exhibition (DATE), 2017
status: mismatch
kind: paper
unit_classes: [BINARY_ALU]
formats: [int32]
authority: incremental
pages_read: 4 / 4
---

## summary
TruncApp approximates integer division by multiplying a truncated dividend by a bit-inversion approximation of the truncated divisor's reciprocal (pp.1635-1636). TruncApp_AM further truncates the multiplication partial products and is evaluated for error, synthesized cost, and image-processing quality (pp.1636-1638).

## families
### approximate_functional  (role: proposes)
mechanism: The leading-one positions normalize the dividend and divisor. A truncation unit retains t bits of each normalized operand. The inverse unit approximates 1/(X_B)_t by inverting the divisor's retained fractional bits and concatenating a leading “1”. An exact multiplier produces TruncApp, while a multiplier that omits selected partial products produces TruncApp_AM. A shift restores the exponent difference, and approximate absolute/sign units support signed operands (pp.1635-1636).
choices:
  method: truncated_reciprocal_multiply   # pp.1635-1636
  segment_or_lut_width: 3 / 4 / 5   # pp.1637-1638
new_choices:
  multiplication_accuracy: {exact, partial_product_truncated} — selects TruncApp or TruncApp_AM multiplication   # p.1636
slots:
  none
parameters: 32-bit signed/unsigned operands; reported implementations are TruncApp(3), TruncApp(4), and TruncApp_AM(5), where t is the truncation length   # pp.1637-1638
results:
| metric | value | unit | technology / device | baseline | condition | page |
| delay | 0.84 | ns | NanGate 45nm CMOS / 2017 | absolute | unsigned TruncApp(3) | p.1638 |
| power | 0.56 | mW | NanGate 45nm CMOS / 2017 | absolute | unsigned TruncApp(3) | p.1638 |
| area | 1261 | μm2 | NanGate 45nm CMOS / 2017 | absolute | unsigned TruncApp(3) | p.1638 |
| energy | 0.47 | pJ | NanGate 45nm CMOS / 2017 | absolute | unsigned TruncApp(3) | p.1638 |
| EDP | 0.39 | pJ×ns | NanGate 45nm CMOS / 2017 | absolute | unsigned TruncApp(3) | p.1638 |
| PDA | 590 | pJ×μm2 | NanGate 45nm CMOS / 2017 | absolute | unsigned TruncApp(3) | p.1638 |
| delay | 1.05 | ns | NanGate 45nm CMOS / 2017 | absolute | unsigned TruncApp(4) | p.1638 |
| power | 0.8 | mW | NanGate 45nm CMOS / 2017 | absolute | unsigned TruncApp(4) | p.1638 |
| area | 1483 | μm2 | NanGate 45nm CMOS / 2017 | absolute | unsigned TruncApp(4) | p.1638 |
| energy | 0.84 | pJ | NanGate 45nm CMOS / 2017 | absolute | unsigned TruncApp(4) | p.1638 |
| EDP | 0.88 | pJ×ns | NanGate 45nm CMOS / 2017 | absolute | unsigned TruncApp(4) | p.1638 |
| PDA | 1241 | pJ×μm2 | NanGate 45nm CMOS / 2017 | absolute | unsigned TruncApp(4) | p.1638 |
| delay | 1.08 | ns | NanGate 45nm CMOS / 2017 | absolute | unsigned TruncApp_AM(5) | p.1638 |
| power | 0.75 | mW | NanGate 45nm CMOS / 2017 | absolute | unsigned TruncApp_AM(5) | p.1638 |
| area | 1491 | μm2 | NanGate 45nm CMOS / 2017 | absolute | unsigned TruncApp_AM(5) | p.1638 |
| energy | 0.81 | pJ | NanGate 45nm CMOS / 2017 | absolute | unsigned TruncApp_AM(5) | p.1638 |
| EDP | 0.88 | pJ×ns | NanGate 45nm CMOS / 2017 | absolute | unsigned TruncApp_AM(5) | p.1638 |
| PDA | 1211 | pJ×μm2 | NanGate 45nm CMOS / 2017 | absolute | unsigned TruncApp_AM(5) | p.1638 |
| delay | 1.08 | ns | NanGate 45nm CMOS / 2017 | absolute | signed TruncApp(3) | p.1638 |
| power | 1.06 | mW | NanGate 45nm CMOS / 2017 | absolute | signed TruncApp(3) | p.1638 |
| area | 1695 | μm2 | NanGate 45nm CMOS / 2017 | absolute | signed TruncApp(3) | p.1638 |
| energy | 1.14 | pJ | NanGate 45nm CMOS / 2017 | absolute | signed TruncApp(3) | p.1638 |
| EDP | 1.24 | pJ×ns | NanGate 45nm CMOS / 2017 | absolute | signed TruncApp(3) | p.1638 |
| PDA | 1940 | pJ×μm2 | NanGate 45nm CMOS / 2017 | absolute | signed TruncApp(3) | p.1638 |
| delay | 1.2 | ns | NanGate 45nm CMOS / 2017 | absolute | signed TruncApp(4) | p.1638 |
| power | 1.53 | mW | NanGate 45nm CMOS / 2017 | absolute | signed TruncApp(4) | p.1638 |
| area | 2099 | μm2 | NanGate 45nm CMOS / 2017 | absolute | signed TruncApp(4) | p.1638 |
| energy | 1.84 | pJ | NanGate 45nm CMOS / 2017 | absolute | signed TruncApp(4) | p.1638 |
| EDP | 2.20 | pJ×ns | NanGate 45nm CMOS / 2017 | absolute | signed TruncApp(4) | p.1638 |
| PDA | 3854 | pJ×μm2 | NanGate 45nm CMOS / 2017 | absolute | signed TruncApp(4) | p.1638 |
| delay | 1.26 | ns | NanGate 45nm CMOS / 2017 | absolute | signed TruncApp_AM(5) | p.1638 |
| power | 1.42 | mW | NanGate 45nm CMOS / 2017 | absolute | signed TruncApp_AM(5) | p.1638 |
| area | 2048 | μm2 | NanGate 45nm CMOS / 2017 | absolute | signed TruncApp_AM(5) | p.1638 |
| energy | 1.79 | pJ | NanGate 45nm CMOS / 2017 | absolute | signed TruncApp_AM(5) | p.1638 |
| EDP | 2.25 | pJ×ns | NanGate 45nm CMOS / 2017 | absolute | signed TruncApp_AM(5) | p.1638 |
| PDA | 3664 | pJ×μm2 | NanGate 45nm CMOS / 2017 | absolute | signed TruncApp_AM(5) | p.1638 |
errors_and_checks: RE=(P_app-P)/P. For unsigned 32-bit designs, MaxRE is 12.5% for all tested truncation lengths. At 32 bits, MeanARE/VarARE are 10%/0.39% for TruncApp(3), 4.2%/0.09% for TruncApp(4), and 3.67%/0.05% for TruncApp_AM(5). For t=4 and n=32, the analytical example gives MinRE=-16.67% (p.1637).
conditions: TruncApp targets error-tolerant DSP applications (p.1635). Increasing t improves MinRE, while t greater than 4 makes positive RE occur in more than 50% of TruncApp outputs; partial-product omission lowers outputs and gives TruncApp_AM lower MeanARE for t greater than 4 (p.1637). Unsigned TruncApp_AM(5) reports 66% less area, 64% less power, and 52% less energy than SEERAD(3) while reporting lower MeanARE (p.1637). Signed TruncApp_AM(5) has nearly the same delay as SEERAD(4) and reports 84% less area and 85% less energy (p.1638). The shift unit contributes the largest delay/power shares in the reported breakdown, while multiplier shares increase with t (p.1638).
evidence: Equations (1)-(13), Figures 1-3, and Tables I-IV, pp.1635-1638; image-division application in Table V, p.1638.

## new_families
none

## space_gaps
* approximate_functional lacks a multiplier slot that distinguishes an exact multiplier from the partial-product-truncated multiplier used by TruncApp_AM (p.1636).
* The family vocabulary names a segment_or_lut_width, while this design exposes truncation length t for both normalized operands and reciprocal generation (pp.1635-1637).

## open_questions
* Figure 2 identifies ignored partial products graphically but does not state a general parameterized rule for which partial products TruncApp_AM omits.
* The document does not report a latency-cycle count or initiation interval.
