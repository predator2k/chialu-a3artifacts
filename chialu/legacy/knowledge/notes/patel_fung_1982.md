---
handle: patel_fung_1982
citation: J. H. Patel, L. Y. Fung, "Concurrent Error Detection in ALU's by Recomputing with Shifted Operands", IEEE Transactions on Computers, vol. C-31, pp. 589-595, 1982
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [unsigned_binary, ones_complement, twos_complement, floating_point]
authority: landmark
pages_read: 589-595 / 7
---

## summary
Recomputing with Shifted Operands (RESO) detects ALU errors by running an operation twice, shifting the operands before recomputation, aligning the two results, and testing equality (pp.590-591). The paper proves coverage for localized failures in bitwise logic/ripple-carry/full and group carry-lookahead adders and discusses extensions to correction/multiplication/division/floating-point operations (pp.591-595).

## families
### time_redundancy  (role: proposes)
mechanism: RESO first computes f(x), stores the result, and then recomputes with operands shifted left by k bits. The recomputed result is shifted right before comparison, or the first result is shifted left before storage so the recomputed result can be compared directly. An n-bit arithmetic operation uses an (n+k)-bit ALU to preserve shifted bits. Carry-in and sign/zero extension are adjusted so the shifted computation represents multiplication by 2^k. A mismatch signals an error (pp.590-591).
choices:
  transform: shift; rotation [outside domain] for bitwise logical operations   # pp.590, 594
  iterations: 2 for detection; 3 for correction of bitwise logical operations   # pp.590, 594-595
  shift_distance: 1 for RESO-1, 2 for RESO-2, and generalized k [outside domain] for RESO-k   # pp.591, 593-594
  correction: true for bitwise logical operations using a third computation and bitwise majority voting; generally unavailable for arithmetic operations   # pp.594-595
new_choices:
  comparison_alignment: {right_shift_recomputed_result, left_shift_stored_result} — selects the Fig. 4(a) or Fig. 4(b) comparison organization   # pp.590-591
  protected_fault_region: {subnetwork, bit_slice, adjacent_bit_slices, lookahead_group} — identifies the localized functional-fault region covered by a theorem   # pp.591-594
slots:
  comparator: UNKNOWN   # p.591
parameters: n-bit protected operations use k-bit operand shifts, an (n+k)-bit ALU, two shifters, one result register, and an equality checker; circular shifting permits an n-bit ALU for bitwise logical operations   # p.591
results:
| metric | value | unit | technology / device | baseline | condition | page |
| pipelined latency overhead | 1 | segment delay per ALU operation | UNKNOWN / 1982 | unchecked ALU operation | computation and recomputation overlap in a pipelined ALU | p.591 |
errors_and_checks: The functional fault model permits arbitrary logical effects from a physical failure confined to a small area or component cluster rather than assuming stuck-at behavior (pp.589, 593, 595). RESO-1 detects every error in bitwise logical operations for a failure confined to one bit-slice and detects arithmetic errors under the stated disjoint/shared sum-and-carry subnetwork structures (pp.591-592). RESO-2 detects every functional error from a failure confined to one bit-slice in ripple-carry and full carry-lookahead adders (pp.593-594). RESO-k detects all bitwise-operation errors for k faulty adjacent slices and all ripple/full carry-lookahead arithmetic errors for k-1 faulty adjacent slices; it also covers one group of a group carry-lookahead adder when the group contains k-1 bits (p.594). False-alarm behavior and an aggregate alias rate are not reported.
conditions: The coding transform must satisfy c^-1(f(c(x))) = f(x), and useful coverage depends on the circuit implementation as well as the transform (p.590). The transform is cost-effective when its coding/decoding hardware is much less complex than the protected function unit (p.590). Shift-based arithmetic protection requires k extra ALU bit-slices, whereas rotation avoids those slices for bitwise logic but requires extra control for arithmetic and becomes more complex for carry-lookahead adders (pp.591, 594). Multiplication/division coverage depends on the specific implementation and is not derived for a particular array (p.595). Floating-point protection treats the exponent and mantissa separately as integers with separate mechanisms (p.595).
evidence: Section II and Figs. 3-4 (p.590); Section III and Fig. 5 (pp.590-591); Theorems 1-4 and Figs. 6-8 (pp.591-592); Theorems 5-7, Fig. 9, and Table I (pp.593-594); Section VI (pp.594-595).

## new_families
none

## space_gaps
* `time_redundancy.transform` lacks `rotation`, which substitutes for shifting in bitwise logical operations without extra bit-slices (p.594).
* `time_redundancy` lacks a protected-unit slot for ripple-carry/carry-lookahead adders and regular multiply/divide arrays (pp.593-595).
* The comparator vocabulary lacks the totally self-checking equality checker based on 1-out-of-2 code checkers that the paper proposes for RESO support hardware (p.591).

## open_questions
* The paper does not quantify coverage for faults in the added register or for combined faults across the ALU/shifters/equality checker.
* The paper leaves multiplier/divider coverage dependent on the selected hardware implementation and fault model (p.595).
* The paper does not specify a technology node, operand width, clock frequency, area, or power result.
