---
handle: jackson_talwar2004
citation: R. Jackson, S. Talwar, "High Speed Binary Addition", 38th Asilomar Conference on Signals, Systems and Computers, 2004.
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [binary]
authority: incremental
pages_read: 1350-1353 / 4
---

## summary
The document generalizes Ling factorization into recursively constructed reduced-generate and hyper-propagate functions for binary carry computation. The document presents theoretical radix-3/radix-4 examples and complexity comparisons, but no fabricated or synthesized delay/area/power results.

## families
### parallel_prefix  (role: analyzes)
mechanism: Bit generate gi and propagate pi functions are recursively combined into group generate G and group propagate P functions. Binary and higher-radix trees reduce the number of combining levels as radix increases, while increasing the complexity of each combining function. # p.1350
choices:
  valency: 2, 3, 4, 5 [outside domain]   # p.1350, p.1353
new_choices:
  none
slots:
  none
parameters: Binary/ternary recurrences; radix-2 through radix-5 equations are compared.   # p.1350, p.1353
results:
| metric | value | unit | technology / device | baseline | condition | page |
| gate fan-in for radix n | n | inputs | UNKNOWN / 2004 | none | parallel-prefix carry recurrence | p.1353 |
errors_and_checks: none
conditions: Higher radix reduces the number of combining levels but increases the complexity of the logic functions at each level. # p.1350
evidence: §II equations (1)-(4), p.1350; Table I and §VI, p.1353.

### ling_prefix  (role: analyzes)
mechanism: Ling factors pn from the group-generate expansion to define pseudo-carry H, then recursively combines subgroup pseudo-carries. The final sum uses a late multiplexer so the extra combination of p and H does not remain on the critical path. # p.1350-p.1351
choices:
  sum_recovery: late_select_mux   # p.1351
new_choices:
  none
slots:
  none
parameters: Generic n-bit operands; binary and ternary pseudo-carry recurrences.   # p.1350-p.1351
results: none
errors_and_checks: none
conditions: Ling factorization reduces the first-level function complexity, but subsequent recursive combinations have the same complexity as parallel-prefix group generate. # p.1351
evidence: §II equations (4)-(9), p.1350-p.1351.

## new_families
### reduced_generate_hyper_propagate  (domain: adder, closest: ling_prefix, why_not: The mechanism recursively combines reduced-generate R and hyper-propagate Q functions at every tree level rather than applying Ling pseudo-carry simplification only at preprocessing.)
mechanism: A selectable factorization writes Gj:i as Dj:k[Bj:k+Gk−1:i], where B is an OR of bit generates and D is group generate OR group propagate. The bracketed term defines reduced generate R. Products of propagate and D define hyper propagate Q. Separate recurrences construct R and Q from subgroup R/Q functions, allowing uniform or mixed-radix carry trees. The sum is recovered with the Ling-style late selection equation. # p.1351-p.1353
choices:
  factorization_range: Int[1..n:1] — the number of bit positions covered by Bj:k in the reduced-generate definition   # p.1351
  combining_radix: Int[2..n:1] — the subgroup arity used by the recursive R/Q equations   # p.1351-p.1353
  radix_schedule: {uniform, mixed} — whether one radix or a combination of radices is used across the carry tree   # p.1352
results:
| metric | value | unit | technology / device | baseline | condition | page |
| achievable radix with n-input gates | n+1 | radix | UNKNOWN / 2004 | parallel_prefix: radix n | generalized reduced-generate/hyper-propagate recurrence | p.1353 |
evidence: §III equations (10)-(12), p.1351; §IV equations (13)-(28), p.1351-p.1352; §V equations (29)-(38), p.1352-p.1353; Table I and §VI, p.1353.

## space_gaps
* The vocabulary lacks a family for recursive reduced-generate R and hyper-propagate Q carry trees, which generalize Ling simplification to every level. # p.1351-p.1353
* parallel_prefix.valency excludes radix 5, which Table I explicitly analyzes. # p.1353

## open_questions
* The document does not map the equations to a named prefix topology or report fanout/wiring constraints.
* The document does not report technology, synthesized delay, area, power, or transistor-level implementation results.
* The document states that complete adder families derived from the equations remain under investigation. # p.1350, p.1353
