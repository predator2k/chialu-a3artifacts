---
handle: zimmermann1997#s05
parent: zimmermann1997
citation: Binary Adder Architectures for Cell-Based VLSI and their Synthesis
chapter: Adder Architectures
pdf_pages: 40-62
status: ok
kind: thesis_chapter
unit_classes: [BINARY_ALU]
formats: [binary integer]
authority: thesis
pages_read: 23 / 23
---

## summary
The chapter defines and classifies ripple-carry, carry-skip, carry-select, conditional-sum, carry-increment, carry-lookahead, and parallel-prefix adders. Unit-gate and placed-and-routed standard-cell comparisons establish CIA-2L/PPA-BK/PPA-SK as efficient cell-based choices, while wiring and fan-out penalize PPA-KS/COSA at large widths. The chapter proposes the 2-level carry-increment adder and identifies it as a variable-group parallel-prefix structure.

## families
### ripple_carry  (role: defines)
mechanism: A series of full-adders propagates the carry linearly; the initial full-adder may use a majority gate for faster carry computation.
choices:
  full_adder_cell: UNKNOWN
  carry_polarity_alternation: UNKNOWN
new_choices:
  none
slots:
  none
parameters: word lengths 8, 16, 32, 64, 128 bits; unit-gate delay 2n and gate count 7n   # p.53
results:
| metric | value | unit | technology / device | baseline | condition | page |
| gate count | 58, 114, 226, 450, 898 | unit gates | abstract | none | widths 8, 16, 32, 64, 128 bits | p.53 |
| gate delay | 16, 32, 64, 128, 256 | gate delays | abstract | none | widths 8, 16, 32, 64, 128 bits | p.53 |
| post-layout area | 238, 457, 821, 1734, 3798 | 1000 λ² | Passport 0.6 µm 3V CMOS | none | widths 8, 16, 32, 64, 128 bits | p.54 |
| post-layout delay | 4.6, 8.2, 15.8, 30.4, 61.8 | ns | Passport 0.6 µm 3V CMOS | none | widths 8, 16, 32, 64, 128 bits | p.54 |
| post-layout power | 24, 52, 95, 194, 387 | µW/MHz | Passport 0.6 µm 3V CMOS | none | widths 8, 16, 32, 64, 128 bits | p.55 |
errors_and_checks: none
conditions: RCA has the smallest area and longest delay; it suits small-area/moderate-speed requirements.   # p.56, p.57
evidence: Sections 4.1.1, 4.2.1–4.2.5; Tables 4.3–4.12.

### carry_skip  (role: taxonomizes)
mechanism: Skipping groups contain ripple full-adders, group-propagate generation, an initial block full-adder, and a final block carry generator. One-level redundant/irredundant and hierarchical two-level forms are presented.
choices:
  block_width: UNKNOWN
  block_sizing: trapezoidal_variable   # p.41
  skip_levels: 1, 2   # p.41, p.42
  skip_gate: and_or_bypass   # p.41
new_choices:
  redundancy: {redundant, irredundant} — whether inherent skip logic redundancy is retained   # p.42
slots:
  block_adder: ripple_carry   # p.41
parameters: adjacent one-level groups differ by one bit; multilevel optimal sizes are highly irregular   # p.41, p.42
results:
| metric | value | unit | technology / device | baseline | condition | page |
| gate count, CSKA-1L/CSKA-2L | 76/71, 146/158, 286/323, 554/633, 1090/1248 | unit gates | abstract | none | widths 8, 16, 32, 64, 128 bits | p.53 |
| gate delay, CSKA-1L/CSKA-2L | 12/12, 16/16, 24/20, 32/24, 48/32 | gate delays | abstract | none | widths 8, 16, 32, 64, 128 bits | p.53 |
| post-layout area, CSKA-1L/CSKA-2L | 298/297, 518/512, 885/924, 1932/2196, 4468/4402 | 1000 λ² | Passport 0.6 µm 3V CMOS | none | widths 8, 16, 32, 64, 128 bits | p.54 |
| post-layout delay, CSKA-1L/CSKA-2L | 4.2/4.2, 5.7/5.7, 9.0/8.1, 11.9/10.2, 15.9/13.3 | ns | Passport 0.6 µm 3V CMOS | none | widths 8, 16, 32, 64, 128 bits | p.54 |
errors_and_checks: none
conditions: Two levels improve speed with little area increase; irredundant and other variants were excluded because efficient cell-based solutions were not expected.   # p.52, p.56
evidence: Sections 4.1.2, 4.2; Tables 4.3–4.12.

### carry_select  (role: analyzes)
mechanism: Each bit computes sum/carry for both possible block carry-ins, and multiplexers select the correct values; the block carry is selected at the block end.
choices:
  block_sizing: variable_increasing_toward_msb [outside domain]   # p.43
  duplication: full_duplicate   # p.43
  select_source: rippled_block_carries   # p.43
new_choices:
  none
slots:
  block_adder: ripple_carry   # p.45
parameters: one-level variable blocks; multilevel hardware grows prohibitively through repeated duplication   # p.43
results:
| metric | value | unit | technology / device | baseline | condition | page |
| gate count | 87, 194, 403, 836, 1707 | unit gates | abstract | none | widths 8, 16, 32, 64, 128 bits | p.53 |
| gate delay | 10, 12, 18, 24, 34 | gate delays | abstract | none | widths 8, 16, 32, 64, 128 bits | p.53 |
| post-layout area | 339, 612, 1322, 2965, 6381 | 1000 λ² | Passport 0.6 µm 3V CMOS | none | widths 8, 16, 32, 64, 128 bits | p.54 |
| post-layout delay | 3.3, 4.8, 6.1, 8.6, 12.8 | ns | Passport 0.6 µm 3V CMOS | none | widths 8, 16, 32, 64, 128 bits | p.54 |
errors_and_checks: none
conditions: Carry-increment optimization outperforms CSLA in area/delay; CSLA also has the highest observed glitching-power fraction.   # p.56, p.58
evidence: Sections 4.1.3, 4.2; Tables 4.3–4.12.

### conditional_sum  (role: defines)
mechanism: Maximum-level recursive carry selection generates both results at level one and duplicates only multiplexers at later levels. Group sizes begin at one bit and double at every level.
choices:
  base_block_width: 1   # p.43
  mux_style: static_gate   # p.44
  selection_radix: 2   # p.43
new_choices:
  fanout_class: unbounded — the chapter classifies COSA by unbounded fan-out   # p.58
slots:
  none
parameters: log2 n levels; gate count 3n log2 n; delay 2 log2 n   # p.44, p.53
results:
| metric | value | unit | technology / device | baseline | condition | page |
| gate count | 115, 289, 687, 1581, 3563 | unit gates | abstract | none | widths 8, 16, 32, 64, 128 bits | p.53 |
| gate delay | 8, 10, 12, 14, 16 | gate delays | abstract | none | widths 8, 16, 32, 64, 128 bits | p.53 |
| post-layout area | 419, 924, 1789, 4399, 10614 | 1000 λ² | Passport 0.6 µm 3V CMOS | none | widths 8, 16, 32, 64, 128 bits | p.54 |
| post-layout delay | 3.4, 4.5, 5.1, 6.4, 9.2 | ns | Passport 0.6 µm 3V CMOS | none | widths 8, 16, 32, 64, 128 bits | p.54 |
errors_and_checks: none
conditions: COSA is fastest in the unit-gate model, but large area/wiring and heavy fan-out degrade post-layout speed and AT/PT products.   # p.56, p.57
evidence: Sections 4.1.4, 4.2; Tables 4.3–4.12.

### carry_increment  (role: proposes)
mechanism: One ripple chain is combined with increment logic so one carry, rather than two carries, propagates. The proposed CIA-2L replaces ripple blocks with merged second-level increment blocks and implements the optimized variable-group 2-level group-prefix algorithm.
choices:
  block_width: UNKNOWN
  block_sizing: variable_ramp   # p.46, p.48
  intergroup_carry: rippled   # p.46
  increment_levels: 1, 2   # p.45, p.47
new_choices:
  higher_increment_levels: 3_to_log2_n — studied beyond the declared two-level domain   # p.48, p.58
slots:
  block_adder: ripple_carry   # p.45
  increment_stage: prefix_and_incrementer   # p.45
parameters: CIA-1L basic slice 10 gates; CIA-2L basic slice 10 gates; 24 gate delays permit 67 bits in CIA-1L; CIA-2L supports 177 bits at 24 gate delays   # p.46, p.48
results:
| metric | value | unit | technology / device | baseline | condition | page |
| gate count, CIA-1L/CIA-2L/CIA-3L | 78/79/80, 157/158/159, 314/316/324, 631/635/639, 1266/1273/1280 | unit gates | abstract | none | widths 8, 16, 32, 64, 128 bits | p.53 |
| gate delay, CIA-1L/CIA-2L/CIA-3L | 10/10/10, 12/12/12, 18/16/16, 24/18/18, 34/22/20 | gate delays | abstract | none | widths 8, 16, 32, 64, 128 bits | p.53 |
| post-layout area, CIA-1L/CIA-2L | 299/289, 584/574, 1119/1094, 2477/2426, 5189/5353 | 1000 λ² | Passport 0.6 µm 3V CMOS | none | widths 8, 16, 32, 64, 128 bits | p.54 |
| post-layout delay, CIA-1L/CIA-2L | 3.6/3.8, 4.7/4.7, 6.1/5.7, 8.0/6.8, 11.2/8.5 | ns | Passport 0.6 µm 3V CMOS | none | widths 8, 16, 32, 64, 128 bits | p.54 |
| post-layout power, CIA-1L/CIA-2L | 32/28, 64/60, 116/124, 257/267, 494/558 | µW/MHz | Passport 0.6 µm 3V CMOS | none | widths 8, 16, 32, 64, 128 bits | p.55 |
errors_and_checks: none
conditions: CIA-2L adds negligible area over CIA-1L and gives the lowest large-width AT/PT products; more than two levels help only above 64 bits and increase complexity.   # p.48, p.49, p.56, p.57
evidence: Sections 4.1.5, 4.2; Figures 4.3–4.6; Tables 4.3–4.12.

### carry_lookahead  (role: instantiates)
mechanism: The standard CLA is a 4-bit Brent-Kung prefix architecture: one phase computes every fourth carry, and a second phase computes the remaining carries.
choices:
  group_size: 4   # p.50
  levels: UNKNOWN
  intergroup_carry: lookahead   # p.50
  block_sizing: uniform   # p.50
new_choices:
  none
slots:
  none
parameters: 2-bit first-level blocks are used when width is not a power of four   # p.52
results:
| metric | value | unit | technology / device | baseline | condition | page |
| gate count | 92, 204, 428, 876, 1772 | unit gates | abstract | none | widths 8, 16, 32, 64, 128 bits | p.53 |
| gate delay | 12, 16, 20, 24, 28 | gate delays | abstract | none | widths 8, 16, 32, 64, 128 bits | p.53 |
| post-layout area | 324, 649, 1267, 2816, 6543 | 1000 λ² | Passport 0.6 µm 3V CMOS | none | widths 8, 16, 32, 64, 128 bits | p.54 |
| post-layout delay | 3.9, 4.7, 5.8, 6.7, 8.2 | ns | Passport 0.6 µm 3V CMOS | none | widths 8, 16, 32, 64, 128 bits | p.54 |
errors_and_checks: none
conditions: A final carry-select stage has the same unit-gate speed as pure CLA but substantially higher gate count.   # p.51
evidence: Sections 4.1.6–4.1.7, 4.2; Tables 4.3–4.12.

### parallel_prefix  (role: compares)
mechanism: Initial generate/propagate preprocessing and final sum generation surround topology-specific carry-generation levels. Binary prefixes normally combine two-bit groups; larger-valency forms reduce levels but increase logic complexity.
choices:
  topology: sklansky, brent_kung, kogge_stone   # p.50, p.52
  valency: 2   # p.49
  log2_sparsity: 0   # p.49
  fanout_cap: 2   # p.52
  wire_track_budget: UNKNOWN
  node_style: and_or   # p.50
new_choices:
  unbounded_fanout: {true, false} — Sklansky is unbounded; Brent-Kung/Kogge-Stone are bounded in the selected architectures   # p.52
slots:
  none
parameters: widths 8, 16, 32, 64, 128 bits; 4-bit forms show no advantage and 8-bit forms become larger/slower   # p.52, p.58
results:
| metric | value | unit | technology / device | baseline | condition | page |
| gate count, SK/BK/KS | 73/70/88, 165/147/216, 373/304/520, 837/621/1224, 1861/1258/2824 | unit gates | abstract | none | widths 8, 16, 32, 64, 128 bits | p.53 |
| gate delay, SK/BK/KS | 10/12/10, 12/16/12, 14/20/14, 16/24/16, 18/28/18 | gate delays | abstract | none | widths 8, 16, 32, 64, 128 bits | p.53 |
| post-layout area, SK/BK/KS | 266/270/408, 580/549/1027, 1276/1051/2292, 2979/2316/5080, 7918/5170/13616 | 1000 λ² | Passport 0.6 µm 3V CMOS | none | widths 8, 16, 32, 64, 128 bits | p.54 |
| post-layout delay, SK/BK/KS | 3.5/4.1/3.4, 4.2/5.4/4.2, 5.2/6.2/5.3, 6.0/7.8/6.9, 8.1/9.3/9.3 | ns | Passport 0.6 µm 3V CMOS | none | widths 8, 16, 32, 64, 128 bits | p.54 |
errors_and_checks: none
conditions: PPA-SK is fastest at large widths but uses substantial area; PPA-BK is slower and area-efficient; PPA-KS suffers large-area routing delay despite bounded fan-out.   # p.56
evidence: Sections 4.1.6, 4.2; Tables 4.3–4.12.

## taxonomy
* Linear carry propagation   # p.52
  * Ripple-carry adder (RCA) -> ripple_carry
* Fixed-level compound schemes with variable blocks   # p.52
  * 1-level redundant carry-skip (CSKA-1L) -> carry_skip
  * 1-level irredundant carry-skip (CSKA-1L’) -> carry_skip
  * 2-level carry-skip (CSKA-2L) -> carry_skip
  * 1-level carry-select (CSLA-1L) -> carry_select
  * 1/2/3-level carry-increment (CIA-1L/-2L/-3L) -> carry_increment
* Linear-area logarithmic-delay prefix schemes   # p.52
  * Standard 4-bit carry-lookahead (CLA) -> carry_lookahead
  * Brent-Kung parallel-prefix (PPA-BK) -> parallel_prefix
* n log n-area logarithmic-delay schemes   # p.52
  * Sklansky parallel-prefix (PPA-SK) -> parallel_prefix
  * Kogge-Stone parallel-prefix (PPA-KS) -> parallel_prefix
  * Conditional-sum (COSA) -> conditional_sum
* Hybrid architectures   # p.51
  * Carry-lookahead blocks plus final carry-select stage -> carry_lookahead

## primary_sources
* Tyagi, 1993 — reduced-area carry-select scheme and select-prefix improvement.   # p.45, p.47
* Sklansky, 1960 — unbounded-fan-out parallel-prefix structure.   # p.52
* Brent and Kung, 1982 — bounded-fan-out parallel-prefix structure.   # p.52
* Kogge and Stone, 1973 — bounded-fan-out parallel-prefix structure.   # p.52
* Turner, 1989 — maximum-block construction used to optimize variable block sizes.   # p.51

## new_families
none

## space_gaps
* `carry_skip` lacks a redundancy choice for the chapter's redundant/irredundant CSKA-1L distinction.   # p.42
* `carry_increment.increment_levels` excludes the chapter's CIA-3L and log2 n-level structures.   # p.48, p.58
* `parallel_prefix.fanout_cap` cannot represent the unbounded fan-out assigned to Sklansky.   # p.52

## open_questions
* The extracted equations contain degraded mathematical symbols, so several exact closed-form complexity expressions beyond Table 4.3 remain unreadable.
* The bibliographic names behind citation keys without names in the chapter text remain unresolved.
