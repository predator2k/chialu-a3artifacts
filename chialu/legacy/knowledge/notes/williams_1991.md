---
handle: williams_1991
citation: Williams, Horowitz, "A Zero-Overhead Self-Timed 160-ns 54-b CMOS Divider", IEEE Journal of Solid-State Circuits, 1991
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [fp64]
authority: landmark
pages_read: 1651-1661 / 11
---

## summary
The paper implements the 54-b mantissa path of an IEEE double-precision divider as a five-stage, latch-free self-timed ring using radix-2 SRT division and dual-monotonic completion encoding. Overlapped stage execution and repeating-remainder detection produce data-dependent completion from 45 to 160 ns in 1.2-pm CMOS. The control logic adds no serial delay under nominal conditions.

## families
### self_timed_variable_latency  (role: proposes)
mechanism: Five directly concatenated precharged stages form an iterating ring without explicit latches. Dual-monotonic wire pairs encode data validity, local completion detectors drive C-element handshaking, and precharge control remains outside the forward critical path. Adjacent stages overlap execution, so data follow the available remainder or quotient-selection path. Five asynchronous quotient shift registers collect digits. A comparison of partial remainders five stages apart terminates the computation when the quotient repeats. # p.1653-p.1657
choices:
  mechanism: self_timed # p.1651, p.1655-p.1656
new_choices:
  ring_stages: 5 — number of latch-free stages reused by the iterative ring # p.1656
  execution_overlap: adjacent_stage — replicated CPA branches allow neighboring stages to execute concurrently # p.1654-p.1655
  early_done_detection: repeating_partial_remainder — equality of remainders five stages apart terminates later iterations # p.1657
slots:
  digit_select: UNKNOWN
parameters: 54 quotient bits; 5 ring stages; maximum 11 ring iterations; minimum 2 ring iterations; nominal forward latency 2.8 ns per quotient bit; 5 V and 35°C nominal measurement condition # p.1656-p.1659
results:
| metric | value | unit | technology / device | baseline | condition | page |
| total latency | 45 to 160 | ns | 1.2-pm CMOS chip (1991) | none | best-case repeating quotient to worst-case data | p.1658-p.1659 |
| quotient-bit interval | 2.8 | ns | 1.2-pm CMOS chip (1991) | none | 5 V, 35°C ambient | p.1659 |
| active area | 9.7 | mm2 | 1.2-pm CMOS chip (1991) | none | includes test registers | p.1659 |
| iterating-ring core area | 6.8 | mm2 | 1.2-pm CMOS chip (1991) | none | central ring only | p.1659 |
| transistor count | 45K | transistors | 1.2-pm CMOS chip (1991) | none | fabricated chip | p.1658 |
| control lead margin | about 2 | ns | 1.2-pm CMOS chip (1991) | data arrival | precharge removal precedes input arrival | p.1659 |
| early-done case coverage | 12 | % of cases | modeled 8-b uniform operands (1991) | full iteration | uniform input distribution | p.1657 |
| early-done performance improvement | 9 | % | modeled 8-b uniform operands (1991) | full iteration | repeating-quotient detection | p.1657 |
| register/latch delay increase | about 30 | % | analyzed implementation (1991) | latch-free ring | 15% propagation plus 5% clock allowance plus 10% data skew | p.1656-p.1657 |
| derated mantissa latency | 190 | ns | 1.2-pm CMOS chip (1991) | MIPS R3010B 375 ns; Weitek 3364 675 ns | comparable specified voltage/temperature | p.1659 |
errors_and_checks: The chip generated correct outputs over the measured operating range and worked on first silicon. Speed-independent completion control remains correct for arbitrary gate-delay values, although control logic enters the serial critical path if the nominal delay margin is exceeded. # p.1653, p.1656, p.1658-p.1659
conditions: The ring requires at least three stages to circulate one data element/reset spacer/bubble, while the implemented stage delays require at least 4.2 stages to remain evaluation-limited; five stages provide about 0.8 stage delays of margin. # p.1656 The early-done benefit depends on the input distribution. # p.1657 Dual-monotonic wiring adds about 20% relative to transistor area, while replacing it with single-ended data would reduce total area by no more than about 15%. # p.1659
evidence: Abstract; Sections III-VII; Figs. 3-16; Table I.

### srt_radix2  (role: extends)
mechanism: Each radix-2 SRT stage selects a digit from {-1,0,1} using an approximation of the carry-save partial remainder. Modified quotient-selection equations permit the remainder path and short CPA to shrink from 4 b to 3 b. A force-next-digit flag preserves correct selection when the trimmed sign bit aliases a negative remainder into a positive encoding. Three speculative CPA branches support overlapped execution. # p.1652-p.1655
choices:
  residual_form: carry_save # p.1652
  residual_estimate_bits: 3 # p.1652
  quotient_prediction: true # p.1652, p.1655
new_choices:
  aliased_remainder_qsl: force_next_negative_digit — a flag forces the next quotient digit to -1 after specified aliased states # p.1652
slots:
  digit_select: UNKNOWN
parameters: radix 2; quotient digits {-1,0,1}; 54 quotient bits; 3-b short CPA; three CPA branches per stage # p.1652, p.1654, p.1656
results:
| metric | value | unit | technology / device | baseline | condition | page |
| datapath-width performance improvement | about 5 | % | analyzed radix-2 implementation (1991) | standard 4-b remainder path/CPA | narrowed to 3 b | p.1652 |
| overlapped-execution performance improvement | 40 | % | analyzed radix-2 implementation (1991) | sequential arrangement of the same blocks | replicated CPAs and adjacent-stage overlap | p.1655 |
| transistor-sizing divider improvement | 4 | % | analyzed radix-2 implementation (1991) | equal CPA-arm sizing | larger q_i=-1 arm | p.1655 |
| estimated latency | 225 | ns | 1.2-pm CMOS estimate (1991) | none | radix 2 without overlapped execution, 54 b | p.1660 |
| estimated latency | 160 | ns | 1.2-pm CMOS estimate (1991) | 225 ns radix 2 | radix 2 with overlapped execution, 54 b | p.1660 |
| estimated silicon area | 7 | mm2 | 1.2-pm CMOS estimate (1991) | none | radix 2 without overlapped execution | p.1660 |
| estimated silicon area | 10 | mm2 | 1.2-pm CMOS estimate (1991) | 7 mm2 radix 2 | radix 2 with overlapped execution | p.1660 |
| estimated radix-4 latency | 150 | ns | 1.2-pm CMOS estimate (1991) | 160 ns overlapped radix 2 | overlapped execution, 54 b | p.1660 |
| estimated radix-4 silicon area | 18 | mm2 | 1.2-pm CMOS estimate (1991) | 10 mm2 overlapped radix 2 | overlapped execution | p.1660 |
errors_and_checks: Quotient selection remains correct when the trimmed remainder sign aliases because the force-next-digit equations constrain the next selection. The final remainder sign permits correct rounding after normal or early termination. # p.1652, p.1657
conditions: Radix 2 was implemented because its fast/simple stages use less ring area; overlapped radix 4 was estimated faster but requires five larger CPA branches rather than three. # p.1659-p.1660
evidence: Section II; Sections IV-VIII; Figs. 1-10; Table II.

### carry_select  (role: instantiates)
mechanism: After iteration stops, a carry-select adder runs multiple carry chains in parallel to convert the redundant quotient and apply a possible least-significant decrement. The remainder sign and rounding alternatives select the correct carry-lookahead result, so final resolution requires one CLA and one multiplexor. # p.1657
choices:
  duplication: full_duplicate # p.1657
new_choices:
  none
slots:
  block_adder: carry_lookahead # p.1657
parameters: single additional 55-b CLA; estimated 4 to 8 ns final conversion/rounding delay # p.1659
results:
| metric | value | unit | technology / device | baseline | condition | page |
| final conversion and rounding delay | 4 to 8 | ns | 1.2-pm CMOS estimate (1991) | mantissa-operation latency | one additional 55-b CLA | p.1659 |
errors_and_checks: The terminal logic produces a correctly rounded quotient after either full iteration or early termination. # p.1657
conditions: The paper implements only the mantissa computation; exponent logic is assumed to operate in parallel. # p.1652, p.1659
evidence: Sections VI-VII.

## new_families
none

## space_gaps
* `self_timed_variable_latency.mechanism` cannot express simultaneous self-timing and repeating-remainder early termination as composable mechanisms. # p.1655-p.1657
* `srt_radix2.digit_select` permits only `qds_table`, while the design uses explicit quotient-selection equations and a force-next-digit flag. # p.1652
* The divider vocabulary lacks choices for latch-free ring stage count and adjacent-stage overlapped execution. # p.1654-p.1656

## open_questions
* The abstract reports that the ring occupies 7 mm2, the measured layout reports a 6.8 mm2 core within 9.7 mm2 active area, and Table II estimates 10 mm2 for overlapped radix 2; the merge pass must preserve the distinct area definitions. # p.1651, p.1659-p.1660
* The paper does not specify complete IEEE exception/subnormal/rounding-mode behavior because the fabricated chip implements only the mantissa path. # p.1652, p.1659
