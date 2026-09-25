---
handle: quach_2004
citation: N. T. Quach, N. Takagi, M. J. Flynn, "Systematic IEEE Rounding Method for High-Speed Floating-Point Multipliers", IEEE Transactions on VLSI Systems, 2004
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [fp32, fp64]
authority: incremental
pages_read: p.511-p.521 / 11 pages
---

## summary
The paper proposes a three-step method—rounding-table construction, prediction, and rounding-digits selection—for integrating all IEEE rounding modes into a high-speed binary floating-point multiplier (p.511-p.512). An improved compound-adder implementation combines rounding and the final 1-bit normalization shift into one selection step and removes roughly one full-length shifter of datapath delay relative to the compared implementation (p.516, p.519).

## families
### round_fused_in_reduction  (role: proposes)
mechanism: Partial products are reduced to sum/carry terms, after which multiple significand values are computed during the carry-propagate addition. A rounding table enumerates the values required for no-shift/right-shift cases; prediction reduces the computed set, and rounding-digits selection minimizes selector logic. A final 4-1 mux selects an unshifted or 1-bit-shifted value, so rounding and final normalization form one selection operation (p.513-p.519).
choices:
new_choices:
  rounding_construction: rounding_table_prediction_rds — the method constructs a generic table, selects a prediction scheme, and performs rounding-digits selection (p.511, p.513-p.516)
  implementation_variant: {simple, improved} — the improved variant changes the least-significant-bit logic and supports every IEEE rounding mode (p.515-p.517)
  prediction_policy: RN optional; RI required; RZ unavailable — prediction availability depends on the rounding mode in the improved implementation (p.519)
slots:
  sig_mul: UNKNOWN   # p.511
  exp: UNKNOWN   # p.512
  subnormal: UNKNOWN   # p.512
parameters: binary significand precision p=24 for single precision and p=53 for double precision; four IEEE modes mapped to RN/RI/RZ hardware cases; no-shift and 1-bit-right-shift normalization columns; simple and improved implementations; final 4-1 selection mux (p.511-p.513, p.515-p.519)
results:
| metric | value | unit | technology / device | baseline | condition | page |
| rounding/fix-up logic depth | at most 3 | gate delays | UNKNOWN (2004) | none | AND/OR/NAND/NOR/inverter fan-in at most three; 4-1 muxes available | p.519 |
| rounding-mode mapping overhead | 1 | 4-1 mux | UNKNOWN (2004) | none | selects among the mode-specific rounding/fix-up equations | p.519 |
| half-adder-row reduction | 1 fewer | row of half adders | UNKNOWN (2004) | implementation in [10] | improved implementation | p.519 |
| shifter reduction | 1 fewer | full-length shifter | UNKNOWN (2004) | implementation in [10] | improved implementation | p.519 |
| datapath delay saving | roughly 1 | full-length shifter | UNKNOWN (2004) | implementation in [10] | full-adder/compound-adder/4-1-mux path replaces two half adders/compound adder/2-1 mux/post-round shift | p.519 |
errors_and_checks: The output contract is a final correctly rounded significand for RN/RP/RM/RZ; the rounding equations were fully verified with a gate-level model. The paper reports no numeric ulp/error-rate result or fault-detection coverage (p.511-p.512, p.519).
conditions: The method is restricted here to IEEE rounding for multipliers using conventional binary representation, and the paper treats only computation of the final correctly rounded significand (p.512). Multiplication permits a 1-bit normalization right shift, which creates the two rounding-table columns and the selectable shifted values (p.513). The improved implementation supports RI, while the simple implementation does not; both are described as roughly equal in hardware consumption and critical-path timing apart from their least-significant-bit logic (p.516-p.517).
evidence: §I-§VII, Tables I-V, VII-XV, Figs. 2-3, and Appendix (p.511-p.521)

### compound_flagged_prefix  (role: extends)
mechanism: A compound adder computes the unincremented and incremented significand values in parallel by duplicating carry-lookahead networks rather than complete adders. The improved circuit replaces the least-significant half adder with a full adder, shortens the compound adder by one bit, and derives the additional R+2 value from R/R+1 through selection and least-significant-bit control without further carry propagation (p.515-p.517).
choices:
  outputs: sum_sum1   # p.515-p.516
  implementation: dual_carry_tree   # p.515
new_choices:
  third_value_generation: lsb_select_without_carry_propagation — R+2 is generated from the two direct compound-adder results by selecting a result and setting its least-significant bit (p.516-p.517)
slots:
  none
parameters: simple compound adder computes multiple significand values with an inserted prediction bit; improved compound adder is one bit shorter and uses a full adder plus a 3-1 least-significant-bit mux; final result uses a 4-1 mux (p.515-p.517)
results: none
errors_and_checks: The compound-adder rounding equations were included in the gate-level functional verification; no independent adder error metric is reported (p.519).
conditions: The optimization assumes high-speed adders whose carry-lookahead networks can be duplicated for simultaneous significand-value computation (p.515). The improved compound adder admits eight RN prediction schemes, supplies an RI solution, and needs no RZ prediction (p.517-p.519).
evidence: §III-A-§III-E, Tables III-VII, Figs. 2-3, §VI, and Appendix (p.515-p.521)

## new_families
none

## space_gaps
* `round_fused_in_reduction` lacks choices for rounding-table construction, prediction policy, rounding-digits selection, and simple/improved least-significant-bit organization (p.511, p.515-p.519).
* `compound_flagged_prefix.outputs` does not express the implemented R/R+1 direct outputs plus the selection-derived R+2 value (p.516-p.517).

## open_questions
* The paper does not identify the partial-product generation/reduction family used before the compound adder (p.511).
* The paper does not specify a named prefix topology, technology node, device, area, power, or absolute delay for either implementation (p.515-p.519).
* Exponent handling is described only generally, while subnormal handling is not settled by the significand-focused implementation (p.511-p.512).
