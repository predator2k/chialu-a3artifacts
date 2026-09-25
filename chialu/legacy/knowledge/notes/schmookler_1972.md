---
handle: schmookler_1972
citation: Schmookler, "Considerations in the Design of a High Speed Decimal Unit", 2nd IEEE Symposium on Computer Arithmetic (ARITH-2), 1972
actual_citation: same
status: ok
kind: paper
unit_classes: [other]
formats: [bcd, binary]
authority: survey
pages_read: 10 / 10
---

## summary
The paper surveys decimal arithmetic and proposes LSI logic arrays for simultaneous decimal multiplication and multioperand addition (pp.1, 4–6). An 8-variable ROM logic block implements each product or sum output function, which gives BCD and binary examples the same stated array counts (pp.5–6).

## families
### bcd_direct_addition  (role: analyzes)
mechanism: A shared binary/decimal adder performs binary addition followed by decimal correction. A dedicated decimal adder, exemplified by the Model 195, forms decimal sums directly and approaches binary-adder cost and performance (p.2).
choices:
  correction_placement: post_binary_addition_decimal_correction [outside domain]   # p.2
new_choices:
  implementation_context: {shared_binary_decimal_adder, dedicated_decimal_adder} — determines whether correction follows binary addition or sums are formed directly   # p.2
slots:
  digit_adder: UNKNOWN   # p.2
parameters: UNKNOWN   # p.2
results:
| metric | value | unit | technology / device | baseline | condition | page |
| storage and datapath increase | 20.4% | percent | UNKNOWN; year UNKNOWN | binary representation with maximum number 2^M-1 | BCD representation of the same numeric range | p.1 |
| decimal-correction delay | two additional | logic levels | current technology; year UNKNOWN | binary addition | shared binary/decimal adder using decimal correction | p.2 |
errors_and_checks: none
conditions: Decimal correction has insignificant incremental cost with the technology discussed, while a dedicated decimal adder can form sums more efficiently than a shared binary/decimal adder (p.2).
evidence: Introduction, pp.1–2.

### parallel_decimal_multiplication  (role: proposes)
mechanism: Each pair of 4-bit operands addresses separate 256-word logic arrays that directly generate product bits. For BCD operands, the output is a two-digit product; the direct lookup removes the need for doublers and quintuplers (pp.5–6).
choices:
  pp_generation: direct_8_variable_rom [outside domain]   # p.6
new_choices:
  none
slots:
  reduction_tree: none
  final_adder: none
parameters: 4-bit × 4-bit simultaneous multiplier; 256 one-bit words per assumed array; eight input variables   # pp.5–6
results:
| metric | value | unit | technology / device | baseline | condition | page |
| logic cost | no more than an AND gate and seven arrays | logic blocks | LSI ROM arrays; year 1972 | binary operands of the same word size | either binary or BCD 4-bit operands | p.6 |
| average multiplier throughput | 2.9 | bits per cycle | UNKNOWN; year 1955 | Richards BCD multiplier | stated as equivalent to 2.4 binary bits | p.1 |
errors_and_checks: none
conditions: Conventional simultaneous decimal multiplication needs costly doubling/quintupling and complement circuits, while direct ROM evaluation avoids those circuits; multioperand addition remains a separate obstacle (pp.4, 6).
evidence: “Some Possible Approaches,” pp.4–6.

### decimal_multioperand_addition  (role: proposes)
mechanism: Four 4-bit operands are added by handling column pairs in a first array stage and combining the partial results in a second array stage. The BCD version includes decimal correction in the second stage and replaces one array with the constraint-derived gate e1 = a1·b1·c1·d1 (p.6; Fig. 2).
choices:
  reduction_style: rom_array_two_stage [outside domain]   # p.6
  correction_placement: at_root   # p.6
new_choices:
  none
slots:
  reduction_tree: none
  root_adder: none
parameters: four 4-bit operands; two array stages; each array is assumed to contain 256 one-bit words   # pp.5–6
results:
| metric | value | unit | technology / device | baseline | condition | page |
| array count | twelve | arrays | LSI ROM arrays; year 1972 | twelve arrays for four binary operands | four BCD digits with decimal correction in the second stage | p.6 |
errors_and_checks: none
conditions: The equal array count depends on a BCD digit’s two high-order bits never both being ones, which permits one first-stage array to be replaced by an AND gate (p.6).
evidence: “Some Possible Approaches,” pp.5–6; Fig. 2.

### binary_decimal_conversion  (role: analyzes)
mechanism: Custom iterative arrays perform binary/BCD conversion, which permits decimal multiplication or division by converting operands to binary, executing the operation, and converting the result back to decimal (p.5).
choices:
  direction: both   # p.5
new_choices:
  none
slots:
  none
parameters: UNKNOWN   # p.5
results: none
errors_and_checks: none
conditions: The paper calls conversion through custom arrays reasonable but reports no conversion latency, area, or array dimensions (p.5).
evidence: Array classification and custom-array discussion, p.5.

## new_families
none

## space_gaps
* `parallel_decimal_multiplication.pp_generation` lacks a `direct_8_variable_rom` value for simultaneous digit-product truth tables (p.6).
* `decimal_multioperand_addition.reduction_style` lacks a `rom_array_two_stage` value for batch addition through cascaded universal logic arrays (p.6).
* `parallel_decimal_multiplication.reduction_tree` cannot name `decimal_multioperand_addition`, although the paper treats batch addition as the unresolved companion mechanism for simultaneous decimal multiples (pp.4–6).
* `binary_decimal_conversion.structure` lacks the cited custom iterative-array implementation style (p.5).

## open_questions
* The paper does not state whether the proposed ROM multiplier and batch adder were fabricated or only estimated.
* The paper identifies 4-bit BCD operands but does not name the exact BCD encoding.
* The paper does not specify a reduction structure or final adder for a complete multi-digit ROM-array multiplier.
