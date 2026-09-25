---
handle: combet1965
citation: M. Combet, H. Van Zonneveld, L. Verbeek, "Computation of the Base Two Logarithm of Binary Numbers", IEEE Transactions on Electronic Computers, vol. EC-14, no. 6, pp. 863-867, 1965
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_SFU]
formats: [binary_7_to_22_bit]
authority: incremental
pages_read: 863-867 / 5 pages
---

## summary
The paper improves Mitchell’s binary-logarithm approximation with a four-segment piecewise-linear correction, reducing the theoretical error range from 0.086 to 0.014 (p.865). A sequential shift/add computer realizes the approximation with a seven-bit mantisse and obtains an error range of 0.019 including round-off (p.865).

## families
### logarithmic_converters  (role: extends)
mechanism: The circuit writes \(N=2^k(1+x)\), obtains characteristic \(k\) by shifting the leftmost 1-bit while counting, and uses the remaining bits as \(x\). Four region-dependent corrections approximate \(L(1+x)\). Comparisons select the correction, and sequential shifted additions apply coefficients whose denominators are powers of two. The constructed unit computes logarithms only; product/quotient use is proposed but not analyzed (pp.864-867).
choices:
  correction: pwl_correction   # p.864
  regions: 4   # p.864
  lns_full_alu: false   # p.863
new_choices:
  characteristic_extraction: sequential_left_shift_and_count — obtains k while normalizing N to x   # p.865
  correction_execution: sequential_shift_add — applies power-of-two correction terms bit-serially   # p.866
slots:
  none
parameters: input length 7 to 22 bits; mantisse precision 7 bits; 4 correction regions; register R 22 bits; counter C 4 bits; maximal shifts 15   # pp.865, 867
results:
| metric | value | unit | technology / device | baseline | condition | page |
| computation time, minimum | 0.5 | ms | UNKNOWN (1965) | none | depends on input length and correction type | p.867 |
| computation time, maximum | 0.6 | ms | UNKNOWN (1965) | none | depends on input length and correction type | p.867 |
| clock frequency | 100 | kc/s | UNKNOWN (1965) | none | constructed computer | p.867 |
| flip-flops | 74 | flip-flops | UNKNOWN (1965) | none | 32 for the internal program and 42 for computation | p.867 |
| AND gates | 103 | gates | UNKNOWN (1965) | none | constructed computer | p.867 |
| OR gates | 4 | gates | UNKNOWN (1965) | none | constructed computer | p.867 |
| pulse shaping amplifiers | 32 | amplifiers | UNKNOWN (1965) | none | constructed computer | p.867 |
| emitter-followers | 20 | emitter-followers | UNKNOWN (1965) | none | constructed computer | p.867 |
errors_and_checks: The constructed seven-bit implementation has maximal total error 0.013 at x=0.625 and x=0.687, maximal negative error -0.006 at x=0.250, and error range 0.019; no error-detection mechanism is reported.   # p.865
conditions: The circuit serves as a basic part of a nuclear-reactor digital period-meter (p.867). Product or quotient generation requires an additional error analysis that the paper does not provide (p.863). More segments reduce approximation error but increase hardware and computation time (p.865).
evidence: Equations (1)-(3) and Figs. 1-4, pp.863-865; Sections II-A-II-D and Figs. 5-10, pp.865-867; Section III, p.867.

### pwl  (role: proposes)
mechanism: The approximation divides \(0<x<1\) into four equal intervals and replaces \(L(1+x)\) with four straight-line expressions. The corrections are \(5x/16\), \(5/64\), \(\bar{x}/8+3/128\), and \(\bar{x}/4\), added to x in successive intervals. Power-of-two terms permit implementation by shifts, complements, and additions (pp.864-866).
choices:
  segments: 4 [outside domain]   # p.864
  segmentation: uniform   # p.864
  x_frac_bits: 7 [outside domain]   # p.865
  slope_encoding: signed_po2_pair   # p.866
new_choices:
  none
slots:
  evaluator: shift_add_coeff   # p.866
  segmenter: uniform_high_bit_decode   # p.867
parameters: q=2; interval length \(2^{-q}\); 4 segments; first 7 bits of x used; correction constants resolved through \(1/128\)   # pp.864-866
results:
| metric | value | unit | technology / device | baseline | condition | page |
| maximal positive approximation error | 0.008 | log2 value | UNKNOWN (1965) | Mitchell LA1 | x=0.44, excluding finite-register round-off | p.865 |
| maximal negative approximation error | -0.006 | log2 value | UNKNOWN (1965) | Mitchell LA1 | x=0.25, excluding finite-register round-off | p.865 |
| approximation error range | 0.014 | log2 value | UNKNOWN (1965) | Mitchell LA1 error range 0.086 | four segments, excluding finite-register round-off | p.865 |
| error-range improvement | about 6 | factor | UNKNOWN (1965) | Mitchell LA1 error range 0.086 | four-segment approximation | p.865 |
| projected error-range reduction | roughly half | error range | UNKNOWN (1965) | four-segment approximation | eight segments instead of four | p.865 |
errors_and_checks: The four-segment mathematical approximation has error range 0.014, from -0.006 to 0.008. Seven-bit storage can reduce the computed mantisse by at most \(2^{-7}=0.0078\). No fault checks or false-alarm behavior are reported.   # p.865
conditions: Four equal segments provide the reported factor-six improvement over LA1 (p.865). Eight segments roughly halve the error range but require more decision/correction hardware and more computation time (p.865). The coefficients use integer numerators and power-of-two denominators for binary implementation (p.864).
evidence: Piecewise approximation and Fig. 3, p.864; error curves and implementation-rounding simulation in Fig. 4, p.865; correction realization and Table II, pp.866-867.

## new_families
none

## space_gaps
* `pwl.segments` excludes the demonstrated value 4.   # p.864
* `pwl.x_frac_bits` excludes the demonstrated seven-bit mantisse implementation.   # p.865
* `pwl` lacks a range-reduction option for leading-one normalization \(N=2^k(1+x)\) with shift-count characteristic extraction.   # pp.864-865

## open_questions
* The paper does not report a technology node or fabrication process.
* The paper does not analyze the product/quotient errors that would result from using the logarithm unit for arithmetic.   # p.863
