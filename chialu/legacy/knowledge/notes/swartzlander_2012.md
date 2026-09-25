---
handle: swartzlander_2012
citation: E. E. Swartzlander, H. H. Saleh, "FFT Implementation with Fused Floating-Point Operations", IEEE Transactions on Computers, vol. 61, no. 2, pp. 284-288, 2012
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_DOT_ACC, other]
formats: [fp32]
authority: incremental
pages_read: 284-288 / 5
---

## summary
The document proposes a fused two-term floating-point dot product and a fused add-subtract unit for radix-2/radix-4 FFT butterflies (pp.284-288). The fused units share normalization/rounding/alignment hardware and reduce placed-and-routed area, latency, and accumulated rounding error relative to parallel discrete fp32 adders and multipliers (pp.285-288).

## families
### fused_two_term_dot  (role: proposes)
mechanism: The Fused DP computes AB ± CD by adding a second multiplier tree and a revised exponent-comparison circuit to an FMA; the datapath from the carry-save adder onward is identical to the FMA. The Fused AS computes A+B and A-B in parallel while sharing exponent-difference calculation, significand swapping, alignment, and part of the output logic. Radix-2/radix-4 FFT butterflies compose these primitives so intermediate products avoid separate normalization and rounding. (pp.284-287)
choices:
  second_op: both   # pp.284-286
new_choices:
  product_combination: add_or_subtract — selects AB+CD or AB-CD in the Fused DP   # p.284
slots:
  none
parameters: 32-bit IEEE-754 operands; four IEEE rounding modes; no hardware implementation of subnormals; radix-2 DIF and radix-4 DIT butterflies; example three-stage radix-2 pipeline; II=1 implied by the pipeline data rate   # pp.284, 286-287
results:
| metric | value | unit | technology / device | baseline | condition | page |
| area | about -33 | percent | 45 nm bulk CMOS standard-cell library; 2012 | two discrete floating-point multipliers plus one floating-point adder | Fused DP placed-and-routed implementation | p.285 |
| delay | about -16 | percent | 45 nm bulk CMOS standard-cell library; 2012 | two discrete floating-point multipliers plus one floating-point adder | Fused DP placed-and-routed implementation | p.285 |
| cell area | about -22 | percent | 45 nm bulk CMOS standard-cell library; 2012 | two parallel discrete floating-point adders | Fused AS implementation | p.286 |
| delay | about +5 | percent | 45 nm bulk CMOS standard-cell library; 2012 | two parallel discrete floating-point adders | Fused AS implementation | p.286 |
| area | -35 | percent | 45 nm bulk CMOS standard-cell library; 2012 | discrete radix-2 FFT butterfly | fused radix-2 DIF FFT butterfly | p.288 |
| latency | -15 | percent | 45 nm bulk CMOS standard-cell library; 2012 | discrete radix-2 FFT butterfly | fused radix-2 DIF FFT butterfly | p.288 |
| clock rate | over 500 | MHz | 45 nm bulk CMOS standard-cell library; 2012 | discrete or fused radix-2 FFT butterfly | three-stage pipeline | p.287 |
| data rate | over 1 | GSPS | 45 nm bulk CMOS standard-cell library; 2012 | discrete or fused radix-2 FFT butterfly | three-stage pipeline | p.287 |
| area | about -26 | percent | 45 nm bulk CMOS standard-cell library; 2012 | discrete radix-4 FFT butterfly | fused radix-4 DIT FFT butterfly | p.288 |
| latency | -13 | percent | 45 nm bulk CMOS standard-cell library; 2012 | discrete radix-4 FFT butterfly | fused radix-4 DIT FFT butterfly | p.288 |
| FFT error | about -25 | percent | UNKNOWN; 2012 | discrete FFT implementation | 64K-point random-input FFT simulation, fused radix-2/radix-4 implementations | p.288 |
| FFT error | about -28 | percent | UNKNOWN; 2012 | radix-2 FFT implementation | 64K-point FFT, radix-4 implementation | p.288 |
errors_and_checks: The Fused DP rounds once, while the discrete two-multiplier-plus-adder path rounds three times (p.285). The radix-2 fused butterfly has worst-case component errors of 1/2 LSB at Y1 and 1 LSB at Y2, versus 1/2 LSB and 2 LSB for the discrete butterfly (p.287). The radix-4 fused butterfly has a worst-case output error of 1 1/2 LSB, versus 2 1/2 LSB for the discrete butterfly (p.288). The 64K-point simulations report lower average and maximum absolute errors for both fused implementations (p.288). Fault checking is none.
conditions: The implementations target DSP workloads where throughput matters more than latency (p.284). Every implementation uses fp32, supports all four IEEE rounding modes, and omits hardware support for subnormals (p.284). The Fused AS loses delay because subtraction requires a two’s-complement operation and because the fused circuit has heavier loading/longer interconnections (p.286). The paper suggests computing round/sticky bits during alignment and retaining only 26 bits of the smaller significand to reduce adder size/delay (p.286).
evidence: Sections 3-7; Figs. 2-9; Tables 1-8; pp.284-288.

## new_families
none

## space_gaps
* `fused_two_term_dot.second_op` covers the two primitives at paper level, but it does not distinguish one-result AB±CD selection from simultaneous A+B/A-B outputs; `product_combination` records the missing Fused DP distinction (p.284).
* The vocabulary lacks an explicit slot/value for omitted hardware subnormal support without a stated flush-to-zero or software-trap behavior (p.284).

## open_questions
* The numerical cells of Tables 1-8 are absent from the supplied document text, so the absolute areas/delays and the exact simulated average/maximum errors remain UNKNOWN.
* The document does not identify the multiplier-tree, carry-save reduction, or terminal carry-propagate-adder families, so those slots must not be guessed.
* The document states that subnormal hardware is not provided but does not state whether subnormal operands/results trap, flush to zero, or use another behavior.
