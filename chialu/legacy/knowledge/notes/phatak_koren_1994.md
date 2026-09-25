---
handle: phatak_koren_1994
citation: Phatak, Koren, "Hybrid Signed-Digit Number Systems: A Unified Framework for Redundant Number Representations with Bounded Carry Propagation Chains", IEEE Transactions on Computers, 1994
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [radix2_hsd, twos_complement]
authority: landmark
pages_read: 880-891 / 12
---

## summary
The paper proposes hybrid signed-digit (HSD) representations that mix signed and unsigned digits to bound the maximum carry-propagation length at a designer-selected value. Static CMOS two-operand adders and redundant partial-product adder trees demonstrate the area/delay continuum between fully signed-digit and two's-complement implementations. (pp.880-889)

## families
### hybrid_signed_digit  (role: proposes)
mechanism: An HSD word places signed digits among unsigned digits. A signed-digit cell determines its carry and intermediate sum from the two signed operand digits and the adjacent lower-order unsigned bits, without waiting for the incoming ripple carry. Carries ripple concurrently through the intervening unsigned runs and stop at the next signed positions, so the maximum propagation length is d+1, where d is the longest number of unsigned positions between neighboring signed digits. Signed-digit positions may be uniform or nonuniform. (pp.881-883)
choices:
  sd_position_spacing: d+1, from 1 through the entire word length [outside domain]   # pp.881-883
  spacing_uniform: {true, false} [outside domain]   # pp.882-883
  interior_adder: ripple   # pp.882, 885
new_choices:
  output_spacing: {0, d_x, d_y} — selects the signed-digit spacing of the sum when aligned input spacings permit conversion during addition   # p.883
  representation_mix: {single_hsd_variant, mixed_sd_hsd} — selects one representation throughout a tree or transitions from SD to HSD at an intermediate level   # pp.888-889
slots:
  none
parameters: radix r=2 for the implemented cells; d is the number of unsigned digits between neighboring signed digits; n=24 for the adder study; the multiplier example is 64 x 64 bits with 32 radix-4 modified-Booth partial products, a 5-level redundant tree and final carry-look-ahead conversion   # pp.882, 885-888
results:
| metric | value | unit | technology / device | baseline | condition | page |
| transistor count | 32 | transistors/cell | static CMOS, node UNKNOWN, 1994 | none | unsigned HSD digit cell | p.884 |
| transistor count | 42 | transistors/cell | static CMOS, node UNKNOWN, 1994 | none | signed HSD digit cell | pp.884-885 |
| transistor count | 74 | transistors/2 digit positions | static CMOS, node UNKNOWN, 1994 | 84 transistors for two full SD cells | alternate-signed-digit HSD, d=1 | p.885 |
| critical-path delay | 6 | delay units | static CMOS, node UNKNOWN, 1994 | 5 units for the full SD design | alternate-signed-digit HSD, d=1 | p.885 |
| critical-path delay | 4.5 + 1.5d | delay units | static CMOS, node UNKNOWN, 1994 | none | odd d | p.885 |
| critical-path delay | 5.5 + 1.5d | delay units | static CMOS, node UNKNOWN, 1994 | none | even d | p.885 |
| transistor count | approximately 67 K | transistors | static CMOS, node UNKNOWN, 1994 | none | 64 x 64 full-SD multiplier tree including final conversion | pp.887-888 |
| critical-path delay | 46.5 | delay units | static CMOS, node UNKNOWN, 1994 | none | 64 x 64 full-SD multiplier tree | p.888 |
| transistor count | 72 K | transistors | static CMOS, node UNKNOWN, 1994 | approximately 67 K for full SD | 64 x 64 HSD multiplier tree, d=1, including final conversion | p.888 |
| critical-path delay | 53 | delay units | static CMOS, node UNKNOWN, 1994 | 46.5 units for full SD | 64 x 64 HSD multiplier tree, d=1 | p.888 |
| transistor count | approximately 66 K | transistors | static CMOS, node UNKNOWN, 1994 | approximately 67 K for SD and 72 K for HSD d=1 | 64 x 64 MHSSD mixed SD/HSD tree | p.889 |
| critical-path delay | 53 | delay units | static CMOS, node UNKNOWN, 1994 | 46.5 units for full SD | 64 x 64 MHSSD mixed SD/HSD tree | p.889 |
| AT-optimal area-ratio threshold | 0.8774 | ratio | static CMOS, node UNKNOWN, 1994 | SD tree area | MHSSD versus SD/HSD signed-digit schemes | p.889 |
| A2T-optimal area-ratio threshold | 0.937 | ratio | static CMOS, node UNKNOWN, 1994 | SD tree area | MHSSD versus SD/HSD signed-digit schemes | p.889 |
errors_and_checks: Arithmetic is exact in the HSD representation; no fault model, detection mechanism, false-alarm behavior or alias rate is reported.   # pp.881-883
conditions: The most significant digit must be signed, and an n-digit HSD result generally needs n+1 digit positions for conversion to radix-complement form.   # pp.882-883
conditions: Redundant-to-two's-complement conversion can make a two-operand redundant adder slower or larger than conventional carry-look-ahead/carry-skip adders, while multioperand trees amortize the single final conversion.   # p.886
conditions: For the n=24 study, HSD delay exceeds ripple-carry delay beyond d>20, and increasing d eventually makes both AT and A2T worse than ripple carry.   # p.887
conditions: Transistor count is only an area estimate because nonlocal tree interconnect and routing can dominate; the MHSSD tree is expected to reduce routing relative to a full-SD tree.   # p.889
evidence: Table II; Figs. 1-5; (21)-(23); Sections III-V; Appendix, pp.881-890

## new_families
none

## space_gaps
* `sd_position_spacing` needs a word-length-dependent value or range because the paper permits any carry bound from 1 through the entire word length, beyond Int[1..8:1].   # pp.880-883
* `hybrid_signed_digit` needs an explicit output-format/spacing choice because addition may preserve or change d without an extra delay penalty.   # p.883
* `binary_run_adder` lacks the paper's unsigned HSD cell, which accepts and produces signed carries encoded as two unipolar bits rather than using an ordinary binary ripple-carry full-adder cell.   # pp.883-885
* Multiplier-tree composition needs a representation-transition choice for the MHSSD design, which uses SD at the top level and HSD with d=1 at later levels.   # pp.888-889

## open_questions
* The paper gives transistor-count and gate-delay estimates rather than fabricated technology-node measurements, so physical area/power and node are UNKNOWN.
* The exact routing-area reduction of MHSSD relative to SD is not reported.
