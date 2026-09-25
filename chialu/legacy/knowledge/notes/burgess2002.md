---
handle: burgess2002
citation: N. Burgess, "The Flagged Prefix Adder and its Applications in Integer Arithmetic", Journal of VLSI Signal Processing, vol. 31, no. 3, pp. 263-271, 2002.
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [binary_integer]
authority: landmark
pages_read: 263-271 / 9 pages
---

## summary
The paper proposes a flagged prefix adder that modifies a parallel prefix tree to compute A+B/A+B+1 or A−B/B−A with one carry tree. The paper applies the structure to modulo 2^w−1 addition, absolute difference, and sign-magnitude addition. Transistor-count comparisons cover Ladner-Fischer and Kogge-Stone trees at 16 and 64 bits.

## families
### compound_flagged_prefix  (role: proposes)
mechanism: Output grey cells in a parallel prefix tree become black cells so that each position returns both G⁰ᵢ₋₁ and ¬K⁰ᵢ₋₁. The late carry is lc(i)=G⁰ᵢ₋₁∨¬K⁰ᵢ₋₁∧inc. Output logic controlled by inc/cmp selectively inverts sum bits, which produces late increment and late complement operations from one tree. The full output cell uses two XOR gates and an AND-OR combination. Dedicated increment-only and absolute-difference cells simplify the controls. (pp.265-266)
choices:
  outputs: sum_sum1_summinus1   # p.265
  implementation: flag_row   # pp.265-266
  late_carry_in: true   # pp.265-266
new_choices:
  output_logic_scope: {full, late_increment_only, absolute_difference_only} — selects the full inc/cmp cell or one of the two application-specific cells   # p.266
slots:
  none
parameters: w-bit operands; evaluated at 16-bit and 64-bit; Ladner-Fischer and Kogge-Stone prefix trees   # pp.269-270
results:
| metric | value | unit | technology / device | baseline | condition | page |
| transistor count | 928 | FET’s | UNKNOWN; 2002 | dual adders: 1,288 FET’s | 16-bit Ladner-Fischer, full flagged prefix adder | p.270 |
| transistor count | 4,352 | FET’s | UNKNOWN; 2002 | dual adders: 6,408 FET’s | 64-bit Ladner-Fischer, full flagged prefix adder | p.270 |
| transistor count | 1,088 | FET’s | UNKNOWN; 2002 | dual adders: 1,608 FET’s | 16-bit Kogge-Stone, full flagged prefix adder | p.270 |
| transistor count | 5,632 | FET’s | UNKNOWN; 2002 | dual adders: 8,968 FET’s | 64-bit Kogge-Stone, full flagged prefix adder | p.270 |
| transistor count | 800 | FET’s | UNKNOWN; 2002 | dual adders: 1,288 FET’s; conditional-sum adder: 1,024 FET’s | 16-bit Ladner-Fischer, late-increment-only cell | p.270 |
| transistor count | 3,840 | FET’s | UNKNOWN; 2002 | dual adders: 6,408 FET’s; conditional-sum adder: 5,120 FET’s | 64-bit Ladner-Fischer, late-increment-only cell | p.270 |
| transistor count | 960 | FET’s | UNKNOWN; 2002 | dual adders: 1,608 FET’s | 16-bit Kogge-Stone, late-increment-only cell | p.270 |
| transistor count | 5,120 | FET’s | UNKNOWN; 2002 | dual adders: 8,968 FET’s | 64-bit Kogge-Stone, late-increment-only cell | p.270 |
| relative transistor count | 63% to 72% | percent of baseline | UNKNOWN; 2002 | dual-adder approach | full flagged prefix adder; range depends on wordlength/topology | p.270 |
| relative transistor count | 57% to 62% | percent of baseline | UNKNOWN; 2002 | dual-adder approach | dedicated late-increment circuit | p.270 |
| relative transistor count | 75% to 78% | percent of baseline | UNKNOWN; 2002 | conditional-sum adder | Ladner-Fischer late-increment circuit | p.270 |
| added delay | one XOR delay and one buffer delay | delay | UNKNOWN; 2002 | standard prefix adder with the same topology | inc/cmp available before or with the tree outputs | p.266 |
errors_and_checks: none
conditions: The flagged prefix modification works on any parallel prefix carry tree. (p.265) The inc/cmp controls require buffering because each control drives a large fan-out load. (p.266) The flagged design has the same stated speed as a dual adder because the dual adder also buffers broadcast multiplexer controls. (p.266) The full output-cell implementation treats inc=cmp=1 as a don’t-care condition. (p.265) The simplified cells apply when only late increment or only absolute difference is required. (p.266)
evidence: §2, Figs. 3-7 and Table 1, pp.265-267; §4, Eqs. 9-18 and Table 2, pp.268-270

### end_around_carry  (role: instantiates)
mechanism: For modulo 2^w−1 addition, the most-significant carry requests a late increment of the lower w sum bits. The all-ones case S=2^w−1 must also reduce to zero. The flagged implementation covers both cases by connecting ¬K⁰_w−1 directly to inc, using the don’t-care relation between ¬K⁰_w−1 and G⁰_w−1. (p.267)
choices:
  modulus: mod_2n_minus_1   # p.267
  recirculation: late_increment_feedback [outside domain]   # p.267
new_choices:
  none
slots:
  none
parameters: w-bit operands; modulus M=2^w−1   # p.267
results:
| metric | value | unit | technology / device | baseline | condition | page |
errors_and_checks: none
conditions: A carry-out causes the lower w bits to be incremented because the 2^w carry has residue +1. (p.267) The case S=M produces all-one sum bits and must produce zero after reduction. (p.267)
evidence: §3.1 and Eq. 6, p.267

## new_families
none

## space_gaps
* end_around_carry.recirculation lacks a value for the flagged tree’s direct ¬K⁰_w−1-to-inc late-increment feedback mechanism. (p.267)
* compound_flagged_prefix lacks a choice for full versus increment-only versus absolute-difference-only output logic. (pp.265-266)

## open_questions
* The paper states that the modification applies to any parallel prefix tree, but transistor counts are given only for Ladner-Fischer and Kogge-Stone topologies.
