---
handle: dedinechin_2007
citation: F. de Dinechin, C. Q. Lauter, J.-M. Muller, "Fast and Correctly Rounded Logarithms in Double-Precision", RAIRO Theoretical Informatics and Applications, vol. 41, no. 1, pp. 85-102, 2007
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_SFU]
formats: [fp64]
authority: landmark
pages_read: 85-102 / 18
---

## summary
The document presents portable and processor-specific software implementations of a correctly rounded natural logarithm for IEEE-754 double precision. The implementation combines a proven two-step Ziv strategy, exact table-based range reduction, polynomial evaluation, and bounded multiprecision arithmetic. The measured average performance is comparable to several default mathematical libraries, while worst-case execution time is bounded.

## families
### correct_rounding_strategy  (role: extends)
mechanism: A quick approximation first attempts a proven rounding test. Difficult inputs restart with a slower approximation whose accuracy exceeds the published 118-bit worst-case requirement for double-precision logarithm. The bounded worst-case result makes two phases sufficient, and both phases support the four IEEE-754 rounding modes. Processor-specific implementations use double-extended/FMA arithmetic, while the portable implementation uses double-double and triple-double arithmetic. # pp.87-95
choices:
  strategy: ziv_two_phase_retry   # pp.87-89
  worst_case_knowledge: published_exhaustive   # pp.88,95
  rounding_modes_covered: all_ieee_modes   # pp.88,92
new_choices:
  phase_count: 2 — number of approximation phases before final rounding   # pp.89,95
  intermediate_representation: double_extended | double_double_extended | double_double | triple_double | scslib — arithmetic representations selected by processor capability and phase   # pp.89-91
slots: none
parameters: first-step accuracy 2^-61; second-step accuracy 2^-119.5; required worst-case accuracy 2^-118; second phase taken less than 1% of calls   # pp.92,95,98
results:
| metric | value | unit | technology / device | baseline | condition | page |
| average time | 1055 | cycles | Pentium 4 Xeon; year UNKNOWN | none (absolute) | Sun libmcr | p.99 |
| maximum time | 831476 | cycles | Pentium 4 Xeon; year UNKNOWN | none (absolute) | Sun libmcr | p.99 |
| average time | 677 | cycles | Pentium 4 Xeon; year UNKNOWN | none (absolute) | IBM libultim | p.99 |
| maximum time | 463488 | cycles | Pentium 4 Xeon; year UNKNOWN | none (absolute) | IBM libultim | p.99 |
| average time | 706 | cycles | Pentium 4 Xeon; year UNKNOWN | none (absolute) | crlibm portable using scslib | p.99 |
| maximum time | 55804 | cycles | Pentium 4 Xeon; year UNKNOWN | none (absolute) | crlibm portable using scslib | p.99 |
| average time | 634 | cycles | Pentium 4 Xeon; year UNKNOWN | none (absolute) | crlibm portable using triple-double | p.99 |
| maximum time | 5140 | cycles | Pentium 4 Xeon; year UNKNOWN | none (absolute) | crlibm portable using triple-double | p.99 |
| average time | 339 | cycles | Pentium 4 Xeon; year UNKNOWN | none (absolute) | crlibm using double-extended | p.99 |
| maximum time | 4824 | cycles | Pentium 4 Xeon; year UNKNOWN | none (absolute) | crlibm using double-extended | p.99 |
| average time | 323 | cycles | Pentium 4 Xeon; year UNKNOWN | none (absolute) | default libm without correct rounding | p.99 |
| maximum time | 8424 | cycles | Pentium 4 Xeon; year UNKNOWN | none (absolute) | default libm without correct rounding | p.99 |
| average time | 118 | cycles | Opteron; year UNKNOWN | default libm | crlibm using double-extended | p.99 |
| maximum time | 862 | cycles | Opteron; year UNKNOWN | default libm | crlibm using double-extended | p.99 |
| average time | 189 | cycles | Opteron; year UNKNOWN | none (absolute) | default libm without correct rounding | p.99 |
| maximum time | 8050 | cycles | Opteron; year UNKNOWN | none (absolute) | default libm without correct rounding | p.99 |
| average time | 339 | cycles | Pentium 4; year UNKNOWN | default libm | crlibm using double-extended | p.99 |
| maximum time | 4824 | cycles | Pentium 4; year UNKNOWN | default libm | crlibm using double-extended | p.99 |
| average time | 323 | cycles | Pentium 4; year UNKNOWN | none (absolute) | default libm without correct rounding | p.99 |
| maximum time | 8424 | cycles | Pentium 4; year UNKNOWN | none (absolute) | default libm without correct rounding | p.99 |
| average time | 150 | cycles | Pentium 3; year UNKNOWN | default libm | crlibm using double-extended | p.99 |
| maximum time | 891 | cycles | Pentium 3; year UNKNOWN | default libm | crlibm using double-extended | p.99 |
| average time | 172 | cycles | Pentium 3; year UNKNOWN | none (absolute) | default libm without correct rounding | p.99 |
| maximum time | 1286 | cycles | Pentium 3; year UNKNOWN | none (absolute) | default libm without correct rounding | p.99 |
| average time | 50 | arbitrary units | Power5; year UNKNOWN | default libm | crlibm without FMA | p.99 |
| maximum time | 259 | arbitrary units | Power5; year UNKNOWN | default libm | crlibm without FMA | p.99 |
| average time | 42 | arbitrary units | Power5; year UNKNOWN | default libm | crlibm using FMA | p.99 |
| maximum time | 204 | arbitrary units | Power5; year UNKNOWN | default libm | crlibm using FMA | p.99 |
| average time | 52 | arbitrary units | Power5; year UNKNOWN | none (absolute) | default libm derived from IBM libultim | p.99 |
| maximum time | 28881 | arbitrary units | Power5; year UNKNOWN | none (absolute) | default libm derived from IBM libultim | p.99 |
| average time | 73 | cycles | Itanium 1; year UNKNOWN | default libm | crlibm using double-extended and FMA | p.99 |
| maximum time | 2150 | cycles | Itanium 1; year UNKNOWN | default libm | crlibm using double-extended and FMA | p.99 |
| average time | 54 | cycles | Itanium 1; year UNKNOWN | none (absolute) | default libm without correct rounding | p.99 |
| maximum time | 8077 | cycles | Itanium 1; year UNKNOWN | none (absolute) | default libm without correct rounding | p.99 |
errors_and_checks: The contract is correct rounding for every fp64 input in all four IEEE-754 rounding modes. The proof assumes a 2^-118 worst-case requirement, a C99-compliant compiler, and IEEE-754-compliant default floating-point operations. The first-step rounding test returns only when correct rounding is proven; otherwise it invokes the second phase. # pp.92-94
conditions: Correctness depends on the published logarithm worst-case search and the stated compiler/floating-point assumptions. The second phase has negligible average overhead when its invocation probability remains below 1%. # pp.92,98
evidence: Sections 1.2-2.10, Section 3.1, Tables 2-3.

### lut_plus_poly  (role: instantiates)
mechanism: The input is decomposed as x = 2^E·m and adjusted to avoid cancellation. High mantissa bits select one of 128 entries containing ri and log(ri), producing z = y·ri-1 with |z| < 2^-7. A polynomial approximates log(1+z), and reconstruction adds E·log(2)-log(ri). The quick and accurate phases share the argument reduction and tables. # pp.95-98
choices:
  degree: 7 [outside domain] (quick phase); 14 [outside domain] (accurate phase)   # pp.96-98
  basis: minimax_remez   # pp.96-97
new_choices:
  table_sharing: quick_and_accurate_phases — both phases reuse the same reduction tables and reduced argument   # p.96
slots:
  range_reducer: range_reduction [method=table_augmented, reduction_type=multiplicative]   # pp.95-96
  evaluator: estrin [phase=double-extended quick]   # pp.96-97
  evaluator: horner [phase=accurate and portable polynomial portions]   # pp.96-98
parameters: 128 table entries; |z| < 2^-7; degree 7 quick polynomial; degree 14 accurate polynomial; DE accurate evaluation uses double-double-extended for the lower 8 degrees   # pp.96-98
results:
| metric | value | unit | technology / device | baseline | condition | page |
| table size | 3584 | bytes | portable implementation; year UNKNOWN | none (absolute) | 128 × (4 + 3 × 8) | p.99 |
| table size | 3072 | bytes | double-extended implementation; year UNKNOWN | none (absolute) | 128 × (4 + 2 × 10) | p.99 |
| aligned table size | 5120 | bytes | Itanium; year UNKNOWN | none (absolute) | 128 × (8 + 2 × 16) | p.100 |
| total code size | about 2 | KB | double-extended implementation; year UNKNOWN | about 5KB scslib version | measured by objdump | p.100 |
| first-step code size | about 500 | bytes | implementations tested; year UNKNOWN | none (absolute) | compiled code | p.100 |
errors_and_checks: The quick phase reaches 2^-61 overall accuracy, and the accurate phase reaches 2^-119.5. # pp.95,97-98
conditions: Table sharing avoids restarting exact argument reduction and permits more table entries with smaller second-phase polynomials. Memory alignment can increase physical table size on 64-bit processors. # pp.96,99-100
evidence: Sections 3.1-3.3 and Section 4.2.

### range_reduction  (role: instantiates)
mechanism: The reduction decomposes x into exponent and mantissa, adjusts the mantissa around √2, and selects a tabulated reciprocal approximation ri. The reduced argument is z = y·ri-1, and reconstruction uses E·log(2)+log(1+z)-log(ri). The DE implementation makes y·ri and the subtraction exact in double-extended arithmetic; the portable implementation represents the exact result as a double-double. # pp.95-96
choices:
  method: table_augmented   # pp.95-96
  reduction_type: multiplicative   # pp.95-96
  worst_case_bound_proven: true   # pp.96-97
new_choices:
  reciprocal_table_reduction: true — ri approximates 1/y and makes the reduced argument small   # pp.95-96
slots: none
parameters: 128 entries; DE ri values have at most 10 consecutive nonzero mantissa bits and are stored as single-precision values; |z| < 2^-7   # p.96
results: none
errors_and_checks: The argument reduction introduces no rounding error in the DE implementation and produces an exact double-double z in the portable implementation. # p.96
conditions: Exact DE reduction depends on the restricted ri representation and Sterbenz’ lemma. The portable path requires double-double arithmetic because no stated ri choice makes y·ri-1 fit in one double. # p.96
evidence: Sections 3.1-3.3.

### estrin  (role: analyzes)
mechanism: The DE quick phase evaluates its degree-7 polynomial as parallel subexpressions and combines them by powers z² and z⁴. The paper proves a tight overall relative error below 2^-61, including inputs whose logarithm is close to zero. # pp.96-97
choices: none
new_choices: none
slots: none
parameters: degree 7; first-step DE implementation   # pp.96-97
results: none
errors_and_checks: Overall relative error is smaller than 2^-61 in all cases. # p.97
conditions: Near-zero logarithms require a relative-error proof using log(1+x) ≈ x; the proof uses machine assistance. # p.97
evidence: Section 3.2.

### horner  (role: instantiates)
mechanism: Horner evaluation is used for the degree-14 accurate polynomial and for degrees 3 through 7 of the portable quick polynomial. The portable accurate phase changes precision by degree, using double arithmetic for degrees 10 through 14 and double-double arithmetic for degrees 3 through 9. # pp.96-98
choices: none
new_choices:
  per_degree_precision: double | double_double | double_double_extended — evaluation precision changes across polynomial terms   # pp.96,98
slots: none
parameters: degree 14 accurate polynomial; degrees 3-7 portable quick polynomial; degrees 10-14 in double and 3-9 in double-double for portable accurate evaluation   # pp.96-98
results: none
errors_and_checks: The mixed-precision evaluation contributes to the proven 2^-119.5 accurate-phase bound. # pp.95,98
conditions: Mixed precision minimizes costly triple-double operations; the implementation never multiplies two triple-double values. # p.98
evidence: Sections 3.2-3.3.

## new_families
none

## space_gaps
* `correct_rounding_strategy` lacks choices for phase count and phase-specific intermediate representation, which distinguish the implementations and their costs. # pp.89-91
* `lut_plus_poly.degree` ends at 5, while this implementation uses degrees 7 and 14. # pp.96-98
* `lut_plus_poly` lacks a choice for sharing reduction state/tables between retry phases. # p.96
* `range_reduction.method` names only generic `table_augmented`, while the document exposes reciprocal-table reduction through z = y·ri-1. # pp.95-96
* Polynomial evaluator families lack a choice for per-degree precision scheduling. # pp.96,98

## open_questions
* The document does not report the calendar year of the benchmark measurements.
* The document does not quantify the probability of the second phase beyond “less than 1%.”
* The document does not give a single table index-bit count, although it reports 128 entries.
