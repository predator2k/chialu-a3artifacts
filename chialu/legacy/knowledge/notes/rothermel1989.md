---
handle: rothermel1989
citation: A. Rothermel, B. J. Hosticka, G. Troester, J. Arndt, "Realization of Transmission-Gate Conditional-Sum (TGCS) Adders with Low Latency Time", IEEE Journal of Solid-State Circuits, vol. 24, no. 3, pp. 558-561, 1989.
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [int8, int16, int32]
authority: incremental
pages_read: 4 / 4 (pp. 558-561)
---

## summary
The paper realizes a static conditional-sum adder whose conditional cells and selection multiplexers use transmission gates, which provides 12.5 ns latency for a fabricated 32-bit adder (p.558). The design uses a regular binary-tree layout and optimized cascaded buffers for high-fanout selection signals (pp.559-560).

## families
### conditional_sum  (role: proposes)
mechanism: Each bit has one conditional cell that calculates sum/carry outputs for carry-in values 0 and 1. A binary hierarchy of two-input multiplexers selects the valid outputs under control of lower-significance carry outputs. Transmission gates implement both the conditional cells and multiplexers, with one series transistor contributed by each element. The input-to-output path has t=1+log2 n series transistors, while staged switching precharges intermediate parasitic capacitances. Cascaded CMOS buffers drive selection signals whose fanout reaches n/2 multiplexers. (pp.558-560)
choices:
  base_block_width: 1   # p.558
  mux_style: transmission_gate   # pp.558-559
  selection_radix: 2   # pp.558-559
new_choices:
  conditional_cell_style: transmission_gate — identifies the circuit style used for the duplicated sum/carry cell, independently of mux_style   # pp.558-559
  selection_signal_buffering: optimized_cascaded_cmos — identifies the buffer hierarchy used to drive high-fanout multiplexer controls   # pp.559-560
slots:
  none
parameters: 8-bit adder/latch and 16/32-bit adders realized; 64/128-bit delays estimated; t=1+log2 n series transistors; six series transistors at 32 bits; NMOS/PMOS channel widths 7/15 µm; 2.5 µm drawn channel length with selected devices shrunk to 2.0/1.5 µm; 5-V supply for the power measurement   # pp.559-561
results:
| metric | value | unit | technology / device | baseline | condition | page |
| latency | 12.5 | ns | standard 2.5-µm CMOS; 1989 | UNKNOWN | 32-bit addition | p.558 |
| area per bit | 80x460 | µm² | standard 2.5-µm CMOS; 1989 | UNKNOWN | 32-bit adder | pp.558, 561 |
| maximum clock frequency | 85 | MHz | 2.5-µm CMOS; 1989 | UNKNOWN | 8-bit adder/latch recursive test configuration | p.560 |
| maximum clock frequency | 120 | MHz | 2.0-µm CMOS; 1989 | UNKNOWN | 8-bit adder/latch recursive test configuration | p.560 |
| maximum clock frequency | 170 | MHz | 1.5-µm CMOS; 1989 | UNKNOWN | 8-bit adder/latch recursive test configuration | p.560 |
| estimated addition time | 13 | ns | 2.0-µm CMOS; 1989 | UNKNOWN | estimated 64-bit implementation | p.561 |
| estimated addition time | 17 | ns | 2.0-µm CMOS; 1989 | UNKNOWN | estimated 128-bit implementation | p.561 |
| power consumption per clock frequency | 180 | µW/MHz | 2.5-µm drawn standard CMOS; 1989 | UNKNOWN | 8-bit adder/latch combination at 5-V supply | p.561 |
| latency advantage | about 30 | percent faster | standard CMOS, node UNKNOWN; 1989 | carry-select adders [4] | TGCS latency compared with carry-select adders | p.561 |
errors_and_checks: The circuit performs exact normal-binary addition; no arithmetic-error bound, fault model, or concurrent checker is reported.   # pp.558, 561
conditions: Static fully complementary operation requires no precharge clock and reports no dc power consumption (p.561). The design pays increased chip area compared with carry-select adders (p.558). Optimized cascaded buffers are required because one selection signal can control n/2 multiplexers (p.559). Additional buffers are required when an adder output directly drives another TGCS adder rather than a latch (p.561). The regular layout supports arbitrary word lengths without changing the architecture (pp.559, 561). The intended applications are latency-critical binary-addition bottlenecks, including carry-save multiplier outputs/redundant-binary conversion/recursive structures (p.561).
evidence: §II and Figs. 1-2 (pp.558-559); §III, Table I, and Figs. 3-7 (pp.559-560); Tables II-III and Fig. 8 (pp.560-561); §IV (p.561).

## new_families
none

## space_gaps
* conditional_sum needs a conditional_cell_style choice because mux_style does not record the paper’s transmission-gate implementation of the conditional cells (pp.558-559).
* conditional_sum needs a selection_signal_buffering choice because the cascaded CMOS buffer hierarchy is required to handle the n/2 control fanout (pp.559-560).

## open_questions
* Table III’s column labels and several values are illegible in the supplied text extraction, so measured per-width delays beyond the clearly stated 12.5 ns result remain unrecorded.
