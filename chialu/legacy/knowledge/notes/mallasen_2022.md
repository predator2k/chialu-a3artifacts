---
handle: mallasen_2022
citation: D. Mallasén, R. Murillo, A. A. Del Barrio, G. Botella, L. Piñuel, M. Prieto-Matías, "PERCIVAL: Open-Source Posit RISC-V Core With Quire Capability", IEEE Transactions on Emerging Topics in Computing, 2022
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU, VEC_SFU, VEC_DOT_ACC, other]
formats: [posit32_2, fp32, fp64, int32, int64]
authority: incremental
pages_read: 1-12 / 12
---

## summary
PERCIVAL adds native 32-bit posit arithmetic, a 512-bit quire, a posit register file, and Xposit instructions to the CVA6 RV64GC core while retaining fp32/fp64 hardware. The PAU implements exact posit add/multiply, logarithm-approximate divide/square root, fused quire operations, conversions, and integer-ALU comparisons. FPGA/ASIC results show that the quire dominates PAU cost but reduces GEMM MSE by up to four orders of magnitude without slowing large GEMMs relative to fp32.

## families
### posit_adder_multiplier  (role: instantiates)
mechanism: The unpipelined multi-cycle PAU contains dedicated posit add, multiply, approximate divide/square-root, conversion, and quire blocks. The ADD block performs subtraction by taking the second operand’s two’s complement. PERCIVAL uses Posit〈32,2〉 and retains separate IEEE fp32/fp64 units.
choices:
  es_bits: 2   # p.4
  approximation: none   # p.4
new_choices:
  none
slots:
  none
parameters: Posit〈32,2〉; PADD/PSUB latency 2 cycles; PMUL latency 1 cycle; no PAU pipeline   # p.4
results:
| metric | value | unit | technology / device | baseline | condition | page |
| area without quire | 5346 | LUTs | 2022; Xilinx Kintex-7 XC7K325T-2FFG900C | fp32 FPU: 4046 LUTs | PAU modules excluding quire | p.7 |
| state without quire | 1318 | FFs | 2022; Xilinx Kintex-7 XC7K325T-2FFG900C | fp32 FPU: 973 FFs | PAU modules excluding quire | p.7 |
| area without quire | 40 524.62 | µm2 | 2022; TSMC 45nm | fp32 FPU: 30 691 µm2 | 5ns constraint | p.8 |
| power without quire | 37.62 | mW | 2022; TSMC 45nm | fp32 FPU: 27.26 mW | toggle rate 0.1 | p.8 |
errors_and_checks: Addition and multiplication use standard posit rounding; no numerical error bound is reported for these exact blocks.   # pp.3-4
conditions: The PAU without quire uses 1.32 times the ASIC area and 1.38 times the power of the fp32 FPU. The authors note that newer two’s-complement posit decoding may reduce cost.   # pp.7-8
evidence: §4.1, Fig. 2, Tables 4-5.

### posit_quire_mac  (role: proposes)
mechanism: A single internal 512-bit two’s-complement quire accumulates QMADD.S/QMSUB.S products without intermediate rounding. QCLR.S initializes the quire, QNEG.S negates it, and QROUND.S converts the final value to Posit32. The quire cannot be loaded/stored and cannot support simultaneous independent accumulations.
choices:
  quire_width_bits: 512   # pp.3-4
  organization: monolithic_register   # pp.4-5
  op_set: fused_dot_product   # pp.4,8
new_choices:
  none
slots:
  none
parameters: 16n-bit quire with n=32; up to 2^31−1 MAC operations; QMADD/QMSUB latency 2 cycles; QROUND latency 1 cycle   # pp.3-4
results:
| metric | value | unit | technology / device | baseline | condition | page |
| total PAU area | 11 879 | LUTs | 2022; Xilinx Kintex-7 XC7K325T-2FFG900C | fp32 FPU: 4046 LUTs | quire included | p.7 |
| total PAU state | 2985 | FFs | 2022; Xilinx Kintex-7 XC7K325T-2FFG900C | fp32 FPU: 973 FFs | quire included | p.7 |
| total PAU area | 76 970.38 | µm2 | 2022; TSMC 45nm | fp32 FPU: 30 691 µm2 | quire included; 5ns constraint | p.8 |
| total PAU power | 67.73 | mW | 2022; TSMC 45nm | fp32 FPU: 27.26 mW | toggle rate 0.1 | p.8 |
| GEMM MSE | 1.937 × 10−16 | UNKNOWN | 2022; UNKNOWN | fp32 fused: 2.361 × 10−12 | 256×256; inputs [−1,1]; fp64 golden result | p.10 |
| GEMM time | 13.9 | s | 2022; PERCIVAL | fp32 fused: 13.9 s; fp64 fused: 15.0 s | 256×256 | p.10 |
errors_and_checks: The quire avoids intermediate rounding and accuracy loss. For 256×256 GEMM over [−1,1], Posit32 MSE is 1.937 × 10−16 versus 9.870 × 10−15 without quire.   # p.10
conditions: The quire occupies about half the PAU area. A single non-loadable quire prevents parallel independent accumulations and safe automatic context switches.   # pp.7,10
evidence: §2.1, §4.1, §7, Tables 3-7, Figs. 6-7.

### approximate_functional  (role: instantiates)
mechanism: PDIV and PSQRT use logarithm-approximate units derived from Mitchell’s Approximate Log Multipliers. The approximation reduces area/performance impact relative to exact operators; exact division and square root could instead be implemented in software using the MAC unit.
choices:
  method: log_subtract_corrected   # p.4
new_choices:
  operation_set: division_and_square_root — selects which posit operations use the logarithmic approximation   # p.4
slots:
  none
parameters: Posit〈32,2〉; PDIV/PSQRT latency 1 cycle   # p.4
results:
| metric | value | unit | technology / device | baseline | condition | page |
| maximum relative error | 11.11% | UNKNOWN | 2022; UNKNOWN | exact hardware operators | posit division/square root | p.4 |
| division area | 413 | LUTs | 2022; Xilinx Kintex-7 XC7K325T-2FFG900C | UNKNOWN | Posit ADiv | p.7 |
| square-root area | 426 | LUTs | 2022; Xilinx Kintex-7 XC7K325T-2FFG900C | UNKNOWN | Posit ASqrt | p.7 |
errors_and_checks: Maximum relative error is 11.11%.   # p.4
conditions: The units trade exactness for lower hardware cost. Exact software implementations using the MAC are described as possible but are not evaluated.   # p.4
evidence: §4.1, Tables 4-5.

### integer_compare_on_bits  (role: instantiates)
mechanism: Posit encodings preserve signed ordering, and NaR maps to the most negative two’s-complement integer. PERCIVAL therefore executes posit comparison/minimum/maximum operations in the existing integer ALU.
choices:
  signed_zero_ordering: false   # pp.1-2
new_choices:
  special_value_ordering: NaR_equal_to_itself_and_less_than_all_posits — comparison behavior for NaR   # p.2
slots:
  none
parameters: Posit32; comparison result available in the next clock cycle with no stated execution latency   # p.4
results:
| metric | value | unit | technology / device | baseline | condition | page |
| comparison latency | 0 | cycles | 2022; UNKNOWN | fp32 FPU comparison: 1 cycle | integer-ALU reuse | p.4 |
errors_and_checks: none
conditions: Integer comparison reuse depends on the posit encoding’s two’s-complement signed ordering.   # pp.2,5
evidence: §2.1, §4.1-4.2.

### posit_ieee_interop  (role: extends)
mechanism: PERCIVAL retains the CVA6 fp32/fp64 FPU and adds a separate Posit32 PAU/register file, so posit and IEEE instructions execute natively on the same core. The scoreboard, decoder, issue path, and write-back path distinguish posit registers and operations.
choices:
  interop_style: separate_parallel_datapaths [outside domain]   # pp.3-5
  quire_present: true   # pp.3-4
new_choices:
  none
slots:
  none
parameters: RV64GCXposit; 32 posit registers p0-p31; separate integer/floating-point/posit register files   # pp.4-5
results:
| metric | value | unit | technology / device | baseline | condition | page |
| total core area | 44 693 | LUTs | 2022; Xilinx Kintex-7 XC7K325T-2FFG900C | bare CVA6: 28 950 LUTs | PAU with quire; no FPU | p.7 |
| total core state | 23 636 | FFs | 2022; Xilinx Kintex-7 XC7K325T-2FFG900C | bare CVA6: 19 579 FFs | PAU with quire; no FPU | p.7 |
errors_and_checks: none
conditions: The separate datapaths preserve simultaneous posit/fp32/fp64 support but add register-file, decoding, scoreboard, and interconnection costs.   # pp.4-7
evidence: §4.2, §5, Tables 1-3.

## new_families
none

## space_gaps
* `posit_ieee_interop.interop_style` lacks `separate_parallel_datapaths`, which PERCIVAL uses instead of converters or one unified datapath.   # pp.3-5
* `approximate_functional` lacks square-root coverage even though the same logarithm-approximate approach implements PDIV and PSQRT.   # p.4
* `posit_quire_mac.quire_width_bits` excludes the general `16n` sizing rule and widths other than its enumerated 128/256/512 values.   # p.3

## open_questions
* The paper does not specify the internal adder/multiplier topology, regime-decoder structure, or final quire carry-propagate adder.
* The paper attributes the 11.11% maximum relative error jointly to division and square root without reporting separate bounds.
