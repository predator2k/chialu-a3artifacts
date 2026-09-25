---
handle: ienne1994
citation: P. Ienne, M. A. Viredaz, "Bit-Serial Multipliers and Squarers", IEEE Transactions on Computers, vol. 43, no. 12, pp. 1445-1450, 1994
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [unsigned_binary, twos_complement]
authority: incremental
pages_read: 1445-1450 / 6
---

## summary
The paper proposes modular bit-serial multiplier and squarer circuits that accept least-significant-bit-first unsigned or sign-extended two’s complement inputs and produce serial full-precision results without latency clock-cycles. The circuits omit irrelevant sign-extension terms, use N - 1 one-bit slices, and can extend the result arbitrarily without extra hardware.

## families
### serial_serial_parallel  (role: proposes)
mechanism: Two operands enter serially and least significant bit first. Each slice stores operand bits, adds two new partial-product terms with a (5, 3) counter, and shifts the partial sum toward the serial output. The symmetric term x_i·y_i is added online. Terms caused by sign extension are omitted because their accumulated error is zero modulo the bits already emitted. The output begins in the first input cycle. # p.1446-p.1448
choices:
  serial_operands: both   # p.1445
  digit_size_bits: 1   # p.1447
  end_reconfigure_to_ripple: false   # p.1447-p.1449
new_choices:
  output_latency_cycles: zero — number of clock cycles between corresponding input/output bits   # p.1445
  output_length_extension: arbitrarily_long_without_extra_hardware — whether continued zero/sign extension produces further correct result bits   # p.1445
  activation_control: shift_register_or_counter_decoder — successive slices can be activated by a modular shift register or by a counter/decoder with less hardware   # p.1448
slots:
  none
parameters: two N-bit operands; K-bit product with K ≥ 2N; N - 1 slices; one bit per operand per cycle; zero clock-cycle latency   # p.1445, p.1447
results:
| metric | value | unit | technology / device | baseline | condition | page |
| output latency | zero | clock-cycle latency | UNKNOWN / 1994 | traditional bit-serial multipliers: one or more clock cycles | unsigned or sign-extended two’s complement inputs | p.1445 |
| slice count | N - 1 | one-bit slices | UNKNOWN / 1994 | UNKNOWN | two N-bit operands | p.1447 |
| silicon validation | successfully tested | — | CMOS 1.0 μm / year UNKNOWN | none | multiplier included in the GENES IV circuit | p.1449 |
errors_and_checks: The multiplier produces a full-precision result with no truncated or rounded bits when K ≥ 2N; continued zero/sign extension produces an arbitrarily long correct output. No fault checker is described.   # p.1445, p.1447, p.1449
conditions: Both operands must have the same size, so a shorter operand is extended to the longer operand’s size.   # p.1447
  Inputs must arrive least significant bit first during the first N cycles.   # p.1447
  Unsigned operands require zero extension and two’s complement operands require sign extension during the remaining K - N cycles.   # p.1447
  The slice critical path contains an AND gate, a (5, 3) counter, and a 2-input multiplexer; the multiplexer adds propagation delay relative to Dadda’s design.   # p.1448
evidence: §II; (1)-(7); Figs. 4-7; implementation statement in §IV, p.1446-p.1449

### squarer  (role: proposes)
mechanism: Identical operands permit symmetric partial products to be combined. Each cross-product term is doubled, while x_i² contributes directly. Moving a delay element after the slice adder doubles the weight of the added term. N - 1 chained slices store the operand and partial sum, producing a serial output without latency. The same circuit handles zero-extended unsigned and sign-extended two’s complement inputs. # p.1448-p.1449
choices:
  folding_scheme: basic_symmetry   # p.1448-p.1449
  combined_signed_unsigned: true   # p.1449
new_choices:
  output_latency_cycles: zero — number of clock cycles between corresponding input/output bits   # p.1449
  activation_control: shift_register_or_counter_decoder — successive slices can use modular shift-register control or counter/decoder control   # p.1448
slots:
  none
parameters: one N-bit operand; K-bit square with K ≥ 2N; N - 1 slices; one input bit per cycle; zero clock-cycle latency   # p.1448-p.1449
results:
| metric | value | unit | technology / device | baseline | condition | page |
| output latency | zero | clock-cycle latency | UNKNOWN / 1994 | UNKNOWN | unsigned or sign-extended two’s complement input | p.1449 |
| slice count | N - 1 | one-bit slices | UNKNOWN / 1994 | UNKNOWN | N-bit operand | p.1448 |
errors_and_checks: The squarer produces a correct result when K ≥ 2N and the input is extended through the remaining cycles. No fault checker is described.   # p.1448-p.1449
conditions: The unit computes only a square, which uses less hardware than implementing the operation with the companion serial-serial multiplier.   # p.1448
  The operand must arrive least significant bit first and must be zero-extended for unsigned input or sign-extended for two’s complement input.   # p.1448-p.1449
  The paper states that the squarer has the same complexity as Dadda’s unsigned squarer while also accepting two’s complement numbers.   # p.1445
evidence: §III; (8); Figs. 8-11; §IV, p.1448-p.1449

## new_families
none

## space_gaps
* The squarer reduction slot cannot represent the paper’s serial (5, 3)-counter slice, which performs iterative local reduction rather than a `csa_reduction_tree` or `compressor_4_2_tree`.   # p.1448-p.1449

## open_questions
* The paper does not report area, clock frequency, power, or an absolute combinational-delay measurement.
* The paper does not state whether the perfectly modular shift-register version or the counter/decoder alternative was used in the manufactured GENES IV multiplier.
* The paper reports Compass ASIC simulation for both units but reports manufactured-silicon testing only for the multiplier.
