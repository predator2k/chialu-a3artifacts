---
handle: sinharoy_2015
citation: B. Sinharoy, et al., "IBM POWER8 Processor Core Microarchitecture", IBM Journal of Research and Development, vol. 59, no. 1, pp. 2:1-2:21, 2015.
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU, VEC_SFU, VEC_DOT_ACC, other]
formats: [int8, int16, int32, int64, fp32, fp64, decimal_fp, decimal_fixed_31_digit]
authority: landmark
pages_read: 2:1–2:21 / 21 pages
---

## summary
The paper describes the POWER8 commercial processor core, including its fixed-point radix-16 SRT dividers, symmetric vector/scalar pipelines, multi-precision floating-point FMA execution, and decimal floating-point unit. The core is fabricated in 22-nm SOI technology and targets greater single-thread and per-core throughput than POWER7. Arithmetic-unit implementation details below the pipeline level are generally not disclosed.

## families
### srt_high_radix  (role: instantiates)
mechanism: Each of the two fixed-point pipelines contains a divider that uses the Sweeney, Robertson, and Tocher algorithm with radix 16. The divider accepts 32-bit or 64-bit operations. Other FXU execution units may receive instructions during a multi-cycle divide unless a result-bus conflict occurs. # p.2:17
choices:
  radix: 16   # p.2:17
new_choices:
  none
slots:
  none
parameters: 2 divider instances; operand width 32 or 64 bits; multi-cycle latency with cycle count unspecified   # p.2:17
results:
none
errors_and_checks: none
conditions: ALU/ROT/BSU/CNT/MXU/MUL instructions may issue under an active divide except when a result-bus conflict occurs.   # p.2:17
evidence: Fixed-Point Unit section and Figure 7, p.2:16–2:17

### replicated_lanes  (role: instantiates)
mechanism: Two fully symmetric VSU pipelines dual-issue scalar/vector instructions from the VMX/VSX/FPU instruction categories. Each pipeline has an associated vector register file; the files are synchronized in single-thread mode and operate separately for the two thread sets in SMT modes. The VSU includes two-cycle VMX/VSX permutation pipelines and reuses floating-point multiplier hardware for packed integer multiplication. # p.2:17–2:18
choices:
  register_file: fp_shared   # p.2:17–2:18
new_choices:
  pipeline_symmetry: fully_symmetric — Both VSU pipelines execute the supported VMX/VSX instruction categories.   # p.2:17
slots:
  none
parameters: 2 VSU pipelines; dual issue; 2-cycle VMX/VSX permute latency; packed int32/int16/int8 multiplication   # p.2:17–2:18
results:
| metric | value | unit | technology / device | baseline | condition | page |
| VMX/VSX permute latency | 2 | cycles | 22-nm SOI, 15 layers of metal; 2015 | POWER7 processor; improvement stated but not quantified | VSU permute pipeline | p.2:17 |
| packed 32-bit integer multiply throughput | 8 | word multiplies per cycle | 22-nm SOI, 15 layers of metal; 2015 | none | signed or unsigned integer data, per core | p.2:18 |
| packed 16-bit integer multiply throughput | 16 | halfword multiplies per cycle | 22-nm SOI, 15 layers of metal; 2015 | none | signed or unsigned integer data, per core | p.2:18 |
| packed 8-bit integer multiply throughput | 32 | byte multiplies per cycle | 22-nm SOI, 15 layers of metal; 2015 | none | signed or unsigned integer data, per core | p.2:18 |
errors_and_checks: none
conditions: Packed integer multiply reuses floating-point multiplier hardware and therefore adds little chip area; the paper does not quantify that area.   # p.2:18
evidence: Organization of the POWER8 processor core, p.2:3; Vector-and-Scalar/Decimal Floating-Point Units section and Figure 8, p.2:17–2:18

### multi_precision_simd_fma  (role: instantiates)
mechanism: Four floating-point pipelines each execute double-precision multiply-add operations. A single FPU operates on either one 64-bit double-precision datum or two 32-bit single-precision data, allowing the core to execute four double-precision or eight single-precision fused multiply-add operations per cycle. # p.2:3, p.2:18
choices:
  lane_split: [1x64, 2x32]   # p.2:18
new_choices:
  none
slots:
  none
parameters: 4 floating-point pipelines; 1 fp64 or 2 fp32 operations per FPU; 4 fp64 or 8 fp32 fused multiply-add operations per cycle per core; 6-cycle floating-point bypass latency   # p.2:17–2:18
results:
| metric | value | unit | technology / device | baseline | condition | page |
| double-precision throughput | 8 | floating-point operations per cycle per core | 22-nm SOI, 15 layers of metal; 2015 | POWER7+ processor; similar peak stated | 4 double-precision fused multiply-adds per cycle | p.2:2 |
| single-precision throughput | 16 | floating-point operations per cycle per core | 22-nm SOI, 15 layers of metal; 2015 | POWER7 processor; twice as high | 8 single-precision fused multiply-adds per cycle | p.2:18 |
| floating-point bypass latency | 6 | cycles | 22-nm SOI, 15 layers of metal; 2015 | POWER7 processor; unchanged | fast bypass within the floating-point unit | p.2:17 |
errors_and_checks: none
conditions: The two FPUs on each VSU pipe operate pairwise for vector floating-point instructions. A single FPU selects fp64 or two-way fp32 operation rather than executing both modes concurrently.   # p.2:18
evidence: Organization of the POWER8 processor core, p.2:3; Vector-and-Scalar/Decimal Floating-Point Units section and Figure 8, p.2:17–2:18

### commercial_decimal_fpu  (role: instantiates)
mechanism: A dedicated decimal floating-point pipeline executes Power ISA decimal floating-point instructions. The DFU is fully pipelined, is attached symmetrically to both UniQueue ports, and natively supports signed decimal fixed-point addition/subtraction with operands up to 31 decimal digits. # p.2:3, p.2:18
choices:
  implementation: hardware_dfu   # p.2:3, p.2:18
new_choices:
  issue_structure: fully_pipelined — The DFU accepts pipelined execution and has a stated dependent issue-to-issue latency.   # p.2:18
slots:
  none
parameters: 1 DFU pipeline; dependent issue-to-issue latency 13 cycles; signed decimal fixed-point operands up to 31 decimal digits   # p.2:18
results:
| metric | value | unit | technology / device | baseline | condition | page |
| dependent instruction issue-to-issue latency | 13 | cycles | 22-nm SOI, 15 layers of metal; 2015 | none | DFU dependent instructions | p.2:18 |
| native decimal fixed-point operand length | up to 31 | decimal digits | 22-nm SOI, 15 layers of metal; 2015 | none | signed decimal fixed-point add/subtract | p.2:18 |
errors_and_checks: IEEE 754-2008 compliant; the paper gives no per-operation rounding-error or exception-coverage measurements.   # p.2:18
conditions: DFU and cryptographic instructions share VSU issue slots, with at most one instruction of each type issued per cycle.   # p.2:11
evidence: Organization of the POWER8 processor core, p.2:3; Instruction Sequencing Unit, p.2:11; Vector-and-Scalar/Decimal Floating-Point Units, p.2:18

## new_families
none

## space_gaps
* `multi_precision_simd_fma` lacks a choice for sharing one multiplier datapath between floating-point FMA and packed int32/int16/int8 multiplication.   # p.2:18
* `commercial_decimal_fpu` is labeled variable-iteration in the vocabulary, while the POWER8 DFU is described as fully pipelined with a 13-cycle dependent issue-to-issue latency.   # p.2:18
* `replicated_lanes` lacks a pipeline-symmetry choice for two vector pipelines that both execute the VMX and VSX instruction categories.   # p.2:17

## open_questions
* The paper does not specify the SRT divider’s digit redundancy, overlapped-stage count, digit-selection implementation, or exact latency.
* The paper does not specify the FMA multiplier/reduction/final-adder/rounding topology or whether rounding hardware is shared between fp32 and fp64 modes.
* The paper does not specify the DFU datapath width, internal decimal encoding, significand-adder family, multiplier family, or divider family.
* The paper does not state whether packed integer multiply uses partitioned partial products, independently replicated lanes, or another internal multiplier organization.
