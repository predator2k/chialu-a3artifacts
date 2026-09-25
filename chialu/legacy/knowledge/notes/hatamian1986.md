---
handle: hatamian1986
citation: M. Hatamian, G. L. Cash, "A 70-MHz 8-bit x 8-bit Parallel Pipelined Multiplier in 2.5-um CMOS", IEEE Journal of Solid-State Circuits, vol. SC-21, no. 4, pp. 505-513, 1986
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [uint8]
authority: landmark
pages_read: 9 / 9 (pp. 505-513)
---

## summary
The document presents a fabricated unsigned 8-bit × 8-bit carry-save array multiplier with registers at individual cells and a spatially pipelined final addition, which accepts new operands every clock cycle. (pp.505-507) The 2.5-µm CMOS chip operates at multiplication rates up to 70 MHz and dissipates about 250 mW at that rate. (p.511) The document also describes a structure-preserving Baugh-Wooley signed extension and simulated single-phase-clock successor. (pp.511-513)

## families
### carry_save_array  (role: extends)
mechanism: An unsigned parallel partial-product array uses carry-save addition with registered full-adder outputs, so vertical data advances one row per pipeline stage. A registered half-adder array replaces the carry-propagating last row and determines successive product bits in successive spatial stages. Operand bits are delayed before AND generation, which supplies each stage with the required time-skewed partial product while halving the registers otherwise required for partial-product skewing. Output registers deskew the product. (pp.505-507)
choices:
  signed_scheme: unsigned   # p.511
  rows_per_pipeline_stage: 1   # p.506
new_choices:
  partial_product_timing: skew_operands_before_generation — Delays operand bits before the AND gates rather than registering complete partial-product words.   # pp.506-507
  pipeline_clocking: two_phase_dynamic — Registers use a dynamic two-phase clock.   # pp.509-510
  final_carry_resolution: registered_half_adder_array — The final carry propagation is distributed across spatial pipeline stages.   # p.506
slots:
  cpa: spatially_pipelined_final_adder [cell_array=registered_half_adder] [outside domain]   # p.506
parameters: 8-bit × 8-bit unsigned operands; 16 pipeline stages for the fabricated 8 × 8 design; general stage count 2N for N × N; II=1 clock cycle; registered full-adder stage delay plus register.   # pp.505-507, p.511
results:
| metric | value | unit | technology / device | baseline | condition | page |
| multiplication rate | up to 70 | MHz | 2.5-µm CMOS; 1986 | none | fabricated 8-bit × 8-bit chip; limited by I/O pad bandwidth/test setup | pp.505, 511 |
| power dissipation | about 250 | mW | 2.5-µm CMOS; 1986 | none | operating at 70 MHz | p.511 |
| nonpipelined multiplication rate | 12.7 | MHz | 2.5-µm CMOS; 1986 | pipelined mode at 70 MHz | register clocks tied to the power supply | p.511 |
| stage delay | about 5 | ns | 2.5-µm CMOS; 1986 | none | inferred in the document from 16 stages and 12.7-MHz nonpipelined operation | p.511 |
| theoretical throughput | approaching 200 | MHz | 2.5-µm CMOS; 1986 | 12.7-MHz nonpipelined measurement | excludes register rise/fall time | p.511 |
| estimated clocked throughput limit | about 140 | MHz | 2.5-µm CMOS; 1986 | theoretical 200-MHz limit | includes pipeline-register rise/fall time but excludes I/O limitation | p.511 |
| implemented area | about 4.4 | × nonpipelined area | 2.5-µm CMOS; 1986 | nonpipelined version | includes registers, clock buffers, and clock routing | p.510 |
| pipeline-register area increase | approximately 130 | % | 2.5-µm CMOS; 1986 | nonpipelined version | includes skewing/deskewing registers | p.510 |
| clock-buffer area increase | approximately 100 | % | 2.5-µm CMOS; 1986 | nonpipelined version | fabricated layout | p.510 |
| clock-routing area increase | approximately 110 | % | 2.5-µm CMOS; 1986 | nonpipelined version | fabricated layout | p.510 |
| redesigned area | about 2.5 | × nonpipelined area | UNKNOWN; 1986 | fabricated design at 4.4× | successor then being fabricated | p.510 |
| registered-cell simulated clock rate | 100 | MHz | 2.5-µm CMOS; 1986 | none | two-phase registered full-adder cell; 0.6-ns input/clock rise and fall times | p.510 |
| single-phase successor simulated rate | 75 | MHz | UNKNOWN; 1986 | fabricated two-phase design | successor then being fabricated | pp.512-513 |
errors_and_checks: none
conditions: Adjacent-stage horizontal clock skew must remain below the full-adder propagation delay, which is about 1 ns for the extracted cell. (p.509) The full-adder cell delay is about 5 ns. (p.509) Timing-simulator-based skew equalization applies when clock distribution uses low-resistance all-metal interconnect, apart from very short crossings. (pp.508-509) The fabricated 70-MHz limit comes from I/O pad bandwidth rather than the analyzed clock network. (p.511) The fabricated structure does not support signed multiplication, while the proposed Baugh-Wooley reorganization preserves the array with minor inversions and constant-bit changes. (pp.511-512)
evidence: Section II and Figs. 1-4 (pp.505-507); Sections III-IV and Figs. 6-12 (pp.508-510); Section V (p.511); Sections VI-VII and Figs. 13-15 (pp.511-513).

## new_families
### spatially_pipelined_final_adder  (domain: adder, closest: ripple_carry, why_not: ripple_carry does not represent carry propagation mapped into successive registered spatial stages with one product bit resolved per stage.)
mechanism: A horizontal array of half adders and registers replaces the carry-propagating last row of a carry-save multiplier. Starting at the least-significant bit, each stage resolves one result bit and registers the carry/sum state for the next stage. Two half-adder stages may be combined because their combined delay is approximately one full-adder-array stage. A registered ripple-carry implementation is also possible, with diagonal full adders and registers elsewhere. (pp.505-506, p.512)
choices:
  cell_array: {registered_half_adder, registered_full_adder}; implemented: registered_half_adder   # p.506
  half_adder_stages_per_pipeline_stage: {1, 2}; implemented: 1 in fabricated chip, 2 in proposed reduction   # pp.506, 512
  clocking: {two_phase_dynamic, single_phase_equalized_delay}; fabricated: two_phase_dynamic   # pp.509-510, 512
results:
| metric | value | unit | technology / device | baseline | condition | page |
| total multiplier stages | 3N/2 | stages | UNKNOWN; 1986 | 2N stages | two half-adder stages combined per pipeline stage | pp.506, 512 |
| estimated chip-area reduction | approximately 20 | % | UNKNOWN; 1986 | 2N-stage implementation | stage count reduced to 3N/2 | p.512 |
| full-adder-array transistor reduction | almost 20 | % | UNKNOWN; 1986 | half-adder final array | register/clock overhead makes total area almost the same | p.506 |
evidence: Section II and Fig. 2 (pp.505-506); Section VII and Fig. 15 (p.512).

## space_gaps
* The carry_save_array `cpa` slot does not admit a spatially pipelined half-adder final row. (p.506)
* The carry_save_array family lacks a choice for skewing operand bits before partial-product generation. (pp.506-507)
* The vocabulary lacks pipeline clocking/clock-distribution choices for two-phase dynamic registers, single-phase equalized-delay registers, and balanced all-metal clock networks. (pp.507-510, 512)

## open_questions
* The abstract reports power dissipation as less than 250 mW, while Section V reports about 250 mW at 70 MHz. (pp.505, 511)
* The document does not report an absolute chip area or transistor count. (p.510)
* The signed Baugh-Wooley version and single-phase version were awaiting fabrication/testing, so the document provides no measured results for either design. (pp.511-513)
