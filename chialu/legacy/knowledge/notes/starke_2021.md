---
handle: starke_2021
citation: W. J. Starke, B. W. Thompto, J. A. Stuecheli, J. E. Moreira, "IBM's POWER10 Processor", IEEE Micro, vol. 41, no. 2, pp. 7-14, 2021.
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_DOT_ACC]
formats: [fp64, fp32, fp16, bf16, int16, int8, uint8, int4]
authority: incremental
pages_read: 7-14 / 8
---

## summary
The document presents POWER10’s matrix math accelerator, which performs rank-1/-2/-4/-8 matrix updates using local 512-bit accumulator registers and packed floating-point/integer inputs (p.11). The accelerator reaches 64 fp64 or 1024 int4 operations per cycle per SMT8 core and provides four-fold core-level matrix throughput over POWER9 SIMD (pp.11-12).

## families
### tensor_core_mixed_precision_mac  (role: instantiates)
mechanism: The matrix math accelerator executes Power ISA 3.1 matrix instructions using two or three 128-bit vector-scalar source registers and eight local 512-bit accumulator registers. Instructions perform rank-1, rank-2, rank-4, or rank-8 updates on a 4 × 2 or 4 × 4 matrix. Packed inputs contain fp64, fp32, fp16, bfloat16, signed int16, signed/unsigned int8, or signed int4 elements. Local accumulator storage reduces bits × distance relative to an equivalent 512-bit SIMD operation (p.11).
choices:
new_choices:
  matrix_update_rank: {1, 2, 4, 8} — supported rank-update instruction shapes (p.11)
  accumulator_matrix_shape: {4x2, 4x4} — matrix shapes held in an accumulator (p.11)
  accumulator_locality: unit_local_registers — accumulators remain inside the matrix unit to reduce data movement (p.11)
slots:
  none
parameters: eight 512-bit accumulator registers; two or three 128-bit source registers; 4 × 2 or 4 × 4 accumulator matrices; rank-1/-2/-4/-8 updates; up to two matrix instructions per cycle for one thread (pp.11-12)
results:
| metric | value | unit | technology / device | baseline | condition | page |
| core matrix-math throughput gain | four-fold | throughput | Samsung’s 7-nm / POWER10 / 2021 | POWER9 core SIMD | matrix math operations | p.11 |
| fp64 maximum operation rate | 64 | floating-point operations per cycle per SMT8 core | Samsung’s 7-nm / POWER10 / 2021 | none | double-precision inputs | p.12 |
| int4 maximum operation rate | 1024 | integer operations per cycle per SMT8 core | Samsung’s 7-nm / POWER10 / 2021 | none | 4-bit integer inputs | p.12 |
| LINPACK socket performance gain | ten times faster | performance | Samsung’s 7-nm / POWER10 / 2021 | dual-socket POWER9 S924 | projected dual-socket POWER10 | p.13 |
| Resnet-50 fp32 socket performance gain | ten times faster | performance | Samsung’s 7-nm / POWER10 / 2021 | standard single-precision Resnet-50 on POWER9 | fp32 inputs | p.13 |
| Resnet-50 bf16 socket performance gain | 15 times faster | performance | Samsung’s 7-nm / POWER10 / 2021 | standard single-precision Resnet-50 on POWER9 | bfloat16 inputs | p.13 |
| Resnet-50 int8 socket performance gain | 20 times faster | performance | Samsung’s 7-nm / POWER10 / 2021 | standard single-precision Resnet-50 on POWER9 | 8-bit integer inputs | p.13 |
errors_and_checks: none
conditions: Local accumulator storage reduces data movement relative to an equivalent 512-bit SIMD operation, which improves power efficiency and permits higher frequency (p.11). Maximum operation rate increases as the input type becomes shorter (p.12). Socket comparisons use a dual-socket POWER10 system against a dual-socket POWER9 S924 server (p.13). Performance figures come from presilicon simulations correlated against first-pass silicon and use projected production frequency because final chips were unavailable (p.13).
evidence: POWER10 Core section and Figure 3 (pp.10-11); Figure 4 and accompanying operation-rate discussion (p.12); Figures 5-6 and POWER10 Performance section (p.13)

## new_families
none

## space_gaps
* `tensor_core_mixed_precision_mac` lacks choices for rank-update shape, accumulator matrix shape, and unit-local accumulator registers (p.11).
* `tensor_core_mixed_precision_mac` does not represent the documented fp64/fp32/fp16/bf16/int16/int8/uint8/int4 operand-format range (p.11).

## open_questions
* The document does not state the internal multiplier/reduction topology, product exactness, partial-sum rounding, exponent-alignment policy, or subnormal behavior.
* The document does not separate the contributions of increased core count, accelerator throughput, and projected frequency in the socket-level benchmark gains (p.13).
