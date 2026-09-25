---
handle: ramkumar2012
citation: B. Ramkumar, H. M. Kittur, "Low-Power and Area-Efficient Carry Select Adder", IEEE Transactions on VLSI Systems, vol. 20, no. 2, pp. 371-375, 2012.
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [8-bit binary, 16-bit binary, 32-bit binary, 64-bit binary]
authority: incremental
pages_read: 371-375 / 5
---

## summary
The paper replaces each Cin = 1 ripple-carry adder in a square-root carry-select adder with a Binary to Excess-1 Converter. The modified 8-, 16-, 32-, and 64-bit adders reduce cell area and power at the cost of increased delay, with improving tradeoffs as width increases.

## families
### carry_select  (role: extends)
mechanism: A regular SQRT CSLA computes each group twice with ripple-carry adders for Cin = 0 and Cin = 1, then selects the required result through multiplexers. The modified SQRT CSLA retains the Cin = 0 ripple-carry adder and replaces the Cin = 1 adder with an n + 1-bit Binary to Excess-1 Converter driven by the first adder's output. A multiplexer selects the direct or incremented result from the incoming carry. # p.371-374
choices:
  block_sizing: square_root_ramp   # p.371, p.373
  duplication: bec_increment   # p.371, p.373-374
  select_source: rippled_block_carries   # p.371, p.373-374
new_choices:
  none
slots:
  block_adder: ripple_carry   # p.371, p.373-374
parameters: 8-, 16-, 32-, and 64-b SQRT CSLAs; the analyzed 16-b design has five groups; an n + 1-bit BEC replaces each n-bit RCA for Cin = 1. # p.371-374
results:
| metric | value | unit | technology / device | baseline | condition | page |
| cell-area reduction | 9.7 | % | TSMC 0.18 um technology; 2012 | regular SQRT CSLA | 8-b modified SQRT CSLA | p.374 |
| cell-area reduction | 15 | % | TSMC 0.18 um technology; 2012 | regular SQRT CSLA | 16-b modified SQRT CSLA | p.374 |
| cell-area reduction | 16.7 | % | TSMC 0.18 um technology; 2012 | regular SQRT CSLA | 32-b modified SQRT CSLA | p.374 |
| cell-area reduction | 17.4 | % | TSMC 0.18 um technology; 2012 | regular SQRT CSLA | 64-b modified SQRT CSLA | p.374 |
| total-power reduction | 7.6 | % | TSMC 0.18 um technology; 2012 | regular SQRT CSLA | 8-b modified SQRT CSLA | p.374 |
| total-power reduction | 10.56 | % | TSMC 0.18 um technology; 2012 | regular SQRT CSLA | 16-b modified SQRT CSLA | p.374 |
| total-power reduction | 13.63 | % | TSMC 0.18 um technology; 2012 | regular SQRT CSLA | 32-b modified SQRT CSLA | p.374 |
| total-power reduction | 15.46 | % | TSMC 0.18 um technology; 2012 | regular SQRT CSLA | 64-b modified SQRT CSLA | p.374 |
| delay overhead | 14 | % | TSMC 0.18 um technology; 2012 | regular SQRT CSLA | 8-b modified SQRT CSLA | p.375 |
| delay overhead | 9.8 | % | TSMC 0.18 um technology; 2012 | regular SQRT CSLA | 16-b modified SQRT CSLA | p.375 |
| delay overhead | 6.7 | % | TSMC 0.18 um technology; 2012 | regular SQRT CSLA | 32-b modified SQRT CSLA | p.375 |
| delay overhead | 3.76 | % | TSMC 0.18 um technology; 2012 | regular SQRT CSLA | 64-b modified SQRT CSLA | p.375 |
| power-delay-product increase | 5.2 | % | TSMC 0.18 um technology; 2012 | regular SQRT CSLA | 8-b modified SQRT CSLA | p.375 |
| power-delay-product reduction | 1.76 | % | TSMC 0.18 um technology; 2012 | regular SQRT CSLA | 16-b modified SQRT CSLA | p.375 |
| power-delay-product reduction | 8.18 | % | TSMC 0.18 um technology; 2012 | regular SQRT CSLA | 32-b modified SQRT CSLA | p.375 |
| power-delay-product reduction | 12.28 | % | TSMC 0.18 um technology; 2012 | regular SQRT CSLA | 64-b modified SQRT CSLA | p.375 |
| area-delay-product reduction | 2.9 | % | TSMC 0.18 um technology; 2012 | regular SQRT CSLA | 8-b modified SQRT CSLA | p.375 |
| area-delay-product reduction | 6.7 | % | TSMC 0.18 um technology; 2012 | regular SQRT CSLA | 16-b modified SQRT CSLA | p.375 |
| area-delay-product reduction | 11 | % | TSMC 0.18 um technology; 2012 | regular SQRT CSLA | 32-b modified SQRT CSLA | p.375 |
| area-delay-product reduction | 14.4 | % | TSMC 0.18 um technology; 2012 | regular SQRT CSLA | 64-b modified SQRT CSLA | p.375 |
| estimated area saving | 113 | gate areas | AOI unit-gate model; 2012 | regular 16-b SQRT CSLA | modified 16-b SQRT CSLA | p.374 |
| estimated delay increase | 11 | gate delays | AOI unit-gate model; 2012 | regular 16-b SQRT CSLA | modified 16-b SQRT CSLA | p.374 |
errors_and_checks: none
conditions: The analytical comparison assigns one area unit and one delay unit to each AND/OR/inverter gate. # p.372 The ASIC comparison uses typical TSMC 0.18 um libraries, placed-and-routed standard cells, extracted parasitic RC, static timing analysis, and the same all-input-condition VCD for both architectures. # p.374 The power-delay product is worse for the modified 8-b design despite its lower area and power. # p.375 The relative area/power savings increase and the delay overhead decreases as width increases from 8 to 64 bits. # p.374-375
evidence: Sections II-VII; Tables I-V; Figs. 2-8, pp.372-375.

### prefix_and_incrementer  (role: instantiates)
mechanism: The Binary to Excess-1 Converter adds one to an n-bit ripple-carry result so that one adder can supply both carry-select candidates. An n + 1-bit BEC replaces an n-bit RCA. The 4-b example forms X0 = NOT B0, X1 = B0 XOR B1, X2 = B2 XOR (B0 AND B1), and X3 = B3 XOR (B0 AND B1 AND B2). # p.372
choices:
  structure: ripple_and_chain   # p.372
new_choices:
  none
slots:
  none
parameters: n + 1-bit BEC for an n-bit RCA; 4-b BEC example; 3-b BEC used with the 2-b RCA in group2 of the 16-b design. # p.372-374
results:
| metric | value | unit | technology / device | baseline | condition | page |
| group2 area count | 43 | gate-count units | AOI unit-gate model; 2012 | 57 gate-count units for regular group2 | modified 16-b SQRT CSLA group2 | p.373-374 |
errors_and_checks: none
conditions: The BEC supplies only the Cin = 1 candidate and remains paired with an RCA that computes the Cin = 0 candidate. # p.372-374 The paper attributes the area reduction to the BEC requiring fewer logic gates than an n-bit full-adder structure. # p.371
evidence: Section III; Table II; Figs. 2-3 and 6-7, pp.372-374.

## new_families
none

## space_gaps
* none

## open_questions
* The supplied rendering does not expose the absolute delay/area/power entries in Table V, so the note records the relative values stated in the surrounding text and Fig. 8.
