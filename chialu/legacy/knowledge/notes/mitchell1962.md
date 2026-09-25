---
handle: mitchell1962
citation: J. N. Mitchell, "Computer Multiplication and Division Using Binary Logarithms", IRE Transactions on Electronic Computers, vol. EC-11, no. 4, pp. 512-517, 1962
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [binary_integer]
authority: landmark
pages_read: 512-517 / 6
---

## summary
The document proposes approximate binary multiplication/division using shift-generated binary logarithms followed by one addition/subtraction and an inverse shift operation (pp.512-514). The document derives maximum multiplication/division errors and reduces the multiplication error through a recursive correction operation (pp.514-517).

## families
### logarithmic_mitchell  (role: proposes)
mechanism: A leading-one position supplies the logarithm characteristic, while the bits below that one are interpreted directly as the fractional logarithm. Multiplication adds two approximate logarithms, division subtracts them, and decoding the resulting characteristic/fraction reconstructs the result. Multiplication can add a scaled approximation of x1x2, or x1'x2' after a mantissa carry, as a correction term. (pp.512-517)
choices:
  correction_scheme: iterative_residual [outside domain]   # pp.516-517
new_choices:
  log_approximation: straight_line_characteristic_plus_fraction — selects the approximation used to obtain the operand logarithm without a table lookup   # pp.512-514
slots:
  antilog_shifter: barrel_mux_tree   # pp.513-514
parameters: The organization example uses 8-bit A/B words and 3-bit characteristic counters; the general description uses an n+1-bit machine word.   # pp.512-513
results:
| metric | value | unit | technology / device | baseline | condition | page |
| maximum logarithm approximation error | 0.08639 | absolute logarithm value | UNKNOWN, 1962 | exact lg N | 0<x<1 | p.514 |
| maximum multiplication error | -11.1 | per cent | UNKNOWN, 1962 | exact product | x1=x2=1/2 | pp.515-516 |
| maximum corrected multiplication error | -2.8 | per cent | UNKNOWN, 1962 | exact product | double logarithmic operation | p.517 |
| maximum division error | 12.5 | per cent | UNKNOWN, 1962 | exact quotient | no-borrow case x1→1, x2=1/2; borrow case x1=0, x2=1/2 | p.516 |
errors_and_checks: Multiplication error ranges from zero to -11.1 per cent, so the approximate product is low. Division error ranges from zero to 12.5 per cent, so the approximate quotient is high. A double multiplication operation limits the reported maximum error to -2.8 per cent. (pp.515-517)
conditions: The scheme avoids logarithm tables and reduces multiplication/division to shifts plus one addition/subtraction, which targets applications that tolerate approximation (pp.512-514). Successive operations of the same type can compound errors because each operation's error has the same sign (p.516). Additional correction operations can reduce multiplication error further, but too many can remove the advantage over iterative multiplication (p.517).
evidence: Sections II-IV, Figs. 2-4, and (4)-(52), pp.512-517.

### logarithmic  (role: proposes)
mechanism: The multiplier replaces each operand with a piecewise-linear binary-log representation k+x. It adds the representations and reconstructs the product by shifting. A second logarithmic multiplication approximates the omitted x1x2 or complemented-mantissa product term and adds the scaled correction to the first result. (pp.514-517)
choices:
  base: mitchell   # pp.512-514
  correction: iterative_residual   # pp.516-517
  iterations: 2   # p.517
new_choices:
  log_approximation: straight_line_characteristic_plus_fraction — distinguishes the table-free interpolation from table/PWL alternatives   # pp.512-514
slots:
  log_adder: UNKNOWN
parameters: One base operation gives at most -11.1 per cent error; the demonstrated double operation gives at most -2.8 per cent error.   # pp.516-517
results:
| metric | value | unit | technology / device | baseline | condition | page |
| maximum multiplication error | -11.1 | per cent | UNKNOWN, 1962 | exact product | uncorrected operation | pp.515-516 |
| maximum multiplication error | -2.8 | per cent | UNKNOWN, 1962 | exact product | double operation with recursively approximated correction term | p.517 |
errors_and_checks: The uncorrected error is one-sided and reaches -11.1 per cent; the double-operation correction reduces the maximum magnitude to 2.8 per cent.   # pp.516-517
conditions: Higher-order correction can reduce the error arbitrarily, subject to the point where its added operations defeat the intended speed advantage.   # p.517
evidence: Section IV and (45)-(52), pp.516-517.

### approximate_functional  (role: proposes)
mechanism: Division forms approximate operand logarithms from leading-one positions and remaining fractional bits, subtracts the divisor logarithm from the dividend logarithm, and reconstructs the quotient from the resulting characteristic/fraction. The document finds no comparably simple division correction and mentions interval-indexed stored correction factors only as a possible method. (pp.513-517)
choices:
  method: log_subtract_uncorrected [outside domain]   # pp.513-517
  bias_correction: false   # p.517
new_choices:
  correction_lookup: none_or_interval_factors — selects no correction or operand-interval correction factors requiring comparisons and memory lookups   # p.517
slots:
  none
parameters: The worked examples divide 3216 by 25 and 15 by 3; no general operand width is fixed.   # pp.513-514
results:
| metric | value | unit | technology / device | baseline | condition | page |
| example division error | 10 | per cent | UNKNOWN, 1962 | exact quotient 5 | 15 divided by 3 produces 5.5 | p.513 |
| maximum division error | 12.5 | per cent | UNKNOWN, 1962 | exact quotient | derived extrema across borrow/no-borrow cases | p.516 |
errors_and_checks: Division error is always positive, reaches 12.5 per cent, and has no implemented correction scheme.   # pp.516-517
conditions: Stored correction factors could reduce division error, but the required operand comparisons and memory lookups might defeat the purpose of logarithmic arithmetic.   # p.517
evidence: Sections II-III/V and (19)-(44), pp.513-517.

## new_families
none

## space_gaps
* logarithmic_mitchell correction_scheme lacks the recursive approximation of x1x2/x1'x2' demonstrated by the document.   # pp.516-517
* approximate_functional method lacks an uncorrected binary-log subtraction value.   # pp.513-517

## open_questions
* The document does not specify a technology, circuit implementation, timing, area, power, or manufactured device.
* The document does not define a fixed operand width beyond the 8-bit organization example.
