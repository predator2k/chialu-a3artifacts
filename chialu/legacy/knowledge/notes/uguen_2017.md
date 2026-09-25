---
handle: uguen_2017
citation: Y. Uguen, F. de Dinechin, "Design-Space Exploration for the Kulisch Accumulator", HAL preprint hal-01488916, 2017
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_DOT_ACC]
formats: [binary16, binary32, binary64]
authority: incremental
pages_read: 7 / 7
---

## summary
The paper compares three Kulisch accumulator architectures and proposes two two’s-complement variants for exact floating-point sums and dot products on FPGAs. The first proposed variant reduces each parallel sub-adder to one binary addition, while the second pipelines the sub-adder banks. Post-route Kintex 7 results identify the first proposed variant as the best of the evaluated split architectures in frequency/resource terms. (§3–§5)

## families
### kulisch_long_accumulator  (role: extends)
mechanism: An exact multiplier emits an unnormalized product whose sign/exponent/mantissa determine its position in a fixed-point accumulator spanning the product exponent range. The compared organizations use one full-width register/adder, RAM-held words with state-directed carry/borrow handling, parallel sub-adders with delayed inter-word carries, or pipelined sub-adder stages. Proposed 1 converts inputs to two’s complement before accumulation, replacing replicated addition/subtraction and separate carry/borrow storage with one binary addition and one carry path. Proposed 2 pipelines the bus and sums matching mantissa words plus incoming carries at each stage. (§2–§4)
choices:
  accumulator_width_bits: 80 [outside domain] for binary16; 554 [outside domain] for binary32; 4196 [outside domain] minimum and 4288 for binary64   # §2, Table 1
  organization: monolithic for Kulisch 1; ram_segmented [outside domain] for Kulisch 2; banked_sub_adders for Kulisch 3/Proposed 1; pipelined_sub_adders [outside domain] for Proposed 2   # §2.2–§4
  carry_resolution: immediate for Kulisch 1; state_directed [outside domain] for Kulisch 2; delayed_with_final_N_cycle_flush [outside domain] for Kulisch 3/Proposed 1/Proposed 2   # §2.2–§4
new_choices:
  sign_management: {sign_magnitude_carry_borrow, twos_complement_single_carry} — selects replicated add/subtract handling or input-side two’s-complement conversion   # §2.5, §3
  sub_adder_width_bits: positive integer — sets the accumulator word/sub-adder width b   # §2.3, §5
slots:
  none
parameters: Input exponent width we and significand width wf produce exact-product widths we' = we + 1 and wf' = 2×wf + 2; the accumulator has N = ceil(wa/b) words; a shifted mantissa spans S = ceil((wf'−1+b)/b) words; evaluated b values include 16, 32, 64, and 128 bits; accumulation latency is evaluated for 1000 summands.   # §2.1–§2.3, §5, Table 3
results:
| metric | value | unit | technology / device | baseline | condition | page |
| implementation tuple: LUTs / registers / DSPs / latency | 58129 / 59932 / 9 / 9233 | LUTs / registers / DSPs / cycles | Xilinx Kintex 7 FPGA; Vivado 2016.3 | UNKNOWN | Kulisch 1; binary64; 1000 accumulations | §5, Table 2 |
| implementation tuple: LUTs / registers / DSPs / latency | 2814 / 1919 / 9 / 68173 | LUTs / registers / DSPs / cycles | Xilinx Kintex 7 FPGA; Vivado 2016.3 | UNKNOWN | Kulisch 2; SA=64; binary64; 1000 accumulations | §5, Table 2 |
| implementation tuple: LUTs / registers / DSPs / latency / max frequency | 841 / 822 / 1 / 1021 / 363 | LUTs / registers / DSPs / cycles / MHz | Xilinx Kintex 7 FPGA; Vivado 2016.3 | UNKNOWN | Proposed 1; binary16; SA=16; 1000 summands | §5, Table 3 |
| implementation tuple: LUTs / registers / DSPs / latency / max frequency | 4751 / 6516 / 2 / 1111 / 344 | LUTs / registers / DSPs / cycles / MHz | Xilinx Kintex 7 FPGA; Vivado 2016.3 | UNKNOWN | Proposed 1; binary32; SA=64; 1000 summands | §5, Table 3 |
| implementation tuple: LUTs / registers / DSPs / latency / max frequency | 5162 / 9760 / 2 / 1103 / 209 | LUTs / registers / DSPs / cycles / MHz | Xilinx Kintex 7 FPGA; Vivado 2016.3 | UNKNOWN | Kulisch 3; binary32; SA=64; 1000 summands | §5, Table 3 |
| implementation tuple: LUTs / registers / DSPs / latency / max frequency | 7774 / 11960 / 2 / 1143 / 298 | LUTs / registers / DSPs / cycles / MHz | Xilinx Kintex 7 FPGA; Vivado 2016.3 | UNKNOWN | Proposed 2; binary32; SA=32; 1000 summands | §5, Table 3 |
| implementation tuple: LUTs / registers / DSPs / latency / max frequency | 5968 / 9716 / 2 / 1098 / 297 | LUTs / registers / DSPs / cycles / MHz | Xilinx Kintex 7 FPGA; Vivado 2016.3 | UNKNOWN | Proposed 2; binary32; SA=64; 1000 summands | §5, Table 3 |
| implementation tuple: LUTs / registers / DSPs / latency / max frequency | 305 / 673 / 9 / 24218 / 356 | LUTs / registers / DSPs / cycles / MHz | Xilinx Kintex 7 FPGA; Vivado 2016.3 | UNKNOWN | IEEE-754 operators; binary32; 1000 summands | §5, Table 3 |
| implementation tuple: LUTs / registers / DSPs / latency / max frequency | 42415 / 72621 / 9 / 1795 / 300 | LUTs / registers / DSPs / cycles / MHz | Xilinx Kintex 7 FPGA; Vivado 2016.3 | UNKNOWN | Proposed 1; binary64; SA=64; 1000 summands | §5, Table 3 |
| implementation tuple: LUTs / registers / DSPs / latency / max frequency | 39590 / 69826 / 9 / 1643 / 273 | LUTs / registers / DSPs / cycles / MHz | Xilinx Kintex 7 FPGA; Vivado 2016.3 | UNKNOWN | Proposed 1; binary64; SA=128; 1000 summands | §5, Table 3 |
| implementation tuple: LUTs / registers / DSPs / latency / max frequency | 36688 / 76171 / 9 / 1493 / 173 | LUTs / registers / DSPs / cycles / MHz | Xilinx Kintex 7 FPGA; Vivado 2016.3 | UNKNOWN | Kulisch 3; binary64; SA=64; 1000 summands | §5, Table 3 |
| implementation tuple: LUTs / registers / DSPs / latency / max frequency | 58175 / 82188 / 9 / 1707 / 201 | LUTs / registers / DSPs / cycles / MHz | Xilinx Kintex 7 FPGA; Vivado 2016.3 | UNKNOWN | Proposed 2; binary64; SA=64; 1000 summands | §5, Table 3 |
| implementation tuple: LUTs / registers / DSPs / latency / max frequency | 854 / 1873 / 14 / 35317 / 338 | LUTs / registers / DSPs / cycles / MHz | Xilinx Kintex 7 FPGA; Vivado 2016.3 | UNKNOWN | IEEE-754 operators; binary64; 1000 summands | §5, Table 3 |
| relative resources | 5x | resources | Xilinx Kintex 7 FPGA; Vivado 2016.3 | naive accumulation in binary64 | best binary32 Kulisch accumulator | §5 |
| relative latency improvement | 30x | latency improvement | Xilinx Kintex 7 FPGA; Vivado 2016.3 | naive accumulation in binary64 | best binary32 Kulisch accumulator | §5 |
| relative resources / latency improvement | 10x / 25x | resources / latency improvement | Xilinx Kintex 7 FPGA; Vivado 2016.3 | naive classical operators | Proposed accumulator; binary32; large dot product | §1 |
errors_and_checks: The internal fixed-point accumulator computes exact floating-point sums and sums of products regardless of the number of terms; conversion back to floating point occurs only after accumulation. No fault-detection mechanism or numerical error bound for the final conversion is reported.   # §1, §2, §6
conditions: Kulisch 1 is practical only for small formats/exponent ranges because it requires a wa-bit shifter and adder. Kulisch 2 has the lowest reported resource use but cannot be pipelined and has long latency. The parallel designs require N final zero-input cycles to propagate carries, which is acceptable when the number of accumulated values is much larger than N. Proposed 2 performs worst among the split designs because its multiple-input sum creates a long datapath. A 64-bit SA is optimal in most evaluated cases, with a frequency/resource trade-off as SA size varies.   # §2.2, §2.4, §2.5, §5
evidence: §2 and Figures 1–6 define the exact product and three Kulisch organizations; §3 defines Proposed 1; §4 and Figures 7–8 define Proposed 2; §5, Figure 9, and Tables 2–3 provide the comparison.

## new_families
none

## space_gaps
* The `organization` domain lacks the RAM-segmented and pipelined-sub-adder organizations evaluated by the paper. (§2.4, §4)
* The family lacks a sign-management choice distinguishing sign+magnitude carry/borrow handling from input-side two’s-complement conversion. (§2.5, §3)
* The `accumulator_width_bits` domain excludes the documented minimum widths of 80, 554, and 4196 bits. (§2, Table 1)
* The family lacks the tunable sub-adder width b, which controls frequency/resource trade-offs and is optimized experimentally. (§2.3, §5)
* The family lacks a slot for the exact unrounded floating-point product generator feeding dot-product accumulation. (§2.1)

## open_questions
* The exact Kintex 7 device part is not specified.
* The paper does not state the rounding contract used when the exact accumulator is converted back to floating point.
