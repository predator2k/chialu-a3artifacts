---
handle: lang_2007b
citation: Lang, Nannarelli, "Combined Radix-10 and Radix-16 Division Unit", 41st Asilomar Conference on Signals, Systems and Computers, 2007
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [bcd, binary]
authority: incremental
pages_read: 967-971 / 5
---

## summary
The document extends a radix-10 digit-recurrence divider to perform radix-16 division in the same unit. The combined unit shares quotient-digit selection, a radix-2 most-significant slice, dual-radix carry-save adders, and quotient conversion/rounding (pp.967-970).

## families
### decimal_digit_recurrence  (role: extends)
mechanism: The radix-10 recurrence computes v[j] = 10w[j-1] - qHj(5d) and w[j] = v[j] - qLjd, with qj = 5qHj + qLj. The digit components are qHj ∈ {-1,0,1} and qLj ∈ {-2,-1,0,1,2}, which give redundancy factor ρ10 = 7/9. The implementation represents the most-significant recurrence slice in radix-2 two's complement and processes the remaining digits in BCD (pp.967-969).
choices:
  quotient_digit_set: redundant_m7_p7   # p.967
  digit_split: radix2_times_radix5   # p.967
new_choices:
  none
slots:
  digit_select: qds_table   # pp.968-969
parameters: one radix-10 quotient digit per iteration; qHj ∈ {-1,0,1}; qLj ∈ {-2,-1,0,1,2}; 20 cycles in the evaluated configuration   # pp.967,970
results:
| metric | value | unit | technology / device | baseline | condition | page |
| cycle time | 1.04 | ns | STM 90 nm CMOS standard cells, 2007 | radix-10 unit: 1.00 ns | dual-radix unit in radix-10 mode | p.970 |
| cycles | 20 | cycles | STM 90 nm CMOS standard cells, 2007 | radix-10 unit: 20 cycles | dual-radix unit in radix-10 mode | p.970 |
| latency | 20.8 | ns | STM 90 nm CMOS standard cells, 2007 | radix-10 unit: 20.0 ns | dual-radix unit in radix-10 mode | p.970 |
| speed-up | 0.96 | ratio | STM 90 nm CMOS standard cells, 2007 | Table III reference is not defined explicitly | dual-radix unit in radix-10 mode | p.970 |
errors_and_checks: The unit performs quotient conversion and rounding and uses a final adder to determine the sign of the remainder and whether the remainder is zero; no numerical error bound or rounding-mode contract is reported (p.969).
conditions: The decimal path requires precomputed 5dBCD/2dBCD and their negatives, BCD-aware carry-save adders, and conversion between BCD digits and the radix-2 most-significant slice (pp.968-969). The combined unit has about 30% more area than the radix-10-only implementation (p.967).
evidence: Equations (1)-(4), Fig. 1, Table I, Fig. 3, Fig. 4, and Table III (pp.967-970).

### srt_high_radix  (role: instantiates)
mechanism: The radix-16 recurrence computes v[j] = 16w[j-1] - qHj(4d) and w[j] = v[j] - qLjd, with qj = 4qHj + qLj. Both digit components use {-2,-1,0,1,2}, which gives redundancy factor ρ16 = 10/16. The selection function is decomposed into two radix-4 selection functions, and the divisor multiples 8d/4d/2d are produced by shifts (pp.967-968).
choices:
  radix: 16   # p.967
new_choices:
  quotient_digit_decomposition: qj = 4qHj + qLj — the radix-16 digit is selected as two components from {-2,-1,0,1,2}   # p.967
slots:
  digit_select: qds_table   # pp.968-969
parameters: one radix-16 quotient digit per iteration; qHj,qLj ∈ {-2,-1,0,1,2}; 16 cycles in the evaluated configuration   # pp.967,970
results:
| metric | value | unit | technology / device | baseline | condition | page |
| cycle time | 1.04 | ns | STM 90 nm CMOS standard cells, 2007 | standard radix-16 unit: 1.00 ns | dual-radix unit in radix-16 mode | p.970 |
| cycles | 16 | cycles | STM 90 nm CMOS standard cells, 2007 | standard radix-16 unit: 16 cycles | dual-radix unit in radix-16 mode | p.970 |
| latency | 16.6 | ns | STM 90 nm CMOS standard cells, 2007 | standard radix-16 unit: 16.0 ns | dual-radix unit in radix-16 mode | p.970 |
| speed-up | 0.96 | ratio | STM 90 nm CMOS standard cells, 2007 | standard radix-16 unit: 1.00 | dual-radix unit in radix-16 mode | p.970 |
errors_and_checks: The unit performs unsigned-binary quotient conversion and rounding and tests the final remainder sign/zero condition; no numerical error bound or rounding-mode contract is reported (pp.967,969).
conditions: The radix-16 path requires five-value qH selection, a 5:1 multiple selector, two extra qH flip-flops, speculative computation of five qL outcomes, and shifted 8d/4d/2d multiples (pp.968-969). The critical-path difference from the separate units is about one INVFO4 (p.970).
evidence: Equations (1)-(4), Table I, Fig. 2, Table II, Fig. 3, Fig. 4, and Table III (pp.967-970).

## new_families
### dual_radix_digit_recurrence_divider  (domain: decimal: decimal dividers, closest: decimal_digit_recurrence, why_not: decimal_digit_recurrence does not represent one runtime-selectable unit that combines radix-10 BCD and radix-16 binary division.)
mechanism: Signal R selects r = 16 with k = 4 or r = 10 with k = 5 in the shared recurrence v[j] = rw[j-1] - qHj(kd), w[j] = v[j] - qLjd. The unit combines selection constants, divisor-multiple generation, a radix-2 most-significant slice, dual-radix carry-save adders, and conversion/rounding. Radix-specific quotient digits leave the recurrence at one digit per iteration (pp.967-970).
choices: supported_radices: {radix10_radix16}; selection_constant_organization: {separate_modules, combined_module}; ms_slice_encoding: {radix2_twos_complement}; radix_select: {runtime_R}
results:
| metric | value | unit | technology / device | baseline | condition | page |
| area | 78500 | μm² | STM 90 nm CMOS standard cells, 2007 | separate radix-16 plus radix-10 units: 97700 μm² | complete dual-radix unit | p.970 |
| area ratio | 0.80 | ratio | STM 90 nm CMOS standard cells, 2007 | separate units: 1.00 | complete dual-radix unit | p.970 |
| area reduction | about 20 | % | STM 90 nm CMOS standard cells, 2007 | separate radix-16 and radix-10 units | complete dual-radix unit | p.970 |
| area increase | about 30 | % | STM 90 nm CMOS standard cells, 2007 | radix-10-only unit | complete dual-radix unit | p.967 |
evidence: Fig. 1, Tables I-II, Figs. 3-4, Table III, and conclusions (pp.967-970).

## space_gaps
* `decimal_digit_recurrence` lacks a slot for signed-digit quotient conversion and rounding, which this unit adapts for BCD and unsigned-binary outputs (pp.967,969).
* `srt_high_radix` lacks a choice for decomposed quotient-digit selection using qj = kqHj + qLj (p.967).
* The divider vocabulary lacks a runtime dual-radix composition family for shared decimal/binary recurrence hardware (pp.967-970).

## open_questions
* The exact operand/significand widths and supported rounding modes are not stated.
* Table III does not explicitly define the reference used for every value in its speed-up column.
* The decimal mode retains qHj ∈ {-1,0,1}, although the shared hardware computes five speculative qH outcomes and the conclusion proposes changing radix-10 to {-2,-1,0,1,2} (pp.969-970).
