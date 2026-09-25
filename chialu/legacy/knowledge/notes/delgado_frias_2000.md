---
handle: delgado_frias_2000
citation: J. G. Delgado-Frias, J. Nyathi, "A High-Performance Encoder with Priority Lookahead", IEEE Transactions on Circuits and Systems I, vol. 47, no. 9, pp. 1390-1393, 2000
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [binary]
authority: incremental
pages_read: pp. 1390-1393 / 4 pages
---

## summary
The paper proposes a dynamic CMOS priority encoder whose priority-lookahead line reduces propagation delay across four-input segments. A simulated 32-bit implementation achieves a 4.4 ns worst-case delay with 9.4% more transistors than the encoder without lookahead.

## families
### priority_encoder  (role: proposes)
mechanism: An N-input fixed-priority encoder sets only the output corresponding to the highest-priority asserted request. The priority-lookahead implementation partitions the encoder into four-bit segments and precharges each lookahead line. An asserted request discharges the segment lookahead line, which propagates priority status between cells faster than the basic pass-transistor priority chain. Cascaded four-bit modules include intermodule discharge/precharge circuitry. # pp.1390-1392
choices:
  lookahead_group: 4  # p.1390
  levels: 1  # p.1390
  output_form: one_hot_only [outside domain]  # p.1390
new_choices:
  circuit_style: dynamic_pass_transistor — precharged priority/lookahead lines use pass transistors and pull-down devices  # pp.1390-1392
  priority_policy: fixed_wired — priority changes only when encoder wiring changes  # p.1390
slots:
  none
parameters: N inputs/outputs; four-bit lookahead segments; tested width 32 bits; Tpp width:length 4:1; PL inverter p-type transistor width:length 6:1  # pp.1390, 1392
results:
| metric | value | unit | technology / device | baseline | condition | page |
| worst-case propagation delay | 4.4 | ns | 1-µm scalable CMOS; 2000 | encoder without PL: 11.4 ns | 32-bit encoder; first and last requests asserted; remaining requests deasserted | p.1392 |
| worst-case propagation delay | 11.4 | ns | 1-µm scalable CMOS; 2000 | none | 32-bit encoder without PL; same worst-case request pattern | p.1392 |
| delay ratio | 2.59 | × | 1-µm scalable CMOS; 2000 | encoder without PL | 11.4 ns / 4.4 ns | p.1392 |
| performance improvement | 159 | % | 1-µm scalable CMOS; 2000 | encoder without PL | 32-bit encoder | pp.1392-1393 |
| transistor-count expression | 16N + 6(N/4) | transistors | 1-µm scalable CMOS; 2000 | without PL: 15N + 4(N/4) | N-bit encoder with four-bit modules | pp.1392-1393 |
| transistor-count ratio | 1.094 | × | 1-µm scalable CMOS; 2000 | encoder without PL | N-bit encoder with four-bit modules | p.1392 |
| transistor-count increase | 9.4 | % | 1-µm scalable CMOS; 2000 | encoder without PL | N-bit encoder with four-bit modules | p.1392 |
errors_and_checks: Functionality is evaluated by SPICE simulation; no fault model, detection coverage, false-alarm behavior, or alias rate is reported.  # p.1392
conditions: The design implements static priority that changes only through wiring. # p.1390 The four-bit segment is selected as a compromise between fan-out and delay. # p.1390 The dynamic cells require a precharge phase before processing requests. # p.1391 The reported critical case asserts the first and last requests while deasserting all intermediate requests. # p.1392 The study excludes a cascaded standard-gate implementation because it requires many more transistors without much performance gain. # p.1392
evidence: Equations (1)-(6) and Section I, p.1390; Figs. 1-4 and Section II, pp.1391-1392; Figs. 5-6, Table I, equations (7)-(8), and Section III, pp.1392-1393.

## new_families
none

## space_gaps
* The `output_form` domain lacks `one_hot_only`, which describes the paper's N-output highest-request indication without a binary encoding stage. # p.1390
* The `priority_encoder` family lacks a `circuit_style` choice for the dynamic pass-transistor implementation. # pp.1390-1392
* The `priority_encoder` family lacks a `priority_policy` choice distinguishing fixed-wired priority from configurable priority. # p.1390

## open_questions
* A four-input second-level priority lookahead, P2L, is described for positions above 16, but the paper does not implement or evaluate it. # p.1390
* The supplied text does not report the supply voltage, output load, or detailed scalable-CMOS process parameters used for the delay simulations. # pp.1392-1393
