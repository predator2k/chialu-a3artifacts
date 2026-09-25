---
handle: rathor_2024
citation: M. Rathor, "ALOHA-FP2I: Efficient Algorithms and Hardware for Multi-Mode Rounding of Floating Point to Integer", ACM Transactions on Embedded Computing Systems, 2024
actual_citation: same
status: ok
kind: paper
unit_classes: [other]
formats: [fp32, fp64, fp128]
authority: incremental
pages_read: 26 / 26
---

## summary
The paper proposes combinational hardware that rounds binary floating-point inputs to integral values retained in floating-point format using a mantissa bit of rounding (MBR) selected from the exponent. Five individual modes and an integrated multi-mode rounding (IMR) design cover fp32/fp64, with an algorithmic extension to fp128. # p.4, p.6, p.12-15

## families
none

## new_families
### fp_round_to_integral  (domain: fp: format converters, closest: shift_round_convert, why_not: shift_round_convert produces an integer/fixed-point format, whereas this mechanism retains floating-point representation)
mechanism: The exponent identifies the relevant integer range and the MBR position. The MBR and mantissa field of interest determine whether retained exponent/mantissa bits are truncated or incremented. Round-up/down additionally OR-reduce discarded bits and condition the increment on the sign. Round-to-even examines the bit preceding the MBR. IMR shares these paths through multiplexers selected by S[2:0]. # p.5-14
choices:
  rounding_mode: {towards_zero, towards_positive_infinity, towards_negative_infinity, nearest_away_from_zero, nearest_even} # p.4
  precision: {binary32, binary64, binary128} # p.4, p.13-15
  implementation: {individual, integrated_multimode} # p.4, p.12-14
  rounding_locator: {mantissa_bit_of_rounding} # p.6-7
  output_representation: {integer_value_in_floating_point_format} # p.2-4
  mode_selection: {fixed, S[2:0]} # p.12-14
results:
| metric | value | unit | technology / device | baseline | condition | page |
| FPGA logic elements | 128 | logic elements | Intel Cyclone II FPGA (2024) | none | fp32, towards zero | p.16 |
| FPGA logic elements | 988 | logic elements | Intel Cyclone II FPGA (2024) | none | fp32, nearest | p.16 |
| FPGA logic elements | 1,109 | logic elements | Intel Cyclone II FPGA (2024) | none | fp32, up | p.16 |
| FPGA logic elements | 1,110 | logic elements | Intel Cyclone II FPGA (2024) | none | fp32, down | p.16 |
| FPGA logic elements | 1,015 | logic elements | Intel Cyclone II FPGA (2024) | none | fp32, even | p.16 |
| FPGA logic elements | 376 | logic elements | Intel Cyclone II FPGA (2024) | none | fp64, towards zero | p.16 |
| FPGA logic elements | 4,515 | logic elements | Intel Cyclone II FPGA (2024) | none | fp64, nearest | p.16 |
| FPGA logic elements | 5,077 | logic elements | Intel Cyclone II FPGA (2024) | none | fp64, up | p.16 |
| FPGA logic elements | 5,079 | logic elements | Intel Cyclone II FPGA (2024) | none | fp64, down | p.16 |
| FPGA logic elements | 4,634 | logic elements | Intel Cyclone II FPGA (2024) | none | fp64, even | p.16 |
| worst-case delay, RR/RF/FR/FF | 13.45/13.66/13.66/13.45 | ns | Intel Cyclone II FPGA (2024) | none | fp32, towards zero | p.16 |
| worst-case delay, RR/RF/FR/FF | 19.13/19.13/19.13/19.13 | ns | Intel Cyclone II FPGA (2024) | none | fp32, nearest | p.16 |
| worst-case delay, RR/RF/FR/FF | 23.43/23.15/23.15/23.43 | ns | Intel Cyclone II FPGA (2024) | none | fp32, up | p.16 |
| worst-case delay, RR/RF/FR/FF | 23.92/26.40/26.40/23.93 | ns | Intel Cyclone II FPGA (2024) | none | fp32, down | p.16 |
| worst-case delay, RR/RF/FR/FF | 19.27/19.27/19.27/19.27 | ns | Intel Cyclone II FPGA (2024) | none | fp32, even | p.16 |
| worst-case delay, RR/RF/FR/FF | 15.31/15.81/15.81/15.31 | ns | Intel Cyclone II FPGA (2024) | none | fp64, towards zero | p.16 |
| worst-case delay, RR/RF/FR/FF | 27.18/27.18/27.18/27.18 | ns | Intel Cyclone II FPGA (2024) | none | fp64, nearest | p.16 |
| worst-case delay, RR/RF/FR/FF | 40.45/40.45/40.45/40.45 | ns | Intel Cyclone II FPGA (2024) | none | fp64, up | p.16 |
| worst-case delay, RR/RF/FR/FF | 42.56/44.47/44.47/42.56 | ns | Intel Cyclone II FPGA (2024) | none | fp64, down | p.16 |
| worst-case delay, RR/RF/FR/FF | 26.13/26.13/26.13/26.13 | ns | Intel Cyclone II FPGA (2024) | none | fp64, even | p.16 |
| power dissipation | 200.68 | mW | Intel Cyclone II FPGA (2024) | none | fp32, towards zero | p.17 |
| power dissipation | 200.72 | mW | Intel Cyclone II FPGA (2024) | none | fp32, nearest | p.17 |
| power dissipation | 200.71 | mW | Intel Cyclone II FPGA (2024) | none | fp32, up | p.17 |
| power dissipation | 200.89 | mW | Intel Cyclone II FPGA (2024) | none | fp32, down | p.17 |
| power dissipation | 200.61 | mW | Intel Cyclone II FPGA (2024) | none | fp32, even | p.17 |
| power dissipation | 208.18 | mW | Intel Cyclone II FPGA (2024) | none | fp64, towards zero | p.17 |
| power dissipation | 208.07 | mW | Intel Cyclone II FPGA (2024) | none | fp64, nearest | p.17 |
| power dissipation | 208.73 | mW | Intel Cyclone II FPGA (2024) | none | fp64, up | p.17 |
| power dissipation | 208.24 | mW | Intel Cyclone II FPGA (2024) | none | fp64, down | p.17 |
| power dissipation | 208.83 | mW | Intel Cyclone II FPGA (2024) | none | fp64, even | p.17 |
| IMR area | 1,760 | LUTs | Intel Cyclone II FPGA (2024) | 4,350 LUTs, five individual designs | fp32, five modes | p.17 |
| IMR area reduction | ×2.47 reduction | UNKNOWN | Intel Cyclone II FPGA (2024) | five individual designs | fp32, five modes | p.17 |
| IMR propagation delay | 28.305 | ns | Intel Cyclone II FPGA (2024) | 26.400 ns, individual designs | 7.2% increase | p.17 |
| IMR power | 201.17 | mW | Intel Cyclone II FPGA (2024) | 200.89 mW, individual designs | 0.1% increase | p.17 |
| compression integration overhead | 0.90% | percent | Intel Cyclone II FPGA (2024) | 36,194-LUT compression processor | nearest | p.18 |
| compression integration overhead | 0.98% | percent | Intel Cyclone II FPGA (2024) | 36,194-LUT compression processor | up/down | p.18 |
| compression integration overhead | 0.92% | percent | Intel Cyclone II FPGA (2024) | 36,194-LUT compression processor | even | p.18 |
| compression integration overhead | 0.03% | percent | Intel Cyclone II FPGA (2024) | 36,194-LUT compression processor | towards zero | p.18 |
| JPEG PSNR | 18.3632 | UNKNOWN | MATLAB 2021a, 8 GB RAM (2024) | original Lena image | QF=50, nearest | p.18-19 |
| JPEG PSNR | 15.5849 | UNKNOWN | MATLAB 2021a, 8 GB RAM (2024) | original Lena image | QF=50, up | p.18-19 |
| JPEG PSNR | 15.5914 | UNKNOWN | MATLAB 2021a, 8 GB RAM (2024) | original Lena image | QF=50, down | p.18-19 |
| JPEG PSNR | 18.5482 | UNKNOWN | MATLAB 2021a, 8 GB RAM (2024) | original Lena image | QF=50, towards zero | p.18-19 |
| JPEG PSNR | 18.3630 | UNKNOWN | MATLAB 2021a, 8 GB RAM (2024) | original Lena image | QF=50, even | p.18-19 |
| ASIC area | 5,327.14 | μm2 | 15 nm open cell library (2024) | [26]: 1,784.41 μm2 | IMR versus nearest-only binary FP | p.20 |
| ASIC propagation delay | 716.82 | ps | 15 nm open cell library (2024) | [26]: 602.07 ps | IMR versus nearest-only binary FP | p.20 |
| ASIC static power | 219.49 | μW | 15 nm open cell library (2024) | [26]: 62.33 μW | IMR versus nearest-only binary FP | p.20 |
| comparative area | 2,09,713.0 | μm2 | 65 nm (2011) | proposed IMR | [25], five-mode decimal FP | p.20 |
| comparative delay | 2,240 | ps | 65 nm (2011) | proposed IMR | [25], five-mode decimal FP | p.20 |
errors_and_checks: Zero/NaN/+−INF pass through unchanged. Quartus simulation functionally validated all five FPGA implementations, but the paper reports no test coverage or numerical-error count. # p.12, p.16
conditions: The output is an integral value in floating-point format; fixed-point output requires separate conversion hardware. Individual mode hardware saves area/power/latency for fixed-mode applications, while IMR shares logic for selectable general-purpose use. fp128 is described as an extension rather than an implementation. # p.2-4, p.13-15
evidence: Tables 1-12; Figures 1-4 and A.1-A.4; Sections 2-4, p.4-25.

## space_gaps
* The vocabulary lacks a standalone binary floating-point round-to-integral family whose result remains in floating-point format. # p.2-4
* The `round` component slots lack an MBR/multiplexer-based implementation family. # p.6-14
* The five-mode domain needs `nearest_away_from_zero` in addition to IEEE nearest-even behavior. # p.4-5

## open_questions
* The Cyclone II device part number and FPGA technology node are not reported. # p.16
* The functional-validation input coverage is not reported. # p.16
* The fp128 extension is not implemented or measured. # p.13-15
