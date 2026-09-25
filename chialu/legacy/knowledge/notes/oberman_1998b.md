---
handle: oberman_1998b
citation: S. F. Oberman and M. J. Flynn, "Reducing the Mean Latency of Floating-Point Addition", Theoretical Computer Science, 1998
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [fp64]
authority: incremental
pages_read: 141-149 / 9
---

## summary
The document analyzes quotient-digit selection table complexity for radix-2 through radix-32 SRT floating-point dividers. The document derives allowable divisor/partial-remainder truncations and measures synthesized table delay/area under different redundancy, encoding, folding, and carry-assimilation choices.

## families
### srt_radix2  (role: analyzes)
mechanism: The divider selects one redundant quotient digit per iteration from truncated divisor and shifted partial-remainder estimates. The evaluated tables keep the partial remainder in carry-save two's-complement form and optionally assimilate a short estimate before table lookup. # pp.142-146
choices:
  residual_form: carry_save   # p.145
new_choices:
  none
slots:
  digit_select: qds_table   # pp.143-146
parameters: radix 2; one quotient bit retired per iteration; quotient-digit table has 3 PLA product terms.   # pp.142,147
results:
| metric | value | unit | technology / device | baseline | condition | page |
| table complexity | 3 | product terms | LSI Logic 500 K 0.5 m standard-cell library; 1998 | none | basic radix-2 table | p.147 |
| table delay | -65 | % | LSI Logic 500 K 0.5 m standard-cell library; 1998 | base radix-4 table | basic radix-2 table | p.147 |
| table area | -93 | % | LSI Logic 500 K 0.5 m standard-cell library; 1998 | base radix-4 table | basic radix-2 table | p.147 |
| table speed | 2.86 | times faster | LSI Logic 500 K 0.5 m standard-cell library; 1998 | base radix-4 table | basic radix-2 table | pp.147-148 |
| table speed | 2.40 | times faster | LSI Logic 500 K 0.5 m standard-cell library; 1998 | radix-4 configuration unreadable in supplied text | basic radix-2 table | pp.147-148 |
errors_and_checks: Minimized equations were exercised with several thousand random and directed IEEE double-precision vectors and compared with the DEC Alpha internal FPU; no failure count or formal coverage is reported.   # p.146
conditions: Radix 2 has the smallest evaluated table and is identified as a practical direct-table implementation.   # pp.147-148
evidence: §II, Table III, §V-A, §VI (pp.142,146-148)

### srt_high_radix  (role: compares)
mechanism: Each iteration shifts the carry-save partial remainder, selects a signed redundant quotient digit using truncated divisor/partial-remainder estimates, generates the selected divisor multiple, and forms the next partial remainder. Increasing radix retires more quotient bits per iteration but enlarges and slows the critical-path selection table. # pp.142-145
choices:
  radix: 4, 8, 16, 32   # pp.142,146-148
  digit_redundancy: minimal, maximal   # pp.142,147-148
new_choices:
  none
slots:
  digit_select: qds_table   # pp.143-148
parameters: radix 4/8/16/32; carry-save two's-complement partial remainder; configurations with 20 or more table inputs were not optimized; delay/area are relative to a Gray-coded radix-4 base table unless absolute values are stated.   # pp.145-148
results:
| metric | value | unit | technology / device | baseline | condition | page |
| base-table cells | 43 | cells | LSI Logic 500 K 0.5 m standard-cell library; 1998 | none | Gray-coded radix-4 base table | p.146 |
| base-table delay | 1.47 | ns | LSI Logic 500 K 0.5 m standard-cell library; 1998 | none | Gray-coded radix-4 base table | p.146 |
| delay | -12 | % | LSI Logic 500 K 0.5 m standard-cell library; 1998 | base radix-4 table | external CPA extended by one bit | p.147 |
| area | -7 | % | LSI Logic 500 K 0.5 m standard-cell library; 1998 | base radix-4 table | external CPA extended by one bit | p.147 |
| delay | -16 | % | LSI Logic 500 K 0.5 m standard-cell library; 1998 | base radix-4 table | external CPA extended by two bits | p.147 |
| area | -9 | % | LSI Logic 500 K 0.5 m standard-cell library; 1998 | base radix-4 table | external CPA extended by two bits | p.147 |
| delay | -23 | % | LSI Logic 500 K 0.5 m standard-cell library; 1998 | base radix-4 table | full-mantissa carry-propagate assimilation | p.147 |
| area | -23 | % | LSI Logic 500 K 0.5 m standard-cell library; 1998 | base radix-4 table | full-mantissa carry-propagate assimilation | p.147 |
| total delay | +49 | % | LSI Logic 500 K 0.5 m standard-cell library; 1998 | unfolded table | folded table including XOR conversion | p.147 |
| total area | -8 | % | LSI Logic 500 K 0.5 m standard-cell library; 1998 | unfolded table | folded table including XOR conversion | p.147 |
| total delay | +80 | % | LSI Logic 500 K 0.5 m standard-cell library; 1998 | unfolded table | folded table with t-bit converter | p.147 |
| total area | -10 | % | LSI Logic 500 K 0.5 m standard-cell library; 1998 | unfolded table | folded table with t-bit converter | p.147 |
| delay | -5 | % | LSI Logic 500 K 0.5 m standard-cell library; 1998 | base Gray-coded table | line encoding | p.147 |
| area | -8 | % | LSI Logic 500 K 0.5 m standard-cell library; 1998 | base Gray-coded table | line encoding | p.147 |
| delay | +19 | % | LSI Logic 500 K 0.5 m standard-cell library; 1998 | base Gray-coded table | choose-highest encoding | p.147 |
| area | +32 | % | LSI Logic 500 K 0.5 m standard-cell library; 1998 | base Gray-coded table | choose-highest encoding | p.147 |
| average delay | about 1.5 | times | LSI Logic 500 K 0.5 m standard-cell library; 1998 | base radix-4 table | radix-8 tables | p.148 |
| area | up to 10 | times | LSI Logic 500 K 0.5 m standard-cell library; 1998 | base radix-4 table | radix-8 tables | p.148 |
| average delay | about 2 | times | LSI Logic 500 K 0.5 m standard-cell library; 1998 | base radix-4 table | radix-16 tables | p.148 |
| area | up to 32 | times | LSI Logic 500 K 0.5 m standard-cell library; 1998 | base radix-4 table | radix-16 tables | p.148 |
| delay | 3.5 to 4.7 | times | LSI Logic 500 K 0.5 m standard-cell library; 1998 | base radix-4 table | radix-32 tables | p.148 |
| area | 57 to 141 | times | LSI Logic 500 K 0.5 m standard-cell library; 1998 | base radix-4 table | radix-32 tables | p.148 |
errors_and_checks: Several thousand random and directed IEEE double-precision vectors were compared with DEC Alpha FPU results; no detected-error count, formal proof, or coverage figure is reported.   # p.146
conditions: More partial-remainder bits and fewer divisor bits typically reduce product terms/delay/area, despite requiring a longer external assimilating adder. Radix-8 tables can have reasonable delay/area, but divisor-multiple generation remains a constraint; direct radix-16 and radix-32 tables are judged impractical.   # p.148
evidence: §II-B-C, §III, Tables II-VI, §V, §VI (pp.142-148)

## new_families
### qds_table  (domain: dividers / square root, closest: srt_high_radix, why_not: The vocabulary names qds_table as a component-slot filler but declares no family for its independently optimized table mechanism.)
mechanism: A quotient-digit selection table maps truncated divisor and shifted partial-remainder estimates to an encoded allowable quotient digit. Uncertainty regions ensure that every represented input pair lies within a valid selection interval. Gray encoding lets logic minimization choose among digits in overlap regions; an explicit decoder recovers the digit. Folding, estimate precision, carry-assimilating-adder width, and output encoding trade external logic against table delay/area. # pp.143-147
choices: divisor_estimate_bits: Int; partial_remainder_estimate_bits: Int; assimilator_input_bits: Int; partial_remainder_input: {redundant_direct, short_cpa, full_cpa}; digit_encoding: {gray, line, choose_highest, unencoded}; folding: {none, signed_magnitude, t_bit_converter}   # pp.143-147
results: See the srt_radix2 and srt_high_radix result tables.
evidence: §III, Fig. 2-Fig. 4, Table I-Table VI, §IV-V (pp.143-148)

## space_gaps
* qds_table needs a declared component family with estimate-precision, encoding, folding, and external-assimilator choices.   # pp.143-148

## open_questions
* The supplied text omits several mathematical symbols and Table II-Table VI parameter labels, so the exact estimator-width tuples for individual synthesized configurations remain UNKNOWN.
