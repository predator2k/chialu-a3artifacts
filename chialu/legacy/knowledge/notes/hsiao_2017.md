---
handle: hsiao_2017
citation: S.-F. Hsiao, C.-S. Wen, Y.-H. Chen, K.-C. Huang, "Hierarchical Multipartite Function Evaluation", IEEE Transactions on Computers, vol. 66, no. 1, pp. 89-99, 2017
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_SFU]
formats: [Q1.15, Q0.16, Q1.23, Q0.24]
authority: incremental
pages_read: 1-10 / 10
---

## summary
The document extends multipartite table-addition function evaluation with a multilevel decomposition of offset tables, joint optimization of table partitions/guard bits, and lossless decomposition of the initial-value table. The faithfully rounded 16-bit and 24-bit reciprocal/sine/power evaluators reduce table size and improve synthesized ASIC/FPGA area and delay. # p.1, pp.4-9

## families
### multipartite  (role: extends)
mechanism: HMP recursively applies multipartite decomposition to the initial-value function produced by the preceding level. A two-level implementation contains one final TI and \(m^{(1)}+m^{(2)}\) symmetric offset tables whose outputs feed a multi-operand adder. An exhaustive search jointly selects input partitions, table-entry guard bits, and table counts against the final precision requirement. HMP_TI further splits TI losslessly into down-sampled \(TI_{new}\) and difference \(TI_{diff}\) tables without increasing the final adder height. # pp.4-6
choices:
  tables: 2-7 [outside domain]   # pp.5,7
  hierarchical: true   # pp.4-5
  accuracy_target: faithful_1ulp   # pp.2,6
new_choices:
  hierarchy_levels: Int[1..N:1] — number of recursive multipartite decompositions; experiments use \(l=2\)   # pp.4-5
  error_optimization: {separate_error_budgets, joint_exhaustive_check} — whether approximation/quantization/final-rounding errors are budgeted separately or checked jointly   # pp.5-6
  initial_table_decomposition: {none, lossless_downsample_difference} — whether TI is split into \(TI_{new}\) and \(TI_{diff}\)   # p.6
slots:
  none
parameters: Input width equals output width; evaluated widths are 16 and 24 bits. The implemented HMP uses \(l=2\), searches \(m^{(j)}\), \((\beta_i^{(j)},\gamma_i^{(j)})\), \(g^{(j)}\), and \(\alpha^{(2)}\), and evaluates one through six TOs. # pp.2,5-7
results:
| metric | value | unit | technology / device | baseline | condition | page |
| table size | 11,392 | bits | UNKNOWN / 2017 | MP: 14,592 bits | 16-b RCP, HMP | p.8 |
| table size | 297,984 | bits | UNKNOWN / 2017 | MP: 379,392 bits | 24-b RCP, HMP | p.8 |
| table size | 6,272 | bits | UNKNOWN / 2017 | MP: 7,808 bits | 16-b SIN, HMP | p.8 |
| table size | 166,528 | bits | UNKNOWN / 2017 | MP: 189,440 bits | 24-b SIN, HMP | p.8 |
| table size | 6,656 | bits | UNKNOWN / 2017 | MP: 7,968 bits | 16-b POW, HMP | p.8 |
| table size | 162,560 | bits | UNKNOWN / 2017 | MP: 207,872 bits | 24-b POW, HMP | p.8 |
| table size | 269,824 | bits | UNKNOWN / 2017 | HMP: 297,984 bits | 24-b RCP, HMP_TI | p.9 |
| table size | 152,448 | bits | UNKNOWN / 2017 | HMP: 166,528 bits | 24-b SIN, HMP_TI | p.9 |
| table size | 150,272 | bits | UNKNOWN / 2017 | HMP: 162,560 bits | 24-b POW, HMP_TI | p.9 |
| Area | 60,635 | um2 | TSMC 90nm / 2017 | MP: 74,022 um2 | 24-b SIN, HMP, m=5 | p.9 |
| Delay | 5.80 | ns | TSMC 90nm / 2017 | MP: 6.52 ns | 24-b SIN, HMP, m=5 | p.9 |
| Energy | 13.71 | uW/MHz | TSMC 90nm / 2017 | MP: 15.43 uW/MHz | 24-b SIN, HMP, m=5 | p.9 |
| Area | 55,395 | um2 | TSMC 90nm / 2017 | MP: 74,022 um2 | 24-b SIN, HMP_TI, m=5 | p.9 |
| Delay | 5.85 | ns | TSMC 90nm / 2017 | MP: 6.52 ns | 24-b SIN, HMP_TI, m=5 | p.9 |
| Energy | 14.48 | uW/MHz | TSMC 90nm / 2017 | MP: 15.43 uW/MHz | 24-b SIN, HMP_TI, m=5 | p.9 |
| Area | 3,931 | slices | Xilinx Virtex-II XC2V1000-fg456-5 / 2017 | MP: 4,954 slices | 24-b SIN, HMP, m=5 | p.9 |
| Delay | 25.2 | ns | Xilinx Virtex-II XC2V1000-fg456-5 / 2017 | MP: 43.0 ns | 24-b SIN, HMP, m=5 | p.9 |
| Area | 3,900 | slices | Xilinx Virtex-II XC2V1000-fg456-5 / 2017 | MP: 4,954 slices | 24-b SIN, HMP_TI, m=5 | p.9 |
| Delay | 25.0 | ns | Xilinx Virtex-II XC2V1000-fg456-5 / 2017 | MP: 43.0 ns | 24-b SIN, HMP_TI, m=5 | p.9 |
errors_and_checks: The target is faithful rounding with total error \(\varepsilon_{total}<1\ ulp\). The search exhaustively checks the combined approximation, quantization, and final-rounding error after table quantization. TI decomposition is lossless. Fault model/detection coverage/false-alarm behavior/alias rate are UNKNOWN. # pp.2,5-6,8
conditions: Table-addition evaluators target low-to-medium precision and avoid multipliers, while piecewise-polynomial methods are generally preferable at medium-to-high precision. Two hierarchy levels are reported as sufficient for the studied medium-precision cases. More tables trade smaller LUT storage for greater arithmetic cost; 24-bit SIN stops improving beyond five TOs. HMP requires only post-lookup addition, while iATA adds before and after lookup. # pp.1,4,6,8
evidence: §2 equations 14-25 and Figs. 3-7; §3 equations 26-32 and Figs. 8-11; §4 Figs. 12-13; Tables 1-10 and Figs. 14-15. # pp.3-9

## new_families
none

## space_gaps
* `multipartite` lacks a hierarchy-depth choice, although HMP recursively decomposes tables and evaluates two levels. # pp.4-5
* `multipartite` lacks a joint-error-optimization choice for selecting partitions and guard bits through exhaustive verification. # pp.5-6
* `multipartite` lacks a lossless initial-table decomposition choice for \(TI_{new}+TI_{diff}\). # pp.6,8

## open_questions
* The document states that HMP extends readily beyond two levels but does not report the useful maximum hierarchy depth. # p.4
* The synthesis tables do not report operating frequency, cell-library corner, voltage, FPGA tool version, or FPGA speed-grade conditions beyond XC2V1000-fg456-5. # p.9
