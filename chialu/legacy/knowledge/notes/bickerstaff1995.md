---
handle: bickerstaff1995
citation: K. C. Bickerstaff, M. J. Schulte, E. E. Swartzlander, "Parallel Reduced Area Multipliers", Journal of VLSI Signal Processing, vol. 9, no. 3, pp. 181-191, 1995
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [unsigned_binary, twos_complement]
authority: incremental
pages_read: 181-191 / 11
---

## summary
The document proposes a Reduced Area partial-product reduction scheme that uses the maximum number of (3,2) counters early and places (2,2) counters to shorten the final carry-propagate adder. The scheme reduces components/interconnect and especially reduces pipeline-latch area relative to Wallace and Dadda multipliers. The scheme supports unsigned sign-magnitude and two's-complement multiplication.

## families
none

## new_families
### reduced_area_counter_tree  (domain: mul, closest: carry_save_array, why_not: carry_save_array specifies a regular 2-D array, while this mechanism is a staged parallel-counter reduction tree with a distinct counter-placement policy)
mechanism: An N-word by M-bit partial-product matrix is reduced to two rows through S stages of parallel (3,2)/(2,2) counters. Each stage places floor(b_i/3) (3,2) counters in column i, which maximizes early reduction. A (2,2) counter is placed only to satisfy the Dadda height sequence or in the rightmost column containing exactly two bits. The latter placement shortens the final carry-propagate adder by S bits. A carry-propagate adder sums the remaining rows. Two's-complement operation complements sign-related partial products and uses specialized (2,2) counters that add one. # pp.182-183, 187, 189-190
choices:
  reduction_schedule: {maximum_3_2_early} — the maximum number of (3,2) counters is used in every stage # pp.182-183
  half_adder_placement: {dadda_height_limit, rightmost_two_bit_column} — (2,2) counters enforce stage-height limits or shorten the final adder # p.183
  signed_scheme: {unsigned_sign_magnitude, twos_complement_specialized_2_2} — two's-complement sign terms use NAND partial products and specialized counters # pp.189-190
  pipeline_placement: {none, every_reduction_stage} — evaluated implementations are non-pipelined or fully pipelined # pp.188-189
parameters: For 8 by 8, 12 by 12, and 16 by 16 RA multipliers, the respective hardware is 39/104/201 (3,2) counters, 7/11/15 (2,2) counters, and 10/17/24-bit final adders; the respective interconnect estimates G/P are 204/48, 473/99, and 861/173. # pp.183, 188
results:
| metric | value | unit | technology / device | baseline | condition | page |
| area reduction | 3.7 to 6.6 | percent | LSI Logic standard-cell area model; 1995 | Dadda | non-pipelined, operand sizes 8 through 64 bits | p.188 |
| area reduction | 3.8 to 8.4 | percent | LSI Logic standard-cell area model; 1995 | Wallace | non-pipelined, operand sizes 8 through 64 bits | p.188 |
| area reduction | 15.1 to 33.6 | percent | LSI Logic standard-cell area model; 1995 | Dadda | fully pipelined, operand sizes 8 through 64 bits | pp.188-189 |
| area reduction | 2.9 to 9.0 | percent | LSI Logic standard-cell area model; 1995 | Wallace | fully pipelined, operand sizes 8 through 64 bits | pp.188-189 |
| layout area | 0.1778 | mm² | 0.7 micron dual-well BiNMOS; 1995 | none | non-pipelined 8 by 8 RA multiplier | p.189 |
| layout area | 0.1821 | mm² | 0.7 micron dual-well BiNMOS; 1995 | RA 0.1778 mm² | non-pipelined 8 by 8 Dadda multiplier; 2.4% increase | p.189 |
| layout area | 0.1943 | mm² | 0.7 micron dual-well BiNMOS; 1995 | RA 0.1778 mm² | non-pipelined 8 by 8 Wallace multiplier; 9.3% increase | p.189 |
| layout area | 0.4238 | mm² | 0.7 micron dual-well BiNMOS; 1995 | none | non-pipelined 12 by 12 RA multiplier | p.189 |
| layout area | 0.4624 | mm² | 0.7 micron dual-well BiNMOS; 1995 | RA 0.4238 mm² | non-pipelined 12 by 12 Dadda multiplier; 9.1% increase | p.189 |
| layout area | 0.4830 | mm² | 0.7 micron dual-well BiNMOS; 1995 | RA 0.4238 mm² | non-pipelined 12 by 12 Wallace multiplier; 14.0% increase | p.189 |
| layout area | 0.7354 | mm² | 0.7 micron dual-well BiNMOS; 1995 | none | non-pipelined 16 by 16 RA multiplier | p.189 |
| layout area | 0.7957 | mm² | 0.7 micron dual-well BiNMOS; 1995 | RA 0.7354 mm² | non-pipelined 16 by 16 Dadda multiplier; 8.2% increase | p.189 |
| layout area | 0.8246 | mm² | 0.7 micron dual-well BiNMOS; 1995 | RA 0.7354 mm² | non-pipelined 16 by 16 Wallace multiplier; 12.1% increase | p.189 |
errors_and_checks: none
conditions: The RA scheme uses S more (3,2) counters than Dadda but shortens the carry-propagate adder by S bits; its hardware advantage assumes one carry-propagate-adder bit costs more than one (3,2) counter. Early bit reduction lowers interconnect and pipeline-latch counts. A smaller final adder may provide a modest speed advantage, depending on adder size/implementation. # pp.187-188
evidence: Sections 2-5; Figs. 1, 4, and 5; Tables 1-7; pp.182-190

## space_gaps
* `csa_reduction_tree` appears as a component-slot value elsewhere in the vocabulary but lacks a declared family whose choices can distinguish Wallace/Dadda/Reduced Area counter-placement schedules. # pp.182-188
* A multiplier reduction-tree family needs a final carry-propagate-adder slot; the estimates use a CLA with 4-bit first-level modules/blocks, while layouts use variable-size carry-lookahead modules. # pp.188-189

## open_questions
* The exact variable-size carry-lookahead module organization used in the physical layouts is not reported. # p.189
