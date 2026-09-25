---
handle: han_carlson1987
citation: T. Han, D. A. Carlson, "Fast Area-Efficient VLSI Adders", 8th IEEE Symposium on Computer Arithmetic (ARITH-8), pp. 49-56, 1987.
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [binary_integer]
authority: landmark
pages_read: 49-56 / 8
---

## summary
The paper combines Brent-Kung and Kogge-Stone prefix graphs to construct a binary adder with intermediate area/delay tradeoffs (pp.49-51). The area-optimal layout achieves \(O(n\log n)\) area at the lowest derived delay for that area class, while a folded layout targets practical adders of up to 64 bits (pp.51-53).

## families
### parallel_prefix  (role: proposes)
mechanism: The hybrid prefix graph places an embedded Kogge-Stone graph between multiple Brent-Kung graphs. Extra depth \(k\) controls the number of Kogge-Stone inputs and the sizes of the surrounding Brent-Kung graphs. Alternating positive/negative black cells implement the associative prefix operator without separate inverter stages, and sum cells consume the alternating carry polarities (pp.50-52).
choices:
  topology: han_carlson   # p.50
  valency: 2   # pp.51-52
  fanout_cap: 2   # pp.51-53
  node_style: aoi_oai_alternating   # p.52
new_choices:
  extra_depth_k: Int[0..log n-1:1] — controls the embedded Kogge-Stone size and surrounding Brent-Kung depth   # pp.50-51
  layout_style: {boundary_io, area_optimal} — trades boundary placement of all inputs/outputs against asymptotically optimal area   # pp.50-51
  level_folding: Bool — places two prefix levels into one physical layout level   # p.53
slots:
  none
parameters: General \(n\)-bit binary addition; demonstrated layout \(n=16\), \(k=1\), prefix depth 5, 4 µm NMOS rules; \(k=1\) is used for \(n\leq64\), while \(k=\log n-\log\log n\) is used in the large-\(n\) timing comparison (pp.52-53).
results:
| metric | value | unit | technology / device | baseline | condition | page |
| area complexity | O(n log n) | area | UNKNOWN | Kogge-Stone O(n²) | area-optimal layout with 1/2(log n-log log n) ≤ k ≤ log n-1 | p.51 |
| minimum delay with O(n log n) area | 3/2(log n)-1/2(log log n-O(1)) | prefix levels | UNKNOWN | Brent-Kung 2 log n-1 | area-optimal layout | p.51 |
| prefix depth | 5 | levels | 4 µm NMOS | Brent-Kung 7 levels | n=16, k=1 | p.52 |
| layout area reduction | one half | area | 4 µm NMOS | unfolded hybrid layout | folding, n≤64 | p.53 |
| layout area, n=16 | 350 × 700 | λ² | 4 µm NMOS | ripple carry 200 × 700 λ² | hybrid prefix adder | p.56 |
| layout area, n=32 | 500 × 1400 | λ² | 4 µm NMOS | ripple carry 200 × 1400 λ² | hybrid prefix adder | p.56 |
| layout area, n=64 | 650 × 2100 | λ² | 4 µm NMOS | ripple carry 200 × 2100 λ² | hybrid prefix adder | p.56 |
| modeled delay, n=16 | 3.5 | t | UNKNOWN, 1987 | CLA 6t; carry-skip 5t | bounded fan-in/fan-out comparison | p.56 |
| modeled delay, n=32 | 4 | t | UNKNOWN, 1987 | CLA 8t; carry-skip 7t | bounded fan-in/fan-out comparison | p.56 |
| modeled delay, n=64 | 4.5 | t | UNKNOWN, 1987 | CLA 10t; carry-skip 10t | bounded fan-in/fan-out comparison | p.56 |
| worst-case delay, n=8 | 7 | gate levels | UNKNOWN, 1987 | ripple carry 18; Brent-Kung 15 | gate-count method | p.56 |
| worst-case delay, n=16 | 8 | gate levels | UNKNOWN, 1987 | ripple carry 34; Brent-Kung 19 | gate-count method | p.56 |
| worst-case delay, n=32 | 9 | gate levels | UNKNOWN, 1987 | ripple carry 66 | gate-count method | p.56 |
| worst-case delay, n=64 | 10 | gate levels | UNKNOWN, 1987 | ripple carry 130; Brent-Kung 27 | gate-count method | p.56 |
| worst-case delay, n=256 | 17 | gate levels | UNKNOWN, 1987 | ripple carry 514; Brent-Kung 35 | gate-count method | p.56 |
| worst-case delay, n=512 | 19 | gate levels | UNKNOWN, 1987 | Brent-Kung 39 | gate-count method | p.56 |
errors_and_checks: none
conditions: The boundary-I/O layout retains a regular connection pattern but does not meet the area lower bound, while the area-optimal layout loses the property that every input/output lies on a boundary (pp.50-51). The \(k=1\) folded design targets \(n\leq64\); for larger \(n\), interconnection area dominates and larger \(k\) is required (pp.51-53). The \(k=0\) Kogge-Stone case is area-inefficient and cannot benefit from folding (p.51). The timing comparisons omit wire-capacitance delay because the compared prefix designs have similar total input-to-output wire length, but an actual implementation must include that delay (p.53).
evidence: §§2.2-2.4, Figures 2.3-2.4, §§3.1-3.3, Figures 3.1-3.5, §4, Tables 2.1-2.2 and 4.1-4.4 (pp.50-56).

## new_families
none

## space_gaps
* `parallel_prefix` lacks the `extra_depth_k` choice that controls the Han-Carlson graph’s Brent-Kung/Kogge-Stone balance (pp.50-51).
* `parallel_prefix` lacks a layout choice covering boundary I/O versus minimum-area placement (pp.50-51).
* `parallel_prefix` lacks a folding choice for mapping two logical prefix levels into one physical level (p.53).
* `node_style: aoi_oai_alternating` covers the alternating polarity approximately, but the document describes explicit `bp.ca`/`bn.ca` cells rather than naming AOI/OAI gates (p.52).

## open_questions
* The paper does not state the logarithm base used in its depth formulas.
* The paper reports modeled delay units and gate levels rather than measured silicon delay.
* The paper does not report power, energy, or fabricated-chip measurements.
