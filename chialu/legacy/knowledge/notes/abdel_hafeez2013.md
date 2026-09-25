---
handle: abdel_hafeez2013
citation: S. Abdel-Hafeez, A. Gordon-Ross, B. Parhami, "Scalable Digital CMOS Comparator Using a Parallel Prefix Tree", IEEE Transactions on VLSI Systems, vol. 21, no. 11, pp. 1989-1998, 2013.
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [binary16, binary32, binary64, binary128, binary256, binary512]
authority: incremental
pages_read: 1989-1998 / 10
---

## summary
The paper proposes a scalable full-ordering binary comparator that resolves comparisons from MSB to LSB through a parallel-prefix tree and suppresses lower-significance activity after the first unequal bit. A 64-b static-CMOS implementation reports 0.86 ns delay and 7.76 mW at 1 GHz in 0.15 μm TSMC technology. (p.1996)

## families
### prefix_comparator  (role: proposes)
mechanism: The comparison resolution module generates per-bit unequal flags, combines them in four-bit prefix partitions, and enables only the most-significant unequal position. Two N-bit buses encode A>B and A<B, while separate OR trees produce the final A>B/A=B/A<B decision. Five hierarchical sets use XOR/NOR/control/multiplexer cells, with lower-significance outputs forced to zero after a decisive unequal bit. (pp.1990-1994)
choices:
  function: full_ordering   # pp.1991-1993
  structure: msb_first_prefix   # pp.1990-1994
  radix: 4   # pp.1992-1994
new_choices:
  activity_policy: terminate_lower_significance_comparisons — Lower-significance bus positions are forced to zero after the most-significant unequal bit.   # p.1991
  result_encoding: dual_N_bit_buses_plus_OR_scans — Separate left/right buses encode greater-than/less-than, and LR=00 encodes equality.   # p.1991
slots: none
parameters: N-bit binary operands; evaluated widths 16, 32, 64, 128, and 256 b; simulated operating-speed range extends to 512 b; five comparison-resolution sets; four-bit partitions; maximum fan-in 5; maximum fan-out 4; combinational operation with optional partitioning into two or more pipeline stages.   # pp.1990-1997
results:
| metric | value | unit | technology / device | baseline | condition | page |
| comparator delay | 0.86 | ns | 0.15 μm TSMC CMOS, 1.5 V / 2013 | none | 64-b, worst-case input-to-output delay | p.1996 |
| power dissipation | 7.76 | mW@1 GHz | 0.15 μm TSMC CMOS, 1.5 V / 2013 | none | 64-b | p.1996 |
| transistor count | 4000 | transistors | 0.15 μm TSMC CMOS, 1.5 V / 2013 | none | complete 64-b comparator | p.1996 |
| operating speed | 1.2 | GHz | 0.15 μm CMOS / 2013 | none | 64-b, worst-case operands | p.1997 |
| operating speed | 1 | GHz | 0.15 μm CMOS / 2013 | none | 512-b, worst-case operands | p.1997 |
| speed advantage | 40% | faster | CMOS gate-level comparison / 2013 | Perri and Corsonello [28] | independent of technology scaling | p.1995 |
| average power rate | 0.9 | μW/MHz | 0.15 μm TSMC CMOS / 2013 | none | fewer than 28 bits evaluated; random-input probability stated as very close to 1 | pp.1996-1997 |
| power rate | 4.12 | μW/MHz | 0.15 μm TSMC CMOS / 2013 | none | more than 32 bits evaluated | pp.1996-1997 |
| transistor activity | less than 35% | active transistors | standard CMOS / 2013 | all transistors active | arbitrary comparator bitwidth during operation | p.1997 |
| analytical delay | 4+⌈log16 N⌉+⌈log4 N⌉ | CMOS gate delays | analytical CMOS gate model / 2013 | none | asynchronous N-bit comparator | p.1994 |
| transistor count | 768 | transistors | analytical static CMOS / 2013 | none | 16-b comparison-resolution structure | p.1994 |
| transistor count | 1424 | transistors | analytical static CMOS / 2013 | none | 32-b comparison-resolution structure | p.1994 |
| transistor count | 2976 | transistors | analytical static CMOS / 2013 | none | 64-b comparison-resolution structure | p.1994 |
| transistor count | 5952 | transistors | analytical static CMOS / 2013 | none | 128-b comparison-resolution structure | p.1994 |
| transistor count | 11 840 | transistors | analytical static CMOS / 2013 | none | 256-b comparison-resolution structure | p.1994 |
errors_and_checks: LR=11 is structurally excluded; the document reports no fault model, detection coverage, false-alarm behavior, or alias rate.   # p.1991
conditions: The design reduces dynamic activity because lower-significance comparisons stop after the first unequal bit, but set 1 always activates and the larger transistor count increases leakage relative to alternate comparators. (pp.1994-1996) The design targets wide combinational comparisons using conventional locally interconnected CMOS cells; optional pipelining increases throughput at the cost of power and latency. (pp.1990, 1997) The reported worst-case simulation uses operands equal through the least-significant comparison position, a slow-slow corner at 1.35 V/125 °C, minimum 0.15 μm channel length, N-type width limited to 2 μm, and P-type width limited to 5 μm. (p.1995)
evidence: Fig. 1 and Section II, pp.1990-1991; Fig. 3, Tables I-III, and Section III, pp.1991-1993; equations (10)-(16) and Tables IV-V, pp.1993-1994; Section V, Table VIII, and Figs. 5-6, pp.1995-1996; Section VI, pp.1996-1997.

## new_families
none

## space_gaps
* `prefix_comparator` lacks an activity-policy choice for terminating or suppressing lower-significance comparisons after the most-significant unequal bit. (p.1991)
* `prefix_comparator` lacks a result-encoding choice for the paper’s dual left/right buses and final OR-scan decision network. (pp.1991-1993)

## open_questions
* The paper describes four-bit grouping and a separate log16 hierarchy, so the vocabulary’s single `radix` choice does not fully express the mixed grouping structure. (pp.1992-1994)
* Table V reports 2976 transistors for the 64-b set structure, while Table VIII reports 4000 transistors for the complete proposed 64-b comparator; the merge pass must preserve the differing scopes. (pp.1994, 1996)
