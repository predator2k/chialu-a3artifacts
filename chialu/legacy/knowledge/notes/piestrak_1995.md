---
handle: piestrak_1995
citation: Piestrak, "A High-Speed Realization of a Residue to Binary Number System Converter", IEEE Transactions on Circuits and Systems II, 1995
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: ["RNS {2^n-1, 2^n, 2^n+1}", "binary 3n-bit"]
authority: incremental
pages_read: 3 / 3
---

## summary
The paper proposes a ROM-less CRT-based residue-to-binary converter for the three-moduli RNS {2^n-1, 2^n, 2^n+1}. The converter reduces the critical carry-propagate work to one 2n-bit 1's-complement addition after two carry-save stages with end-around carry. The paper reports an analytic lower-bound delay of 18 two-input-NAND-gate delay units for its high-speed implementation.

## families
### rns_reverse_converter  (role: proposes)
mechanism: The converter forms the 2n-bit quantities A, B, C, and -X1 by parallel bit manipulation, then computes X* = |A+B+C-X1|_(2^(2n)-1). A four-operand modulo adder implements this sum with two stages of 2n-bit carry-save adders with end-around carry and one 2n-bit 1's-complement adder. The final 3n-bit binary result concatenates X* as the 2n most-significant bits with residue X2 as the n least-significant bits. A NAND gate in the end-around-carry path forces the positive-zero representation. # pp.661-662
choices:
  algorithm: crt   # p.661
  moduli_count: 3   # p.661
  implementation: adder_based   # pp.661-662
new_choices:
  moduli_set: {2^n-1, 2^n, 2^n+1} — identifies the three RNS moduli accepted by the converter   # p.661
  modular_accumulation: four_operand_moma — selects the (4, 2^(2n)-1) multioperand modular adder   # pp.661-662
  ones_complement_adder_variant: {CE_EAC_CPA, HS_dual_CPA_mux} — selects a cost-effective CPA with end-around carry or two parallel CPAs followed by a 2-to-1 multiplexer   # p.662
  zero_representation_control: NAND_in_EAC_path — prevents oscillation and emits only positive zero   # p.662
slots:
  none
parameters: three residue inputs; moduli {2^n-1, 2^n, 2^n+1}; 3n-bit binary range; 2n-bit modular operands; two CSA stages; one 2n-bit 1's-complement addition   # pp.661-662
results:
| metric | value | unit | technology / device | baseline | condition | page |
| delay | 2t_FA + t_1C(2n) | time | UNKNOWN; 1995 | existing converters requiring several CPA stages | converter in Fig. 2 | p.662 |
| high-speed delay lower bound | 18 | two-input NAND-gate delay units | UNKNOWN; 1995 | converters in Table I | t_FA = t_MUX = 2 units and t_CPA(2n) = 12 units | p.662 |
| basic modular-adder hardware | 6n | full adders | UNKNOWN; 1995 | none | unsimplified (4, 2^(2n)-1) MOMA | p.662 |
| simplified CSA1 hardware | 2n-1 | two-input XNOR/OR gate pairs | UNKNOWN; 1995 | 2n-1 full adders | constant-one inputs simplify all but one CSA1 full adder | p.662 |
| critical carry-propagate operand width | 2n | bits | UNKNOWN; 1995 | 3n-bit full RNS range | one 1's-complement addition | p.662 |
errors_and_checks: The NAND gate in the CPA end-around-carry path suppresses the negative-zero representation and produces only positive zero; no fault-detection or numerical-error metric is reported.   # p.662
conditions: The converter applies to the three-moduli system {2^n-1, 2^n, 2^n+1}.   # p.661
conditions: The CE version uses the least hardware, but its timing depends on end-around-carry stabilization; the paper treats t_1C(2n) = 2t_CPA(2n) as the more realistic estimate.   # p.662
conditions: The HS version uses two parallel 2n-bit CPAs and a 2-to-1 multiplexer at extra hardware cost.   # p.662
conditions: The 18-unit lower bound assumes a carry-lookahead adder and 2n < 64.   # p.662
evidence: Abstract and §I, p.661; §II and Figs. 1-2, pp.661-662; §III and Table I discussion, p.662; §IV, p.662.

## new_families
none

## space_gaps
* rns_reverse_converter lacks a moduli-set choice for the explicitly supported {2^n-1, 2^n, 2^n+1} system.   # p.661
* rns_reverse_converter lacks a modular-accumulation choice that distinguishes the two-stage CSA-with-EAC plus final 1's-complement-adder structure from generic adder-based conversion.   # pp.661-662
* rns_reverse_converter lacks a choice for the CE feedback-EAC implementation versus the HS dual-CPA-and-multiplexer implementation.   # p.662

## open_questions
* The body rows of Table I are not legible in the supplied document text, so its converter-by-converter hardware and delay values remain UNKNOWN.
* The final CPA topology remains open because carry lookahead appears only in the assumptions used to derive the 18-unit lower bound.
