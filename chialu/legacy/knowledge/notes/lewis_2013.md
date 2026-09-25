---
handle: lewis_2013
citation: D. Lewis, D. Cashman, M. Chan, J. Chromczak, G. Lai, A. Lee, et al., "Architectural Enhancements in Stratix V", ACM/SIGDA International Symposium on Field-Programmable Gate Arrays (FPGA), 2013
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [binary]
authority: incremental
pages_read: 147-156 / 10
---

## summary
Stratix V adds a second carry-skip level across each 20-bit LAB, while retaining the two-bit skip inside each ALM. The resulting long carry chain has one multiplexer delay per 20 bits and an estimated factor-of-5 speed improvement with a modest LAB-area increase. # p.154-p.155

## families
### carry_skip  (role: extends)
mechanism: Each ALM forms two binary sums and combines the per-bit propagate/generate signals into a two-bit skip. A multiplexer passes `cin` directly to `cout` when both bits propagate. Stratix V combines the ALM propagate signals into a second skip covering all 20 adder bits in a LAB. A wide chain traverses five two-bit stages in the initial half-LAB, one 20-bit skip per intervening LAB, and five two-bit stages in the final half-LAB. # p.154-p.155
choices:
  block_width: 2 # p.154-p.155
  skip_levels: 2 # p.154-p.155
  skip_gate: mux # p.154-p.155
new_choices:
  level_block_widths: [2, 20] — skip span at the ALM and LAB levels # p.154-p.155
slots:
  block_adder: ripple_carry # p.154-p.155
parameters: 2 adder bits/ALM; 10 ALMs/LAB; 20 adder bits/LAB; one second-level skip per LAB # p.148, p.154-p.155
results:
| metric | value | unit | technology / device | baseline | condition | page |
| delay per bit | halved | relative delay | UNKNOWN / Stratix IV | Stratix II/III one-bit ripple carry | two-bit ALM carry skip | p.155 |
| long-carry-chain speed improvement | factor of 5 | factor | 28nm TSMC / Stratix V | two-bit carry skip | early SPICE timing estimate; modest LAB-area increase | p.155 |
errors_and_checks: none
conditions: The propagate/generate logic remains outside the critical path and can use small gates, while only the carry multiplexer requires large transistors. # p.155 A tested carry-select extension was no faster than the basic two-level carry skip. # p.155 The reported factor-of-5 improvement is an early SPICE estimate rather than measured silicon timing. # p.155
evidence: §6; Figures 16-18; pp.154-155

### ripple_carry  (role: compares)
mechanism: Stratix II and later ALMs provide two adder bits. Each full-adder bit uses a one-bit ripple carry, and the speed-critical `cin`-to-`cout` multiplexer path is optimized across the dedicated cascade wire between adjacent logic elements. # p.154
choices:
new_choices:
  none
slots:
  none
parameters: 2 adder bits/ALM; 1-bit carry step # p.154
results:
| metric | value | unit | technology / device | baseline | condition | page |
| carry delay | one mux | mux delay per bit | UNKNOWN / Stratix II and Stratix III | UNKNOWN | dedicated ripple-carry path | p.154-p.155 |
errors_and_checks: none
conditions: The one-bit ripple structure was replaced by a two-bit skip in Stratix IV because the carry-multiplexer path limited wide-adder speed. # p.154-p.155
evidence: §6; Figure 15; pp.154-155

### carry_select  (role: compares)
mechanism: Stratix I duplicates the carry chain and selects the result through an output multiplexer. The paper reports three multiplexer delays per ten bits and states that the duplicated chain and output selector were too expensive. A later carry-select variant added to the two-level skip was not faster than the basic skip design. # p.154-p.155
choices:
  duplication: full_duplicate # p.154
new_choices:
  none
slots:
  none
parameters: reported delay span of 10 bits; other block parameters UNKNOWN # p.154
results:
| metric | value | unit | technology / device | baseline | condition | page |
| carry delay | 3 | muxes per 10 bits | UNKNOWN / Stratix I | UNKNOWN | Stratix I carry-select adder | p.154 |
errors_and_checks: none
conditions: Carry-chain duplication and an output-select multiplexer impose a cost that the authors found unjustified. # p.154 The evaluated two-level-skip-plus-select version was not faster than two-level skip alone. # p.155
evidence: §6; Figure 18; pp.154-155

## new_families
none

## space_gaps
* `carry_skip.block_width` cannot represent distinct widths for multiple skip levels; Stratix V uses 2-bit first-level blocks and a 20-bit second-level block, which also exceeds the declared maximum of 16. # p.154-p.155

## open_questions
* The paper does not quantify the Stratix V LAB-area increase associated with the second skip level.
* Figure 18 plots simulated delays, but the text does not print the individual delay values or state sufficient data for exact extraction.
* The paper does not identify the fabrication technology or implementation year for the Stratix I-IV comparison rows.
