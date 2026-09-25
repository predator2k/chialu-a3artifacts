---
handle: momeni2015
citation: A. Momeni, J. Han, P. Montuschi, F. Lombardi, "Design and Analysis of Approximate Compressors for Multiplication", IEEE Transactions on Computers, vol. 64, no. 4, pp. 984-994, 2015
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [uint8]
authority: landmark
pages_read: 11 / 11
---

## summary
The paper proposes two approximate 4-2 compressors and four 8×8 unsigned Dadda multipliers that place these compressors in all or only the least-significant reduction columns. Design 2 removes cin/cout and reduces compressor error rate, delay, power, and transistor count, while Multipliers 3/4 retain exact compressors in the most-significant columns to reduce error. Circuit simulations use 32 nm, 22 nm, and 16 nm CMOS models, and image-multiplication experiments report NED and PSNR.

## families
### approximate_compressor_tree  (role: proposes)
mechanism: Design 1 approximates a 4-2 compressor by simplifying carry to cin and simplifying sum/cout to reduce error distance and logic complexity. Design 2 interchanges carry/cout behavior, makes cout equal to cin, and removes both cin and cout because cin is zero in the first reduction stage. Four Dadda schemes use Design 1 or Design 2 either throughout the reduction tree or only in the n-1 least-significant columns, with exact compressors in the n most-significant columns. An exact CPA produces the final result. # p.3-6
choices:
  approximate_columns: all [outside domain] (Multipliers 1/2); n-1 [outside domain] (Multipliers 3/4)   # p.5-6
  compressor: momeni_d1_d2   # p.3-5
  error_recovery: none   # p.3-7
  dual_quality_runtime: false   # p.3-6
new_choices:
  carry_interface: {retained, eliminated} — Design 1 retains cin/cout, while Design 2 eliminates both signals.   # p.3-4
slots:
  none
parameters: approximate 4-2 compressors; 8×8 unsigned Dadda multiplier; two reduction stages; Multiplier 1 uses Design 1 throughout; Multiplier 2 uses Design 2 throughout; Multiplier 3 uses Design 1 in n-1 LSB columns; Multiplier 4 uses Design 2 in n-1 LSB columns; exact CPA; compressor simulations at 1 GHz and fan-out 4   # p.5-6
results:
| metric | value | unit | technology / device | baseline | condition | page |
| delay / power / PDP | 60.36 / 2.98 / 180 | ps / μW / aJ | 32 nm CMOS / 2015 | exact compressor [8] | exact | p.6 |
| delay / power / PDP | 58.32 / 1.27 / 74 | ps / μW / aJ | 32 nm CMOS / 2015 | exact compressor [8] | Design 1 | p.6 |
| delay / power / PDP | 44.35 / 1.14 / 50 | ps / μW / aJ | 32 nm CMOS / 2015 | exact compressor [8] | Design 2 | p.6 |
| delay / power / PDP | 55.82 / 1.50 / 84 | ps / μW / aJ | 22 nm CMOS / 2015 | exact compressor [8] | exact | p.6 |
| delay / power / PDP | 56.79 / 0.62 / 35 | ps / μW / aJ | 22 nm CMOS / 2015 | exact compressor [8] | Design 1 | p.6 |
| delay / power / PDP | 41.69 / 0.58 / 24 | ps / μW / aJ | 22 nm CMOS / 2015 | exact compressor [8] | Design 2 | p.6 |
| delay / power / PDP | 47.59 / 0.95 / 45 | ps / μW / aJ | 16 nm CMOS / 2015 | exact compressor [8] | exact | p.6 |
| delay / power / PDP | 37.16 / 0.39 / 14 | ps / μW / aJ | 16 nm CMOS / 2015 | exact compressor [8] | Design 1 | p.6 |
| delay / power / PDP | 24.44 / 0.36 / 9 | ps / μW / aJ | 16 nm CMOS / 2015 | exact compressor [8] | Design 2 | p.6 |
| transistor count | 52 | transistors | CMOS / 2015 | exact compressor [8] | exact | p.6 |
| transistor count | 28 | transistors | CMOS / 2015 | exact compressor [8] | Design 1 | p.6 |
| transistor count | 26 | transistors | CMOS / 2015 | exact compressor [8] | Design 2 | p.6 |
| delay / power / transistor improvement | 3.38 / 52.49 / 42.11 | % / % / % | 32 nm CMOS / 2015 | exact Dadda reduction circuitry | Multiplier 1 | p.6-7 |
| delay / power / transistor improvement | 26.52 / 58.58 / 48.15 | % / % / % | 32 nm CMOS / 2015 | exact Dadda reduction circuitry | Multiplier 2 | p.6-7 |
| delay / power / transistor improvement | 0 / 17.50 / 14.03 | % / % / % | 32 nm CMOS / 2015 | exact Dadda reduction circuitry | Multiplier 3 | p.6-7 |
| delay / power / transistor improvement | 0 / 26.15 / 22.42 | % / % / % | 32 nm CMOS / 2015 | exact Dadda reduction circuitry | Multiplier 4 | p.6-7 |
| average NED / max high NED / max low NED / correct outputs | 0.6065×10-1 / 0.1593 / 0.1375 / 103 out of 65025 | ratio / ratio / ratio / outputs | UNKNOWN / 2015 | exact multiplication | Multiplier 1 | p.7 |
| average NED / max high NED / max low NED / correct outputs | 0.5352×10-1 / 0.1278 / 0.1329 / 458 out of 65025 | ratio / ratio / ratio / outputs | UNKNOWN / 2015 | exact multiplication | Multiplier 2 | p.7 |
| average NED / max high NED / max low NED / correct outputs | 0.9199×10-3 / 0.3199×10-2 / 0.2707×10-2 / 5888 out of 65025 | ratio / ratio / ratio / outputs | UNKNOWN / 2015 | exact multiplication | Multiplier 3 | p.7 |
| average NED / max high NED / max low NED / correct outputs | 0.7827×10-3 / 0.1845×10-2 / 0.3076×10-2 / 9320 out of 65025 | ratio / ratio / ratio / outputs | UNKNOWN / 2015 | exact multiplication | Multiplier 4 | p.7 |
| PSNR / average NED | 25.3 / 4.4×10-2 | dB / ratio | Microsoft Visual Studio 2010 / 2015 | exact image multiplication | Multiplier 1, example 1 | p.9 |
| PSNR / average NED | 26.3 / 3.7×10-2 | dB / ratio | Microsoft Visual Studio 2010 / 2015 | exact image multiplication | Multiplier 2, example 1 | p.9 |
| PSNR / average NED | 53.9 / 0.10×10-2 | dB / ratio | Microsoft Visual Studio 2010 / 2015 | exact image multiplication | Multiplier 3, example 1 | p.9 |
| PSNR / average NED | 53.2 / 0.12×10-2 | dB / ratio | Microsoft Visual Studio 2010 / 2015 | exact image multiplication | Multiplier 4, example 1 | p.9 |
| PSNR / average NED | 25.1 / 4.5×10-2 | dB / ratio | Microsoft Visual Studio 2010 / 2015 | exact image multiplication | Multiplier 1, example 2 | p.9 |
| PSNR / average NED | 25.8 / 4.1×10-2 | dB / ratio | Microsoft Visual Studio 2010 / 2015 | exact image multiplication | Multiplier 2, example 2 | p.9 |
| PSNR / average NED | 54.2 / 0.096×10-2 | dB / ratio | Microsoft Visual Studio 2010 / 2015 | exact image multiplication | Multiplier 3, example 2 | p.9 |
| PSNR / average NED | 54.9 / 0.083×10-2 | dB / ratio | Microsoft Visual Studio 2010 / 2015 | exact image multiplication | Multiplier 4, example 2 | p.9 |
errors_and_checks: Design 1 has 12 incorrect outputs out of 32 and an error rate of 37.5%; Design 2 has 4 incorrect outputs out of 16 and an error rate of 25%. NED is the absolute error distance normalized by the maximum possible error. The evaluated multipliers omit zero-valued operand cases because the compressors err on all-zero patterns; a zero-input detector can restore correct zero products. No error indicator is provided.   # p.4-5, p.7, p.10
conditions: Multipliers 1/2 reduce delay/power/transistor count but have larger error distances. Multipliers 3/4 reduce power/transistor count and error distance, but exact compressors on the critical path eliminate delay improvement. Image pixels with very high or very low RGB values incur larger inaccuracies. The designs apply to error-tolerant computation.   # p.6-7, p.9-10
evidence: §III, Tables II-III, Figures 6-8; §IV, Figure 9; §V, Tables IV-X and Figure 10; §VI, Tables XI-XII and Figures 11-13; §VII, Table XIII.

## new_families
none

## space_gaps
* `approximate_columns` cannot represent the document's `all` or `n-1` placement policies. # p.5-6
* `carry_interface` is needed to distinguish Design 1's retained cin/cout from Design 2's eliminated cin/cout. # p.3-4
* The vocabulary lacks a choice for placing approximate and exact compressor cells by partial-product-column significance. # p.5-6

## open_questions
* The exact CPA topology used for the final binary result is not specified. # p.5
* The physical-layout behavior of the proposed multipliers is not established because physical designs are future work. # p.9
* The provision and behavior of an error indicator are not established because the paper identifies the indicator as future work. # p.10
