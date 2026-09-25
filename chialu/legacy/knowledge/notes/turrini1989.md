---
handle: turrini1989
citation: S. Turrini, "Optimal Group Distribution in Carry-Skip Adders", 9th IEEE Symposium on Computer Arithmetic (ARITH-9), pp. 96-103, 1989.
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [int32]
authority: incremental
pages_read: 96-103 / 8
---

## summary
The paper proposes an algorithm that selects an optimal, potentially asymmetric group/subgroup distribution for multilevel carry-skip adders under implementation-specific ripple/skip delays (pp.96-99). A fabricated 32-bit, two-level bipolar ECL adder occupies 0.3 x 2.1 mm, has about 1.7 ns worst-case delay, and consumes about 0.6 Watts at -5.2 V (p.102).

## families
### carry_skip  (role: extends)
mechanism: The algorithm assigns each block a pair of limits for a carry generated within the block and a carry entering and ending within the block. It partitions a specified worst-case delay into block constraints, recursively expands higher-order blocks into lower-order blocks, and retains expansions producing the most bits. The resulting tree has blocks as nodes, carry-skip levels as tree levels, and adder bits as leaves. AEID supplies the minimum delay increment needed to obtain a distribution with at least one additional bit. (pp.97-100)
choices:
  block_sizing: recursive_delay_pair_optimized [outside domain]   # pp.97-100
  skip_levels: unrestricted [outside domain]   # pp.96-97
new_choices:
  distribution_symmetry: {symmetric, asymmetric} — Whether group placement must be symmetric; the algorithm permits asymmetric distributions.   # p.97
  delay_granularity: {uniform, per_cell_per_level, path_merge_adjusted} — Whether ripple/skip delays are uniform or reflect cell level and merge-node loading.   # pp.97,99
  carry_in_modeling: Bool — Whether a carry into the low-order bit is included during optimization.   # p.97
slots:
  block_adder: ripple_carry   # pp.96-98
parameters: Demonstrated distributions include 2-level/32-bit, 2-level/34-bit, 4-level/56-bit, and up to 5 or 6 levels/128 bits; the fabricated adder is 32-bit and 2-level; the program handles 128 bits and 4 or more carry-skip levels.   # pp.99-103
results:
| metric | value | unit | technology / device | baseline | condition | page |
| area | 0.3 x 2.1 | mm | bipolar ECL; double poly; 0.3 um emitter minimum npn transistor; 3 metal layers; 4 um pitch; τf of 35 ps / 1989 | UNKNOWN | 32-bit, 2-level distribution; voltage-reference generators included | p.102 |
| worst-case adder delay | about 1.7 | ns | bipolar ECL; double poly; 0.3 um emitter minimum npn transistor; 3 metal layers; 4 um pitch; τf of 35 ps / 1989 | UNKNOWN | layout and spice simulations; 32-bit, 2-level distribution | p.102 |
| power consumption | about 0.6 | Watts | bipolar ECL; double poly; 0.3 um emitter minimum npn transistor; 3 metal layers; 4 um pitch; τf of 35 ps / 1989 | UNKNOWN | power supply voltage of -5.2 V | p.102 |
| power supply voltage | -5.2 | V | bipolar ECL; double poly; 0.3 um emitter minimum npn transistor; 3 metal layers; 4 um pitch; τf of 35 ps / 1989 | UNKNOWN | reported implementation operating point | p.102 |
| worst-case carry delay | 8 | gate delays | unit-delay model / 1989 | UNKNOWN | 2-level, 34-bit distribution | p.100 |
| worst-case carry delay | 8 | gate delays | unit-delay model / 1989 | 2-level, 32-bit example | 4-level, 56-bit distribution | pp.100-101 |
| maximum packed width | 38 | bits | abstract delay model / 1989 | 5-level distribution with 34 bits | 4-level distribution; worst-case delay 11 gate delays; terminal ripple/skip cells take 2 units | p.101 |
| gate-count reduction | at least three | factor | bipolar ECL / 1989 | Ling adder | carry-skip implementation at comparable speed | p.103 |
| optimization runtime | less than a second | VAX 785 CPU time | VAX 785 / 1989 | UNKNOWN | configurations with 128 bits and 4 or more carry-skip levels | p.103 |
errors_and_checks: none
conditions: The algorithm accepts different ripple-cell and skip-cell delays at each carry-skip level, including larger delays where carry paths merge. # pp.97,99 The algorithm may generate more bits than requested, after which bits can be removed without changing worst-case delay unless removal lowers both delay limits of the affected block. # p.100 Higher carry-skip levels do not always improve performance because Skip-signal generation consumes the timing allowance; the useful level limit depends on operand width and cell delays. # p.101 Manchester-chain ripple delay must be modeled as a function of the number of pass transistors in a group. # p.101 The ECL implementation favors carry-skip when area/current matter and reports speed comparable with more complex adders, while using fewer gates than a Ling adder. # pp.102-103 The tree-building phase has exponential behavior, although the paper reports practical performance through 5 or 6 levels and 128 bits. # p.99
evidence: Abstract and limitations (pp.96-97); worst-case-delay model and algorithm (pp.97-100); Figures 2-5 and Tables 1-2 (pp.100-102); ECL process/layout/simulation results (pp.102-103).

## new_families
none

## space_gaps
* The `skip_levels` domain ends at 3, but the paper demonstrates a 4-level adder and discusses practical optimization through 5 or 6 levels. # pp.99-103
* The `block_sizing` domain lacks a value for recursive optimization using per-block generation/ending delay pairs rather than uniform/trapezoidal sizing. # pp.97-100
* The family lacks choices for asymmetric distributions, low-order carry-in modeling, and implementation-specific delays at merge nodes. # pp.97,99

## open_questions
* The numerical entries in Tables 1 and 2 are not legible in the supplied document text, so only values stated in the surrounding prose are recorded.
* The fabricated ECL adder’s exact full-adder and skip-cell circuit topologies are not specified.
