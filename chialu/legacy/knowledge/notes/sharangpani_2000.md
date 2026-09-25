---
handle: sharangpani_2000
citation: H. Sharangpani, K. Arora, "Itanium Processor Microarchitecture", IEEE Micro, vol. 20, no. 5, pp. 24-43, 2000.
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU, VEC_DOT_ACC]
formats: [fp32, fp64, extended_precision, mixed_precision]
authority: landmark
pages_read: 20 / 20
---

## summary
The document describes Itanium’s arithmetic resources, including two fully pipelined 82-bit FMAC units and supplemental single-precision FMAC units (p.38). The document reports latency/throughput/data-feed constraints and software reuse of the FMACs for division/integer multiplication, but it does not disclose their internal multiplier/adder/rounding structures (pp.38-39).

## families
### classic_fma  (role: instantiates)
mechanism: The FPU uses two fully pipelined, native 82-bit FMAC units supporting single-, double-, extended-, and mixed-mode-precision computation. Each unit executes FMA, FMS, FNMA, FCVTFX, and FCVTXF operations; bypassed FMAC arithmetic has five clock cycles of latency. The hardware also executes two integer XMA operations in parallel after operands pass through setf/getf transfer paths (pp.38-39).
choices:
new_choices:
  operation_set: {FMA, FMS, FNMA, FCVTFX, FCVTXF, XMA} — operations explicitly assigned to the FMAC hardware   # pp.38-39
  integer_multiply_add_support: true — the FMAC hardware executes integer XMA operations   # p.39
slots:
  none
parameters: 2 fully pipelined FMAC units; native datapath width 82 bits; single/double/extended/mixed precision; FMAC arithmetic latency 5 clock cycles; operating frequency 800 MHz   # pp.24,38
results:
| metric | value | unit | technology / device | baseline | condition | page |
| FMAC arithmetic latency | 5 | clock cycles | 0.18-micron process / Itanium; 2000 | UNKNOWN | FMAC arithmetic operations bypassed between units | pp.38,24 |
| double-precision peak throughput | 4 | flops/clock | 0.18-micron process / Itanium; 2000 | UNKNOWN | Two 82-bit FMAC units | pp.38,24 |
| double-precision peak performance | 3.2 | Gflops | 0.18-micron process / Itanium; 2000 | UNKNOWN | 800 MHz | pp.38,24 |
| fixed multiply latency | 7 | clock cycles | 0.18-micron process / Itanium; 2000 | UNKNOWN | Floating-point execution resource | pp.31,24 |
| integer multiply sequence latency | 18 | clocks | 0.18-micron process / Itanium; 2000 | UNKNOWN | 9-clock setf, 7-clock fmul, and 2-clock getf sequence | pp.39,24 |
| 1,024-bit RSA performance | over 1,000 | decryptions per second | 0.18-micron process / Itanium; 2000 | UNKNOWN | Twin XMA pipelines at 800 MHz using private keys | pp.39,24 |
errors_and_checks: No numerical error bound is reported. SIR hardware provides precise numeric exceptions through early operand examination and hardware microreplay; FPSR fields provide precision/rounding controls and status for one primary and three speculative tracks (pp.38-39).
conditions: Peak double-precision throughput requires six operands per clock; the L2 cache supplies at most four, so the other two require register-file reuse and a primed cache (p.38). Division executes in software and can use software-pipelined operations across the twin FMAC units, but the division algorithm is not identified (p.38). Integer multiplication through the FMAC incurs setf/getf transfer latency (p.39).
evidence: Table B (p.31); “Floating-point feature set,” “FMAC units,” Figure B, and “FPU and integer core coupling” (pp.38-39).

### multi_precision_simd_fma  (role: instantiates)
mechanism: Each main 82-bit FMAC supports single-, double-, or extended-precision operations. An 82-bit register read supplies two single-precision SIMD operands; the second operand is peeled off and sent to a supplemental single-precision FMAC. Two SIMD instructions therefore execute four single-precision FMAC operations per clock (p.38).
choices:
  lane_split: {1x82_extended, 1x64, 2x32} [outside domain]   # p.38
new_choices:
  lane_implementation: main_fmac_plus_supplemental_single_precision_unit — the second 2x32 lane uses auxiliary hardware rather than fracturing the main FMAC   # p.38
slots:
  none
parameters: 2 main 82-bit FMAC units; 2 supplemental single-precision FMAC units; 2 SIMD instructions/clock; 4 single-precision FMAC operations/clock   # p.38
results:
| metric | value | unit | technology / device | baseline | condition | page |
| single-precision peak throughput | 8 | flops/clock | 0.18-micron process / Itanium; 2000 | UNKNOWN | Two SIMD instructions in parallel with supplemental FMAC units | pp.38,24 |
| single-precision peak performance | 6.4 | Gflops | 0.18-micron process / Itanium; 2000 | UNKNOWN | 800 MHz | pp.38,24 |
errors_and_checks: No SIMD-specific numerical error bound is reported; precision/rounding controls and numeric status reside in the FPSR (p.39).
conditions: Two ldf-pair instructions can supply four double-precision values per clock only when each consecutive operand pair targets one even and one odd floating-point register (p.38). Peak FMAC use also requires two operands per clock from register reuse because the L2 cache supplies only four of the required six operands (p.38).
evidence: “Floating-point feature set,” “FMAC units,” “Operand bandwidth,” and Figure B (p.38).

## new_families
none

## space_gaps
* `multi_precision_simd_fma.lane_split` lacks the native `1x82_extended` mode reported for each main FMAC (p.38).
* `multi_precision_simd_fma` lacks a `lane_implementation` choice distinguishing fractured/shared lanes from Itanium’s peeled supplemental single-precision units (p.38).
* `classic_fma` lacks choices for its supported operation set and integer XMA reuse (pp.38-39).

## open_questions
* The document does not identify the FMAC’s internal multiplier, CPA, alignment, normalization, or rounding families.
* The document does not identify the software division algorithm, so no divider family can be assigned.
* The document does not state the integer operand width used by the XMA path.
