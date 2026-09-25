---
handle: bewick1994#s06
parent: bewick1994
citation: G. W. Bewick, "Fast Multiplication: Algorithms and Implementation", PhD dissertation, Stanford University, CSL-TR-94-617, 1994
chapter: Exploring the Design Space
pdf_pages: 110-148
status: ok
kind: thesis_chapter
unit_classes: [BINARY_ALU]
formats: [IEEE-754 double precision, unsigned 53x53 integer]
authority: thesis
pages_read: 39 / 39
---

## summary
The chapter compares complete 53x53 multipliers using simple multiplication, conventional Booth algorithms, partially redundant Booth 3, and arrival-aware Booth 3 implementations in experimental BiCMOS ECL. Booth 2 gives the lowest delay, conventional Booth 3 gives lower area/power, and partially redundant Booth 3 approaches Booth 2 delay with lower area/power. Physical wiring/asymmetric input delays materially affect summation-network performance.   # p.110, p.123-p.148

## families
### booth_recoded_parallel  (role: proposes)
mechanism: Horizontal multiplexer rows select decoded multiplicand multiples, and a fully parallel carry-save network reduces the partial products before a 106-bit carry-propagate addition. Conventional Booth 3 generates hard multiples with a full carry-propagate adder. Partially redundant Booth 3 replaces each long hard-multiple addition with short adders separated by a carry interval. Improved Booth 3 exposes early low-order hard-multiple bits to the summation-network optimizer.   # p.113-p.120, p.131-p.139
choices:
  booth_radix: UNKNOWN   # p.123-p.130
  hard_multiple_gen: cpa_precompute, partially_redundant   # p.119, p.131
  sign_extension: UNKNOWN   # p.110-p.148
  negative_pp_encoding: UNKNOWN   # p.110-p.148
new_choices:
  algorithm_order: {Booth 2, Booth 3, Booth 4} — the chapter's recoding classification   # p.123-p.130
  carry_interval_bits: Int[5..14:1] — spacing between carries in partially redundant hard multiples   # p.131-p.138
  hard_multiple_arrival_profile: {uniform, staged_by_bit_range} — whether hard-multiple bits reach reduction at equal or differing times   # p.138
  implementation_configuration: {Fastest, Minimum Width, Minimum Area, 90% Tree Speed, 75% Tree Speed} — physical speed/area/power operating points   # p.121-p.122
slots:
  reduction: csa_reduction_tree   # p.113-p.120
  hard_multiple_adder: carry_lookahead [arrival_profile=staged_by_bit_range]   # p.138
parameters: 53x53-bit operands; 106-bit product; 14-bit short adders in the fabricated redundant Booth 3 design   # p.110, p.131, p.139
results:
| metric | value | unit | technology / device | baseline | condition | page |
| delay/area/power | 2.6/15.4/14.4 | nsec/mm2/Watts | 0.6µ drawn BiCMOS; bipolar ECL | none | Booth 2; Fastest | p.124 |
| delay/area/power | 3.0/11.0/9.7 | nsec/mm2/Watts | same | none | Booth 3; Fastest | p.124 |
| delay/area/power | 3.1/13.7/10.3 | nsec/mm2/Watts | same | none | Booth 4; Fastest | p.124 |
| delay/area/power | 3.5/9.3/7.2 | nsec/mm2/Watts | same | none | Booth 2; Minimum Width | p.124 |
| delay/area/power | 3.7/8.0/6.1 | nsec/mm2/Watts | same | none | Booth 3; Minimum Width | p.124 |
| delay/area/power | 3.7/10.7/7.3 | nsec/mm2/Watts | same | none | Booth 4; Minimum Width | p.124 |
| delay/area/power | 3.7/9.2/6.4 | nsec/mm2/Watts | same | none | Booth 2; Minimum Area | p.124 |
| delay/area/power | 4.0/7.8/5.3 | nsec/mm2/Watts | same | none | Booth 3; Minimum Area | p.124 |
| delay/area/power | 4.0/10.6/6.9 | nsec/mm2/Watts | same | none | Booth 4; Minimum Area | p.124 |
| delay/area/power | 2.8/14.3/12.9 | nsec/mm2/Watts | same | none | Booth 2; 90% Tree Speed | p.124 |
| delay/area/power | 3.2/10.4/9.0 | nsec/mm2/Watts | same | none | Booth 3; 90% Tree Speed | p.124 |
| delay/area/power | 3.2/12.6/9.8 | nsec/mm2/Watts | same | none | Booth 4; 90% Tree Speed | p.124 |
| delay/area/power | 3.0/12.0/10.9 | nsec/mm2/Watts | same | none | Booth 2; 75% Tree Speed | p.124 |
| delay/area/power | 3.4/9.3/7.8 | nsec/mm2/Watts | same | none | Booth 3; 75% Tree Speed | p.124 |
| delay/area/power | 3.5/11.4/8.6 | nsec/mm2/Watts | same | none | Booth 4; 75% Tree Speed | p.124 |
| hard-multiple delay/power/area | 700/350/0.5 | psec/mW/mm2 | same | none | 53-bit 3M generator | p.119 |
| hard-multiple delay/power/area | 700/500/0.7 | psec/mW/mm2 | same | none | 53-bit 5M or 7M generator | p.119 |
| delay/area/adder power/driver power/total power | 0.2/0.53/0.50/0.76/1.26 | nsec/mm2/Watts/Watts/Watts | same | none | 55-bit multiple generator from 14-bit subsections | p.131 |
| delay variation | 50 | psecs | same | none | length-5 versus length-14 short adder | p.132 |
| power variation | 10 | mW | same | none | length-5 versus length-14 short adder | p.132 |
| delay/area/power | 2.7/16.4/12.1; 2.8/15.8/11.5; 2.7/14.9/11.4; 2.6/14.0/11.7; 2.6/13.7/10.7; 2.7/13.6/10.8; 2.7/12.8/10.5; 2.7/13.1/10.7; 2.6/12.6/10.7; 2.6/13.0/10.5 | nsec/mm2/Watts | same | none | redundant Booth 3; Fastest; carry intervals 5 through 14 respectively | p.133 |
| delay/area/power | 3.4/11.0/7.1; 3.5/10.7/6.9; 3.5/10.5/6.7; 3.5/9.8/6.4; 3.3/9.8/6.9; 3.5/9.5/6.4; 3.7/9.1/6.0; 3.6/9.4/6.2; 3.4/9.1/6.3; 3.6/8.9/5.8 | nsec/mm2/Watts | same | none | redundant Booth 3; Minimum Width; carry intervals 5 through 14 respectively | p.133 |
| delay/area/power | 4.0/10.9/6.1; 3.8/10.5/6.1; 3.9/10.2/5.9; 3.6/9.7/6.3; 3.9/9.6/5.7; 3.7/9.4/6.0; 3.8/9.1/5.9; 3.7/9.3/5.9; 3.6/8.9/5.9; 3.7/8.9/5.6 | nsec/mm2/Watts | same | none | redundant Booth 3; Minimum Area; carry intervals 5 through 14 respectively | p.133 |
| delay/area/power | 2.8/14.9/11.0; 2.9/14.2/10.6; 2.8/13.7/10.6; 2.7/13.2/10.6; 2.8/12.6/9.9; 2.8/12.6/9.7; 2.9/12.0/9.5; 2.8/12.0/9.4; 2.7/11.7/9.5; 2.8/12.2/9.7 | nsec/mm2/Watts | same | none | redundant Booth 3; 90% Tree Speed; carry intervals 5 through 14 respectively | p.134 |
| delay/area/power | 3.1/12.0/8.6; 3.2/11.8/8.3; 3.1/12.0/8.8; 3.0/12.0/9.3; 3.1/10.6/8.2; 3.1/10.8/8.3; 3.1/10.8/8.2; 3.1/10.6/8.1; 3.0/10.6/8.4; 3.1/10.3/8.0 | nsec/mm2/Watts | same | none | redundant Booth 3; 75% Tree Speed; carry intervals 5 through 14 respectively | p.134 |
| partial-product arrival | 0-14: 200; 15-36: 400; 37-54: 700 | psec | same | uniform arrival | improved Booth 3 | p.138 |
| power decrease | ~25 | % | same | Booth 2 | fastest redundant Booth 3 | p.148 |
| area decrease | ~15 | % | same | Booth 2 | fastest redundant Booth 3 | p.148 |
| design goal delay/power | 3.5 typical, 4.4 worst/4.5 | nsec/Watts | same | none | fabricated redundant Booth 3 | p.143 |
| post-bug estimate delay/power | 5/about 3.5 | nsec/Watts | same | design goal | all summation-network output drivers incorrectly power-ramped | p.143 |
| layout size | 4 by 2.5 | mm | same | none | multiplier excluding test/I/O circuitry | p.143 |
errors_and_checks: The full 106-bit product is required for IEEE accuracy. The fabricated design computes the high 66 bits and encodes whether the low 40 bits are exactly zero into one sticky indication. About 3000 vectors passed transistor/resistor-level simulation, but no completely working fabricated multiplier was obtained.   # p.110, p.139, p.143
conditions: Booth 4 is not competitive for lengths at most 64 because hard-multiple adders and larger multiplexers offset the reduced partial-product count. Carry intervals from 10 through 14 are about equally acceptable. The comparisons are technology-sensitive because ECL static power/circuit libraries differ from CMOS and gate arrays.   # p.123-p.130, p.138
evidence: Sections 5.2-5.6; Tables 5.3-5.8; Figures 5.6-5.21

### carry_save_array  (role: analyzes)
mechanism: Simple multiplication and Booth multiplication use fully parallel carry-save summation networks. The layout generator selects and places CSAs/multiplexers while accounting for wire lengths, asymmetric CSA input delays, and nonuniform partial-product arrival times.   # p.113-p.120, p.138, p.147
choices:
  signed_scheme: unsigned   # p.123
  rows_per_pipeline_stage: UNKNOWN   # p.121
new_choices:
  physical_delay_model: {gate_only, extracted_wire_and_asymmetric_input} — whether placement uses physical wire/input timing   # p.147
slots:
  cpa: ling_prefix   # p.120
parameters: 53 partial-product width; fully parallel summation; measured special network has 9 CSA levels   # p.121, p.147
results:
| metric | value | unit | technology / device | baseline | condition | page |
| delay/area/power | 3.1/33.0/26.9 | nsec/mm2/Watts | 0.6µ drawn BiCMOS; bipolar ECL | none | Simple; Fastest | p.124 |
| delay/area/power | 4.2/18.2/15.0 | nsec/mm2/Watts | same | none | Simple; Minimum Width | p.124 |
| delay/area/power | 4.7/17.1/11.1 | nsec/mm2/Watts | same | none | Simple; Minimum Area | p.124 |
| delay/area/power | 3.3/29.4/24.5 | nsec/mm2/Watts | same | none | Simple; 90% Tree Speed | p.124 |
| delay/area/power | 3.7/24.5/20.4 | nsec/mm2/Watts | same | none | Simple; 75% Tree Speed | p.124 |
| estimation accuracy | within 10 | % of SPICE | same | SPICE | generated summation-network delay/power/area | p.120 |
| critical-path delay | 2.0 | nsec | same | 8-level Wallace wiring | 9 CSA levels; power ramping/differential wiring disabled | p.147 |
| wire delay | 1.25 | nsecs | same | none | critical path | p.147 |
| intrinsic CSA delay | 750 | psec | same | none | critical path | p.147 |
| per-wire delay range | 7 to 331 | psec | same | none | critical path | p.147 |
| wire-delay standard deviation | 119 | psec | same | none | critical path | p.147 |
| path delay | 1.4 | nsec | same | 9-level critical path | 11 CSA levels | p.147 |
| path delay | 1.85 | nsec | same | 11-level path | 8 CSA levels | p.147 |
errors_and_checks: none
conditions: Simple multiplication is inferior in this ECL implementation, but conclusions about power/area do not transfer directly to CMOS or gate-array libraries. Level count alone does not predict delay because wire lengths and asymmetric CSA inputs can reverse path ordering.   # p.123-p.130, p.147
evidence: Sections 5.2, 5.3.1, and 5.8; Tables 5.3; Figures 5.4-5.16

### ling_prefix  (role: instantiates)
mechanism: A laid-out modified Ling carry-propagate adder accepts two 106-bit operands and returns the high 66 product bits plus an indication that the low 40 bits are exactly zero. The same final adder is treated as fixed overhead for every multiplier algorithm.   # p.120
choices:
  pseudo_carry_group: UNKNOWN   # p.120
  topology: UNKNOWN   # p.120
  sum_recovery: UNKNOWN   # p.120
  order: UNKNOWN   # p.120
new_choices:
  low_product_zero_detection: true — the adder reports whether its low 40 result bits are exactly zero   # p.120
slots:
  none
parameters: 106-bit inputs; high 66 output bits; low 40-bit zero indication; nominal -5V supply; 100°C; no output load   # p.120
results:
| metric | value | unit | technology / device | baseline | condition | page |
| area | 1.125 | mm2 | experimental BiCMOS; bipolar ECL | none | 106-bit modified Ling adder | p.121 |
| delay | 860 | nsec | same | none | table value as extracted; critical-path SPICE with extracted capacitances | p.121 |
| power | 1.13 | Watts | same | none | 106-bit modified Ling adder | p.121 |
errors_and_checks: The low 40 bits are reduced to an exact-zero indication rather than emitted individually.   # p.120
conditions: The adder is common fixed overhead, and its delay increasingly dominates after the carry-save network is accelerated. Simulation increases wire capacitance by 50% for possible Miller capacitance between adjacent switching wires.   # p.120-p.121, p.132
evidence: Section 5.2; Table 5.2

## taxonomy
Multiplier algorithms   # p.123-p.139
  Conventional algorithms
    Simple multiplication -> carry_save_array   # p.123-p.130
    Booth 2 -> booth_recoded_parallel   # p.123-p.130
    Booth 3 -> booth_recoded_parallel   # p.123-p.130
    Booth 4 -> booth_recoded_parallel   # p.123-p.130
  Partially redundant algorithms
    Redundant Booth 3 with carry interval 5-14 -> booth_recoded_parallel   # p.131-p.138
  Arrival-aware algorithms
    Improved Booth 3 with staged hard-multiple arrivals -> booth_recoded_parallel   # p.138-p.139
Implementation configurations   # p.121-p.122
  Fastest -> unmapped   # p.122
  Minimum Area -> unmapped   # p.122
  Minimum Width -> unmapped   # p.122
  90% Summation Network Speed -> unmapped   # p.122
  75% Summation Network Speed -> unmapped   # p.122

## primary_sources
* Santoro, UNKNOWN — CMOS multiplier implementation reaching a different conclusion about simple versus Booth multiplication   # p.123, p.128
* Jouppi et al., UNKNOWN — CMOS multiplier implementation reaching a different conclusion about simple versus Booth multiplication   # p.123
* Adiletta et al., UNKNOWN — ECL gate-array multiplier implementation and literature comparison point   # p.123, p.128, p.143-p.146
* Mori et al., UNKNOWN — 54x54 custom CMOS full-tree multiplier comparison point   # p.143-p.146
* Goto et al., UNKNOWN — 54x54 custom CMOS full-tree multiplier comparison point   # p.143-p.146
* Elkind et al., UNKNOWN — 56x56 custom ECL iterative multiplier comparison point   # p.143-p.146

## new_families
none

## space_gaps
* `csa_reduction_tree` is used as a multiplier reduction-slot value but lacks a declared family with choices for wire-aware placement/asymmetric input timing/nonuniform bit arrival.   # p.113-p.120, p.138, p.147
* `booth_recoded_parallel` lacks the chapter's Booth 2/Booth 3/Booth 4 naming and an explicit carry-interval choice for partially redundant hard multiples.   # p.123-p.138
* `booth_recoded_parallel` lacks a hard-multiple per-bit arrival-profile choice used by improved Booth 3.   # p.138-p.139
* Physical implementation configuration and differential/single-ended wiring are major design choices absent from the family vocabulary.   # p.121-p.122

## open_questions
* Table 5.2 prints/extracts the 106-bit adder delay as `860` under `Delay (nsec)`, which conflicts with the complete multiplier delays and may represent a missing decimal point or a psec value.   # p.121
* The current chapter names Booth 2/3/4 but does not state their radix mapping, so `booth_radix` remains `UNKNOWN`.   # p.123-p.130
* The chapter does not identify years for the cited implementation papers.   # p.123, p.143-p.146
