---
handle: tiwari_2021
citation: S. Tiwari, N. Gala, C. Rebeiro, V. Kamakoti, "PERI: A Configurable Posit Enabled RISC-V Core", ACM Transactions on Architecture and Code Optimization, 2021
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [posit32_2, posit32_3, int32, fp32]
authority: incremental
pages_read: 1-26 / 26
---

## summary
PERI provides a parameterized posit FPU that implements the RISC-V “F” instruction set and integrates with a SHAKTI C-class core. The FPU includes fused add/multiply, iterative division/square root, integer conversion, comparison, sign injection, and classification, with runtime switching between es = 2 and es = 3 for 32-bit posits. The paper compares PERI with a 32-bit IEEE-754 FPU using ASIC synthesis, FPGA synthesis, application accuracy, and runtime.

## families
### posit_adder_multiplier  (role: extends)
mechanism: Each operation decodes tapered posit fields into sign/exponent/fraction, performs arithmetic, and encodes the result with round-to-nearest with tie-to-even. The parameterized BSV generator accepts ps and es, while the evaluated 32-bit design supports es = 2 or es = 3. The runtime-configurable variant sizes the exponent for es = 3 and the fraction for es = 2, then adjusts encoding/decoding according to the selected es-mode. # p.7-13
choices:
  es_bits: 2 and 3   # p.12-13
  regime_decode: lzc_plus_shifter   # p.8-9
  internal_representation: twos_complement   # p.4, p.8
  approximation: none   # p.7-13
new_choices:
  runtime_es_switching: {fixed, two_es_runtime} — selects es through the 5-bit pcsr es-mode field and converts values with FCVT.ES   # p.6, p.12-13
slots:
  sig_datapath: UNKNOWN   # p.10
parameters: ps = 32; evaluated es = 2, es = 3, and runtime es = 2/3; round-to-nearest with tie-to-even   # p.6, p.9-10, p.12-13
results:
| metric | value | unit | technology / device | baseline | condition | page |
| ASIC FMA area | 46340.16 | μm2 | 65-nm Low-power TSMC / 2021 | IEEE-754: 28448.64 μm2 | es = 2, 400 MHz | p.18 |
| ASIC FMA area | 45132.48 | μm2 | 65-nm Low-power TSMC / 2021 | IEEE-754: 28448.64 μm2 | es = 3, 400 MHz | p.18 |
| ASIC FMA area | 52738.56 | μm2 | 65-nm Low-power TSMC / 2021 | fixed es = 2: 46340.16 μm2 | runtime es = 2/3, 400 MHz | p.18 |
| FPGA FMA area | 1797 | LUTs | Artix-7 xc7a100tcsg324-1 / 2021 | PERC: 1740 LUTs | ps = 32, es = 2 | p.19 |
| FPGA FMA delay | 47.46 | ns | Artix-7 xc7a100tcsg324-1 / 2021 | PERC: 54.394 ns | ps = 32, es = 2 | p.19-20 |
errors_and_checks: Random es = 2 operation results agreed with SoftPosit; es = 2 special cases were extensively verified, while es = 3 corner cases were verified manually. # p.14-15
conditions: The FMA/encoder/decoder structure favors posit accuracy/range rather than area-constrained or lower-runtime applications; per-operation encoders and decoders increase area, and shared codecs remain an unimplemented optimization. # p.17-18, p.24
evidence: Algorithms 1-3; Figures 3; Tables 8-10, 12-13; Sections 5.1-5.3, 5.10, 7.1, 8.

### classic_fma  (role: instantiates)
mechanism: Algorithm 3 decodes three operands, multiplies two fractions, orders and aligns the product/addend by exponent, performs addition or subtraction according to signs/opcode, normalizes subtraction results, and performs one final posit encoding and rounding. The block also executes FADD.S, FSUB.S, and FMUL.S to reuse its resources. # p.10-11
choices:
  subsume_fp_add: true   # p.10
  pipeline_depth: 6   # p.18
new_choices:
  none
slots:
  align: full_align   # p.10
  lza: UNKNOWN
  cpa: UNKNOWN
  round: UNKNOWN
  multiplier: UNKNOWN
parameters: ps = 32; es = 2, es = 3, or runtime es = 2/3; 6 cycles at 400 MHz   # p.18
results:
| metric | value | unit | technology / device | baseline | condition | page |
| latency | 6 | cycles | 65-nm Low-power TSMC / 2021 | IEEE-754: 6 cycles | all evaluated posit es modes, 400 MHz | p.18 |
errors_and_checks: The operation produces one rounded posit result and propagates zero/NaR cases without IEEE-754 NV/OF/UF/NX flags. # p.10-11
conditions: The product/add path is combinational before retiming, and synthesis retiming creates the six pipeline stages. # p.17-18
evidence: Algorithm 3; Sections 5.3 and 8; Tables 8-10.

### restoring_nonrestoring  (role: instantiates)
mechanism: A shared DIV/SQRT module decodes the operands, determines the result sign/exponent, and performs one iteration of non-restoring fraction division per cycle before posit encoding. FDIV sets the DZ flag for division by zero. # p.10-11
choices:
  style: nonrestoring   # p.11
  bits_per_cycle: 1   # p.11, p.17
new_choices:
  none
slots:
  residual_adder: UNKNOWN
parameters: maximum 32 cycles for es = 2; latency depends on fraction length   # p.17-18
results:
| metric | value | unit | technology / device | baseline | condition | page |
| shared DIV/SQRT area | 19658.88 | μm2 | 65-nm Low-power TSMC / 2021 | IEEE-754: 15805.44 μm2 | es = 2, 400 MHz | p.18 |
| shared DIV/SQRT area | 20226.72 | μm2 | 65-nm Low-power TSMC / 2021 | IEEE-754: 15805.44 μm2 | es = 3, 400 MHz | p.18 |
| shared DIV/SQRT area | 21547.2 | μm2 | 65-nm Low-power TSMC / 2021 | fixed es = 2: 19658.88 μm2 | runtime es = 2/3, 400 MHz | p.18 |
| DIV latency | [3,31,32] | cycles | 65-nm Low-power TSMC / 2021 | IEEE-754: [2,26,27] cycles | es = 2, 400 MHz | p.18 |
| DIV latency | [3,30,31] | cycles | 65-nm Low-power TSMC / 2021 | IEEE-754: [2,26,27] cycles | es = 3, 400 MHz | p.18 |
errors_and_checks: Division by zero sets DZ; NaR operands produce NaR. # p.10-11
conditions: Posit division takes more cycles than IEEE-754 because the posit fraction is longer, which slightly increases application runtime. # p.18-19
evidence: Algorithm 4; Sections 5.4, 8, and 8.1; Tables 8-11.

### digit_recurrence_sqrt_combined  (role: instantiates)
mechanism: The common DIV/SQRT module performs one non-restoring square-root iteration on the fraction per cycle and encodes the resulting root. Negative or NaR square-root inputs produce NaR. # p.10-11
choices:
  shared_with_division: true   # p.11
new_choices:
  none
slots:
  digit_select: UNKNOWN
parameters: one iteration per cycle; latency [3,29,30,31] cycles for es = 2 and [3,28,29,30] cycles for es = 3   # p.18
results:
| metric | value | unit | technology / device | baseline | condition | page |
| SQRT latency | [3,29,30,31] | cycles | 65-nm Low-power TSMC / 2021 | IEEE-754: [2,24,25,26] cycles | es = 2, 400 MHz | p.18 |
| SQRT latency | [3,28,29,30] | cycles | 65-nm Low-power TSMC / 2021 | IEEE-754: [2,24,25,26] cycles | es = 3, 400 MHz | p.18 |
errors_and_checks: Negative or NaR operands produce NaR, while zero produces zero. # p.10-11
conditions: Root latency grows with the available posit fraction length. # p.11, p.18
evidence: Algorithm 4; Sections 5.4 and 8; Table 9.

### shift_round_convert  (role: extends)
mechanism: Integer-to-posit conversion counts leading zeros, shifts the integer to form the fraction, derives the exponent, and invokes the posit encoder. Posit-to-integer conversion shifts the decoded fraction by the exponent, saturates values beyond the signed/unsigned range, and rounds using RNE or RTZ. # p.11-12
choices:
  rounding_modes: RNE and RTZ [outside domain]   # p.11-12
  overflow_behavior: saturate   # p.11
  reuse_add_datapath: false   # p.7, p.11
new_choices:
  none
slots:
  shift_unit: UNKNOWN
  round: UNKNOWN
  lz: UNKNOWN
parameters: 32-bit signed/unsigned integer conversions; 3 cycles for I2F and F2I   # p.11, p.18
results:
| metric | value | unit | technology / device | baseline | condition | page |
| I2F area | 4582.08 | μm2 | 65-nm Low-power TSMC / 2021 | IEEE-754: 4193.76 μm2 | es = 2, 400 MHz | p.18 |
| F2I area | 4206.24 | μm2 | 65-nm Low-power TSMC / 2021 | IEEE-754: 4135.68 μm2 | es = 2, 400 MHz | p.18 |
| I2F delay | 19.161 | ns | Artix-7 xc7a100tcsg324-1 / 2021 | PERC: 19.997 ns | ps = 32, es = 2 | p.19-20 |
| F2I delay | 17.012 | ns | Artix-7 xc7a100tcsg324-1 / 2021 | PERC: 21.322 ns | ps = 32, es = 2 | p.19-20 |
errors_and_checks: Posit conversions set no exception flags. # p.11-12
conditions: RTZ is required for the reported JPEG output sizes to match IEEE-754; default posit RNE produces larger compressed files. # p.15
evidence: Algorithms 5-6; Sections 5.5-5.6 and 7.2; Tables 4, 8-10, 12-13.

### integer_compare_on_bits  (role: instantiates)
mechanism: Posit bit patterns use two’s-complement ordering, so FMIN.S/FMAX.S/FEQ.S/FLT.S/FLE.S reuse the core’s signed/unsigned integer comparison hardware rather than a dedicated FPU comparator. # p.12, p.14
choices:
  signed_zero_ordering: false   # p.6, p.12
new_choices:
  none
slots:
  none
parameters: 32-bit posit comparisons   # p.5-6, p.12
results:
| metric | value | unit | technology / device | baseline | condition | page |
| comparator instances in posit FPU | 0 | comparator | SHAKTI C-class / 2021 | dedicated IEEE-754 comparison logic | integer comparison block reused | p.12, p.14 |
errors_and_checks: Posit comparison has no exceptional cases and sets no flags; two NaRs compare equal. # p.6, p.12
conditions: Integer comparison is valid because posit has one zero/one NaR representation and no unordered values. # p.4, p.6, p.12
evidence: Sections 2.1, 3, 5.7, and 6.

### posit_ieee_interop  (role: extends)
mechanism: The tightly coupled integration replaces the IEEE-754 FPU while retaining RISC-V “F” encodings and the 32-register state. The alternate RoCC integration uses custom opcodes, keeps the posit register file inside the accelerator, and permits separate IEEE-754 and posit FPUs to coexist. # p.5-6, p.14, p.20-22
choices:
  interop_style: isa_posit_replaces_float   # p.14
  quire_present: false   # p.5, p.7
new_choices:
  accelerator_coexistence: {none, separate_rocc_posit_fpu} — retains the IEEE-754 register file/FPU while adding a posit accelerator with its own register file   # p.21-22
slots:
  none
parameters: RV32IMAFC; 32 posit registers of 32 bits; tightly coupled execution-stage offload or write-back-stage RoCC offload   # p.5, p.13-14, p.21-22
results:
| metric | value | unit | technology / device | baseline | condition | page |
| execution-cycle difference between integration approaches | 0 | cycles | SHAKTI C-class / 2021 | tightly coupled “F” replacement | RoCC accelerator | p.22 |
errors_and_checks: none
conditions: The “F” replacement requires fewer compiler changes but excludes simultaneous IEEE-754 use; the RoCC form supports coexistence and additional posit operations but requires new compiler instructions. # p.22
evidence: Figures 4 and 6; Tables 14-17; Sections 3, 6, and 9.

## new_families
none

## space_gaps
* `posit_adder_multiplier.es_bits` does not express a set of es values selected at runtime. # p.12-13
* `shift_round_convert.rounding_modes` lacks the RNE-plus-RTZ combination implemented for posit-to-integer conversion. # p.11-12
* `posit_ieee_interop.interop_style` lacks coexistence through a separate RoCC posit accelerator and register file. # p.21-22
* The posit-unit vocabulary lacks slots for decoder/encoder sharing, although replicated codecs consume substantial area and shared codecs are identified as an optimization. # p.17-18

## open_questions
* The internal multiplier, carry-propagate adder, normalization, and rounding-family implementations are not identified.
* Table 9 does not define which operand/result cases correspond to each value in the bracketed DIV/SQRT cycle lists.
* The generator is described as supporting any ps/es combination, but complete automated verification is reported only for ps = 32, es = 2; es = 3 receives manual corner-case verification.
