---
handle: harris2003
citation: D. Harris, "A Taxonomy of Parallel Prefix Networks", 37th Asilomar Conference on Signals, Systems and Computers, 2003.
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [int16, int32, int64]
authority: landmark
pages_read: 2213-2217 / 5
---

## summary
The paper classifies valency-2 parallel-prefix networks by logic levels/fanout/wiring tracks and places established adder networks within this taxonomy. The taxonomy identifies new interior networks whose estimated latency and area are competitive for some circuit technologies.

## families
### parallel_prefix  (role: proposes)
mechanism: An N-input associative prefix computation uses precomputation, a prefix-cell network, and postcomputation. For addition, generate/propagate signals enter black cells that compute both prefix outputs, gray cells that discard an unneeded propagate output, and buffers that reduce noncritical loading. The tuple (l,f,t) describes logic levels L+l, maximum fanout 2^f+1, and horizontal wiring tracks 2^t for L=log2N. Established networks occupy the plane l+f+t=L-1, while the proposed family uses interior points with l,f,t>0.
choices:
  topology: brent_kung / sklansky / kogge_stone / ladner_fischer / han_carlson / knowles_mixed / (l,f,t) interior family [outside domain]   # pp.2213-2215
  valency: 2   # p.2213
  fanout_cap: 2^f+1 [outside domain]   # p.2214
  wire_track_budget: 2^t [outside domain]   # p.2214
  node_style: dynamic_domino   # pp.2215,2217
new_choices:
  taxonomy_coordinates: (l,f,t), constrained by l+f+t=L-1 for established networks — l adds logic levels, f determines fanout, and t determines wiring tracks   # pp.2214-2215
  circuit_family: {inverting_static_cmos, noninverting_static_cmos, footed_domino, footless_domino} — circuit implementations compared in the delay tables   # pp.2215,2217
  wire_capacitance_ratio: w — wire capacitance per traversed column divided by unit-inverter input capacitance   # p.2215
slots:
  none
parameters: N=16 for the six illustrated networks and the (1,1,1) interior network; N=32 permits (1,1,2), (1,2,1), and (2,1,1); delay comparisons include N=32/64   # pp.2214-2217
results:
| metric | value | unit | technology / device | baseline | condition | page |
| logic levels | L+l | levels | UNKNOWN / 2003 | ideal prefix network: L | N-bit network, L=log2N | p.2214 |
| maximum fanout | 2^f+1 | loads | UNKNOWN / 2003 | ideal prefix network: no greater than 2 | N-bit network | p.2214 |
| horizontal wiring tracks | 2^t | tracks per stage | UNKNOWN / 2003 | ideal prefix network: 1 | N-bit network | p.2214 |
| datapath columns | half as many | columns | UNKNOWN / 2003 | dense network | networks with l>0 | p.2215 |
| wire capacitance ratio w | 0.5 | unit-inverter input capacitance per column traversed | 180 nm / 2003 | trial layout | widely spaced tracks | p.2215 |
| wire capacitance ratio w | 1 | unit-inverter input capacitance per column traversed | 180 nm / 2003 | trial layout | many tightly spaced tracks | p.2215 |
errors_and_checks: none
conditions: Latency depends on logic levels/fanout/wiring capacitance rather than logic depth alone. # pp.2213-2215; Large track counts increase wiring capacitance when tracks use a tight pitch. # p.2214; Cells use equal, arbitrary drive capability that is generally greater than minimum. # p.2215; Networks with l>0 use half as many cell columns, which can reduce area and wire length. # pp.2214-2215; The new architecture is competitive in latency and area only for some technologies. # pp.2213,2215
evidence: §I and Fig.1, p.2213; Fig.2, p.2214; §III and Figs.3-4, pp.2214-2216; §IV and Tables 1-4, pp.2215,2217.

## new_families
none

## space_gaps
* The parallel_prefix topology domain lacks the Harris interior `(l,f,t)` family, including (1,1,1) for N=16 and (1,1,2)/(1,2,1)/(2,1,1) for N=32. # p.2215
* The parallel_prefix family lacks explicit logic-level/fanout/wiring-track coordinates, which are the paper's principal design variables. # pp.2214-2215
* The parallel_prefix node_style choice does not preserve the paper's inverting/noninverting static CMOS and footed/footless domino distinctions. # pp.2215,2217

## open_questions
* The supplied rendering does not preserve enough row labels and values in Tables 1-4 to associate the visible delay numbers reliably with individual networks. # p.2217
* The exact printed upper bound for l/f/t is unclear in the supplied text, so the merge pass must not infer it from the plane equation. # p.2214
