---
handle: srinivas_parhi_1992
citation: Srinivas, Parhi, "A Fast VLSI Adder Architecture", IEEE Journal of Solid-State Circuits, 1992
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [twos_complement_fixed_point]
authority: incremental
pages_read: 761-767 / 7
---

## summary
The paper proposes a fixed-point two’s-complement adder that performs carry-free radix-2 redundant addition and then converts the result through parallel sign-select conversion (pp.761-765). The design trades increased transistor count for lower modeled gate delay at word lengths from 16 to 64 b (p.767).

## families
### generalized_signed_digit  (role: extends)
mechanism: Two two’s-complement operands feed a hybrid radix-2 adder without an input converter. Each redundant result digit belongs to {-1, 0, 1} and is encoded by two bits satisfying S=S*-S**. Parallel converter pairs process blocks under assumed positive and negative signs for the less-significant portion. A sign-multiplexor network finds the most-significant nonzero block and selects the correct binary result. The resulting architecture is called the sign-select conversion adder. (pp.761-765)
choices:
  radix: 2   # pp.761-762
  digit_encoding: S=S*-S** two-bit difference encoding [outside domain]   # pp.761-762
  addition_scheme: carry_free   # pp.761-762
  final_conversion: sign_select_parallel [outside domain]   # pp.763-765
new_choices:
  converter_block_size: b=4 for W<=16; b=8 for W>16 through 64 — number of redundant digits handled by each duplicated converter pair   # pp.763, 765-766
  conversion_selection: sign_select — selects between conversions computed with sign inputs 0 and 1   # pp.763-765
  carry_output_generation: input_and_sum_signs — derives carry as c=sb XOR ab from the two input signs and the sum sign   # pp.764-766
slots:
  none
parameters: W=8, 16, 32, and 64 b in comparisons; detailed implementation W=32 b; b=4 for W<=16 and b=8 for W>16 through 64; bit-parallel input/output; no pipeline or II reported   # pp.763-767
results:
| metric | value | unit | technology / device | baseline | condition | page |
| critical-path delay | 8 | gate delays | CMOS, node UNKNOWN; 1992 | ripple 15; binary lookahead 8; carry-select 8 | W=8, b=4 | p.767 |
| critical-path delay | 8 | gate delays | CMOS, node UNKNOWN; 1992 | ripple 31; binary lookahead 11; carry-select 11 | W=16, b=4 | p.767 |
| critical-path delay | 12 | gate delays | CMOS, node UNKNOWN; 1992 | ripple 63; binary lookahead 14; carry-select 14.5 | W=32, b=8 | p.767 |
| critical-path delay | 13 | gate delays | CMOS, node UNKNOWN; 1992 | ripple 127; binary lookahead 17; carry-select 18.5 | W=64, b=8 | p.767 |
| critical-path breakdown | 3 + 8 + 1 = 12 | gate delays | CMOS, node UNKNOWN; 1992 | none | W=32; type-I adder + converter + block multiplexor | p.767 |
| transistor count | 284 | transistors | CMOS, node UNKNOWN; 1992 | binary lookahead 273; carry-select 732 | W=8 | p.767 |
| transistor count | 756 | transistors | CMOS, node UNKNOWN; 1992 | binary lookahead 577; carry-select 1468 | W=16 | p.767 |
| transistor count | 1772 | transistors | CMOS, node UNKNOWN; 1992 | binary lookahead 1185; carry-select 2958 | W=32 | p.767 |
| transistor count | 3620 | transistors | CMOS, node UNKNOWN; 1992 | binary lookahead 2401; carry-select 5926 | W=64 | p.767 |
| speed improvement | 28 % | percent | CMOS, node UNKNOWN; 1992 | binary lookahead and carry-select | W=16 | p.767 |
| speed improvement | 14.3% | percent | CMOS, node UNKNOWN; 1992 | binary lookahead | W=32 | p.767 |
| speed improvement | 17.25% | percent | CMOS, node UNKNOWN; 1992 | carry-select | W=32 | p.767 |
| speed improvement | about 24% | percent | CMOS, node UNKNOWN; 1992 | binary lookahead | W=64 | p.767 |
| speed improvement | nearly 30% | percent | CMOS, node UNKNOWN; 1992 | carry-select | W=64 | p.767 |
| area increase | 30% | percent | CMOS, node UNKNOWN; 1992 | binary lookahead | W=16; transistor count used as area measure | p.767 |
| area increase | 50% | percent | CMOS, node UNKNOWN; 1992 | binary lookahead | W=32; paired with 14.3% speed improvement | p.767 |
| area increase | 50% | percent | CMOS, node UNKNOWN; 1992 | binary lookahead | W=64; paired with about 24% speed improvement | p.767 |
errors_and_checks: The architecture performs fixed-point two’s-complement addition through an exact redundant-to-binary conversion; no approximation metric, fault model, or concurrent checker is reported. Overflow behavior is not specified.   # pp.761-765
conditions: The modeled delay treats each buffered 2-to-1 transmission-gate multiplexor as one simple gate delay and each complex gate as 1.5 simple-gate delays. The design is faster than the compared schemes for word lengths longer than 32 b, while requiring about 50% more transistors than binary lookahead at 32 and 64 b. The repeated modules provide a regular CMOS VLSI structure.   # pp.766-767
evidence: Sections II-IV and Figs. 1-9 define the redundant adder, converter, sign-select network, and carry generation (pp.761-766); Tables I-III and Section V provide delay/transistor comparisons (pp.766-767).

## new_families
none

## space_gaps
* `generalized_signed_digit.final_conversion` lacks the `sign_select_parallel` conversion used by the architecture.   # pp.763-765
* `generalized_signed_digit.digit_encoding` lacks the two-bit difference encoding S=S*-S**.   # pp.761-762
* The vocabulary lacks a redundant-to-binary converter slot or family with converter block size/sign-selection choices.   # pp.763-766

## open_questions
* The abstract reports a 20-28% speed advantage for word lengths from 16 to 64, while Section V reports only 14.3% against binary lookahead at W=32.   # pp.761, 767
* The supplied page headers alternate between volume 21 and volume 27, so the journal volume requires bibliographic verification.
