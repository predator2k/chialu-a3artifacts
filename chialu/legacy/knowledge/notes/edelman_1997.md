---
handle: edelman_1997
citation: Edelman, "The Mathematics of the Pentium Division Bug", SIAM Review, 1997
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [fp32]
authority: landmark
pages_read: 54–67 / 14 pages
---

## summary
The paper specifies the Pentium’s radix-4 SRT division recurrence, carry-save partial-remainder implementation, and quotient-digit lookup table. The paper proves that a defective table entry requires six consecutive divisor bits equal to one and bounds the absolute quotient error by `5e-5` for operands in `[1, 2)`.

## families
### srt_high_radix  (role: analyzes)
mechanism: The divider selects radix-4 quotient digits `qk ∈ {−2, −1, 0, 1, 2}` and updates the partial remainder using `pk+1 := 4(pk − qk d)`, subject to `|pk+1| ≤ 8/3 d`. The Pentium indexes a two-dimensional quotient-digit table with a four-fraction-bit lower approximation `D` of the divisor and a truncated carry-save estimate `Pk` of the partial remainder. Five entries that should return `+2` return `0`, which sends the partial remainder outside the representable recurrence range. (pp.55–59)
choices:
  radix: 4   # p.55
new_choices:
  quotient_digit_set: {−2, −1, 0, 1, 2} — redundant digits available to each radix-4 iteration   # p.55
  divisor_index_quantization: D ≤ d < D + 1/16 — divisor table index is rounded down to four fractional bits   # p.57
  residual_index_formation: Pk = Ck + Sk — carry and sum words are separately rounded down to multiples of 1/8 before addition   # p.59
slots:
  digit_select: qds_table   # p.57
parameters: normalized numerator and denominator `1 ≤ p,d < 2`; one radix-4 quotient digit per iteration; `D` has form `x.yyyy`; `Pk` has form `xxxx.yyy`; internal Pentium precision is UNKNOWN   # pp.55,57,60
results:
| metric | value | unit | technology / device | baseline | condition | page |
| flawed quotient-table entries | 5 | entries | defective Pentium, node UNKNOWN, 1997 | correct quotient-digit table | `D ∈ {17/16, 20/16, 23/16, 26/16, 29/16}` | p.57 |
| required at-risk divisor run | 6 | consecutive one bits | defective Pentium, node UNKNOWN, 1997 | divisors without the required run | bits `d5` through `d10`, with `1.d1d2d3d4` selecting a bad column | pp.63–64 |
| earliest possible bug occurrence | 9 | quotient-digit step | defective Pentium, node UNKNOWN, 1997 | first iteration | `q0` through `q7` are guaranteed correct | p.66 |
| absolute error bound | `5e-5` | absolute quotient error | defective Pentium, node UNKNOWN, 1997 | correct quotient | numerator and denominator in `[1, 2)` | pp.55,66 |
| reported test-case error | `4.65e-5` | absolute quotient error | defective Pentium, node UNKNOWN, 1995 | correct quotient | `14909255/11009918`; exhaustive single-precision computation attributed to Pratt | p.66 |
| highest reported relative error | roughly `6e-5` | relative quotient error | defective Pentium, node UNKNOWN, 1995 | correct quotient | Pratt’s reported single-precision results | p.66 |
errors_and_checks: The five defective entries return `0` instead of `+2`; after that invalid choice, the recurrence cannot recover the correct quotient. Kahan’s tester concentrates on table fenceposts, while Bryant’s BDD verifier checks that partial remainders remain in the critical region; unreachable entries must not be treated as invalid merely because testing cannot exercise them. (pp.54,56–58)
conditions: Correct SRT operation requires every selected digit to keep `|pk+1| ≤ 8/3 d`; overlap regions permit either of two valid digits but do not correct an invalid digit. (pp.55–56) A flawed entry is reachable only through the immediately lower “foothold” entry, following `q = −2` or `q = −1`, then exactly one `q = 2`. (pp.60,63–65) The at-risk divisor must select one of five bad columns and have `d5` through `d10` all equal to one. (pp.57,63–64)
evidence: §§2–4; Fig. 3.1; Fig. 4.1; Table 4.1; Table 5.1; Lemma 5.1; Theorem 6.1; Lemma 6.6; §7.

### carry_save_datapath  (role: instantiates)
mechanism: The Pentium retains each partial remainder as sum and carry words `ck + sk`. Each iteration combines `ck`, `sk`, and `−qk d` without full carry propagation, then shifts the result by two bits for radix 4. Positive `qk` uses the one’s complement of `qk d`, with the delayed addition of one injected into the carry word. (pp.58–59)
choices:
  compressor: 3_2   # pp.58–59
  accumulator_redundant: true   # p.59
new_choices:
  negative_multiple_encoding: ones_complement_with_delayed_one — the correction bit is injected into the carry word before shifting   # p.59
slots:
  none
parameters: two-word partial remainder `ck + sk`; three-input carry-save update per iteration; radix-4 two-bit shift; internal word width UNKNOWN   # pp.58–60
results: none
errors_and_checks: Separate truncation of `ck` and `sk` makes the table index `Pk` nonunique for a given exact `pk`, which is included in the reachability analysis.   # pp.57,59
conditions: The least significant bit of the carry word is normally zero, but the bit carries the delayed one’s-complement correction when required.   # pp.58–59
evidence: §4.1 and the “Radix 4 SRT Division with Carry–Save Addition Pentium Style” pseudocode.

## new_families
none

## space_gaps
* `srt_high_radix` needs a `quotient_digit_set` choice because the redundant set `{−2, −1, 0, 1, 2}` defines the valid selection intervals. (pp.55–56)
* `srt_high_radix` needs choices for divisor/residual index quantization because `D` and `Pk` truncation determine table reachability. (pp.57–59)
* `qds_table` appears as a slot family but lacks a declared schema for thresholds, overlap entries, unreachable entries, and table verification. (pp.57–58)

## open_questions
* The document does not state the actual number of internal Pentium carry-save bits. (p.60)
* Quotient-table entries outside the five reconstructed bad columns remain ambiguous where overlap permits two correct digits. (p.57)
* The document does not determine exactly how the five erroneous table entries were introduced. (pp.66–67)
