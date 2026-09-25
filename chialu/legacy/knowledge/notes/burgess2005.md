---
handle: burgess2005
citation: N. Burgess, "Prenormalization Rounding in IEEE Floating-Point Operations Using a Flagged Prefix Adder", IEEE Transactions on VLSI Systems, 2005.
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [ieee754_binary_normalized, fp64]
authority: incremental
pages_read: 12 / 12
---

## summary
The paper merges IEEE 754 rounding with carry-propagate assimilation through one flagged prefix adder and small rounding logic (pp.266–270). The architecture covers floating-point addition/subtraction, multiplication, and SRT division in all IEEE rounding modes (pp.270–276).

## families
### compound_flagged_prefix  (role: extends)
mechanism: A parallel-prefix adder exposes a group-propagate flag with each sum bit. Two late invert-enable signals selectively invert flagged bits or all bits, which derives incremented sums and absolute differences from one addition or subtraction without a second carry-propagate addition (pp.267–268).
choices:
  outputs: sum_sum1_summinus1   # p.267
  implementation: flag_row   # pp.267–268
  late_carry_in: true   # pp.267–268
new_choices:
  none
slots:
  none
parameters: n-bit adder; any logarithmic-depth prefix tree; two invert-enable signals   # pp.267–268
results:
| metric | value | unit | technology / device | baseline | condition | page |
| added prefix-tree logic | 1 | 2-input AND gate per bit | UNKNOWN; 2005 | conventional parallel-prefix adder | all grey cells become black cells | p.267 |
| added output logic | 1 AND–OR complex gate + 1 XOR gate | gates per bit | UNKNOWN; 2005 | conventional parallel-prefix adder | both invert enables supported | p.268 |
errors_and_checks: The adder supports exact increment/negation transformations; no fault-detection mechanism is reported.   # pp.267–268
conditions: Ladner–Fischer, Kogge–Stone, Brent–Kung, or another logarithmic-depth prefix tree can be used (p.267). Supporting only one invert enable reduces the logic slightly (p.268).
evidence: §II; Tables I–II; Figs. 1–5; pp.266–268

### round_fused_in_reduction  (role: proposes)
mechanism: The multiplier’s redundant product first passes through half adders. A 53-bit flagged prefix adder assimilates the most-significant product bits, while a seven-gate rounding block and modified full adders inject 1-ulp/2-ulp adjustments through the late-carry input before a one-bit normalization right shift (pp.270–272).
choices:
new_choices:
  rounding_architecture: flagged_prefix_late_carry — one assimilating prefix adder performs the late rounding increment instead of selecting duplicated speculative sums   # p.272
slots:
  none
parameters: 53-bit flagged prefix adder; 52 most-significant result bits; one-bit normalization right shift; two pipeline stages for assimilation/rounding   # pp.270–272
results:
| metric | value | unit | technology / device | baseline | condition | page |
| rounding-logic size | 7 | CMOS complex gates | UNKNOWN; 2005 | none | multiplication rounding block | p.271 |
| critical-path delay | 11 AOI + 9 inverter + 1 XOR | gate delays | UNKNOWN; 2005 | none | includes conditional one-bit normalization shift | p.272 |
| assimilation/rounding latency | 2 | pipeline stages | UNKNOWN; 2005 | none | partial-product formation/reduction completed earlier | p.272 |
| complete multiplier latency | 4 | cycles | UNKNOWN; 2005 | none | two cycles for partial products/reduction and fourth-cycle writeback time | p.272 |
| critical-path difference | +2 | AOI delays | UNKNOWN; 2005 | Seidel–Even duplicated compound-adder scheme | proposed nonduplicated scheme | p.272 |
errors_and_checks: The architecture implements all IEEE rounding modes for normalized products (pp.270–271); no error or fault checker is reported.
conditions: The unrounded product lies in [1,4), and normalization requires at most a one-bit right shift (p.270). The two-stage organization assumes partial-product formation/reduction occurs in preceding stages (p.272).
evidence: §IV; §V; Table V; Figs. 8–11; pp.269–272

### single_path  (role: instantiates)
mechanism: A single add/subtract path combines operand assimilation and rounding in a flagged prefix adder. A two-bit adder handles subtraction complementation near the least-significant bits, the late-carry input performs rounding increments, and the all-bit inversion input derives an absolute difference after a negative true subtraction (pp.272–274).
choices:
  pipeline_depth: 4   # p.274
  post_round_renorm: true   # pp.273–274
new_choices:
  none
slots:
  sig_adder: compound_flagged_prefix [late_carry_in=true]   # pp.273–274
  round: flagged_prefix   # pp.273–274
parameters: one alignment stage; two ADD/ROUND stages; one normalization stage; full-wordlength post-add normalization shifter   # p.274
results:
| metric | value | unit | technology / device | baseline | condition | page |
| ADD/ROUND latency | 2 | pipeline stages | UNKNOWN; 2005 | none | alignment and normalization excluded | p.274 |
| complete addition latency | 4 | pipeline stages | UNKNOWN; 2005 | none | alignment precedes and normalization follows ADD/ROUND | p.274 |
errors_and_checks: The path implements IEEE rounding for true addition and subtraction, including exact absolute difference for a negative result (pp.273–274); no fault checker is reported.
conditions: A true subtraction can require a large normalization left shift, so normalization follows ADD/ROUND (pp.272–274). The total ADD/ROUND delay is too large for one contemporary pipeline stage (p.274).
evidence: §VI-A–B; Tables VI–VII; Fig. 12; pp.272–274

### two_path  (role: extends)
mechanism: The far path handles true additions and true subtractions with alignment shifts of at least two places. The near path handles true subtractions with zero- or one-place alignment and predicts normalization distance in parallel with its flagged-prefix ADD/ROUND stage (pp.274–275).
choices:
  path_threshold: 2   # p.274
  close_path_trigger: exp_diff_and_effective_sub   # p.274
new_choices:
  none
slots:
  sig_adder: compound_flagged_prefix [late_carry_in=true]   # pp.274–275
  round: flagged_prefix   # pp.274–275
  near_lz: lza   # p.274
parameters: two paths; near-path alignment shift 0 or 1; far-path alignment shift 2 or more; three-cycle total latency   # pp.274–275
results:
| metric | value | unit | technology / device | baseline | condition | page |
| total addition latency | 3 | cycles | UNKNOWN; 2005 | four-stage combined path | one shifter removed from each critical path | p.275 |
| near-path rounding logic | 3 | CMOS complex gates | UNKNOWN; 2005 | combined single-path rounding block | true subtraction only | p.274 |
errors_and_checks: Both paths provide IEEE rounding for normalized operands (pp.274–275); no error or fault checker is reported.
conditions: Each operation requires either a large alignment shift or a large normalization shift, but not both (p.274). A final multiplexer selects the near- or far-path result (p.275).
evidence: §VI-C; Table VIII; Figs. 13–14; pp.274–275

### sig_div_then_round  (role: extends)
mechanism: Signed-digit SRT quotient components pass through half subtracters and a flagged prefix adder. The rounding block incorporates quotient complementation and signed round/sticky information, so its nonnegative adjustment spans 0.5, 1, 1.5, or 2 ulps before an optional one-bit normalization left shift (pp.275–276).
choices:
new_choices:
  signed_round_information: signed_round_and_sticky_digits — positive/negative round and sticky polarities determine increment or decrement cases before complementation   # pp.275–276
slots:
  round: flagged_prefix   # pp.275–276
parameters: SRT radix UNKNOWN; signed-digit quotient and remainder; unrounded quotient in [1,2); adjustment range 0.5–2 ulps; normalization left shift at most one place   # pp.275–276
results:
| metric | value | unit | technology / device | baseline | condition | page |
| rounding-logic size | 18 | gates | UNKNOWN; 2005 | none | SRT division rounding block | p.276 |
errors_and_checks: The architecture produces correctly rounded prenormalized quotients for all IEEE rounding modes (pp.275–276); no fault checker is reported.
conditions: The quotient/remainder must be available in signed-digit representation (p.275). SRT square root always requires the left shift, but its nonredundant root estimate/decrement removes the need for this flagged adder (p.276).
evidence: §VII; Table IX; Figs. 15–16; pp.275–276

## new_families
none

## space_gaps
* `flagged_prefix` appears as a rounding-slot value but has no declared family; the document specifies its group-propagate flags, two inversion enables, and late-carry behavior (pp.267–268).
* `round_fused_in_reduction` lacks a choice distinguishing one-adder late-carry rounding from duplicated compound-adder/select rounding (p.272).
* `sig_div_then_round` lacks choices for signed round/sticky representation and prenormalization adjustment range (pp.275–276).

## open_questions
* The exact prefix topology remains unspecified because the paper permits any logarithmic-depth topology (p.267).
* The architecture is format-independent, but the detailed multiplier path uses 53 bits; Fig. 6’s caption/prose also disagree about whether the illustrated layout is single or double precision (pp.268–270).
* Technology, area, power, clock frequency, and fabricated-silicon measurements are not reported.
