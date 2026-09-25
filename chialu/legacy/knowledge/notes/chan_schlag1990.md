---
handle: chan_schlag1990
citation: P. K. Chan, M. D. F. Schlag, "Analysis and Design of CMOS Manchester Adders with Variable Carry-Skip", IEEE Transactions on Computers, vol. 39, no. 8, pp. 983-992, 1990.
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [binary]
authority: incremental
pages_read: 86-95 / 10
---

## summary
The paper derives RC timing models for two dynamic-CMOS Manchester carry-skip circuits and shows that carry-skip delay grows linearly with block size while carry-ripple delay grows quadratically. The paper provides an O(n) heuristic and an O(n^3 log n) optimal algorithm for sizing variable blocks in one-level carry-skip adders.

## families
### manchester_carry_chain  (role: analyzes)
mechanism: An x-bit dynamic-CMOS block precharges its internal nodes and evaluates a pass-transistor carry chain. A bypass transistor conducts when every propagate signal in the block is true. One implementation restores the carry through an inverter; the second uses a NAND gate as both a buffer and the element combining the carry-bypass and carry signals. The NAND implementation gives faster carry-skip operation but a longer buffer delay. # p.87
choices:
  circuit_style: dynamic   # p.87
  variable_skip: true   # p.86
new_choices:
  buffer_combination: inverter | NAND_gate — selects the restoring/combining circuit at the block output   # p.87
slots: none
parameters: n-bit adder; m variable-size blocks; each analyzed block has x bits; buffers are inserted between blocks   # p.86
results: none
errors_and_checks: none
conditions: The RC model treats conducting transistors as linear resistors, node capacitances as grounded capacitors, and interconnect as lumped RC circuits. # p.87 The simplified derivation assumes equal transistor resistances r and equal node capacitances c. # p.87 The critical path is the serial pass-transistor carry chain, and bypass helps the worst case when every block propagate is true. # p.87
evidence: §1.2-§2.2; Figures 1-7; Equations (3)-(8), pp.86-89

### carry_skip  (role: extends)
mechanism: The adder partitions n bits into variable-size Manchester blocks. A worst-case carry is generated at the beginning of one block, skips intervening blocks, and is absorbed at the end of a later block. The normalized block model uses carry-ripple delay R(x)=x^2, carry-skip delay S(x)=a1x+a2, and restoring-buffer delay δ. A linear-time heuristic grows block sizes under critical-path constraints, while an exhaustive search over endpoint block-size pairs constructs an optimal configuration in O(n^3 log n) time. # pp.88-94
choices:
  block_sizing: algorithmically_optimized_variable [outside domain]   # pp.89-94
  skip_levels: 1   # p.86
  skip_gate: and_or_bypass   # p.87
new_choices:
  block_size_search: linear_time_heuristic | O(n^3 log n)_optimal_algorithm — selects near-optimal sizing or the proved optimal search   # pp.89-94
slots:
  block_adder: manchester_carry_chain [circuit_style=dynamic, variable_skip=true]   # pp.86-87
parameters: one skip level; n-bit operand; m blocks; variable block sizes z1…zm constrained by n=Σzi; heuristic complexity O(n); optimal-search complexity O(n^3 log n)   # pp.88-94
results:
| metric | value | unit | technology / device | baseline | condition | page |
| maximum delay | 81 | UNKNOWN | UNKNOWN; result year 1990 | none | 24-bit configuration (2,4,6,6,4,2), R(x)=x^2, S(x)=3x+2, δ=1; heuristic and optimal | p.90, p.94 |
| maximum delay | 218 | UNKNOWN | UNKNOWN; result year 1990 | none | 64-bit even-block heuristic configuration (2,4,6,7,8,5,5,8,7,6,4,2), R(x)=x^2, S(x)=3x+2, δ=1 | p.90 |
| maximum delay | 216 | UNKNOWN | UNKNOWN; result year 1990 | 218 for the even-block heuristic configuration | 64-bit odd-block heuristic configuration (2,4,6,7,8,10,8,7,6,4,2) | p.90 |
| maximum delay | 215 | UNKNOWN | UNKNOWN; result year 1990 | 216 for the reported odd-block heuristic configuration | 64-bit optimal configuration (2,4,6,8,10,10,9,7,5,3), R(x)=x^2, S(x)=3x+2, δ=1 | p.94 |
| maximum delay | 651 | UNKNOWN | UNKNOWN; result year 1990 | none | 200-bit optimal configuration (1,4,6,8,9,11,13,14,16,18,15,16,15,13,11,10,8,6,4,2) | p.94 |
| optimization CPU time | 326 | seconds | Sun 3/60; result year 1990 | none | computation of the reported 200-bit optimal configuration | p.94 |
errors_and_checks: none
conditions: The critical-path model assumes that skip circuitry is ready at time zero, block delays add, each block carry-out switches at most once, and an absorbed carry determines the block output within R(x). # p.88 The optimal algorithm requires monotonic non-decreasing R(x), linear S(x), non-decreasing R(x)-S(x), invertible R(x) and R(x)-S(x), R(x)-R(0)≥S(x+1)-S(x), and R′(x)≥S′(x) for x≥2. # p.90 The proof assumes R(x)=G(x), although the buffer delay δ can be incorporated by adding δ to R(x) and S(x). # p.90, p.94 The algorithm applies to the two analyzed CMOS Manchester circuits and the cited constant-skip model. # p.90
evidence: §2.2-§5; Equations (8)-(27); Examples 1-3; Figures 7-11, pp.88-94

## new_families
none

## space_gaps
* carry_skip.block_sizing lacks an explicit value for algorithmically optimized variable blocks whose sizes are produced by a heuristic or exact polynomial search rather than a named geometric profile. # pp.89-94
* manchester_carry_chain lacks a choice for the inverter-versus-NAND block-output implementation, which changes the carry-skip and buffer delays. # p.87

## open_questions
* The physical unit represented by the normalized maximum-delay values 81, 218, 216, 215, and 651 is not stated.
* The final asymptotic expression for one-level skip is degraded in the supplied text, so the merge pass must not infer its missing exponent or radical. # p.94
