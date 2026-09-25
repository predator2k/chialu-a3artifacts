---
handle: hashemi2015
citation: S. Hashemi, R. I. Bahar, S. Reda, "DRUM: A Dynamic Range Unbiased Multiplier for Approximate Applications", IEEE/ACM International Conference on Computer-Aided Design (ICCAD), 2015
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [uint16, uint24, uint32, int16, int24, int32, fixed16]
authority: landmark
pages_read: 418-425 / 8
---

## summary
DRUM dynamically selects the leading k-bit range of each n-bit operand, unbiases the discarded portion, multiplies the selected ranges with a smaller accurate multiplier, and shifts the product into position (p.420). The design provides a design-time accuracy/power tradeoff with bounded, near-zero-mean error and increasing savings as operand width grows (pp.421-423). Three hardware applications retain close-to-accurate output quality while reducing combinational power by 22.3%-58.3% (pp.424-425).

## families
### dynamic_segment  (role: proposes)
mechanism: Two leading-one detectors locate each operand’s most significant 1. The next k-2 bits and an inserted 1 at bit t-k+1 form a k-bit approximation whose discarded low portion approximates its expected value. A k×k accurate multiplier computes the reduced product, and a barrel shifter restores its position. Inputs whose leading 1 lies within the least-significant k bits pass those k bits directly. Optional two’s-complement preprocessing/postprocessing supports signed multiplication (p.420).
choices:
  segment_width: k, design-time range 1 to n; evaluated at 3, 4, 5, 6, 7, 8 [3 outside domain]   # p.422
  segment_select: dynamic_leading_one   # p.420
  unbiasing: lsb_set_to_one   # p.420
  runtime_width_scaling: false   # p.422
new_choices:
  signed_operation: {unsigned, twos_complement_prepostprocess} — optional conversion/negation around the unsigned DRUM core   # p.420
slots:
  core_multiplier: Wallace-Tree multiplier [outside slot domain]   # p.420
parameters: n-bit operands; k selected bits per operand; k×k accurate core; evaluated n=16/24/32 and k=3-8; application widths 16×16, 32×32, and 16×32   # pp.420, 422, 425
results:
| metric | value | unit | technology / device | baseline | condition | page |
| max error | 56.25 | % | ModelSim, 2015 | accurate multiplication | n=16, k=3, one billion random operand pairs | p.422 |
| max error | 26.56 | % | ModelSim, 2015 | accurate multiplication | n=16, k=4 | p.422 |
| max error | 12.86 | % | ModelSim, 2015 | accurate multiplication | n=16, k=5 | p.422 |
| max error | 6.31 | % | ModelSim, 2015 | accurate multiplication | n=16, k=6 | p.422 |
| max error | 3.1 | % | ModelSim, 2015 | accurate multiplication | n=16, k=7 | p.422 |
| max error | 1.54 | % | ModelSim, 2015 | accurate multiplication | n=16, k=8 | p.422 |
| average absolute error | 11.90 | % | ModelSim, 2015 | accurate multiplication | n=16, k=3 | p.422 |
| average absolute error | 5.89 | % | ModelSim, 2015 | accurate multiplication | n=16, k=4 | p.422 |
| average absolute error | 2.94 | % | ModelSim, 2015 | accurate multiplication | n=16, k=5 | p.422 |
| average absolute error | 1.47 | % | ModelSim, 2015 | accurate multiplication | n=16, k=6 | p.422 |
| average absolute error | 0.73 | % | ModelSim, 2015 | accurate multiplication | n=16, k=7 | p.422 |
| average absolute error | 0.37 | % | ModelSim, 2015 | accurate multiplication | n=16, k=8 | p.422 |
| error bias | 2.08 | % | ModelSim, 2015 | accurate multiplication | n=16, k=3 | p.422 |
| error bias | 0.53 | % | ModelSim, 2015 | accurate multiplication | n=16, k=4 | p.422 |
| error bias | -0.14 | % | ModelSim, 2015 | accurate multiplication | n=16, k=5 | p.422 |
| error bias | -0.04 | % | ModelSim, 2015 | accurate multiplication | n=16, k=6 | p.422 |
| error bias | 0.01 | % | ModelSim, 2015 | accurate multiplication | n=16, k=7 | p.422 |
| error bias | 0.01 | % | ModelSim, 2015 | accurate multiplication | n=16, k=8 | p.422 |
| error standard deviation | 14.75 | % | ModelSim, 2015 | accurate multiplication | n=16, k=3 | p.422 |
| error standard deviation | 7.26 | % | ModelSim, 2015 | accurate multiplication | n=16, k=4 | p.422 |
| error standard deviation | 3.61 | % | ModelSim, 2015 | accurate multiplication | n=16, k=5 | p.422 |
| error standard deviation | 1.80 | % | ModelSim, 2015 | accurate multiplication | n=16, k=6 | p.422 |
| error standard deviation | 0.90 | % | ModelSim, 2015 | accurate multiplication | n=16, k=7 | p.422 |
| error standard deviation | 0.45 | % | ModelSim, 2015 | accurate multiplication | n=16, k=8 | p.422 |
| area | 649.4 | um2 | industrial 65-nm standard-cell library, 2015 | accurate Wallace tree: 2165 um2 | DRUM6, n=16 | p.423 |
| power | 0.296 | mW | industrial 65-nm standard-cell library, 2015 | accurate Wallace tree: 1.04 mW | DRUM6, n=16 | p.423 |
| area savings | 70 | % | industrial 65-nm standard-cell library, 2015 | accurate Wallace tree | DRUM6, n=16 | p.423 |
| power savings | 71.45 | % | industrial 65-nm standard-cell library, 2015 | accurate Wallace tree | DRUM6, n=16 | p.423 |
| critical path | 1.91 | ns | industrial 65-nm standard-cell library, 2015 | accurate Wallace tree: 3.61 ns | DRUM6, n=16 | p.423 |
| Gaussian-filter SNR | 91.04 | dB | fixed-point MATLAB, 2015 | accurate filtered image | DRUM6, 7×7 kernel, 16-bit data | p.424 |
| JPEG SNR | 40.04 | dB | fixed-point MATLAB, 2015 | accurate: 40.32 dB | DRUM6, 20 coefficients | p.424 |
| perceptron error rate | 15.1 | % | fixed-point MATLAB, 2015 | accurate multiplier: 15.0% | DRUM6, 1000 two-dimensional points | p.425 |
| application area | 186964 | um2 | industrial 65-nm standard-cell library, 2015 | accurate: 253982 um2 | image filtering, DRUM6 | p.425 |
| application power savings | 58.3 | % | industrial 65-nm standard-cell library, 2015 | accurate combinational power: 15.55 mW | image filtering, DRUM6 power 6.48 mW | p.425 |
| application area | 1357863 | um2 | industrial 65-nm standard-cell library, 2015 | accurate: 1862116 um2 | JPEG compression, DRUM6 | p.425 |
| application power savings | 22.3 | % | industrial 65-nm standard-cell library, 2015 | accurate combinational power: 14.11 mW | JPEG, DRUM6 power 10.97 mW | p.425 |
| application area | 19786 | um2 | industrial 65-nm standard-cell library, 2015 | accurate: 25022 um2 | perceptron, DRUM6 | p.425 |
| application power savings | 55.3 | % | industrial 65-nm standard-cell library, 2015 | accurate combinational power: 2.24 mW | perceptron, DRUM6 power 1.00 mW | p.425 |
errors_and_checks: Analytical maximum/expected operand and multiplication errors are functions of n and k. For n=16 and k=6, the analytical maximum operand truncation error is 3.125% and maximum multiplication error is 6.34%; simulation reports 6.31%. The fitted result-error distribution is Gaussian with near-zero bias; no runtime error detection or correction is provided (pp.421-423).
conditions: DRUM targets error-tolerant signal-processing/computer-vision/machine-learning applications. Savings increase with input width because k can remain fixed while steering logic grows as O(n log n) and arithmetic logic as O(k²). Signed support adds preprocessing/postprocessing overhead; n=16 signed power savings are 59% rather than 71% unsigned. Application savings depend on multiplier utilization, and memory power is excluded (pp.420-422, 425).
evidence: Section III-A and Figures 1-3 define selection/unbiasing/hardware (p.420); Section III-B and Equations 1-5 define error bounds (p.421); Tables II-V and Figures 6-9 report standalone results (pp.422-423); Tables VI-IX report application results (pp.424-425).

## new_families
none

## space_gaps
* `dynamic_segment.segment_width` permits only 4-16, while the paper defines k from 1 to n and evaluates k=3 (p.422).
* `dynamic_segment.core_multiplier` lists adder families, while DRUM requires a smaller accurate multiplier and instantiates a Wallace-Tree multiplier (p.420).
* `dynamic_segment` lacks a slot for the barrel shifter that restores the reduced product’s position (p.420).
* `dynamic_segment` lacks the optional signed-operation preprocessing/postprocessing choice established by the paper (p.420).

## open_questions
* The exact area/power values for DRUM3/4/5/7/8 and most signed-width configurations are graphical and are not printed numerically (p.422).
* The industrial 65-nm standard-cell library is not identified by vendor, and application clock frequencies are not reported (pp.421, 423).
