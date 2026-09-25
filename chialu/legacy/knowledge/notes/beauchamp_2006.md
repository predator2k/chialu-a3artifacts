---
handle: beauchamp_2006
citation: M. J. Beauchamp, S. Hauck, K. D. Underwood, K. S. Hemmert, "Embedded Floating-Point Units in FPGAs", ACM/SIGDA International Symposium on Field-Programmable Gate Arrays (FPGA), 2006
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU, VEC_DOT_ACC, other]
formats: [fp64]
authority: incremental
pages_read: 9 / 9
---

## summary
The document evaluates dedicated double-precision floating-point multiply-add blocks embedded as columns in an island-style FPGA. The modeled blocks reduce average benchmark area by 55.0% and increase average clock rate by 40.7% against an architecture using embedded 18-bit x 18-bit multipliers.

## families
### fpga_carry_chain  (role: instantiates)
mechanism: Each CLB contains a dedicated upward carry route that connects directly to the CLB above without connection boxes, switch boxes, or isolation buffers. Each CLB handles two result bits and provides two points for entering or leaving the chain. Placement moves every CLB in a chain together to preserve relative position.
choices:
new_choices:
  direction: upward_only — physical direction supported by each column carry-chain   # p.15
  attachment_points_per_clb: 2 — opportunities to enter or leave the chain   # p.15
slots:
  none
parameters: 57-bit adder in double-precision addition; two output bits per CLB   # p.15
results:
| metric | value | unit | technology / device | baseline | condition | page |
| maximum frequency | 126 | MHz | 2006; modeled Xilinx Virtex-II Pro-like FPGA; node UNKNOWN | 87 MHz without fast carry-chain | matrix multiply | p.16 |
| maximum frequency | 117 | MHz | 2006; modeled Xilinx Virtex-II Pro-like FPGA; node UNKNOWN | 89 MHz without fast carry-chain | matrix-vector multiply | p.16 |
| maximum frequency | 149 | MHz | 2006; modeled Xilinx Virtex-II Pro-like FPGA; node UNKNOWN | 87 MHz without fast carry-chain | dot product | p.16 |
| maximum frequency | 104 | MHz | 2006; modeled Xilinx Virtex-II Pro-like FPGA; node UNKNOWN | 79 MHz without fast carry-chain | FFT | p.16 |
| maximum frequency | 142 | MHz | 2006; modeled Xilinx Virtex-II Pro-like FPGA; node UNKNOWN | 84 MHz without fast carry-chain | LU decomposition | p.16 |
| average maximum frequency | 128 | MHz | 2006; modeled Xilinx Virtex-II Pro-like FPGA; node UNKNOWN | 85 MHz without fast carry-chain | five benchmarks | p.16 |
| average speed increase | 49.7% | percent | 2006; modeled Xilinx Virtex-II Pro-like FPGA; node UNKNOWN | without fast carry-chain | five benchmarks | p.16 |
errors_and_checks: none
conditions: The chain is required for a reasonable comparison because the CLB-only and embedded-multiplier implementations extensively use it; general routing would significantly reduce the 57-bit adder frequency.   # p.15
evidence: §3, §4.2, Table 6, Figure 5, pp.13-16

## new_families
### embedded_fpga_fpu_block  (domain: dsp, closest: hard_fp_dsp, why_not: The FPU is a standalone columnar embedded block rather than IEEE floating-point logic inside a DSP slice.)
mechanism: A coarse-grained double-precision floating-point multiply-add unit is embedded alongside CLB/RAM columns in an island-style FPGA. Horizontal routing crosses the block, while vertical routing remains at its periphery. Outputs may be registered. VPR models the block with parameterized dimensions/timing and evaluates eight aspect ratios; height 32 CLBs provides the highest average frequency with the fewest routing tracks and without significant area increase.
choices:
  block_height_clbs: {4, 8, 16, 32, 64, 96, 128, 160}   # p.17
  output_registration: Bool   # p.13
  placement_style: {column_based}   # p.13
results:
| metric | value | unit | technology / device | baseline | condition | page |
| setup time | 0.50 | ns | 2006; modeled 64-bit FPU; node UNKNOWN | estimated component model | FPU block | p.14 |
| clock-to-q | 0.50 | ns | 2006; modeled 64-bit FPU; node UNKNOWN | estimated component model | FPU block | p.14 |
| area | 107 | 10^6 L^2 | 2006; modeled 64-bit FPU; node UNKNOWN | normalized component estimate | FPU block | p.14 |
| area | 161 | CLBs | 2006; modeled 64-bit FPU; node UNKNOWN | normalized component estimate | FPU block | p.14 |
| area | 9,662 | 10^6 L^2 | 2006; modeled Xilinx Virtex-II Pro-like FPGA; node UNKNOWN | 20,037 embedded multipliers; 23,945 CLBs only | matrix multiply | p.18 |
| area | 7,265 | 10^6 L^2 | 2006; modeled Xilinx Virtex-II Pro-like FPGA; node UNKNOWN | 20,187 embedded multipliers; 24,283 CLBs only | matrix-vector multiply | p.18 |
| area | 4,544 | 10^6 L^2 | 2006; modeled Xilinx Virtex-II Pro-like FPGA; node UNKNOWN | 15,223 embedded multipliers; 20,565 CLBs only | dot product | p.18 |
| area | 16,792 | 10^6 L^2 | 2006; modeled Xilinx Virtex-II Pro-like FPGA; node UNKNOWN | 28,443 embedded multipliers; 33,856 CLBs only | FFT | p.18 |
| area | 7,640 | 10^6 L^2 | 2006; modeled Xilinx Virtex-II Pro-like FPGA; node UNKNOWN | 18,169 embedded multipliers; 23,461 CLBs only | LU decomposition | p.18 |
| average area | 9,181 | 10^6 L^2 | 2006; modeled Xilinx Virtex-II Pro-like FPGA; node UNKNOWN | 20,412 embedded multipliers; 25,222 CLBs only | five benchmarks | p.18 |
| average area reduction | 55.0% | percent | 2006; modeled Xilinx Virtex-II Pro-like FPGA; node UNKNOWN | embedded-multiplier architecture | five benchmarks | p.18 |
| average area reduction | 63.6% | percent | 2006; modeled Xilinx Virtex-II Pro-like FPGA; node UNKNOWN | CLB-only architecture | five benchmarks | p.18 |
| average maximum frequency | 179 | MHz | 2006; modeled Xilinx Virtex-II Pro-like FPGA; node UNKNOWN | 128 MHz embedded multipliers; 97 MHz CLBs only | five benchmarks | p.18 |
| average speed increase | 40.7% | percent | 2006; modeled Xilinx Virtex-II Pro-like FPGA; node UNKNOWN | embedded-multiplier architecture | five benchmarks | p.18 |
| average speed increase | 85.1% | percent | 2006; modeled Xilinx Virtex-II Pro-like FPGA; node UNKNOWN | CLB-only architecture | five benchmarks | p.18 |
| average routing tracks | 44 | tracks | 2006; modeled Xilinx Virtex-II Pro-like FPGA; node UNKNOWN | 49 embedded multipliers; 47 CLBs only | five benchmarks | p.18 |
| average routing-track reduction | 8.6% | percent | 2006; modeled Xilinx Virtex-II Pro-like FPGA; node UNKNOWN | embedded-multiplier architecture | five benchmarks | p.19 |
| normalized performance | 13.38 | Gflops | 2006; modeled Xilinx Virtex-II Pro-like FPGA; node UNKNOWN | 3.99 embedded multipliers; 2.49 CLBs only | area-normalized benchmark performance | p.19 |
| chip area occupied | 17.6% | percent | 2006; modeled Xilinx Virtex-II Pro-like FPGA; node UNKNOWN | entire chosen FPGA configuration | embedded FPUs | p.19 |
evidence: Abstract, §§3-6, Tables 2/7/8, Figures 6-12, pp.12-19

## space_gaps
* `hard_fp_dsp.fp_format` lacks fp64, while the evaluated block is a standalone fp64 FPU rather than floating-point logic within a DSP slice.   # pp.13-19
* `fpga_carry_chain` lacks direction and per-CLB attachment-point choices used by the modeled architecture.   # pp.15-16
* The embedded FPU family needs an operation-access choice because coupled multiply-add wastes hardware on isolated adds/multiplies, while independent access is proposed as a modification.   # pp.18-19

## open_questions
* The document does not specify the FPU’s internal multiplier/adder architecture, rounding path, exception handling, or subnormal support.
* The document does not state whether “multiply-add” means a single-rounding fused operation or composed multiplication and addition.
* The technology node is not reported, and the FPU area/timing values are estimates rather than fabricated measurements.   # p.14
* The prose reports 13.38, 3.99, and 2.49 Gflops together with improvement factors of 2.4 and 4.4, but it does not explain the basis for those factors.   # p.19
