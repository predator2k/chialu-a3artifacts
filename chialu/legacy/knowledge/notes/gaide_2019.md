---
handle: gaide_2019
citation: B. Gaide, D. Gaitonde, C. Ravishankar, T. Bauer, "Xilinx Adaptive Compute Acceleration Platform: Versal Architecture", ACM/SIGDA International Symposium on Field-Programmable Gate Arrays (FPGA), 2019
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [UNKNOWN]
authority: incremental
pages_read: 84-93 / 10
---

## summary
The paper presents the 7nm Versal ACAP architecture. The arithmetic contribution integrates most dedicated carry logic into LUT cascade paths while retaining 8-bit carry-lookahead logic, which reduces dedicated carry-logic area by a factor of 5 without changing long-chain speed relative to UltraScale at 7nm. # p.87

## families
### carry_lookahead  (role: instantiates)
mechanism: Each Versal LUT supplies an additional PROP output for carry-lookahead operation. Dedicated LUT-to-LUT cascade paths and 8-bit lookahead blocks implement the carry structure, while much of UltraScale's dedicated carry circuitry is absorbed into the LUT. LUT outputs serve both generic and arithmetic functions, which also reduces CLB output-muxing costs. # pp.86-87
choices:
  group_size: 8   # pp.86-87, Figs. 4 and 7
new_choices:
  carry_logic_placement: lut_absorbed_with_cascade — Most dedicated carry logic is absorbed into LUTs and their cascade paths.   # p.87
slots: none
parameters: 8-bit lookahead structure; full supported carry-chain width UNKNOWN   # p.87, Fig. 7
results:
| metric | value | unit | technology / device | baseline | condition | page |
| dedicated carry-logic area reduction | factor of 5 | relative area | 7nm Versal, 2019 | UltraScale carry logic at 7nm | long carry-chain speeds remain constant | p.87 |
errors_and_checks: none
conditions: The area result applies to the dedicated carry logic rather than the complete CLB or adder. The comparison holds both architectures at 7nm, and the paper reports constant long carry-chain speed. # p.87
evidence: §3.1, §3.1.1, §3.1.3, Figs. 4, 5, and 7, pp.86-87

## new_families
none

## space_gaps
* `carry_lookahead` lacks a `carry_logic_placement` choice covering LUT-absorbed carry logic with dedicated cascade paths. # p.87

## open_questions
* The paper does not state how the 8-bit lookahead blocks connect across a full-width adder, so `intergroup_carry`, `levels`, and the maximum carry-chain width remain UNKNOWN. # p.87
* The paper does not report complete-adder area, delay, power, operand width, or arithmetic format. # p.87
