---
handle: oklobdzija_barnes1985
citation: V. G. Oklobdzija, E. R. Barnes, "Some Optimal Schemes for ALU Implementation in VLSI Technology", 7th IEEE Symposium on Computer Arithmetic (ARITH-7), 1985.
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [binary16, binary32, binary48, binary54, binary64]
authority: landmark
pages_read: 7 / 7 (printed pp.2-8)
---

## summary
The paper gives an optimal histogram-based algorithm for dividing a carry-skip adder into variable-width groups under a constant group-skip delay model (pp.2-5). A second algorithm adds a block-level skip path and can match or outperform the reported full carry-lookahead baseline while retaining a regular carry chain (pp.5-8).

## families
### carry_skip  (role: proposes)
mechanism: The adder augments a ripple-carry chain with group-propagate paths that let an entering carry skip a group when every bit propagates it. The first algorithm selects the number of groups and derives symmetric variable group sizes from a histogram so that the maximum carry delay is minimized. The second algorithm forms symmetric blocks of groups, adds block-skip paths, trims oversized middle blocks to the required width, and applies the first algorithm within each block (pp.2-6).
choices:
  block_sizing: trapezoidal_variable   # pp.3-6
  skip_levels: 2   # pp.5-6
new_choices:
  group_partition_method: histogram_optimal — group widths are constructed from bounded histogram-column heights rather than selected heuristically   # pp.3-5
  skip_delay_model: constant_relative_delay_T — T is the assumed group-skip time measured relative to one-bit ripple time   # pp.3,7
slots:
  block_adder: ripple_carry   # p.2
parameters: Single-level examples use n=48/m=7/groups 4,7,8,9,9,8,7,4; n=54/m=7/groups 4,7,10,12,10,7,4; and n=64/m=8/groups 4,7,10,11,11,10,7,4, with T=3 (pp.3-4). Two-level examples use n=32/blocks 4,8,8,8,4; n=48/blocks 4,8,12,12,8,4; and n=64/blocks 4,8,15,10,15,8,4, with T=3 (p.6).
results:
| metric | value | unit | technology / device | baseline | condition | page |
| maximum carry delay, single-level n=48 | 12 | UNKNOWN | UNKNOWN, 1985 | Lehman-Burla heuristic: 14 | equal group-skip and one-bit ripple times | p.2 |
| maximum carry delay, single-level n=48 | 21 | UNKNOWN | n-MOS model, node UNKNOWN, 1985 | none | T=3 | p.3 |
| maximum carry delay, single-level n=54 | 21 | UNKNOWN | n-MOS model, node UNKNOWN, 1985 | none | T=3 | p.3 |
| maximum carry delay, single-level n=64 | 24 | UNKNOWN | n-MOS model, node UNKNOWN, 1985 | none | T=3 | p.4 |
| maximum carry delay, two-level n=32 | 15 | UNKNOWN | n-MOS model, node UNKNOWN, 1985 | none | T=3 | p.6 |
| maximum carry delay, two-level n=48 | 18 | UNKNOWN | n-MOS model, node UNKNOWN, 1985 | none | T=3 | p.6 |
| maximum carry delay, two-level n=64 | 21 | UNKNOWN | n-MOS model, node UNKNOWN, 1985 | none | T=3 | p.6 |
| maximum carry delay, single-level n=16 | 6 | UNKNOWN | UNKNOWN, 1985 | full CLA, group size 4: 6 | T=1 gate-delay comparison | p.7 |
| maximum carry delay, single-level n=32 | 9 | UNKNOWN | UNKNOWN, 1985 | full CLA, group size 4: 8 | T=1 gate-delay comparison | p.7 |
| maximum carry delay, single-level n=48 | 12 | UNKNOWN | UNKNOWN, 1985 | full CLA, group size 4: 10 | T=1 gate-delay comparison | p.7 |
| maximum carry delay, single-level n=64 | 14 | UNKNOWN | UNKNOWN, 1985 | full CLA, group size 4: 10 | T=1 gate-delay comparison | p.7 |
| maximum carry delay, two-level n=16 | 5 | UNKNOWN | UNKNOWN, 1985 | full CLA, group size 4: 6 | T=1 gate-delay comparison | p.8 |
| maximum carry delay, two-level n=32 | 7 | UNKNOWN | UNKNOWN, 1985 | full CLA, group size 4: 8 | T=1 gate-delay comparison | p.8 |
| maximum carry delay, two-level n=48 | 9 | UNKNOWN | UNKNOWN, 1985 | full CLA, group size 4: 10 | T=1 gate-delay comparison | p.8 |
| maximum carry delay, two-level n=64 | 10 | UNKNOWN | UNKNOWN, 1985 | full CLA, group size 4: 10 | T=1 gate-delay comparison | p.8 |
| CLA delay advantage over single-level carry-skip | 40% | % | UNKNOWN, 1985 | single-level carry-skip | n=64, T=1 | p.8 |
| two-level carry-skip delay advantage over CLA | approximately 20% | % | UNKNOWN, 1985 | full CLA, group size 4 | n=16, T=1 | p.8 |
errors_and_checks: none
conditions: The single-level grouping proof establishes optimality for 2 ≤ T ≤ 7 (p.5). The analysis treats T as constant because group-skip delay changes slowly over the relevant group-size range (p.3). The block algorithm assumes the block-skip time Tb equals the group-skip time Tg, although the authors state that the technique extends to Tg ≠ Tb (p.5). The T=1 comparison assumes delay independent of gate fan-in/fan-out, which favors the CLA baseline (p.7). The n-MOS delay model counts traversed FET transistors and adjusts for fan-out/wiring capacitance; simulation of an implemented 32-bit n-MOS ALU confirmed the assumptions, but no measured delay is reported (p.7). The method is especially applicable to large floating-point fraction ALUs (p.8).
evidence: Abstract; §§1-4.1; Procedure 2; Lemmas 1-2; Theorem 1; Procedure 3; Figs.1-8; Tables 1-2 (pp.2-8).

## new_families
none

## space_gaps
* carry_skip lacks separate choices for group-skip delay Tg and block-skip delay Tb, which the paper distinguishes before setting Tb=Tg for its analysis (p.5).
* carry_skip cannot separately encode block sizing and the within-block group sizing applied by the two-level construction (pp.5-6).

## open_questions
* The technology node, circuit dimensions, area, power, and measured delay of the implemented 32-bit n-MOS ALU are not reported (p.7).
* The supplied text states that the block method extends to Tg ≠ Tb but does not give the resulting construction or optimality range (p.5).
