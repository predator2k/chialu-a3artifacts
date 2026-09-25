---
handle: muller_2016#s13
parent: muller_2016
citation: J.-M. Muller, "Elementary Functions: Algorithms and Implementation", 3rd ed., Birkhauser, 2016
chapter: Examples of Implementation
pdf_pages: 233-240
status: ok
kind: book_chapter
unit_classes: [VEC_SFU]
formats: [fixed-point, double-precision, internal extended-precision, double-extended, double-double]
authority: textbook
pages_read: 8 / 8
---

## summary
The chapter instantiates range reduction, polynomial/rational approximation, table reconstruction, FMA evaluation, and retry-based correct rounding in five elementary-function libraries and processors. The implementations favor computation over large tables on Itanium, while correctly rounded libraries use increasing-precision fallback phases. The chapter reports latency, table size, approximation degree, intermediate precision, and observed/proven accuracy.

## families
### single_poly  (role: instantiates)
mechanism: The Itanium library evaluates high-degree polynomials over large domains using available instruction-level parallelism. Its sine approximation uses an odd degree-9 polynomial and its cosine correction uses an even degree-8 polynomial. Its arctangent implementation uses a degree-47 polynomial for |x| < 1 and degree-10/degree-44 auxiliary polynomials for |x| ≥ 1. LIBMCR evaluates log(r/y) with an odd Taylor polynomial through s13, and HP-UX approximates 2^u by a polynomial.
choices:
  degree: 9 [outside domain], 8, 47 [outside domain], 10 [outside domain], 44 [outside domain], 13 [outside domain], or UNKNOWN by function   # p.235, p.236, p.239, p.240
  basis: taylor for LIBMCR; UNKNOWN otherwise   # p.239, p.235, p.236, p.240
  coeff_encoding: UNKNOWN   # p.235, p.236, p.239, p.240
  guard_bits: UNKNOWN   # p.235, p.236, p.239, p.240
new_choices:
  symmetry_form: odd | even — constrains a polynomial to xP(x²), x+x³P(x²), or Q(x²) forms   # p.233, p.235, p.236
slots:
  range_reducer: range_reduction [method=cody_waite] for Itanium sine/cosine; none for Itanium arctangent   # p.235, p.236
  evaluator: estrin for the Itanium large-degree strategy; UNKNOWN for other examples   # p.235, p.239, p.240
parameters: sine degree 9; cosine-correction degree 8; arctangent degree 47; auxiliary degrees 10 and 44; LIBMCR Taylor series through s13; HP-UX L typically 10   # p.235, p.236, p.239, p.240
results:
| metric | value | unit | technology / device | baseline | condition | page |
| latency | 52 | cycles | INTEL/HP Itanium; node/year UNKNOWN | UNKNOWN | Intel double-precision natural logarithm | p.235 |
| latency | 70 | cycles | INTEL/HP Itanium; node/year UNKNOWN | UNKNOWN | Intel double-precision sine or cosine | p.235 |
| accuracy | within 0.51 | ulps | INTEL/HP Itanium; node/year UNKNOWN | UNKNOWN | most Intel library functions | p.235 |
| reciprocal relative error | less than 2−8.886 | relative error | Itanium frcpa; node/year UNKNOWN | exact 1/x | arctangent path for \|x\| ≥ 1 | p.236 |
| evaluation accuracy | 77-bit | accuracy | SUN LIBMCR; device/year UNKNOWN | UNKNOWN | Taylor evaluation of log(r/y) | p.239 |
errors_and_checks: The Cyrix approximations are shown to be monotonic. The HP-UX trigonometric error is an observed rather than proven maximum.   # p.233, p.240
conditions: Large-degree polynomials simplify range reduction and reduce memory use on Itanium, where parallel execution/Estrin evaluation and extended precision limit the speed/accuracy penalty.   # p.234, p.235
evidence: Sections 12.1, 12.2, 12.5, and 12.6; pp.233-240.

### piecewise_poly  (role: instantiates)
mechanism: CRLIBM logarithm first places a normalized mantissa in [11/16, 23/16], splits that interval into 8 subintervals, subtracts the selected midpoint exactly, and evaluates a degree-12 polynomial in the resulting local argument. The coefficients depend on the selected subinterval.
choices:
  segments: 8   # p.238
  degree: 12 [outside domain]   # p.239
  basis: UNKNOWN   # p.239
  coeff_encoding: per_coeff_width [outside domain interpretation: the first two coefficients are sums of two double-precision numbers]   # p.239
  guard_bits: UNKNOWN   # p.239
  coefficient_optimization: UNKNOWN   # p.239
  rounding_contract: exact   # p.237, p.239
new_choices:
  none
slots:
  range_reducer: range_reduction [reduction_type=additive]   # p.238
  evaluator: UNKNOWN   # p.239
  segmenter: UNKNOWN   # p.238
parameters: 8 subintervals; degree-12 polynomial; first two coefficients represented as sums of two double-precision numbers   # p.238, p.239
results:
| metric | value | unit | technology / device | baseline | condition | page |
| quick-phase accuracy | 57 or 64 | bits | CRLIBM; device/year UNKNOWN | UNKNOWN | ln(x), depending on execution path | p.238 |
| accurate-phase accuracy | 120 | bits | CRLIBM/SCSLIB; device/year UNKNOWN | correct rounding threshold from Table 10.6 | ln(x) | p.238 |
errors_and_checks: The accurate phase provides enough precision to guarantee correct rounding.   # p.238
conditions: Subnormal inputs use ln(x) = −52 ln(2) + ln(2^52x), while normalized positive inputs use the 8-subinterval reduction.   # p.238
evidence: Sections 12.4, 12.4.2; pp.237-239.

### lut_plus_poly  (role: instantiates)
mechanism: The implementations combine stored anchor values with local polynomial evaluation. Itanium sine/cosine reconstructs from tabulated sin(Nπ/16)/cos(Nπ/16). CRLIBM uses tabulated double-double sine/cosine anchors at kπ/256. LIBMCR selects an accurate table point y and evaluates log(r/y) locally. HP-UX exponential reads 2^(2^-L n) and approximates the remaining 2^u.
choices:
  degree: UNKNOWN   # p.235, p.238, p.239, p.240
  index_bits: 10 for a typical HP-UX exponential configuration; UNKNOWN otherwise   # p.240
  basis: taylor for LIBMCR; UNKNOWN otherwise   # p.239, p.235, p.238, p.240
  coeff_encoding: UNKNOWN   # p.235, p.238, p.239, p.240
  guard_bits: UNKNOWN   # p.235, p.238, p.239, p.240
  breakpoint_placement: gal_accurate_points for LIBMCR; uniform for the kπ/256 and Nπ/16 tables   # p.235, p.238, p.239
  multiplier_shape: UNKNOWN   # p.235, p.238, p.239, p.240
new_choices:
  anchor_representation: single_extended | double_double — precision used to store or reconstruct table anchors   # p.235, p.238
slots:
  range_reducer: range_reduction [method=table_augmented]   # p.235, p.238, p.239, p.240
  evaluator: UNKNOWN   # p.235, p.238, p.239, p.240
  segmenter: uniform_high_bit_decode for HP-UX leading-L-bit selection; UNKNOWN otherwise   # p.240, p.235, p.238, p.239
parameters: Intel tables range from none at all to 256 double-extended entries; CRLIBM reduced y lies in [−π/512, π/512]; HP-UX L is typically 10   # p.235, p.238, p.240
results:
| metric | value | unit | technology / device | baseline | condition | page |
| table size | none at all | double-extended table entries | INTEL/HP Itanium; node/year UNKNOWN | UNKNOWN | tangent and arctangent | p.235 |
| table size | 256 | double-extended table entries | INTEL/HP Itanium; node/year UNKNOWN | UNKNOWN | natural logarithm | p.235 |
| added accuracy | 14 extra | bits of accuracy | CRLIBM; device/year UNKNOWN | direct double-precision evaluation | quick-phase sine/cosine construction | p.238 |
| table-anchor argument error | less than 2−5 + 2−12 | absolute error | SUN LIBMCR; device/year UNKNOWN | r | \|y−r\| | p.239 |
| table-anchor logarithm distance | less than 2−24 | ulps | SUN LIBMCR; device/year UNKNOWN | nearest double-precision number | log(y) | p.239 |
errors_and_checks: CRLIBM table/polynomial reconstruction supports a correctly rounded two-phase algorithm. LIBMCR invokes multiple precision when the almost-rounded result is too close to a rounding midpoint.   # p.237, p.239
conditions: Large tables should be avoided on Itanium because memory-reference latency exceeds the computational polynomial portion.   # p.234
evidence: Sections 12.2.1, 12.4.1, 12.5, and 12.6; pp.235-240.

### estrin  (role: instantiates)
mechanism: Estrin’s method evaluates the large-degree polynomials used by the Itanium elementary-function library by exploiting parallel floating-point units.
choices:
  none
new_choices:
  none
slots:
  none
parameters: large polynomial degrees; exact schedule UNKNOWN   # p.235
results:
| metric | value | unit | technology / device | baseline | condition | page |
| none | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | no isolated Estrin cost is reported | p.235 |
errors_and_checks: Extended internal precision limits the accuracy penalty of high-degree evaluation for double-precision results.   # p.235
conditions: Estrin evaluation is suitable because several pipelined floating-point units provide parallelism.   # p.234, p.235
evidence: Section 12.2; pp.234-235.

### fma_based  (role: instantiates)
mechanism: Itanium uses fused multiply-add to shorten and improve polynomial evaluation. Its sine/cosine range reduction computes r = (x − NP1) − NP2 with two consecutive fused multiply-adds, where P1 permits exact computation of x − NP1 and P1 + P2 closely approximates π/16.
choices:
  none
new_choices:
  none
slots:
  none
parameters: two consecutive fused multiply-adds for sine/cosine range reduction   # p.235
results:
| metric | value | unit | technology / device | baseline | condition | page |
| none | UNKNOWN | UNKNOWN | Itanium FMA; node/year UNKNOWN | separate additions and multiplications | no isolated numerical speed/accuracy result is reported | p.234 |
errors_and_checks: FMA evaluation is generally more accurate than separate addition/multiplication, but the chapter gives no isolated bound.   # p.234
conditions: FMA and parallelism make polynomial computation shorter than memory references, which favors computation over large tables.   # p.234
evidence: Sections 12.2 and 12.2.1; pp.234-235.

### range_reduction  (role: instantiates)
mechanism: Itanium sine/cosine uses Cody-Waite reduction with N closest to 16x/π and a two-term π/16 constant. CRLIBM reduces trigonometric inputs to a double-double y in [−π/512, π/512]. CRLIBM logarithm uses exponent extraction, an 8-subinterval mantissa partition, and exact midpoint subtraction. LIBMCR and HP-UX use table-augmented decompositions.
choices:
  method: cody_waite for Itanium sine/cosine; table_augmented for LIBMCR logarithm and HP-UX exponential; UNKNOWN for CRLIBM reductions   # p.235, p.238, p.239, p.240
  split_constant_terms: 2 for Itanium π/16 reduction; UNKNOWN otherwise   # p.235
  reduction_type: additive   # p.235, p.238, p.239, p.240
  worst_case_bound_proven: UNKNOWN   # p.235, p.238, p.239, p.240
new_choices:
  none
slots:
  none
parameters: N closest to 16x/π; P1+P2 approximates π/16; CRLIBM y in [−π/512, π/512]; logarithm mantissa range [11/16, 23/16] split into 8 subintervals; HP-UX L typically 10   # p.235, p.238, p.240
results:
| metric | value | unit | technology / device | baseline | condition | page |
| reduced-argument bound | π/512 < 2−7 | value | abstract | original trigonometric argument | CRLIBM sine/cosine quick phase | p.238 |
| local logarithm argument bound | less than 0.01575 | value | abstract | unreduced r/y | LIBMCR s=(r−y)/(r+y) | p.239 |
errors_and_checks: The Itanium choice of P1 makes x−NP1 exact. CRLIBM midpoint subtraction is performed without error.   # p.235, p.238
conditions: Itanium uses simple range reduction to avoid loading constants. Its arctangent implementation performs no range reduction and instead uses a degree-47 polynomial.   # p.235, p.236
evidence: Sections 12.2-12.6; pp.235-240.

### correct_rounding_strategy  (role: compares)
mechanism: LIBULTIM uses Ziv’s multilevel strategy, increasing precision only when a lower-precision result cannot guarantee rounding. CRLIBM uses a quick 60-to-80-bit phase and one accurate fallback phase sized from known hard-to-round cases. LIBMCR calls an almost-correct routine, tests proximity to a rounding midpoint, and increases multiple precision until rounding is guaranteed.
choices:
  strategy: ziv_two_phase_retry for CRLIBM; ziv_multilevel_retry [outside domain] for LIBULTIM and LIBMCR   # p.237, p.239
  worst_case_knowledge: conservative_unknown for LIBULTIM; filtered_search for CRLIBM; UNKNOWN for LIBMCR   # p.237, p.239
  rounding_modes_covered: nearest_only for the described LIBMCR test; UNKNOWN otherwise   # p.239
new_choices:
  retry_levels: two | increasing_until_proven — distinguishes CRLIBM’s bounded two phases from multilevel fallback   # p.237, p.239
slots:
  none
parameters: LIBULTIM assumes 800 bits suffice; CRLIBM quick phase uses 60 to 80 bits; CRLIBM ln accurate phase uses 120 bits   # p.237, p.238
results:
| metric | value | unit | technology / device | baseline | condition | page |
| assumed fallback precision | 800 | bits of precision | IBM LIBULTIM; device/year UNKNOWN | UNKNOWN | worst correct-rounding cases unavailable | p.237 |
| quick-phase accuracy | between 60 and 80 | bits of accuracy | CRLIBM; device/year UNKNOWN | UNKNOWN | function-dependent | p.237 |
| accurate-phase accuracy | 120 | bits | CRLIBM/SCSLIB; device/year UNKNOWN | hard-to-round cases from Lefèvre’s algorithms | ln(x) | p.238 |
| largest observed error | 0.502 | ulps | HP-UX Itanium; node/year UNKNOWN | correctly rounded result | double-precision trigonometric functions; observed, not proven | p.240 |
errors_and_checks: LIBULTIM, CRLIBM, and LIBMCR target correctly rounded double-precision functions. CRLIBM publishes a proof with each function. HP-UX does not provide correct rounding.   # p.237, p.239, p.240
conditions: CRLIBM’s accurate phase is rarely used, so its performance matters less than tight quick-phase error bounds. LIBMCR retries when a result is too close to the midpoint of consecutive floating-point numbers under round-to-nearest.   # p.237, p.239
evidence: Sections 12.3-12.6; pp.237-240.

## taxonomy
* Examples of implementation
  * Cyrix FastMath processor
    * 2^x−1: rational approximation of 2^(x/2)−1 plus reconstruction -> unmapped   # p.233
    * sine: odd xP(x²) approximation -> single_poly   # p.233
    * cosine: ±sqrt(1−sin²(x)) reconstruction -> unmapped   # p.233
    * log2(x+1): odd gQ(g²) rational approximation after g=x/(x+2) -> unmapped   # p.233, p.234
    * tangent: odd xP(x²)/Q(x²) approximation -> unmapped   # p.234
    * arctangent: five-segment odd xP(x²)/Q(x²) approximation -> unmapped   # p.234
  * Intel functions for Itanium
    * simple range reduction -> range_reduction   # p.235
    * large-degree parallel polynomial evaluation -> single_poly   # p.235
    * Estrin evaluation -> estrin   # p.235
    * fused multiply-add evaluation -> fma_based   # p.234, p.235
    * sine/cosine table reconstruction plus polynomials -> lut_plus_poly   # p.235, p.236
    * arctangent degree-47/degree-10/degree-44 polynomials -> single_poly   # p.236
  * LIBULTIM
    * Ziv multilevel increasing-precision evaluation -> correct_rounding_strategy   # p.237
  * CRLIBM
    * quick phase plus accurate phase -> correct_rounding_strategy   # p.237
    * sine/cosine table reconstruction plus small polynomials -> lut_plus_poly   # p.238
    * logarithm 8-subinterval degree-12 approximation -> piecewise_poly   # p.238, p.239
  * SUN LIBMCR
    * almost-correct result plus increasing-precision fallback -> correct_rounding_strategy   # p.239
    * Gal accurate table plus local Taylor series -> lut_plus_poly   # p.239
  * HP-UX Itanium
    * shared sine/cosine calculations -> unmapped   # p.239, p.240
    * exponential table plus polynomial -> lut_plus_poly   # p.240

## primary_sources
* Cody and Waite, year UNKNOWN — split-constant sine/cosine range reduction   # p.235
* Harrison, Kubaska, Story and Tang, year UNKNOWN — IA-64 elementary-function algorithms and the two detailed Intel examples   # p.234, p.235
* Ziv, year UNKNOWN — multilevel increasing-precision strategy for correct rounding   # p.237
* Lefèvre, year UNKNOWN — generation of worst cases used to size CRLIBM’s accurate phase   # p.237
* Gal, year UNKNOWN — accurate-table method used by LIBMCR logarithm   # p.239
* Markstein, year UNKNOWN — sharing common sine/cosine calculations and Itanium elementary-function algorithms   # p.239, p.240

## new_families
### rational_approximation  (domain: sfu, closest: single_poly, why_not: single_poly and piecewise_poly cannot represent a numerator/denominator approximation or its division cost)
mechanism: Cyrix implements several core functions with approximations of the form xR(x), where R is rational or polynomial. Rational cases use odd forms such as gQ(g²) or xP(x²)/Q(x²). The flat, nonzero R functions permit accurate fixed-point evaluation. Arctangent uses five distinct rational approximations over five subintervals.
choices: symmetry_form: {odd, unrestricted}; segments: Int[1..64:1]; numerator_degree: Int[0..64:1]; denominator_degree: Int[0..64:1]; evaluation_format: {fixed_point, floating_point}
results:
| metric | value | unit | technology / device | baseline | condition | page |
| multiplication reduction | UNKNOWN | multiplications | Cyrix FastMath; node/year UNKNOWN | unrestricted approximation | odd approximation form | p.234 |
evidence: pp.233-234.

### shared_sincos  (domain: sfu, closest: lut_plus_poly, why_not: existing approximation families do not encode one range-reduction/evaluation path producing two function results)
mechanism: A sine/cosine implementation shares range reduction and computation of both functions of the reduced argument when a program requests both results for the same input. The HP-UX compiler for Itanium implements the shared calculation.
choices: output_pair: {sin_cos}; shared_stage: {range_reduction, reduced_argument_evaluation, both}
results:
| metric | value | unit | technology / device | baseline | condition | page |
| shared-work saving | UNKNOWN | UNKNOWN | HP-UX Itanium; node/year UNKNOWN | separate sine and cosine routines | both functions invoked for the same argument | p.239, p.240 |
evidence: pp.239-240.

## space_gaps
* single_poly.degree stops at 8, while the chapter uses degrees 9, 10, 12, 13, 44, and 47.   # p.235, p.236, p.239
* The vocabulary lacks rational and piecewise-rational approximation families for xP(x²)/Q(x²) implementations.   # p.233, p.234
* correct_rounding_strategy.strategy lacks a general multilevel retry value for LIBULTIM/LIBMCR.   # p.237, p.239
* The vocabulary lacks a shared multi-output sine/cosine family.   # p.239, p.240
* piecewise_poly.coeff_encoding cannot state that selected coefficients are represented as sums of two double-precision numbers.   # p.239

## open_questions
* The chapter does not give the Cyrix rational numerator/denominator degrees or its evaluation schedule.
* The chapter does not give most polynomial coefficients, guard-bit counts, exact Estrin schedules, or multiplier shapes.
* The chapter does not identify technology nodes, implementation years, or cycle baselines for the reported libraries/processors.
* The chapter does not state how the Itanium frcpa reciprocal approximation maps to a reusable seed-table or reciprocal-unit family.
