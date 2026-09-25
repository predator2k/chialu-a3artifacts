---
handle: babic2011
citation: Z. Babic, A. Avramovic, P. Bulic, "An Iterative Logarithmic Multiplier", Microprocessors and Microsystems, vol. 35, no. 1, pp. 23-33, 2011
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [uint8, uint12, uint16]
authority: incremental
pages_read: 23-33 / 11
---

## summary
The paper proposes an unsigned binary logarithmic multiplier that iteratively approximates the residual product until the requested accuracy or an exact result is reached. Cascaded/pipelined correction blocks allow one result per clock after the initial latency. Spartan-3 implementations compare area/frequency/power and errors for zero through three correction circuits.

## families
### logarithmic  (role: extends)
mechanism: Each operand is decomposed as \(N=2^k+(N-2^k)\). A basic block adds \(2^{k1+k2}\), \((N1-2^{k1})2^{k2}\), and \((N2-2^{k2})2^{k1}\); the discarded residual product becomes the next correction input. Cascaded basic blocks repeat this calculation until the selected correction count is reached or one residual becomes zero. The method omits Mitchell’s \(x1+x2\) comparison, so a correction block starts when the preceding block produces its residues. A four-stage pipeline overlaps the cascaded blocks. # pp.25-30
choices:
  base: mitchell   # pp.24-25
  correction: iterative_residual   # pp.25-26
  iterations: 1-6 [outside domain]   # pp.26,31
  mantissa_adder: exact   # pp.27-29
new_choices:
  pipeline_stages_per_basic_block: 4 — partitions characteristic/residue generation, shifting, decoding/partial addition, and final addition   # pp.28-29
slots:
  log_adder: UNKNOWN   # pp.27-29
parameters: 8/12/16-bit unsigned operands; 16-bit FPGA implementations; 0-3 implemented correction circuits; 4 pipeline stages per basic block; BB + 2 ECC initial latency 6 clock periods; II=1 after initial latency   # pp.27-31
results:
| metric | value | unit | technology / device | baseline | condition | page |
| device utilization | 533 / 276 / 64 / 99 | LUTs / slices / FFs / IOBs | Xilinx Spartan-3 xc3s1500-5fg676 / 2011 | MA/OD-MA set | BB, non-pipelined | p.30 |
| device utilization | 1099 / 564 / 80 / 99 | LUTs / slices / FFs / IOBs | Xilinx Spartan-3 xc3s1500-5fg676 / 2011 | MA/OD-MA set | BB + 1 ECC, non-pipelined | p.30 |
| device utilization | 1596 / 814 / 77 / 99 | LUTs / slices / FFs / IOBs | Xilinx Spartan-3 xc3s1500-5fg676 / 2011 | MA/OD-MA set | BB + 2 ECC, non-pipelined | p.30 |
| device utilization | 1937 / 993 / 78 / 99 | LUTs / slices / FFs / IOBs | Xilinx Spartan-3 xc3s1500-5fg676 / 2011 | MA/OD-MA set | BB + 3 ECC, non-pipelined | p.30 |
| device utilization | 404 / 216 / 170 / 99 | LUTs / slices / FFs / IOBs | Xilinx Spartan-3 xc3s1500-5fg676 / 2011 | non-pipelined BB | BB, pipelined | p.30 |
| device utilization | 803 / 427 / 306 / 99 | LUTs / slices / FFs / IOBs | Xilinx Spartan-3 xc3s1500-5fg676 / 2011 | non-pipelined BB + 1 ECC | BB + 1 ECC, pipelined | p.30 |
| device utilization | 1189 / 635 / 440 / 99 | LUTs / slices / FFs / IOBs | Xilinx Spartan-3 xc3s1500-5fg676 / 2011 | non-pipelined BB + 2 ECC | BB + 2 ECC, pipelined | p.30 |
| device utilization | 1546 / 824 / 569 / 99 | LUTs / slices / FFs / IOBs | Xilinx Spartan-3 xc3s1500-5fg676 / 2011 | non-pipelined BB + 3 ECC | BB + 3 ECC, pipelined | p.30 |
| maximum frequency | 58.075 / 153.335 | MHz | Xilinx Spartan-3 xc3s1500-5fg676 / 2011 | non-pipelined / pipelined | BB | p.30 |
| maximum frequency | 50.180 / 153.335 | MHz | Xilinx Spartan-3 xc3s1500-5fg676 / 2011 | non-pipelined / pipelined | BB + 1 ECC | p.30 |
| maximum frequency | 41.429 / 153.335 | MHz | Xilinx Spartan-3 xc3s1500-5fg676 / 2011 | non-pipelined / pipelined | BB + 2 ECC | p.30 |
| maximum frequency | 37.826 / 153.335 | MHz | Xilinx Spartan-3 xc3s1500-5fg676 / 2011 | non-pipelined / pipelined | BB + 3 ECC | p.30 |
| power: logic+signals / IOB / quiescent / total | 3.05 / 45.69 / 151.29 / 200.02 | mW | Xilinx Spartan-3 xc3s1500-5fg676 / 2011 | MA: 5.15 / 45.68 / 151.29 / 202.12 | BB, non-pipelined, 25 MHz, 12.5% toggle | p.30 |
| power: logic+signals / IOB / quiescent / total | 5.3 / 45.69 / 151.31 / 202.3 | mW | Xilinx Spartan-3 xc3s1500-5fg676 / 2011 | OD-MA: 9.06 / 31.39 / 151.28 / 191.73 | BB + 1 ECC, non-pipelined, 25 MHz, 12.5% toggle | p.30 |
| power: logic+signals / IOB / quiescent / total | 8.25 / 46.63 / 151.38 / 206.25 | mW | Xilinx Spartan-3 xc3s1500-5fg676 / 2011 | BB | BB + 2 ECC, non-pipelined, 25 MHz, 12.5% toggle | p.30 |
| power: logic+signals / IOB / quiescent / total | 10.15 / 48.8 / 151.44 / 210.39 | mW | Xilinx Spartan-3 xc3s1500-5fg676 / 2011 | BB | BB + 3 ECC, non-pipelined, 25 MHz, 12.5% toggle | p.30 |
| power: logic+signals / IOB / quiescent / total | 3.72 / 51.26 / 152.06 / 207.04 | mW | Xilinx Spartan-3 xc3s1500-5fg676 / 2011 | non-pipelined BB | BB, pipelined, 25 MHz | p.31 |
| power: logic+signals / IOB / quiescent / total | 7.32 / 51.62 / 152.66 / 211.6 | mW | Xilinx Spartan-3 xc3s1500-5fg676 / 2011 | pipelined BB | BB + 1 ECC, pipelined, 25 MHz | p.31 |
| power: logic+signals / IOB / quiescent / total | 10.66 / 51.67 / 153.03 / 215.36 | mW | Xilinx Spartan-3 xc3s1500-5fg676 / 2011 | pipelined BB | BB + 2 ECC, pipelined, 25 MHz | p.31 |
| power: logic+signals / IOB / quiescent / total | 13.37 / 51.93 / 153.42 / 218.72 | mW | Xilinx Spartan-3 xc3s1500-5fg676 / 2011 | pipelined BB | BB + 3 ECC, pipelined, 25 MHz | p.31 |
| maximum relative error, ECCs 0/1/2/3/4/5 | 25.0 / 6.25 / 1.56 / 0.39 / 0.097 / 0.024 | % | algorithmic / 2011 | exact multiplication | worst case | p.31 |
| average relative error, ECCs 0/1/2/3 | 8.9131 / 0.8337 / 0.0708 / 0.0048 | % | exhaustive simulation / 2011 | exact multiplication | 8-bit operands | p.31 |
| average relative error, ECCs 0/1/2/3 | 9.3692 / 0.9726 / 0.1029 / 0.0106 | % | exhaustive simulation / 2011 | exact multiplication | 12-bit operands | p.31 |
| average relative error, ECCs 0/1/2/3 | 9.4124 / 0.9874 / 0.1070 / 0.0117 | % | exhaustive simulation / 2011 | exact multiplication | 16-bit operands | p.31 |
| error rates below 0.1% / 0.5% / 1% | 32.9 / 54.8 / 69.9; 79.9 / 96.9 / 99.6; 99.0 / 100 / 100 | % | exhaustive simulation / 2011 | exact multiplication | 8-bit, 1/2/3 ECC | p.31 |
| error rates below 0.1% / 0.5% / 1% | 20.6 / 48.1 / 65.6; 71.6 / 95.7 / 99.4; 98.2 / 100 / 100 | % | exhaustive simulation / 2011 | exact multiplication | 12-bit, 1/2/3 ECC | p.31 |
| error rates below 0.1% / 0.5% / 1% | 19.3 / 47.4 / 65.2; 70.6 / 95.5 / 99.4; 98.0 / 100 / 100 | % | exhaustive simulation / 2011 | exact multiplication | 16-bit, 1/2/3 ECC | p.31 |
| TAE / false vectors / mismatching | 0.548 / 27 / 3.99 | % / count / % | block-matching simulation / 2011 | exact multiplication | 32 × 32 region, 1 ECC, B=676 | p.32 |
| TAE / false vectors / mismatching | 0.034 / 1 / 0.15 | % / count / % | block-matching simulation / 2011 | exact multiplication | 32 × 32 region, 2 ECC, B=676 | p.32 |
| TAE / false vectors / mismatching | 0.566 / 56 / 3.17 | % / count / % | block-matching simulation / 2011 | exact multiplication | 48 × 48 region, 1 ECC, B=1764 | p.32 |
| TAE / false vectors / mismatching | 0.035 / 10 / 0.56 | % / count / % | block-matching simulation / 2011 | exact multiplication | 48 × 48 region, 2 ECC, B=1764 | p.32 |
errors_and_checks: The approximation underestimates the exact product because every residual error is nonnegative. The relative error decreases each iteration and becomes zero when either residual becomes zero; exact multiplication requires as many iterations as the smaller operand’s number of one bits. No fault-detection mechanism is reported. # pp.25-27,30-31
conditions: The design targets DSP cases where multiplication speed matters more than exact accuracy. # pp.23-24 The combinational delay increases by 30-45% per correction circuit, while pipelining restores 153.335 MHz and II=1 at added latency/register cost. # pp.28-30,32 Motion-vector mismatches can slightly reduce video-compression performance. # p.32
evidence: Algorithm 2 and Eqs. (7)-(27), pp.25-31; Figs. 1-5, pp.27-30; Tables 1-9, pp.30-32.

## new_families
none

## space_gaps
* The logarithmic family lacks a pipeline-organization choice for the paper’s four-stage basic block and staggered correction-block cascade. # pp.28-30

## open_questions
* The paper does not identify the topology/circuit family of its 32-bit adders. # pp.27-29
