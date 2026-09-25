---
handle: camus2015
citation: V. Camus, J. Schlachter, C. Enz, "Energy-Efficient Inexact Speculative Adder with High Performance and Accuracy Control", IEEE International Symposium on Circuits and Systems (ISCAS), pp. 45-48, 2015
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [uint32]
authority: incremental
pages_read: 4 / 4 (pp.45-48)
---

## summary
The paper proposes the Inexact Speculative Adder (ISA), which partitions carry propagation into concurrent speculative sub-adders with error correction/reduction blocks (pp.45-46). The ISA independently sizes speculation, addition, correction, and balancing paths to trade delay/accuracy/hardware cost (pp.47-48).

## families
### segmented_carry_speculative  (role: proposes)
mechanism: The ISA divides the carry chain into concurrent SPEC-ADD-COMP paths. Each SPEC estimates a sub-adder carry-in from a limited preceding carry-lookahead window, and each ADD computes a local sum. Each COMP compares the speculated carry with the preceding ADD carry-out. A mismatch first triggers increment/decrement correction of local low bits; an overflowing correction instead flips preceding high bits to reduce error magnitude. Correction precomputation and compensation selection remain outside the critical path, which contains only the COMP multiplexers (pp.46-47).
choices:
  sub_adder_width: 16/8/4/2 bits [2 outside domain]   # p.48
  prediction_window: 0/1/2/4 bits [1 outside domain]   # p.48
  carry_in_scheme: propagate_window   # p.46
  correction: error_reduction_stage   # pp.46-47
new_choices:
  correction_bus_width: independently sized c-bit bus — controls the increment/decrement correction reach   # pp.46-48
  balancing_bus_width: independently sized r-bit bus — controls how many preceding sum bits are flipped after failed correction   # pp.46-48
  speculation_input: {static, dynamic} — selects the carry value guessed when the SPEC window is entirely propagating   # p.46
slots:
  none
parameters: 32-bit unsigned addition; 2x16/4x8/8x4/16x2 concurrent-path configurations; SPEC length s, correction length c, and reduction length r; over 500 synthesized implementations; 3.3 GHz and 5 GHz timing constraints; two samples of five million inputs each   # pp.47-48
results:
| metric | value | unit | technology / device | baseline | condition | page |
| power reduction | 11 to 26 | % | 65 nm technology library; 2015 | ETBA | identical RERMS and nearby REMAX | p.48 |
| EDAP reduction | 24 to 60 | % | 65 nm technology library; 2015 | ETBA | identical RERMS and nearby REMAX | p.48 |
| EDAP efficiency | twice | as efficient | 65 nm technology library; 2015 | selected 8x4 ISA | some 4x8 ISA implementations with higher accuracy | p.48 |
errors_and_checks: Relative error is RE = |(S − Scor)/Scor|. RERMS is estimated with five million uniformly distributed unsigned inputs, while REMAX is estimated with five million logarithmically uniformly distributed unsigned inputs (p.47). An XOR detects disagreement between the speculated carry and the preceding sub-adder carry-out (p.46). Correction succeeds unless every bit in the correction bus is propagating; otherwise balancing reduces the error magnitude without guaranteeing exactness (pp.46-47).
conditions: Long SPEC windows reduce speculation-fault probability for uniformly distributed inputs (p.46). The combined SPEC/correction reach prevents errors for propagation chains within their cumulative lengths (p.47). A balancing width larger than the SPEC width does not further reduce worst-case error, although it can improve typical accuracy (p.47). Short SPEC windows and fewer speculative paths improve power/EDAP, while added critical-path speculation overhead can prevent a design from satisfying the timing constraint (p.48). Weakly compensated designs can exhibit high relative errors, which limits practical use to error-tolerant applications (pp.45,48).
evidence: Fig. 1 and §§II.B-II.C describe the datapath; Fig. 2 gives a worked configuration; §§II.D-II.E establish correction/balancing behavior; §III.A defines evaluation; Figs. 6-7 and §III.B report comparisons (pp.45-48).

## new_families
none

## space_gaps
* `segmented_carry_speculative.sub_adder_width` excludes the reported 2-bit sub-adders in the 16x2 configurations (p.48).
* `segmented_carry_speculative.prediction_window` excludes the reported 1-bit SPEC configurations (p.48).
* The family lacks independently sized correction/balancing buses, which are central ISA accuracy controls (pp.46-48).
* The family lacks the static/dynamic speculation-input choice described for SPEC blocks (p.46).

## open_questions
* The implementation family used inside each ADD sub-adder is not specified (pp.46-48).
* Exact RERMS/REMAX values for the plotted implementations are not tabulated in the document (Figs. 6-7, p.48).
* The comparative study evaluates regular identical paths rather than independently optimized speculative paths, so results for nonuniform path sizing remain unreported (p.48).
