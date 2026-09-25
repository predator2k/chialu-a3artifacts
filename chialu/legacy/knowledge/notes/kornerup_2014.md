---
handle: kornerup_2014
citation: Kornerup, "Digit Selection for SRT Division and Square Root", IEEE Transactions on Computers, 2005
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: []
authority: incremental
pages_read: 5 / 5
---

## summary
The document corrects the digit-selection parameter test from the cited 2005 SRT division/square-root paper. The corrected method determines table-index truncation parameters `(u,t)` from the radix and redundant digit set, and it gives a search-free result for maximally redundant digit sets.

## families
### srt_high_radix  (role: extends)
mechanism: SRT result digits are selected by a table or equivalent logic indexed by `u` leading fractional divisor digits and `t` leading fractional partial-remainder digits. The corrected method derives admissible `(u,t)` pairs from radix `β=2^p`, digit set `D={−a,...,a}`, redundancy index `ρ=a/(β−1)`, and exhaustive checks of `Δ(t,u,d,ρ,k)`. The original test could accept an invalid table because it checked only `d=a`; the corrected test also checks `d=0,...,a−1`. # pp.1–4
choices:
  radix: 4, 8, 16, 32, 64 [outside domain], 128 [outside domain]   # p.3
  digit_redundancy: minimal, maximal   # pp.4–5
new_choices:
  divisor_truncation_bits_u: integer satisfying Eq. (7) — number of leading fractional divisor digits indexing the selection table   # p.3
  remainder_truncation_bits_t: integer selected by Eqs. (8)–(10) and the `simple`/`rest` tests — number of leading fractional partial-remainder digits indexing the table   # pp.3–4
  maximum_digit_a: integer with `β/2 ≤ a ≤ β−1` — fixes the symmetric digit set `D={−a,...,a}` and redundancy index `ρ=a/(β−1)`   # pp.1,3
slots:
  digit_select: qds_table [index_bits=u+t]   # pp.1,3
parameters: `β=2^p`, `p=2,...,7`; `D={−a,...,a}`; normalized divisor `1/2≤y<1`; table indices `u,t`; operand width/latency/II UNKNOWN   # pp.1,3
results:
| metric | value | unit | technology / device | baseline | condition | page |
| δkd for false acceptance | 0.890625 | dimensionless | UNKNOWN | Theorem 3 of the 2005 paper | `β=16`, `u=9`, `t0=2`, `d=a=15`, `k=2^(u−1)` | p.2 |
| δkd for false acceptance | 0.94140625 | dimensionless | UNKNOWN | Theorem 3 of the 2005 paper | `β=32`, `u=11`, `t0=2`, `d=a=31`, `k=2^(u−1)` | p.2 |
| δkd for corrected parameters | 1.25 | dimensionless | UNKNOWN | false-accept pair `u=9,t0=2` | `β=16`, `u′=6`, `t=3`, `d=a=15`, `k=2^(u′−1)` | p.3 |
| δkd for corrected parameters | 1.125 | dimensionless | UNKNOWN | false-accept pair `u=11,t0=2` | `β=32`, `u′=7`, `t=3`, `d=a=31`, `k=2^(u′−1)` | p.3 |
| minimum table index width `u+t` | 16 | bits | UNKNOWN | other valid `(u,t)` pairs in Example 1 | `β=16`, minimally redundant `a=8`, selected pair `(u,t)=(9,7)` | p.4 |
| table index width `u+t` | 9 | bits | UNKNOWN | alternate valid maximally redundant pair | `β=16`, `a=15`, `(u,t)=(5,4)` or `(6,3)` | p.5 |
errors_and_checks: A table is valid only when `Δ(t,u,d,ρ,k)≥0` for every required `d` and `k`. The original `d=a`-only test has counterexamples at radices 16 and 32; the corrected `simple` and `rest` tests cover all digit values. # pp.2–4
conditions: The table size is exponential in `u+t`, so the method seeks a small `u+t`; minimizing `u` generally also minimizes synthesized delay and area. # p.1. No solution exists for `u<umin`; if `(u,t)` is valid, `(u+s,t)` and `(u,t+s)` are also valid but have larger tables. # p.4. Maximally redundant digit sets admit `(u,t)=(p+1,p)` and, for `p>2`, `(p+2,3)` without search. # pp.4–5
evidence: Sections II–IV; Eqs. (1)–(10); Theorems 1–2; Examples 1–2; pp.1–5

## new_families
### qds_table  (domain: div: dividers / square root, closest: srt_high_radix, why_not: the table is a reusable digit-selection component rather than a complete divider recurrence)
mechanism: A digit-selection table maps truncated divisor or root-approximation bits and truncated partial-remainder bits to a valid redundant quotient or root digit. Its address uses `u+t` bits, where `u` and `t` are derived from `β`, `a`, and `ρ`. Validity requires checking every uncertainty rectangle represented by the truncated inputs; the corrected `Δ` tests determine whether `t̂` must increase to `t̂+1`. # pp.1–4
choices: radix: power of two; digit_set: symmetric `D={−a,...,a}`; divisor_truncation_bits_u: positive integer satisfying Eq. (7); remainder_truncation_bits_t: positive integer selected by Eqs. (8)–(10) and `Δ`; parameter_objective: minimize `u+t`
results:
| metric | value | unit | technology / device | baseline | condition | page |
| table index width `u+t` | 16 | bits | UNKNOWN | other valid pairs in Example 1 | `β=16`, `a=8`, `(u,t)=(9,7)` | p.4 |
| table index width `u+t` | 9 | bits | UNKNOWN | alternate valid pair | `β=16`, `a=15`, `(u,t)=(5,4)` or `(6,3)` | p.5 |
evidence: Sections I–IV; Theorems 1–2; Examples 1–2; pp.1–5

## space_gaps
* `srt_high_radix.radix` excludes the analyzed radices 64 and 128. # p.3
* `srt_high_radix` lacks exact digit-set parameter `a`, although valid table parameters depend on `a` and `ρ=a/(β−1)`. # pp.1,3
* `qds_table` appears as a component-slot value throughout the vocabulary but lacks its own family definition and choices for `u`, `t`, radix, and digit set. # pp.1–4

## open_questions
* The document states that the method concerns SRT division and square root, but Theorems 1–2 are phrased for SRT division and do not specify separate square-root recurrence constraints.
* The document provides an arXiv identifier and year but no later journal venue for the correction.
