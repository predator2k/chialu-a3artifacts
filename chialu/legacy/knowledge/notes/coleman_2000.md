---
handle: coleman_2000
citation: J. N. Coleman, E. I. Chester, C. I. Softley, J. Kadlec, "Arithmetic on the European Logarithmic Microprocessor", IEEE Transactions on Computers, vol. 49, no. 7, pp. 702-715, 2000
actual_citation: same
status: ok
kind: paper
unit_classes: [other]
formats: [lns32, lns20, fp32, fp20, fxp32]
authority: landmark
pages_read: 702-715 / 14
---

## summary
The document presents a logarithmic-number-system ALU whose addition/subtraction uses first-order Taylor interpolation with a table-scaled error correction computed in parallel. The 32-bit ALU provides add/subtract/multiply/divide paths, while a range shifter handles difficult near-equal subtractions. Simulated case studies report same-width floating-point accuracy limits for add/subtract and overall speed/accuracy gains from exact logarithmic multiplication/division.

## families
### logarithmic_converters  (role: proposes)
mechanism: Real values are represented by fixed-point base-2 logarithms, so multiplication/division become fixed-point addition/subtraction and square root becomes a right shift plus rounding. Addition/subtraction evaluates \(F(r)=\log_2(1\pm2^r)\) by linear interpolation. A stored maximum interval error \(E(n)\) scales a template \(P(c,\delta)\), and the resulting correction is accumulated through a carry-save stage. A range shifter transforms subtractions with \(-0.5<r<0\) before interpolation. (pp. 702, 705-708)
choices:
  correction: table_scaled_interpolation_error [outside domain]   # pp. 705-706
  regions: 6   # p.707
  lns_full_alu: true   # p.708
new_choices:
  add_sub_evaluation: first_order_taylor_with_scaled_error_template — selects the nonlinear LNS addition/subtraction evaluator   # pp. 705-706
  close_subtraction_handling: range_shifter — transforms operands before interpolation when \(-0.5<r<0\)   # pp. 707-708
  error_template_scope: shared_add_sub — one subtraction-derived \(P\) table also corrects addition   # p.707
slots:
  none
parameters: 32-bit LNS uses an 8-bit integer part, 23-bit fraction, sign, and 4 internal guard bits; 20-bit LNS uses an 8-bit integer part and 11-bit fraction. The 32-bit range shifter covers \(-0.5<r<0\).   # pp. 704, 707
results:
| metric | value | unit | technology / device | baseline | condition | page |
| ROM storage | 322 | kbits | UNKNOWN / 2000 | none | 32-bit ALU | p.714 |
| ROM storage | 11 | kbits | UNKNOWN / 2000 | none | 20-bit ALU | p.714 |
| maximum add/subtract error | within 0.5 | LSB-relative arithmetic error | software simulation / 2000 | same-width FLP limit of 0.5 | 32-bit and 20-bit designs | p.708 |
| average add/subtract latency | about 31 | ns | 0.7µ two-level-metal standard-cell / 2000 | FLP unit | equal additions/subtractions; practical range-shifter-use assumption | p.709 |
| average subtraction latency | about 35 | ns | 0.7µ two-level-metal standard-cell / 2000 | FLP unit | range shifter used in somewhat less than half of subtractions | p.709 |
| execution time | about 64 | percent of FLP time | 0.7µ two-level-metal standard-cell / 2000 | 32-bit FLP | roughly equal additions and multiplications | p.709 |
| speed parity point | twice FLP speed | ratio | 0.7µ two-level-metal standard-cell / 2000 | 32-bit FLP | add/multiply ratio about 40/60 percent | p.709 |
| RLS execution time | 0.46 (speedup 2.2) | × FLP time | modeled 0.7µ ALUs / 2000 | 32-bit FLP | 1,000 input samples | p.712 |
| Laguerre execution time | 0.41 (speedup 2.5) | × FLP time | modeled 0.7µ ALUs / 2000 | 32-bit FLP | 1,000 trials at \(n=10\) | p.713 |
| Torus execution time | 0.68 (speedup 1.5) | × FLP time | modeled 0.7µ ALUs / 2000 | 32-bit FLP | graphics case study | p.714 |
| case-study accuracy gain | 0.5 to 2.5 | bits | software simulation / 2000 | same-width FLP | RLS/Laguerre/Torus | p.714 |
| case-study speed gain | 1.5 to 2.5 | times | modeled 0.7µ ALUs / 2000 | same-width FLP | RLS/Laguerre/Torus | p.714 |
errors_and_checks: Addition/subtraction maintains maximum relative arithmetic error within the same-width FLP limit of 0.5, although a small opposite bias remains between addition and subtraction. LNS multiplication/division introduce no rounding error. No fault-detection mechanism is reported.   # pp. 704, 708
conditions: LNS subtraction is less accurate than FLP when operands are nearly equal because FLP subtraction is exact in that case. LNS gains depend on the add/subtract-to-multiply/divide ratio, operand signs, and dynamic range. Physical delays come from unrouted 0.7µ standard-cell designs and assume 5 ns asynchronous-ROM access.   # pp. 709-710
evidence: Sections 2.1-2.5, 3-5; Figs. 2-10; Tables 1-7; pp. 704-714.

### lut_plus_poly  (role: instantiates)
mechanism: The evaluator partitions \(r\) at powers of two and divides each segment into uniform intervals. The interval address selects stored \(F\), derivative \(D\), and maximum error \(E\); low-order bits form \(\delta\). The unit computes \(F(-n\Delta)-\delta D(-n\Delta)\) and simultaneously computes \(E(n)P(c,\delta)\). Multiplier low-order bits are truncated, final carry-propagate stages are omitted, and sum/carry vectors enter an enlarged carry-save tree before the final rounded result. (pp. 705-707)
choices:
  degree: 1   # pp. 703, 705
  index_bits: 8   # p.707
  basis: taylor   # pp. 703, 705
  coeff_encoding: per_coeff_width   # pp. 706-707
  guard_bits: 4   # p.707
  breakpoint_placement: power_of_two_segmented_uniform [outside domain]   # pp. 705, 707
  multiplier_shape: truncated   # p.707
new_choices:
  error_correction: scaled_template_table — multiplies interval error \(E(n)\) by a stored normalized error curve \(P(c,\delta)\)   # pp. 705-706
slots:
  segmenter: hierarchical   # pp. 705, 707
parameters: For the 32-bit implementation, F/D/E contain 256 words per segment, P contains 1,024 words, and F1/F2 contain 2 kwords each. The evaluated 40-bit basis design uses seven segments, 512-word F/D/E tables, and a 4-kword P table.   # pp. 705-707
results:
| metric | value | unit | technology / device | baseline | condition | page |
| maximum interpolation error | 3.9 | LSB | software simulation / 2000 | 5,022 LSB without correction | 512-word F/D/E tables and 4-kword P table | p.706 |
| error reduction | over 3 orders of magnitude | ratio | software simulation / 2000 | uncorrected interpolation | 512-word F/D/E tables and 4-kword P table | p.706 |
| total table storage | 417,792 | bits | UNKNOWN / 2000 | 229,376 bits for F/D alone | 512 intervals per segment and P = 4K | p.706 |
errors_and_checks: The correction cannot be exact; even with many intervals a residual error of about 2 remains. Product truncation has negligible simulated effect on accuracy.   # pp. 706-707
conditions: Doubling the uncorrected interval count reduces maximum error by a factor of 4. With small interval counts, doubling the P-table size halves maximum error. Computing P near \(c=-4\) gives a better fit than \(c=0\), where error rises from 3.9 to 5.2 in the stated example.   # pp. 705-706
evidence: Sections 2.3-2.5; Figs. 2-5; Tables 1-3; pp. 705-708.

## new_families
none

## space_gaps
* `logarithmic_converters.correction` needs a `table_scaled_interpolation_error` value for the \(E(n)P(c,\delta)\) correction.   # pp. 705-706
* `logarithmic_converters` needs choices for close-subtraction transformation and sharing one correction template between addition/subtraction.   # p.707
* `lut_plus_poly.breakpoint_placement` needs a value for power-of-two segments containing uniform subintervals.   # pp. 705, 707

## open_questions
* Exact numeric entries in Tables 1-4 are unavailable in the supplied text extraction, so the detailed error/storage/delay rows must not be reconstructed from surrounding prose.
