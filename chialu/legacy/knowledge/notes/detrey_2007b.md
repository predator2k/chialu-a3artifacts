---
handle: detrey_2007b
citation: J. Detrey, F. de Dinechin, "Floating-Point Trigonometric Functions for FPGAs", International Conference on Field Programmable Logic and Applications (FPL), pp. 29-34, 2007
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_SFU]
formats: [custom_fp, fp32, fixed_point]
authority: incremental
pages_read: 29-34 / 6
---

## summary
The paper proposes parameterized, pipelinable FPGA sine/cosine operators for floating-point formats up to single precision. The reference operator combines Payne-Hanek argument reduction, a close/far dual path, HOTBM polynomial evaluation, reconstruction, and exception handling. Three variants trade specification or output format for area/delay reductions.

## families
### range_reduction  (role: instantiates)
mechanism: Radian inputs use Payne-Hanek reduction: k is x × 2/π rounded to the nearest integer, while the fractional part of x × 4/π supplies the reduced argument. Exponent-controlled truncation selects the required constant bits. A close path derives fixed-point Y from floating-point (Ey, My) for x < 1/2, while a far path uses an LZC and shifter to derive (Ey, My) from Y. The sin(πx)/cos(πx) variant instead splits x into integer/fractional parts. # pp.30-33
choices:
  method: payne_hanek   # pp.30-31
  reduction_type: multiplicative   # p.30
  worst_case_bound_proven: true   # pp.30-32
new_choices:
  path_structure: close_far_dual — selects complementary fixed-to-floating and floating-to-fixed datapaths around x < 1/2   # pp.31-32
slots: none
parameters: π-related constant roughly 2^(wE-1)+3wF bits; extraction roughly 3wF bits; multiplier roughly wF × 3wF bits; gK usually close to wF; g ≤ 2   # pp.30-32
results: none
errors_and_checks: The reference reduction supports guaranteed faithful rounding for any input; Kahan-Douglas analysis determines gK from the smallest possible reduced argument.   # pp.30-32
conditions: Cody-Waite is useful only for small arguments; iterative modular reduction is poorly suited to a pipelined implementation. The sin(πx)/cos(πx) specification removes the irrational constant multiplication and one guard bit.   # pp.31-33
evidence: §2; Figs. 2 and 4; §3 “Dual-path argument reduction”; §4 “Functions of πx”

### lut_plus_poly  (role: instantiates)
mechanism: HOTBM approximates the reduced functions with minimax polynomials and evaluates them using an optimized parallel composition of lookup tables, powering units, and small multipliers. Cosine evaluates fcos(y)=1−cos(πy/4), omitting its constant leading bit. Sine evaluates fsin(y)=(π/4)sin(πy/4)/y in fixed point and multiplies the result by floating-point y. # p.32
choices:
  basis: minimax_remez   # p.32
  guard_bits: 2   # p.32
new_choices: none
slots:
  range_reducer: range_reduction [method=payne_hanek, reduction_type=multiplicative]   # pp.30-32
parameters: exponent width wE; fraction width wF; at most g=2 guard bits; formats through (wE,wF)=(8,23)   # pp.29,32,34
results: none
errors_and_checks: The HOTBM operators produce faithful results; the complete datapath guarantees relative error below 2^(-wF). HOTBM outputs are faithful relative to guard-extended, error-carrying inputs.   # p.32
conditions: Pipelined CORDIC has long latency and large hardware cost. HOTBM area grows exponentially with precision and is poorly suited beyond 32 bits.   # pp.32-33
evidence: §3 “Table-based evaluation”; Fig. 5; §6

## new_families
### shared_dual_trigonometric  (domain: sfu: elementary-function units, closest: lut_plus_poly, why_not: `lut_plus_poly` describes local approximation but not shared sine/cosine reduction, dual-path formatting, reconstruction, and exceptions)
mechanism: One argument-reduction datapath feeds parallel sine and cosine HOTBM evaluators. Reconstruction uses the octant k and input sign to select/sign the two reduced results. The reference returns floating-point sine and cosine with faithful rounding. Variants compute sin(πx)/cos(πx), return fixed-point results, or compute sine alone. # pp.31-33
choices:
  function_outputs: {sin, sin_cos}
  angle_scaling: {radian, pi_scaled}
  result_format: {floating_point, fixed_point}
  argument_reduction_paths: {single, close_far_dual}
results:
| metric | value | unit | technology / device | baseline | condition | page |
| area | 803 | slices | Virtex-II XC2V1000-4; 2007 | UNKNOWN | dual; (5,10) | p.34 |
| delay | 69 | ns | Virtex-II XC2V1000-4; 2007 | UNKNOWN | dual; (5,10) | p.34 |
| area | 1159 | slices | Virtex-II XC2V1000-4; 2007 | UNKNOWN | dual; (6,13) | p.34 |
| delay | 86 | ns | Virtex-II XC2V1000-4; 2007 | UNKNOWN | dual; (6,13) | p.34 |
| area | 1652 | slices | Virtex-II XC2V1000-4; 2007 | UNKNOWN | dual; (7,16) | p.34 |
| delay | 91 | ns | Virtex-II XC2V1000-4; 2007 | UNKNOWN | dual; (7,16) | p.34 |
| area | 2549 | slices | Virtex-II XC2V1000-4; 2007 | UNKNOWN | dual; (7,20) | p.34 |
| delay | 99 | ns | Virtex-II XC2V1000-4; 2007 | UNKNOWN | dual; (7,20) | p.34 |
| area | 3320 | slices | Virtex-II XC2V1000-4; 2007 | UNKNOWN | dual; (8,23) | p.34 |
| delay | 109 | ns | Virtex-II XC2V1000-4; 2007 | UNKNOWN | dual; (8,23) | p.34 |
| logic area | 424 | slices | Virtex-II XC2V1000-4; 2007 | UNKNOWN | dual+embedded mult.; (5,10) | p.34 |
| multiplier area | 7 | multipliers | Virtex-II XC2V1000-4; 2007 | UNKNOWN | dual+embedded mult.; (5,10) | p.34 |
| delay | 61 | ns | Virtex-II XC2V1000-4; 2007 | UNKNOWN | dual+embedded mult.; (5,10) | p.34 |
| logic area | 537 | slices | Virtex-II XC2V1000-4; 2007 | UNKNOWN | dual+embedded mult.; (6,13) | p.34 |
| multiplier area | 7 | multipliers | Virtex-II XC2V1000-4; 2007 | UNKNOWN | dual+embedded mult.; (6,13) | p.34 |
| delay | 76 | ns | Virtex-II XC2V1000-4; 2007 | UNKNOWN | dual+embedded mult.; (6,13) | p.34 |
| logic area | 816 | slices | Virtex-II XC2V1000-4; 2007 | UNKNOWN | dual+embedded mult.; (7,16) | p.34 |
| multiplier area | 10 | multipliers | Virtex-II XC2V1000-4; 2007 | UNKNOWN | dual+embedded mult.; (7,16) | p.34 |
| delay | 87 | ns | Virtex-II XC2V1000-4; 2007 | UNKNOWN | dual+embedded mult.; (7,16) | p.34 |
| logic area | 1372 | slices | Virtex-II XC2V1000-4; 2007 | UNKNOWN | dual+embedded mult.; (7,20) | p.34 |
| multiplier area | 17 | multipliers | Virtex-II XC2V1000-4; 2007 | UNKNOWN | dual+embedded mult.; (7,20) | p.34 |
| delay | 96 | ns | Virtex-II XC2V1000-4; 2007 | UNKNOWN | dual+embedded mult.; (7,20) | p.34 |
| logic area | 1700 | slices | Virtex-II XC2V1000-4; 2007 | UNKNOWN | dual+embedded mult.; (8,23) | p.34 |
| multiplier area | 19 | multipliers | Virtex-II XC2V1000-4; 2007 | UNKNOWN | dual+embedded mult.; (8,23) | p.34 |
| delay | 99 | ns | Virtex-II XC2V1000-4; 2007 | UNKNOWN | dual+embedded mult.; (8,23) | p.34 |
| area | 363 | slices | Virtex-II XC2V1000-4; 2007 | UNKNOWN | dual πx; (5,10) | p.34 |
| delay | 58 | ns | Virtex-II XC2V1000-4; 2007 | UNKNOWN | dual πx; (5,10) | p.34 |
| area | 641 | slices | Virtex-II XC2V1000-4; 2007 | UNKNOWN | dual πx; (6,13) | p.34 |
| delay | 61 | ns | Virtex-II XC2V1000-4; 2007 | UNKNOWN | dual πx; (6,13) | p.34 |
| area | 865 | slices | Virtex-II XC2V1000-4; 2007 | UNKNOWN | dual πx; (7,16) | p.34 |
| delay | 73 | ns | Virtex-II XC2V1000-4; 2007 | UNKNOWN | dual πx; (7,16) | p.34 |
| area | 1531 | slices | Virtex-II XC2V1000-4; 2007 | UNKNOWN | dual πx; (7,20) | p.34 |
| delay | 84 | ns | Virtex-II XC2V1000-4; 2007 | UNKNOWN | dual πx; (7,20) | p.34 |
| area | 2081 | slices | Virtex-II XC2V1000-4; 2007 | UNKNOWN | dual πx; (8,23) | p.34 |
| delay | 89 | ns | Virtex-II XC2V1000-4; 2007 | UNKNOWN | dual πx; (8,23) | p.34 |
| area | 244 | slices | Virtex-II XC2V1000-4; 2007 | UNKNOWN | dual πx+3 mult.; (5,10) | p.34 |
| delay | 46 | ns | Virtex-II XC2V1000-4; 2007 | UNKNOWN | dual πx+3 mult.; (5,10) | p.34 |
| area | 462 | slices | Virtex-II XC2V1000-4; 2007 | UNKNOWN | dual πx+3 mult.; (6,13) | p.34 |
| delay | 61 | ns | Virtex-II XC2V1000-4; 2007 | UNKNOWN | dual πx+3 mult.; (6,13) | p.34 |
| area | 559 | slices | Virtex-II XC2V1000-4; 2007 | UNKNOWN | dual πx+4 mult.; (7,16) | p.34 |
| delay | 69 | ns | Virtex-II XC2V1000-4; 2007 | UNKNOWN | dual πx+4 mult.; (7,16) | p.34 |
| area | 1005 | slices | Virtex-II XC2V1000-4; 2007 | UNKNOWN | dual πx+8 mult.; (7,20) | p.34 |
| delay | 76 | ns | Virtex-II XC2V1000-4; 2007 | UNKNOWN | dual πx+8 mult.; (7,20) | p.34 |
| area | 1365 | slices | Virtex-II XC2V1000-4; 2007 | UNKNOWN | dual πx+10 mult.; (8,23) | p.34 |
| delay | 85 | ns | Virtex-II XC2V1000-4; 2007 | UNKNOWN | dual πx+10 mult.; (8,23) | p.34 |
| area | 376 | slices | Virtex-II XC2V1000-4; 2007 | UNKNOWN | fixed out; (5,10) | p.34 |
| delay | 57 | ns | Virtex-II XC2V1000-4; 2007 | UNKNOWN | fixed out; (5,10) | p.34 |
| area | 642 | slices | Virtex-II XC2V1000-4; 2007 | UNKNOWN | fixed out; (6,13) | p.34 |
| delay | 63 | ns | Virtex-II XC2V1000-4; 2007 | UNKNOWN | fixed out; (6,13) | p.34 |
| area | 923 | slices | Virtex-II XC2V1000-4; 2007 | UNKNOWN | fixed out; (7,16) | p.34 |
| delay | 72 | ns | Virtex-II XC2V1000-4; 2007 | UNKNOWN | fixed out; (7,16) | p.34 |
| area | 1620 | slices | Virtex-II XC2V1000-4; 2007 | UNKNOWN | fixed out; (7,20) | p.34 |
| delay | 82 | ns | Virtex-II XC2V1000-4; 2007 | UNKNOWN | fixed out; (7,20) | p.34 |
| area | 2203 | slices | Virtex-II XC2V1000-4; 2007 | UNKNOWN | fixed out; (8,23) | p.34 |
| delay | 88 | ns | Virtex-II XC2V1000-4; 2007 | UNKNOWN | fixed out; (8,23) | p.34 |
| area | 709 | slices | Virtex-II XC2V1000-4; 2007 | UNKNOWN | sine alone; (5,10) | p.34 |
| delay | 70 | ns | Virtex-II XC2V1000-4; 2007 | UNKNOWN | sine alone; (5,10) | p.34 |
| area | 1027 | slices | Virtex-II XC2V1000-4; 2007 | UNKNOWN | sine alone; (6,13) | p.34 |
| delay | 86 | ns | Virtex-II XC2V1000-4; 2007 | UNKNOWN | sine alone; (6,13) | p.34 |
| area | 1428 | slices | Virtex-II XC2V1000-4; 2007 | UNKNOWN | sine alone; (7,16) | p.34 |
| delay | 92 | ns | Virtex-II XC2V1000-4; 2007 | UNKNOWN | sine alone; (7,16) | p.34 |
| area | 2050 | slices | Virtex-II XC2V1000-4; 2007 | UNKNOWN | sine alone; (7,20) | p.34 |
| delay | 101 | ns | Virtex-II XC2V1000-4; 2007 | UNKNOWN | sine alone; (7,20) | p.34 |
| area | 2659 | slices | Virtex-II XC2V1000-4; 2007 | UNKNOWN | sine alone; (8,23) | p.34 |
| delay | 105 | ns | Virtex-II XC2V1000-4; 2007 | UNKNOWN | sine alone; (8,23) | p.34 |
| pipeline depth | 18 | cycles | Virtex-II -4; 2007 | UNKNOWN | preliminary single precision | p.33 |
| clock frequency | 100 | MHz | Virtex-II -4; 2007 | UNKNOWN | preliminary single precision | p.33 |
| result interval | 10 | ns | Virtex-II -4; 2007 | Pentium 4 libm | one sine and cosine | p.33 |
| result interval | 80 | ns | Pentium 4, UNKNOWN technology; 2007 | FPGA result | libm sine average | p.33 |
evidence: Figs. 3-5; §§3-5; Table 1

## space_gaps
* The evaluator slot lacks a `hotbm_parallel` family for the LUT/powering-unit/small-multiplier architecture.   # p.32
* The range-reduction vocabulary lacks the close/far dual-path structure used to produce both fixed-point and floating-point reduced arguments.   # pp.31-32
* The elementary-function vocabulary lacks a complete shared dual-output trigonometric operator family.   # pp.31-33

## open_questions
* The paper omits the HOTBM polynomial degrees, segmentation, coefficient widths, table sizes, and detailed error analysis.
* The preliminary 18-cycle pipeline is not represented in Table 1, whose post-route delays describe the presented implementations.
