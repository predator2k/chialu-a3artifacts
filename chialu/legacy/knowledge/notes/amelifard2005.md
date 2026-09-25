---
handle: amelifard2005
citation: B. Amelifard, F. Fallah, M. Pedram, "Closing the Gap between Carry Select Adder and Ripple Carry Adder: A New Class of Low-Power High-Performance Adders", 6th International Symposium on Quality Electronic Design (ISQED), pp. 148-152, 2005.
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [int32, int64]
authority: incremental
pages_read: 5 / 5
---

## summary
The paper proposes Carry Select Adder with Sharing (CSAS), which time-multiplexes each duplicated upper carry-select block and preserves one result in latches (p.2-p.3). The synthesized 32-bit and 64-bit implementations occupy less area than conventional carry-select adders at intermediate delays between ripple-carry and carry-select designs (p.4-p.5).

## families
### carry_select  (role: extends)
mechanism: Each non-LSB ripple block performs the Cin=1 addition during one half-cycle, stores that result in transparent latches, and performs the Cin=0 addition during the other half-cycle. A mux selects the stored or current result using the carry propagated from the preceding group. Iterative application creates an m-stage CSAS whose group widths are chosen by balancing paths that include two block evaluations, latch delay L, and downstream mux delays (p.2-p.3).
choices:
  block_sizing: delay_balanced_analytical [outside domain]   # p.3
  duplication: time_multiplexed_shared [outside domain]   # p.2
  select_source: rippled_block_carries   # p.2-p.3
new_choices:
  evaluation_schedule: cin1_then_cin0_half_cycles — the shared block evaluates both assumed carry inputs within one clock cycle   # p.2
  speculative_storage: transparent_latch — latches preserve the Cin=1 sum/carry while the block evaluates Cin=0   # p.2
slots:
  block_adder: ripple_carry   # p.2-p.3
parameters: 32-bit CSAS uses 2-5 stages with printed groupings (10-22), (8-8-16), (7-6-6-13), and (6-6-5-5-10); 64-bit CSAS uses 2-4 stages with groupings (21-43), (17-14-33), and (15-12-10-27). The library cell data are full adder 0.6 nS/70 µm2, MUX 0.7 nS/17 µm2, and latch 0.8 nS/42 µm2 (p.4-p.5).
results:
| metric | value | unit | technology / device | baseline | condition | page |
| area | 2769 | µm2 | 0.35um library, 3.3V / 2005 | 32-bit RCA: 2181 µm2; Area Ratio 127.0% | 32-bit CSAS, 2 stages (10-22) | p.5 |
| delay | 15.6 | Ns | 0.35um library, 3.3V / 2005 | 32-bit RCA: 19 Ns; Delay Ratio 82.1% | 32-bit CSAS, 2 stages (10-22) | p.5 |
| power | 99.3 | mW | 0.35um library, 3.3V / 2005 | 32-bit RCA: 73.7 mW; Power Ratio 134.7% | 32-bit CSAS, 2 stages (10-22) | p.5 |
| area | 3152 | µm2 | 0.35um library, 3.3V / 2005 | 32-bit RCA: 2181 µm2; Area Ratio 144.5% | 32-bit CSAS, 3 stages (8-8-16) | p.5 |
| delay | 13.8 | Ns | 0.35um library, 3.3V / 2005 | 32-bit RCA: 19 Ns; Delay Ratio 72.6% | 32-bit CSAS, 3 stages (8-8-16) | p.5 |
| power | 115.1 | mW | 0.35um library, 3.3V / 2005 | 32-bit RCA: 73.7 mW; Power Ratio 156.2% | 32-bit CSAS, 3 stages (8-8-16) | p.5 |
| area | 3373 | µm2 | 0.35um library, 3.3V / 2005 | 32-bit RCA: 2181 µm2; Area Ratio 154.7% | 32-bit CSAS, 4 stages (7-6-6-13) | p.5 |
| delay | 12.1 | Ns | 0.35um library, 3.3V / 2005 | 32-bit RCA: 19 Ns; Delay Ratio 63.7% | 32-bit CSAS, 4 stages (7-6-6-13) | p.5 |
| power | 123.7 | mW | 0.35um library, 3.3V / 2005 | 32-bit RCA: 73.7 mW; Power Ratio 167.8% | 32-bit CSAS, 4 stages (7-6-6-13) | p.5 |
| area | 3456 | µm2 | 0.35um library, 3.3V / 2005 | 32-bit RCA: 2181 µm2; Area Ratio 158.5% | 32-bit CSAS, 5 stages (6-6-5-5-10) | p.5 |
| delay | 11.3 | Ns | 0.35um library, 3.3V / 2005 | 32-bit RCA: 19 Ns; Delay Ratio 59.5% | 32-bit CSAS, 5 stages (6-6-5-5-10) | p.5 |
| power | 135.3 | mW | 0.35um library, 3.3V / 2005 | 32-bit RCA: 73.7 mW; Power Ratio 183.6% | 32-bit CSAS, 5 stages (6-6-5-5-10) | p.5 |
| area | 5677 | µm2 | 0.35um library, 3.3V / 2005 | 64-bit RCA: 4447 µm2; Area Ratio 127.7% | 64-bit CSAS, 2 stages (21-43) | p.5 |
| delay | 26.37 | Ns | 0.35um library, 3.3V / 2005 | 64-bit RCA: 37.42 Ns; Delay Ratio 70.5% | 64-bit CSAS, 2 stages (21-43) | p.5 |
| power | 203.6 | mW | 0.35um library, 3.3V / 2005 | 64-bit RCA: 150 mW; Power Ratio 135.7% | 64-bit CSAS, 2 stages (21-43) | p.5 |
| area | 6368 | µm2 | 0.35um library, 3.3V / 2005 | 64-bit RCA: 4447 µm2; Area Ratio 143.2% | 64-bit CSAS, 3 stages (17-14-33) | p.5 |
| delay | 21.35 | Ns | 0.35um library, 3.3V / 2005 | 64-bit RCA: 37.42 Ns; Delay Ratio 57.1% | 64-bit CSAS, 3 stages (17-14-33) | p.5 |
| power | 232.3 | mW | 0.35um library, 3.3V / 2005 | 64-bit RCA: 150 mW; Power Ratio 154.9% | 64-bit CSAS, 3 stages (17-14-33) | p.5 |
| area | 6759 | µm2 | 0.35um library, 3.3V / 2005 | 64-bit RCA: 4447 µm2; Area Ratio 152.0% | 64-bit CSAS, 4 stages (15-12-10-27) | p.5 |
| delay | 18.8 | Ns | 0.35um library, 3.3V / 2005 | 64-bit RCA: 37.42 Ns; Delay Ratio 50.2% | 64-bit CSAS, 4 stages (15-12-10-27) | p.5 |
| power | 248.3 | mW | 0.35um library, 3.3V / 2005 | 64-bit RCA: 150 mW; Power Ratio 165.5% | 64-bit CSAS, 4 stages (15-12-10-27) | p.5 |
errors_and_checks: The architecture performs exact binary addition by evaluating both possible carry inputs; no fault model, detection coverage, or checker is reported (p.2-p.3).
conditions: The delay analysis assumes ripple-adder delay is linear in width and buffering keeps each adder/multiplexer load constant (p.2). The implementation requires each shared upper block to complete two additions within one clock cycle (p.2-p.3). Synthesis targets minimum power/area, uses equiprobable input bits, and excludes output flip-flops (p.4). CSAS is faster than RCA but slower than CSA, while its area and power are below CSA; the intended use permits an intermediate area/delay tradeoff (p.1, p.5).
evidence: §2 equations (1)-(11) and Figures 1-2; §3 equations (12)-(21) and Figures 3-4; Tables 1-6 (p.1-p.5).

## new_families
none

## space_gaps
* carry_select.duplication lacks time_multiplexed_shared, where one upper block evaluates Cin=1 and Cin=0 in successive half-cycles and a latch preserves the first result (p.2).
* carry_select.block_sizing lacks analytically path-balanced variable groups derived from full-adder/mux/latch delays A/M/L (p.2-p.3).

## open_questions
* Table 5 reports simulated 64-bit CSAS delays of 26.37 Ns, 21.35 Ns, and 18.8 Ns, while Table 6 reports 27.76 ns, 23.46 ns, and 21.45 ns for the same configurations (p.5).
* Table 3 and Table 4 assign different group partitions to the 32-bit three-, four-, and five-stage CSAS configurations while reporting the same simulated delays (p.5).
* The conclusion states that four-stage 64-bit CSAS has 3.4% less delay than two-stage CSA, but Table 5 values 18.8 Ns and 19.81 Ns imply a different reduction (p.4-p.5).
