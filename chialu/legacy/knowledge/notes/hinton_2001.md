---
handle: hinton_2001
citation: G. Hinton, D. Sager, M. Upton, D. Boggs, D. Carmean, A. Kyker, P. Roussel, "The Microarchitecture of the Pentium 4 Processor", Intel Technology Journal, Q1, 2001.
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU, other]
formats: [int8, int16, int32, int64, fp32, fp64, x87_extended]
authority: landmark
pages_read: 13 / 13
---

## summary
The paper describes the shipped Pentium 4 execution units, including a double-pumped staggered integer ALU and an FP divider using double-pumped radix-2 SRT division/square root (p.8-10). The paper also reports arithmetic latency/throughput but does not disclose the internal adder, multiplier, or SRT digit-selection circuits (p.8-10).

## families
### srt_radix2  (role: instantiates)
mechanism: The FP divider executes divide, square-root, and remainder uops with a double-pumped SRT radix-2 algorithm. The double pumping produces two quotient or square-root bits during each main processor clock (p.10).
choices: none
new_choices:
  double_pumped: true — two radix-2 steps are performed per main processor clock # p.10
slots:
  digit_select: UNKNOWN # p.10
parameters: radix 2; 2 quotient or square-root bits per clock; typical divide latency about 60 clocks # p.9-10
results:
| metric | value | unit | technology / device | baseline | condition | page |
| output rate | two | bits of quotient (or square root) every clock cycle | Intel 0.18u CMOS / Pentium 4 / 2000 | UNKNOWN | double-pumped SRT radix-2 FP divider | p.10 |
| typical divide latency | about 60 | clocks | Intel 0.18u CMOS / Pentium 4 / 2000 | UNKNOWN | typical integer multiply/divide forms; opcode and format are not specified | p.9 |
errors_and_checks: none
conditions: The divider handles divide, square-root, and remainder uops; residual encoding, quotient prediction, and digit-selection implementation are not disclosed (p.10).
evidence: “Complex Integer Operations” (p.9); “FP/SSE Execution Units” (p.10).

### digit_recurrence_sqrt_combined  (role: instantiates)
mechanism: One FP divider executes divide and square-root uops using a double-pumped SRT radix-2 algorithm. The shared unit emits two quotient or square-root bits per main processor clock (p.10).
choices:
  radix: 2 # p.10
  shared_with_division: true # p.10
new_choices:
  double_pumped: true — two radix-2 steps are performed per main processor clock # p.10
slots:
  digit_select: UNKNOWN # p.10
parameters: radix 2; 2 square-root bits per clock; on-the-fly conversion and subiteration speculation UNKNOWN # p.10
results:
| metric | value | unit | technology / device | baseline | condition | page |
| square-root output rate | two | bits every clock cycle | Intel 0.18u CMOS / Pentium 4 / 2000 | UNKNOWN | shared double-pumped SRT radix-2 FP divider | p.10 |
errors_and_checks: none
conditions: The document establishes shared divide/square-root execution but does not describe the result-dependent subtrahend, residual representation, digit-selection logic, or conversion method (p.10).
evidence: “FP/SSE Execution Units” (p.10).

## new_families
### staggered_add  (domain: adder, closest: ripple_carry, why_not: The document specifies temporal low/high segmentation and flag phasing but does not identify the internal full-adder or carry-propagation topology.)
mechanism: A 32-bit ALU addition is divided across three fast-clock cycles. Bits <15:0> are computed first and immediately forwarded to a dependent operation. Bits <31:16> are computed in the next fast cycle using the low segment’s carry-out. Flags are processed in the third fast cycle. The fast clock runs at twice the main processor clock, so dependent ALU operations have an effective latency of one-half main clock cycle (p.8-9).
choices:
  low_segment_width_bits: {16} # p.8
  fast_clock_ratio: {2} # p.8
  flag_phase: {third_fast_cycle} # p.8-9
results:
| metric | value | unit | technology / device | baseline | condition | page |
| effective dependent ALU latency | one-half | clock cycle | Intel 0.18u CMOS / Pentium 4 / 2000 | UNKNOWN | frequent fully dependent ALU operations | p.8 |
| ALU fast-clock frequency | 3 | GHz | Intel 0.18u CMOS / Pentium 4 / 2000 | UNKNOWN | 1.5GHz Pentium 4 processor | p.1, p.3 |
| fast-clock sequence length | three | fast clock cycles | Intel 0.18u CMOS / Pentium 4 / 2000 | UNKNOWN | low 16 bits, high 16 bits, then flags | p.8-9 |
| workload share using ALU loop | 60-70% | of all uops | Intel 0.18u CMOS / Pentium 4 / 2000 | UNKNOWN | typical integer programs | p.8 |
evidence: “Low Latency Integer ALU” and Figure 7 (p.8-9).

## space_gaps
* The adder vocabulary lacks a temporal segmentation choice for a staggered low-part/high-part/flags pipeline (p.8-9).
* `srt_radix2` lacks choices for double pumping and quotient bits produced per main clock (p.10).
* The vocabulary lacks an execution-cluster family for a partially pipelined FP/SSE port shared by addition, multiplication, division, and MMX operations (p.10).

## open_questions
* The internal topology and circuit style of each 16-bit staggered adder segment are not disclosed.
* The SRT residual representation, estimate width, digit-selection circuit, and conversion method are not disclosed.
* The “about 14 and 60 clocks” multiply/divide latencies are not assigned to specific opcodes or operand formats (p.9).
