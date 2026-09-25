---
handle: vazquez_2009
citation: Vazquez, Antelo, "A High-Performance Significand BCD Adder with IEEE 754-2008 Decimal Rounding", 19th IEEE Symposium on Computer Arithmetic (ARITH-19), 2009
actual_citation: same
status: ok
kind: paper
unit_classes: [other]
formats: [decimal64, decimal128, bcd]
authority: incremental
pages_read: 10 / 10
---

## summary
The paper merges sign-magnitude BCD addition/subtraction with IEEE 754-2008 decimal rounding by computing related BCD sums speculatively with one binary compound adder. Estimated Decimal64/Decimal128 implementations reduce delay and area relative to the Wang and Schulte injection-based design. # p.135, p.143–144

## families
### speculative_decimal_addition  (role: proposes)
mechanism: A binary 3:2 carry-save pre-correction produces `Ops`/`Opc`, conditionally adds decimal bias through `Gi`, and feeds a modified binary compound adder. The compound adder computes `S*` and `SI*=S*+2`; digitwise post-correction produces `S^H`, `SI^H`, and `¬S^H`. Direct rounding logic computes `inc1`/`inc2`, and a final selection chooses the correctly rounded sign-magnitude BCD result without another carry propagation or trailing-9 detection. # p.137–142
choices:
  speculation_target: both   # p.137–142
  recovery: dual_path_select   # p.139, p.142
  fused_ieee_rounding: true   # p.135, p.141–142
new_choices:
  operand_representation: sign_magnitude — selects `S^H`, `SI^H`, or `¬S^H` using `cmp=eop Cout` and the rounding increment   # p.137, p.140, p.142
  pre_correction_structure: binary_3_2_csa_with_conditional_bias — combines operand addition/complementing with `+6` and `+6Gi` corrections   # p.138–140
  rounding_implementation: direct_mode_conditions — implements a separate combinational rounding condition for each mode   # p.141–142
slots:
  carry_network: compound_flagged_prefix [outputs=sum_sum2 [outside domain], topology=kogge_stone]   # p.140, p.143
parameters: Decimal64 `p=16`; Decimal128 `p=34`; `p+1`-digit `U`; `p+3`-digit `L` including guard/round/sticky positions; five stages; `(4p-1)`-bit compound adder; 63-bit Kogge-Stone tree for the evaluated Decimal64 binary adder   # p.136–137, p.140, p.143
results:
| metric | value | unit | technology / device | baseline | condition | page |
| pre-correction delay | 6.5 | # FO4 | static CMOS model, node UNKNOWN, 2009 | none | Decimal64 | p.143 |
| pre-correction area | 1010 | NAND2 | static CMOS model, node UNKNOWN, 2009 | none | Decimal64 | p.143 |
| binary-adder delay | 10.5 | # FO4 | static CMOS model, node UNKNOWN, 2009 | none | Decimal64 | p.143 |
| binary-adder area | 1800 | NAND2 | static CMOS model, node UNKNOWN, 2009 | none | Decimal64 | p.143 |
| rounding delay | 2.5 | # FO4 | static CMOS model, node UNKNOWN, 2009 | none | Decimal64 | p.143 |
| rounding area | 200 | NAND2 | static CMOS model, node UNKNOWN, 2009 | none | Decimal64 | p.143 |
| selection delay | 6.6 | # FO4 | static CMOS model, node UNKNOWN, 2009 | none | Decimal64 | p.143 |
| selection area | 570 | NAND2 | static CMOS model, node UNKNOWN, 2009 | none | Decimal64 | p.143 |
| total delay | 26.1 | # FO4 | static CMOS model, node UNKNOWN, 2009 | Wang & Schulte [12]: 30.3 # FO4 | Decimal64 | p.143 |
| total area | 3580 | NAND2 | static CMOS model, node UNKNOWN, 2009 | Wang & Schulte [12]: 4490 NAND2 | Decimal64 | p.143 |
| delay ratio | 1.16 | Ratio | static CMOS model, node UNKNOWN, 2009 | Proposed: 1.00 | Wang & Schulte [12], Decimal64 | p.143 |
| area ratio | 1.25 | Ratio | static CMOS model, node UNKNOWN, 2009 | Proposed: 1.00 | Wang & Schulte [12], Decimal64 | p.143 |
| pre-correction delay | 6.5 | # FO4 | static CMOS model, node UNKNOWN, 2009 | none | Decimal128 | p.143 |
| pre-correction area | 2140 | NAND2 | static CMOS model, node UNKNOWN, 2009 | none | Decimal128 | p.143 |
| binary-adder delay | 12.7 | # FO4 | static CMOS model, node UNKNOWN, 2009 | none | Decimal128 | p.143 |
| binary-adder area | 4300 | NAND2 | static CMOS model, node UNKNOWN, 2009 | none | Decimal128 | p.143 |
| rounding delay | 2.5 | # FO4 | static CMOS model, node UNKNOWN, 2009 | none | Decimal128 | p.143 |
| rounding area | 200 | NAND2 | static CMOS model, node UNKNOWN, 2009 | none | Decimal128 | p.143 |
| selection delay | 7.4 | # FO4 | static CMOS model, node UNKNOWN, 2009 | none | Decimal128 | p.143 |
| selection area | 1160 | NAND2 | static CMOS model, node UNKNOWN, 2009 | none | Decimal128 | p.143 |
| total delay | 29.1 | # FO4 | static CMOS model, node UNKNOWN, 2009 | Wang & Schulte [12]: 32.2 # FO4 | Decimal128 | p.143 |
| total area | 7800 | NAND2 | static CMOS model, node UNKNOWN, 2009 | Wang & Schulte [12]: 9950 NAND2 | Decimal128 | p.143 |
| delay ratio | 1.11 | Ratio | static CMOS model, node UNKNOWN, 2009 | Proposed: 1.00 | Wang & Schulte [12], Decimal128 | p.143 |
| area ratio | 1.28 | Ratio | static CMOS model, node UNKNOWN, 2009 | Proposed: 1.00 | Wang & Schulte [12], Decimal128 | p.143 |
errors_and_checks: The architecture targets correctly rounded IEEE 754-2008 decimal results. It implements five IEEE modes plus round-to-nearest-down and away-from-zero; no fault-detection results are reported. # p.136, p.141–142
conditions: The figures are hand estimates from a static-CMOS logical-effort model without gate-sizing optimization. # p.142–143 The comparison covers only significand BCD addition/subtraction and rounding. # p.135, p.143 The rounding modification adds a small constant delay independent of digit count. # p.135
evidence: Algorithm and architecture in Figs. 2–8, rounding conditions in Table 1, estimates in Tables 2–3, pp.139–144.

### compound_flagged_prefix  (role: instantiates)
mechanism: The modified flagged prefix adder computes binary carries and carry OR-propagate groups in one `log2(4p-1)`-level prefix tree. Modified four-bit sum cells correct the exceptional decimal digit case outside the carry critical path. The secondary carry set produces `SI*=S*+2` because both compound-adder operands have zero least-significant bits. # p.140–141
choices:
  outputs: sum_sum2 [outside domain]   # p.139–141
  implementation: flag_row   # p.140–141
  topology: kogge_stone   # p.143
new_choices: none
slots: none
parameters: `(4p-1)` binary sum bits; `log2(4p-1)` prefix levels; evaluated as a 63-bit Kogge-Stone tree for Decimal64   # p.140, p.143
results: none
errors_and_checks: none
conditions: Any conventional binary compound adder may implement the mechanism, while the quantitative evaluation specifically uses Kogge-Stone. # p.140, p.143
evidence: Sections 4.2 and 5.1, Figs. 5 and 8, pp.140–143.

## new_families
none

## space_gaps
* `compound_flagged_prefix.outputs` lacks `sum_sum2`, which is the related-output pair computed by the proposed compound adder. # p.139–141
* `speculative_decimal_addition` lacks choices for sign-magnitude handling and the pre-correction/post-correction structure. # p.137–142
* `decimal_fp_addition.rounding` lacks the paper's direct combinational implementation of IEEE rounding conditions. # p.141–142

## open_questions
* The paper permits any conventional compound adder but evaluates a Kogge-Stone implementation, so the merge must not treat Kogge-Stone as mandatory. # p.140, p.143
* The paper reports modeled gate estimates rather than a technology node, synthesized netlist, or fabricated implementation. # p.142–143
