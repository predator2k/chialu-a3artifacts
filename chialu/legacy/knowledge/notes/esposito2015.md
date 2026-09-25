---
handle: esposito2015
citation: D. Esposito, D. De Caro, E. Napoli, N. Petra, A. G. M. Strollo, "Variable Latency Speculative Han-Carlson Adder", IEEE Transactions on Circuits and Systems I, vol. 62, no. 5, pp. 1353-1361, 2015.
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [int32, int64, int128]
authority: incremental
pages_read: 9 / 9
---

## summary
The paper proposes a variable-latency speculative adder obtained by pruning intermediate levels from a Han-Carlson parallel-prefix carry tree and correcting failed speculation in a second cycle (p.1, p.3, p.5). A necessary-and-sufficient error detector reduces the error probability, while the Han-Carlson checking-node arrangement halves the number of detector terms relative to speculative Kogge-Stone (p.4). UMC 65 nm synthesis shows benefits under tight speed constraints, while non-speculative adders remain preferable when the constraint is relaxed (p.6–p.9).

## families
### speculative_variable_latency  (role: proposes)
mechanism: The speculative prefix stage assumes that carry-propagate chains do not exceed K bits and computes approximate carries from a pruned Han-Carlson graph. Checking nodes feed a necessary-and-sufficient error detector. A successful speculation completes in one clock cycle; a detected misprediction discards the approximate result and enables the pruned prefix levels to produce the exact sum in the next cycle (p.1, p.3–p.5).
choices:
  speculation_window: UNKNOWN   # p.3, p.6
  detection: propagate_run_detector   # p.3–p.4
  recovery: extra_cycle_correction   # p.1, p.5
new_choices:
  error_detection_precision: precise — the proposed detector implements a necessary-and-sufficient condition rather than the earlier necessary-only coarse condition   # p.4, p.6
  pruned_levels: UNKNOWN — the number of removed prefix levels determines K and the speculative-stage depth   # p.3
slots:
  base_adder: parallel_prefix [topology=han_carlson] [outside slot domain]   # p.1, p.3
parameters: 32-bit, 64-bit, and 128-bit operands; one cycle without misprediction; two cycles after misprediction; K is a power of two, but the printed tested/optimal K values are unreadable in the supplied table and equation text   # p.1, p.3, p.6
results:
| metric | value | unit | technology / device | baseline | condition | page |
| minimum achievable average delay | 225 | ps | UMC 65 nm (2015) | non-speculative Han-Carlson: about 280 ps | 64-bit | p.6 |
| area crossover average delay | <385 | ps | UMC 65 nm (2015) | non-speculative Han-Carlson | 64-bit | p.7 |
| area reduction | 20 | % | UMC 65 nm (2015) | non-speculative Han-Carlson | 64-bit; timing point UNKNOWN | p.7 |
| power reduction | 9 | % | UMC 65 nm (2015) | non-speculative Han-Carlson | 64-bit; timing point UNKNOWN | p.7 |
| minimum-delay improvement | 18 | % | UMC 65 nm (2015) | non-speculative Kogge-Stone | 64-bit | p.9 |
| minimum-delay improvement | 11 | % | UMC 65 nm (2015) | speculative Kogge-Stone | 64-bit | p.9 |
| area reduction | 45 | % | UMC 65 nm (2015) | non-speculative Kogge-Stone | 64-bit; timing point UNKNOWN | p.9 |
| power saving | 35 | % | UMC 65 nm (2015) | non-speculative Kogge-Stone | 64-bit; timing point UNKNOWN | p.9 |
errors_and_checks: The precise detector implements a necessary-and-sufficient misprediction condition, while the coarse necessary-only detector can produce false-positive errors that increase average addition time (p.4). Monte Carlo error probabilities use uniformly distributed inputs, 1% relative error, and 99% confidence; precise detection lowers error probability relative to coarse detection, and Han-Carlson has lower error probability than Kogge-Stone (p.5–p.6). Detected failures are corrected to the exact sum in the next clock period (p.3, p.5).
conditions: The design wins when high speed or tight timing constraints are required (p.7, p.9). Non-speculative adders win when the speed constraint is relaxed because error-detection/correction overhead dominates (p.1, p.9). Error-rate evaluation assumes uniformly distributed input vectors (p.5).
evidence: §III and Figs. 3–5 (p.3–p.5); Tables I–II (p.6); Figs. 6–7 and synthesis discussion (p.6–p.9).

### parallel_prefix  (role: extends)
mechanism: The proposed carry tree retains the initial and final Brent-Kung rows of Han-Carlson and prunes rows only from its inner Kogge-Stone portion. Half of the Han-Carlson carries are derived from parent carries through an additional tree level, which reduces error probability. Han-Carlson checking nodes occur early enough that the error detector becomes the faster critical path despite Han-Carlson having more prefix levels than Kogge-Stone (p.2–p.4, p.6).
choices:
  topology: han_carlson (proposed); kogge_stone (comparison)   # p.1–p.4
new_choices:
  speculative_pruning: prune_final_inner_rows — final rows of the Kogge-Stone portion are removed while the outer Brent-Kung rows remain unchanged   # p.3
slots:
  none
parameters: 32-bit, 64-bit, and 128-bit synthesized adders; generated Verilog; UMC 65 nm library   # p.5–p.6
results: none
errors_and_checks: Han-Carlson requires half as many OR terms for its error signal as Kogge-Stone, and its simulated error probability is lower (p.4, p.6).
conditions: Han-Carlson reduces cells/wiring relative to Kogge-Stone while retaining similar speed, but detector/correction fanout can slow checking and speculative-prefix cells (p.1, p.5).
evidence: Fig. 1 (p.2); Figs. 2–5 and equations (12)–(33) (p.3–p.5); Tables I–II (p.6); Fig. 7 (p.8–p.9).

## new_families
none

## space_gaps
* The speculative_variable_latency.base_adder slot should admit parallel_prefix because the proposed base architecture is a Han-Carlson parallel-prefix tree (p.1, p.3).
* speculative_variable_latency lacks a choice distinguishing necessary-and-sufficient precise detection from necessary-only coarse detection, which changes false-positive probability and average latency (p.4, p.6).
* parallel_prefix lacks a speculative-pruning choice that identifies which topology rows are removed and retained (p.3).

## open_questions
* Table I and Table II numerical entries are not recoverable from the supplied text, so their spatial/timing-complexity and error-probability values remain UNKNOWN.
* The tested and optimal K values are missing where mathematical symbols were dropped from the supplied text, so speculation_window remains UNKNOWN.
* The timing points associated with the 20%/9% and 45%/35% synthesis improvements are missing from the supplied text and must not be inferred.
