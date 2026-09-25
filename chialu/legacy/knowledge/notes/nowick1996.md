---
handle: nowick1996
citation: S. M. Nowick, "Design of a Low-Latency Asynchronous Adder Using Speculative Completion", IEE Proceedings - Computers and Digital Techniques, vol. 143, no. 5, pp. 301-307, 1996.
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [int32]
authority: landmark
pages_read: 301-307 / 7
---

## summary
The paper proposes speculative completion, which combines a single-rail asynchronous datapath with worst-case/speculative matched delays and parallel abort detection. A 32-bit Brent-Kung BLC adder is estimated to improve average performance by 5-30% over a comparable seven-gate-delay synchronous implementation under random inputs. # p.301, p.305

## families
### speculative_variable_latency  (role: proposes)
mechanism: One worst-case model delay and one speculative delay run in parallel with a single-rail 32-bit BLC datapath. A conservative abort network detects propagate patterns that may require levels 4-5, so the speculative path completes after five gate delays only when level-3 generate signals are final. Detection products also provide local late-enable signals to modified sum generators. Aborted cases await the late carry signals and complete after nine gate delays. # p.302-305
choices:
  speculation_window: 8   # p.303
  detection: propagate_run_detector   # p.303
  recovery: await_completion   # p.302, p.304
new_choices:
  completion_delay_count: 2 — one worst-case and one speculative matched delay   # p.302-303
  abort_product_literals: {3, 4, 5} — propagate literals in each compared detection product   # p.303
  kill_augmentation_bits: {0, 1, 2} — kill-condition inputs augmenting each detection product   # p.304
  late_enable_distribution: per_product_local — each detection product enables the affected sum modules   # p.304-305
slots:
  base_adder: parallel_prefix [topology=brent_kung, valency=2]   # p.302
parameters: 32-bit; two completion paths; speculative path 5 gate delays; late path 9 gate delays; abort stable before the speculative path's final gate; nine abort-network variants   # p.302-305
results:
| metric | value | unit | technology / device | baseline | condition | page |
| early latency | 5 | no. gates | UNKNOWN; year 1996 | synchronous implementation, 7 gate delays | level-3 generate signals are final | p.304 |
| late latency | 9 | no. gates | UNKNOWN; year 1996 | synchronous implementation, 7 gate delays | speculative completion is aborted | p.304 |
| abort detection area, (3p, 0k) | 12 | no. lits. | UNKNOWN; year 1996 | none | random inputs; equal gate delays | p.305 |
| early completion, (3p, 0k) | 59 | % | UNKNOWN; year 1996 | none | random inputs; equal gate delays | p.305 |
| average adder latency, (3p, 0k) | 6.64 | no. gates | UNKNOWN; year 1996 | 7 gate delays | random inputs; equal gate delays | p.305 |
| performance improvement, (3p, 0k) | 5 | % | UNKNOWN; year 1996 | comparable synchronous implementation | random inputs; equal gate delays | p.305 |
| abort detection area, (4p, 0k) | 20 | no. lits. | UNKNOWN; year 1996 | none | random inputs; equal gate delays | p.305 |
| early completion, (4p, 0k) | 72 | % | UNKNOWN; year 1996 | none | random inputs; equal gate delays | p.305 |
| average adder latency, (4p, 0k) | 6.12 | no. gates | UNKNOWN; year 1996 | 7 gate delays | random inputs; equal gate delays | p.305 |
| performance improvement, (4p, 0k) | 14 | % | UNKNOWN; year 1996 | comparable synchronous implementation | random inputs; equal gate delays | p.305 |
| abort detection area, (5p, 0k) | 30 | no. lits. | UNKNOWN; year 1996 | none | overlapping products; random inputs; equal gate delays | p.305 |
| early completion, (5p, 0k) | 83 | % | UNKNOWN; year 1996 | none | overlapping products; random inputs; equal gate delays | p.305 |
| average adder latency, (5p, 0k) | 5.68 | no. gates | UNKNOWN; year 1996 | 7 gate delays | overlapping products; random inputs; equal gate delays | p.305 |
| performance improvement, (5p, 0k) | 23 | % | UNKNOWN; year 1996 | comparable synchronous implementation | overlapping products; random inputs; equal gate delays | p.305 |
| abort detection area, (3p, 1k) | 16 | no. lits. | UNKNOWN; year 1996 | none | random inputs; equal gate delays | p.305 |
| early completion, (3p, 1k) | 67 | % | UNKNOWN; year 1996 | none | random inputs; equal gate delays | p.305 |
| average adder latency, (3p, 1k) | 6.32 | no. gates | UNKNOWN; year 1996 | 7 gate delays | random inputs; equal gate delays | p.305 |
| performance improvement, (3p, 1k) | 11 | % | UNKNOWN; year 1996 | comparable synchronous implementation | random inputs; equal gate delays | p.305 |
| abort detection area, (4p, 1k) | 25 | no. lits. | UNKNOWN; year 1996 | none | random inputs; equal gate delays | p.305 |
| early completion, (4p, 1k) | 79 | % | UNKNOWN; year 1996 | none | random inputs; equal gate delays | p.305 |
| average adder latency, (4p, 1k) | 5.84 | no. gates | UNKNOWN; year 1996 | 7 gate delays | random inputs; equal gate delays | p.305 |
| performance improvement, (4p, 1k) | 20 | % | UNKNOWN; year 1996 | comparable synchronous implementation | random inputs; equal gate delays | p.305 |
| abort detection area, (5p, 1k) | 36 | no. lits. | UNKNOWN; year 1996 | none | overlapping products; random inputs; equal gate delays | p.305 |
| early completion, (5p, 1k) | 87 | % | UNKNOWN; year 1996 | none | overlapping products; random inputs; equal gate delays | p.305 |
| average adder latency, (5p, 1k) | 5.52 | no. gates | UNKNOWN; year 1996 | 7 gate delays | overlapping products; random inputs; equal gate delays | p.305 |
| performance improvement, (5p, 1k) | 27 | % | UNKNOWN; year 1996 | comparable synchronous implementation | overlapping products; random inputs; equal gate delays | p.305 |
| abort detection area, (3p, 2k) | 24 | no. lits. | UNKNOWN; year 1996 | none | random inputs; equal gate delays | p.305 |
| early completion, (3p, 2k) | 72 | % | UNKNOWN; year 1996 | none | random inputs; equal gate delays | p.305 |
| average adder latency, (3p, 2k) | 6.12 | no. gates | UNKNOWN; year 1996 | 7 gate delays | random inputs; equal gate delays | p.305 |
| performance improvement, (3p, 2k) | 14 | % | UNKNOWN; year 1996 | comparable synchronous implementation | random inputs; equal gate delays | p.305 |
| abort detection area, (4p, 2k) | 35 | no. lits. | UNKNOWN; year 1996 | none | overlapping products; random inputs; equal gate delays | p.305 |
| early completion, (4p, 2k) | 84 | % | UNKNOWN; year 1996 | none | overlapping products; random inputs; equal gate delays | p.305 |
| average adder latency, (4p, 2k) | 5.65 | no. gates | UNKNOWN; year 1996 | 7 gate delays | overlapping products; random inputs; equal gate delays | p.305 |
| performance improvement, (4p, 2k) | 24 | % | UNKNOWN; year 1996 | comparable synchronous implementation | overlapping products; random inputs; equal gate delays | p.305 |
| abort detection area, (5p, 2k) | 48 | no. lits. | UNKNOWN; year 1996 | none | overlapping products; random inputs; equal gate delays | p.305 |
| early completion, (5p, 2k) | 90 | % | UNKNOWN; year 1996 | none | overlapping products; random inputs; equal gate delays | p.305 |
| average adder latency, (5p, 2k) | 5.39 | no. gates | UNKNOWN; year 1996 | 7 gate delays | overlapping products; random inputs; equal gate delays | p.305 |
| performance improvement, (5p, 2k) | 30 | % | UNKNOWN; year 1996 | comparable synchronous implementation | overlapping products; random inputs; equal gate delays | p.305 |
errors_and_checks: Arithmetic results remain exact. Conservative abort detection covers every relevant 8-p run, so a late computation cannot be accepted early; safe approximation may instead cause unnecessary aborts. The modified sum generator selects functionally correct early or late carries. No fault-detection coverage is reported. # p.303-305
conditions: The estimates assume random inputs, equal gate delays, and an abort network that meets its timing constraint. Early completion requires all final generate signals by level 3. Late cases take nine gate delays, which exceeds the seven-gate synchronous baseline. Wiring/fanout capacitance, layout, and transistor-level simulation are absent. # p.303-305
evidence: §2.1-2.2, §3.1-3.3, Table 1, §4, §5, Appendix

### parallel_prefix  (role: instantiates)
mechanism: The datapath is a 32-bit binary-lookahead Brent-Kung adder adapted from Suzuki et al. Level 0 forms bit propagate/generate signals. Levels 1-5 form successively wider cumulative propagate/generate functions, and level 6 XORs each bit propagate with the preceding final generate. CMOS gate stack depth is limited to two, fanout is mostly limited to two, and the layout is regular. # p.302
choices:
  topology: brent_kung   # p.301-302
  valency: 2   # p.302
new_choices:
  none
slots:
  none
parameters: 32-bit; levels 0-6; ordinary critical path 7 gate delays; level groups cover 2, 4, 8, 16 and 32 bits successively   # p.302
results:
| metric | value | unit | technology / device | baseline | condition | page |
| ordinary BLC critical-path latency | 7 | gate delays | UNKNOWN; year 1996 | none | equal-delay gate model | p.302 |
errors_and_checks: none
conditions: The paper analyzes a gate-level structure rather than a laid-out implementation, so wiring/fanout capacitance is not included. # p.301, p.305
evidence: Fig. 3, §2.2, §3.2.1

## new_families
none

## space_gaps
* The `speculative_variable_latency` `base_adder` slot should admit `parallel_prefix`, because the demonstrated base datapath is a Brent-Kung BLC adder. # p.302
* The vocabulary lacks choices for multiple asynchronous matched delays, abort-network approximation, and local late-enable distribution. # p.302-305

## open_questions
* The technology node, transistor area, power, wiring delay, and fanout capacitance remain unreported because layout and simulation were future work. # p.301, p.305
* Preliminary work suggests that another sum-generation design may reduce worst-case latency from nine to seven gate delays, but the paper provides no implementation or evaluated result. # p.305
