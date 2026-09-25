---
handle: andraka_1998
citation: R. Andraka, "A Survey of CORDIC Algorithms for FPGA Based Computers", ACM/SIGDA International Symposium on FPGAs, pp. 191-200, 1998
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_SFU]
formats: [UNKNOWN]
authority: survey
pages_read: 191-200 / 10
---

## summary
The paper surveys circular/linear/hyperbolic CORDIC functions and FPGA implementations using iterative, bit-serial, unrolled, and pipelined architectures. The surveyed processors compute rotations, coordinate transformations, magnitude, trigonometric functions, ratios, and related elementary functions using shifts and add-subtract operations.

## families
### cordic  (role: analyzes)
mechanism: Each iteration applies an elementary rotation whose tangent is 2^-i, so multiplication becomes shifting and the x/y recurrences require add-subtract operations (p.192). Rotation mode reduces a residual angle, while vectoring mode reduces the residual y component (pp.192-193). Walther's mode variable unifies circular, linear, and hyperbolic recurrences in one processor (p.195). FPGA implementations range from reused iterative datapaths to unrolled combinational or pipelined chains, with either bit-parallel or bit-serial arithmetic (pp.196-199).
choices:
  mode: both   # p.192
  coordinate_set: unified   # p.195
  topology: folded_sequential, unrolled_pipelined   # pp.196-199
  scale_compensation: constant_multiplier, none   # pp.192-195
  angle_recoding: true   # p.196
new_choices:
  datapath_seriality: {bit_parallel, bit_serial} — selects word-wide operations or one-bit-per-clock add-subtract operations   # pp.196-198
  decision_digit_set: {minus1_plus1, minus1_zero_plus1} — a zero digit removes an iteration for fixed-angle rotations but makes gain angle-dependent   # pp.192,196
  angle_accumulator_implementation: {lookup_table, hardwired_constants, omitted} — stores elementary angles, distributes constants in an unrolled chain, or disappears when angles use the binary-arctangent base   # pp.192,197
slots:
  none
parameters: General accuracy is approximately one additional bit per iteration; circular gain approaches approximately 1.647 (pp.191-192). Reported implementations include 16-bit/8-iteration iterative, 7-iteration bit-serial pipeline, and 14-bit/5-iteration parallel pipeline designs (pp.197-199).
results:
| metric | value | unit | technology / device | baseline | condition | page |
| fixed-angle complexity reduction | about 25 | percent | UNKNOWN; 1998 | CORDIC with angle accumulator | hardwired fixed rotation angle | p.196 |
| area | 21 | CLBs | Xilinx 4000E series; 1998 | UNKNOWN | 16-bit, 8-iteration iterative processor | p.197 |
| bit clock rate | up to about 90 | MHz | Xilinx 4000E series; 1998 | UNKNOWN | 16-bit, 8-iteration iterative processor | p.197 |
| processing time | about 1.5 | µs | Xilinx 4000E series; 1998 | UNKNOWN | 16-bit, 8-iteration iterative processor | p.197 |
| processing-time ratio | about three and a half times longer | UNKNOWN | Xilinx 4000E series; 1998 | much larger bit-parallel iterative solution | 16-bit, 8-iteration processor | p.197 |
| area | approximately 20 | percent of FPGA | Atmel 6005 or NSC Clay31 FPGA; 1998 | UNKNOWN | 7-iteration bit-serial vector-magnitude design | p.198 |
| bit clock rate | up to 125 | Mhz | Atmel 6005 or NSC Clay31 FPGA; 1998 | UNKNOWN | 7-iteration bit-serial vector-magnitude design | p.198 |
| area | half | XC4013E | Xilinx XC4013E-2; 1998 | UNKNOWN | 14-bit, 5-iteration parallel pipelined processor | p.198 |
| clock rate | 52 | MHz | Xilinx XC4013E-2; 1998 | UNKNOWN | 14-bit, 5-iteration parallel pipelined processor | p.198 |
| data rate | 52 | MHz | Xilinx XC4013E-2; 1998 | UNKNOWN | 14-bit, 5-iteration polar-to-Cartesian processor | p.198 |
errors_and_checks: The general algorithm produces approximately one additional accuracy bit per iteration (p.191). Vector-magnitude accuracy improves by 2 bits per iteration (p.194). The stated arcsine recurrence loses accuracy as the input approaches ±1, with rapid error growth above about 0.98; double iteration corrects the gain problem at increased complexity (p.194). No fault model or concurrent checking is reported.
conditions: Circular rotation as stated covers angles from -π/2 to π/2, so larger rotations require an initial quadrant-reduction rotation (p.193). Hyperbolic convergence requires repeated iterations at i=4, 13, 40, and subsequent positions following k, 3k+1 (p.195). Bit-parallel iterative variable shifters map poorly to FPGA logic because of high fan-in, while bit-serial implementations require w clocks for each of n iterations (pp.196-197). Unrolling replaces variable shifts with wiring and table entries with hardwired constants, but an unpipelined chain has substantial combinational delay (p.197). Wider parallel pipelines lose performance through adder carry propagation and require substantial cross-routing between x/y registers (p.198).
evidence: §§3-3.11, equations and function derivations (pp.192-196); §4.1 and Figures 1-3 (pp.196-197); §4.2 and Figures 4-7 (pp.197-199).

## new_families
none

## space_gaps
* `cordic.datapath_seriality` should distinguish `bit_parallel` from `bit_serial`, which changes area, clock rate, and cycles per iteration (pp.196-198).
* `cordic.topology` lacks `unrolled_combinational`, which the paper distinguishes from an unrolled pipeline (p.197).
* `cordic.decision_digit_set` should distinguish {-1,+1} from fixed-angle {-1,0,+1} recoding (p.196).
* `cordic.angle_accumulator_implementation` should represent lookup-table, hardwired-constant, and omitted accumulators (pp.192,197).

## open_questions
* The 7-iteration design's surrounding text names “Atmel 6005 or NSC Clay31 FPGA” without identifying which device supplies the approximately 20% area and 125 Mhz measurements (p.198).
* The 16-bit, 8-iteration result identifies the Xilinx 4000E series without an exact FPGA part or speed grade (p.197).
