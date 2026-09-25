---
handle: brent_kung1982
citation: R. P. Brent, H. T. Kung, "A Regular Layout for Parallel Adders", IEEE Transactions on Computers, vol. C-31, no. 3, pp. 260-264, 1982.
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [binary_twos_complement]
authority: landmark
pages_read: 260-264 / 5
---

## summary
The paper proposes a regular parallel-prefix layout that adds n-bit binary numbers in O(log n) time and O(n) area when a width-w network processes operand segments as a pipeline (pp.260-263). The full-width carry network computes all carries in O(log n) time and O(n log n) area (p.262).

## families
### parallel_prefix  (role: proposes)
mechanism: Carry generation is reformulated as a prefix computation over associative pairs `(g,p)`, using `(g,p)o(g',p') = (g V (p A g'), p A p')` (pp.261-262). A binary reduction tree computes group terms, and an inverted tree distributes the terms needed for every carry (pp.262-263). White processors transmit pairs, while black processors implement the prefix operator with AND/OR logic (p.262). A width-w variant pipelines least-significant-first operand segments and uses a superimposed tree plus an accumulator to apply preceding-segment carry state (pp.262-263).
choices:
  topology: brent_kung   # pp.262-263
  valency: 2   # p.262
  log2_sparsity: 0   # pp.262-263
  fanout_cap: 2   # pp.261-262
  node_style: and_or   # pp.261-262
new_choices:
  input_width_w: Int[1..n:1] — number of bits accepted from each operand at one time   # pp.262-263
  segment_schedule: least_significant_first — order in which width-w operand segments enter the pipeline   # p.262
slots:
  none
parameters: n-bit binary operands; full-width network w=n; pipelined network 1≤w≤n; illustrated networks use n=16 and w=16; combinational II is not reported   # pp.262-263
results:
| metric | value | unit | technology / device | baseline | condition | page |
| time complexity | O(log n) | time | abstract VLSI model; 1982 | none | full-width carry network, n>2 | p.262 |
| area complexity | O(n log n) | area | abstract VLSI model; 1982 | none | full-width carry network, n>2 | p.262 |
| time complexity | O(n/w + log w) | time | abstract VLSI model; 1982 | serial carry chain at w=1 | width-w pipelined network | p.263 |
| area complexity | O(w log w + 1) | area | abstract VLSI model; 1982 | serial carry chain at w=1 | width-w pipelined network | p.263 |
| area complexity | O(n) | area | abstract VLSI model; 1982 | none | w=n/log n | pp.261,263 |
| time complexity | O(log n) | time | abstract VLSI model; 1982 | none | w=n/log n | pp.261,263 |
| area-time product | O(n log w + w log^2 w + 1) | area-time | abstract VLSI model; 1982 | none | width-w pipelined network | p.263 |
| computation time, n=8 | 12 | time units | abstract gate-time model; 1982 | serial: 15 time units | AND/OR/XOR each take unit time | p.263 |
| computation time, n=16 | 16 | time units | abstract gate-time model; 1982 | serial: 31 time units | AND/OR/XOR each take unit time | p.263 |
| computation time, n=32 | 20 | time units | abstract gate-time model; 1982 | serial: 63 time units | AND/OR/XOR each take unit time | p.263 |
| computation time, n=64 | 24 | time units | abstract gate-time model; 1982 | serial: 127 time units | AND/OR/XOR each take unit time | p.263 |
| estimated speed | about 4 times faster | relative speed | NMOS; year UNKNOWN | 32-bit straightforward serial adder | Guibas/Vuillemin 32-bit chip implementation | p.263 |
errors_and_checks: none
conditions: The model assumes constant-time two-input gates, constant-area gates, fanout to two signals in constant time, minimum-width wires, and at most two wires crossing at a point (p.261). The model treats propagation along a wire of any length as constant time and excludes driver area beyond a fixed percentage of wire area (p.261). The computation occupies a convex planar region with inputs/outputs on its boundary, and area is the cost measure (p.261). The width-w explanation assumes n is divisible by w and processes segments from least significant to most significant (p.262). The design targets binary two's-complement arithmetic; the paper states that one's-complement and sign-magnitude arithmetic require minor modifications (p.263). The design is described as especially suitable for a pipelined adder (p.261).
evidence: Sections III-VII; Lemmas 1-2; Theorems 3-4; Corollary 1; Figs. 3-7; Table I (pp.261-264).

## new_families
none

## space_gaps
* `parallel_prefix` lacks an operand-width/segment-pipelining choice for processing n-bit operands through a width-w prefix network, although the paper derives area/time as functions of w (pp.262-263).
* `parallel_prefix` lacks a layout-regularity choice, although regular wiring and replicated white/black processors are central design constraints (pp.260-263).

## open_questions
* The NMOS implementation's process node, physical area, absolute delay, and result year are not reported; only an estimated relative speed is given (p.263).
* The constants hidden by the asymptotic area/time bounds are not reported (pp.262-263).
* The paper does not quantify initiation interval or pipeline-register overhead for the width-w scheme (pp.262-263).
