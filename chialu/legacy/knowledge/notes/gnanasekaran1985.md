---
handle: gnanasekaran1985
citation: R. Gnanasekaran, "A Fast Serial-Parallel Binary Multiplier", IEEE Transactions on Computers, vol. C-34, pp. 741-744, 1985
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [unsigned_binary, twos_complement]
authority: incremental
pages_read: 4 / 4 (pp. 741-744)
---

## summary
The fast serial-parallel multiplier performs carry-save add-shift processing for n clocks and then reconfigures as an (n - 1)-bit ripple-carry parallel adder. (pp.741-742) The modeled design is about one-third faster than a conventional CSAS multiplier for an approximately one-third hardware increase. (pp.742-744) The signed extension handles 2's-complement operands without external correction. (pp.743-744)

## families
### serial_serial_parallel  (role: proposes)
mechanism: The multiplicand is available in parallel, while multiplier bits enter lsb first and product lsb bits leave serially. The structure operates as a carry-save add-shift unit during row accumulation. At the end of accumulation, Q stops the clocked operation and enables a second set of adders to resolve the stored sum/carry words through an (n - 1)-bit ripple path. The 2's-complement version selects direct or carry-generated sign extension and complements the multiplicand during the final row when bn = 1. (pp.741-744)
choices:
  serial_operands: one   # p.741
  digit_size_bits: 1   # p.741
  end_reconfigure_to_ripple: true   # pp.741-742
new_choices:
  product_delivery: serial_lsb_parallel_msb — records that the first (n - 1) product bits leave serially while the remaining (n + 1) bits become available in parallel   # p.743
slots:
  none
parameters: n-bit operands; multiplier order lsb first; first n row-addition clocks; terminal delay (n - 1)tFA; (n - 1) serial lsb outputs and (n + 1) parallel msb outputs; modular 4-bit implementation shown   # pp.741-743
results:
| metric | value | unit | technology / device | baseline | condition | page |
| modeled multiplication time | (5n-1)t | UNKNOWN | UNKNOWN / 1985 | CSAS: 8nt; Chen and Willoner: 8nt; parallel array: nt | β = 4 | p.743 |
| delay ratio | 0.625 | ratio | UNKNOWN / 1985 | CSAS multiplier | β = 4 and Tcell = βtFA | p.742 |
| speed increase | about one-third | increase | UNKNOWN / 1985 | conventional CSAS/add-shift technique | approximately one-third hardware increase | pp.741-742 |
| clocks saved | about (3/4)n | clock pulses | UNKNOWN / 1985 | CSAS multiplier | parallel-adder delay spans (n - 1)/4 clocks with β = 4 | p.743 |
| hardware | 4(n-1) | equivalent basic 1 bit full-adder circuits | UNKNOWN / 1985 | CSAS: 3(n-1); Chen and Willoner: 5n; parallel array: n(n-1) | modulo counters excluded | p.743 |
errors_and_checks: none
conditions: All multiplicand bits must be available at the beginning, while multiplier bits are accepted lsb first. (p.741) The speed model assumes β = 4, although β is stated to range from 2 to 6. (p.742) The hardware comparison excludes the modulo counters, and the FSP implementation requires two modulo counters. (p.743) The implementation targets the hardware/power versus speed tradeoff for a fixed circuit technology. (pp.741-744)
evidence: Abstract and §I on p.741; Fig. 3 and (1)-(7) on p.742; Table I and Fig. 4 on p.743; Fig. 6 and §IV on p.744.

### carry_save_datapath  (role: instantiates)
mechanism: The first n row additions retain separate sum/carry words in feedback latches. Conventional CSAS spends the next n clocks propagating those carries. The FSP modification instead assimilates the final sum/carry words with a parallel ripple adder, which removes accumulated storage/gating delay from the carry-resolution phase. (pp.741-742)
choices:
  assimilation_point: end_of_chain   # pp.741-742
  accumulator_redundant: true   # pp.741-742
new_choices:
  none
slots:
  assimilator: ripple_carry   # pp.741-742
parameters: n carry-save row additions; one multiplier bit processed per clock; separate n-bit sum/carry words before assimilation   # pp.741-742
results: none
errors_and_checks: none
conditions: Carry-save operation applies during partial-product accumulation and terminates before the final carry propagation. (pp.741-742)
evidence: Fig. 2 and §II-A on pp.741-742; equations (3)-(5) on p.742.

### ripple_carry  (role: instantiates)
mechanism: A second set of full adders forms an (n - 1)-bit parallel ripple adder after carry-save accumulation. The ripple path adds the stored sum/carry words without passing through the feedback storage elements used by conventional CSAS carry propagation. (pp.741-742)
choices:
new_choices:
  none
slots:
  none
parameters: width (n - 1) bits; delay Tp = (n - 1)tFA   # p.742
results:
| metric | value | unit | technology / device | baseline | condition | page |
| terminal parallel-adder delay | (n - 1)tFA | UNKNOWN | UNKNOWN / 1985 | conventional CSAS uses n additional clock intervals | ripple-carry full-adder path | p.742 |
errors_and_checks: none
conditions: The delay analysis treats each ripple stage as one full-adder delay, tFA. (p.742)
evidence: Fig. 3 and equation (2) on p.742; Table I on p.743.

## new_families
none

## space_gaps
* `serial_serial_parallel` lacks a terminal-adder component slot for the document's explicitly instantiated `(n - 1)`-bit `ripple_carry` adder. (pp.741-742)
* `serial_serial_parallel` lacks a product-delivery choice for the mixed serial-lsb/parallel-msb interface. (p.743)

## open_questions
* The abstract describes CSAS operation for the first n clocks and reconfiguration at the (n + 1)st clock, while §II-A says the structure acts as CSAS during the first (n - 1) clocks and Q is set by the nth clock. (pp.741-742)
* Table I prints speed formulas using `t` without explicitly defining `t` in the supplied text. (p.743)
