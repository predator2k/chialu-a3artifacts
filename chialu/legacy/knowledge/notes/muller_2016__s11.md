---
handle: muller_2016#s11
parent: muller_2016
citation: J.-M. Muller, "Elementary Functions: Algorithms and Implementation", 3rd ed., Birkhauser, 2016
chapter: Final Rounding
pdf_pages: 202-225
status: ok
kind: book_chapter
unit_classes: [VEC_SFU]
formats: [radix-2 floating-point, IEEE-754 single-precision, IEEE-754 double-precision, double-extended precision, quad-precision]
authority: textbook
pages_read: 24 / 24
---

## summary
The chapter defines monotonicity preservation and correct rounding for elementary-function implementations. It classifies the Table Maker's Dilemma responses as increased fixed precision, Ziv multilevel retries, probabilistic estimates, theoretical bounds, exhaustive worst-case searches, and special-case handling. It establishes exhaustive double-precision bounds for several functions/domains while leaving higher precisions and some full trigonometric ranges unresolved.

## families
### correct_rounding_strategy  (role: taxonomizes)
mechanism: An approximation F(x) is computed with mantissa error at most 2^-m and rounded to an n-bit target format. A result near a rounding breakpoint may not determine the correct target value, which creates the Table Maker's Dilemma. Ziv's strategy retries with successively larger m. Alternatively, a known worst-case distance from every breakpoint permits one fixed working precision.
choices:
  strategy: ziv_multilevel_retry [outside domain]   # p.206
  worst_case_knowledge: published_exhaustive   # p.212
  rounding_modes_covered: all_ieee_modes   # p.213
new_choices:
  monotonicity_contract: preserve_source_monotonicity — bounds approximation error using the separation of consecutive function values   # p.203
  breakpoint_type: target_number_for_directed_or_midpoint_for_nearest — identifies values at which rounding changes   # p.205
  special_input_handling: analytic_replacement — replaces function evaluation near zero when the correctly rounded result is known directly   # p.212
slots:
  none
parameters: target mantissa n; working precision m > n; approximation error ±2^-m; initial Ziv precision m0 approximately n+10 or n+20   # p.204, p.206
results:
| metric | value | unit | technology / device | baseline | condition | page |
| monotonicity sufficient bound | ε ≤ 1/2 ulp(x) × min(t∈[x,x+ulp(x)]) \|f'(t)\| | absolute error | abstract | consecutive machine inputs | increasing f | p.203 |
| sine monotonicity error | less than 0.354 | ulps of target format | abstract | n-bit target | sin on [-π/4,+π/4] | p.204 |
| sine monotonicity precision | n+2 | bits of precision | abstract | n-bit target | sufficient when rounded to n bits | p.204 |
| Ferguson-Brightman relative-error bound | ε < \|f(m+)-f(m)\| / (\|f(m+)\|+\|f(m)\|) | relative error | abstract | consecutive machine numbers m,m+ | preserves monotonic behavior | p.204 |
| initial retry failure probability | about one over one million | probability | abstract | m0=n+20 | probabilistic statement | p.206 |
| exhaustive working precision | 35 | bits | abstract | n=16 | log2 | p.207 |
| exhaustive working precision | 29 | bits | abstract | n=16 | 2^x | p.207 |
| exhaustive working precision | 51 | bits | abstract | n=24 | log2 | p.207 |
| exhaustive working precision | 48 | bits | abstract | n=24 | 2^x | p.207 |
| probabilistic hard-tail threshold | k0 ≥ n + log2(ne) + 1.529 | bits | abstract | N=2×ne×2^(n-1) inputs | independent random trailing-bit model | p.209 |
| incorrect-set probability | about 0.6 | probability | abstract | m=113 | double-precision exp candidate set | p.210 |
| incorrect-set probability | about 0.007 | probability | abstract | m=120 | double-precision exp candidate set | p.210 |
| incorrect-set probability | about 0.12 | probability | abstract | m=120 | double-precision sin/cos candidate set | p.210 |
| incorrect-set probability | about 0.0005 | probability | abstract | m=128 | double-precision sin/cos candidate set | p.210 |
| theoretical upper bound on m | 494416 | bits | abstract | n=24 | exp range ln 2 | p.211 |
| theoretical upper bound on m | 3074888 | bits | abstract | n=24 | exp range 10 | p.211 |
| theoretical upper bound on m | 1038560 | bits | abstract | n=53 | exp range ln 2 | p.211 |
| theoretical upper bound on m | 5234891 | bits | abstract | n=53 | exp range 10 | p.211 |
| theoretical upper bound on m | 2527507 | bits | abstract | n=112 | exp range ln 2 | p.211 |
| theoretical upper bound on m | 10409113 | bits | abstract | n=112 | exp range 10 | p.211 |
| exponential sufficient error | ε ≤ 2^-113 | mantissa distance | abstract | double precision | all four rounding modes and \|x\|≥2^-30 | p.213 |
| exponential sufficient error | ε ≤ 2^-158 | mantissa distance | abstract | double precision | all four rounding modes and 2^-54≤\|x\|<2^-30 | p.213 |
| logarithm sufficient error | ε ≤ 2^-118 | mantissa distance | abstract | double precision | natural logarithm and all four rounding modes | p.214 |
errors_and_checks: Correct rounding requires the rounded approximation to equal rounding of the exact function value. Failure remains possible when the approximation interval crosses a target-format breakpoint. The exhaustive bounds certify the covered function/domain combinations; the probabilistic model does not constitute a proof.   # p.205, p.211, p.213
conditions: Ziv retries usually add only slightly more average time than evaluation at m=m0 because large m is rarely required.   # p.206
conditions: The random-bit model is unsuitable for some small arguments, so those inputs require separate analytic treatment.   # p.208
conditions: The double-precision exponential bound m=114 applies for absolute inputs larger than 2^-30, while smaller inputs require separate bounds or direct handling.   # p.210, p.213
conditions: Full-range worst cases remain unknown for double-precision sine and cosine; the reported searches cover sine below approximately 2.5707 and cosine below approximately 1.5706787.   # p.210
conditions: The theoretical transcendence bound proves termination but may require millions of bits, so exhaustive worst-case knowledge is materially tighter for covered formats/domains.   # p.211, p.212
evidence: Sections 10.1-10.7; Figure 10.1; Tables 10.1-10.14; Theorems 14-17, pp.202-225.

## taxonomy
Final rounding   # p.202
  monotonicity preservation   # p.203
    derivative/separation error bound -> unmapped   # p.203
    Ferguson-Brightman consecutive-machine-number criterion -> unmapped   # p.204
  correct rounding   # p.204
    Table Maker's Dilemma   # p.205
      directed-rounding breakpoint at a floating-point number -> correct_rounding_strategy   # p.205
      nearest-rounding breakpoint at a midpoint -> correct_rounding_strategy   # p.205
    working-precision strategies   # p.206
      Ziv multilevel retry -> correct_rounding_strategy   # p.206
      fixed precision from exhaustive worst cases -> correct_rounding_strategy   # p.207, p.212
      probabilistic estimate near 2n -> correct_rounding_strategy   # p.207, p.209
      theoretical transcendence bound -> correct_rounding_strategy   # p.211
    domain handling   # p.212
      analytic treatment of special small inputs -> correct_rounding_strategy   # p.212
      Lefèvre exhaustive double-precision search -> correct_rounding_strategy   # p.212

## primary_sources
* Silverstein et al., UNKNOWN — monotonicity failures can disrupt divided-difference evaluation   # p.202
* Agarwal et al., UNKNOWN — correct rounding preserves monotonicity/symmetry/identities but can conflict with range limits   # p.202
* Ferguson and Brightman, UNKNOWN — techniques and a relative-error theorem for proving monotonicity   # p.204
* Ziv, UNKNOWN — multilevel retry strategy with progressively larger working precision   # p.206
* Schulte and Swartzlander, UNKNOWN — correctly rounded single-precision algorithms and exhaustive precision searches for 1/x, square root, 2^x, and log2(x)   # p.207
* Dunham, UNKNOWN — probabilistic analysis of the Table Maker's Dilemma   # p.207
* Gal and Bachelis, UNKNOWN — probabilistic analysis of the Table Maker's Dilemma   # p.207
* Feldstein and Goodmann, UNKNOWN — statistical distribution of trailing digits in numerical computations   # p.208
* Nesterenko and Waldschmidt, 1995 — lower bound used to limit the distance between machine numbers and exponentials/logarithms of machine numbers   # p.211
* Lefèvre, UNKNOWN — linear-approximation and massive-parallelism algorithms for finding worst cases of the Table Maker's Dilemma   # p.212

## new_families
none

## space_gaps
* The `strategy` domain needs `ziv_multilevel_retry`, because the chapter permits more than two progressively higher-precision attempts.   # p.206
* The family lacks a monotonicity-preservation choice for derivative/separation bounds that do not require correct rounding.   # p.203, p.204
* The family lacks analytic special-input replacement as a companion to worst-case search.   # p.212, p.213, p.214

## open_questions
* The chapter does not establish full-range double-precision worst cases for sine or cosine.   # p.210
* The chapter does not provide practical exhaustive bounds for quad-precision or higher precisions.   # p.209, p.211
* A future standard must decide whether to require correct rounding over the entire domain, provide cheaper modes, and flag results that are not correctly rounded.   # p.225
