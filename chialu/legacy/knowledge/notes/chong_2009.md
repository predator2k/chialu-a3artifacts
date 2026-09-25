---
handle: chong_2009
citation: Y. J. Chong, S. Parameswaran, "Flexible Multi-Mode Embedded Floating-Point Unit for Field Programmable Gate Arrays", ACM/SIGDA International Symposium on Field-Programmable Gate Arrays (FPGA), 2009
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU, VEC_DOT_ACC, other]
formats: [fp32, fp64, int24, int26, int27, int53]
authority: incremental
pages_read: 171-180 / 10
---

## summary
The paper proposes an embedded FPGA FPU whose adder/multiplier each perform one fp64 operation or two fp32 operations in parallel, with accessible integer multiplier/adder/shifter components (pp.171-172, 176). The multiplier places two independent 24×24 partial-product sets within one radix-4 Booth/Wallace tree, so both precision modes complete in one cycle (pp.175-176). Modeled benchmarks report geometric-mean area/delay improvements of 5.2×/5.8× for fp64 and 4.4×/4.2× for fp32 against a standard Virtex-II FPGA (pp.178-179).

## families
### single_path  (role: instantiates)
mechanism: The floating-point adder uses the conventional serial sequence of exponent difference, pre-alignment, significand addition/subtraction, normalization and rounding. Duplicated fp32 blocks are linked and widened for fp64 operation. Configuration multiplexers select two independent fp32 paths or one combined fp64 path (pp.173-175).
choices:
  post_round_renorm: true   # p.173
new_choices:
  none
slots:
  sig_adder: carry_lookahead   # pp.172,175
  round: increment_adder   # pp.173,175
  subnormal: UNKNOWN   # p.174
  align: full_align   # pp.173,175
  norm: single_barrel   # pp.173,175
parameters: five algorithmic stages; 53-bit combined significand adder; independent 27-bit/26-bit adders; two 53-bit right shifters or one 106-bit right shifter; two 27-bit left shifters or one 54-bit left shifter (pp.173-176)
results:
| metric | value | unit | technology / device | baseline | condition | page |
|---|---:|---|---|---|---|---|
errors_and_checks: IEEE754 compliant except hardware denormal support is omitted and only round-to-nearest-even is implemented (p.174).
conditions: The conventional path is chosen for area/complexity savings rather than the faster leading-one-predictor or dual-path architectures (p.174).
evidence: §3.2, §4, §4.1, Figures 2, 6 and 7 (pp.173-175)

### booth_recoded_parallel  (role: extends)
mechanism: A radix-4 modified-Booth generator feeds a seven-level Wallace tree and a final carry-select adder. In fp32 mode, two 24-bit partial-product sets occupy opposite corners of the 53-bit array. Zero padding and a three-bit separation prevent the two computations from contaminating each other during reduction (pp.174-176).
choices:
  booth_radix: 4   # p.174
  hard_multiple_gen: none   # p.174
  sign_extension: prevention_constant   # p.176
new_choices:
  precision_partition: one_53x53_or_two_24x24 — selects one full partial-product set or two separated sets in the same tree   # pp.175-176
slots:
  reduction: csa_reduction_tree   # pp.174-176
parameters: N=53; a=b=24; seven Wallace-tree reduction levels; g=3 minimum separation; one-cycle fp32/fp64 multiplication (pp.174-176)
results:
| metric | value | unit | technology / device | baseline | condition | page |
|---|---:|---|---|---|---|---|
errors_and_checks: A separation of at least g=3 guarantees that intermediate values from the two fp32 products remain independent (p.176).
conditions: The one-cycle structure uses more hardware than Akkaş’s two-cycle high-precision arrangement, while avoiding its every-other-cycle fp64 initiation limit (pp.173,175).
evidence: §3.3, §4.2, Figures 4 and 8 (pp.174-176)

### bridge_fma  (role: instantiates)
mechanism: The block contains separate floating-point multiplier/adder datapaths and an internal selectable bus from the multiplier output to one adder input. The connection supports one fp64, two parallel fp32, one 53-bit integer or two parallel 24-bit integer multiply-add operations (pp.172,176).
choices:
  composition_style: cascade_mul_then_add   # pp.176,179
new_choices:
  none
slots:
  align: full_align   # pp.173-176
  lza: lzc_after_add   # pp.173-175
  cpa: carry_lookahead   # p.172
  round: increment_adder   # pp.173-175
  multiplier: booth_recoded_parallel   # pp.174-176
parameters: one fp64 or two fp32 operations in parallel; optional input/output registers; internal multiplier-to-adder link (pp.176,179)
results:
| metric | value | unit | technology / device | baseline | condition | page |
|---|---:|---|---|---|---|---|
errors_and_checks: The product is rounded before addition, so the multiply-add does not preserve the dedicated-FMA single-rounding contract (p.179).
conditions: The internal link avoids external routing delay, but accumulated rounding error can exceed that of a dedicated floating-point MAC (pp.172,179).
evidence: §4.3, Figure 9, §9 and §10 (pp.176,179-180)

## new_families
### flexible_embedded_fpu_block  (domain: dsp: FPGA DSP blocks, closest: hard_fp_dsp, why_not: hard_fp_dsp does not represent a configurable fp64/two-fp32 FPU that exposes its internal integer multiplier/adder/shifters.)
mechanism: One hard FPGA block combines a dual-precision floating-point multiplier and adder. Configuration multiplexers expose the 53×53/two-24×24 multiplier, 53/two-26-and-27-bit adder, 64-bit right shifter and 54-bit left shifter for integer use. Dedicated shifter ports permit concurrent shifter/adder operation, while shared arithmetic ports limit pin count (pp.175-177).
choices: precision_modes: {one_fp64, two_fp32}; integer_component_access: {none, multiplier_adder_shifters}; multiplier_adder_link: Bool; optional_io_registers: Bool
results:
| metric | value | unit | technology / device | baseline | condition | page |
|---|---:|---|---|---|---|---|
| synthesized block area | 264,065 | µm2 | 0.13µm standard-cell library; 2009 | none | before 15% place-and-route overhead | p.177 |
| estimated block area | 302,524 | µm2 | 0.13µm standard-cell library; 2009 | none | Table 1 estimate | p.177 |
| estimated block size | 37 | slices | Xilinx Virtex-II-equivalent; 2009 | none | area-based estimate | p.177 |
| modeled block size | 144 | slices | XC2V3000-6-FF1152 VEB; 2009 | 37-slice estimate | enlarged to supply 288 outputs | p.177 |
| fp64 geometric-mean area improvement | 5.2 | × | XC2V3000-6-FF1152/VEB; 2009 | FPGA without embedded FPUs | five benchmarks | p.178 |
| fp64 geometric-mean delay improvement | 5.8 | × | XC2V3000-6-FF1152/VEB; 2009 | FPGA without embedded FPUs | five benchmarks | p.178 |
| fp32 geometric-mean area improvement | 4.4 | × | XC2V3000-6-FF1152/VEB; 2009 | FPGA without embedded FPUs | five benchmarks | p.178 |
| fp32 geometric-mean delay improvement | 4.2 | × | XC2V3000-6-FF1152/VEB; 2009 | FPGA without embedded FPUs | five benchmarks | p.178 |
| integer geometric-mean area improvement | 1.21 | × | XC2V3000-6-FF1152/VEB; 2009 | FPGA fabric/embedded multipliers | six circuits | p.179 |
| integer geometric-mean delay improvement | 1.71 | × | XC2V3000-6-FF1152/VEB; 2009 | FPGA fabric/embedded multipliers | six circuits | p.179 |
evidence: §4.3–§9, Figures 9-10 and Tables 1-4 (pp.176-180)

## space_gaps
* hard_fp_dsp needs an fp64 and dual-fp32 lane-composition value for fp_format (pp.171-172,176).
* bridge_fma needs a product-rounding choice that distinguishes an intermediate-rounded cascade from a single-round fused operation (p.179).
* booth_recoded_parallel lacks a choice for placing multiple independent partial-product regions within one shared reduction tree (pp.175-176).
* The FPGA DSP-block vocabulary lacks a family for exposing floating-point-unit internals as independently accessible integer multiplier/adder/shifter resources (pp.176-177).

## open_questions
* Figure 8’s text defines the second small product as p2=y1×y2, although the surrounding description implies two operand pairs; the intended expression is ambiguous (p.175).
* Table 3 prints a 9.6× area improvement for `ode`, while its printed areas are 1237 and 356 slices; the note preserves only the reported geometric mean rather than resolving the discrepancy (p.178).
* The paper does not state whether unsupported denormals are trapped, flushed to zero or handled outside the block (p.174).
