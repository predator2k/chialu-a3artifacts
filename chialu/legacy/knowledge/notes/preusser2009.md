---
handle: preusser2009
citation: T. B. Preusser, R. G. Spallek, "Mapping Basic Prefix Computations to Fast Carry-Chain Structures", International Conference on Field Programmable Logic and Applications (FPL), 2009.
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU, other]
formats: [binary]
authority: incremental
pages_read: 604-608 / 5
---

## summary
The paper defines a portable transformation that maps non-inverting prefix computations onto FPGA carry chains through ordinary binary addition (p.606-p.607). Token forwarding on a Xilinx Spartan-3 uses about one-third to one-quarter of the LUTs required by general-purpose synthesis, while the addition-based mapping achieves the highest reported frequency at every tested width (p.607-p.608).

## families
### fpga_carry_chain  (role: extends)
mechanism: Each prefix position is classified as kill, propagate or generate. Addends x and y are selected so an ordinary binary addition induces the required carry transition, after which the intended prefix outputs are recovered from the sum bits and local propagate signals because intermediate carry signals are unavailable. The procedure relies on synthesis support for binary addition rather than vendor-specific carry primitives. Two parallel carry-chain rails can implement more complex computations when inter-chain signals flow in only one direction (p.606-p.607).
choices:
  none
new_choices:
  generic_prefix_mapping: binary_addition_transformation — maps a qualifying user-defined prefix computation through the supported binary-addition operator rather than explicit carry primitives # p.606-p.607
  custom_function_implementation: general_purpose_equations | manual_MUXCY | binary_addition_transformation — the three implementation approaches compared for token forwarding # p.607-p.608
slots:
  none
parameters: token-forwarding widths 16, 32, 64 and 128 bits; combinational logic between registered inputs and outputs; latency and II UNKNOWN # p.607-p.608
results:
| metric | value | unit | technology / device | baseline | condition | page |
|---|---:|---|---|---|---|---|
| LUT use | 49 | LUTs | Xilinx Spartan-3 xc3s200-4 / 2009 | comparison reference | 16-bit token forwarding, general-purpose equations | p.608 |
| maximum achieved clock frequency | 170.7 | MHz | Xilinx Spartan-3 xc3s200-4 / 2009 | comparison reference | 16-bit token forwarding, general-purpose equations | p.608 |
| LUT use | 16 | LUTs | Xilinx Spartan-3 xc3s200-4 / 2009 | 49 LUTs, general-purpose equations | 16-bit token forwarding, manual MUXCY | p.608 |
| maximum achieved clock frequency | 143.5 | MHz | Xilinx Spartan-3 xc3s200-4 / 2009 | 170.7 MHz, general-purpose equations | 16-bit token forwarding, manual MUXCY | p.608 |
| LUT use | 17 | LUTs | Xilinx Spartan-3 xc3s200-4 / 2009 | 49 LUTs, general-purpose equations | 16-bit token forwarding, mapping by addition | p.608 |
| maximum achieved clock frequency | 187.2 | MHz | Xilinx Spartan-3 xc3s200-4 / 2009 | 170.7 MHz, general-purpose equations | 16-bit token forwarding, mapping by addition | p.608 |
| LUT use | 125 | LUTs | Xilinx Spartan-3 xc3s200-4 / 2009 | comparison reference | 32-bit token forwarding, general-purpose equations | p.608 |
| maximum achieved clock frequency | 129.8 | MHz | Xilinx Spartan-3 xc3s200-4 / 2009 | comparison reference | 32-bit token forwarding, general-purpose equations | p.608 |
| LUT use | 32 | LUTs | Xilinx Spartan-3 xc3s200-4 / 2009 | 125 LUTs, general-purpose equations | 32-bit token forwarding, manual MUXCY | p.608 |
| maximum achieved clock frequency | 129.8 | MHz | Xilinx Spartan-3 xc3s200-4 / 2009 | 129.8 MHz, general-purpose equations | 32-bit token forwarding, manual MUXCY | p.608 |
| LUT use | 33 | LUTs | Xilinx Spartan-3 xc3s200-4 / 2009 | 125 LUTs, general-purpose equations | 32-bit token forwarding, mapping by addition | p.608 |
| maximum achieved clock frequency | 156.5 | MHz | Xilinx Spartan-3 xc3s200-4 / 2009 | 129.8 MHz, general-purpose equations | 32-bit token forwarding, mapping by addition | p.608 |
| LUT use | 291 | LUTs | Xilinx Spartan-3 xc3s200-4 / 2009 | comparison reference | 64-bit token forwarding, general-purpose equations | p.608 |
| maximum achieved clock frequency | 93.5 | MHz | Xilinx Spartan-3 xc3s200-4 / 2009 | comparison reference | 64-bit token forwarding, general-purpose equations | p.608 |
| LUT use | 64 | LUTs | Xilinx Spartan-3 xc3s200-4 / 2009 | 291 LUTs, general-purpose equations | 64-bit token forwarding, manual MUXCY | p.608 |
| maximum achieved clock frequency | 92.4 | MHz | Xilinx Spartan-3 xc3s200-4 / 2009 | 93.5 MHz, general-purpose equations | 64-bit token forwarding, manual MUXCY | p.608 |
| LUT use | 65 | LUTs | Xilinx Spartan-3 xc3s200-4 / 2009 | 291 LUTs, general-purpose equations | 64-bit token forwarding, mapping by addition | p.608 |
| maximum achieved clock frequency | 106.8 | MHz | Xilinx Spartan-3 xc3s200-4 / 2009 | 93.5 MHz, general-purpose equations | 64-bit token forwarding, mapping by addition | p.608 |
| LUT use | 409 | LUTs | Xilinx Spartan-3 xc3s200-4 / 2009 | comparison reference | 128-bit token forwarding, general-purpose equations | p.608 |
| maximum achieved clock frequency | 88.3 | MHz | Xilinx Spartan-3 xc3s200-4 / 2009 | comparison reference | 128-bit token forwarding, general-purpose equations | p.608 |
| LUT use | 128 | LUTs | Xilinx Spartan-3 xc3s200-4 / 2009 | 409 LUTs, general-purpose equations | 128-bit token forwarding, manual MUXCY | p.608 |
| maximum achieved clock frequency | 89.4 | MHz | Xilinx Spartan-3 xc3s200-4 / 2009 | 88.3 MHz, general-purpose equations | 128-bit token forwarding, manual MUXCY | p.608 |
| LUT use | 129 | LUTs | Xilinx Spartan-3 xc3s200-4 / 2009 | 409 LUTs, general-purpose equations | 128-bit token forwarding, mapping by addition | p.608 |
| maximum achieved clock frequency | 97.0 | MHz | Xilinx Spartan-3 xc3s200-4 / 2009 | 88.3 MHz, general-purpose equations | 128-bit token forwarding, mapping by addition | p.608 |
| LUT-use ratio | about 3-4 | times | Xilinx Spartan-3 xc3s200-4 / 2009 | carry-chain implementations | general-purpose synthesis across tested token-forwarding widths | p.607 |
errors_and_checks: The transformation preserves the qualifying prefix function through Boolean derivation; no approximation, fault model or detection coverage is reported # p.606-p.607
conditions: The method requires kill/propagate/generate behavior without inversion of the incoming carry (p.606). Prefix XOR cannot use the addition transformation on the common MUX-based chains, although the Stratix LUT chain can implement the required inversion (p.606). Multi-rail computations require inter-chain signals to run in one direction so parallel general-purpose logic does not dominate delay (p.607). Frequencies are the highest obtained after several timing-constrained synthesis rounds with registered inputs/outputs on an otherwise empty device (p.608). General-purpose LUT trees may degrade more quickly as device filling increases because of signal load and routing demand (p.608).
evidence: §3, Eq. 1-2 and Fig. 1 (p.605-p.606); §4, Eq. 3, Table 1 and the three-step mapping procedure (p.606-p.607); §5 and Fig. 3 (p.607-p.608)

## new_families
### saturated_prefix_counter  (domain: shift: bit counting, closest: popcount_counter_tree, why_not: the design saturates through parallel prefix OR rails rather than producing an exact count with a counter tree)
mechanism: A 2-saturated bit counter uses parallel 2^0 and 2^1 OR rails mapped to carry chains. Signals between the rails run only in one direction, which keeps the fast chain traversal on the critical path (p.607).
choices: saturation_level: {2}; rail_operator: {parallel_or} # p.607
results: none reported # p.607
evidence: Table 1 and Fig. 2 (p.607)

## space_gaps
* `fpga_carry_chain` lacks a `generic_prefix_mapping` choice covering manual primitives and portable binary-addition transformation for non-arithmetic prefix functions (p.605-p.607).
* The bit-counting vocabulary lacks a family for carry-chain implementations that produce a saturated count through parallel prefix rails rather than an exact population count (p.607).

## open_questions
* The paper does not report the carry-chain segmentation or packing used by the Spartan-3 implementation (p.607-p.608).
* The paper gives a one-direction inter-chain constraint and a 2-saturated example but does not formally characterize the complete class of qualifying multi-rail computations (p.607).
