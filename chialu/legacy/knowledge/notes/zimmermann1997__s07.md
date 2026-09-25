---
handle: zimmermann1997#s07
parent: zimmermann1997
citation: zimmermann1997 — Binary Adder Architectures for Cell-Based VLSI and their Synthesis
chapter: Adder Synthesis
pdf_pages: 73-91
status: ok
kind: thesis_chapter
unit_classes: [BINARY_ALU]
formats: [binary]
authority: thesis
pages_read: 19 / 19
---

## summary
The chapter defines fixed and flexible synthesis algorithms for binary parallel-prefix adders. The proposed non-heuristic algorithm generates optimal or near-optimal prefix structures under depth/size/resource constraints and non-uniform timing profiles. Prefix-graph validity and irredundancy are characterized and verified through graph properties and legal transformations.   # p.74, p.78, p.83-p.91

## families
### ripple_carry  (role: taxonomizes)
mechanism: Serial evaluation of the associative prefix operator from LSB to MSB produces every intermediate prefix output. The serial-prefix structure uses the minimum number of black nodes and has maximum evaluation depth, corresponding to ripple-carry addition.
choices:
  full_adder_cell: UNKNOWN   # p.78, p.84
  carry_polarity_alternation: UNKNOWN   # p.78
new_choices:
  none
slots:
  none
parameters: word length n; structure size n-1 black nodes; structure depth n-1 black nodes   # p.78
results:
| metric | value | unit | technology / device | baseline | condition | page |
| structure size | n-1 | black nodes | abstract | parallel-prefix structures | serial-prefix structure | p.78 |
| structure depth | n-1 | black-node delays | abstract | log n minimum | serial-prefix structure | p.78 |
| 32-bit structure depth | 31 | black-node delays | abstract | other Figure 6.3 structures | serial-prefix structure | p.79 |
| 32-bit structure size | 31 | black nodes | abstract | other Figure 6.3 structures | serial-prefix structure | p.79 |
errors_and_checks: The optimized generation algorithm starts from a valid serial-prefix graph.   # p.81
conditions: The serial-prefix structure minimizes size but maximizes evaluation depth. Optimized full-adder cells can implement serial-prefix structures efficiently during technology mapping.   # p.78, p.84
evidence: Sections 6.3.2 and 6.4.2; Figures 6.2 and 6.3; Table 6.1.   # p.75, p.78-p.80

### carry_lookahead  (role: taxonomizes)
mechanism: Parallel application of associative prefix operators arranges carry evaluation in trees. Adders using these structures are described as carry-lookahead adders with different lookahead schemes.
choices:
  group_size: UNKNOWN   # p.78
  levels: UNKNOWN   # p.78
  intergroup_carry: lookahead   # p.78
  block_sizing: UNKNOWN   # p.78
new_choices:
  none
slots:
  none
parameters: structure depth ranges from n-1 down to log n as parallelism increases   # p.78
results:
| metric | value | unit | technology / device | baseline | condition | page |
| minimum structure depth | log n | black-node delays | abstract | serial evaluation | fully parallel prefix evaluation | p.78 |
errors_and_checks: none
conditions: More parallel evaluation reduces depth but requires additional black nodes for all prefix outputs. Wiring complexity and fan-out also vary among lookahead schemes.   # p.78
evidence: Section 6.4.2.   # p.78-p.80

### carry_increment  (role: taxonomizes)
mechanism: Carry-increment prefix structures exploit parallelism through hierarchical levels of serial evaluation chains rather than evaluation trees. The one-level form reduces to two prefix levels, while the two-level form reduces to three prefix levels.
choices:
  block_width: UNKNOWN   # p.77
  block_sizing: UNKNOWN   # p.77
  intergroup_carry: rippled   # p.78
  increment_levels: 1 | 2   # p.77-p.79
new_choices:
  max_black_nodes_per_bit_position: increment-level-dependent bound — bounded-# prefix structures constrain the black nodes in each bit-position column.   # p.78
slots:
  block_adder: UNKNOWN   # p.77
  increment_stage: UNKNOWN   # p.77
parameters: one or two increment levels; two or three reduced prefix levels; 32-bit examples   # p.77-p.79
results:
| metric | value | unit | technology / device | baseline | condition | page |
| structure depth | 8 | black-node delays | abstract | other 32-bit Figure 6.3 structures | 1-level carry-increment | p.79 |
| structure size | 54 | black nodes | abstract | other 32-bit Figure 6.3 structures | 1-level carry-increment | p.79 |
| structure depth | 6 | black-node delays | abstract | other 32-bit Figure 6.3 structures | 2-level carry-increment | p.79 |
| structure size | 68 | black nodes | abstract | other 32-bit Figure 6.3 structures | 2-level carry-increment | p.79 |
errors_and_checks: none
conditions: The increment-level count places the structure between serial-prefix and Sklansky structures. Bounding black nodes per column can recover size-optimal results for difficult timing profiles.   # p.78, p.84
evidence: Sections 6.3.5, 6.3.6, and 6.4.2; Figure 6.3(a)-(b).   # p.77-p.79

### parallel_prefix  (role: compares)
mechanism: A prefix graph evaluates the associative addition prefix operator in an arbitrary serial/parallel order. Structure depth represents critical-path black nodes, structure size represents total black nodes, and topology determines wiring complexity/fan-out.
choices:
  topology: sklansky | brent_kung | kogge_stone | han_carlson   # p.76-p.80
  valency: 2   # p.88-p.90
  log2_sparsity: UNKNOWN   # p.74-p.80
  fanout_cap: 2   # p.79
  wire_track_budget: UNKNOWN   # p.79-p.80
  node_style: and_or   # p.84
new_choices:
  structure_depth: n-1 through log n — number of black nodes on the critical path.   # p.78
  structure_size: total black-node count — circuit-area abstraction.   # p.78-p.80
slots:
  none
parameters: arbitrary word length; fixed algorithms include serial-prefix, Sklansky, Brent-Kung, and one-/two-level carry-increment structures   # p.74-p.78
results:
| metric | value | unit | technology / device | baseline | condition | page |
| Sklansky depth | log n | black-node delays | abstract | serial-prefix structure | minimum-depth topology | p.76, p.78 |
| Kogge-Stone depth | log n | black-node delays | abstract | other topologies | bounded fan-out topology | p.79 |
| Kogge-Stone maximum fan-out | 2 | loads | abstract | growing fan-out structures | Kogge-Stone topology | p.79 |
| Sklansky 32-bit depth | 5 | black-node delays | abstract | Figure 6.3 topologies | Sklansky structure | p.79 |
| Sklansky 32-bit size | 80 | black nodes | abstract | Figure 6.3 topologies | Sklansky structure | p.79 |
| Brent-Kung 32-bit depth | 8 | black-node delays | abstract | Figure 6.3 topologies | Brent-Kung structure | p.79 |
| Brent-Kung 32-bit size | 57 | black nodes | abstract | Figure 6.3 topologies | Brent-Kung structure | p.79 |
errors_and_checks: A valid graph computes the required prefix outputs, is equivalent to the serial-prefix graph, and has a path from each covered input. An irredundant graph has exactly one such path from each input.   # p.89-p.91
conditions: Sklansky is fastest but largest. Brent-Kung has almost twice the depth with fewer black nodes. Kogge-Stone bounds fan-out but its circuit/wiring complexity usually cancels that advantage; Han-Carlson mitigates the problem partly.   # p.78-p.79
evidence: Sections 6.3, 6.4.2, and 6.5; Figures 6.2, 6.3, and 6.13-6.17; Table 6.1.   # p.74-p.80, p.88-p.91

### prefix_synthesis_nonuniform_arrival  (role: proposes)
mechanism: The algorithm generates a serial-prefix graph, compresses every column with depth-decreasing transformations to obtain minimum depth, and then performs depth-controlled expansion with inverse transformations to reduce size. Linear graph traversals avoid heuristic transform selection and accept per-input arrival/per-output required-time margins.
choices:
  arrival_profile: uniform | multiplier_vee | lsb_late | msb_late   # p.78, p.83-p.87
  search_method: local_transform_compress_expand [outside domain]   # p.80-p.83
  fanout_cap: UNKNOWN   # p.84
  region_hybridization: true   # p.83-p.84
new_choices:
  depth_constraint: arbitrary per-output required time — expansion preserves permitted output depth.   # p.81-p.83
  size_constraint: optional total-black-node bound — adapted expansion generates area-constrained structures.   # p.83
  max_black_nodes_per_column: unbounded | bounded — the bound generates carry-increment forms and repairs steep timing profiles.   # p.83-p.84
  starting_graph: serial_prefix — required for a perfect minimum-depth compression result.   # p.81
slots:
  none
parameters: arbitrary word length; arbitrary input/output timing profiles; optional depth/size/resource and per-column bounds   # p.78, p.83-p.85
results:
| metric | value | unit | technology / device | baseline | condition | page |
| synthesis runtime | below 1s | seconds | Sun SPARCstation-10 | UNKNOWN | prefix graphs up to several hundred bits | p.83 |
| linear trade-off bound | depth + size ≥ 2n-2 | abstract | abstract | Snir lower bound | depths from 2 log n-3 through n-1 | p.83 |
| optimized 32-bit depth/size | 5 / 74 | black-node delays / black nodes | abstract | compressed size 80 | uniform arrivals | p.86 |
| optimized 32-bit depth/size | 6 / 59 | black-node delays / black nodes | abstract | compressed depth/size 5 / 80 | uniform arrivals | p.86 |
| optimized 32-bit depth/size | 7 / 55 | black-node delays / black nodes | abstract | compressed depth/size 5 / 80 | uniform arrivals | p.86 |
| optimized 32-bit depth/size | 8 / 54 | black-node delays / black nodes | abstract | compressed depth/size 5 / 80 | uniform arrivals | p.86 |
| optimized 32-bit depth/size | 12 / 50 | black-node delays / black nodes | abstract | compressed depth/size 5 / 80 | uniform arrivals | p.86 |
| late-bit accommodation | 4 | black-node delays | abstract | uniform timing | any single bit, total depth log n+1 | p.84-p.85 |
| steep multiplier profile depth/size | 16 / 65 | black-node delays / black nodes | abstract | compressed size 114 | no per-column bound | p.87 |
| steep multiplier profile depth/size | 16 / 56 | black-node delays / black nodes | abstract | compressed size 68 | maximum 5 black nodes per column | p.87 |
| steep multiplier profile depth/size | 16 / 56 | black-node delays / black nodes | abstract | compressed size 57 | maximum 3 black nodes per column | p.87 |
errors_and_checks: Generated graphs are correct-by-construction because compression/expansion use validity- and irredundancy-preserving transformations. Most solutions are size-optimal or near-optimal.   # p.83-p.84, p.91
conditions: Uniform profiles attain the linear Snir bound for depths from 2 log n-3 through n-1. Depths nearer log n have an exponential size/depth trade-off and are usually near-optimal except at minimum depth. Steep negative arrival slopes require a per-column bound of about log n for size-optimal results. Fan-out optimization is deferred to buffering/technology mapping.   # p.83-p.84
evidence: Sections 6.4.1-6.4.5 and 6.5; Figures 6.4-6.12.   # p.78-p.91

## taxonomy
* Fixed parallel-prefix structures   # p.74-p.78
  * serial-prefix graph -> ripple_carry   # p.75, p.78
  * 1-level carry-increment parallel-prefix graph -> carry_increment   # p.77
  * 2-level carry-increment parallel-prefix graph -> carry_increment   # p.77
  * Sklansky parallel-prefix graph -> parallel_prefix   # p.76
  * Brent-Kung parallel-prefix graph -> parallel_prefix   # p.76-p.77
* Flexible parallel-prefix structures   # p.78-p.85
  * uniform signal-arrival profiles -> prefix_synthesis_nonuniform_arrival   # p.83
    * minimum-depth Sklansky form -> parallel_prefix   # p.81, p.83
    * size-optimized Sklansky/Brent-Kung forms -> parallel_prefix   # p.83
    * mixed serial/Brent-Kung region forms -> parallel_prefix   # p.83
  * non-uniform signal-arrival profiles -> prefix_synthesis_nonuniform_arrival   # p.84
    * late upper/lower half-word -> prefix_synthesis_nonuniform_arrival   # p.84, p.86
    * late single bit -> prefix_synthesis_nonuniform_arrival   # p.84-p.85
    * early upper/lower output half-word -> prefix_synthesis_nonuniform_arrival   # p.84, p.86
    * steep multiplier-final-adder profile -> prefix_synthesis_nonuniform_arrival   # p.84, p.87
  * bounded black nodes per column -> carry_increment   # p.83-p.84
  * size-constrained graph synthesis -> prefix_synthesis_nonuniform_arrival   # p.83
  * resource-constrained harmonic schedule -> unmapped   # p.84-p.87
  * strict time-optimal resource schedule -> unmapped   # p.85
* Optimization approaches   # p.80-p.83
  * heuristic local transformations -> prefix_synthesis_nonuniform_arrival   # p.80-p.81
  * non-heuristic compression plus expansion -> prefix_synthesis_nonuniform_arrival   # p.81-p.83
  * evolutionary algorithms, not pursued -> unmapped   # p.91
* Prefix-graph classes   # p.89-p.91
  * valid and irredundant -> unmapped   # p.89-p.91
  * valid and redundant -> unmapped   # p.89-p.91
  * invalid -> unmapped   # p.89-p.90

## primary_sources
* Sklansky, 1960 — minimum-depth parallel-prefix structure.   # p.78
* Kogge and Stone, 1973 — minimum-depth prefix structure with fan-out bounded by 2.   # p.79
* Brent and Kung, 1982 — lower-size topology with almost twice Sklansky depth.   # p.78
* Han and Carlson, 1987 — mixed Kogge-Stone/Brent-Kung bounded-fan-out structure.   # p.79
* Snir, 1986 — linear size/depth trade-off for mixed serial/parallel-prefix structures.   # p.78, p.83
* Fishburn, 1990 — local prefix transformations for timing optimization.   # p.79-p.81
* Guyot et al., 1994 — related heuristic local-transform optimization.   # p.80
* Zimmermann, 1996 — universal flexible synthesis based on local prefix-graph transformations.   # p.78
* WNS, 1996 — time-optimal and harmonic resource-constrained prefix schedules.   # p.84-p.85
* KZ, 1996 — parameterized algorithms for fixed prefix structures.   # p.74-p.75

## new_families
none

## space_gaps
* `search_method` lacks the chapter's non-heuristic compression/depth-controlled-expansion method.   # p.81-p.83
* `prefix_synthesis_nonuniform_arrival` lacks output required-time profiles and explicit depth/size constraints.   # p.78, p.83
* `prefix_synthesis_nonuniform_arrival` lacks a maximum-black-nodes-per-column choice for bounded carry-increment synthesis and steep arrival profiles.   # p.83-p.84
* `parallel_prefix.topology` lacks Snir variable serial/parallel structures.   # p.78, p.83
* Resource-constrained prefix schedules lack a family, although the chapter states that they have no significance for combinational adder design.   # p.84-p.85
* Evolutionary synthesis is absent from `search_method`; the chapter considers but rejects it because of implementation problems.   # p.91

## open_questions
* The OCR does not preserve every symbolic expression in Table 6.1 reliably, so unreadable topology formulas must not be reconstructed during merge.   # p.80
* The chapter does not quantify how often “near-optimal” structures differ from the size optimum in the exponential trade-off region.   # p.83
* The chapter defers fan-out buffering and decoupling to logic optimization/technology mapping without specifying a synthesis-time fan-out limit.   # p.84
