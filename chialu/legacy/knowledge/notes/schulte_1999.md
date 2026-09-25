---
handle: schulte_1999
citation: Schulte, Stine, "Approximating Elementary Functions with Symmetric Bipartite Tables", IEEE Transactions on Computers, 1999
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_SFU, BINARY_ALU]
formats: [fixed_point, ieee_floating_point]
authority: landmark
pages_read: 842-847 / 6
---

## summary
The paper proposes the symmetric bipartite table method (SBTM), which approximates elementary functions with two parallel table lookups and exploits coefficient symmetry/leading zeros to reduce memory. A modified SBTM supplies faithfully rounded initial approximations for multiplicative divide and square-root algorithms.

## families
### bipartite  (role: extends)
mechanism: The input x is partitioned into x0, x1, and x2. Parallel tables produce a0(x0,x1) and a1(x0,x2) from a two-term Taylor approximation. The second table stores only half of its symmetric entries and omits its sign/leading extension bits. Conditional XOR rows complement its address and output when the most significant bit of x2 is one. The borrow-save result is converted by a carry-propagate adder or Booth encoded for a following multiplication. # pp.842-844
choices:
  symmetric: true   # pp.843-844
new_choices:
  coefficient_selection: closed_form_two_term_taylor — coefficients are selected from a centered two-term Taylor expansion   # p.843
  output_form: {twos_complement_cpa, booth_encoded} — selects conversion or direct use by a subsequent multiplication   # p.842
slots:
  none
parameters: two parallel tables; input partitions n0, n1, n2; table precisions p0, p1; output precision p; guard bits g; n=16, 20, and 24 evaluated; n=8 through 24 simulated   # pp.842-845
results:
| metric | value | unit | technology / device | baseline | condition | page |
| memory reduction of second table | 2 | factor | UNKNOWN; 1999 | nonsymmetric storage of a1(x0,x2) | symmetry-based complementation | p.843 |
| memory ratio | 2.47 to 5.19 | times less memory | UNKNOWN; 1999 | 3-block method [11] | 24-bit operands, l=28, 0.5 <= x < 1 | p.846 |
| memory | 704,512 | bits | UNKNOWN; 1999 | equivalent piecewise linear approximation | f(x)=1/x, n=24 | p.847 |
| carry-propagate adder width | 26 | bits | UNKNOWN; 1999 | equivalent piecewise linear approximation | f(x)=1/x, n=24 | p.847 |
| symmetry logic | 15 | exclusive-or gates | UNKNOWN; 1999 | no symmetry logic | f(x)=1/x, n=24 | p.847 |
errors_and_checks: The original SBTM is faithfully rounded, so the approximation differs from f(x) by at most one ulp when (9)/(10), or the sufficient g=2 constraint (11), is satisfied. The 24-bit comparison targets maximum approximation error less than 2^-25 and exhaustively tests all inputs over 0.5 <= x < 1. # pp.844,846
conditions: The method applies to differentiable functions and relies on range reduction when operands fall outside the analyzed ranges. The SBTM uses less memory than previous bipartite methods but adds conditional-complement logic. The SBTM uses more memory but less combinational logic than piecewise linear approximation, and it is expected to have more area but less delay for most technologies and operand sizes of 24 bits or less. # pp.843-847
evidence: Sections 2-4 and 6; Figs. 1-2; Tables 1-4 and 6; equations (1)-(11), (18)   # pp.842-847

### symmetric_bipartite  (role: proposes)
mechanism: The modified SBTM partitions x into x0, x1, x2, and x3. Only x0, x1, and x2 address the two symmetric tables, while x3 is replaced by its midpoint δ3. The modified coefficient formulas include δ3. Additional error bounds account for the omitted low input bits, allowing the tables to serve as initial approximations for reciprocal, square root, and reciprocal square root iterations. # pp.845-846
choices:
  guard_bits: 3   # p.846
  function: both   # p.846
new_choices:
  omitted_input_partition: midpoint_replacement — unused low bits x3 are replaced by δ3   # p.845
  direct_square_root_seed: true — the method also supplies square-root initial approximations beyond reciprocal/reciprocal-square-root seeds   # p.846
slots:
  none
parameters: input partitions x0, x1, x2, x3; only the three most significant partitions address tables; output fraction length j; k=ceil(j/3); g=3 when n1>0; Table 7 compares k=8 reciprocal tables   # pp.845-846
results:
| metric | value | unit | technology / device | baseline | condition | page |
| table-addressed input partitions | 3 | partitions | UNKNOWN; 1999 | all input bits used | modified SBTM omits x3 | p.845 |
| additional guard bits versus original SBTM | 1 | bit | UNKNOWN; 1999 | original SBTM | modified SBTM with omitted low input bits | p.846 |
errors_and_checks: Faithful rounding requires ε0+ε1+ε2+ε3 <= 2^-pf. For n1>0 and g=3, constraints (16) and (17) are sufficient. # p.846
conditions: The smaller tables introduce additional error because x3 is omitted. The method supports multiplicative reciprocal/divide, square-root, and reciprocal-square-root algorithms. The modified SBTM requires less memory than the faithful bipartite reciprocal tables of [12], while [12] produces borrow-save outputs that simplify Booth encoding. # pp.845-846
evidence: Section 5 and Section 6; Tables 5 and 7; equations (12)-(17)   # pp.845-846

### pwl  (role: compares)
mechanism: The piecewise linear method divides x into x0 and x1 and evaluates a0(x0)+a1(x0)x1 using a table lookup, multiplication, and addition. A multiplier-accumulator can combine the multiplication and addition to reduce delay. # p.847
choices:
new_choices:
  none
slots:
  none
parameters: For 2m bits of accuracy, the cited conventional design uses about 2^m by 3m bits of memory, an m-bit by m-bit multiplier, and a (2m+2)-bit adder. # p.847
results:
| metric | value | unit | technology / device | baseline | condition | page |
| memory | 73,728 | bits | UNKNOWN; 1999 | SBTM | equivalent approximation of 1/x, n=24 | p.847 |
| multiplier | 12-bit by 12-bit | multiplier | UNKNOWN; 1999 | SBTM | equivalent approximation of 1/x, n=24 | p.847 |
| adder width | 26 | bits | UNKNOWN; 1999 | SBTM | equivalent approximation of 1/x, n=24 | p.847 |
| memory | 51,200 | bits | UNKNOWN; 1999 | SBTM | operand-modification method [25], equivalent approximation | p.847 |
| multiplier | 25-bit by 26-bit | multiplier | UNKNOWN; 1999 | SBTM | operand-modification method [25], equivalent approximation | p.847 |
| operand-modification logic | 12 | inverters | UNKNOWN; 1999 | SBTM | method [25], equivalent approximation | p.847 |
errors_and_checks: The compared implementations provide 2m bits of accuracy; no separate measured error distribution is reported. # p.847
conditions: Piecewise linear approximation requires less memory than SBTM but requires a multiplier and comparable addition logic. # p.847
evidence: Section 6; equation (18)   # p.847

## new_families
none

## space_gaps
* The `bipartite` family lacks choices for coefficient generation, output conversion, input partition widths, and guard-bit precision exposed by the SBTM. # pp.842-844
* The `symmetric_bipartite` seed family lacks direct square-root support in its `function` domain. # p.846
* The `pwl` family lacks an evaluator slot for the multiplier-accumulator implementation described by the comparison. # p.847

## open_questions
* The exact dimensions/compression values in Tables 3-5 and 7 are not recoverable from the supplied table images and must not be guessed.
* The paper reports resource formulas/counts rather than fabricated area, delay, power, or technology-node measurements.
