---
handle: bayrakci_2007
citation: Bayrakci, Akkas, "Reduced Delay BCD Adder", IEEE ASAP, 2007
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [bcd]
authority: incremental
pages_read: 266-271 / 6
---

## summary
The paper proposes a 64-bit BCD adder that computes independent 4-bit binary sums, derives decimal digit generate/propagate signals, resolves carries through a Kogge-Stone parallel-prefix network, and applies correction with parallel 4-bit adders. The paper compares the proposed adder with five BCD adders synthesized in the same 0.18 micron TSMC standard-cell library and reports the shortest delay for the proposed design. (p.266, pp.268-271)

## families
### bcd_direct_addition  (role: proposes)
mechanism: Sixteen independent 4-bit adders compute the binary digit sums without incoming decimal carries. Each adder/analyzer produces DG when the two-digit sum is at least 10 and DP when the sum is 9. A parallel carry network evaluates `OutputCarry = DG + DP · InputCarry`. Independent correction adders then add 0, 1, 6, or 7 according to the digit carry-in/carry-out combination, so only the carry network has width-dependent delay. (pp.267-269)
choices:
  digit_code: bcd8421   # pp.267-268
  correction_placement: postsum_plus6   # pp.268-269
  carry_scheme: full_lookahead   # pp.268-269
new_choices:
  carry_network_structure: parallel_prefix — The decimal DG/DP recurrence can use a parallel-prefix network or two-level carry-lookahead logic; the implementation uses Kogge-Stone.   # pp.268-269
slots:
  digit_adder: carry_lookahead   # p.268
parameters: 64-bit BCD operands; 16 decimal digits; independent 4-bit first-level adders; independent 4-bit correction adders; one Kogge-Stone carry network   # pp.268-270
results:
| metric | value | unit | technology / device | baseline | condition | page |
| delay | 1.40 | ns | TSMC 0.18 micron CMOS standard cell library; 2007 | five implemented decimal adders | 64-bit BCD addition | p.271 |
| area | 1422 | gates | TSMC 0.18 micron CMOS standard cell library; 2007 | five implemented decimal adders | 64-bit BCD addition | p.271 |
| delay | 11.03 | ns | TSMC 0.18 micron CMOS standard cell library; 2007 | proposed reduced-delay BCD adder | conventional BCD adder; 64-bit BCD addition | p.271 |
| area | 955 | gates | TSMC 0.18 micron CMOS standard cell library; 2007 | proposed reduced-delay BCD adder | conventional BCD adder; 64-bit BCD addition | p.271 |
| delay | 3.41 | ns | TSMC 0.18 micron CMOS standard cell library; 2007 | proposed reduced-delay BCD adder | modified Hwang adder; 64-bit BCD addition | p.271 |
| area | 1762 | gates | TSMC 0.18 micron CMOS standard cell library; 2007 | proposed reduced-delay BCD adder | modified Hwang adder; 64-bit BCD addition | p.271 |
| delay | 4.74 | ns | TSMC 0.18 micron CMOS standard cell library; 2007 | proposed reduced-delay BCD adder | RBCD adder; 64-bit BCD addition | p.271 |
| area | 3784 | gates | TSMC 0.18 micron CMOS standard cell library; 2007 | proposed reduced-delay BCD adder | RBCD adder; 64-bit BCD addition | p.271 |
| delay | 1.54 | ns | TSMC 0.18 micron CMOS standard cell library; 2007 | proposed reduced-delay BCD adder | CLA version of Schmookler adder; 64-bit BCD addition | p.271 |
| area | 1336 | gates | TSMC 0.18 micron CMOS standard cell library; 2007 | proposed reduced-delay BCD adder | CLA version of Schmookler adder; 64-bit BCD addition | p.271 |
| delay | 1.69 | ns | TSMC 0.18 micron CMOS standard cell library; 2007 | proposed reduced-delay BCD adder | modified Thompson et al. adder; 64-bit BCD addition | p.271 |
| area | 2369 | gates | TSMC 0.18 micron CMOS standard cell library; 2007 | proposed reduced-delay BCD adder | modified Thompson et al. adder; 64-bit BCD addition | p.271 |
errors_and_checks: Exact decimal addition for valid BCD operands; no fault model or error-rate measurements are reported.   # pp.266-271
conditions: The design supports decimal addition rather than binary addition. Subtraction requires 10's-complement arithmetic, the 9's complement of the second operand, and carry-in set to 1. The comparison modifies three prior adders and uses synthesis estimates rather than fabricated measurements.   # pp.268-271
evidence: §2; §3; Figures 2-4; Table 1; §4; Table 2; §5, pp.267-271

### parallel_prefix  (role: instantiates)
mechanism: The carry network applies the decimal recurrence `OutputCarry = DG + DP · InputCarry` to all digit positions. The paper states that any binary parallel-prefix scheme can compute this recurrence and implements a Kogge-Stone network to reduce decimal carry delay. The first-level and correction adders operate independently for every digit, which leaves this network as the only width-dependent part. (pp.268-269)
choices:
  topology: kogge_stone   # p.269
new_choices:
  prefix_signal_semantics: decimal_digit_generate_propagate — Prefix inputs are DG/DP signals derived from BCD digit sums rather than binary bit generate/propagate signals.   # p.268
slots:
  none
parameters: 16 digit positions for 64-bit BCD operands   # pp.269-270
results:
| metric | value | unit | technology / device | baseline | condition | page |
| delay | 1.40 | ns | TSMC 0.18 micron CMOS standard cell library; 2007 | five implemented decimal adders | complete 64-bit reduced-delay BCD adder using Kogge-Stone carry network | p.271 |
errors_and_checks: none
conditions: The paper reports only complete-adder delay/area, so it does not isolate the carry network's delay/area. A two-level carry-lookahead network is an alternative, but the evaluated design uses Kogge-Stone.   # pp.268-269
evidence: Equation 1; Figures 3-4; §3, pp.268-269; Table 2, p.271

## new_families
none

## space_gaps
* `bcd_direct_addition.carry_scheme` lacks a `parallel_prefix` value for the implemented decimal carry network.   # pp.268-269
* `bcd_direct_addition` lacks a slot for the decimal carry network, which this design fills with `parallel_prefix`.   # pp.268-269
* `bcd_direct_addition.correction_placement` does not express parallel selection among corrections 0/1/6/7.   # p.268

## open_questions
* The paper calls the first-level unit a 4-bit binary CLA in Figure 2 but labels other first-level/correction units only as 4-bit binary adders, so the exact adder family for every digit stage is ambiguous.   # pp.268-269
* The paper does not report the Kogge-Stone valency, fanout cap, wire-track budget, or node style.   # pp.268-270
