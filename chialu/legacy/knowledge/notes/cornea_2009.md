---
handle: cornea_2009
citation: Cornea, Harrison, Anderson, Tang, Schneider, Gvozdev, "A Software Implementation of the IEEE 754R Decimal Floating-Point Arithmetic Using the Binary Encoding Format", IEEE Transactions on Computers, 2009
actual_citation: Marius Cornea, Cristina Anderson, John Harrison, Ping Tak Peter Tang, Eric Schneider, Charles Tsen, "A Software Implementation of the IEEE 754R Decimal Floating-Point Arithmetic Using the Binary Encoding Format", 18th IEEE Symposium on Computer Arithmetic (ARITH'07), 2007
status: ok
kind: paper
unit_classes: [other]
formats: [decimal32, decimal64, decimal128, binary64, int32]
authority: incremental
pages_read: 11 / 11
---

## summary
The document presents a software implementation of IEEE 754R decimal floating-point arithmetic that stores significands as binary integers and executes decimal operations with binary hardware. The principal contribution is a correctly rounded reciprocal-multiplication method for decimal coefficients, supplemented by addition/multiplication/division/square-root/conversion algorithms and measured software latencies. # p.1, pp.2-10

## families
### decimal_encoding_codec  (role: instantiates)
mechanism: BID represents the decimal significand as a binary integer rather than as DPD declets. The software library keeps coefficient arithmetic in the integer domain and uses binary multiplication/division/shifting, tables, and corrective rounding to implement decimal operations. # pp.1-2
choices:
  significand_encoding: bid   # p.1
new_choices:
  implementation_domain: software_binary_integer — identifies a decimal codec whose operations remain in binary-integer software rather than unpacked decimal hardware   # pp.1-2
slots:
  none
parameters: decimal32 p = 7 for storage only; decimal64 p = 16; decimal128 p = 34; binary64 coefficient Ca in [0, 2^53); decimal64↔binary64 conversion described   # pp.2,6-8
results:
Device order is D1 = EM64t Xeon 5100 3.0 GHz, D2 = EM64t Xeon 3.2 GHz, and D3 = IA-64 Itanium 2 1.4 GHz.
| metric | value | unit | technology / device | baseline | condition | page |
| abs128 | 19 / 1; 2 / 2; 44 / 44 | clock cycles | D1 / D2 / D3; 2007 | UNKNOWN | maximum / median | p.9 |
| abs64 | 15 / 6; 6 / 5; 12 / 12 | clock cycles | D1 / D2 / D3; 2007 | UNKNOWN | maximum / median | p.9 |
| add128 | 205 / 94; 337 / 178; 242 / 149 | clock cycles | D1 / D2 / D3; 2007 | UNKNOWN | maximum / median | p.9 |
| add64 | 133 / 71; 249 / 132; 219 / 118 | clock cycles | D1 / D2 / D3; 2007 | UNKNOWN | maximum / median | p.9 |
| div128 | 808 / 559; 1369 / 1020; 679 / 454 | clock cycles | D1 / D2 / D3; 2007 | UNKNOWN | maximum / median | p.9 |
| div64 | 266 / 171; 484 / 312; 294 / 180 | clock cycles | D1 / D2 / D3; 2007 | UNKNOWN | maximum / median | p.9 |
| fma64 | 283 / 211; 487 / 365; 284 / 228 | clock cycles | D1 / D2 / D3; 2007 | UNKNOWN | maximum / median | p.9 |
| maxnum128 | 108 / 69; 187 / 130; 120 / 85 | clock cycles | D1 / D2 / D3; 2007 | UNKNOWN | maximum / median | p.9 |
| minnum128 | 113 / 75; 182 / 126; 117 / 82 | clock cycles | D1 / D2 / D3; 2007 | UNKNOWN | maximum / median | p.9 |
| mul128 | 449 / 307; 750 / 543; 306 / 280 | clock cycles | D1 / D2 / D3; 2007 | UNKNOWN | maximum / median | p.9 |
| mul64 | 132 / 69; 227 / 116; 149 / 102 | clock cycles | D1 / D2 / D3; 2007 | UNKNOWN | maximum / median | p.9 |
| quantize128 | 97 / 92; 188 / 172; 100 / 98 | clock cycles | D1 / D2 / D3; 2007 | UNKNOWN | maximum / median | p.9 |
| quantize64 | 45 / 27; 78 / 64; 76 / 62 | clock cycles | D1 / D2 / D3; 2007 | UNKNOWN | maximum / median | p.9 |
| sqrt128 | 544 / 519; 1001 / 911; 458 / 431 | clock cycles | D1 / D2 / D3; 2007 | UNKNOWN | maximum / median | p.9 |
| sqrt64 | 194 / 188; 292 / 287; 223 / 213 | clock cycles | D1 / D2 / D3; 2007 | UNKNOWN | maximum / median | p.9 |
| add64 | 684 / 486 | clock cycles | EM64t Xeon 5100 3.0 GHz; year UNKNOWN | decNumber | maximum / median | p.10 |
errors_and_checks: Results are correctly rounded in all rounding modes, and IEEE status flags are set correctly; no concurrent fault-checking mechanism is reported. # pp.6-8
conditions: Measurements use corner cases and ordinary cases selected to exercise the library rather than represent a decimal workload. Results are preliminary, from a pre-beta library with few optimizations. # p.9
evidence: §§1-6; Table 1, p.9; Tables 2-3, pp.9-10

## new_families
### bid_reciprocal_rounding  (domain: decimal: decimal misc, closest: decimal_fp_addition, why_not: existing families do not cover correctly rounding a binary-integer decimal coefficient by multiplication with reciprocal powers)
mechanism: Method 1 multiplies C by an upward-rounded y-bit approximation kx of 10^-x and truncates. Method 2 first truncates C·2^-x and then multiplies by an upward-rounded approximation hx of 5^-x. The discarded fractional product identifies exact results, midpoints, and values on either side of a midpoint, after which a one-unit correction implements the required rounding mode and inexact flag. # pp.2-6
choices: reciprocal: {power_of_10, power_of_5}; preshift: {none, by_x_bits, by_x_minus_1_bits}; precision_selection: {property_bound, boundary_inequality_reduction}; correction: {none, add_one_lsd}
results:
| metric | value | unit | technology / device | baseline | condition | page |
| reciprocal approximation width | 65 | bits | UNKNOWN; 2007 | analytical Property 1 bound | q = 19, x = 3, k3 ≈ 10^-3 | p.3 |
| reciprocal approximation width | 62 | bits | UNKNOWN; 2007 | 65 bits | boundary-inequality refinement, q = 19, x = 3 | p.4 |
| Method 2 width reduction | x | bits | UNKNOWN; 2007 | Method 1 | approximation of 5^-x | p.4 |
evidence: Properties 1-3 and Methods 1/2, pp.2-4; addition/multiplication application, pp.5-6

### binary_decimal_fp_conversion  (domain: decimal: decimal misc, closest: binary_decimal_conversion, why_not: binary_decimal_conversion covers integer/decimal digit conversion rather than correctly rounded binary-floating-point/decimal-floating-point conversion)
mechanism: Binary64-to-decimal64 conversion prechecks exact cases, selects one of two decimal exponents with a breakpoint table, multiplies the normalized binary coefficient by a tabulated approximation to 2^k/10^f, and rounds in all modes. Decimal64-to-binary64 normalizes the BID coefficient, multiplies by a tabulated approximation to 10^f/2^k, and applies an additional shift before rounding for underflow. Continued-fraction or mediant searches bound hard-to-round cases. # pp.7-9
choices: direction: {binary_to_decimal, decimal_to_binary, both}; scale_factor: {table_multiplier}; exponent_selection: {breakpoint_table}; exact_case_precheck: Bool; hard_case_analysis: {analytic_integer_bound, continued_fraction_search}
results:
| metric | value | unit | technology / device | baseline | condition | page |
| hardest binary64-to-decimal64 case | 2^-115.53 | relative distance | UNKNOWN; 2007 | exact rounding boundary | reported example | p.8 |
| hardest decimal64-to-binary64 case | 2^-114.62 | relative distance | UNKNOWN; 2007 | exact rounding boundary | reported example | p.8 |
| cvt bid128 to int32 | 127 / 51; 240 / 107; 143 / 92 | clock cycles | D1 / D2 / D3; 2007 | UNKNOWN | maximum / median | p.9 |
| cvt int32 to bid64 | 98 / 9; 167 / 13; 181 / 13 | clock cycles | D1 / D2 / D3; 2007 | UNKNOWN | maximum / median | p.9 |
| cvt int32 to bid128 | 97 / 46; 169 / 84; 182 / 93 | clock cycles | D1 / D2 / D3; 2007 | UNKNOWN | maximum / median | p.9 |
| cvt string to bid128 | 336 / 54; 321 / 133; 391 / 95 | clock cycles | D1 / D2 / D3; 2007 | UNKNOWN | maximum / median | p.9 |
| cvt string to bid64 | 215 / 82; 553 / 81; 332 / 133 | clock cycles | D1 / D2 / D3; 2007 | UNKNOWN | maximum / median | p.9 |
| cvt bid128 to string | 345 / 103; 812 / 201; 509 / 198 | clock cycles | D1 / D2 / D3; 2007 | UNKNOWN | maximum / median | p.9 |
| cvt bid64 to string | 130 / 84; 249 / 152; 281 / 155 | clock cycles | D1 / D2 / D3; 2007 | UNKNOWN | maximum / median | p.9 |
evidence: §5, pp.7-9; Table 2, p.9

## space_gaps
* decimal_fp_addition lacks a BID software alignment value based on binary-integer multiplication by 10^(e1-e2). # p.5
* The decimal division vocabulary lacks a BID software family based on scaled multiprecision integer divide/remainder with remainder-based rounding. # p.6
* The decimal square-root vocabulary lacks a BID software family based on a 2·p-digit integer square root and long-integer multiplication for rounding. # pp.6-7

## open_questions
* The document does not state the implementation language or exact compiler/configuration used for the performance measurements.
* The document does not isolate the cycle cost of reciprocal rounding from the complete arithmetic-operation latencies.
* The document does not provide the omitted multiprecision integer-division or integer-square-root implementation details.
