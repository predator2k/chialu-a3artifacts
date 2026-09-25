---
handle: dedinechin_2010
citation: F. de Dinechin, B. Pasca, "Floating-Point Exponential Functions for DSP-Enabled FPGAs", International Conference on Field-Programmable Technology (FPT), pp. 110-117, 2010
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_SFU]
formats: [custom_float_wE_wF, fp32, fp64, extended_precision, quadruple_precision]
authority: incremental
pages_read: 8 / 8
---

## summary
The document proposes a parameterized, fully pipelined floating-point exponential generator for DSP-enabled FPGAs. The architecture combines relaxed range reduction, a table for \(e^A\), and either a second table or piecewise polynomial approximation for the residual, while guaranteeing faithful rounding with three guard bits. Implementations cover single through quadruple precision on Xilinx and Altera devices. # p.110, pp.112-117

## families
### range_reduction  (role: extends)
mechanism: The input is converted to fixed point, then reduced as \(X \approx E\log 2+Y\), where \(E\) is a relaxed approximation to \(\langle X/\log 2\rangle\). The relaxed computation only has to ensure \(Y\in[-1/2,1/2)\). Chunked KCM tables compute multiplication by \(1/\log 2\) and \(\log 2\); the latter stores independently rounded partial products and embeds the final rounding offset in the first table. # pp.111-114
choices:
  method: relaxed_kcm_log2_reduction [outside domain]   # pp.112-114
  split_constant_terms: UNKNOWN
  reduction_type: multiplicative   # p.110
  worst_case_bound_proven: true   # pp.112-114
new_choices:
  quotient_relaxation: bounded_error — \(E\) may be off by one if the resulting \(Y\) remains in \([-1/2,1/2)\)   # p.112
  kcm_rounding_embedding: first_table_half_ulp — the first KCM table stores \(KE_0+u/2\), so truncation rounds the final sum   # p.114
slots: none
parameters: fixed-point \(X_{\mathrm{fix}}\) weights \(w_E\) through \(-w_F-g\); \(E\) width \(w_E+1\); \(g=3\); FPGA LUT input size \(\alpha\in\{4..6\}\); KCM \(\gamma=2\) for \(\log 2\), \(\gamma=3\) for \(1/\log 2\)   # pp.112-114
results:
| metric | value | unit | technology / device | baseline | condition | page |
|---|---:|---|---|---|---|---|
| range-reduction product error | <0.1875 | absolute | FPGA, 2010 | exact \(X_{\mathrm{fix}}/\log 2\) | relaxed computation of \(E\) | p.112 |
errors_and_checks: The analysis proves at most one ulp of \(Y\) error from input shifting or \(E\log 2\), with the two cases mutually exclusive. # p.114
conditions: Reduction to \(Y\in[0,1)\) was considered but rejected because guaranteeing \(Y\ge0\) costs more hardware. # p.112
evidence: §II-D, §III-A-B, Fig. 2, pp.112-114

### lut_plus_poly  (role: proposes)
mechanism: The reduced argument is split as \(Y=A+Z\). A table supplies \(e^A\), while the residual uses \(f(Z)=e^Z-Z-1\), obtained from a table at small precision or a generated piecewise polynomial at larger precision. The datapath forms \(e^Z-1=Z+f(Z)\), then reconstructs \(e^Y=e^A+e^A(e^Z-1)\). Normalization tests the most significant bit of \(e^Y\), shifts when needed, and rounds the concatenated exponent/mantissa. # pp.112-115
choices:
  degree: 2; 3   # pp.114-116
  index_bits: 9; 11 [outside domain]; 14 [outside domain]   # pp.114-116
  basis: UNKNOWN
  coeff_encoding: UNKNOWN
  guard_bits: 3   # p.114
  breakpoint_placement: UNKNOWN
  multiplier_shape: truncated   # p.113
new_choices:
  residual_evaluator: dual_table_or_piecewise_polynomial — \(f(Z)\) is tabulated for small precision and polynomially approximated for larger precision   # pp.113-114
  leading_table_reconstruction: \(e^A\times(1+Z+f(Z))\) — a leading-value table is multiplied by the residual reconstruction   # p.113
slots:
  range_reducer: range_reduction [reduction_type=multiplicative]   # pp.111-114
  evaluator: horner   # Fig. 3, p.115
parameters: arbitrary \(w_E,w_F\); user-specified target frequency; \(g=3\); single precision \(k=9\); double precision \(k=9,d=2,512\) intervals; reported configurations include \((w_E,w_F)=(8,23),(10,40),(11,52),(15,64),(15,112)\)   # pp.110, 114-116
results:
| metric | value | unit | technology / device | baseline | condition | page |
|---|---|---|---|---|---|---|
| frequency / latency / logic / DSP / memory | 315 / 10 / 515 ALUTs, 476 Reg. / 2 18-bit elem. / 3 M9K | MHz / cycles / resources | Stratix III EPSL50F484C2, 2010 | Table I literature/Altera rows | (8,23) | p.116 |
| frequency / latency / logic / DSP / memory | 187 / 3 / 670 ALUTs, 187 Reg. / 2 18-bit elem. / 1 M9K | MHz / cycles / resources | Stratix III EPSL50F484C2, 2010 | Table I literature/Altera rows | (8,23) | p.116 |
| frequency / latency / logic / DSP / memory | 334 / 16 / 399 slices / 1 DSP48 / 1 BRAM | MHz / cycles / resources | Virtex-4 XC4VFX100-12-ff1152, 2010 | Table I literature rows | (8,23), \(f_T=330\) | p.116 |
| frequency / latency / logic / DSP / memory | 261 / 8 / 365 slices / 1 DSP48 / 1 BRAM | MHz / cycles / resources | Virtex-4 XC4VFX100-12-ff1152, 2010 | Table I literature rows | (8,23), \(f_T=200\) | p.116 |
| frequency / latency / logic / DSP / memory | 384 / 17 / 561 LUTs, 531 Reg. / 1 DSP48E / 1 BRAM | MHz / cycles / resources | Virtex-5 XC5VFX100T-3-ff1738, 2010 | Table I literature rows | (8,23), \(f_T=380\) | p.116 |
| frequency / latency / logic / DSP / memory | 360 / 9 / 545 LUTs, 231 Reg. / 1 DSP48E / 1 BRAM | MHz / cycles / resources | Virtex-5 XC5VFX100T-3-ff1738, 2010 | Table I literature rows | (8,23), \(f_T=200\) | p.116 |
| frequency / latency / logic / DSP / memory | 493 / 23 / 603 LUTs, 602 Reg. / 1 DSP48E1 / 1 BRAM | MHz / cycles / resources | Virtex-6 XC6VHX380T-3-ff1923, 2010 | Table I literature rows | (8,23), \(f_T=600\) | p.116 |
| frequency / latency / logic / DSP / memory | 179 / 5 / 452 LUTs, 189 Reg. / 1 DSP48E1 / 1 BRAM | MHz / cycles / resources | Virtex-6 XC6VHX380T-3-ff1923, 2010 | Table I literature rows | (8,23), \(f_T=50\) | p.116 |
| frequency / latency / logic / DSP / memory | 310 / 30 / 1377 LUTs, 1141 Reg. / 10 DSP48E / 4 BRAM | MHz / cycles / resources | Virtex-5, 2010 | none | (10,40), \(k=5,d=2\) | p.116 |
| frequency / latency / logic / DSP / memory | 488 / 32 / 1469 LUTs, 1344 Reg. / 10 DSP48E1 / 3 BRAM | MHz / cycles / resources | Virtex-6, 2010 | none | (10,40), \(k=5,d=2\) | p.116 |
| frequency / latency / logic / DSP / memory | 327 / 29 / 1307 ALUTs, 3757 Reg. / 22 18-bit elem. / 10 M9K | MHz / cycles / resources | Stratix III, 2010 | Altera MegaWizard | (11,52) | p.116 |
| frequency / latency / logic / DSP / memory | 310 / 35 / 1867 LUTs, 1456 Reg. / 12 DSP48E / 5 BRAM | MHz / cycles / resources | Virtex-5, 2010 | [9]-[12] | (11,52) | p.116 |
| frequency / latency / logic / DSP / memory | 488 / 38 / 1928 LUTs, 1791 Reg. / 12 DSP48E1 / 5 BRAM | MHz / cycles / resources | Virtex-6, 2010 | [9]-[12] | (11,52) | p.116 |
| frequency / latency / logic / DSP / memory | 486 / 41 / 2894 LUTs, 2539 Reg. / 20 DSP48E1 / 11 BRAM | MHz / cycles / resources | Virtex-6, 2010 | none | (15,64), \(k=11,d=2\) | p.116 |
| frequency / latency / logic / DSP / memory | 395 / 69 / 8071 LUTs, 7725 Reg. / 71 DSP48E1 / 123 BRAM | MHz / cycles / resources | Virtex-6, 2010 | none | (15,112), \(k=14,d=3\) | p.116 |
| projected throughput | over 60 | GDPexp/s | Virtex-6 XC6VSX475T, 2010 | 4 GFPExp/s Intel VML | 168 double-precision cores above 400 MHz; data movement ignored | p.117 |
| projected throughput | in excess of 400 | GSPExp/s | Virtex-6 XC6VSX475T, 2010 | 6 GSPExp/s Intel VML | single precision; data movement ignored | p.117 |
errors_and_checks: The operator is faithfully rounded: error is below one result ulp. The derived \(e^Y\) error is at most 3.5 ulps in the dual-table case and 4 ulps in the polynomial case before the possible one-bit normalization shift; \(g=3\) provides the required final accuracy. Increasing \(g\) increases the percentage of correctly rounded results. # pp.113-114
conditions: A single DSP implements the final multiplication when \(1+w_F+g<17\). Larger precisions use polynomial evaluation and may use truncated multipliers. Degree 2 suffices through double-extended precision. Resource balance depends on \(k\), polynomial degree, FPGA DSP shape, embedded-memory size, and the requested frequency. # pp.113-116
evidence: §II-E, §III-B-F, Figs. 2-4, Table I, pp.113-117

## new_families
none

## space_gaps
* `range_reduction.method` lacks the relaxed \(X/\log 2\) quotient with bounded-remainder KCM implementation used by this architecture. # pp.112-114
* `lut_plus_poly` lacks a choice distinguishing a residual table from a piecewise-polynomial residual evaluator. # pp.113-114
* `lut_plus_poly` lacks the exponential-specific leading-table reconstruction \(e^A\times(1+Z+f(Z))\). # p.113

## open_questions
* The document treats the generic polynomial evaluator as a black box, so the polynomial basis/coefficient encoding/exact interval-addressing rule are not stated.
* The document says truncated multipliers may be used for large precision and were being added to the generic evaluator, so their use in every reported implementation is ambiguous.
