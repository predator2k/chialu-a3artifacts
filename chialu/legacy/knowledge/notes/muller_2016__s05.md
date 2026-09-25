---
handle: muller_2016#s05
parent: muller_2016
citation: J.-M. Muller, "Elementary Functions: Algorithms and Implementation", 3rd ed., Birkhauser, 2016
chapter: Table-Based Methods
pdf_pages: 82-102
status: ok
kind: book_chapter
unit_classes: [VEC_SFU]
formats: [IEEE-754 double-precision floating-point, fixed-point, radix-2 floating-point, base-10 floating-point]
authority: textbook
pages_read: 21 / 21
---

## summary
The chapter classifies table-based elementary-function methods into standard tables with local approximations, Gal accurate tables, and specialized-hardware methods using consecutive lookups. It defines Tang table-driven algorithms, Wong-Goto reductions, bipartite/multipartite tables, and their storage/accuracy tradeoffs.   # p.82-p.102

## families
### direct_lut  (role: compares)
mechanism: Direct tabulation stores one rounded function value for every input address and serves as the storage baseline for bipartite methods.
choices:
  none
new_choices:
  none
slots:
  none
parameters: n-bit input/output; 2^n entries; n-bit words   # p.99-p.100
results:
| metric | value | unit | technology / device | baseline | condition | page |
| table size | n × 2^n | bits | abstract | none | straightforward n-bit tabulation | p.99 |
| table size | 60 | kbytes | abstract | none | n = 15 | p.100 |
| table size | 144 | kbytes | abstract | bipartite 11 kbytes | 18-bit values and 16-bit addresses | p.102 |
errors_and_checks: Stored target-precision values can introduce an error close to 1/2 ulp, so the final error cannot remain bounded by 1/2 ulp or slightly more.   # p.85
conditions: Direct tables become exponentially large with address width and are suited only to low precision.   # p.99-p.100
evidence: Sections 4.1 and 4.4.4; Example 7.

### piecewise_poly  (role: analyzes)
mechanism: The approximation domain is split into subintervals, and each subinterval stores coefficients for a low-degree polynomial or rational approximation.
choices:
  segments: 4   # p.82-p.83
  degree: 4   # p.82-p.83
  basis: minimax_remez   # p.82-p.84
  coeff_encoding: UNKNOWN   # p.82
  guard_bits: UNKNOWN   # p.82
  coefficient_optimization: rounded_remez   # p.82-p.84
  rounding_contract: UNKNOWN   # p.82
new_choices:
  subinterval_size: equal — the sine example divides [0, π/4] into equal subintervals   # p.82-p.83
slots:
  range_reducer: range_reduction [method=UNKNOWN]   # p.82
  evaluator: horner   # p.87
  segmenter: uniform_high_bit_decode   # p.82-p.84
parameters: 1, 2, or 4 sine subintervals; polynomial degrees 3 through 7 in Tables 4.1-4.3   # p.82-p.83
results:
| metric | value | unit | technology / device | baseline | condition | page |
| required degree | 6 | polynomial degree | abstract | none | sin on [0, π/4], one polynomial, absolute error less than 10^-8 | p.82-p.83 |
| required degree | 5 | polynomial degree | abstract | degree 6 with one polynomial | sin on [0, π/4], two equal subintervals | p.82-p.83 |
| required degree | 4 | polynomial degree | abstract | degree 6 with one polynomial | sin on [0, π/4], four equal subintervals | p.82-p.83 |
| absolute error | 0.367 × 10^-8 to 0.472 × 10^-8 | absolute error | abstract | none | degree 4 over the four sine subintervals | p.83 |
errors_and_checks: The sine tables report absolute approximation error; subdomain boundaries require care to preserve monotonicity.   # p.82-p.83
conditions: Smaller subintervals reduce polynomial degree/computation but increase coefficient storage. Large software tables may increase cache-miss probability.   # p.82
evidence: Section 4.1; Tables 4.1-4.5.

### lut_plus_poly  (role: defines)
mechanism: Tang reduces x to a small residual, evaluates a low-degree minimax polynomial, and reconstructs f(x) using tabulated function values. Gal replaces regular breakpoints with nearby machine numbers whose function values lie close to machine numbers.
choices:
  degree: 3; 4; 5; 7; 9 [outside domain]   # p.87-p.89
  index_bits: 6; 8   # p.87-p.91
  basis: minimax_remez   # p.87-p.89
  coeff_encoding: plain   # p.87-p.89
  guard_bits: UNKNOWN   # p.85-p.87
  breakpoint_placement: uniform; gal_accurate_points   # p.87-p.91
  multiplier_shape: full_square   # p.87
new_choices:
  working_precision: target_or_higher — standard tables need precision above the target, while Gal tables can use target precision with care   # p.84-p.85
slots:
  range_reducer: range_reduction [method=UNKNOWN]   # p.85-p.86
  evaluator: horner   # p.87
  segmenter: uniform_high_bit_decode   # p.87-p.88
parameters: exp table has 32 values of 2^(j/32); ln uses 64, 256, or 512 breakpoints; Gal sine/cosine uses Xi = i/256 + εi for 16 ≤ i ≤ 201   # p.86-p.91
results:
| metric | value | unit | technology / device | baseline | condition | page |
| approximation error | 0.1 × 10^-29 | absolute error | abstract | none | ln, 256 breakpoints, degree 7 | p.88 |
| approximation error | 0.2 × 10^-32 | absolute error | abstract | none | ln, 512 breakpoints, degree 7 | p.88 |
| approximation error | 0.92 × 10^-40 | absolute error | abstract | none | ln, 512 breakpoints, degree 9 | p.88 |
| worst table rounding error | 9.6 × 10^-6 | absolute error | abstract | 4.6 × 10^-4 regular table | Gal base-10 four-digit example | p.90 |
| average table rounding error | 4.3 × 10^-6 | absolute error | abstract | 2.7 × 10^-4 regular table | Gal base-10 four-digit example | p.90 |
| average accuracy improvement | 60 | times | abstract | regular table | Gal base-10 four-digit example | p.90 |
| worst-case accuracy improvement | 50 | times | abstract | regular table | Gal base-10 four-digit example | p.90 |
| last-bit accuracy | about 99.9 | percent of tested cases | abstract | none | Gal-Bachelis IEEE-754 double sine/cosine | p.91 |
errors_and_checks: Standard target-precision tables cannot support a final bound near 1/2 ulp. Gal-Bachelis obtains last-bit accuracy experimentally but does not guarantee correct rounding without wider intermediate precision.   # p.85, p.91
conditions: Standard tables suit hardware or processors with inexpensive wider precision. Accurate tables suit software when intermediate precision equals target precision, but finding points for multiple functions becomes expensive.   # p.85, p.89-p.92
evidence: Sections 4.2-4.3; Tables 4.6-4.8; Examples 5-6.

### uniform_high_bit_decode  (role: instantiates)
mechanism: Regular breakpoints or leading input subwords address tables directly; Tang uses k/64 and i/256 grids, while bipartite tables use pairs of fixed-width input subwords.
choices:
  none
new_choices:
  none
slots:
  none
parameters: 6-bit ln grid; 8-bit Gal nominal grid; 2k-bit bipartite addresses   # p.87, p.91, p.99
results:
| metric | value | unit | technology / device | baseline | condition | page |
| address width per bipartite table | 2k = 2n/3 | bits | abstract | n address bits | n = 3k | p.99-p.100 |
errors_and_checks: none
conditions: Direct high-bit decoding applies to regularly spaced partitions; Gal perturbs nominal grid points and therefore needs stored Xi corrections.   # p.87-p.91
evidence: Sections 4.2.2, 4.3, and 4.4.4.

### bipartite  (role: defines)
mechanism: The n = 3k input is split into x0, x1, and x2. Two tables provide A(x0,x1) and B(x0,x2), whose sum approximates f(x); B uses a derivative constant shared by intervals with the same x0.
choices:
  symmetric: true   # p.101
new_choices:
  input_partition: three_subwords — x0, x1, and x2 select two parallel tables   # p.99-p.100
slots:
  none
parameters: n = 3k; two 2k-address-bit tables; Example 7 uses 6/6/4-bit subwords for a 16-bit input   # p.99-p.102
results:
| metric | value | unit | technology / device | baseline | condition | page |
| table size | (4n/3) × 2^(2n/3) | bits | abstract | n × 2^n bits | n = 3k | p.100 |
| table size | 2.5 | kbytes | abstract | direct table 60 kbytes | n = 15 | p.100 |
| approximation error bound | (2^(-4k-1) + 2^(-3k)) max_[α,1]\|f''\| | absolute error | abstract | none | unrounded A/B formula | p.100 |
| total error bound | (2^(-4k-1) + 2^(-3k)) max_[α,1]\|f''\| + 2^(-3k) | absolute error | abstract | none | rounded A/B tables | p.100 |
| total error | less than 2^-19 + 2^-27 | absolute error | abstract | none | 16-bit cosine example | p.102 |
| table size | 11 | kbytes | abstract | direct table 144 kbytes | 16-bit cosine example | p.102 |
errors_and_checks: The error includes Taylor remainder and table-value rounding; guard bits or a larger internal n improve accuracy.   # p.100
conditions: The basic bound assumes f and f'' have similar orders of magnitude. Symmetric midpoint expansion halves the B table.   # p.100-p.101
evidence: Section 4.4.4; Figures 4.3; Example 7.

### multipartite  (role: taxonomizes)
mechanism: Three or more tables are read in parallel, and their values are summed to generalize the bipartite decomposition.
choices:
  tables: UNKNOWN   # p.102
  hierarchical: UNKNOWN   # p.102
new_choices:
  table_size_optimization: total_table_size — decomposition parameters can be optimized for minimum aggregate storage   # p.102
slots:
  none
parameters: three tables or more   # p.102
results:
| metric | value | unit | technology / device | baseline | condition | page |
errors_and_checks: none
conditions: Optimal total-table-size methods can be designed at reasonable cost.   # p.102
evidence: Section 4.4.4.

## taxonomy
* Table-based methods   # p.84-p.85
  * Standard table at regularly spaced values plus polynomial/rational approximation   # p.84-p.85
    * Tang table-driven algorithms -> lut_plus_poly   # p.85-p.88
  * Accurate tables at almost regularly spaced machine numbers   # p.85, p.88-p.92
    * Gal accurate tables method -> lut_plus_poly   # p.88-p.92
  * Several consecutive table lookups with dedicated operators   # p.85, p.92-p.102
    * Wong and Goto logarithm/exponential algorithms -> unmapped   # p.92-p.98
    * Ercegovac et al. evaluation module -> lut_plus_poly   # p.97-p.99
    * Bipartite method -> bipartite   # p.98-p.102
    * Multipartite methods -> multipartite   # p.102
  * Miscellaneous table-with-approximation methods   # p.102
    * Matched interpolation polynomials -> piecewise_poly   # p.102
    * Polynomial approximation with non-uniform segments -> piecewise_poly   # p.102
    * Automated FPGA table-with-polynomial evaluation -> lut_plus_poly   # p.102
    * Second-order, one-multiplication FPGA method -> piecewise_poly   # p.102

## primary_sources
* Tang, UNKNOWN — table-driven algorithms for exp/ln/sin   # p.85-p.88
* Gal, UNKNOWN — accurate tables method   # p.88
* Gal and Bachelis, 1991 — IEEE-754 sine/cosine accurate-table implementation   # p.88-p.91
* Wong and Goto, UNKNOWN — consecutive-lookup algorithms using rectangular multipliers   # p.92-p.98
* Ercegovac, Lang, Muller and Tisserand, UNKNOWN — table-reduced tailored-series evaluation   # p.97-p.99
* Sunderland et al., UNKNOWN — first reported bipartite-style sine tables   # p.98
* DasSarma and Matula, UNKNOWN — rediscovery/naming of the bipartite method for reciprocal seeds   # p.99
* Schulte and Stine, UNKNOWN — general bipartite formula and symmetric midpoint improvement   # p.100-p.101
* Schulte and Stine; Muller, UNKNOWN — independent multipartite generalizations   # p.102
* De Dinechin and Tisserand, UNKNOWN — optimized multipartite table design   # p.102

## new_families
### successive_table_reduction  (domain: sfu, closest: lut_plus_poly, why_not: The method successively multiplies by short tabulated factors rather than selecting coefficients for one local polynomial.)
mechanism: Wong and Goto repeatedly select short correction factors, use rectangular multipliers to move the residual toward zero or one, and finish with a short Taylor expression. Logarithm uses K1/K2/K3 factors; exponential decomposes the fixed-point argument into short fields and multiplies tabulated exponentials.
choices: factor_bits: integer; residual_stages: integer; rectangular_multiplier_shape: width_pair; final_series_degree: integer
results:
| metric | value | unit | technology / device | baseline | condition | page |
| multiplier size | 16 × 56 | bits | abstract | full double-precision multiplier | general stated implementation | p.92 |
| multiplier time | slightly more than half | full double-precision multiplication time | abstract | full double-precision multiplier | rectangular multiplier | p.92 |
| final logarithm error | within 1 | ulp | abstract | claimed 0.5 ulps | 56-bit intermediate rounded to 53-bit IEEE double | p.95-p.96 |
evidence: p.92-p.98

## space_gaps
* `lut_plus_poly.breakpoint_placement` covers Gal points, but the vocabulary lacks the chapter's working-precision choice between target precision and wider intermediate precision.   # p.84-p.85
* `bipartite` lacks input partition widths, table word widths, midpoint expansion, and guard-bit choices.   # p.99-p.102
* The vocabulary lacks Wong-Goto successive multiplicative table reduction with rectangular multipliers.   # p.92-p.98

## open_questions
* The chapter does not give publication years for most cited primary sources.
* The chapter does not state exact table counts or decomposition parameters for the multipartite generalizations.
