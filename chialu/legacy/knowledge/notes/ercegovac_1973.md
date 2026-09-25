---
handle: ercegovac_1973
citation: M. D. Ercegovac, "Radix-16 Evaluation of Certain Elementary Functions", IEEE Transactions on Computers, vol. C-22, no. 6, pp. 561-566, 1973
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU, VEC_SFU]
formats: [binary_floating_point]
authority: incremental
pages_read: 561-566 / 6
---

## summary
The paper extends continued-product/continued-sum algorithms for division, logarithms, and exponentials to radix 16, producing four result bits per step (p.561). The paper defines multiplicative/additive normalization recurrences and compares estimated radix-16 hardware/performance with radix 2 (pp.561-565).

## families
### digit_recurrence_exp_log  (role: extends)
mechanism: Multiplicative normalization recursively transforms the argument with factors \(M_k=1+S_k16^{-k}\), while logarithm evaluation accumulates \(-\ln(M_k)\) (pp.561-563). Exponential evaluation uses additive normalization of the reduced argument and forms the result through the same continued-product factors (pp.563-564). Rounded scaled remainders select symmetric redundant digits, with specialized selection in the initial irregular steps (pp.561-564).
choices:
  radix: 16   # p.561
  normalization: multiplicative for logarithm; additive for exponential   # pp.563-564
  digit_set: signed_redundant   # p.561
  selection: rounding_of_scaled_residual   # pp.561-564
new_choices:
  execution_organization: {two_arithmetic_units, one_pipelined_arithmetic_unit} — whether normalization/result evaluation use separate units or overlap in one pipelined unit   # pp.564-565
slots:
  none
parameters: m=M/4 radix-16 digits; 4 bits/step; \(S_k\in\{-10,\ldots,10\}\); redundancy ratio 4/3; logarithm/exponential constants stored to m-digit precision in ROM   # pp.561,563-564
results:
| metric | value | unit | technology / device | baseline | condition | page |
| hardware requirement ratio | approximately 2:3 | radix-2:radix-16 ratio | UNKNOWN; year 1973 | radix 2 | complete arithmetic unit estimate | p.564 |
| ROM capacity ratio | about 1:3 | radix-2:radix-16 ratio | UNKNOWN; year 1973 | radix 2 | favors the binary/radix-2 case | p.565 |
| average performance ratio \(P_{16}/P_2\) | approximately 4/3 | ratio | UNKNOWN; year 1973 | radix 2 | radix-2 zero-digit bypass gives M/3 average cycles; radix 16 uses M/4 cycles | p.565 |
| efficiency ratio \(E_{16}/E_2\) | approximately 1 | ratio | UNKNOWN; year 1973 | radix 2 | ROM requirements excluded | p.565 |
| pipelined-mode performance | 15-25 percent lower | percent | UNKNOWN; year 1973 | two separate arithmetic units | normalization/result evaluation overlapped in one unit | p.565 |
errors_and_checks: Logarithm has accumulated roundoff from m-digit ROM constants, with a bound proportional to \(m16^{-m}\); the leading coefficient is not legible in the supplied text (p.563). No fault-detection mechanism is discussed.
conditions: The algorithms cover only fractional parts of radix-2 floating-point numbers (p.561). Logarithm reduces \(X=X_02^E\) and evaluates \(\ln X_0\) (p.563). Exponential reduces the argument to \(X_0\in(-\ln2,0]\), with the power-of-two factor incorporated into the exponent (pp.563-564). Radix 16 provides shorter execution time, while radix 2 requires less hardware and ROM capacity (pp.564-565). The comparisons are implementation estimates rather than measurements from a specified technology (pp.564-565).
evidence: Algorithms N/L/E and (2.1)-(2.11), (5.1)-(5.5), (6.1)-(6.6); Figs. 2, 4, 5, and 6; Sections II, V-VIII (pp.561-565).

### barrel_mux_tree  (role: instantiates)
mechanism: A fast variable shifting network of the “barrel switch” type shifts normalization/result-evaluation operands within the radix-16 arithmetic unit (pp.564-565).
choices:
new_choices:
  none
slots:
  none
parameters: width and stage organization UNKNOWN   # pp.564-565
results:
| metric | value | unit | technology / device | baseline | condition | page |
| shifting-network hardware | more than 30 percent more | percent | UNKNOWN; year 1973 | radix-16 network | radix-2 implementation | p.564 |
| shifting delay | \(t_{sh2}>1.3t_{sh16}\) | delay relation | UNKNOWN; year 1973 | radix-16 network | radix-2 versus radix-16 implementation | p.564 |
errors_and_checks: none
conditions: The network comparison is an estimate for the paper’s radix-2/radix-16 implementations (p.564).
evidence: Section VII and Figs. 2, 3, 5, and 6 (pp.563-565).

## new_families
### continued_product_division  (domain: div: dividers / square root, closest: srt_high_radix, why_not: The quotient is formed by a continued-product recurrence driven by multiplicative normalization rather than by SRT quotient-digit selection.)
mechanism: Multiplicative normalization selects \(S_k\) so that \(X_0\prod_{i=0}^{m}M_i\) approaches 1, where \(M_k=1+S_k16^{-k}\). Result evaluation begins with \(Q_0=Y_0\) and applies \(Q_{k+1}=Q_k(1+S_k16^{-k})\), producing an approximation to \(Y_0/X_0\) (p.562). Normalization/result evaluation can use two units or overlap in a split, pipelined arithmetic unit (pp.564-565).
choices: radix: {16}; result_recurrence: {continued_product}; digit_set: {symmetric_redundant_m10_p10}; execution_organization: {separate_units, overlapped_pipeline}
results:
| metric | value | unit | technology / device | baseline | condition | page |
| relative error | \(|\delta|=|\epsilon_{m+1}|\) | dimensionless | UNKNOWN; year 1973 | exact \(Y_0/X_0\) | quotient after multiplicative normalization/result evaluation | p.562 |
evidence: Algorithm D, (4.1)-(4.5), Figs. 1-3 and 6 (pp.562-565).

## space_gaps
* `digit_recurrence_exp_log` lacks an execution-organization choice for separate versus overlapped normalization/result-evaluation units (pp.564-565).
* `digit_recurrence_exp_log` lacks a shifting-network slot that `barrel_mux_tree` can fill (pp.564-565).
* `digit_set: signed_redundant` does not preserve the paper’s specific \(S_k\in\{-10,\ldots,10\}\) set and redundancy ratio 4/3 (p.561).
* The divider vocabulary lacks the continued-product division mechanism defined by Algorithm D (p.562).

## open_questions
* The leading coefficient in the logarithm accumulated-roundoff bound is not legible in the supplied text (p.563).
* The paper does not specify a technology node/device, fabricated implementation, operand width M, or clock frequency for its hardware/performance estimates (pp.561,564-565).
