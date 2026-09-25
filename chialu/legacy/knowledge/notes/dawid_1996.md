---
handle: dawid_1996
citation: H. Dawid, H. Meyr, "The Differential CORDIC Algorithm: Constant Scale Factor Redundant Implementation without Correcting Iterations", IEEE Transactions on Computers, vol. 45, no. 3, pp. 307-318, 1996
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_SFU]
formats: [radix2_bsd, radix2_carry_save]
authority: incremental
pages_read: 307-318 / 12
---

## summary
The document proposes Differential CORDIC (DCORDIC), which transforms rotation/vectoring recurrences into additions/subtractions and absolute-value computations suitable for MSD-first redundant arithmetic. DCORDIC retains the conventional CORDIC accuracy/constant scale factor without correcting or branching iterations and is realized as parallel pipelined radix-2 architectures.

## families
### redundant_high_radix_cordic  (role: proposes)
mechanism: DCORDIC differentially encodes the signs of the conventional CORDIC variables and recursively decodes each steering sign. The rotation recurrence computes |pᵢ₊₁| = ||pᵢ| − αᵢ|, while the vectoring recurrence computes |yᵢ₊₁| = ||yᵢ| − |xᵢ|2⁻ⁱ|. MSD-first absolute-value computation permits radix-2 binary signed-digit or carry-save implementation. The dependent variables use pipelined 3-2/4-2 additions or steered additions/subtractions, so every conventional microrotation is retained and the scale factor remains constant without correcting/branching iterations.
choices:
  residual_arithmetic: [signed_digit, carry_save]   # p.310
  radix: 2   # p.308
  scale_handling: differential_constant_scale [outside domain]   # p.307
new_choices:
  mode: both — separate parallel architectures implement rotation and vectoring modes   # pp.309-313
slots:
  none
parameters: N+1 microrotations for N-bit inputs; BSD absolute-value on-line delay δ = 0; rotation iteration delay Iᵣ = 2.5 GFA delays; vectoring iteration delay Iᵥ = 3 GFA delays; rotation sign delay Sₚ = Nₚ + 1 cycles; vectoring sign delay Sᵧ = Nxy + 2 cycles; generated wordlength/stage count/pipelining/angle coding/internal number system are parameterized   # pp.308, 310, 312-314
results:
| metric | value | unit | technology / device | baseline | condition | page |
| throughput | 62.5 | MHz | European Silicon Structures (ES2) 1.0 μ CMOS standard cell; year UNKNOWN | none | carry save, 12 bit, rotation mode, max conditions including wire-load estimates | p.314 |
| area | 6.9 | mm² | European Silicon Structures (ES2) 1.0 μ CMOS standard cell; year UNKNOWN | none | carry save, 12 bit, rotation mode, max conditions including wire-load estimates | p.314 |
| throughput | 62.5 | MHz | European Silicon Structures (ES2) 1.0 μ CMOS standard cell; year UNKNOWN | none | carry save, 16 bit, rotation mode, max conditions including wire-load estimates | p.314 |
| area | 11.7 | mm² | European Silicon Structures (ES2) 1.0 μ CMOS standard cell; year UNKNOWN | none | carry save, 16 bit, rotation mode, max conditions including wire-load estimates | p.314 |
| total delay | 3.5·N + 1 | GFA delays | UNKNOWN; year UNKNOWN | double iteration and correcting iteration: 3.75·N GFA delays | rotation mode; number conversion and scale correction excluded | p.316 |
| combinational area | N | iterations | UNKNOWN; year UNKNOWN | double iteration and correcting iteration: 1.5·N iterations | rotation mode stage-count estimate | p.316 |
| latches | 7.75·N² | latches | UNKNOWN; year UNKNOWN | double iteration and correcting iteration: 9·N² latches | rotation mode; Nxy = Np = N approximation | p.316 |
| total delay | 4·N + log₂N + 5 | GFA delays | UNKNOWN; year UNKNOWN | prior vectoring method: 5.25·N GFA delays | vectoring mode; number conversion and scale correction excluded | p.316 |
| combinational area | N | iterations | UNKNOWN; year UNKNOWN | prior vectoring method: 1.5·N iterations | vectoring mode stage-count estimate | p.316 |
| latches | 9.5·N² + N³/6 | latches | UNKNOWN; year UNKNOWN | prior vectoring method: 9·N² latches | vectoring mode; Nxy = Np = N approximation | p.316 |
errors_and_checks: DCORDIC has the same accuracy/convergence and numeric properties as conventional CORDIC. With round-to-nearest, log₂N LSD guard digits are sufficient, with one additional digit for radix-2 redundant representation; the stated internal widths are Nxy = 2 + N + log₂N and usually Np = N. No fault-detection mechanism is reported.   # pp.311, 316
conditions: Digit-local pseudo-overflow correction requires the usable range of a W-digit redundant number to be limited to (−2^(W−1), 2^(W−1)). BSD is preferred because carry-save absolute-value negation requires a deferred +2 correction and more complex architectures. DCORDIC has the same achievable throughput as compared redundant methods but generally consumes more latches. A combined rotation/vectoring implementation is not straightforward because the two architectures differ. The transformations also apply to hyperbolic/linear CORDIC modes and sign-directed shift-and-add algorithms.   # pp.310-311, 314-316
evidence: Theorems 1-2 and algorithms in §3, BSD/CS implementation analysis in §4, Figs. 1-3, Table 1, and Table 2.

## new_families
none

## space_gaps
* `redundant_high_radix_cordic.scale_handling` lacks a value for differential reformulation that preserves a constant scale factor without correcting/branching iterations.   # pp.307, 316
* `redundant_high_radix_cordic` lacks a `mode` choice even though rotation/vectoring modes use different steering variables, delays, and architectures.   # pp.309-313

## open_questions
* Table 1 does not state the year in which the synthesis results were produced.
* Table 1 reports only rotation-mode implementations, so no synthesized vectoring-mode area/throughput is established.
* The document leaves the choice between fixed-coefficient multiplication and additional rotations for final scale-factor correction to the designer.   # p.312
