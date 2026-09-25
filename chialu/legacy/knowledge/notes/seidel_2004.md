---
handle: seidel_2004
citation: P.-M. Seidel and G. Even, "Delay-Optimized Implementation of IEEE Floating-Point Addition", IEEE Transactions on Computers, 2004
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [fp64]
authority: incremental
pages_read: 97-113 / 17
---

## summary
The document proposes a two-stage, two-path IEEE floating-point adder for normalized double-precision addition/subtraction with all four rounding modes. A nonstandard path-selection condition, injection-based rounding, one’s-complement subtraction, compound addition, and borrow-save leading-zero approximation produce an estimated latency of 30.6 FO4 delays. # p.97,p.108

## families
### delay_optimized_unified  (role: proposes)
mechanism: The R-path handles effective additions, exponent differences with |Δ| ≥ 2, and preshifted significand sums with magnitude at least 2; the N-path handles the remaining effective subtractions. The R-path performs alignment and compound sum/sum+1 rounding, while the N-path limits alignment to one bit, approximates leading zeros from a borrow-save difference, converts the result to sign-magnitude, and normalizes without rounding. Both paths span two balanced pipeline stages, and IS_R selects the result. # p.99,p.101-p.107
choices:
  path_separation: nonstandard_unified_rounding   # p.99
  subtraction_style: ones_complement_lazy_increment [outside domain]   # p.100,p.105
  lz_count_source: approximate_borrow_save   # p.100-p.101
new_choices:
  path_selection_predicate: effective addition or |Δ| ≥ 2 or preshifted fsum ∈ [2,4) — defines the R-path selection condition   # p.99,p.107
slots:
  sig_adder: compound_flagged_prefix [outputs=sum_sum1, implementation=flag_row]   # p.100,p.103
  round: injection   # p.99,p.105-p.107
  exp: exponent_path   # p.101-p.104
  far_align: full_align   # p.101-p.104
  norm: coarse_fine   # p.100-p.101,p.105
  near_lz: lza   # p.100-p.101
parameters: normalized fp64 operands; 53-bit significands; 11-bit exponents; addition/subtraction; four IEEE rounding modes reduced internally to RZ/RNU/RI; two paths; two pipeline stages; cycle time 15.3 FO4 delays   # p.97-p.98,p.108
results:
| metric | value | unit | technology / device | baseline | condition | page |
| latency | 30.6 | FO4 delays | technology-independent Logical Effort / 2004 | none | optimized gate sizing and driver insertion | p.108 |
| cycle time | 15.3 | FO4 delays | technology-independent Logical Effort / 2004 | none | slowest stage | p.108 |
| R-path first-stage delay | 15.3 | FO4 delays | technology-independent Logical Effort / 2004 | none | optimized implementation | p.108 |
| R-path second-stage delay | 15.3 | FO4 delays | technology-independent Logical Effort / 2004 | none | optimized implementation | p.108 |
| N-path first-stage delay | 15.3 | FO4 delays | technology-independent Logical Effort / 2004 | none | optimized implementation | p.108 |
| N-path second-stage delay | 14.8 | FO4 delays | technology-independent Logical Effort / 2004 | none | optimized implementation | p.108 |
| latency change | -13 | percent | technology-independent Logical Effort / 2004 | adopted AMD design, 35.2 FO4 delays | optimized implementations | p.112 |
| cycle-time change | -22 | percent | technology-independent Logical Effort / 2004 | adopted AMD design, 19.7 FO4 delays | optimized implementations | p.112 |
errors_and_checks: The output is correctly normalized and rounded for all four IEEE rounding modes on normalized inputs. A reduced-precision instance passed exhaustive testing, and the fp64 algorithm passed all 2,872 translated test vectors; 84 percent of reduced-precision vectors translated successfully. # p.97,p.108
conditions: The design excludes denormal inputs/outputs; cited extensions add 1-2 logic levels for denormal support. # p.97 The estimates are technology-independent Logical Effort results rather than fabricated-silicon measurements. # p.107-p.108 Multiple precisions require prealignment of rounding positions and postalignment of results. # p.98
evidence: Sections 4-6; Figs. 1-3; Table 2; Sections 7 and 8.1, pp.99-112.

### compound_flagged_prefix  (role: instantiates)
mechanism: One parallel-prefix carry computation produces Gen_C/Prop_C and bitwise XOR strings. The ordinary sum uses Gen_C, while the incremented sum substitutes OR(Gen_C, Prop_C); the rounding decision selects between the two results. The N-path partitions this computation across pipeline stages so that only an XOR line for the incremented sum remains in the second stage. # p.100
choices:
  outputs: sum_sum1   # p.100
  implementation: flag_row   # p.100
new_choices: none
slots: none
parameters: two instances; one in the R-path second stage and one partitioned across the N-path stages   # p.100
results: none
errors_and_checks: none
conditions: The R-path timing analysis assumes that the sum MSB becomes valid one logic level before the slowest sum bit. # p.100
evidence: Section 4.5 and Figs. 1-3, pp.100-104.

### parallel_prefix  (role: instantiates)
mechanism: A parallel-prefix adder computes carry-generate/carry-propagate signals and bitwise addend XORs for the compound sum and incremented-sum outputs. The document does not identify the prefix topology. # p.97,p.100
choices:
new_choices: none
slots: none
parameters: operand width follows the fp64 significand datapath   # p.97,p.100
results: none
errors_and_checks: none
conditions: The prefix network is analyzed as part of the complete Logical Effort datapath rather than as a standalone adder. # p.107-p.109
evidence: Sections 4.5 and 6; Table 2, pp.100,107-109.

## new_families
### borrow_save_lza  (domain: shift: bit counting, closest: lzd_cell_tree, why_not: lzd_cell_tree does not cover approximate leading-zero counts from redundant borrow-save operands followed by postnormalization)
mechanism: P-recoding followed by N-recoding converts the borrow-save significand difference into a redundant string whose leading zero count places the shifted magnitude in [1,4). Bitwise XOR feeds separate priority encoders for positive and negative cases; the selected shift estimate performs coarse normalization, and a final one-bit postnormalization selects [1,2). # p.100-p.101,p.105,p.107
choices: reduction: {pn_recoding, propagate_kill_generate}; sign_handling: {dual_priority_encoders}; correction: {one_bit_postnormalization}
results:
| metric | value | unit | technology / device | baseline | condition | page |
| reduction delay | 3 | XOR-gate delays | technology-independent / 2004 | none | P-recoding, N-recoding, and bitwise XOR | p.101 |
| reduction cost | 3 XOR-gates and two AND-gates | gates per bit | technology-independent / 2004 | none | implemented PN-recoding method | p.101 |
evidence: Section 4.6, Fig. 3, and Sections 5.2.3/5.3.3, pp.100-101,104-107.

## space_gaps
* `subtraction_style` lacks the document’s one’s-complement subtraction with a deferred/lazy increment rather than end-around carry. # p.100,p.105
* `lza` is a permitted `near_lz` slot value but has no declared family or choices for borrow-save recoding, sign handling, or postnormalization. # p.100-p.101
* `path_separation` does not encode the exact IS_R predicate based jointly on effective operation, |Δ|, and preshifted significand magnitude. # p.99,p.107

## open_questions
* The parallel-prefix topology is not identified.
* The reduced-precision significand/exponent widths used for exhaustive testing are not reported. # p.108
* No CMOS process, voltage, area, power, or fabricated frequency is reported because the quantitative analysis uses Logical Effort. # p.107-p.108
