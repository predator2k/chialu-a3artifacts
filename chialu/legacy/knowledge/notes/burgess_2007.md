---
handle: burgess_2007
citation: N. Burgess, C. N. Hinds, "Design of the ARM VFP11 Divide and Square Root Synthesisable Macrocell", Proc. 18th IEEE Symposium on Computer Arithmetic (ARITH-18), pp. 87-96, 2007.
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [fp32, fp64]
authority: incremental
pages_read: 10 / 10
---

## summary
The document presents a synthesizable combined IEEE 754 divide/square-root macrocell based on minimum-redundancy radix-4 SRT recurrence. Quintuple speculative remainder updates and nonredundant assimilation of eight remainder MSBs reduce the critical path to one carry-propagate operation while supporting correctly rounded fp32/fp64 results in 15/29 cycles. # pp.87-88, pp.94-95

## families
### digit_recurrence_sqrt_combined  (role: extends)
mechanism: The macrocell unifies radix-4 SRT division and square root as Ri+1 = r·Ri − Fi·qi+1. Four comparisons of the top eight remainder bits select a one-hot digit while five possible updated remainders and positive/negative root estimates are computed speculatively. The selected update retains a redundant remainder except for eight assimilated MSBs, which preserve sign information and remove a 3:2 reduction before the next comparisons. # pp.88,96
choices:
  radix: 4   # pp.87-88
  shared_with_division: true   # pp.87-88
  on_the_fly_conversion: true   # p.87
new_choices:
  digit_redundancy: minimum — qi+1 uses the radix-4 digit set with redundancy factor u = 2/3   # p.88
  remainder_update: quintuple_parallel_speculation — all five updates for k = -2 … +2 are computed before qi+1 is known   # pp.88,95
  digit_selection_implementation: four_parallel_comparators_one_hot — four comparisons replace a lookup table and feed one-hot digit logic   # pp.87-88
  partial_remainder_representation: redundant_with_8_msb_nonredundant — the top eight bits are assimilated for the next comparison   # pp.88,94
slots:
  digit_select: comparator_digit_selection [comparison_width=8, comparison_count=4] [outside domain]   # pp.87-88
parameters: radix 4; 2 bits/cycle; fp32 latency 15 cycles; fp64 latency 29 cycles; four 8-bit remainder comparisons; five speculative remainder updates; target logic depth 15 levels; implemented critical path 18 CMOS logic/buffer stages   # pp.87-89
results:
| metric | value | unit | technology / device | baseline | condition | page |
| operating frequency | 270 | MHz | 180nm CMOS / 2007 | none | process implementation | p.89 |
| delay / CMOS gate | 142 | ns | 180nm CMOS / 2007 | none | Table 2 value as printed | p.89 |
| operating frequency | 350 – 550 | MHz | 130nm CMOS / 2007 | none | process variants trade speed for leakage power | p.89 |
| delay / CMOS gate | 78 – 122 | ns | 130nm CMOS / 2007 | none | Table 2 value as printed | p.89 |
| operating frequency | 450 – 750 | MHz | 90nm CMOS / 2007 | none | process variants trade speed for leakage power | p.89 |
| delay / CMOS gate | 57 – 95 | ns | 90nm CMOS / 2007 | none | Table 2 value as printed | p.89 |
| latency | 15 | cycles | UNKNOWN / 2007 | none | correctly rounded fp32 divide or square root | p.87 |
| latency | 29 | cycles | UNKNOWN / 2007 | none | correctly rounded fp64 divide or square root | p.87 |
| critical-path delay | 16.0 | FO4 delays | UNKNOWN / 2007 | none | Logical Effort estimate through Fk logic | p.91 |
| critical-path delay | 15.4 | FO4 delays | UNKNOWN / 2007 | none | Logical Effort estimate through Mk comparators | p.92 |
| critical-path mismatch | 3.8% | difference | UNKNOWN / 2007 | other macrocell critical path | Logical Effort estimates | p.91 |
| comparative cycle time | 50% | faster | UNKNOWN / 2007 | best previous proposal | authors’ summary | p.95 |
| estimated hardware | 4855 | CMOS cells | UNKNOWN / 2007 | 1037-cell low-power unit [13] | excludes buffers and other uncounted logic | p.95 |
| hardware overhead | around a factor of 4.5 | area ratio | UNKNOWN / 2007 | low-power unit [13] | estimated cell counts excluding buffers | p.95 |
errors_and_checks: The macrocell produces correctly rounded quotients and square roots for IEEE 754 single-precision and double-precision operations; no fault-detection mechanism or numerical error rate is reported. # p.87
conditions: The design targets a processor clock of up to 750MHz in 90nm CMOS and a logic depth near 15 levels. # p.87 The speculative architecture wins on cycle time because each critical path contains only one carry-propagate operation. # p.94 The speculative architecture loses area because five full-length carry-save adders and full-length multiplexers replace the low-power design’s single carry-save adder and multiplexer. # p.95 Multiplicative division was rejected because a dedicated fast multiplier was considered large/power-hungry and iterative dependencies require many cycles in a deeply pipelined processor. # p.87
evidence: §1; §2 and Figures 1-4; Table 2; §3 critical-path analyses; §4 and Table 4; §5.

## new_families
### comparator_digit_selection  (domain: div: dividers / square root, closest: qds_table, why_not: the digit_select slots admit only qds_table, while this macrocell explicitly replaces the lookup table with parallel comparisons)
mechanism: Four comparators subtract radix-4 selection constants Mk from the top eight bits of Ri. The four signs are combined into a one-hot encoding of qi+1. Five previously computed remainder/root candidates are then selected without another carry-propagate calculation on the same path. # pp.87-88
choices: comparison_width: Int[1..16:1]; comparison_count: Int[2..8:1]; output_encoding: {binary, one_hot, zero_one_hot}; constants_storage: {registers, hardwired}
results:
| metric | value | unit | technology / device | baseline | condition | page |
| critical-path delay | 15.4 | FO4 delays | UNKNOWN / 2007 | 16.0 FO4 Fk path | comparator path including buffers/selection | p.92 |
evidence: §2, Figures 1-2 and 4; §3 critical path 2.

## space_gaps
* digit_recurrence_sqrt_combined lacks choices for remainder-update speculation, digit redundancy, partial-remainder encoding, and MSB assimilation width. # pp.88,94
* digit_select lacks a comparator-based family even though the document explicitly uses comparators instead of qds_table. # pp.87-88
* digit_recurrence_sqrt_combined lacks a slot or choice for the positive/negative on-the-fly square-root estimate representation Qi+ and Qi−. # pp.87-88

## open_questions
* Figure 1 describes 54-bit R*i+1 adders, while §3 describes five 56-bit carry-save adders with 8-bit carry-propagate subtractors. # pp.88,91
* Table 2 prints delay-per-CMOS-gate values of 142 ns, 78 – 122 ns, and 57 – 95 ns, which the merge pass must preserve or verify against the typeset source because the values conflict dimensionally with the listed MHz frequencies. # p.89
