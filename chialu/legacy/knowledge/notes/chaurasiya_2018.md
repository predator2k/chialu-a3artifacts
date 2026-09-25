---
handle: chaurasiya_2018
citation: R. Chaurasiya, J. Gustafson, R. Shrestha, et al., "Parameterized Posit Arithmetic Hardware Generator", IEEE International Conference on Computer Design (ICCD), 2018
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [posit8, posit16, posit32, binary16, binary32]
authority: landmark
pages_read: 334-341 / 8
---

## summary
The document presents a parameterized generator for posit adders/subtractors and multipliers with configurable word size N and exponent size es. The generated units implement posit decoding/encoding, zero/NaR handling, normalization, and round-to-nearest-ties-to-even, and are evaluated with FPGA/ASIC synthesis and a four-tap FIR filter. # p.334, pp.336-341

## families
### posit_adder_multiplier  (role: proposes)
mechanism: The adder converts negative inputs to 2’s complement, decodes the variable-length regime with one leading-zero detector, extracts exponent/fraction fields, aligns significands by the net-scaling-factor difference, adds or subtracts them, normalizes the result, reconstructs the regime/exponent, and rounds through G/R/S bits. The multiplier adds operand scaling factors, multiplies significands, normalizes, bounds extreme regimes, and reuses the adder’s packing/rounding stages. # pp.336-339
choices:
  es_bits: 1, 2, 3, 4 [outside domain for 4] # pp.339-340
  regime_decode: lzc_plus_shifter # pp.336-338
  internal_representation: twos_complement # pp.336-338
  approximation: none # p.339
new_choices:
  word_size_N: positive integer — selects the generated posit width; synthesized examples use 8, 16, and 32 bits # pp.334,339-340
  rounding_mode: {round_to_zero, round_to_nearest_ties_to_even} — RZ supports comparison with [8], while RE implements posit unbiased rounding # p.339
slots:
  sig_datapath: UNKNOWN # pp.337-338
parameters: N is parameterized; synthesized PAUs use N={8,16,32} and es={1,2,3,4}; exhaustive verification uses (N=8, es=4); FPGA synthesis uses Zedboard/Zynq-7000 and Vivado 2017.4; ASIC synthesis uses 200 MHz. # pp.334,339-340
results:
| metric | value | unit | technology / device | baseline | condition | page |
| ASIC adder area | 2157.56 | μm2 | 90 nm CMOS Faraday, 2018 | [8]: 2472.43 μm2 | (8,1), 200 MHz | p.339 |
| ASIC adder power | 0.15 | mW | 90 nm CMOS Faraday, 2018 | [8]: 0.16 mW | (8,1), 200 MHz | p.339 |
| ASIC adder area | 2079.95 | μm2 | 90 nm CMOS Faraday, 2018 | [8]: 2436.67 μm2 | (8,2), 200 MHz | p.339 |
| ASIC adder power | 0.14 | mW | 90 nm CMOS Faraday, 2018 | [8]: 0.15 mW | (8,2), 200 MHz | p.339 |
| ASIC adder area | 6870.18 | μm2 | 90 nm CMOS Faraday, 2018 | [8]: 6366.86 μm2 | (16,1), 200 MHz | p.339 |
| ASIC adder power | 0.47 | mW | 90 nm CMOS Faraday, 2018 | [8]: 0.43 mW | (16,1), 200 MHz | p.339 |
| ASIC adder area | 6795.71 | μm2 | 90 nm CMOS Faraday, 2018 | [8]: 6210 μm2 | (16,2), 200 MHz | p.339 |
| ASIC adder power | 0.44 | mW | 90 nm CMOS Faraday, 2018 | [8]: 0.40 mW | (16,2), 200 MHz | p.339 |
| ASIC adder area | 19122.54 | μm2 | 90 nm CMOS Faraday, 2018 | [8]: 15360.12 μm2 | (32,1), 200 MHz | p.339 |
| ASIC adder power | 1.43 | mW | 90 nm CMOS Faraday, 2018 | [8]: 1.08 mW | (32,1), 200 MHz | p.339 |
| ASIC adder area | 18517 | μm2 | 90 nm CMOS Faraday, 2018 | [8]: 15471.45 μm2 | (32,2), 200 MHz | p.339 |
| ASIC adder power | 1.33 | mW | 90 nm CMOS Faraday, 2018 | [8]: 1.08 mW | (32,2), 200 MHz | p.339 |
| ASIC multiplier area | 1635.42 | μm2 | 90 nm CMOS Faraday, 2018 | [8]: 1917.66 μm2 | (8,1), 200 MHz | p.339 |
| ASIC multiplier power | 0.12 | mW | 90 nm CMOS Faraday, 2018 | [8]: 0.13 mW | (8,1), 200 MHz | p.339 |
| ASIC multiplier area | 1463.72 | μm2 | 90 nm CMOS Faraday, 2018 | [8]: 1923.15 μm2 | (8,2), 200 MHz | p.339 |
| ASIC multiplier power | 0.11 | mW | 90 nm CMOS Faraday, 2018 | [8]: 0.13 mW | (8,2), 200 MHz | p.339 |
| ASIC multiplier area | 7252.78 | μm2 | 90 nm CMOS Faraday, 2018 | [8]: 7767.08 μm2 | (16,1), 200 MHz | p.339 |
| ASIC multiplier power | 0.57 | mW | 90 nm CMOS Faraday, 2018 | [8]: 0.58 mW | (16,1), 200 MHz | p.339 |
| ASIC multiplier area | 6790.22 | μm2 | 90 nm CMOS Faraday, 2018 | [8]: 7218.28 μm2 | (16,2), 200 MHz | p.339 |
| ASIC multiplier power | 0.53 | mW | 90 nm CMOS Faraday, 2018 | [8]: 0.54 mW | (16,2), 200 MHz | p.339 |
| ASIC multiplier area | 28146.38 | μm2 | 90 nm CMOS Faraday, 2018 | [8]: 26054 μm2 | (32,1), 200 MHz | p.339 |
| ASIC multiplier power | 2.47 | mW | 90 nm CMOS Faraday, 2018 | [8]: 2.27 mW | (32,1), 200 MHz | p.339 |
| ASIC multiplier area | 27268.30 | μm2 | 90 nm CMOS Faraday, 2018 | [8]: 25338.09 μm2 | (32,2), 200 MHz | p.339 |
| ASIC multiplier power | 2.39 | mW | 90 nm CMOS Faraday, 2018 | [8]: UNKNOWN | (32,2), 200 MHz | p.339 |
| FPGA adder resources | 934 | Slice LUT | Zynq-7000/Vivado 2017.4, 2018 | binary32: 1049 Slice LUT | (32,1) | p.340 |
| FPGA adder delay | 38.041 | ns | Zynq-7000/Vivado 2017.4, 2018 | binary32: 41.576 ns | (32,1) | p.340 |
| FPGA multiplier resources | 576 | Slice LUT | Zynq-7000/Vivado 2017.4, 2018 | binary32: 533 Slice LUT | (32,1) | p.340 |
| FPGA multiplier DSP use | 4 | DSP | Zynq-7000/Vivado 2017.4, 2018 | binary32: 4 DSP | (32,1) | p.340 |
| FPGA multiplier delay | 31.013 | ns | Zynq-7000/Vivado 2017.4, 2018 | binary32: 29.051 ns | (32,1) | p.340 |
| FPGA adder resources | 981 | Slice LUT | Zynq-7000/Vivado 2017.4, 2018 | binary32: 1049 Slice LUT | (32,2) | p.340 |
| FPGA adder delay | 40.032 | ns | Zynq-7000/Vivado 2017.4, 2018 | binary32: 41.576 ns | (32,2) | p.340 |
| FPGA multiplier resources | 572 | Slice LUT | Zynq-7000/Vivado 2017.4, 2018 | binary32: 533 Slice LUT | (32,2) | p.340 |
| FPGA multiplier DSP use | 4 | DSP | Zynq-7000/Vivado 2017.4, 2018 | binary32: 4 DSP | (32,2) | p.340 |
| FPGA multiplier delay | 33.021 | ns | Zynq-7000/Vivado 2017.4, 2018 | binary32: 29.051 ns | (32,2) | p.340 |
| FPGA adder resources | 951 | Slice LUT | Zynq-7000/Vivado 2017.4, 2018 | binary32: 1049 Slice LUT | (32,3) | p.340 |
| FPGA adder delay | 39.254 | ns | Zynq-7000/Vivado 2017.4, 2018 | binary32: 41.576 ns | (32,3) | p.340 |
| FPGA multiplier resources | 582 | Slice LUT | Zynq-7000/Vivado 2017.4, 2018 | binary32: 533 Slice LUT | (32,3) | p.340 |
| FPGA multiplier DSP use | 4 | DSP | Zynq-7000/Vivado 2017.4, 2018 | binary32: 4 DSP | (32,3) | p.340 |
| FPGA multiplier delay | 32.263 | ns | Zynq-7000/Vivado 2017.4, 2018 | binary32: 29.051 ns | (32,3) | p.340 |
| FPGA adder resources | 955 | Slice LUT | Zynq-7000/Vivado 2017.4, 2018 | binary32: 1049 Slice LUT | (32,4) | p.340 |
| FPGA adder delay | 39.960 | ns | Zynq-7000/Vivado 2017.4, 2018 | binary32: 41.576 ns | (32,4) | p.340 |
| FPGA multiplier resources | 576 | Slice LUT | Zynq-7000/Vivado 2017.4, 2018 | binary32: 533 Slice LUT | (32,4) | p.340 |
| FPGA multiplier DSP use | 4 | DSP | Zynq-7000/Vivado 2017.4, 2018 | binary32: 4 DSP | (32,4) | p.340 |
| FPGA multiplier delay | 32.281 | ns | Zynq-7000/Vivado 2017.4, 2018 | binary32: 29.051 ns | (32,4) | p.340 |
| FPGA adder resources | 894 | Slice LUT | Zynq-7000/Vivado 2017.4, 2018 | binary32: 1049 Slice LUT | (31,3) | p.340 |
| FPGA adder delay | 39.964 | ns | Zynq-7000/Vivado 2017.4, 2018 | binary32: 41.576 ns | (31,3) | p.340 |
| FPGA multiplier resources | 560 | Slice LUT | Zynq-7000/Vivado 2017.4, 2018 | binary32: 533 Slice LUT | (31,3) | p.340 |
| FPGA multiplier DSP use | 4 | DSP | Zynq-7000/Vivado 2017.4, 2018 | binary32: 4 DSP | (31,3) | p.340 |
| FPGA multiplier delay | 31.927 | ns | Zynq-7000/Vivado 2017.4, 2018 | binary32: 29.051 ns | (31,3) | p.340 |
| FPGA adder resources | 873 | Slice LUT | Zynq-7000/Vivado 2017.4, 2018 | binary32: 1049 Slice LUT | (30,3) | p.340 |
| FPGA adder delay | 39.542 | ns | Zynq-7000/Vivado 2017.4, 2018 | binary32: 41.576 ns | (30,3) | p.340 |
| FPGA multiplier resources | 655 | Slice LUT | Zynq-7000/Vivado 2017.4, 2018 | binary32: 533 Slice LUT | (30,3) | p.340 |
| FPGA multiplier DSP use | 3 | DSP | Zynq-7000/Vivado 2017.4, 2018 | binary32: 4 DSP | (30,3) | p.340 |
| FPGA multiplier delay | 32.199 | ns | Zynq-7000/Vivado 2017.4, 2018 | binary32: 29.051 ns | (30,3) | p.340 |
| FPGA adder resources | 837 | Slice LUT | Zynq-7000/Vivado 2017.4, 2018 | binary32: 1049 Slice LUT | (29,3) | p.340 |
| FPGA adder delay | 39.748 | ns | Zynq-7000/Vivado 2017.4, 2018 | binary32: 41.576 ns | (29,3) | p.340 |
| FPGA multiplier resources | 464 | Slice LUT | Zynq-7000/Vivado 2017.4, 2018 | binary32: 533 Slice LUT | (29,3) | p.340 |
| FPGA multiplier DSP use | 2 | DSP | Zynq-7000/Vivado 2017.4, 2018 | binary32: 4 DSP | (29,3) | p.340 |
| FPGA multiplier delay | 29.496 | ns | Zynq-7000/Vivado 2017.4, 2018 | binary32: 29.051 ns | (29,3) | p.340 |
| FPGA adder resources | 821 | Slice LUT | Zynq-7000/Vivado 2017.4, 2018 | binary32: 1049 Slice LUT | (28,3) | p.340 |
| FPGA adder delay | 39.369 | ns | Zynq-7000/Vivado 2017.4, 2018 | binary32: 41.576 ns | (28,3) | p.340 |
| FPGA multiplier resources | 459 | Slice LUT | Zynq-7000/Vivado 2017.4, 2018 | binary32: 533 Slice LUT | (28,3) | p.340 |
| FPGA multiplier DSP use | 2 | DSP | Zynq-7000/Vivado 2017.4, 2018 | binary32: 4 DSP | (28,3) | p.340 |
| FPGA multiplier delay | 28.966 | ns | Zynq-7000/Vivado 2017.4, 2018 | binary32: 29.051 ns | (28,3) | p.340 |
| FPGA adder resources | 391 | Slice LUT | Zynq-7000/Vivado 2017.4, 2018 | binary16: 356 Slice LUT | (16,1) | p.340 |
| FPGA adder delay | 32.374 | ns | Zynq-7000/Vivado 2017.4, 2018 | binary16: 27.027 ns | (16,1) | p.340 |
| FPGA multiplier resources | 218 | Slice LUT | Zynq-7000/Vivado 2017.4, 2018 | binary16: 212 Slice LUT | (16,1) | p.340 |
| FPGA multiplier DSP use | 1 | DSP | Zynq-7000/Vivado 2017.4, 2018 | binary16: 1 DSP | (16,1) | p.340 |
| FPGA multiplier delay | 24.041 | ns | Zynq-7000/Vivado 2017.4, 2018 | binary16: 21.379 ns | (16,1) | p.340 |
| FPGA adder resources | 404 | Slice LUT | Zynq-7000/Vivado 2017.4, 2018 | binary16: 356 Slice LUT | (16,2) | p.340 |
| FPGA adder delay | 33.974 | ns | Zynq-7000/Vivado 2017.4, 2018 | binary16: 27.027 ns | (16,2) | p.340 |
| FPGA multiplier resources | 223 | Slice LUT | Zynq-7000/Vivado 2017.4, 2018 | binary16: 212 Slice LUT | (16,2) | p.340 |
| FPGA multiplier DSP use | 1 | DSP | Zynq-7000/Vivado 2017.4, 2018 | binary16: 1 DSP | (16,2) | p.340 |
| FPGA multiplier delay | 23.680 | ns | Zynq-7000/Vivado 2017.4, 2018 | binary16: 21.379 ns | (16,2) | p.340 |
| FPGA adder resources | 386 | Slice LUT | Zynq-7000/Vivado 2017.4, 2018 | binary16: 356 Slice LUT | (16,3) | p.340 |
| FPGA adder delay | 32.466 | ns | Zynq-7000/Vivado 2017.4, 2018 | binary16: 27.027 ns | (16,3) | p.340 |
| FPGA multiplier resources | 219 | Slice LUT | Zynq-7000/Vivado 2017.4, 2018 | binary16: 212 Slice LUT | (16,3) | p.340 |
| FPGA multiplier DSP use | 1 | DSP | Zynq-7000/Vivado 2017.4, 2018 | binary16: 1 DSP | (16,3) | p.340 |
| FPGA multiplier delay | 24.078 | ns | Zynq-7000/Vivado 2017.4, 2018 | binary16: 21.379 ns | (16,3) | p.340 |
| FPGA adder resources | 371 | Slice LUT | Zynq-7000/Vivado 2017.4, 2018 | binary16: 356 Slice LUT | (16,4) | p.340 |
| FPGA adder delay | 33.079 | ns | Zynq-7000/Vivado 2017.4, 2018 | binary16: 27.027 ns | (16,4) | p.340 |
| FPGA multiplier resources | 233 | Slice LUT | Zynq-7000/Vivado 2017.4, 2018 | binary16: 212 Slice LUT | (16,4) | p.340 |
| FPGA multiplier DSP use | 1 | DSP | Zynq-7000/Vivado 2017.4, 2018 | binary16: 1 DSP | (16,4) | p.340 |
| FPGA multiplier delay | 24.581 | ns | Zynq-7000/Vivado 2017.4, 2018 | binary16: 21.379 ns | (16,4) | p.340 |
| FPGA adder resources | 382 | Slice LUT | Zynq-7000/Vivado 2017.4, 2018 | binary16: 356 Slice LUT | (15,1) | p.340 |
| FPGA adder delay | 30.416 | ns | Zynq-7000/Vivado 2017.4, 2018 | binary16: 27.027 ns | (15,1) | p.340 |
| FPGA multiplier resources | 207 | Slice LUT | Zynq-7000/Vivado 2017.4, 2018 | binary16: 212 Slice LUT | (15,1) | p.340 |
| FPGA multiplier DSP use | 1 | DSP | Zynq-7000/Vivado 2017.4, 2018 | binary16: 1 DSP | (15,1) | p.340 |
| FPGA multiplier delay | 23.848 | ns | Zynq-7000/Vivado 2017.4, 2018 | binary16: 21.379 ns | (15,1) | p.340 |
| FPGA adder resources | 353 | Slice LUT | Zynq-7000/Vivado 2017.4, 2018 | binary16: 356 Slice LUT | (14,1) | p.340 |
| FPGA adder delay | 29.835 | ns | Zynq-7000/Vivado 2017.4, 2018 | binary16: 27.027 ns | (14,1) | p.340 |
| FPGA multiplier resources | 184 | Slice LUT | Zynq-7000/Vivado 2017.4, 2018 | binary16: 212 Slice LUT | (14,1) | p.340 |
| FPGA multiplier DSP use | 1 | DSP | Zynq-7000/Vivado 2017.4, 2018 | binary16: 1 DSP | (14,1) | p.340 |
| FPGA multiplier delay | 23.282 | ns | Zynq-7000/Vivado 2017.4, 2018 | binary16: 21.379 ns | (14,1) | p.340 |
| FPGA adder resources | 290 | Slice LUT | Zynq-7000/Vivado 2017.4, 2018 | binary16: 356 Slice LUT | (13,1) | p.340 |
| FPGA adder delay | 28.420 | ns | Zynq-7000/Vivado 2017.4, 2018 | binary16: 27.027 ns | (13,1) | p.340 |
| FPGA multiplier resources | 181 | Slice LUT | Zynq-7000/Vivado 2017.4, 2018 | binary16: 212 Slice LUT | (13,1) | p.340 |
| FPGA multiplier DSP use | 1 | DSP | Zynq-7000/Vivado 2017.4, 2018 | binary16: 1 DSP | (13,1) | p.340 |
| FPGA multiplier delay | 23.445 | ns | Zynq-7000/Vivado 2017.4, 2018 | binary16: 21.379 ns | (13,1) | p.340 |
| FPGA adder resources | 254 | Slice LUT | Zynq-7000/Vivado 2017.4, 2018 | binary16: 356 Slice LUT | (12,1) | p.340 |
| FPGA adder delay | 28.549 | ns | Zynq-7000/Vivado 2017.4, 2018 | binary16: 27.027 ns | (12,1) | p.340 |
| FPGA multiplier resources | 167 | Slice LUT | Zynq-7000/Vivado 2017.4, 2018 | binary16: 212 Slice LUT | (12,1) | p.340 |
| FPGA multiplier DSP use | 0 | DSP | Zynq-7000/Vivado 2017.4, 2018 | binary16: 1 DSP | (12,1) | p.340 |
| FPGA multiplier delay | 21.142 | ns | Zynq-7000/Vivado 2017.4, 2018 | binary16: 21.379 ns | (12,1) | p.340 |
errors_and_checks: Exhaustive simulation of the (N=8, es=4) adder and multiplier with unbiased rounding exactly matches the Julia package for every input combination. The FIR examples report proposed-work relative errors of 0 for most listed inputs, 0.0434782608695652 for one input, and 0.0847457627118644 for another. # pp.339,341
conditions: Posit maximum fraction accuracy applies from 1/useed to useed and decreases by one bit for each further factor of useed in magnitude. # pp.339-340 Posit resource use is comparable to IEEE floating point at m=n and is lower in the reported m<n comparisons. # p.340 The proposed ASIC units outperform [8] at small widths, while the document states that larger units could obtain similar performance through pipelining. # p.339 The RE adder has more FPGA datapath delay than [8] because unbiased rounding adds a module; the RZ multiplier has lower delay, while the RE multiplier has similar delay. # p.339
evidence: Fig. 2 and Algorithms 1-5, pp.336-339; Fig. 3 and Tables III-IV, pp.339-340; Tables V-VII, pp.340-341.

## new_families
none

## space_gaps
* The posit_adder_multiplier family needs a multiplier-core slot because the document implements a separate significand multiplication datapath whose implementation family is not represented by sig_datapath. # p.338
* The es_bits domain excludes es=4, which is synthesized for posit16/posit32 and used for exhaustive verification with posit8. # pp.339-340
* The vocabulary lacks word size and rounding-mode choices, although N and RZ/RE are explicit generator configurations. # pp.334,339

## open_questions
* The document does not identify the carry-propagate adder family used for significand addition.
* The document does not identify the integer multiplier family inferred for significand multiplication.
* Tables III-V do not explicitly identify whether each proposed synthesis result uses RZ or unbiased rounding.
