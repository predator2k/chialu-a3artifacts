---
handle: nicoud_1971
citation: Nicoud, "Iterative Arrays for Radix Conversion", IEEE Transactions on Computers, 1971
actual_citation: same
status: ok
kind: paper
unit_classes: [other]
formats: [binary, bcd, biquinary]
authority: landmark
pages_read: 1479-1489 / 11 pages
---

## summary
The paper derives four integer and four fractional radix-conversion algorithms and maps the digit-level recurrence to combinational iterative arrays. Two array orientations support binary-to-decimal/decimal-to-binary conversion of integers and fractions, with optimized BCD/biquinary cells for bipolar or MOS implementation. # p.1479, p.1481-1488

## families
### binary_decimal_conversion  (role: extends)
mechanism: Algorithm 3 decomposes conversion into cells satisfying `a+q+b+=b*p+a`, where `a,a+` are p-digits and `b,b+` are q-digits. For binary/decimal conversion, a BD cell satisfies `b+*10+d+=d*2+b`, while a DB cell satisfies `d+*2+b+=b*10+d`. Two arrays with changed boundary placement cover both conversion directions for integers and fractions. Cells that only implement a positional shift or whose weight exceeds the largest input can be suppressed. # p.1481-1486
choices:
  direction: both   # p.1485
  structure: combinational_cell_array   # p.1483-1486
new_choices:
  digit_code: bcd8421 / 1-2-4-5 / biquinary — decimal-digit encoding changes cell complexity and propagation delay   # p.1485-1488
  polarity_alternation: true — alternating true-input/complementary-output cells with their duals avoids per-cell output inverters   # p.1487-1488
slots:
  none
parameters: General radices p/q; array dimensions chosen so `q^n < p^(m+1)-1 < q^(n+1)` for the largest m+1-digit integer; evaluated examples include 16-bit and 32-bit binary integers. # p.1483, p.1486-1487
results:
| metric | value | unit | technology / device | baseline | condition | page |
| minimum array size | 33 | cells | technology UNKNOWN; 1971 | 80-cell complete array | binary-to-decimal conversion of integers up to 16 bits | p.1486 |
| propagation delay | 13 | cell delays | technology UNKNOWN; 1971 | none | 33-cell array for integers up to 16 bits | p.1486 |
| B-BCD cell resistors | 5 | MOS resistors | MOS; node UNKNOWN; 1971 | none | decomposed equations (4) | p.1487 |
| B-BCD cell transistors | 20 | MOS transistors | MOS; node UNKNOWN; 1971 | none | decomposed equations (4) | p.1487 |
| B-BCD cell output delay | not more than 2 | single-gate propagation delays | MOS; node UNKNOWN; 1971 | none | decomposed cell | p.1487 |
| maximum conversion time | less than 12 | μs | MOS; node UNKNOWN; 1971 | none | 32-bit binary-to-decimal array, gate propagation delay 0.2 μs | p.1487 |
| complete array size | 320 | cells | MOS; node UNKNOWN; 1971 | none | corresponding 32-bit binary-to-decimal array | p.1487 |
| complete array complexity | about 8000 | MOS transistors | MOS; node UNKNOWN; 1971 | none | corresponding complete array | p.1487 |
| complete array connections | about 150 | connections | MOS; node UNKNOWN; 1971 | none | corresponding complete array | p.1487 |
| conversion time with serial registers | up to 50 | μs | MOS; node UNKNOWN; 1971 | parallel array without transfer time | shift rate 2 MHz, including transfers | p.1487 |
| package pins with serial registers | less than 16 | pins | MOS; node UNKNOWN; 1971 | parallel input/output array | serial shift registers included | p.1487 |
| BCD-B cell resistors | 6 | MOS resistors | MOS; node UNKNOWN; 1971 | none | equations (7) | p.1488 |
| BCD-B cell transistors | 19 | MOS transistors | MOS; node UNKNOWN; 1971 | none | equations (7) | p.1488 |
| BCD-B cell propagation delay | 2 | units | MOS; node UNKNOWN; 1971 | none | equations (7) | p.1488 |
| transistor reduction | 5 to 20 | percent | MOS; node UNKNOWN; 1971 | BCD-B network using equations (7) | Guild positional-shift array, two through ten decimal digits | p.1488 |
| biquinary-array delay | n | gate delays | bipolar or MOS; node UNKNOWN; 1971 | BCD-coded cells | conversion of an n-bit number | p.1488 |
errors_and_checks: Integer conversion is exact when the array is sized for the input range. Fractional conversion truncated at level `(-k)` has maximum error `p^-k`; applying the rounding term `p^-k*q^l/2` gives zero mean error and minimum variance. Suppressing additional cells increases error variance. # p.1484
conditions: Iterative arrays are especially suitable for small numbers. Couleur sequential systems have the best plotted quality factor above 24 digits, while ROM converters are of little interest above ten digits. Serial shift registers reduce pins but make the advantage over sequential methods insignificant. Conversion in both directions cannot occur simultaneously for real numbers because fractions may recur. # p.1484, p.1487, p.1489
evidence: Algorithms 1-4 and Fig. 1, p.1480-1483; integer/fraction arrays in Figs. 2-5, p.1483-1484; binary/decimal cells and arrays in Figs. 6-11 and Tables I-A/I-B/II, p.1485-1488; comparison in Fig. 12, p.1489.

## new_families
### iterative_radix_conversion  (domain: decimal misc, closest: binary_decimal_conversion, why_not: binary_decimal_conversion limits the mechanism to binary/decimal operands, while the recurrence accepts arbitrary positive radices p/q and digit codes)
mechanism: A p-number is converted to radix q through a two-dimensional combinational array of cells satisfying `a+q+b+=b*p+a`. The same cell can simulate a row that multiplies a q-number by p and adds a p-digit or a column that divides a p-number by q. Integer and fractional conversions use the same recurrence with different boundary conditions. Array cells can use any encoding of the p-digits and q-digits, and cells outside the required numerical weight range can be removed. # p.1481-1484
choices: calculation_form: {q_radix_horner, p_radix_repeated_division, digit_cell_recurrence}; operand_class: {integer, fraction, fixed_point_real}; radix_pair: positive_integer_p_q; cell_pruning: {none, weight_bounded}; rounding_term: {none, half_unit_term}
results:
| metric | value | unit | technology / device | baseline | condition | page |
| array dimension approximation | `n > m(log p)/(log q)` | relation | UNKNOWN; 1971 | complete rectangular array | largest input has m p-digits | p.1483 |
| fractional truncation error | `p^-k` | maximum error | UNKNOWN; 1971 | unlimited recurring fraction | conversion interrupted at level `(-k)` | p.1484 |
evidence: Sections III-VII, Algorithms 1-4, and Figs. 1-5, p.1480-1484.

## space_gaps
* `binary_decimal_conversion` lacks a `digit_code` choice for BCD8421/1-2-4-5/biquinary implementations, whose cell complexity and delay differ. # p.1485-1488
* The vocabulary lacks a general arbitrary-p/arbitrary-q iterative-array conversion family. # p.1480-1484

## open_questions
* Fig. 12 plots complexity/speed/quality curves without tabulated values, so exact numerical comparisons among counter/sequential/iterative-array/ROM converters remain UNKNOWN. # p.1489
