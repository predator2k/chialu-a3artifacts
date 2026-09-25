---
handle: verma2008
citation: A. K. Verma, P. Brisk, P. Ienne, "Variable Latency Speculative Addition: A New Paradigm for Arithmetic Circuit Design", Design, Automation and Test in Europe (DATE), 2008
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [binary_integer]
authority: landmark
pages_read: 6 / 6
---

## summary
The paper proposes an Almost Correct Adder (ACA) that limits carry computation to short sliding windows and deterministically fails only when a longer propagate sequence occurs. The Variable Latency Speculative Adder (VLSA) detects those failures and produces an exact result after a recovery cycle. Synthesized 64–2048-bit designs use a UMC 0.18µm CMOS standard-cell library. (pp.1250–1255)

## families
### segmented_carry_speculative  (role: proposes)
mechanism: The ACA assumes that no carry propagates more than a window parameter k. Each carry uses only the product of k consecutive propagate/generate matrices, and recursive doubling shares products for overlapping windows. The network requires O(n log k) matrix multiplications, O(n log log n) space for k=O(log n), and bounded fanout. A longer propagate chain can make the deterministic sum incorrect. (pp.1251–1253)
choices:
  sub_adder_width: 6/24 [outside domain]   # pp.1251–1252
  correction: none   # p.1253
new_choices:
  window_placement: per_bit_sliding — a truncated carry window is formed for each output position   # pp.1251–1253
  window_product_sharing: recursive_doubling — overlapping windows reuse products of 2, 4, 8, ... consecutive matrices   # p.1253
slots:
  sub_adder: UNKNOWN   # p.1253
parameters: n=20 with 6-bit local adders; n=16 and k=6 in the shared-logic example; n=1024 with 24-bit local adders; synthesized widths 64/128/256/512/1024/2048 bits at the 99.99% target.   # pp.1251–1255
results:
| metric | value | unit | technology / device | baseline | condition | page |
| ACA speedup | 1.5–2.5 | × | UMC 0.18µm CMOS; 2008 | DesignWare fast adder | 64–2048-bit synthesized designs, 99.99% accuracy target | p.1255 |
| ACA area | 25 | % smaller | UMC 0.18µm CMOS; 2008 | DesignWare fast adder | 64–2048-bit synthesized designs | p.1255 |
| longest run bound at 99% probability | 11 | bits | UNKNOWN; 2008 | none | n=64 independent unbiased bits | p.1252 |
| longest run bound at 99% probability | 12 | bits | UNKNOWN; 2008 | none | n=128 independent unbiased bits | p.1252 |
| longest run bound at 99% probability | 13 | bits | UNKNOWN; 2008 | none | n=256 independent unbiased bits | p.1252 |
| longest run bound at 99% probability | 14 | bits | UNKNOWN; 2008 | none | n=512 independent unbiased bits | p.1252 |
| longest run bound at 99% probability | 15 | bits | UNKNOWN; 2008 | none | n=1024 independent unbiased bits | p.1252 |
| longest run bound at 99% probability | 16 | bits | UNKNOWN; 2008 | none | n=2048 independent unbiased bits | p.1252 |
| longest run bound at 99.99% probability | 17 | bits | UNKNOWN; 2008 | none | n=64 independent unbiased bits | p.1252 |
| longest run bound at 99.99% probability | 18 | bits | UNKNOWN; 2008 | none | n=128 independent unbiased bits | p.1252 |
| longest run bound at 99.99% probability | 20 | bits | UNKNOWN; 2008 | none | n=256 independent unbiased bits | p.1252 |
| longest run bound at 99.99% probability | 21 | bits | UNKNOWN; 2008 | none | n=512 independent unbiased bits | p.1252 |
| longest run bound at 99.99% probability | 22 | bits | UNKNOWN; 2008 | none | n=1024 independent unbiased bits | p.1252 |
| longest run bound at 99.99% probability | 23 | bits | UNKNOWN; 2008 | none | n=2048 independent unbiased bits | p.1252 |
errors_and_checks: The ACA error is deterministic for an input and occurs when the addenda contain a propagate chain longer than the implemented window. The stated probabilities assume random independent unbiased input bits; no application-trace error rate is reported.   # pp.1252–1253
conditions: The ACA alone applies when occasional incorrect additions do not change the application outcome. The paper gives ciphertext-only frequency attacks as an example. The accuracy analysis assumes uniformly distributed A XOR B.   # pp.1250–1252
evidence: §3, Table 1, Figures 1/3/4, §5, Figure 8, pp.1251–1255

### speculative_variable_latency  (role: proposes)
mechanism: The VLSA runs the ACA and an error detector in parallel. The detector ORs the products of every length-(k+1) propagate chain. A no-error result is valid after one cycle; an error stalls new input while a recovery network produces the corrected sum after two cycles. (pp.1253–1254)
choices:
  detection: propagate_run_detector   # pp.1253–1254
  recovery: extra_cycle_correction   # p.1254
new_choices:
  none
slots:
  base_adder: segmented_carry_speculative [correction=none]   # p.1254
parameters: one-cycle normal latency; two-cycle error latency; VALID/STALL handshake; TCLK > max(TSUM*, TERROR); TSUM < 2TCLK; reported average latency 1.0001 cycles when the ACA is correct in more than 99.99% of cases.   # p.1254
results:
| metric | value | unit | technology / device | baseline | condition | page |
| error-detector critical-path delay | approximately 2/3 | of baseline delay | UMC 0.18µm CMOS; 2008 | DesignWare fast adder | 64–2048-bit synthesized designs | p.1255 |
| average VLSA latency | 1.0001 | cycles | UNKNOWN; 2008 | one-cycle ACA result | ACA correct in more than 99.99% of cases | p.1254 |
| average VLSA speedup | 1.5 | × | UMC 0.18µm CMOS; 2008 | DesignWare fast adder | ACA, error detection, and error recovery combined | p.1255 |
errors_and_checks: The detector is specified to flag an incorrect ACA sum by detecting any all-propagate chain of length k+1. Recovery makes the final VLSA result exact. Detection coverage/false-alarm rates are not separately quantified.   # pp.1253–1254
conditions: A pipelined implementation gains average latency because errors are rare. A purely combinational implementation has virtually no advantage because the recovery critical path is comparable to a traditional fast adder.   # p.1254
evidence: §4.1–§4.3, Figures 5–7, §5, Figure 8, pp.1253–1255

### carry_lookahead  (role: instantiates)
mechanism: Error recovery reuses the ACA’s propagate/generate values for k-bit blocks. An n/k-bit carry look-ahead adder computes the block carries, which combine with per-bit propagate/generate values to form the corrected sum. (pp.1253–1254)
choices:
  none
new_choices:
  none
slots:
  none
parameters: n/k block inputs; group size k is inherited from the ACA and is not claimed to be optimal for recovery.   # pp.1253–1254
results: none
errors_and_checks: none
conditions: Recovery may be slower than a traditional adder because k is not guaranteed to be the optimal CLA group size. The measured ACA-plus-recovery delay is approximately the same as the traditional adder.   # pp.1254–1255
evidence: §4.2, Figure 5, pp.1253–1255

## new_families
none

## space_gaps
* `segmented_carry_speculative.sub_adder_width` ends at 16, while the paper explicitly uses 24-bit local adders for the 1024-bit 99.99% case.   # p.1252
* `speculative_variable_latency.base_adder` does not admit `segmented_carry_speculative`, although the VLSA explicitly uses the ACA as its base adder.   # p.1254
* `speculative_variable_latency` lacks a recovery-adder slot for the n/k-bit `carry_lookahead` network.   # pp.1253–1254

## open_questions
* The exact relation among k, the longest propagate-run bound, and local-adder width is ambiguous: Figure 1 maps a longest run of 4 to 6-bit adders, while later equations use products of k matrices and detect chains of length k+1.   # pp.1251–1253
* Figure 8 does not print exact per-width delay or normalized-area coordinates, so only the textual aggregate comparisons can be recorded.   # p.1255
* The paper does not measure error probability on application workloads, so the random-independent-input probabilities must not be generalized.   # pp.1252–1255
