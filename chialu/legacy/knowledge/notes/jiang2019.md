---
handle: jiang2019
citation: H. Jiang, L. Liu, F. Lombardi, J. Han, "Low-Power Unsigned Divider and Square Root Circuit Designs Using Adaptive Approximation", IEEE Transactions on Computers, vol. 68, no. 11, pp. 1635-1646, 2019
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [uint16, uint32]
authority: incremental
pages_read: 12 / 12
---

## summary
The document proposes adaptively approximate unsigned divider and square-root circuits that retain significant input windows and use reduced-width exact cores. Leading-one detection, scaling shifts, and divider overflow correction provide bounded error while reducing power/delay. Combinational and sequential implementations are evaluated in ST’s 28 nm CMOS process and three image-processing applications.

## families
### approximate_functional  (role: proposes)
mechanism: AAXD detects each operand’s leading-one position, selects 2k consecutive dividend bits and k consecutive divisor bits, and appends zeros when fewer bits remain. An exact 2(k + 1)/(k + 1) divider computes the reduced division. A bidirectional shifter scales its quotient by 2^(lA-lB-k), and n OR gates saturate an overflowing (n + 1)-bit intermediate quotient to 2^n-1. The exact core may be an array, sequential, or high-radix divider.
choices:
  method: dynamic_segment_exact_core   # p.3-4
  segment_or_lut_width: 2k dividend bits / k divisor bits [outside domain]   # p.3
  bias_correction: false   # p.4
  runtime_quality_scaling: false   # p.6-8
new_choices:
  overflow_correction: or_gate_saturation — ORs qsn into every retained quotient bit   # p.4
  core_implementation: combinational_or_sequential — selects the reduced-width exact-divider structure   # p.4,8
slots:
  none
parameters: 2n/n unsigned division; k<n; evaluated as 16/8 with 2k=6, 8, 10 and as 32/16 with 2k=20; sequential latency N=k+3 cycles   # p.3,7-8,10-11
results:
| metric | value | unit | technology / device | baseline | condition | page |
| delay reduction | 60.51 | % | ST 28 nm CMOS, 2019 | EXDr | AAXD, 16/8, 6-bit pruned dividend | p.7 |
| area reduction | 38.63 | % | ST 28 nm CMOS, 2019 | EXDr | AAXD, 16/8, 6-bit pruned dividend | p.7 |
| power reduction | 65.88 | % | ST 28 nm CMOS, 2019 | EXDr | AAXD, 16/8, 6-bit pruned dividend | p.7 |
| PDP reduction | 51.61%-86.53% | % | ST 28 nm CMOS, 2019 | EXDr | evaluated AAXD configurations | p.7 |
| ADP reduction | 24.18%-75.76% | % | ST 28 nm CMOS, 2019 | EXDr | evaluated AAXD configurations | p.7 |
| delay | 10.16 | ns | ST 28 nm CMOS, 2019 | EXDr 18.49 ns | AAXD-20, 32/16, combinational | p.11 |
| area | 966.1 | µm2 | ST 28 nm CMOS, 2019 | EXDr 1,218.0 µm2 | AAXD-20, 32/16, combinational | p.11 |
| power | 67.94 | µW | ST 28 nm CMOS, 2019 | EXDr 136.80 µW | AAXD-20, 32/16, combinational | p.11 |
| PDP | 690.27 | fJ | ST 28 nm CMOS, 2019 | EXDr 2,529.43 fJ | AAXD-20, 32/16, combinational | p.11 |
| EPO | 9.27 | pJ/op | ST 28 nm CMOS, 2019 | EXDr_S 13.71 pJ/op | AAXD_S-20, 32/16, N=13 | p.11 |
| TPA | 3,089 | ops/(s·µm2) | ST 28 nm CMOS, 2019 | EXDr_S 1,549 ops/(s·µm2) | AAXD_S-20 | p.11 |
| average PSNR | 44.71 | dB | UNKNOWN, 2019 | competing approximate dividers | change detection, AAXD-10 | p.9 |
errors_and_checks: The integer error is the absolute difference from the accurate quotient. The tighter analyzed ED bound is ceil((2^n-1)(2^(n-k)-1)/(2^(n-1)+2^(n-k)-1)); the looser bound is EDLUB=2^(n-k+1)-2. Exhaustive 16/8 testing uses all valid dividend/divisor pairs satisfying no overflow.   # p.4-6
conditions: Static LSB truncation causes large relative errors for small operands. AAXD requires the dividend’s n MSBs to be smaller than the divisor. Smaller k reduces core complexity and sequential iterations but reduces accuracy. Auxiliary logic limits sequential area/power savings.   # p.3,8
evidence: §3.2, §4.1, Fig. 2-4, Fig. 6-8, Table 3, Table 4, Table 7-8.

### approximate_recurrence  (role: extends)
mechanism: AXSR3 replaces exact subtractor cells at less-significant positions of a restoring array square-root circuit with approximate subtractor cell 3. The replacement depth selects the approximated portion. The design is evaluated primarily as a comparison against adaptive pruning.
choices:
  replaced_depth: 11, 12, 13, 14   # p.6
  cell: axsc3   # p.4,6
  radix: 2   # p.2,6
  adaptive_pruning: false   # p.6
new_choices:
  none
slots:
  none
parameters: 16-bit radicand; replacement depth 11-14   # p.6
results:
| metric | value | unit | technology / device | baseline | condition | page |
| EDmax | 12 | integer result units | UNKNOWN, 2019 | exact SQR | AXSR3-11 | p.6 |
| EDmax | 24 | integer result units | UNKNOWN, 2019 | exact SQR | AXSR3-12 | p.6 |
| EDmax | 24 | integer result units | UNKNOWN, 2019 | exact SQR | AXSR3-13 | p.6 |
| EDmax | 47 | integer result units | UNKNOWN, 2019 | exact SQR | AXSR3-14 | p.6 |
| delay | 4.04 | ns | ST 28 nm CMOS, 2019 | ESRr_A 4.32 ns | AXSR3-14 | p.7 |
| area | 168.3 | µm2 | ST 28 nm CMOS, 2019 | ESRr_A 222.4 µm2 | AXSR3-14 | p.7 |
| power | 53.31 | µW | ST 28 nm CMOS, 2019 | ESRr_A 93.82 µW | AXSR3-14 | p.7 |
errors_and_checks: AXSR3 has lower ER than AASR but larger EDmax; small inputs can have large relative error.   # p.6,10
conditions: Approximation of only less-significant subtractors yields limited delay/area/power reductions.   # p.2,11
evidence: §3.3, §5.1.2, Table 1-2, Fig. 8(b).

## new_families
### adaptive_pruned_sqrt  (domain: approx: approximate dividers, closest: approximate_recurrence, why_not: the mechanism prunes and rescales the radicand around its leading one and may use a LUT core rather than replacing recurrence cells)
mechanism: AASR detects the radicand’s leading-one position and retains a 2k-bit window, truncating redundant LSBs or appending zeros. An even leading-one position is increased by one so the scale exponent is integral. Any exact combinational or sequential 2k-bit square-root circuit computes the reduced result, which is shifted by (lA-2k+1)/2. The auxiliary path requires no adder/subtractor.
choices: pruned_radicand_width: Int[2..32:2]; core: {restoring_array, lut, sequential}; adaptive_leading_one_window: Bool
results:
| metric | value | unit | technology / device | baseline | condition | page |
| ER | 95.71 | % | UNKNOWN, 2019 | exact SQR | AASR-6, 16-bit | p.6 |
| NMED | 5.33 | % | UNKNOWN, 2019 | exact SQR | AASR-6, 16-bit | p.6 |
| MRED | 7.98 | % | UNKNOWN, 2019 | exact SQR | AASR-6, 16-bit | p.6 |
| EDmax | 31 | integer result units | UNKNOWN, 2019 | exact SQR | AASR-6, 16-bit | p.6 |
| delay | 1.10 | ns | ST 28 nm CMOS, 2019 | ESRr_A 4.32 ns | AASR_A-6 | p.7 |
| area | 76.5 | µm2 | ST 28 nm CMOS, 2019 | ESRr_A 222.4 µm2 | AASR_A-6 | p.7 |
| power | 19.38 | µW | ST 28 nm CMOS, 2019 | ESRr_A 93.82 µW | AASR_A-6 | p.7 |
| delay | 0.89 | ns | ST 28 nm CMOS, 2019 | ESRr_A 16.96 ns | AASR_T-6, 32-bit | p.11 |
| power | 4.99 | µW | ST 28 nm CMOS, 2019 | ESRr_A 99.00 µW | AASR_T-6, 32-bit | p.11 |
| TPA | 148,920 | ops/(s·µm2) | ST 28 nm CMOS, 2019 | ESRr_S 1,696 ops/(s·µm2) | AASR_S-6, 32-bit | p.11 |
evidence: §3.3, §4.2, Table 1-3, Table 5, Table 7-8.

## space_gaps
* approximate_functional lacks a slot for the reduced-width exact divider core and a choice for OR-gate overflow correction.   # p.3-4
* The vocabulary lacks an adaptive-pruning approximate square-root family that permits array/LUT/sequential exact cores.   # p.4,7-8

## open_questions
* The paper varies k between synthesized configurations rather than stating that k changes during operation, so runtime quality scaling is not established.
* The accepted-manuscript pagination differs from the final journal page range; references above use the manuscript’s printed pages 1-12.
