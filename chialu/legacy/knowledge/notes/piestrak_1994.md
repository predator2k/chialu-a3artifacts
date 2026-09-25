---
handle: piestrak_1994
citation: S. J. Piestrak, "Design of Residue Generators and Multioperand Modular Adders Using Carry-Save Adders", IEEE Transactions on Computers, vol. 43, no. 1, pp. 68-77, 1994
actual_citation: Stanislaw J. Piestrak, "Design of Residue Generators and Multi-Operand Modular Adders Using Carry-Save Adders", venue UNKNOWN, 1991
status: ok
kind: paper
unit_classes: [BINARY_ALU, other]
formats: [binary, residue_mod_A]
authority: incremental
pages_read: 8 / 8 (pp.100-107)
---

## summary
The document proposes carry-save residue generators and multioperand modular adders whose end-around-carry cycle follows the period P(A) of powers of 2 modulo A (pp.101-102). The proposed circuits reduce weighted bits with full adders before a ROM/PLA final converter and target RNS arithmetic and arithmetic error-detecting codes (pp.100, 102-106).

## families
### residue  (role: extends)
mechanism: An n-bit input is partitioned into P(A) sets G_j according to equal weights [2^j]_A. A carry-save network with end-around carry reduces the sets, and a cyclic binary adder leaves P(A)+1 or fewer bits for a final residue converter. The end-around carry is valid because [2^(tP(A))]_(2^P(A)-1)=1, so a carry leaving the highest periodic position returns to weight 1 (pp.101-103).
choices:
  modulus: arbitrary odd A [outside domain]   # pp.101-102
  generator_style: csa_tree   # pp.102-103
new_choices:
  eac_cycle_length: P(A) — the period of powers of 2 modulo A determines the cyclic carry span   # pp.101-102
  final_converter: ROM | PLA | specialized generator — the remaining weighted bits are converted to [X]_A after carry-save reduction   # pp.103-104
  cyclic_adder_partitioning: one P(A)-bit adder | multiple shorter adders — partitioning reduces delay for large P(A) but adds final-converter inputs   # p.102
slots:
  comparator: none
parameters: n input bits; a output bits; period P(A); n=uP(A)+v; CSA reduction target n'=2P(A) or 2P(A)+1; final target n''=P(A)+1   # pp.100, 102-103
results:
| metric | value | unit | technology / device | baseline | condition | page |
| generator hardware | 25 FAs + one HA | cells | UNKNOWN; 1991 | none stated | 32-bit generator mod 9 | p.103 |
| generator delay | 9Δ | delay | UNKNOWN; 1991 | none stated | 32-bit generator mod 9 | p.103 |
| final converter | 128 x 4 | ROM | UNKNOWN; 1991 | none stated | 32-bit generator mod 9 | p.103 |
| hardware | n-a | FAs | UNKNOWN; 1991 | conventional tree also uses n-a FAs | modulus A=2^a-1 | p.105 |
| proposed delay | [B(⌈n/a⌉)+2a]Δ | delay | UNKNOWN; 1991 | 2a⌈log(n/a)⌉Δ conventional tree | modulus A=2^a-1 | p.105 |
errors_and_checks: The generator computes the exact residue [X]_A. The document identifies encoding/decoding for arithmetic error-detecting codes as an application but reports no fault model, detection coverage, false-alarm rate, or alias rate (pp.100, 107).
conditions: Procedure 1 becomes more efficient as n/P(A) grows and cannot exploit much carry-save reduction when n/P(A)<3 (p.103). Large P(A) can make the cyclic-adder delay prohibitive, so the cycle may be partitioned among shorter binary adders (p.102). ROM-only implementation is suggested for n<10, while the split ROM/correction scheme is described as probably applicable for 10<n≤10+a (p.103).
evidence: Definition and identity in §2; EAC construction in §3; Procedure 1/Figs. 2-4 in §4.1; special generators in §§4.2-4.3; comparison in §§4.5 and 6 (pp.101-105, 107).

## new_families
### periodic_eac_multioperand_modular_adder  (domain: redundant: residue number systems, closest: rns_channel_arithmetic, why_not: rns_channel_arithmetic does not describe multioperand periodic carry-save reduction or its ROM/PLA final conversion)
mechanism: The k residue operands are partitioned into equal binary-weight columns G_j. Full-adder carry-save stages reduce ka bits while carries wrap after q=min(P(A),m) positions, where m encodes the largest unreduced operand sum. A cyclic adder reduces the remaining bits, and a ROM/PLA evaluates the final weighted residue. A high-speed version uses a combinational CSA tree, while a cost-effective version reuses one CSA stage with a carry-save register (pp.105-106).
choices: modulus: odd integer A; reduction_implementation: {high_speed_csa_tree, cost_effective_csa_register}; cyclic_mode: {enabled, disabled}; final_converter: {rom, pla}; cycle_span: Int[1..P(A)]
results:
| metric | value | unit | technology / device | baseline | condition | page |
| hardware | 7 FAs + one HA | cells | UNKNOWN; 1991 | none stated | 4-operand adder mod 5 | p.105 |
| delay | 5Δ | delay | UNKNOWN; 1991 | none stated | 4-operand adder mod 5 | p.105 |
| final converter | 5-input | PLA | UNKNOWN; 1991 | none stated | 4-operand adder mod 5 | p.105 |
| cost-effective hardware reduction | 3 | FAs fewer | UNKNOWN; 1991 | combinational version | 4-operand adder mod 5; adds an 8-bit CSR | p.105 |
| high-speed hardware | 32 FAs + two HAs | cells | UNKNOWN; 1991 | none stated | 8-operand adder mod 25 | p.106 |
| high-speed final converter | 256 x 5 | ROM | UNKNOWN; 1991 | none stated | 8-operand adder mod 25 | p.106 |
| high-speed delay | 7Δ+d(ROM) | delay | UNKNOWN; 1991 | none stated | 8-operand adder mod 25 | p.106 |
| cost-effective hardware | 7 FAs + 14-bit CSR | cells | UNKNOWN; 1991 | high-speed version | 8-operand adder mod 25 | p.106 |
| cost-effective delay | 11Δ+d(ROM) | delay | UNKNOWN; 1991 | 7Δ+d(ROM) high-speed version | 8-operand adder mod 25 | p.106 |
evidence: Procedure 2/Figs. 7-8 and Examples 5-6 in §§5.1-5.2; complexity/comparison in §§5.3-5.4 (pp.105-106).

## space_gaps
* The residue modulus domain excludes arbitrary odd A, although the document constructs period-based CSA residue generators for arbitrary odd A (pp.101-103).
* The residue family lacks P(A), cyclic end-around-carry span, cyclic-adder partitioning, and final-converter implementation choices (pp.101-104).
* The vocabulary lacks a family for exact multioperand modular addition using a periodic EAC carry-save network and ROM/PLA final conversion (pp.105-106).
* The proposed cost-effective variants require a carry-save-register implementation choice rather than only a combinational csa_tree value (pp.104-106).

## open_questions
* The document does not identify its venue, and its 1991 copyright/header conflicts with the supplied 1994 IEEE Transactions citation.
* Example 6 prints delays of 7Δ+d(ROM) and 11Δ+d(ROM), but the accompanying prose says the cost-effective version is slower by 2Δ (p.106).
* The extracted text omits or corrupts parts of §§4.3-4.4 and Table V, so their exact formulas and converter bounds must not be reconstructed from OCR fragments.
