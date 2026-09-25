---
handle: hu_qian2015
citation: J. Hu, W. Qian, "A New Approximate Adder with Low Relative Error and Correct Sign Calculation", Design, Automation and Test in Europe (DATE), pp. 1449-1454, 2015
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [uint32, int32]
authority: incremental
pages_read: 1449-1454 / 6
---

## summary
The document proposes a segmented approximate adder that speculates each block carry from the previous block’s most-significant generate signal and uses a propagate-controlled mux to limit relative error. An optional combinational sign-correction module guarantees the correct sign for 2’s-complement addition without an additional clock cycle.

## families
### segmented_carry_speculative  (role: proposes)
mechanism: The adder partitions n bits into k-bit blocks. Each carry generator substitutes the previous block’s most-significant generate signal for the true carry-in, which limits the longest carry-propagation path to 2k. An error-reduction mux selects either that generate signal or the previous approximate carry according to the current block-propagate signal pp^i. The signed variant forms sp and CS signals from leading block propagates and approximate carries, then forces affected leading sum blocks to zero when sign correction is required.
choices:
  sub_adder_width: 4; 8   # p.1453, p.1454
  carry_in_scheme: previous_block_msb_generate [outside domain]   # p.1450
  correction: error_reduction_stage; sign_repair in the signed variant   # p.1450, p.1453
new_choices:
  none
slots:
  sub_adder: ripple_carry   # p.1452, p.1454
parameters: n=32 bits; k=4 or 8 bits; m=ceil(n/k); longest carry path=2k; combinational Verilog HDL; pipeline stages/latency cycles/II=UNKNOWN   # p.1450, p.1453, p.1454
results:
| metric | value | unit | technology / device | baseline | condition | page |
| area | 238.6 | UNKNOWN | 45nm NAN-gate cell library; 2015 | RCA/CLA and six approximate adders | k=4, error reduction, no sign correction | p.1454 |
| delay | 1.23 | ns | 45nm NAN-gate cell library; 2015 | RCA/CLA and six approximate adders | k=4, error reduction, no sign correction | p.1454 |
| power | 33.1 | UNKNOWN | 45nm NAN-gate cell library; 2015 | RCA/CLA and six approximate adders | k=4, error reduction, no sign correction | p.1454 |
| error rate | 10.03 | % | 45nm NAN-gate cell library; 2015 | exact result | k=4, error reduction, no sign correction | p.1454 |
| maximal relative error | 6.25 | % | 45nm NAN-gate cell library; 2015 | exact result | k=4, error reduction, no sign correction | p.1454 |
| area | 307.8 | UNKNOWN | 45nm NAN-gate cell library; 2015 | RCA/CLA and six approximate adders | k=4, error reduction and sign correction | p.1454 |
| delay | 1.3 | ns | 45nm NAN-gate cell library; 2015 | RCA/CLA and six approximate adders | k=4, error reduction and sign correction | p.1454 |
| power | 41.7 | UNKNOWN | 45nm NAN-gate cell library; 2015 | RCA/CLA and six approximate adders | k=4, error reduction and sign correction | p.1454 |
| error rate | <10.03 | % | 45nm NAN-gate cell library; 2015 | exact result | k=4, error reduction and sign correction | p.1454 |
| maximal relative error | 6.25 | % | 45nm NAN-gate cell library; 2015 | exact result | k=4, error reduction and sign correction | p.1454 |
| speedup | 4.3 | x | 45nm NAN-gate cell library; 2015 | RCA | 32-bit, k=4, sign-corrected proposed adder | p.1454 |
| power saving | 47 | % | 45nm NAN-gate cell library; 2015 | CLA | 32-bit, k=4, sign-corrected proposed adder | p.1454 |
| area | 248.2 | UNKNOWN | 45nm NAN-gate cell library; 2015 | RCA/CLA and six approximate adders | k=8, error reduction, no sign correction | p.1454 |
| delay | 2.03 | ns | 45nm NAN-gate cell library; 2015 | RCA/CLA and six approximate adders | k=8, error reduction, no sign correction | p.1454 |
| power | 34.31 | UNKNOWN | 45nm NAN-gate cell library; 2015 | RCA/CLA and six approximate adders | k=8, error reduction, no sign correction | p.1454 |
| error rate | 0.29 | % | 45nm NAN-gate cell library; 2015 | exact result | k=8, error reduction, no sign correction | p.1454 |
| maximal relative error | 0.39 | % | 45nm NAN-gate cell library; 2015 | exact result | k=8, error reduction, no sign correction | p.1454 |
| area | 270.26 | UNKNOWN | 45nm NAN-gate cell library; 2015 | RCA/CLA and six approximate adders | k=8, error reduction and sign correction | p.1454 |
| delay | 2.09 | ns | 45nm NAN-gate cell library; 2015 | RCA/CLA and six approximate adders | k=8, error reduction and sign correction | p.1454 |
| power | 39.72 | UNKNOWN | 45nm NAN-gate cell library; 2015 | RCA/CLA and six approximate adders | k=8, error reduction and sign correction | p.1454 |
| error rate | <0.29 | % | 45nm NAN-gate cell library; 2015 | exact result | k=8, error reduction and sign correction | p.1454 |
| maximal relative error | 0.39 | % | 45nm NAN-gate cell library; 2015 | exact result | k=8, error reduction and sign correction | p.1454 |
errors_and_checks: The error-reduction design has maximal relative error no greater than 1/2^k under all input cases. The error-rate analysis assumes uniformly distributed inputs. The sign-corrected variant guarantees no sign error for 2’s-complement signed addition and has a lower error rate than the unsigned variant.   # p.1451, p.1453
conditions: The design targets error-tolerant multimedia/machine-learning applications. Larger k reduces error rate/maximal relative error but increases block delay. RCA sum generators favor area/power when k is small, while CLA sum generators can reduce the asymptotic block delay to O(log k) when k is large.   # p.1449, p.1452, p.1454
evidence: §III, Eqs. (3)-(7), Figs. 1-4, pp.1450-1452; §IV, Figs. 5-6, p.1453; §V, Tables I-II, pp.1453-1454

## new_families
none

## space_gaps
* `carry_in_scheme` lacks the document’s `previous_block_msb_generate` speculation source.   # p.1450
* `correction` cannot express the simultaneous error-reduction stage and sign-repair module used by the signed variant.   # p.1453

## open_questions
* Tables I and II do not print units for the area and power columns.
