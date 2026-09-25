---
handle: pereira_1995
citation: R. Pereira, J. A. Michell, J. M. Solana, "Fully Pipelined TSPC Barrel Shifter for High-Speed Applications", IEEE Journal of Solid-State Circuits, vol. 30, no. 6, pp. 686-690, 1995
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [int16]
authority: incremental
pages_read: 686-690 / 5
---

## summary
The document presents a six-stage TSPC shift-and-rotate circuit that accepts new 16-b data and instructions each clock cycle (p.686, p.688-689). The design implements rightward operations through leftward rotation and masking, which reduces duplicated directional hardware (p.687-688). A 1.5 μm CMOS prototype operates at 100 MHz in bit-path tests, while worst-case HSPICE simulation reports over 100 MHz (p.690).

## families
### barrel_mux_tree  (role: proposes)
mechanism: The six-stage pipeline contains an input stage, four radix-2 shift/rotate stages, and a masking output stage. The four central stages select shifts or rotations of 0/1, 0/2, 0/4, and 0/8 positions. A right rotation becomes a one-position left rotation followed by a left rotation selected by the 1's complement of LGTH. A right arithmetic shift uses the same transformation and masks the most significant output bits with the input sign bit. TSPC pipeline control permits a new instruction each clock cycle. (p.686-689)
choices:
  stage_radix: 2  # p.687
  select_encoding: binary  # p.686-688
  direction_handling: amount_negation  # p.687-688
  stage_order: small_shift_first  # p.687
new_choices:
  pipeline_depth: 6 — The data array places one pipeline stage on each input/selection/masking step.  # p.686-689
  circuit_style: TSPC-N_2-2A201C — The selection cells use TSPC 2-2A201C gates, while the control and mask circuits use pipelined TSPC-N cells.  # p.686-688
  instruction_programming: online_each_clock_cycle — The pipelined programming unit and mask generator permit reprogramming every clock cycle.  # p.686, p.688
slots:
  none
parameters: N = 16 b; shift/rotate distance = 0 to 15 positions; pipeline stages = 6; latency = 6 clock cycles; II = 1 clock cycle; four binary length bits plus direction/type controls.  # p.686-689
results:
| metric | value | unit | technology / device | baseline | condition | page |
| 2-2A201C cell maximum operating frequency | near 280 | MHz | 1.5 μm CMOS / 1995 | none | Most limiting TSPC cell | p.689 |
| complete online-programmable circuit maximum operating frequency | near 200 | MHz | 1.5 μm CMOS / 1995 | none | HSPICE typical parameters; clock buffer is limiting | p.689 |
| complete online-programmable circuit maximum operating frequency | over 100 | MHz | 1.5 μm CMOS / 1995 | none | HSPICE slow parameters with pessimistic clock buffering/U0 buffers/routing | p.689 |
| prototype maximum operating frequency | over 100 | MHz | 1.5 μm CMOS prototype / 1995 | none | HSPICE slow parameters | p.690 |
| full-function prototype test frequency | up to 25 | MHz | 1.5 μm CMOS prototype / 1995 | none | Limited by the test system | p.690 |
| fixed-programming bit-path test frequency | 100 | MHz | 1.5 μm CMOS prototype / 1995 | none | Input/output and serial-in/serial-out tests | p.690 |
| prototype area | 2.3 | mm² | 1.5 μm CMOS prototype / 1995 | none | Includes test circuitry | p.690 |
| test-only area | 0.33 | mm² | 1.5 μm CMOS prototype / 1995 | none | Portion of the 2.3 mm² prototype | p.690 |
errors_and_checks: No arithmetic accuracy or concurrent-error-detection contract is reported. The prototype includes boundary-scan and serial-signature-analysis test facilities, but the document gives no fault coverage or false-alarm result.  # p.689-690
conditions: Pipeline throughput applies when six-cycle latency is acceptable (p.686, p.688-689). The fabricated prototype uses static instruction programming and a simplified control unit, whereas the complete online-programmable circuit is evaluated by simulation (p.686, p.689-690). The 25 MHz full-function test is limited by the external test system rather than identified as the circuit limit (p.690).
evidence: Section II and Fig. 1 (p.686); Section III and Figs. 2-3 (p.687-688); Section IV and Figs. 4-6 (p.688-689); Section V and Figs. 7-8 (p.689-690).

## new_families
none

## space_gaps
* barrel_mux_tree lacks a pipeline-depth choice for a register between every shift/rotate stage (p.686-689).
* barrel_mux_tree lacks a circuit-style choice for TSPC dynamic cells (p.686-688).
* barrel_mux_tree lacks an online/static instruction-programming choice (p.686, p.689).
* barrel_mux_tree lacks an output-fill/masking choice that distinguishes zero fill from arithmetic sign extension (p.687-688).

## open_questions
* The exact worst-case maximum frequency is not reported beyond “over 100 MHz” for either the online-programmable circuit or the prototype (p.689-690).
