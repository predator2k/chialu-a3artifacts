---
handle: saleh_2008
citation: H. H. Saleh, E. E. Swartzlander, "A Floating-Point Fused Dot-Product Unit", IEEE ICCD, 2008
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_DOT_ACC]
formats: [fp32]
authority: incremental
pages_read: 427-431 / 5
---

## summary
The document proposes a fused unit for Y=A*B+C*D that combines two multiplier trees, alignment, a 4:2 reduction tree, and the remaining components of a conventional floating-point multiplier. The single-precision implementation performs one rounding operation and occupies 16,104 µm2 with a 2,721 ps latency in a 45 nm process. # p.427-430

## families
### fused_two_term_dot  (role: proposes)
mechanism: Two floating-point products are formed in multiplier trees, aligned according to an exponent comparison, and combined through a 4:2 reduction tree. The architecture adds the second multiplier tree, aligner, and reduction tree to a conventional floating-point multiplier and reuses the multiplier's remaining components. The unit produces Y=A*B+C*D with one rounding operation rather than the three rounding operations used by two discrete multipliers followed by an adder. # p.427-429
choices:
  second_op: dot2   # p.427
new_choices:
  operation_bypass: {none, addition_skip_multiplier_trees, multiplication_skip_alignment} — data-forwarding multiplexers can bypass the multiplier trees for addition or bypass alignment for multiplication   # p.428-429
slots:
  none
parameters: two products; IEEE Std-754 single-precision operands; one rounding operation; 2,721 ps fused-operation latency; pipeline stages/cycles/II UNKNOWN   # p.427-430
results:
| metric | value | unit | technology / device | baseline | condition | page |
| standard-cell area | 16,104 | µm2 | 45 nm high-performance standard-cell process / 2008 | none | fused dot-product; placed and routed | p.430 |
| latency | 2,721 | ps | 45 nm high-performance standard-cell process / 2008 | none | fused dot-product; extracted/back-annotated netlist | p.430 |
| height | 140 | µm | 45 nm high-performance standard-cell process / 2008 | none | fused dot-product | p.430 |
| width | 141 | µm | 45 nm high-performance standard-cell process / 2008 | none | fused dot-product | p.430 |
| utilization | 81.7 | % | 45 nm high-performance standard-cell process / 2008 | none | fused dot-product | p.430 |
| total wire length | 127 | mm | 45 nm high-performance standard-cell process / 2008 | none | fused dot-product | p.430 |
| dynamic power | 5839 | µW | 45 nm high-performance standard-cell process / 2008 | none | fused dot-product; operating point not reported | p.430 |
| leakage power | 1366 | µW | 45 nm high-performance standard-cell process / 2008 | none | fused dot-product; operating point not reported | p.430 |
| total power | 7205 | µW | 45 nm high-performance standard-cell process / 2008 | none | fused dot-product; operating point not reported | p.430 |
| standard-cell area | 9,482 | µm2 | 45 nm high-performance standard-cell process / 2008 | none | conventional F-P multiplier | p.430 |
| latency | 1,804 | ps | 45 nm high-performance standard-cell process / 2008 | none | conventional F-P multiplier | p.430 |
| dynamic power | 5068 | µW | 45 nm high-performance standard-cell process / 2008 | none | conventional F-P multiplier; operating point not reported | p.430 |
| leakage power | 808 | µW | 45 nm high-performance standard-cell process / 2008 | none | conventional F-P multiplier; operating point not reported | p.430 |
| total power | 5876 | µW | 45 nm high-performance standard-cell process / 2008 | none | conventional F-P multiplier; operating point not reported | p.430 |
| area | 3,811 | µm2 | 45 nm high-performance standard-cell process / 2008 | none | conventional F-P adder | p.430 |
| latency | 1,644 | ps | 45 nm high-performance standard-cell process / 2008 | none | conventional F-P adder | p.430 |
| area | 22,775 | µm2 | 45 nm high-performance standard-cell process / 2008 | none | conventional parallel dot product; multiplexers/register ignored | p.430 |
| latency | 3,448 | ps | 45 nm high-performance standard-cell process / 2008 | none | conventional parallel dot product; multiplexers/register ignored | p.430 |
| area | 13,293 | µm2 | 45 nm high-performance standard-cell process / 2008 | none | conventional serial dot product; multiplexers/register ignored | p.430 |
| latency | 5,252 | ps | 45 nm high-performance standard-cell process / 2008 | none | conventional serial dot product; multiplexers/register ignored | p.430 |
| area ratio | about 70 | % | 45 nm process / 2008 | conventional parallel dot product | fused dot-product | p.427 |
| speed improvement | 27 | % faster | 45 nm process / 2008 | conventional parallel dot product | fused dot-product | p.427 |
| multiplier-time ratio | 150 | % | 45 nm process / 2008 | conventional floating-point multiplier | fused dot-product | p.427 |
| FFT butterfly error range | –1.7x10-5 to 1.6x10-5 | error | UNKNOWN / 2008 | Matlab double-precision result | single-precision FDP simulation | p.429 |
| FFT butterfly error range | –2.4x10-5 to 2.3x10-5 | error | UNKNOWN / 2008 | Matlab double-precision result | discrete single-precision operations | p.429 |
| FFT butterfly error increase | about 40 | % higher | UNKNOWN / 2008 | fused dot-product | discrete floating-point operations | p.429 |
errors_and_checks: The analytic model assigns one rounding-error term to the fused unit and three rounding-error terms to discrete execution, so the document claims one-third of the discrete approach's rounding error. The FFT simulation reports errors of –1.7x10-5 to 1.6x10-5 for the FDP and –2.4x10-5 to 2.3x10-5 for discrete operations. No maximum-ulp contract or fault checker is specified. # p.429
conditions: The parallel conventional implementation maximizes throughput at higher area/power, while the serial implementation reduces area/power at lower throughput. Addition-only use requires multiplier-tree bypass multiplexers and adds one multiplexer delay relative to a discrete adder. Multiplication-only use requires alignment bypass and adds two multiplexer-operation delays. The evaluated implementation covers IEEE Std-754 single precision. # p.428-430
evidence: §II and Figs. 6-7, p.428; §III and Figs. 8-9, p.429-430; Table 1, §VI, Table 2, and Fig. 11, p.430-431

## new_families
none

## space_gaps
* fused_two_term_dot lacks an operation-bypass choice for the document's addition-only and multiplication-only forwarding paths. # p.428-429

## open_questions
* The multiplier-tree recoding/reduction structure and final carry-propagate adder family are not identified. # p.428
* The rounding mode, exception handling, subnormal handling, and correctly-rounded guarantee are not reported. # p.427-430
* The pipeline depth, initiation interval, voltage, process corner, clocking assumptions, and power-activity conditions are not reported. # p.430
