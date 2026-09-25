---
handle: vangal_2002
citation: S. Vangal, et al., "5-GHz 32-bit Integer Execution Core in 130-nm Dual-VT CMOS", IEEE Journal of Solid-State Circuits, vol. 37, no. 11, pp. 1421-1432, 2002.
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [int32]
authority: landmark
pages_read: 1421-1432 / 12
---

## summary
The document demonstrates a 32-bit single-ended dynamic Han-Carlson ALU within a measured 5-GHz integer execution core in 130-nm dual-VT CMOS. The ALU uses complementary signal generators, sparse even-carry propagation, and stack-node preconditioning to reduce wiring, leakage, and delay relative to a differential domino Kogge-Stone reference. The ALU and scheduler loop reaches 10 GHz at 1.7 V and 25 C.

## families
### parallel_prefix  (role: extends)
mechanism: A radix-2 Han-Carlson tree forms P/G signals and then performs five carry-merge stages. The tree skips odd carries and propagates 16 even carries through alternate-bit interstage connections. A final carry-merge operation for missing odd carries is folded into complementary signal generators and the sum XORs. Dynamic and static domino stages perform carry merging, while precondition transistors set intermediate stack nodes during precharge. Split and transposed evaluation stacks limit charge-sharing noise. # p.1424-1425
choices:
  topology: han_carlson   # p.1424
  valency: 2   # p.1424
  node_style: dynamic_domino   # p.1424-1425
new_choices:
  signal_rail: single_ended_csg — single-rail carries feed complementary signal generators that produce dual-rail sum/sum# outputs   # p.1424-1425
  stack_node_preconditioning: enabled — intermediate dynamic/static stack nodes are predischarged/precharged during precharge   # p.1425
slots:
  none
parameters: 32-bit operands; one P/G stage; five carry-merge stages; 16 even carries generated; one missing-odd-carry stage folded into the CSG/output XOR; single-cycle add/subtract/accumulate; 336 µm × 84 µm ALU layout   # p.1424-1425
results:
| metric | value | unit | technology / device | baseline | condition | page |
| delay reduction | 10% | delay reduction | 130-nm six-metal dual-VT CMOS; 2002 | reference design in [5] | CSG odd-carry merge folded into output sum XORs | p.1424 |
| carry-tree delay improvement | 10% | delay improvement | 130-nm six-metal dual-VT CMOS; 2002 | without stack-node preconditioning | preconditioned intermediate stack nodes | p.1425 |
| carry-merge gate count | 50% fewer | carry-merge gates | 130-nm six-metal dual-VT CMOS; 2002 | differential domino Kogge-Stone implementation | single-ended Han-Carlson ALU | p.1425 |
| active leakage energy | 40% less | active leakage energy | 130-nm six-metal dual-VT CMOS; 2002 | differential domino Kogge-Stone implementation | single-ended Han-Carlson ALU | p.1425 |
| interstage routing complexity | 50% reduction | routing complexity | 130-nm six-metal dual-VT CMOS; 2002 | Kogge-Stone | alternate bits propagated between carry-merge stages | p.1425 |
| ALU layout | 336 µm × 84 µm | area dimensions | 130-nm six-metal dual-VT CMOS; 2002 | none | compact single-ended layout | p.1425 |
| worst-case interstage wire length | 168 µm | wire length | 130-nm six-metal dual-VT CMOS; 2002 | none | carry-merge tree | p.1425 |
| maximum ALU frequency | 6.8 GHz | GHz | 130-nm six-metal dual-VT CMOS; 2002 | none | 1.25 V, zero body bias, room temperature | p.1428 |
| supply reduction for 5-GHz ALU operation | 9.5% | supply-voltage reduction | 130-nm six-metal dual-VT CMOS; 2002 | 1.05 V with zero body bias | 0.95 V with 450-mV FBB | p.1428 |
| ALU power | 95 mW | mW | 130-nm six-metal dual-VT CMOS; 2002 | none | 5 GHz, 1.05 V, 25 C | p.1429 |
| ALU and scheduler loop frequency | 10 GHz | GHz | 130-nm six-metal dual-VT CMOS; 2002 | none | 1.7 V, 25 C | p.1429 |
errors_and_checks: No arithmetic-error contract or concurrent fault checker is reported; dynamic-node shielding and stack transposition address capacitive-coupling and charge-sharing noise rather than arithmetic error detection.   # p.1424-1425
conditions: The ALU supports single-cycle add/subtract/accumulate with results available to the following cycle.   # p.1424
The CSG does not remove an ALU gate stage because the true and complementary reference paths are balanced, so its reported delay benefit primarily comes from reduced carry-tree wire length.   # p.1424
The worst-case domino pull-down stack is two devices wide, and all dynamic nodes are shielded to satisfy noise/leakage constraints.   # p.1424
Stack-node preconditioning uses split/transposed evaluation stacks to limit its charge-sharing noise.   # p.1425
The 10-GHz result applies to the coupled ALU/scheduler loop rather than an isolated ALU measurement.   # p.1429
evidence: Section IV and Figs. 8-11, p.1424-1425; Section X and Figs. 26, 28, and 29, p.1428-1429.

## new_families
none

## space_gaps
* `parallel_prefix` lacks a signal-rail/CSG choice for the measured single-ended carry tree with dual-rail sum outputs.   # p.1424-1425
* `parallel_prefix` lacks a stack-node-preconditioning choice for dynamic carry-merge stages.   # p.1425

## open_questions
* The abstract reports 95 mW at 5 GHz and 0.95 V, while Section X reports 95 mW at 5 GHz, 1.05 V, and 25 C; the document does not reconcile the supply-voltage discrepancy.   # p.1421, p.1429
