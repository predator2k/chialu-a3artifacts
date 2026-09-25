---
handle: brisebarre_2005
citation: N. Brisebarre, D. Defour, P. Kornerup, J.-M. Muller, N. Revol, "A New Range-Reduction Algorithm", IEEE Transactions on Computers, vol. 54, no. 3, pp. 331-339, 2005
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_SFU]
formats: [fp64]
authority: incremental
pages_read: 331-339 / 9
---

## summary
The document proposes a table-augmented range-reduction algorithm for double-precision trigonometric inputs with absolute value below 2^63 - 1, with Payne-Hanek reduction as the fallback for larger inputs. The algorithm splits a rounded integer argument into eight 7-bit parts, accumulates tabulated remainders as three double-precision components, and returns a two-component reduced argument. The ANSI-C implementation is reported as 4 to 5 times faster than Sun’s Payne-Hanek implementation when its tables reside in main memory.

## families
### range_reduction  (role: proposes)
mechanism: For 8 < x < 2^63 - 1, the algorithm rounds x to an integer, splits that integer into eight signed 7-bit parts, and retrieves each part’s remainder modulo π/2 from Thi/Tmed/Tlo tables. Three additive sums Shi/Smed/Slo preserve the remainder with bounded error. A second reduction subtracts one of four tabulated multiples of π/2, and Fast2sum produces the two-double result (yhi, ylo). Inputs at most 8 use only the second reduction; inputs at least 2^63 - 1 use Payne-Hanek reduction. # pp.335-338
choices:
  method: table_augmented   # pp.335-338
  split_constant_terms: 3   # p.336
  reduction_type: additive   # pp.335-336
  worst_case_bound_proven: true   # pp.336-337
new_choices:
  argument_chunk_bits: 7 — the rounded integer is split into eight table-indexing parts of 7 bits each   # p.335
  remainder_components: 3 — each tabulated remainder and reduction constant is represented by high/medium/low double-precision components   # pp.335-336
  regime_switching: small_table_step_medium_table_pipeline_huge_payne_hanek — the algorithm selects a path from the input magnitude   # pp.335,338
  precision_parameter_p: Int[1..44:1] — p selects the final accuracy branch and error bound   # p.337
slots:
  none
parameters: double-precision input; C = π/2; eight 7-bit parts I0(x) through I7(x); 1,024 table entries; three tables Thi/Tmed/Tlo; 10 address bits; 24 Kbytes total table memory; p from 1 to 44; output as two double-precision numbers; small range x ≤ 8; medium range 8 < x < 2^63 - 1; huge-input fallback x ≥ 2^63 - 1   # pp.335-338
results:
| metric | value | unit | technology / device | baseline | condition | page |
| table memory | 24 | Kbytes | UNKNOWN / 2005 | none | three tables, each 2^10 × 8 bytes | p.336 |
| stored table precision | 153 | bits | UNKNOWN / 2005 | none | Thi + Tmed + Tlo approximation; g = 39 | p.336 |
| intermediate absolute error | less than or equal to 2^-149 | absolute error | UNKNOWN / 2005 | exact x minus an integer multiple of π/2 | S(x) after balanced-tree computation of Slo | p.336 |
| reduced-triple absolute error | less than 2^-148 | absolute error | UNKNOWN / 2005 | exact x minus an integer multiple of π/2 | Rhi + Rmed + Rlo | p.336 |
| worst-case relative error bound | 2^-86 | relative error | UNKNOWN / 2005 | exact reduced argument | p = 14 | p.337 |
| rare-branch probability | around 7.8 × 10^-5 | probability | UNKNOWN / 2005 | estimate (10), C = π/2 | p = 14 and abs(Rhi(x)) < 2^-p | p.337 |
| frequent-case error bound | 2^-90 | relative error | UNKNOWN / 2005 | exact reduced argument | p = 10 and abs(Rhi(x)) ≥ 2^-p | p.337 |
| rare-branch probability | around 1.25 × 10^-3 | probability | UNKNOWN / 2005 | estimate (10), C = π/2 | p = 10 and abs(Rhi(x)) < 2^-p | p.337 |
| operation-count ratio | roughly three times as many | operations | UNKNOWN / 2005 | proposed algorithm | Payne-Hanek over [8, 2^63 - 1] | p.338 |
| implementation speed | 4 to 5 times faster | execution time ratio | UNKNOWN / 2005 | Sun Payne-Hanek implementation | ANSI-C; depends on final precision; tables in main memory | p.338 |
| variant floating-point operations | 17 + 2⌈log_256 x⌉; 19 ≤ N ≤ 33 | operations | UNKNOWN / 2005 | none | loop stops when I = 0 or all parts are processed | p.338 |
| variant table accesses | at most 11 + 2⌈log_256 x⌉ | accesses | UNKNOWN / 2005 | none | loop stops when I = 0 or all parts are processed | p.338 |
| table-memory reduction variant | 4 | Kbytes | UNKNOWN / 2005 | 24 Kbytes design | Tlo values stored in single precision | p.338 |
errors_and_checks: The algorithm targets an always-correct range reduction rather than correctly rounded elementary-function output. For p = 14, the reported worst-case relative-error bound is 2^-86. The intermediate S(x) has absolute error at most 2^-149, and the reduced triple R(x) has absolute error below 2^-148. The bounds assume correctly rounded IEEE-754 arithmetic with round-to-nearest and use the double-precision worst-case reduced magnitude 0.71 × 2^-61. # pp.335-337
conditions: The main table path applies to double-precision trigonometric arguments with 8 < abs(x) < 2^63 - 1. Inputs with abs(x) ≤ 8 use the final reduction step alone, while inputs with abs(x) ≥ 2^63 - 1 require Payne-Hanek or multiple-precision reduction. The speed result assumes frequent calls keep the tables in main memory. The method’s major drawback is its table size. Extensions to fractional multiples of π and to fractional multiples of ln(2) are described as straightforward but are not evaluated. # pp.335,338-339
evidence: §1.1-1.3, §2.1-2.4, §3, §4; Figs. 1-4; Tables 1-2; Algorithm Range-Reduction, pp.331-339

## new_families
none

## space_gaps
* The range_reduction family lacks choices for table-index chunk width, high/medium/low remainder decomposition, magnitude-based fallback thresholds, and a tunable final precision parameter p. # pp.335-338
* The range_reduction method domain identifies table_augmented but does not distinguish this high-radix digit-splitting table method from other table-augmented reductions. # pp.335-336
* The range_reduction family has no slot for the Fast2sum-based expansion-compression stage that converts three floating-point components into two. # p.337

## open_questions
* Table 2’s individual table-access and operation counts are not legible in the supplied text, so only the prose comparisons and explicitly printed variant formulas are recorded.
* The paper states that extensions to other multiples of π and ln(2) are straightforward, but it does not report implementations or measurements for those constants.
