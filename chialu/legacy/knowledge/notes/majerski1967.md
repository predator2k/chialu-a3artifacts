---
handle: majerski1967
citation: S. Majerski, "On Determination of Optimal Distributions of Carry Skips in Adders", IEEE Transactions on Electronic Computers, vol. EC-16, no. 1, pp. 45-58, 1967.
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [binary]
authority: incremental
pages_read: 14 / 14
---

## summary
The paper derives optimal carry-skip distributions that minimize maximum carry propagation time and economical distributions that minimize skip count for a specified time (pp.45,47). The methods cover S1 classical/S2 NOR-gate adders, one/two skip layers, and operation with/without end-around-carry (pp.45-57).

## families
### carry_skip  (role: extends)
mechanism: A skip circuit bypasses consecutive carry positions when their propagation functions permit transmission. One-layer distributions place each position in at most one skip; two-layer distributions nest a shorter second-layer skip inside a longer first-layer skip. Closed-form procedures maximize the supported position count for a given maximum carry propagation time, then remove positions/skips to obtain economical distributions for a specified width and time (pp.46-51).
choices:
  block_sizing: optimal_distribution [outside domain]   # pp.47-51
  skip_levels: {1, 2} [outside domain]   # p.47
  skip_gate: {and_or_bypass, nor_gate [outside domain]}   # pp.46-47
new_choices:
  carry_circuit_type: {S1_classical, S2_nor_gate} — selects the one-position carry circuit and propagation-time unit   # pp.45-47
  optimization_objective: {optimal, economical} — minimizes mcpt first or minimizes skip count for fixed n/T   # p.47
  end_around_carry_mode: {absent, present} — selects the corresponding distribution equations   # pp.45,52-57
slots:
  block_adder: ripple_carry   # pp.45-46
parameters: n positions; one/two skip layers; S1/S2 carry circuits; with/without end-around-carry; maximum carry propagation time T; skip count p or P+Σp_i; asynchronous operation   # pp.45-47
results:
| metric | value | unit | technology / device | baseline | condition | page |
| maximum carry propagation time | 12 | S1 time units | UNKNOWN; result year 1967 | none | optimal 48-position S1, one layer, no end-around-carry | p.48 |
| skip count | 11 | skips | UNKNOWN; result year 1967 | none | optimal 48-position S1, one layer, no end-around-carry | p.48 |
| maximum carry propagation time | 15 | S2 time units | UNKNOWN; result year 1967 | none | optimal 48-position S2, one layer, no end-around-carry | p.49 |
| skip count | 7 | skips | UNKNOWN; result year 1967 | none | optimal 48-position S2, one layer, no end-around-carry | p.49 |
| maximum carry propagation time | 9 | S1 time units | UNKNOWN; result year 1967 | none | optimal 48-position S1, two layers, no end-around-carry | p.50 |
| skip count | 16 | skips | UNKNOWN; result year 1967 | none | optimal 48-position S1, two layers, no end-around-carry | p.50 |
| maximum carry propagation time | 11 | S2 time units | UNKNOWN; result year 1967 | none | optimal 48-position S2, two layers, no end-around-carry | p.51 |
| skip count | 12 | skips | UNKNOWN; result year 1967 | none | optimal 48-position S2, two layers, no end-around-carry | p.51 |
| maximum carry propagation time | 17 | S1 time units | UNKNOWN; result year 1967 | none | optimal 48-position S1, one layer, with end-around-carry | p.52 |
| skip count | 8 | skips | UNKNOWN; result year 1967 | none | optimal 48-position S1, one layer, with end-around-carry | p.52 |
| maximum carry propagation time | 21 | S2 time units | UNKNOWN; result year 1967 | none | optimal 48-position S2, one layer, with end-around-carry | p.53 |
| skip count | 6 | skips | UNKNOWN; result year 1967 | none | optimal 48-position S2, one layer, with end-around-carry | p.53 |
| maximum carry propagation time | 12 | S1 time units | UNKNOWN; result year 1967 | none | optimal 48-position S1, two layers, with end-around-carry | p.55 |
| skip count | 18 | skips | UNKNOWN; result year 1967 | none | optimal 48-position S1, two layers, with end-around-carry | p.55 |
| maximum carry propagation time | 17 | S2 time units | UNKNOWN; result year 1967 | none | optimal 48-position S2, two layers, with end-around-carry | p.57 |
| skip count | 11 | skips | UNKNOWN; result year 1967 | none | optimal 48-position S2, two layers, with end-around-carry | p.57 |
errors_and_checks: none
conditions: Maximum carry propagation time assumes worst-case propagation rather than carry-completion detection (pp.45,47). S2 skips comprise odd numbers of positions at even starting offsets, and S2 optimization removes positions in pairs (pp.45-46,49,51). The optimization imposes no limits on group/section sizes or group counts (p.57). S1/S2 time values are not directly comparable because their time units differ (p.57).
evidence: Definitions 1-9 and Figs. 1-2 (pp.46-47); Sections III-X and Figs. 3-22 (pp.47-57); Figs. 23-24 (p.58).

### end_around_carry  (role: instantiates)
mechanism: End-around-carry variants make group/section indexing cyclic and include paths that traverse all groups or sections before returning to the starting group/section. Separate maximum-propagation equations and distribution procedures are derived for S1/S2 and one/two-layer skip structures (pp.52-57).
choices:
  recirculation: direct_carry_circuit_feedback [outside domain]   # pp.52-57
new_choices:
  skip_layers: {1, 2} — selects one-layer or nested two-layer carry-skip distributions   # pp.52-57
slots:
  none
parameters: S1/S2; n positions; one/two skip layers; cyclic groups/sections; S2 requires an even position count or one added NOR gate   # pp.52-56
results:
| metric | value | unit | technology / device | baseline | condition | page |
| maximum carry propagation time | 17 | S1 time units | UNKNOWN; result year 1967 | none | optimal 48-position S1, one skip layer | p.52 |
| maximum carry propagation time | 21 | S2 time units | UNKNOWN; result year 1967 | none | optimal 48-position S2, one skip layer | p.53 |
| maximum carry propagation time | 12 | S1 time units | UNKNOWN; result year 1967 | none | optimal 48-position S1, two skip layers | p.55 |
| maximum carry propagation time | 17 | S2 time units | UNKNOWN; result year 1967 | none | optimal 48-position S2, two skip layers | p.57 |
errors_and_checks: none
conditions: The paper does not identify a numerical modulus or arithmetic number system for end-around-carry (pp.52-57). S2 end-around-carry methods require an even number of carry-circuit positions and yield only odd mcpt values (pp.53,56).
evidence: Sections VII-X and Figs. 13-22 (pp.52-57).

## new_families
none

## space_gaps
* carry_skip.block_sizing lacks the paper's closed-form optimal/economical nonuniform-distribution value (pp.47-57).
* carry_skip.skip_gate lacks the S2 all-NOR skip circuit value (pp.45-46).
* carry_skip lacks a choice distinguishing one-position classical S1 and six-NOR-gate S2 carry circuits (pp.45-47).
* end_around_carry.recirculation lacks direct cyclic carry-circuit feedback combined with carry skips (pp.52-57).

## open_questions
* The implementation technology/device and absolute propagation delays are not reported; T uses abstract S1/S2 gate-delay units (p.47).
* The paper does not state which modulus or number representation motivates end-around-carry (pp.52-57).
