---
handle: tommiska_2003
citation: M. T. Tommiska, "Efficient Digital Implementation of the Sigmoid Function for Reprogrammable Logic", IEE Proceedings - Computers and Digital Techniques, vol. 150, no. 6, pp. 403-411, 2003
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_SFU]
formats: [fixed_point, s2.3, s3.3, s3.6, s3.10, s4.5]
authority: incremental
pages_read: 403-411 / 9 pages
---

## summary
The paper proposes SIG-sigmoid, a combinational bit-level sigmoid approximation for FPGA neural networks, and compares it with four piecewise-linear and one piecewise-quadratic approximation. SIG-sigmoid provides the highest reported quality factors for the tested Altera FPGA implementations (pp.409-410).

## families
### sigmoid_tanh_pwl  (role: compares)
mechanism: The A-law approximation uses seven linear segments whose gradients are powers of two. The Alippi–Storti-Gajani approximation uses integer breakpoints/power-of-two ordinates and addition/shift operations. PLAN reduces four piecewise-linear regions to bit-level gate equations. CRI recursively interpolates between lines without multiplication or division and requires q+1 clock cycles (pp.404-405).
choices:
  approximation: A-law=shift_add_powers_of_two; Alippi–Storti-Gajani=shift_add_powers_of_two; PLAN=pwl_segments; CRI=pwl_segments   # pp.404-405
  segments: A-law=7; PLAN=4; CRI={3, 5, 9, 17} for q={0, 1, 2, 3}   # pp.404-405
  symmetry_folding: true   # pp.403-405
new_choices:
  recursion_level: Int[0..3:1] — CRI interpolation level q, which determines segment count and latency   # p.405
slots:
  none
parameters: A-law s3.6 input/0.7 output; Alippi–Storti-Gajani s3.6/0.7; PLAN s4.5/1.7; CRI q=0..3 with q+1 cycles   # pp.405,409
results:
| metric | value | unit | technology / device | baseline | condition | page |
| Eave | 2.47 | % | UNKNOWN, 2003 | exact sigmoid | A-law, range [-8,8[ | p.406 |
| Emax | 4.90 | % | UNKNOWN, 2003 | exact sigmoid | A-law, range [-8,8[ | p.406 |
| area | 36 | LE | EP2A15F672C7, 2003 | none | A-law | p.409 |
| clock rate | 58.6 | MHz | EP2A15F672C7, 2003 | none | A-law, one cycle | p.409 |
| quality factor | 0,134 | UNKNOWN | EP2A15F672C7, 2003 | equation (17) | A-law | p.409 |
| Eave | 0.87 | % | UNKNOWN, 2003 | exact sigmoid | Alippi–Storti-Gajani, range [-8,8[ | p.406 |
| Emax | 1.89 | % | UNKNOWN, 2003 | exact sigmoid | Alippi–Storti-Gajani, range [-8,8[ | p.406 |
| area | 36 | LE | EP2A15F672C7, 2003 | none | Alippi–Storti-Gajani | p.409 |
| clock rate | 64.2 | MHz | EP2A15F672C7, 2003 | none | Alippi–Storti-Gajani, one cycle | p.409 |
| quality factor | 1,085 | UNKNOWN | EP2A15F672C7, 2003 | equation (17) | Alippi–Storti-Gajani | p.409 |
| Eave | 0.59 | % | UNKNOWN, 2003 | exact sigmoid | PLAN, range [-8,8[ | p.406 |
| Emax | 1.89 | % | UNKNOWN, 2003 | exact sigmoid | PLAN, range [-8,8[ | p.406 |
| area | 39 | LE | EP2A15F672C7, 2003 | none | PLAN | p.409 |
| clock rate | 75.8 | MHz | EP2A15F672C7, 2003 | none | PLAN, one cycle | p.409 |
| quality factor | 1,743 | UNKNOWN | EP2A15F672C7, 2003 | equation (17) | PLAN | p.409 |
| Eave | 2.41 | % | UNKNOWN, 2003 | exact sigmoid | CRI q=0, range [-8,8[ | p.406 |
| Emax | 11.9 | % | UNKNOWN, 2003 | exact sigmoid | CRI q=0, range [-8,8[ | p.406 |
| Eave | 1.20 | % | UNKNOWN, 2003 | exact sigmoid | CRI q=1, range [-8,8[ | p.406 |
| Emax | 3.78 | % | UNKNOWN, 2003 | exact sigmoid | CRI q=1, range [-8,8[ | p.406 |
| Eave | 0.92 | % | UNKNOWN, 2003 | exact sigmoid | CRI q=2, range [-8,8[ | p.406 |
| Emax | 2.45 | % | UNKNOWN, 2003 | exact sigmoid | CRI q=2, range [-8,8[ | p.406 |
| Eave | 0.85 | % | UNKNOWN, 2003 | exact sigmoid | CRI q=3, range [-8,8[ | p.406 |
| Emax | 2.06 | % | UNKNOWN, 2003 | exact sigmoid | CRI q=3, range [-8,8[ | p.406 |
| area | 65 | LE | EPC10K20RC240-4, 2002 | none | CRI q=0..3 | p.409 |
| normalized clock rate | 34.7 | MHz | EPC10K20RC240-4, 2002 | none | CRI q=0 | p.409 |
| normalized clock rate | 16.3 | MHz | EPC10K20RC240-4, 2002 | none | CRI q=1 | p.409 |
| normalized clock rate | 11.6 | MHz | EPC10K20RC240-4, 2002 | none | CRI q=2 | p.409 |
| normalized clock rate | 8.7 | MHz | EPC10K20RC240-4, 2002 | none | CRI q=3 | p.409 |
| quality factor | 0,019 | UNKNOWN | EPC10K20RC240-4, 2003 | equation (17) | CRI q=0 | p.409 |
| quality factor | 0,055 | UNKNOWN | EPC10K20RC240-4, 2003 | equation (17) | CRI q=1 | p.409 |
| quality factor | 0,079 | UNKNOWN | EPC10K20RC240-4, 2003 | equation (17) | CRI q=2 | p.409 |
| quality factor | 0,076 | UNKNOWN | EPC10K20RC240-4, 2003 | equation (17) | CRI q=3 | p.409 |
errors_and_checks: Eave and Emax are absolute approximation errors measured at 10^6 uniformly spaced domain points; no fault-detection mechanism is reported   # p.403
conditions: None of the four PWL schemes requires a multiplier (p.404). CRI accuracy saturates above q=3 and its q+1-cycle iteration reduces throughput (p.405). PLAN has the best reported non-SIG quality factor (p.409).
evidence: Sections 2.1 and 4; Tables 2-4 and 6-10 (pp.404-409)

### piecewise_poly  (role: compares)
mechanism: The Zhang–Vassiliadis–Delgado-Frias approximation evaluates a second-order expression over ]-4,4[, using symmetry-dependent constants. Algebraic simplification produces an implementation with one multiplier, two shifters and two XORs (p.405).
choices:
  segments: 2 [outside domain]   # p.405
  degree: 2   # p.405
new_choices:
  none
slots:
  none
parameters: s3.10 input; 3.10 output; input range ]-4,4[; one multiplier/two shifters/two XORs   # pp.405,409
results:
| metric | value | unit | technology / device | baseline | condition | page |
| Eave | 0.77 | % | UNKNOWN, 2003 | exact sigmoid | range ]-4,4[ | p.406 |
| Emax | 2.16 | % | UNKNOWN, 2003 | exact sigmoid | range ]-4,4[ | p.406 |
| area | 176 | LE | EP2A15F672C7, 2003 | none | fixed-point implementation | p.409 |
| clock rate | 66.4 | MHz | EP2A15F672C7, 2003 | none | one cycle | p.409 |
| quality factor | 0,227 | UNKNOWN | EP2A15F672C7, 2003 | equation (17) | fixed-point implementation | p.409 |
errors_and_checks: Eave and Emax use 10^6 uniformly spaced samples; no fault-detection mechanism is reported   # pp.403,406
conditions: The required multiplier raises area to 176 LEs, so the implementation compares poorly with the multiplierless approximations (pp.409-410).
evidence: Section 2.2; Tables 6-10 (pp.405-409)

### sigmoid_tanh_pwl  (role: proposes)
mechanism: SIG-sigmoid truncates fixed-point input/output values, minimizes each output bit as a Boolean sum of products, and implements the resulting two-level logic combinationally. Positive-only or negative-only mapping uses sigmoid symmetry and a z-bit adder/subtractor; all-input mapping omits that arithmetic but doubles the mapped inputs (pp.405-406).
choices:
  approximation: bit_level_mapping   # p.405
  symmetry_folding: true   # pp.405-406
new_choices:
  mapped_input_region: {all, negative, positive} — selects which input-sign region is directly mapped   # p.405
  logic_realization: minimized_sop — realizes each output bit as minimized AND/OR planes   # p.405
slots:
  none
parameters: sig_235p=s2.3/0.5; sig_236p=s2.3/0.6; sig_336p=s3.3/0.6; sig_337p=s3.3/0.7; combinational, one cycle   # pp.405,409
results:
| metric | value | unit | technology / device | baseline | condition | page |
| Eave | 0.69 | % | UNKNOWN, 2003 | exact sigmoid | sig_235p, range [-4,4[ | p.406 |
| Emax | 1.51 | % | UNKNOWN, 2003 | exact sigmoid | sig_235p, range [-4,4[ | p.406 |
| area | 22 | LE | EP2A15F672C7, 2003 | none | sig_235p | p.409 |
| clock rate | 89.5 | MHz | EP2A15F672C7, 2003 | none | sig_235p | p.409 |
| quality factor | 3,905 | UNKNOWN | EP2A15F672C7, 2003 | equation (17) | sig_235p | p.409 |
| Eave | 0.40 | % | UNKNOWN, 2003 | exact sigmoid | sig_236p, range [-4,4[ | p.406 |
| Emax | 0.77 | % | UNKNOWN, 2003 | exact sigmoid | sig_236p, range [-4,4[ | p.406 |
| area | 25 | LE | EP2A15F672C7, 2003 | none | sig_236p | p.409 |
| clock rate | 94.7 | MHz | EP2A15F672C7, 2003 | none | sig_236p | p.409 |
| quality factor | 12,299 | UNKNOWN | EP2A15F672C7, 2003 | equation (17) | sig_236p | p.409 |
| Eave | 0.33 | % | UNKNOWN, 2003 | exact sigmoid | sig_336p, range [-8,8[ | p.406 |
| Emax | 0.77 | % | UNKNOWN, 2003 | exact sigmoid | sig_336p, range [-8,8[ | p.406 |
| area | 32 | LE | EP2A15F672C7, 2003 | none | sig_336p | p.409 |
| clock rate | 85.7 | MHz | EP2A15F672C7, 2003 | none | sig_336p | p.409 |
| quality factor | 10,540 | UNKNOWN | EP2A15F672C7, 2003 | equation (17) | sig_336p | p.409 |
| Eave | 0.17 | % | UNKNOWN, 2003 | exact sigmoid | sig_337p, range [-8,8[ | p.406 |
| Emax | 0.39 | % | UNKNOWN, 2003 | exact sigmoid | sig_337p, range [-8,8[ | p.406 |
| area | 45 | LE | EP2A15F672C7, 2003 | none | sig_337p | p.409 |
| clock rate | 76.4 | MHz | EP2A15F672C7, 2003 | none | sig_337p | p.409 |
| quality factor | 25,608 | UNKNOWN | EP2A15F672C7, 2003 | equation (17) | sig_337p | p.409 |
errors_and_checks: Truncation is the only stated SIG-sigmoid error source, with worst-case Emax=2^-(z+1); measured Eave/Emax use 10^6 uniformly spaced samples; no fault checks are reported   # pp.403,405
conditions: Positive-only implementations provide the best tested SIG results (p.406). sig_236p is selected for [-4,4[, while sig_337p is selected for [-8,8[ (pp.409-410). The stated 0.39% training and 0.78% feedforward limits are tentative assumptions requiring simulation and real-world verification (p.409).
evidence: Sections 2.3, 4 and 5; Fig. 2; Tables 5-12 (pp.405-410)

## new_families
none

## space_gaps
* `sigmoid_tanh_pwl.segments` lacks the two-region value used by the piecewise second-order approximation (p.405).
* `sigmoid_tanh_pwl` needs `mapped_input_region` and `logic_realization` choices to describe SIG-sigmoid’s all/negative/positive mapping and minimized SOP implementation (p.405).

## open_questions
* Table 7 does not state the fixed-point input/output formats used for the CRI implementations (p.409).
* The paper does not establish the neural-network-level validity of its tentative 0.39% training and 0.78% feedforward Emax limits (p.409).
