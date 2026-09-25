---
handle: almurib2016
citation: H. A. F. Almurib, T. N. Kumar, F. Lombardi, "Inexact Designs for Approximate Low Power Addition by Cell Replacement", Design, Automation and Test in Europe (DATE), pp. 660-665, 2016
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [int12, int16]
authority: incremental
pages_read: 660-665 / 6
---

## summary
The paper proposes three inexact full-adder cells, InXA1/InXA2/InXA3, and uses them to replace low-order exact cells in ripple-carry adders. Exhaustive cell/RCA simulations and image-addition experiments identify InXA2 as the best overall design among the evaluated approximate cells. # p.660, p.665

## families
### lower_part_approximate  (role: proposes)
mechanism: An n-bit ripple-carry adder replaces exact full-adder cells from the LSB upward with InXA cells. InXA1 retains an exact Sum and approximates Carry, so its carry error can propagate into subsequent cells. InXA2 and InXA3 retain exact Carry and approximate Sum, which prevents an LSB sum error from propagating to higher cells. The paper sweeps the number of approximate bits, denoted NAB, while the remaining upper cells stay exact. # p.661, p.663
choices:
  lower_width: 3 / 6 / 9 / 12 [outside domain]   # p.663
  lower_cell: inexact_cell_inxa   # p.660-p.661
  carry_to_upper: ripple_cell_cout [outside domain]   # p.661, p.663
new_choices:
  cell_variant: {InXA1, InXA2, InXA3} — selects one of the three proposed cell truth functions   # p.661
  approximated_output: {Carry, Sum} — InXA1 approximates Carry; InXA2/InXA3 approximate Sum   # p.661
slots:
  upper_adder: ripple_carry   # p.660, p.663
parameters: 1-bit InXA cells; 12-bit exhaustive RCA experiment; NAB swept from 1 through 12, with reported plots at 25%/50%/75%/100%; 16-bit image-addition adder; image example NAB=5   # p.663-p.664
results:
| metric | value | unit | technology / device | baseline | condition | page |
| InXA1 erroneous Sum entries | 0 | entries | 45 nm PTM (2016) | exact full-adder truth table | exhaustive 8-input cell truth table | p.662 |
| InXA1 erroneous Carry entries | 2 | entries | 45 nm PTM (2016) | exact full-adder truth table | exhaustive 8-input cell truth table | p.662 |
| InXA1 Sum error rate | 0 | % | 45 nm PTM (2016) | exact full-adder truth table | exhaustive 8-input cell truth table | p.662 |
| InXA1 Carry error rate | 25 | % | 45 nm PTM (2016) | exact full-adder truth table | exhaustive 8-input cell truth table | p.662 |
| InXA2 erroneous Sum entries | 2 | entries | 45 nm PTM (2016) | exact full-adder truth table | exhaustive 8-input cell truth table | p.662 |
| InXA2 erroneous Carry entries | 0 | entries | 45 nm PTM (2016) | exact full-adder truth table | exhaustive 8-input cell truth table | p.662 |
| InXA2 Sum error rate | 25 | % | 45 nm PTM (2016) | exact full-adder truth table | exhaustive 8-input cell truth table | p.662 |
| InXA2 Carry error rate | 0 | % | 45 nm PTM (2016) | exact full-adder truth table | exhaustive 8-input cell truth table | p.662 |
| InXA3 erroneous Sum entries | 2 | entries | 45 nm PTM (2016) | exact full-adder truth table | exhaustive 8-input cell truth table | p.662 |
| InXA3 erroneous Carry entries | 0 | entries | 45 nm PTM (2016) | exact full-adder truth table | exhaustive 8-input cell truth table | p.662 |
| InXA3 Sum error rate | 25 | % | 45 nm PTM (2016) | exact full-adder truth table | exhaustive 8-input cell truth table | p.662 |
| InXA3 Carry error rate | 0 | % | 45 nm PTM (2016) | exact full-adder truth table | exhaustive 8-input cell truth table | p.662 |
| InXA1 transistor count | 6 | transistors | 45 nm PTM (2016) | EFA: 10; AMA1-4/AXA | 1-bit cell | p.662 |
| InXA2 transistor count | 8 | transistors | 45 nm PTM (2016) | EFA: 10; AMA1-4/AXA | 1-bit cell | p.662 |
| InXA3 transistor count | 6 | transistors | 45 nm PTM (2016) | EFA: 10; AMA1-4/AXA | 1-bit cell | p.662 |
| InXA1 X input-node capacitance | 6 | Cgn | 45 nm PTM (2016) | AMA1-4/AXA | minimum-transistor capacitance model | p.662 |
| InXA1 Y input-node capacitance | 6 | Cgn | 45 nm PTM (2016) | AMA1-4/AXA | minimum-transistor capacitance model | p.662 |
| InXA1 Cin input-node capacitance | 8 | Cgn | 45 nm PTM (2016) | AMA1-4/AXA | minimum-transistor capacitance model | p.662 |
| InXA2 X input-node capacitance | 6 | Cgn | 45 nm PTM (2016) | AMA1-4/AXA | minimum-transistor capacitance model | p.662 |
| InXA2 Y input-node capacitance | 6 | Cgn | 45 nm PTM (2016) | AMA1-4/AXA | minimum-transistor capacitance model | p.662 |
| InXA2 Cin input-node capacitance | 2 | Cgn | 45 nm PTM (2016) | AMA1-4/AXA | minimum-transistor capacitance model | p.662 |
| InXA3 X input-node capacitance | 6 | Cgn | 45 nm PTM (2016) | AMA1-4/AXA | minimum-transistor capacitance model | p.662 |
| InXA3 Y input-node capacitance | 6 | Cgn | 45 nm PTM (2016) | AMA1-4/AXA | minimum-transistor capacitance model | p.662 |
| InXA3 Cin input-node capacitance | 0 | Cgn | 45 nm PTM (2016) | AMA1-4/AXA | minimum-transistor capacitance model | p.662 |
| EFA average delay | 0.174419 | ns | 45 nm PTM (2016) | exact full adder [8] | exhaustive input simulation | p.662 |
| EFA average energy dissipation | 0.926751 | fJ | 45 nm PTM (2016) | exact full adder [8] | exhaustive input simulation | p.662 |
| EFA average EDP | 0.161643 | ns.fJ | 45 nm PTM (2016) | exact full adder [8] | exhaustive input simulation | p.662 |
| EFA worst delay | 0.424647 | ns | 45 nm PTM (2016) | exact full adder [8] | exhaustive input simulation | p.662 |
| EFA worst energy dissipation | 2.366840 | fJ | 45 nm PTM (2016) | exact full adder [8] | exhaustive input simulation | p.662 |
| EFA worst EDP | 1.005072 | ns.fJ | 45 nm PTM (2016) | exact full adder [8] | exhaustive input simulation | p.662 |
errors_and_checks: InXA1 differs from the exact truth table in two Carry outputs and no Sum outputs. InXA2/InXA3 each differ in two Sum outputs and no Carry outputs. The paper evaluates RCA ER/NMED/MRED exhaustively and image quality through MSE/PSNR/NK/MAE/NAE/AD/MD/SC; no formal error bound or concurrent checker is provided. # p.661-p.664
conditions: Cell simulations use LTSPICE IV, the 45 nm PTM, all eight input combinations, and inputs supplied every 2ns. InXA1/InXA2 outperform earlier approximate cells in plotted delay/energy/EDP metrics; InXA3 saves energy but has larger delay. InXA2 avoids carry-error propagation and gives the lowest reported RCA error rate/NMED and generally the best image-addition quality. The application assumes error-tolerant image processing. # p.662-p.665
evidence: §II; Tables 1-4; Figures 1-9; §III and Figures 10-12; §IV and Figures 13-22; §V, pp.661-665

## new_families
none

## space_gaps
* `lower_part_approximate.lower_width` excludes NAB values such as 1/3/6/9 that the paper evaluates; the domain permits only multiples of four. # p.663
* `lower_part_approximate.carry_to_upper` lacks ordinary ripple-connected cell Cout, including the distinction between InXA1's approximate Cout and InXA2/InXA3's exact Cout. # p.661, p.663
* `lower_part_approximate.lower_cell: inexact_cell_inxa` does not distinguish the three truth functions, so a `cell_variant` choice is needed. # p.661

## open_questions
* Figures 7-12 and 14-20 provide plotted results without tabulated numeric values, so exact proposed-cell delay/energy/EDP and RCA/image-error values cannot be copied from the supplied text.
* The InXA3 discussion says “InXA2 reduces a gate delay,” which may be a naming error that the merge pass must not resolve. # p.661
* The conclusion says InXA1 has the worst NMED, while §III assigns the worst MRED to InXA1; the document does not resolve the discrepancy. # p.663, p.665
