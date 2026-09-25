---
handle: markstein_1990
citation: Markstein, "Computation of Elementary Functions on the IBM RISC System/6000 Processor", IBM Journal of Research and Development, 1990
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU, VEC_SFU]
formats: [fp64]
authority: landmark
pages_read: 111-119 / 9
---

## summary
The paper establishes branch-free, correctly rounded Newton-Raphson algorithms for IEEE division and square root using the RS/6000 accumulate instruction. The paper also extends the accurate-table method with a discriminant-triggered higher-precision fallback that correctly rounds elementary functions in the selected IEEE rounding mode.

## families
### newton_raphson  (role: extends)
mechanism: Division microcode refines a table-derived reciprocal with E = 1 - BY and Y' = Y + EY, then refines Q = AY through the exact residual R = A - BQ and Q' = Q + RY. Accumulate instructions preserve the full product in each addition. The final Q' is evaluated in the requested rounding mode. # pp.112-115
choices:
  dedicated_multiplier: false  # p.112
new_choices:
  all_ones_divisor_handling: initial quotient overestimates A/B when B = 2^N - 1 — prevents the exceptional reciprocal convergence direction from defeating final rounding  # pp.114-115
slots:
  seed: monolithic_rom  # p.112
  iter_mult: UNKNOWN  # p.112
  final_round: back_multiply_remainder  # pp.112-115
parameters: N = 53 mantissa bits on RS/6000; iteration count depends on the precision of the initial reciprocal guess  # pp.112,115
results: none
errors_and_checks: The final quotient is correctly rounded in each of the four IEEE rounding modes, and the final operation correctly indicates whether the result is exact.  # pp.112,115
conditions: Every intermediate application of (2), (3), and (4) uses round-to-nearest except the final application of (4). Q must reach more than N-bit accuracy before rounding, and Y used by (3)-(4) must result from (2).  # p.115
evidence: Division section, Equations (2)-(9), Lemmas 1-2, Propositions 1-3, pp.112-115.

### back_multiply_remainder  (role: extends)
mechanism: An accumulate instruction computes R = A - BQ exactly once Q is within one ulp. A second accumulate instruction computes Q' = Q + RY, selecting the current approximation or its adjacent representable value through the requested rounding mode without a conditional correction branch. # pp.112-115
choices:
  quotient_candidates: 2  # p.112
new_choices:
  none
slots:
  none
parameters: quotient Q within one ulp; reciprocal Y correctly rounded, except for the separately handled B = 2^N - 1 case  # pp.113-115
results:
| metric | value | unit | technology / device | baseline | condition | page |
| conditional-branch delay avoided | as much as 15 | cycles | technology node UNKNOWN / IBM RISC System/6000 / 1990 | Tuckerman compare followed by conditional branches | pipelined square-root completion | p.115 |
errors_and_checks: The residual determines the side of the current approximation containing the exact quotient and correctly sets exact/inexact status.  # pp.112,115
conditions: Exact residual computation requires the full double-length product to participate in the accumulate addition.  # p.112
evidence: Equations (3)-(4), Proposition 1, and final division conditions, pp.112-115.

### newton_raphson  (role: extends)
mechanism: Square root uses g' = g + (x - g²)y, where y approximates 1/(2g). Two accumulate instructions preserve all significant bits of x - g². Reciprocal refinement is interleaved with square-root refinement, and a deliberately high reciprocal resolves the difficult half-ulp cases without Tuckerman branches. # pp.115-117
choices:
  steps: 4 [outside domain]  # pp.116-117
new_choices:
  reciprocal_bias: 0.5 + 2^(-53) replaces 0.5 in reciprocal refinement — keeps 1/(2g) between one-half and one ulp high  # pp.116-117
slots:
  none
parameters: 53-bit mantissas; initial g and y have eight correct significant bits; refinements produce 16-bit, 32-bit, 64-bit-before-rounding, and final correctly rounded approximations  # pp.116-117
results:
| metric | value | unit | technology / device | baseline | condition | page |
| iteration latency | six | cycles | technology node UNKNOWN / IBM RISC System/6000 / 1990 | four cycles if an oracle provided y | reciprocal and square-root refinements interleaved | p.116 |
errors_and_checks: The final iteration produces the correctly rounded square root in the restored user rounding mode and correctly sets all status bits.  # p.117
conditions: The method relies on the accumulate instruction retaining an N-bit difference after cancellation in x - g². Initial guesses for the exceptional mantissas must be sufficiently poor that no erroneous extra iteration occurs.  # pp.116,119
evidence: Square root section, Equations (10)-(18), Equation (16) exceptions, and square-root code fragment, pp.115-117.

### classic_fma  (role: instantiates)
mechanism: The RS/6000 accumulate instruction evaluates x + yz while allowing all bits of yz to participate in the sum before rounding. Division, square root, argument reduction, and polynomial reconstruction use this property to make cancellation expose useful low-order product bits. # pp.111-112,116-119
choices:
new_choices:
  none
slots:
  none
parameters: 53-bit mantissas; full double-length product participates in the sum  # p.112
results: none
errors_and_checks: Exact residuals result when the preconditions on reciprocal/quotient accuracy hold.  # p.112
conditions: Algorithms lacking equivalent product precision may fail or require impractical extra computation.  # p.111
evidence: Introduction, division derivation, square-root derivation, and Conclusions, pp.111-112,116-119.

### range_reduction  (role: instantiates)
mechanism: Argument reduction computes x' = x - nc from a split constant c = c₁ + c₂, and perhaps further terms. The first subtraction is exact when n = x/c₁ is correctly rounded; later terms extend accuracy when the reduced argument is small. # pp.116-117
choices:
  reduction_type: additive  # pp.116-117
new_choices:
  none
slots:
  none
parameters: two or more floating-point pieces represent c  # pp.116-117
results: none
errors_and_checks: Error control during argument reduction is required before function approximation.  # p.116
conditions: Additional constant pieces are needed when x' is sufficiently small to contain fewer than N significant bits.  # p.117
evidence: Elementary function library argument-reduction discussion, pp.116-117.

### lut_plus_poly  (role: extends)
mechanism: The reduced domain is divided into 256 approximately equal intervals whose points x_i are selected so f(x_i) has at least 11 zeros or ones beginning at significand bit 54. A table supplies t_i, and an economized power series evaluates h(x - x_i) before one accumulate computes t_i + (x - x_i)h(x - x_i). # p.117
choices:
  index_bits: 8  # p.117
  breakpoint_placement: gal_accurate_points  # p.117
new_choices:
  series_form: economized_power_series — represents the local correction polynomial h(x - x_i)  # p.117
slots:
  range_reducer: range_reduction [reduction_type=additive]  # pp.116-117
  evaluator: fma_based  # p.117
  segmenter: nonuniform  # p.117
parameters: 256 intervals; 53-bit long IEEE word behaves as though it had 64 bits; correction product is less than 1/2048 of |t_i|  # p.117
results:
| metric | value | unit | technology / device | baseline | condition | page |
| correctly rounded single-pass cases | 1023/1024 | cases | technology node UNKNOWN / IBM RISC System/6000 / 1990 | all evaluations | sufficient h accuracy and correction below 1/2048 of \|t_i\| | p.117 |
errors_and_checks: t_i and h each contribute less than 1/2048 ulp error; rounding remains uncertain only when the discriminant lies within 1/1024 ulp of the rounding boundary.  # pp.117-118
conditions: The table values cease to provide enough precision during the rare higher-precision fallback.  # p.118
evidence: Equations (19)-(22) and accurate-table discussion, pp.117-118.

### fma_based  (role: instantiates)
mechanism: Horner evaluation maps each polynomial stage to one RS/6000 accumulate instruction. The final table-plus-polynomial reconstruction also uses one accumulate instruction. # pp.111-112,117
choices:
new_choices:
  none
slots:
  none
parameters: a degree-n polynomial uses n accumulate instructions  # pp.111-112
results: none
errors_and_checks: none
conditions: The method assumes the RS/6000 accumulate instruction's full-product precision.  # pp.111-112
evidence: Introduction and Equation (21), pp.111-112,117.

### correct_rounding_strategy  (role: proposes)
mechanism: A normal-precision evaluation computes a discriminant against 1/2 ulp for round-to-nearest or zero for directed rounding. Cases within 1/1024 ulp of the boundary retry at double length. An inverse function may decide between adjacent candidates by evaluating g(y + u/2); still rarer unresolved cases use a longer calculation. # pp.117-119
choices:
  strategy: ziv_two_phase_retry  # pp.117-118
  worst_case_knowledge: conservative_unknown  # pp.118-119
  rounding_modes_covered: all_ieee_modes  # pp.111,118
new_choices:
  fallback_evaluation: direct_function_or_inverse_function — selects the sharper computation for resolving the last bit  # p.118
slots:
  none
parameters: retry trigger within 1/1024 ulp; double-length discriminant gains more than 40 correct bits; longer fallback remains possible  # p.118
results:
| metric | value | unit | technology / device | baseline | condition | page |
| additional execution cost | of the order of 20% | percent | technology node UNKNOWN / IBM RISC System/6000 / 1990 | standard mathematical library | always correctly rounded elementary functions | p.116 |
| higher-precision frequency | about once in a thousand | evaluations | technology node UNKNOWN / IBM RISC System/6000 / 1990 | normal accurate-table evaluation | discriminant near critical value | p.118 |
| higher-precision latency bound | 1000 | cycles | technology node UNKNOWN / IBM RISC System/6000 / 1990 | normal evaluation | carefully coded double-length path | p.118 |
| discriminant-test overhead | about 15 | cycles | technology node UNKNOWN / IBM RISC System/6000 / 1990 | normal evaluation | discriminant computation and comparison | p.118 |
| average high-precision overhead | one | cycle | technology node UNKNOWN / IBM RISC System/6000 / 1990 | normal evaluation | retry frequency about 1/1000 | p.118 |
| exp and ln latency | 50 to 70 | cycles | technology node UNKNOWN / IBM RISC System/6000 / 1990 | UNKNOWN | accurate table method | p.118 |
| unresolved double-length frequency | possibly once in a trillion | evaluations | technology node UNKNOWN / IBM RISC System/6000 / 1990 | double-length fallback | more than 40 additional correct discriminant bits | p.118 |
errors_and_checks: The contract is correct rounding in the selected IEEE mode; the discriminant detects when normal precision cannot decide the last bit.  # pp.117-118
conditions: Transcendental results for rational floating-point arguments cannot equal the rational midpoint, except for each function's specific rational-result argument. More-than-double precision remains theoretically possible.  # pp.117-119
evidence: Discriminant Equation (22), fallback analysis, inverse-function test, and open questions, pp.117-119.

## new_families
none

## space_gaps
* The division `newton_raphson` family lacks a choice for forcing the initial quotient above A/B for the all-ones divisor mantissa.  # p.115
* The SFU `newton_raphson` family lacks choices for interleaved reciprocal refinement and deliberate one-ulp reciprocal bias.  # pp.116-117
* `correct_rounding_strategy` lacks choices for the discriminant threshold and direct-function versus inverse-function fallback.  # p.118

## open_questions
* The division reciprocal-table width and exact iteration count are not reported.  # pp.112,115
* The elementary-function polynomial degrees and coefficient formats are not reported.  # pp.117-118
* The paper leaves open whether N-bit discriminants always suffice for logarithm arguments between √(1/2) and √2 and whether more-than-double precision can therefore be eliminated for exp/log.  # pp.118-119
