---
handle: dedinechin_2011
citation: F. de Dinechin, B. Pasca, "Designing Custom Arithmetic Data Paths with FloPoCo", IEEE Design and Test of Computers, vol. 28, no. 4, 2011
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU, VEC_SFU, VEC_DOT_ACC]
formats: [fp32, fp64, custom_fp(9,31), custom_fp(10,36)]
authority: survey
pages_read: 10 / 10
---

## summary
FloPoCo generates parameterized/pipelined FPGA arithmetic datapaths from operator specifications and a target frequency. The demonstrated fused X²+Y²+Z² datapath uses three squarers, shared alignment/addition, deferred normalization/rounding, and three guard bits for last-bit accuracy. Virtex/Stratix results compare composed multiplier/squarer implementations with the fused implementation.

## families
### multi_term_fused_dot  (role: proposes)
mechanism: The X²+Y²+Z² datapath sorts the input exponents, computes three significand squares in parallel, aligns the smaller terms, adds the extended significands, and performs normalization/rounding/packing once. The fused structure removes intermediate rounding/normalization and logic for adding unlike signs. Frequency-directed generation inserts synchronization barriers according to the target FPGA/timing model. # p.20–25
choices:
  alignment_strategy: single_wide_window   # p.21
  rounding_contract: last_bit_accurate [outside domain]   # p.20–21
  normalization_deferral: final_only   # p.20–21
new_choices:
  internal_guard_bits: 3 — extra internal significand bits that ensure last-bit accuracy   # p.21
  pipeline_target: 50/100/200/300/350 MHz — requested frequency drives synchronization-barrier placement   # p.20–22
slots:
  multiplier: squarer   # p.20–21
parameters: N=3 squared terms; tested formats (8,23), (10,36), and (11,52); g=3; reported latency 0 to 50 cycles; target frequency 50 to 350 MHz.   # p.21–22
results:
| metric | value | unit | technology / device | baseline | condition | page |
| latency | 34 | cycles | Virtex-4 xc4vfx100-12; year UNKNOWN | reference | (8,23); LogiCore; target 350 MHz | p.21 |
| frequency | 482 | MHz | Virtex-4 xc4vfx100-12; year UNKNOWN | reference | (8,23); LogiCore | p.21 |
| logic | 1,356 | slices | Virtex-4 xc4vfx100-12; year UNKNOWN | reference | (8,23); LogiCore | p.21 |
| DSP use | 12 | DSPs | Virtex-4 xc4vfx100-12; year UNKNOWN | reference | (8,23); LogiCore | p.21 |
| latency | 35 | cycles | Virtex-4 xc4vfx100-12; year UNKNOWN | LogiCore | (8,23); option 1 | p.21 |
| frequency | 327 | MHz | Virtex-4 xc4vfx100-12; year UNKNOWN | LogiCore | (8,23); option 1 | p.21 |
| logic | 1,279 | slices | Virtex-4 xc4vfx100-12; year UNKNOWN | LogiCore | (8,23); option 1 | p.21 |
| DSP use | 12 | DSPs | Virtex-4 xc4vfx100-12; year UNKNOWN | LogiCore | (8,23); option 1 | p.21 |
| latency | 35 | cycles | Virtex-4 xc4vfx100-12; year UNKNOWN | LogiCore | (8,23); option 2 | p.21 |
| frequency | 333 | MHz | Virtex-4 xc4vfx100-12; year UNKNOWN | LogiCore | (8,23); option 2 | p.21 |
| logic | 1,043 | slices | Virtex-4 xc4vfx100-12; year UNKNOWN | LogiCore | (8,23); option 2 | p.21 |
| DSP use | 9 | DSPs | Virtex-4 xc4vfx100-12; year UNKNOWN | LogiCore | (8,23); option 2 | p.21 |
| latency | 11 | cycles | Virtex-4 xc4vfx100-12; year UNKNOWN | LogiCore | (8,23); option 3 | p.21 |
| frequency | 369 | MHz | Virtex-4 xc4vfx100-12; year UNKNOWN | LogiCore | (8,23); option 3 | p.21 |
| logic | 470 | slices | Virtex-4 xc4vfx100-12; year UNKNOWN | LogiCore | (8,23); option 3 | p.21 |
| DSP use | 9 | DSPs | Virtex-4 xc4vfx100-12; year UNKNOWN | LogiCore | (8,23); option 3 | p.21 |
| latency | 50 | cycles | Virtex-4 xc4vfx100-12; year UNKNOWN | reference | (11,52); LogiCore; target 350 MHz | p.21 |
| frequency | 354 | MHz | Virtex-4 xc4vfx100-12; year UNKNOWN | reference | (11,52); LogiCore | p.21 |
| logic | 3,074 | slices | Virtex-4 xc4vfx100-12; year UNKNOWN | reference | (11,52); LogiCore | p.21 |
| DSP use | 48 | DSPs | Virtex-4 xc4vfx100-12; year UNKNOWN | reference | (11,52); LogiCore | p.21 |
| latency | 47 | cycles | Virtex-4 xc4vfx100-12; year UNKNOWN | LogiCore | (11,52); option 1 | p.21 |
| frequency | 319 | MHz | Virtex-4 xc4vfx100-12; year UNKNOWN | LogiCore | (11,52); option 1 | p.21 |
| logic | 3,859 | slices | Virtex-4 xc4vfx100-12; year UNKNOWN | LogiCore | (11,52); option 1 | p.21 |
| DSP use | 48 | DSPs | Virtex-4 xc4vfx100-12; year UNKNOWN | LogiCore | (11,52); option 1 | p.21 |
| latency | 45 | cycles | Virtex-4 xc4vfx100-12; year UNKNOWN | LogiCore | (11,52); option 2 | p.21 |
| frequency | 322 | MHz | Virtex-4 xc4vfx100-12; year UNKNOWN | LogiCore | (11,52); option 2 | p.21 |
| logic | 3,137 | slices | Virtex-4 xc4vfx100-12; year UNKNOWN | LogiCore | (11,52); option 2 | p.21 |
| DSP use | 18 | DSPs | Virtex-4 xc4vfx100-12; year UNKNOWN | LogiCore | (11,52); option 2 | p.21 |
| latency | 16 | cycles | Virtex-4 xc4vfx100-12; year UNKNOWN | LogiCore | (11,52); option 3 | p.21 |
| frequency | 368 | MHz | Virtex-4 xc4vfx100-12; year UNKNOWN | LogiCore | (11,52); option 3 | p.21 |
| logic | 1,866 | slices | Virtex-4 xc4vfx100-12; year UNKNOWN | LogiCore | (11,52); option 3 | p.21 |
| DSP use | 18 | DSPs | Virtex-4 xc4vfx100-12; year UNKNOWN | LogiCore | (11,52); option 3 | p.21 |
| latency | 6 | cycles | Virtex-4; year UNKNOWN | none | (10,36); option 3; target 200 MHz | p.22 |
| frequency | 203 | MHz | Virtex-4; year UNKNOWN | none | (10,36); option 3; target 200 MHz | p.22 |
| logic | 874 | slices | Virtex-4; year UNKNOWN | none | (10,36); option 3; target 200 MHz | p.22 |
| DSP use | 9 | DSPs | Virtex-4; year UNKNOWN | none | (10,36); option 3; target 200 MHz | p.22 |
| latency | 2 | cycles | Virtex-4; year UNKNOWN | none | (10,36); option 3; target 100 MHz | p.22 |
| frequency | 109 | MHz | Virtex-4; year UNKNOWN | none | (10,36); option 3; target 100 MHz | p.22 |
| logic | 809 | slices | Virtex-4; year UNKNOWN | none | (10,36); option 3; target 100 MHz | p.22 |
| DSP use | 9 | DSPs | Virtex-4; year UNKNOWN | none | (10,36); option 3; target 100 MHz | p.22 |
| latency | 0 | cycles | Virtex-4; year UNKNOWN | none | (10,36); option 3; target 50 MHz | p.22 |
| frequency | 51 | MHz | Virtex-4; year UNKNOWN | none | (10,36); option 3; target 50 MHz | p.22 |
| logic | 751 | slices | Virtex-4; year UNKNOWN | none | (10,36); option 3; target 50 MHz | p.22 |
| DSP use | 9 | DSPs | Virtex-4; year UNKNOWN | none | (10,36); option 3; target 50 MHz | p.22 |
| latency | 7 | cycles | Virtex-4; year UNKNOWN | none | (11,52); option 3; target 200 MHz | p.22 |
| frequency | 187 | MHz | Virtex-4; year UNKNOWN | none | (11,52); option 3; target 200 MHz | p.22 |
| logic | 1,285 | slices | Virtex-4; year UNKNOWN | none | (11,52); option 3; target 200 MHz | p.22 |
| DSP use | 18 | DSPs | Virtex-4; year UNKNOWN | none | (11,52); option 3; target 200 MHz | p.22 |
| latency | 3 | cycles | Virtex-4; year UNKNOWN | none | (11,52); option 3; target 100 MHz | p.22 |
| frequency | 102 | MHz | Virtex-4; year UNKNOWN | none | (11,52); option 3; target 100 MHz | p.22 |
| logic | 1,272 | slices | Virtex-4; year UNKNOWN | none | (11,52); option 3; target 100 MHz | p.22 |
| DSP use | 18 | DSPs | Virtex-4; year UNKNOWN | none | (11,52); option 3; target 100 MHz | p.22 |
| latency | 2 | cycles | Virtex-4; year UNKNOWN | none | (11,52); option 3; target 50 MHz | p.22 |
| frequency | 64 | MHz | Virtex-4; year UNKNOWN | none | (11,52); option 3; target 50 MHz | p.22 |
| logic | 1,130 | slices | Virtex-4; year UNKNOWN | none | (11,52); option 3; target 50 MHz | p.22 |
| DSP use | 18 | DSPs | Virtex-4; year UNKNOWN | none | (11,52); option 3; target 50 MHz | p.22 |
| latency | 5 | cycles | Virtex-5 xc5vfx100T-3; year UNKNOWN | none | (10,36); option 3; target 200 MHz | p.22 |
| frequency | 196 | MHz | Virtex-5 xc5vfx100T-3; year UNKNOWN | none | (10,36); option 3 | p.22 |
| logic | 1,444 | L | Virtex-5 xc5vfx100T-3; year UNKNOWN | none | (10,36); option 3 | p.22 |
| registers | 762 | R | Virtex-5 xc5vfx100T-3; year UNKNOWN | none | (10,36); option 3 | p.22 |
| DSP use | 9 | DSP48E | Virtex-5 xc5vfx100T-3; year UNKNOWN | none | (10,36); option 3 | p.22 |
| latency | 8 | cycles | Stratix II EP2S15F484C3; year UNKNOWN | none | (10,36); option 3; target 200 MHz | p.22 |
| frequency | 179 | MHz | Stratix II EP2S15F484C3; year UNKNOWN | none | (10,36); option 3 | p.22 |
| logic | 1,395 | L | Stratix II EP2S15F484C3; year UNKNOWN | none | (10,36); option 3 | p.22 |
| registers | 1,295 | R | Stratix II EP2S15F484C3; year UNKNOWN | none | (10,36); option 3 | p.22 |
| DSP use | 18 | 9-bit multipliers | Stratix II EP2S15F484C3; year UNKNOWN | none | (10,36); option 3 | p.22 |
| latency | 4 | cycles | Stratix IV EP4S40G2F40I1; year UNKNOWN | none | (10,36); option 3; target 200 MHz | p.22 |
| frequency | 213 | MHz | Stratix IV EP4S40G2F40I1; year UNKNOWN | none | (10,36); option 3 | p.22 |
| logic | 1,529 | L | Stratix IV EP4S40G2F40I1; year UNKNOWN | none | (10,36); option 3 | p.22 |
| registers | 792 | R | Stratix IV EP4S40G2F40I1; year UNKNOWN | none | (10,36); option 3 | p.22 |
| DSP use | 18 | 18-bit multipliers | Stratix IV EP4S40G2F40I1; year UNKNOWN | none | 9 used; 9 lost to DSP-block I/O constraints | p.22 |
errors_and_checks: g=3 ensures a last-bit-accurate result; the source code contains the detailed error analysis. FloPoCo testbenches compare generated VHDL with MPFR-based expected behavior and support exhaustive/random/corner-case tests.   # p.21, p.25–26
conditions: The fused datapath is specialized to X²+Y²+Z² and exploits the expression’s parallelism/symmetry. Targeting a higher frequency tends to improve actual frequency, while a lower target saves resources; placement/routing congestion prevents a guaranteed final frequency. Table 1 uses ISE 11.5 postsynthesis results. Table 3’s Altera results use Quartus II 9.1 post-place-and-route results in empty FPGAs.   # p.20–22, p.25
evidence: Figure 1 and Table 1, p.21; Tables 2–3, p.22; cycle-management description, p.23–25; testing description, p.25–26.

### squarer  (role: instantiates)
mechanism: FloPoCo provides a specialized squarer that saves resources relative to a general multiplier. Option 2 replaces the three general multipliers in the composed sum-of-squares datapath with three squarers, while option 3 incorporates the squarers into the fused datapath.   # p.19–21
choices:
new_choices:
  none
slots:
  none
parameters: three squarers; input significand width 1+wF; square-path internal width 2+wF+g.   # p.21
results: none
errors_and_checks: none
conditions: The specialization applies because every product in X²+Y²+Z² has identical operands.   # p.20
evidence: FloPoCo library description, p.19; motivating example and Figure 1, p.20–21; Table 1, p.21.

## new_families
none

## space_gaps
* `multi_term_fused_dot.rounding_contract` lacks the document’s `last_bit_accurate` contract.   # p.20–21
* `multi_term_fused_dot` lacks an `internal_guard_bits` choice; g=3 ensures last-bit accuracy for the demonstrated datapath.   # p.21
* The vocabulary lacks a cross-family frequency-directed pipelining choice that places barriers from target frequency/device timing models.   # p.19, p.25

## open_questions
* The numerical error bound represented by “last-bit accurate” is not defined in the article.   # p.18–21
* Figure 1 does not specify the internal reduction-adder or final rounding microarchitecture.   # p.21
* The publication year is known, but the implementation-result year is not reported.   # p.21–22
