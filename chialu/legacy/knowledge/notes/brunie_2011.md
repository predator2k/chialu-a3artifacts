---
handle: brunie_2011
citation: N. Brunie, F. de Dinechin, B. de Dinechin, "Mixed-Precision Fused Multiply and Add", 45th Asilomar Conference on Signals, Systems and Computers, 2011
actual_citation: Nicolas Brunie, Florent de Dinechin, Benoit de Dinechin, "A Mixed-Precision Fused Multiply and Add", 45th Asilomar Conference on Signals, Systems and Computers, 2011
status: ok
kind: paper
unit_classes: [VEC_DOT_ACC]
formats: [binary16, binary32, binary64, binary128]
authority: incremental
pages_read: 165-169 / 5
---

## summary
The document proposes MPFMAk, which multiplies binaryk operands and adds the exact product to a binary2k addend with one rounding to binary2k. The product-anchored MPFMA32 supports subnormals, binary32 FMA, and binary64 addition in a three-stage implementation occupying 14000 μm² in 28 nm technology. The document reports the MPFMA32 area as one third above FMA32 at the same 3.5 ns latency.

## families
### mixed_precision_cascade_fma  (role: proposes)
mechanism: MPFMAk computes R = ◦(A × B + C), where A/B use binaryk and C/R use binary2k. A product-anchored datapath computes the product while shifting the addend into a roughly 3q-bit register. A 2p post-multiplier shifter normalizes subnormal products, which reduces the effective adder to 2q + 6 bits and the LZC/LZA to q + 3 bits. The binaryk product is exact in binary2k before the single binary2k rounding. Minor multiplexing/exponent changes also support binary2k addition, while an additional rounding module supports binaryk FMA.
choices:
  exact_product_preserved: true   # p.166
  two_term_expansion_output: false   # p.165
new_choices:
  alignment_anchor: product — whether the fixed datapath anchor is the product rather than the larger operand   # pp.167-168
  auxiliary_operations: binaryk_fma_and_binary2k_addition — which simpler operations the MPFMA datapath supports   # pp.167-168
slots:
  align: full_align   # pp.167-168
parameters: k ∈ {16, 32, 64}; A/B are binaryk; C/R are binary2k; q ≥ 2p + 2; MPFMA32 has p = 24, q = 53, a 112-bit effective addition, and 3 pipeline stages   # pp.165-168
results:
| metric | value | unit | technology / device | baseline | condition | page |
| area | 10566 | μm² | 28 nm component library / 2011 | none (absolute) | FMA32; 3 pipeline stages | p.168 |
| best latency | 3.5 | ns | 28 nm component library / 2011 | none (absolute) | FMA32; 3 pipeline stages | p.168 |
| area | 24500 | μm² | 28 nm component library / 2011 | none (absolute) | FMA64; 3 pipeline stages | p.168 |
| best latency | 3.5 | ns | 28 nm component library / 2011 | none (absolute) | FMA64; 3 pipeline stages | p.168 |
| area | 8800 | μm² | 28 nm component library / 2011 | none (absolute) | Add64; 3 pipeline stages | p.168 |
| best latency | 3.5 | ns | 28 nm component library / 2011 | none (absolute) | Add64; 3 pipeline stages | p.168 |
| area | 14000 | μm² | 28 nm component library / 2011 | none (absolute) | MPFMA32 with FMA32/Add64 support; 3 pipeline stages | p.168 |
| best latency | 3.5 | ns | 28 nm component library / 2011 | none (absolute) | MPFMA32 with FMA32/Add64 support; 3 pipeline stages | p.168 |
| area increase | one third | more than FMA32 area | 28 nm component library / 2011 | FMA32 | MPFMA32 with FMA32/Add64 support | p.168 |
| area saved by removing an auxiliary operation | a few hundred | μm² | 28 nm component library / 2011 | full MPFMA32 | remove either FMA32 or Add64 support | p.168 |
errors_and_checks: AB is exact without over-/underflow in binary2k, and AB+C receives one final IEEE-754-2008 binary2k rounding; the operator fully supports subnormals and gives a bit-identical result for the stated C99/IEEE-754 mixed-precision accumulation. Constructed special cases and millions of random vectors were tested, but no measured error or coverage rate is reported.   # pp.165-166, 168
conditions: The alignment analysis assumes q ≥ 2p + 2. The product-anchored organization hides the large alignment shifter behind the multiplier but uses a roughly 3q-bit register. Carry-save representation is absent because the existing fixed-point multiplier cannot expose a carry-save result. The compared operators use the same processor context/design effort and are acknowledged as not fully optimized. No power result is reported.   # pp.166-168
evidence: §II-B, pp.165-166; §III-B-E and Figs. 1-3, pp.166-167; §IV-A and Fig. 4, pp.167-168; §V and Table II, p.168

## new_families
none

## space_gaps
* The `mixed_precision_cascade_fma` family lacks an alignment-anchor choice for the documented larger-operand-swap/product-anchored alternatives.   # pp.167-168
* The `mixed_precision_cascade_fma` family lacks a choice for optional binaryk FMA/binary2k addition modes.   # pp.167-168

## open_questions
* The document alternates between LZC and LZA for output normalization, so the `lza` slot cannot be resolved to `lza` or `lzc_after_add`.   # pp.167-168
* The document does not identify the circuit family used for the effective carry-propagate addition or the existing fixed-point multiplier.   # p.168
