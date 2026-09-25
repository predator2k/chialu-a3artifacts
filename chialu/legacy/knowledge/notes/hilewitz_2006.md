---
handle: hilewitz_2006
citation: Y. Hilewitz, R. B. Lee, "Fast Bit Compression and Expansion with Parallel Extract and Parallel Deposit Instructions", Proc. IEEE ASAP, 2006
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [int64]
authority: incremental
pages_read: 1-8 / 8
---

## summary
The paper proposes parallel extract (pex) and parallel deposit (pdep) instructions for compressing and distributing mask-selected bits. Static pex/pdep use inverse-butterfly/butterfly networks in one cycle, while variable forms add a hardware mask decoder and require three pipeline stages (pp.2-6). Application kernels achieve 3.41× average speedup over the basic ISA and 2.48× over an ISA with extr/dep (p.8).

## families
none

## new_families
### parallel_extract_deposit  (domain: shift: sub-word SIMD, closest: masked_merged, why_not: pex/pdep compress or expand arbitrary selected bits through butterfly networks rather than rotating and merging a contiguous masked field.)
mechanism: pex selects source bits marked by a mask, preserves their order, compresses them, and right-aligns them through an inverse butterfly network. pdep takes right-aligned bits and distributes them, in order, to mask-selected positions through a butterfly network. Each n-bit network has lg(n) stages of n/2 two-input switches. Static instructions read predecoded controls from application registers. Variable instructions translate the mask with a decoder containing a parallel-prefix population counter and LROTC circuits. The decoder’s rotated/complemented controls absorb the rotations otherwise required between butterfly stages. # pp.2-5
choices:
  operation: {parallel_extract, parallel_deposit, arbitrary_permutation} — The unit can support pex/pdep and optionally bfly/ibfly or grp. # pp.3,5
  mask_timing: {static_predecoded, loop_invariant_predecoded, dynamic_decode} — Controls can be prepared by software, generated once by setb/setib, or decoded for each instruction. # pp.2-3
  network_direction: {butterfly, inverse_butterfly} — pdep uses butterfly stages and pex uses inverse-butterfly stages. # pp.2-4
  decoder_placement: {none, shared_hardware_decoder, software} — Static-only units omit the decoder; variable pex/pdep share one decoder; software can prepare controls. # pp.5,8
  instruction_subset: {grp_variable_static, pex_pdep_variable_static, pex_pdep_static_only} — Figures 6-8 evaluate three functional-unit configurations. # pp.5-6
  control_storage: {application_registers} — Static controls reside in application registers loaded by mov or setb/setib. # p.3
results:
| metric | value | unit | technology / device | baseline | condition | page |
| cycle time | 0.70 | ns | TSMC 90nm standard-cell library; 2006 | reference | ALU | p.6 |
| area | 10.0K | NAND gate equiv. | TSMC 90nm standard-cell library; 2006 | reference | ALU | p.6 |
| cycle time | 0.81 | ns | TSMC 90nm standard-cell library; 2006 | ALU, 0.70 ns | Figure 6 unit supporting grp/pex.v/pdep.v/pex/pdep/ibfly/bfly; relative cycle time 1.16 | p.6 |
| area | 30.5K | NAND gate equiv. | TSMC 90nm standard-cell library; 2006 | ALU, 10.0K | Figure 6 unit; relative area 3.05 | p.6 |
| cycle time | 0.77 | ns | TSMC 90nm standard-cell library; 2006 | ALU, 0.70 ns | Figure 7 unit supporting variable/static pex/pdep and ibfly/bfly; relative cycle time 1.10 | p.6 |
| area | 22.1K | NAND gate equiv. | TSMC 90nm standard-cell library; 2006 | ALU, 10.0K | Figure 7 unit; relative area 2.21 | p.6 |
| cycle time | 0.67 | ns | TSMC 90nm standard-cell library; 2006 | ALU, 0.70 ns | Figure 8 static pex/pdep and ibfly/bfly unit; relative cycle time 0.96 | p.6 |
| area | 7.6K | NAND gate equiv. | TSMC 90nm standard-cell library; 2006 | ALU, 10.0K | Figure 8 static pex/pdep and ibfly/bfly unit; relative area 0.76 | p.6 |
| speedup | 1.85× to 5.21× | × | SimpleScalar Alpha simulation; 2006 | baseline Alpha ISA | Application kernels | p.8 |
| average speedup | 3.41× | × | SimpleScalar Alpha simulation; 2006 | baseline Alpha ISA | Application kernels | p.8 |
| speedup | 1.60× to 4.30× | × | SimpleScalar Alpha simulation; 2006 | Alpha ISA with extr/dep | Application kernels | p.8 |
| average speedup | 2.48× | × | SimpleScalar Alpha simulation; 2006 | Alpha ISA with extr/dep | Application kernels | p.8 |
evidence: Table 1 and §§3-4 define the instructions and networks (pp.2-5); Figures 6-8 and Tables 2-3 define and compare the functional units (pp.5-6); Figure 12 reports application performance (p.8).

## space_gaps
* The vocabulary lacks a butterfly/inverse-butterfly permutation-network family with network direction, supported operation set, static/dynamic control generation and control storage choices (pp.2-6).
* popcount_counter_tree lacks an output-form choice for the decoder’s parallel-prefix population counter, which produces the population count from position 0 through every position 0 to n−2 rather than one total count (p.4).

## open_questions
* The paper reports synthesis for 64-bit decoder controls, but Table 2 does not explicitly restate the width of every synthesized functional unit (pp.4,6).
