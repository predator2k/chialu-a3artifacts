---
handle: knowles2001
citation: S. Knowles, "A Family of Adders", 15th IEEE Symposium on Computer Arithmetic (ARITH-15), 2001 (first presented ARITH-14, 1999).
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [int32]
authority: landmark
pages_read: 10 / 10
---

## summary
The paper defines a family of minimum-depth parallel-prefix adders between the Ladner-Fischer and Kogge-Stone extrema. Per-level lateral fanout trades wiring/area against delay, and six 32b structures are laid out in an industrial 0µ25 CMOS process.

## families
### parallel_prefix  (role: proposes)
mechanism: Each bit first produces carry-generate/carry-propagate/carry-kill terms. Binary associative and idempotent prefix operations then compute every carry in log2n stages, followed by the sum stage. A graph is identified by its lateral fanouts from the level nearest the output toward the input. Intermediate graphs retain minimum logical depth while adding overlapping prefix subterms to reduce fanout at the cost of more lateral wiring. # §2, §4
choices:
  topology: knowles_mixed   # §4
  valency: 2   # §2
  fanout_cap: {1 [outside domain], 2, 4, 16 [outside domain]}   # §4, §5
  node_style: and_or   # §2
new_choices:
  level_fanout_vector: [16,8,4,2,1] / [16,4,2,2,1] / [16,2,2,2,1] / [4,4,2,2,1] / [2,2,2,1,1] / [1,1,1,1,1] — records lateral fanout independently at each prefix level. # §4, §5
  buffering_vector: [2,1,1,0,0] / [1,1,0,0,0] / [1,1,1,0,0] — records buffering inverters inserted at each level. # §5
  level_uniformity: uniform / irregular_hybrid — selects equal fanout for all fanning nodes within a level or path-dependent fanout. # §6
slots:
  none
parameters: n-bit operands with n a power of 2; demonstrated graphs at 4b/8b/16b and layouts at 32b; minimum-depth computation has 1+log2n unate logical stages plus 1 non-unate stage; CMOS mapping has 3+log2n inverting gate stages before optional buffering. # §2, §4, §5
results:
| metric | value | unit | technology / device | baseline | condition | page |
| delay | 13.7 | ref invs | 0µ25 6-metal CMOS / year UNKNOWN | none | [16,8,4,2,1], buffering [2,1,1,0,0] | §5 |
| length | 38 | µm | 0µ25 6-metal CMOS / year UNKNOWN | none | [16,8,4,2,1], buffering [2,1,1,0,0] | §5 |
| transverse wire flux, total | 9 | UNKNOWN | 0µ25 6-metal CMOS / year UNKNOWN | none | [16,8,4,2,1] | §5 |
| delay | 13.2 | ref invs | 0µ25 6-metal CMOS / year UNKNOWN | none | [16,4,2,2,1], buffering [2,1,1,0,0] | §5 |
| length | 38 | µm | 0µ25 6-metal CMOS / year UNKNOWN | none | [16,4,2,2,1], buffering [2,1,1,0,0] | §5 |
| transverse wire flux, total | 13 | UNKNOWN | 0µ25 6-metal CMOS / year UNKNOWN | none | [16,4,2,2,1] | §5 |
| delay | 13.0 | ref invs | 0µ25 6-metal CMOS / year UNKNOWN | none | [16,2,2,2,1], buffering [2,1,1,0,0] | §5 |
| length | 41 | µm | 0µ25 6-metal CMOS / year UNKNOWN | none | [16,2,2,2,1], buffering [2,1,1,0,0] | §5 |
| transverse wire flux, total | 17 | UNKNOWN | 0µ25 6-metal CMOS / year UNKNOWN | none | [16,2,2,2,1] | §5 |
| delay | 13.2 | ref invs | 0µ25 6-metal CMOS / year UNKNOWN | none | [4,4,2,2,1], buffering [1,1,0,0,0] | §5 |
| length | 35 | µm | 0µ25 6-metal CMOS / year UNKNOWN | none | [4,4,2,2,1], buffering [1,1,0,0,0] | §5 |
| transverse wire flux, total | 16 | UNKNOWN | 0µ25 6-metal CMOS / year UNKNOWN | none | [4,4,2,2,1] | §5 |
| delay | 12.7 | ref invs | 0µ25 6-metal CMOS / year UNKNOWN | none | [4,4,2,2,1], buffering [1,1,1,0,0] | §5 |
| length | 39 | µm | 0µ25 6-metal CMOS / year UNKNOWN | none | [4,4,2,2,1], buffering [1,1,1,0,0] | §5 |
| transverse wire flux, total | 16 | UNKNOWN | 0µ25 6-metal CMOS / year UNKNOWN | none | [4,4,2,2,1] | §5 |
| delay | 12.1 | ref invs | 0µ25 6-metal CMOS / year UNKNOWN | none | [2,2,2,1,1], buffering [1,1,1,0,0] | §5 |
| length | 46 | µm | 0µ25 6-metal CMOS / year UNKNOWN | none | [2,2,2,1,1], buffering [1,1,1,0,0] | §5 |
| transverse wire flux, total | 26 | UNKNOWN | 0µ25 6-metal CMOS / year UNKNOWN | none | [2,2,2,1,1] | §5 |
| delay | 12.1 | ref invs | 0µ25 6-metal CMOS / year UNKNOWN | none | [1,1,1,1,1], buffering [1,1,0,0,0] | §5 |
| length | 63 | µm | 0µ25 6-metal CMOS / year UNKNOWN | none | [1,1,1,1,1], buffering [1,1,0,0,0] | §5 |
| transverse wire flux, total | 42 | UNKNOWN | 0µ25 6-metal CMOS / year UNKNOWN | none | [1,1,1,1,1] | §5 |
| delay | 11.8 | ref invs | 0µ25 6-metal CMOS / year UNKNOWN | none | [1,1,1,1,1], buffering [1,1,1,0,0] | §5 |
| length | 63 | µm | 0µ25 6-metal CMOS / year UNKNOWN | none | [1,1,1,1,1], buffering [1,1,1,0,0] | §5 |
| transverse wire flux, total | 42 | UNKNOWN | 0µ25 6-metal CMOS / year UNKNOWN | none | [1,1,1,1,1] | §5 |
| area increase | 80% | more area | 0µ25 6-metal CMOS / year UNKNOWN | [4,4,2,2,1], buffering [1,1,0,0,0] | both Kogge-Stone layouts | §5 |
errors_and_checks: none
conditions: Each level-j lateral wire spans 2^j bits, and its fanout is a power of 2 from 1 through 2^j. # §4 Fanout cannot decrease from level j to level j+1. # §4 The measured delays are normalized to a reference inverter driving four identical inverters with zero wiring load. # §5 The reference inverter is typically 120-150ps at worst-case process parameters/125C/2V0 and 40-50% faster at typical process parameters/25C/2V5. # §5 Irregular hybrids preserve the critical path while reducing wiring on shorter paths, but structured layout density follows maximum per-level wire flux, so the paper expects no area advantage there. # §6 Random placement/routing might provide an area advantage, but the other comparisons become less robust. # §6
evidence: §2 prefix equations and Figure 1; §4 construction rules and Figures 4-6; §5 implementation table; §6 and Figure 7.

## new_families
none

## space_gaps
* `parallel_prefix.fanout_cap` excludes the demonstrated unit-fanout Kogge-Stone extreme and maximum fanout 16 used by several 32b structures. # §5
* `parallel_prefix` lacks per-level fanout/buffering vectors, which are the paper's identifiers and implementation controls. # §4, §5
* `parallel_prefix` lacks a choice for irregular path-dependent hybrids within a level. # §6

## open_questions
* The table does not state a unit for transverse wire flux. # §5
* The document does not report the year when the layouts or measurements were produced. # §5
