---
handle: mahalingam2006
citation: V. Mahalingam, N. Ranganathan, "Improving Accuracy in Mitchell's Logarithmic Multiplication Using Operand Decomposition", IEEE Transactions on Computers, vol. 55, no. 12, pp. 1523-1535, 2006
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [binary_fixed_point, int32]
authority: incremental
pages_read: 1523-1535 / 13
---

## summary
Operand decomposition preprocesses two binary multiplicands into four operands whose two products sum to the original product, which reduces the average error of Mitchell logarithmic multiplication (pp.1527-1528). The method also combines with divided approximation/table correction/Mitchell error correction and is evaluated through random/biased inputs, Gaussian smoothing, and a 32-bit CMOS implementation (pp.1529-1534).

## families
### logarithmic_mitchell  (role: extends)
mechanism: Inputs X and Y are decomposed into A, B, C, and D using bitwise OR/XOR/complement equations, with X × Y = (C × D) + (A × B). Two Mitchell logarithmic multiplications compute the decomposed products, which a binary adder combines. The decomposition lowers the probability of a 1 in the decomposed operands from 1/2 to 1/4 and reduces mantissa-to-integer carryovers during logarithm addition (pp.1527-1528).
choices:
  correction_scheme: operand_decomposition   # pp.1527-1528
new_choices:
  decomposed_product_schedule: {parallel, sequential} — whether the two decomposed multiplications use parallel hardware or reuse one datapath   # p.1534
  secondary_correction: {none, divided_approximation, table_of_correction_values, Mitchell_error_correction} — the correction method combined with operand decomposition   # pp.1528-1530
slots:
  antilog_shifter: UNKNOWN   # pp.1527-1528
parameters: n-bit X/Y and four n-bit decomposed operands; parallel 32-bit implementation with four leading-one detectors, four 32 × 5-bit ROMs, six logarithmic shifters, three ripple-carry adders, and a zero detector   # pp.1527,1534
results:
| metric | value | unit | technology / device | baseline | condition | page |
| average-error reduction | 44.7 | percent | UNKNOWN / 2006 | Mitchell algorithm | average over experimental inputs | p.1523 |
| chip-area dimensions | 3,800 × 1,050 | λ × λ | 0.7 μm CMOS / 2006 | 4,320λ × 1,260λ 32-bit fixed-point array multiplier | 32-bit parallel OD-Mitchell implementation | p.1534 |
| power | 85 | μW | 0.7 μm CMOS / 2006 | 30 percent of standard 32-bit fixed-point array multiplier power | 100 MHz, 1.08 V | p.1534 |
| correction-hardware overhead | less than 2 | percent | 0.7 μm CMOS / 2006 | Mitchell logarithmic multiplier | two-region divided approximation using three mantissa bits | p.1534 |
| correction-hardware overhead | 50 | percent | 0.7 μm CMOS / 2006 | Mitchell logarithmic multiplier | TCV or MEC correction | p.1534 |
| sequential area increase | less than 4 | percent of whole unit | 0.7 μm CMOS / 2006 | Mitchell multiplier | sequential reuse of the decomposed multiplications | p.1534 |
errors_and_checks: Multiplication error is EP = ((TV − LV)/TV) × 100, and AEP is the arithmetic mean of EP over N multiplications. A zero detector forces zero output when either input is zero. No fault-detection contract is reported.   # pp.1525,1531
conditions: The parallel OD implementation almost doubles area/power relative to the original Mitchell multiplier, while pipeline-stage delay remains determined by logarithm approximation (p.1534). The sequential implementation approximately doubles delay but adds less than 4 percent area for decomposition logic (p.1534).
evidence: Section 3; Tables 2-5; Figs. 5-8; Section 4.4 (pp.1527-1534)

### logarithmic  (role: extends)
mechanism: The base algorithm approximates log2(1+x) by x, adds the two approximate logarithms, and forms the antilogarithm through shifting. Operand decomposition reduces carryovers in the fractional-logarithm sum without adding a correction term. OD-DA applies two-region divided approximation, OD-TCV adds one of 64 table values to each logarithm sum, and OD-MEC applies Mitchell’s product correction to each decomposed multiplication (pp.1525-1530).
choices:
  base: mitchell   # pp.1525-1526
  correction: operand_decomposition   # pp.1527-1528
  mantissa_adder: exact   # pp.1527-1528
new_choices:
  correction_composition: {OD_only, OD_DA, OD_TCV, OD_MEC} — operand decomposition can precede several independently defined correction methods   # pp.1528-1530
slots:
  log_adder: ripple_carry   # p.1534
parameters: 32-bit primary experiment; 1,000/10,000/100,000 random vectors; two-region OD-DA using three mantissa bits; 64-entry OD-TCV table   # pp.1529-1531,1534
results:
| metric | value | unit | technology / device | baseline | condition | page |
| average error percentage | 2.1 | percent | UNKNOWN / 2006 | Mitchell 3.88 percent | 32-bit operands, 100,000 random multiplications | p.1531 |
| products below error threshold | 45 | percent of products | UNKNOWN / 2006 | Mitchell 21 percent | error below 1 percent, 100,000 multiplications | p.1531 |
| average error percentage | 1.9 | percent | UNKNOWN / 2006 | Mitchell 3.4 percent | inputs biased toward 1 bits | p.1532 |
| average error percentage | 1.8 | percent | UNKNOWN / 2006 | Mitchell 3.3 percent | inputs biased toward 0 bits | p.1532 |
| average error percentage | 0.10 to 0.17 | percent | UNKNOWN / 2006 | divided approximation 2.45 to 2.71 percent | OD-DA across evaluated widths | p.1532 |
| average error percentage | about 0.01 | percent | UNKNOWN / 2006 | TCV without OD | OD-TCV | p.1530 |
| average error percentage | 0.02 | percent | 0.7 μm CMOS / 2006 | UNKNOWN | OD-TCV hardware comparison | p.1534 |
| average error percentage | 0.03 | percent | 0.7 μm CMOS / 2006 | UNKNOWN | OD-MEC hardware comparison | p.1534 |
| products below error threshold | 99 | percent of products | UNKNOWN / 2006 | Mitchell error correction without OD | OD-MEC error below 1 percent | p.1530 |
errors_and_checks: Basic Mitchell multiplication has an approximately 11.1 percent maximum error and approximately 3.8 percent average error, with positive error that can compound across successive multiplications. Operand decomposition improves average error but does not generally reduce maximum possible error. No fault model/checking mechanism is evaluated.   # pp.1524-1526,1530
conditions: The method targets DSP applications that tolerate multiplication error (pp.1523-1524). Small convolution weights can make one decomposed operand zero, so only one Mitchell multiplication is required (p.1532). OD-DA provides lower correction hardware overhead than OD-TCV/OD-MEC, while OD-TCV/OD-MEC provide lower reported average error (p.1534).
evidence: Sections 2.2, 3.1-3.4, and 4.1-4.4; Tables 2-8; Figs. 6-17 (pp.1525-1534)

## new_families
none

## space_gaps
* logarithmic_mitchell lacks a decomposed-product scheduling choice for the parallel/sequential area-delay tradeoff (p.1534).
* logarithmic and logarithmic_mitchell model one correction value but not OD combined with divided approximation/TCV/MEC (pp.1528-1530).

## open_questions
* Table 7 contains exact width-by-width AEP values, but the supplied table image does not expose its cells as text; the merge pass must not infer those values.
* OD-TCV average error is stated as about 0.01 percent on p.1530 and 0.02 percent on p.1534; the document does not reconcile the difference.
* The document does not specify whether the evaluated binary operands are signed or unsigned.
