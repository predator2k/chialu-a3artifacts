---
handle: seidel_2001
citation: P.-M. Seidel and G. Even, "On the Design of Fast IEEE Floating-Point Adders", 15th IEEE Symposium on Computer Arithmetic, 2001
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [fp64]
authority: landmark
pages_read: 11 / 11
---

## summary
The document proposes a normalized double-precision IEEE floating-point adder with a nonstandard two-path split, unified injection-based rounding, one’s-complement subtraction, compound addition, and borrow-save leading-zero approximation (p.184). The design supports all four IEEE rounding modes and produces correctly normalized/rounded sums and differences (p.184). The analyzed latency is 24 logic levels in two balanced pipeline stages, with an optional 23-level variant (pp.190-191).

## families
### delay_optimized_unified  (role: proposes)
mechanism: The R-path handles effective additions, exponent differences with magnitude at least 2, and effective subtractions whose pre-shifted significand result is at least 2. The N-path handles the remaining effective subtractions, uses at most a one-bit alignment shift, performs no rounding, and normalizes an exact significand difference. One’s-complement subtraction, unconditional pre-shifts, injection rounding, a compound prefix adder, borrow-save leading-zero approximation, and precomputed post-normalization balance the two pipeline stages (pp.186-190).
choices:
  path_separation: nonstandard_unified_rounding   # p.186
  subtraction_style: ones_complement [outside domain]   # p.187
  lz_count_source: approximate_borrow_save   # p.188
new_choices:
  path_selection_criterion: IS-R = S.EFF OR |δ| >= 2 OR fpsum in [2,4) — selects the R-path using operation type, exponent difference, and significand range   # pp.186,190
  result_binades_for_rounding: 2 — bounds R-path rounding/post-normalization to significands in [1,4)   # pp.186,188
slots:
  sig_adder: compound_flagged_prefix [outputs=sum_sum1]   # pp.187-190
  round: injection   # p.187
  exp: exponent_path   # pp.186,189
  far_align: full_align   # pp.186,189
  near_lz: lza   # pp.188-190
parameters: normalized fp64 inputs/outputs; 53-bit significands; 11-bit exponent strings; two paths; 2 pipeline stages; 12 logic levels per stage; all four IEEE rounding modes   # pp.184-185,190
results:
| metric | value | unit | technology / device | baseline | condition | page |
| latency | 24 | logic levels | UNKNOWN; 2001 | none | normalized fp64; latch delays excluded | p.190 |
| pipeline-stage latency | 12 | logic levels each | UNKNOWN; 2001 | none | 2 balanced stages | p.190 |
| N-path latency | 21 | logic levels | UNKNOWN; 2001 | none | N-path is not timing-critical | p.190 |
| optimized latency | 23 | logic levels | UNKNOWN; 2001 | 24-level proposed design | duplicate alignment shifters; more than a 53-bit shifter added | p.191 |
| adapted AMD-design latency | 26 | logic levels | UNKNOWN; 2001 | AMD patent implementation | extended to fp64 and all four IEEE rounding modes | p.193 |
| adapted SUN-design latency | 28 | logic levels | UNKNOWN; 2001 | SUN patent implementation | restricted to normalized fp64 and all four IEEE rounding modes | p.194 |
| latency reduction | at least 2 | logic levels | UNKNOWN; 2001 | adapted AMD/SUN designs | technology-independent delay analysis | p.194 |
errors_and_checks: The output contract is correctly normalized IEEE rounding under all four rounding modes for normalized inputs (p.184). A parameterized reduced-precision version passed exhaustive comparison against a naive algorithm without errors, but the tested exponent/significand widths are not stated (pp.185,191).
conditions: The presented datapath accepts normalized inputs; denormal input/output support is delegated to cited extensions (p.184). The delay counts exclude latch delays (p.184). The N-path applies only to effective subtraction with |δ| < 2 and a pre-shifted significand difference below 2, so the N-path requires no rounding (pp.186,189). The optional 23-level result requires duplicated alignment-shifter hardware (p.191).
evidence: Abstract and §1 (pp.184-185); §§4.1-4.7 (pp.186-188); Figures 1-4 and §5 (pp.188-190); §6 (pp.190-191); §7 (p.191); Table 1 and §§8.1-8.2 (pp.191-194).

### compound_flagged_prefix  (role: instantiates)
mechanism: One parallel-prefix network computes carry-generate/carry-propagate strings and bitwise operand XORs. The ordinary sum uses Gen-C[i], while the incremented sum replaces that carry with OR(Gen-C[i], Prop-C[i]). The N-path partitions this computation across pipeline stages by passing the sum, operand XOR, and combined generate/propagate string across the boundary, leaving one XOR line for the incremented result (pp.187-188).
choices:
  outputs: sum_sum1   # p.187
  implementation: shared_generate_propagate_strings [outside domain]   # pp.187-188
new_choices:
  pipeline_partition: prefix_state_then_xor — passes prefix state across the stage boundary and completes the incremented sum with one XOR line   # pp.187-188
slots:
  none
parameters: two instances; 53-bit fp64 significand path; one instance partitioned across the two pipeline stages   # pp.187-188
results:
| metric | value | unit | technology / device | baseline | condition | page |
| post-prefix sum/sum+1 completion | 2 | logic levels | UNKNOWN; 2001 | none | Gen-C, Prop-C, and operand XOR strings already available | p.187 |
errors_and_checks: none
conditions: The R-path rounding decision selects between the sum and incremented sum (p.187). The N-path partition is required to preserve the 12-logic-level first-stage boundary (pp.187,190).
evidence: §4.5 (pp.187-188) and §6 (p.190).

## new_families
none

## space_gaps
* `delay_optimized_unified.subtraction_style` needs a value for one’s-complement subtraction with pre-shift/missing-ulp compensation rather than end-around carry (p.187).
* `two_path.close_path_trigger` lacks the document’s combined effective-subtraction/exponent-difference/significand-range predicate (p.186).
* `compound_flagged_prefix.implementation` lacks the shared carry-generate/carry-propagate-string implementation used for sum and sum+1 (pp.187-188).

## open_questions
* The document does not identify the topology or fanout of the parallel-prefix network.
* The document does not state the exponent/significand widths used for exhaustive reduced-precision verification.
* The 23-logic-level duplicate-shifter variant is analyzed, but the document does not report a physical implementation.
