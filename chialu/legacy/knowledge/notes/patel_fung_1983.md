---
handle: patel_fung_1983
citation: J. H. Patel, L. Y. Fung, "Concurrent Error Detection in Multiply and Divide Arrays", IEEE Transactions on Computers, vol. C-32, pp. 417-422, 1983
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [binary_integer, uint32]
authority: incremental
pages_read: pp.417-422 / 6 pages
---

## summary
The paper extends recomputing with shifted operands (RESO) to ripple-carry/Wallace-tree multiplier arrays and a nonperforming-restoration divider array (pp.418-420). The paper proves detection of errors caused by failures confined to one array cell or specified neighboring logic and estimates 19 percent multiplier overhead and 23 percent divider overhead for 32-bit arrays (pp.418, 420-421).

## families
### time_redundancy  (role: extends)
mechanism: The first step computes and stores the result. The second step shifts the operands left, recomputes on the same array, realigns the second result, and compares it with the stored result. RESO-1 shifts both multiplier operands by one bit and compares the recomputed product with the first product shifted by two bits. RESO-(2,3) shifts the divider dividend by two bits and divisor by three bits; separate comparisons check the realigned quotient and remainder. A mismatch signals an error. (pp.417-420)
choices:
  transform: shift   # p.417
  iterations: 2   # p.417
  shift_distance: 1 (multiplier); dividend=2, divisor=3 [outside domain] (divider)   # pp.418-420
  correction: false   # pp.417-420
new_choices:
  operand_shift_pattern: multiply=(1,1); divide=(2,3) — the separate left-shift distances applied to each operand during recomputation   # pp.418-420
  comparison_outputs: product; quotient_and_remainder — the realigned outputs checked between computation steps   # pp.418-420
slots:
  comparator: two_rail_tree [input_code=two_rail]   # p.417
parameters: RESO-1 checks n-bit multiplication with an (n+1)-bit multiplier array; the 32-bit example uses a 33-bit array, three 32-bit shifters, and one 34-bit equality checker (p.418). RESO-(2,3) checks n-bit operands and a t-bit quotient with one additional row and three additional cells per row; the 32-bit example uses a 35 by 33-cell array, four shifters of at most 35 bits, and two equality checkers of at most 35 bits (pp.420-421).
results:
| metric | value | unit | technology / device | baseline | condition | page |
| multiplier added array cells | 65 | adder cells | UNKNOWN; 1983 | 32-bit multiplier with 32^2 adder cells | RESO-1 expands the multiplier to 33^2 adder cells | p.418 |
| multiplier hardware increase | 19 | percent | UNKNOWN; 1983 | original 32-bit multiplier | RESO-1; each shifter/checker bit is assumed as complex as one adder cell | p.418 |
| divider added array cells | 131 | divider cells | UNKNOWN; 1983 | 32-bit divider with 32 by 32 cells | RESO-(2,3) uses 35 by 33 cells | p.421 |
| divider hardware increase | 23 | percent | UNKNOWN; 1983 | original 32-bit divider | RESO-(2,3); each shifter/checker bit is assumed half as complex as one divider cell | p.421 |
errors_and_checks: RESO-1 detects all errors in the examined ripple-carry and Wallace-tree multipliers when a failure is confined to one adder cell or one logical gate generating an adder input (p.418). The pipelined variants also cover failures confined to one 1-bit latch (p.418). RESO-(2,3) detects all errors in the examined divider array when a failure is confined to one cell or one inverter generating a quotient bit (pp.420-421). The functional fault model permits arbitrary altered outputs and covers permanent/intermittent failures, but it assumes the affected chip area contains no unrelated lines or components (p.417). False-alarm behavior and alias rate are not reported.
conditions: Directly shifting both divider operands by the same amount can let a quotient inverter or first-cell borrow error affect both computations identically, so the error can escape detection (p.419). RESO-(1,2) fails to detect some divider-array errors, while RESO-(2,3) is identified as the most effective and economical examined variant (p.420). Pipelining can reduce the time overhead, but no numerical latency overhead is reported (pp.418, 421). Larger RESO-k or RESO-(l,m) shifts cover failures affecting larger neighboring areas but require a larger array (p.422).
evidence: Section II and Fig. 1 define RESO (p.417); Section III, Theorem 1, Figs. 2-3, and the 32-bit estimate establish multiplier coverage/cost (p.418); Section IV, Theorem 2, Figs. 4-6, Tables I-II, and the 32-bit estimate establish divider coverage/cost (pp.418-421); Section V states the coverage/area tradeoff (pp.421-422).

## new_families
none

## space_gaps
* `time_redundancy.shift_distance` cannot represent separate dividend/divisor shifts or the associated quotient/remainder realignment required by RESO-(l,m) (pp.419-420).
* `time_redundancy` lacks a checked-unit slot for the multiplier/divider array whose hardware is reused during recomputation (pp.418-420).

## open_questions
* The multiplier discussion does not state whether signed multiplication is covered (p.418).
* The paper states that RESO-(1,2) misses some divider errors but does not enumerate those error cases (p.420).
* The exact circuit structures of the shifters/registers/equality checkers are not specified beyond the optional 1-out-of-2 totally self-checking checker implementation (p.417).
