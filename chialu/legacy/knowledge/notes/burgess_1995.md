---
handle: burgess_1995
citation: Burgess, Williams, "Choices of Operand Truncation in the SRT Division Algorithm", IEEE Transactions on Computers, 1995
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [binary]
authority: incremental
pages_read: 6 / 6
---

## summary
The paper derives necessary and sufficient truncation conditions for SRT quotient-digit selection and tabulates valid remainder/divisor precisions for radices 2, 4, 8, and 16. The analysis finds identical truncation requirements for carry-save and borrow-save partial remainders and identifies asymmetric remainder truncation choices that reduce selection-logic inputs or assimilation-adder length. # pp.933-937

## families
### srt_radix2  (role: analyzes)
mechanism: Each iteration selects a redundant quotient digit from truncated approximations of the divisor and partial remainder, then applies \(R_{i+1}=rR_i-Dq_i\). Robertson-diagram bounds include the uncertainty contributed by unexamined remainder digits. Carry-save and borrow-save representations require the same truncation, although carry-save selection bounds are biased. # pp.934-936
choices:
  residual_form: {carry_save, signed_digit [outside domain]}   # pp.934-936
new_choices:
  quotient_digit_set: {-1, 0, 1} — redundant digits available at radix 2   # p.934
  remainder_truncation: t=3, f=0 — examined integer/fractional remainder digits   # p.937
  divisor_truncation_bits: 0 — divisor bits examined by quotient selection   # p.937
  qds_input_architecture: {redundant_inputs, assimilated_remainder} — the selection table may consume redundant remainder portions directly or a short-CPA result   # p.936
slots:
  digit_select: qds_table   # pp.934-936
parameters: radix r=2; qmax=1; t=3; f=0; b=0; selection inputs w=6   # p.937
results:
| metric | value | unit | technology / device | baseline | condition | page |
| quotient-selection truncation (t,f,b,w) | (3,0,0,6) | digits/bits/inputs | UNKNOWN / 1995 | none | r=2, qmax=1, p=n | p.937 |
| fractional remainder digits examined | 0 | bits | UNKNOWN / 1995 | higher-radix SRT | r=2 only | p.936 |
| divisor bits examined | 0 | bits | UNKNOWN / 1995 | higher-radix SRT | r=2 only | p.936 |
errors_and_checks: The tabulated combination satisfies the necessary and sufficient quotient-selection conditions for every quotient digit and divisor subrange. # p.936
conditions: Radix 2 has simpler quotient-selection logic because no divisor bits or fractional partial-remainder bits need inspection. # p.936
evidence: Section II; (2)-(4); Sections III-IV; (5)-(18); Table I, pp.934-937.

### srt_high_radix  (role: analyzes)
mechanism: The analysis partitions \(1\leq D<2\) into ranges addressed by b divisor bits and determines remainder precisions that preserve overlap between adjacent quotient-digit regions. The parameters t/f describe integer/fractional remainder digits when both redundant portions use equal precision; p/n permit different positive/negative or sum/carry precisions. Programs enumerate combinations satisfying the bounds for every quotient digit and divisor range. # pp.935-937
choices:
  radix: {4, 8, 16}   # pp.934,937
  digit_redundancy: {minimal, intermediate, maximal}   # pp.934,937
new_choices:
  quotient_digit_maximum: r/2 ≤ qmax ≤ r-1 — controls quotient-digit redundancy and required divisor multiples   # p.934
  remainder_representation: {carry_save, borrow_save_signed_digit} — representations proven to require identical truncation   # p.936
  remainder_truncation: {equal_p_n, asymmetric_p_gt_n} — whether both redundant portions contribute the same examined precision   # pp.935-937
  divisor_truncation_bits: b — number of divisor fraction bits examined by quotient selection   # p.936
  qds_input_architecture: {redundant_inputs, assimilated_remainder} — direct-table inputs versus a short carry-propagate assimilation before the table   # pp.936-937
slots:
  digit_select: qds_table   # pp.934-937
parameters: r∈{4,8,16}; radix r=2^s; qmax∈[r/2,r-1]; Tables I-II enumerate t/f/b and t/p/n/b choices; quotient-selection input count is w=b+2(t+f) when p=n   # pp.934,936-937
results:
| metric | value | unit | technology / device | baseline | condition | page |
| radix-4 truncation (t,f,b,w) | (3,3,1,15) | digits/bits/inputs | UNKNOWN / 1995 | none | qmax=2, p=n | p.937 |
| radix-4 truncation (t,f,b,w) | (4,1,2,12) | digits/bits/inputs | UNKNOWN / 1995 | none | qmax=3, p=n | p.937 |
| examined digits | approximately 3log₂r | digits | UNKNOWN / 1995 | radix r | inspection of Tables I-II | p.937 |
| quotient-selection inputs w | approximately 6log₂r | inputs | UNKNOWN / 1995 | radix r | larger digit sets generally reduce f and b | p.937 |
| minimum-radix-8 truncation sum f+b | 11 | bits | UNKNOWN / 1995 | alternative radix-8 truncations | minimally redundant radix-8 division | p.937 |
| ROM input reduction after assimilation | halved | inputs | UNKNOWN / 1995 | ROM consuming separate sum/carry portions | higher-radix selection | p.937 |
errors_and_checks: Equations (14) and (18) provide necessary and sufficient conditions for correct quotient-digit selection; Tables I-II contain combinations satisfying the conditions for every qi and divisor subrange m. # p.936
conditions: Intermediate digit sets from \([-(1+r/2),\ldots,+(1+r/2)]\) through \([-(r-2),\ldots,+(r-2)]\) appear most practicable at higher radices. # p.937
conditions: More divisor bits can be preferable to more remainder bits because divisor inputs remain constant during all iterations and need no propagation/setup time on the iteration critical path. # p.937
conditions: Assimilating the redundant remainder before a ROM is preferable at higher radices when the short carry propagation costs less than operating the larger direct-input ROM. # p.937
conditions: Higher radix reduces iterations but increases quotient-selection logic at least linearly with radix and increases divisor-multiple generation cost. # p.937
evidence: Sections III-V; (5)-(18); Tables I-II, pp.935-937.

## new_families
none

## space_gaps
* `srt_high_radix` lacks choices for partial-remainder representation, separate integer/fractional truncation, divisor truncation, and asymmetric p/n inspection. # pp.935-937
* `qds_table` is named as a slot target but lacks a family definition covering direct redundant inputs versus pre-table assimilation. # pp.936-937
* `srt_radix2.residual_form` lacks the borrow-save signed-digit representation analyzed alongside carry-save. # p.936

## open_questions
* `srt_radix2.residual_estimate_bits` does not specify whether it maps to t integer bits, f fractional bits, or their total, so the reported t=3/f=0 result must not be collapsed into that choice without clarification.
