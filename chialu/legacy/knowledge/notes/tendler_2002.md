---
handle: tendler_2002
citation: J. M. Tendler, J. S. Dodson, J. S. Fields, H. Le, B. Sinharoy, "POWER4 System Microarchitecture", IBM Journal of Research and Development, vol. 46, no. 1, pp. 5-25, 2002.
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU, VEC_DOT_ACC]
formats: [PowerPC 32-bit, PowerPC 64-bit]
authority: landmark
pages_read: 5-25 / 25
---

## summary
The paper describes the POWER4 processor/system microarchitecture, including two fully pipelined floating-point units per processor that can each start a fused multiply-add every cycle. The paper reports execution latency/throughput and fabrication details but does not disclose the fused multiply-add arithmetic structure or rounding implementation.

## families
### classic_fma  (role: instantiates)
mechanism: Each POWER4 processor contains two identical floating-point execution units. Each unit can start one fused multiply-add per cycle, and the two units provide a maximum of four floating-point operations per cycle per processor. Floating-point instructions use six execution cycles, while full pipelining permits two floating-point instructions to issue per processor cycle. A dependent floating-point instruction cannot issue within six cycles of its producer. # p.8, p.14
choices:
  pipeline_depth: 6   # p.14
new_choices:
  none
slots:
  none
parameters: two floating-point units per processor; six execution cycles; initiation interval 1 cycle per unit; maximum two floating-point instructions issued per processor cycle; maximum four FLOPs/cycle per processor   # p.8, p.14
results:
| metric | value | unit | technology / device | baseline | condition | page |
| floating-point execution latency | 6 | cycles | 0.18-µm copper SOI / POWER4 (2002) | none | floating-point instruction | p.14 |
| fused multiply-add initiation interval | 1 | cycle | 0.18-µm copper SOI / POWER4 (2002) | none | each of two floating-point units | p.8, p.14 |
| peak floating-point throughput | 4 | FLOPs/cycle/processor | 0.18-µm copper SOI / POWER4 (2002) | none | two fused multiply-add instructions started per cycle | p.8 |
| introduced processor frequency | 1.1 GHz and 1.3 GHz | GHz | 0.18-µm copper SOI / POWER4 (2002) | none | initial POWER4 systems | p.5 |
errors_and_checks: none
conditions: A floating-point instruction dependent on an earlier floating-point instruction cannot issue within six cycles of the producer; independent floating-point instructions can issue during that interval. # p.14
evidence: POWER4 processor overview and Figure 3 on p.8; instruction execution pipeline and Figure 4 on pp.13-14.

## new_families
none

## space_gaps
* The vocabulary lacks a choice that records the number of replicated FMA pipelines per processor; POWER4 provides two identical floating-point units. # p.8
* The vocabulary lacks an initiation-interval choice for classic_fma; each POWER4 floating-point unit can start a fused multiply-add every cycle. # p.8, p.14

## open_questions
* The paper does not identify the multiplier, carry-propagate adder, alignment, leading-zero, or rounding families used inside the fused multiply-add units.
* The paper does not state whether the reported six-cycle floating-point execution latency applies uniformly to every fused multiply-add instruction variant.
* The paper states compatibility with 32-bit and 64-bit PowerPC applications but does not identify the implemented IEEE floating-point formats.
