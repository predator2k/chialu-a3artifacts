---
handle: wires1999
citation: K. E. Wires, M. J. Schulte, L. P. Marquette, P. I. Balzola, "Combined Unsigned and Two's Complement Squarers", 33rd Asilomar Conference on Signals, Systems and Computers, 1999
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [unsigned_integer, twos_complement_integer]
authority: incremental
pages_read: 5 / 5
---

## summary
The paper proposes parallel squarers that select unsigned or two's-complement operation with an input control signal while retaining the reduced partial-product structure of an unsigned squarer (pp.1215-1218). Synthesized 8/16/32/64-bit implementations show 2% to 16% more area and 1% to 15% longer delay than unsigned squarers (p.1219).

## families
### squarer  (role: extends)
mechanism: Antidiagonal symmetry replaces each pair of equal cross-products with one partial product shifted left, while diagonal terms are simplified and further identities reduce matrix height. A control signal t selects two's-complement operation when t = 1 and unsigned operation when t = 0; XOR-controlled partial products implement the format-dependent inversions. Even-width and odd-width operands use different final matrix expressions. A parallel-counter tree reduces the matrix to sum/carry vectors, which a carry-lookahead adder combines. (pp.1215-1218)
choices:
  folding_scheme: basic_symmetry   # p.1215
  combined_signed_unsigned: true   # p.1217
new_choices:
  none
slots:
  reduction: csa_reduction_tree   # pp.1215,1218
parameters: n-bit input; t = 0 for unsigned and t = 1 for two's complement; maximum matrix height = ⌈n/2⌉; partial-product count = (n²+n)/2 for even n and (n²+n+2)/2 for odd n; evaluated widths = 8, 16, 32, and 64 bits   # pp.1217-1218
results:
| metric | value | unit | technology / device | baseline | condition | page |
| area | 0.0193 | mm² | 2.5 Volt, 0.25 micron CMOS standard cell library, four metal layers, 1999 | none | 8-bit unsigned squarer | p.1218 |
| delay | 2.263 | ns | 2.5 Volt, 0.25 micron CMOS standard cell library, four metal layers, 1999 | none | 8-bit unsigned squarer | p.1218 |
| area | 0.0221 | mm² | 2.5 Volt, 0.25 micron CMOS standard cell library, four metal layers, 1999 | none | 8-bit signed squarer | p.1218 |
| delay | 2.302 | ns | 2.5 Volt, 0.25 micron CMOS standard cell library, four metal layers, 1999 | none | 8-bit signed squarer | p.1218 |
| area | 0.0223 | mm² | 2.5 Volt, 0.25 micron CMOS standard cell library, four metal layers, 1999 | none | 8-bit combined squarer | p.1218 |
| delay | 2.607 | ns | 2.5 Volt, 0.25 micron CMOS standard cell library, four metal layers, 1999 | none | 8-bit combined squarer | p.1218 |
| area | 0.0377 | mm² | 2.5 Volt, 0.25 micron CMOS standard cell library, four metal layers, 1999 | none | 8-bit unsigned multiplier | p.1218 |
| delay | 3.075 | ns | 2.5 Volt, 0.25 micron CMOS standard cell library, four metal layers, 1999 | none | 8-bit unsigned multiplier | p.1218 |
| area | 0.0728 | mm² | 2.5 Volt, 0.25 micron CMOS standard cell library, four metal layers, 1999 | none | 16-bit unsigned squarer | p.1218 |
| delay | 3.493 | ns | 2.5 Volt, 0.25 micron CMOS standard cell library, four metal layers, 1999 | none | 16-bit unsigned squarer | p.1218 |
| area | 0.0795 | mm² | 2.5 Volt, 0.25 micron CMOS standard cell library, four metal layers, 1999 | none | 16-bit signed squarer | p.1218 |
| delay | 3.457 | ns | 2.5 Volt, 0.25 micron CMOS standard cell library, four metal layers, 1999 | none | 16-bit signed squarer | p.1218 |
| area | 0.0817 | mm² | 2.5 Volt, 0.25 micron CMOS standard cell library, four metal layers, 1999 | none | 16-bit combined squarer | p.1218 |
| delay | 3.707 | ns | 2.5 Volt, 0.25 micron CMOS standard cell library, four metal layers, 1999 | none | 16-bit combined squarer | p.1218 |
| area | 0.1300 | mm² | 2.5 Volt, 0.25 micron CMOS standard cell library, four metal layers, 1999 | none | 16-bit unsigned multiplier | p.1218 |
| delay | 4.211 | ns | 2.5 Volt, 0.25 micron CMOS standard cell library, four metal layers, 1999 | none | 16-bit unsigned multiplier | p.1218 |
| area | 0.2669 | mm² | 2.5 Volt, 0.25 micron CMOS standard cell library, four metal layers, 1999 | none | 32-bit unsigned squarer | p.1218 |
| delay | 5.009 | ns | 2.5 Volt, 0.25 micron CMOS standard cell library, four metal layers, 1999 | none | 32-bit unsigned squarer | p.1218 |
| area | 0.2681 | mm² | 2.5 Volt, 0.25 micron CMOS standard cell library, four metal layers, 1999 | none | 32-bit signed squarer | p.1218 |
| delay | 4.876 | ns | 2.5 Volt, 0.25 micron CMOS standard cell library, four metal layers, 1999 | none | 32-bit signed squarer | p.1218 |
| area | 0.2728 | mm² | 2.5 Volt, 0.25 micron CMOS standard cell library, four metal layers, 1999 | none | 32-bit combined squarer | p.1218 |
| delay | 5.043 | ns | 2.5 Volt, 0.25 micron CMOS standard cell library, four metal layers, 1999 | none | 32-bit combined squarer | p.1218 |
| area | 0.4480 | mm² | 2.5 Volt, 0.25 micron CMOS standard cell library, four metal layers, 1999 | none | 32-bit unsigned multiplier | p.1218 |
| delay | 5.416 | ns | 2.5 Volt, 0.25 micron CMOS standard cell library, four metal layers, 1999 | none | 32-bit unsigned multiplier | p.1218 |
| area | 0.9771 | mm² | 2.5 Volt, 0.25 micron CMOS standard cell library, four metal layers, 1999 | none | 64-bit unsigned squarer | p.1218 |
| delay | 6.114 | ns | 2.5 Volt, 0.25 micron CMOS standard cell library, four metal layers, 1999 | none | 64-bit unsigned squarer | p.1218 |
| area | 1.0190 | mm² | 2.5 Volt, 0.25 micron CMOS standard cell library, four metal layers, 1999 | none | 64-bit signed squarer | p.1218 |
| delay | 5.871 | ns | 2.5 Volt, 0.25 micron CMOS standard cell library, four metal layers, 1999 | none | 64-bit signed squarer | p.1218 |
| area | 1.0350 | mm² | 2.5 Volt, 0.25 micron CMOS standard cell library, four metal layers, 1999 | none | 64-bit combined squarer | p.1218 |
| delay | 6.160 | ns | 2.5 Volt, 0.25 micron CMOS standard cell library, four metal layers, 1999 | none | 64-bit combined squarer | p.1218 |
| area | 1.6620 | mm² | 2.5 Volt, 0.25 micron CMOS standard cell library, four metal layers, 1999 | none | 64-bit unsigned multiplier | p.1218 |
| delay | 6.551 | ns | 2.5 Volt, 0.25 micron CMOS standard cell library, four metal layers, 1999 | none | 64-bit unsigned multiplier | p.1218 |
| area overhead | 57% to 79% | more area | 2.5 Volt, 0.25 micron CMOS standard cell library, four metal layers, 1999 | unsigned squarer of equal width | unsigned multiplier, widths 8/16/32/64 bits | p.1218 |
| delay overhead | 7% to 36% | longer critical-path delay | 2.5 Volt, 0.25 micron CMOS standard cell library, four metal layers, 1999 | unsigned squarer of equal width | unsigned multiplier, widths 8/16/32/64 bits | p.1219 |
| area overhead | 2% to 16% | more area | 2.5 Volt, 0.25 micron CMOS standard cell library, four metal layers, 1999 | unsigned squarer of equal width | combined squarer, widths 8/16/32/64 bits | p.1219 |
| delay overhead | 1% to 15% | longer critical-path delay | 2.5 Volt, 0.25 micron CMOS standard cell library, four metal layers, 1999 | unsigned squarer of equal width | combined squarer, widths 8/16/32/64 bits | p.1219 |
errors_and_checks: Exact integer squaring is preserved by equivalent partial-product transformations; no approximation error, fault model, or concurrent checker is reported.   # pp.1215-1218
conditions: The analysis assumes that A is an integer, although the design can be modified for fractional or mixed numbers (p.1215). The even-width and odd-width matrices require different final identities (pp.1216-1218). The combined design adds n XOR gates and about one XOR-gate delay relative to the unsigned design (p.1218). The reported area/delay values are synthesis estimates, and routing plus synthesis area-delay tradeoffs cause deviations from structural expectations (pp.1218-1219). Power is not measured; lower power than parallel multipliers is stated only as an expectation (p.1219).
evidence: Abstract and §1 (p.1215); unsigned matrices/equations in Figs.1-2 and §2 (pp.1215-1216); two's-complement matrices/equations in Figs.3-4 and §3 (pp.1216-1217); combined matrices/equations in Figs.5-6 and §4 (pp.1217-1218); Table 1 and §5 (pp.1218-1219).

## new_families
none

## space_gaps
* The squarer family lacks a final-adder slot, although every evaluated squarer reduces its matrix to sum/carry vectors and uses a carry_lookahead adder for final assimilation (pp.1215,1218).
* The reduction slot names csa_reduction_tree, but the vocabulary lacks a corresponding family definition for the paper's tree of (3,2) and (2,2) parallel counters (pp.1215,1218).

## open_questions
* The carry-lookahead adder's group size, levels, and intergroup-carry structure are not reported.
* The paper does not report measured or estimated power values.
