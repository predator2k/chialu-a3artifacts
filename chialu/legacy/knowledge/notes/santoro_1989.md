---
handle: santoro_1989
citation: M. R. Santoro, G. Bewick, M. A. Horowitz, "Rounding Algorithms for IEEE Multipliers", 9th IEEE Symposium on Computer Arithmetic, 1989
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [IEEE_754_binary]
authority: incremental
pages_read: 176-183 / 8
---

## summary
The paper presents three technology-independent algorithms for rounding normalized binary floating-point products. Algorithms 2 and 3 compute alternative rounded sums in parallel, while Algorithm 3 removes the lower-order carry from the critical path. Three exact sticky-bit methods complete IEEE round-to-nearest/even handling.

## families
### sig_mul_then_round  (role: instantiates)
mechanism: Algorithm 1 reduces two normalized n-bit mantissas to a 2n-bit carry-save product, performs carry-propagate addition, adds an overflow-dependent rounding constant, truncates the low bits, and shifts right with exponent adjustment when normalization requires it. The unused low n-2 sum bits affect the result only through their carry into the retained n+2 bits. # p.176-177
choices:
  none
new_choices:
  none
slots:
  sig_mul: UNKNOWN   # p.176
  round: increment_adder   # p.176-177
parameters: normalized n-bit mantissas; 2n-bit carry-save product; n+2-bit retained carry-propagate adder with input carry; two serial carry-propagate additions   # p.176-177
results:
| metric | value | unit | technology / device | baseline | condition | page |
| carry-propagate adder width | n+2 | bit | technology independent (1989) | 2n-bit carry-propagate adder | auxiliary hardware supplies the carry from the low n-2 bits | p.177 |
errors_and_checks: Algorithm 1 initially produces round-to-nearest/up; IEEE round-to-nearest/even requires the later L/R/sticky tie correction. # p.176, p.180-181
conditions: Algorithm 1 is suitable for software simulation or moderate-performance hardware, but its two serial carry-propagate additions limit high-performance use. # p.177, p.182
evidence: §3; Figure 1; conclusion, p.176-177, p.182

### round_fused_in_reduction  (role: proposes)
mechanism: Algorithms 2A/2B combine Cin, Rin, Rv, Rcarry, and Rsum with a half-adder/CSA row and a compound carry-propagate adder that forms A+B and A+B+1 concurrently. Algorithm 2A injects Rin into an available multiplier or accumulator slot. Algorithm 2B creates slots at the L/R positions with carry-save adders. Algorithm 3 classifies the possible R-to-L carries before Cin and Rv are known, starts the compound addition early, and selects the final output after Cin and overflow become available. # p.177-180
choices:
  none
new_choices:
  rounding_algorithm: {algorithm_2a, algorithm_2b, algorithm_3} — selects the placement and timing of Rin/Cin and the output-selection logic   # p.178-180
slots:
  sig_mul: UNKNOWN   # p.176, p.178-180
parameters: five R-position inputs: Rv, Rin, Cin, Rcarry, Rsum; two outputs: A+B and A+B+1; possible R-to-L carry values 0/1/2   # p.177-180
results:
| metric | value | unit | technology / device | baseline | condition | page |
| carry-propagate addition scheduling | parallel | scheme | technology independent (1989) | Algorithm 1: two additions in series | Algorithms 2 and 3 | p.182 |
| lower-order carry critical-path dependence | eliminated | dependency | technology independent (1989) | Algorithm 2 waits for Cin before preliminary addition | Algorithm 3 | p.179-180 |
errors_and_checks: Any algorithm’s round-to-nearest/up output becomes IEEE round-to-nearest/even by using L/R/sticky and forcing L to 0 in the tie case. # p.180-181
conditions: Algorithm 2A suits conventional array/full-tree multipliers with a slot for Rin. # p.178, p.182; Algorithm 2B suits designs without that slot. # p.178, p.182; Algorithm 3 suits iterative multipliers or designs where Cin is on the critical path. # p.179, p.182
evidence: §4-6; Figures 2-5; Tables 1-3; conclusion, p.177-182

### conditional_sum  (role: instantiates)
mechanism: The compound adder forms A+B and A+B+1 concurrently and selects one result after an overflow/carry-derived control becomes known. Only the carry chain must be duplicated, so the compound structure uses less hardware than two independent carry-propagate adders. # p.178
choices:
  selection_radix: 2   # p.178
new_choices:
  select_signal: overflow_or_carry_logic — the selector need not be an input carry; Algorithms 2/3 derive it from overflow and R-position carry information   # p.178, p.180
slots:
  none
parameters: two candidate outputs, A+B and A+B+1   # p.178
results: none
errors_and_checks: none
conditions: The R-position logic must reduce the possible correction to two adjacent candidates because the compound adder does not compute A+B+2 directly. # p.179
evidence: §4-5; Tables 1-2, p.178-180

## new_families
### sticky_bit_generation  (domain: fp: floating-point multipliers, closest: round_fused_in_reduction, why_not: sticky generation is a separate exact reduction mechanism rather than a rounding-position choice)
mechanism: The first method performs full carry-propagate addition and ORs all product bits below R. The second counts trailing zeros in both binary operands and sums the counts while multiplication proceeds. The third directly ORs carry-save bits below R; its proof depends on the first nonzero carry/sum pair containing exactly one 1 when every partial product is positive. # p.181-182
choices:
  source: {post_cpa_or, input_trailing_zero_count, carry_save_or}   # p.181-182
  booth_compatible: Bool   # p.182
results: none
evidence: §7.1-7.3; Figure 6, p.181-182

## space_gaps
* `round_fused_in_reduction` lacks a choice for `algorithm_2a`/`algorithm_2b`/`algorithm_3`, which determine rounding-bit injection and Cin timing. # p.178-180
* Floating-point multiplier families lack a sticky-bit component slot for `post_cpa_or`/`input_trailing_zero_count`/`carry_save_or`. # p.181-182
* `conditional_sum` lacks a choice for selection by a non-carry overflow/correction signal. # p.178, p.180

## open_questions
* The paper leaves operand precision, technology, area, delay, pipeline depth, and implementation frequency unspecified. # p.176-183
* The paper permits array/tree/iterative multipliers but does not fix one multiplier family for any algorithm. # p.176, p.178-179
* The direct carry-save sticky method excludes Booth encoding, but the paper does not characterize other negative-partial-product encodings. # p.182
