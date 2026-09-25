---
handle: canal_2000
citation: R. Canal, A. Gonzalez, J. E. Smith, "Very Low Power Pipelines Using Significance Compression", Proc. MICRO-33, pp. 181-190, 2000
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [int32]
authority: incremental
pages_read: 181-190 / 10
---

## summary
The paper maintains byte-significance metadata through a five-stage pipeline so caches, registers, ALU lanes, and latches activate only for significant bytes. Byte-serial, semi-parallel, and full-width gated organizations trade performance/control complexity while retaining most activity reductions.

## families
### lane_width_gating  (role: extends)
mechanism: Each 32-bit data value carries three extension bits that identify whether each upper byte is significant or a sign extension; the low byte is always represented. The bits reside with values in caches and registers, flow through the pipeline, control byte-bank accesses and ALU activity, and gate pipeline latches. Serial organizations process significant bytes over multiple cycles, while semi-parallel and byte-parallel organizations instantiate more byte lanes but disable unneeded lanes.
choices:
  detection: significance_tags   # p.181-182
  gating: operand_isolation   # p.181, p.188-189
new_choices:
  significance_granularity: {byte, halfword} — granularity at which storage and datapath activity is suppressed   # p.182, p.186
  extension_bit_count: {2, 3} — metadata bits carried with each 32-bit data word   # p.182
  pipeline_organization: {byte_serial, halfword_serial, byte_semi_parallel, byte_parallel_skewed, byte_parallel_compressed, byte_parallel_skewed_with_bypasses} — lane width and scheduling across pipeline stages   # p.187-190
  latch_clock_gating: true — significance bits suppress byte-level latch and clock activity   # p.186
slots:
  none
parameters: 32-bit MIPS-like integer ISA; 5-stage in-order pipeline; primary granularity 8 bits with a 16-bit comparison; 3 data extension bits; 1 instruction extension bit; byte-serial widths of 3-byte instruction fetch/1-byte register file/1-byte ALU/1-byte data cache; semi-parallel widths of 3/2/2/1 bytes; full-width organizations use 4-byte datapaths   # p.182-184, p.187-189
results:
| metric | value | unit | technology / device | baseline | condition | page |
| activity reduction, instruction fetch | 18.2 | % | UNKNOWN; year 2000 | conventional 32-bit pipeline | 8-bit significance compression, Mediabench average | p.186 |
| activity reduction, register-file reads | 46.5 | % | UNKNOWN; year 2000 | conventional 32-bit pipeline | 8-bit significance compression, Mediabench average | p.186 |
| activity reduction, register-file writes | 42.1 | % | UNKNOWN; year 2000 | conventional 32-bit pipeline | 8-bit significance compression, Mediabench average | p.186 |
| activity reduction, ALU | 33.2 | % | UNKNOWN; year 2000 | conventional 32-bit pipeline | 8-bit significance compression, Mediabench average | p.186 |
| activity reduction, data-cache data | 30.1 | % | UNKNOWN; year 2000 | conventional 32-bit pipeline | 8-bit significance compression, Mediabench average | p.186 |
| activity reduction, data-cache tag | 0.9 | % | UNKNOWN; year 2000 | conventional 32-bit pipeline | 8-bit significance compression, Mediabench average | p.186 |
| activity reduction, PC increment | 73.3 | % | UNKNOWN; year 2000 | conventional 32-bit pipeline | 8-bit significance compression, Mediabench average | p.186 |
| activity reduction, pipeline latches | 42.2 | % | UNKNOWN; year 2000 | conventional 32-bit pipeline | 8-bit significance compression, Mediabench average | p.186 |
| activity reduction, instruction fetch | 18.2 | % | UNKNOWN; year 2000 | conventional 32-bit pipeline | 16-bit significance compression, Mediabench average | p.186 |
| activity reduction, register-file reads | 35.9 | % | UNKNOWN; year 2000 | conventional 32-bit pipeline | 16-bit significance compression, Mediabench average | p.186 |
| activity reduction, ALU | 22.1 | % | UNKNOWN; year 2000 | conventional 32-bit pipeline | 16-bit significance compression, Mediabench average | p.186 |
| activity reduction, data-cache data | 23.4 | % | UNKNOWN; year 2000 | conventional 32-bit pipeline | 16-bit significance compression, Mediabench average | p.186 |
| activity reduction, data-cache tag | 0 | % | UNKNOWN; year 2000 | conventional 32-bit pipeline | 16-bit significance compression, Mediabench average | p.186 |
| activity reduction, PC increment | 46.7 | % | UNKNOWN; year 2000 | conventional 32-bit pipeline | 16-bit significance compression, Mediabench average | p.186 |
| activity reduction, pipeline latches | 34.9 | % | UNKNOWN; year 2000 | conventional 32-bit pipeline | 16-bit significance compression, Mediabench average | p.186 |
| CPI increase | 79 | % | UNKNOWN; year 2000 | conventional 32-bit 5-stage pipeline | byte-serial implementation, Mediabench average | p.187 |
| CPI | 1.96 | cycles per instruction | UNKNOWN; year 2000 | conventional 32-bit 5-stage pipeline | halfword-serial implementation, Mediabench average | p.187 |
| CPI increase | 24 | % | UNKNOWN; year 2000 | conventional 32-bit 5-stage pipeline | byte semi-parallel implementation, Mediabench average | p.188 |
| CPI increase | 6 | % | UNKNOWN; year 2000 | conventional 32-bit 5-stage pipeline | byte-parallel compressed implementation, Mediabench average | p.189 |
| CPI increase | 2 | % | UNKNOWN; year 2000 | conventional 32-bit 5-stage pipeline | byte-parallel skewed implementation with bypasses, Mediabench average | p.190 |
errors_and_checks: none
conditions: The evaluation targets an in-order 32-bit MIPS-like integer pipeline and Mediabench workloads compiled with gcc optimization flags (p.182, p.187). The baseline uses no branch prediction, so every branch stalls fetch until ALU-stage resolution (p.187). The three-bit data encoding adds 9% metadata overhead, while the two-bit alternative adds 6% but represents fewer internal-byte patterns (p.182, p.186). Activity reduction serves as a proxy for dynamic-energy reduction; load-capacitance effects and final circuit-level energy are not quantified (p.181, p.190). Full-width implementations require additional latches, forwarding paths, or control complexity (p.189-190).
evidence: §2.1 and Table 1, p.182-183; §2.3-2.9 and Tables 5-6, p.183-186; §4 and Figs. 3-4, p.187; §5 and Figs. 5-6, p.188; §6 and Figs. 7-10, p.189-190.

## new_families
none

## space_gaps
* `lane_width_gating` lacks choices for significance granularity, persistent extension-bit encoding, and serial/semi-parallel/full-width lane organization, which determine the paper's storage overhead and performance tradeoff (p.182, p.187-190).
* `lane_width_gating.gating` cannot record concurrent functional-unit operand isolation and byte-level latch clock gating as separate mechanisms (p.186).

## open_questions
* The paper selects the three-bit data encoding for evaluation but leaves the two-bit versus three-bit implementation choice unsettled (p.182).
* The sentence accompanying the halfword-serial CPI of 1.96 describes a 29% comparison whose named reference appears inconsistent with the plotted configurations, so the merge pass must not assign that percentage to a baseline without checking the original figure (p.187).
