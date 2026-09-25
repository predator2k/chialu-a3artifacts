---
handle: lichtenau_2016
citation: C. Lichtenau, S. Carlough, S. M. Mueller, "Quad Precision Floating Point on the IBM z13", ARITH-23, 2016
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [fp128, fp64, fp32, hfp128, hfp64, hfp32, dfp128, dfp64, dfp32]
authority: landmark
pages_read: 87-94 / 8
---

## summary
The paper describes the Vector and Floating Point Unit (VFU) of the IBM z13, whose Decimal and Quad Precision Engine (DQE) executes binary and hexadecimal quad precision floating-point operations on the 140-bit mantissa dataflow of a decimal floating-point engine, with divide and square root in a separate SRT engine. The DQE is an 8-stage pipeline at 5 GHz in 22 nm that shares one two-stage shifter, one compound adder and one injection rounder across the binary, hexadecimal and decimal radices. The paper proves that homogeneous-precision binary add and subtract require either a wide normalization or a rounding but never both, so the normalizer and the rounding selection are built in parallel instead of in series.

## families
### single_path  (role: instantiates)
mechanism: One serial DQE pipeline carries every operand case: unpack and swap by exponent difference, a two-stage shifter that shifts up to 36 digits left or right and then 0 to 3 bits right, the Arithmetical Engine (AREN) holding a compound adder and a leading zero anticipator (LZA), a normalize-and-round stage whose normalizer circuit and rounding-select circuit run in parallel, and a pack stage. For binary addition only the mantissa with the smaller exponent is shifted, by the exponent difference. Effective subtraction inverts the second operand into the adder and the LZA, and the end-around carry (eac) selects between A-B and !(A+!B). Single and double precision operands are padded so that mantissa overflow after add and round is detected at one position for every precision and radix.
choices:
  operand_order: swap_before_shift   # p.88
  negation_handling: end_around_carry   # p.90
  subnormal_representation: as_stored   # p.92
new_choices:
  tail_path_split: parallel_normalizer_and_rounding_select — the post-adder stage builds the normalizer circuit and the rounding-selection circuit side by side and selects one of them, because an operation needs a wide normalization or a rounding but never both   # p.88, p.92
  shared_radix_datapath: binary_hexadecimal_decimal — one shifter, one adder and one rounder serve all three radices, the decimal 6-corrections suppressed for binary   # p.88, p.90
slots:
  sig_adder: compound_flagged_prefix [implementation=dual_carry_tree]   # p.90
  align: full_align   # p.88
  lz: lza   # p.89
  exp: exponent_path   # p.93
parameters: 8-stage fully pipelined DQE, a new operation started every cycle for all arithmetic operations but multiply, divide and binary/decimal converts; VFU pipeline 10 cycles deep, 2 of them operand bypass and result forwarding; shifter output 141b; mantissa dataflow 140b; binary QP mantissa 113b, hex QP 112b (28 digits), decimal QP 134b (34 digits); 5 GHz, 2-way simultaneous multi-threading   # p.87, p.88
results:
| metric | value | unit | technology / device | baseline | condition | page |
| Add/Sub latency | 11 | cycles | IBM 22 nm, 2016 | 35 cycles on zEC12 | quad precision, executed in the DQE | p.94 |
| Add/Sub throughput | 1.5 | CPI | IBM 22 nm, 2016 | 28 CPI on zEC12 | two DQEs in the processor | p.94 |
| VFU area | 3.9 | mm2 | IBM 22 nm, 2016 | UNKNOWN | total VFU including the vector and floating-point register files | p.94 |
| core frequency | 5 | GHz | IBM 22 nm, 2016 | UNKNOWN | VFU of the z13 | p.87 |
errors_and_checks: The exact sum or absolute difference is rounded once, at the first or the second rounding point. An IEEE overflow can only occur when the rounder is used, and an IEEE underflow only when the normalizer is used. The LZA count may be one too large, and the normalization shift is corrected by LZA2large, which is derived from the most significant bit of the normalizer output. IEEE exception flags and the DXC exception code are generated in the pack stage.   # p.89, p.92, p.93
conditions: The proof that add and subtract need a wide normalization or a rounding but not both is stated for homogeneous precision arithmetic (p.92). Decimal operands are aligned to the preferred quantum in the first pipeline stage, so no normalization occurs even under massive cancellation and a 1-digit shift suffices (p.91). For subtraction the operands are preshifted one bit left for binary and four bits left for decimal, so one shift-left-by-one shifter covers addition and subtraction (p.92). The reported motivation is 18% faster convergence on commercial products like ILOG and SPSS when double precision operations in critical routines are replaced by quad precision (p.87).
evidence: Sections II, II.A-II.E, III, IV; Figures 1, 3, 9; Table II.

### compound_flagged_prefix  (role: instantiates)
mechanism: The compound adder computes per digit. 4-bit adders produce the digit generate and propagate signals, which feed two regular binary carry trees, one with carry-in 0 and one with carry-in 1. The two carry vectors select the digits of H0 (sum), H1 (sum+1) and HC (inverted sum). HN, the mantissa handed to the normalizer, comes from H0 or H1 based on the eac and the effective operation, and HC is selected on the eac for an effective subtract with B > A. The adder spans 37 decimal digits or 119 binary mantissa bits including the round, guard and sticky positions.
choices:
  outputs: H0 (sum), H1 (sum+1), HC (inverted sum) [outside domain]   # p.89, p.90
  implementation: dual_carry_tree   # p.90
new_choices: none
slots: none
parameters: 37 decimal digits or 119 binary mantissa bits including round, guard and sticky; the multiplier's 226-bit carry and sum vectors assimilated first on the low part, then on the high part with the carry from the low part   # p.89
results: none
errors_and_checks: none
conditions: For an effective subtract with B > A neither decimal nor binary requires rounding, and the select logic takes HC on the eac (p.91).
evidence: Section III, Section III.A; Figures 3, 4.

### bcd_direct_addition  (role: extends)
mechanism: The same compound adder performs decimal addition on binary coded decimal digits. A 6 is added to each digit of the B operand before the addition, and the digit sums are post-corrected by -6 on an effective addition without carry-out or by +6 on an effective subtraction with carry-out. For binary operations the 6-corrections are suppressed, and the binary support is a separate drawn path in the adder figure. In the injection path, digits 0 to 33 use a regular 3-to-2 CSA that adds ai + bi + 6, and digit 34 takes a full addition of A and B with a potential 6 or 12 correction.
choices:
  digit_code: bcd8421   # p.88, p.90
  correction_placement: presum_plus6 on the B operand together with a postsum -6 or +6 correction [outside domain]   # p.90
  carry_scheme: full_lookahead   # p.90
new_choices: none
slots: none
parameters: decimal QP 134b (34 digits), DP 64b (16 digits), SP 28b (7 digits); densely packed decimal operands unpacked to binary coded decimal, and binary and hexadecimal mantissas aligned to the decimal data path   # p.88
results: none
errors_and_checks: none
conditions: Decimal numbers always use the rounding path because they were aligned to their target quantum in the shifter step (p.88). The decimal shift amount calculation also includes the leading zero count of the input operands, so it is more complicated than the binary one (p.88).
evidence: Sections II.A, III.A, III.B; Figures 4, 5.

### injection  (role: extends)
mechanism: Rounding is applied by injection into the adder, using a scheme similar to the binary one of Even and Seidel and extended to binary and decimal. The injection is applied at two rounding points in parallel to account for a potential mantissa overflow, the second rounding point injecting into digits 33 to 36. A 2-to-2 CSA compression of the operands A and B creates the hole for the injection term: one bit wide for binary, and 4 bits wide for decimal through a special decimal CSA block. The compound adder computes result and result plus one for digits 0 through 33 while the injection values for the first and second rounding points are added to digits 34 to 36, producing the injection carry-outs Cj and Ck.
choices: none
new_choices:
  rounding_points: 2 — the injection is applied at a first and a second rounding point in parallel, the second one used when digits 0 to 36 have a mantissa overflow   # p.88, p.90
  injection_hole_width: 1 bit for binary and 4 bits for decimal — the width freed by the CSA compression of A and B for the injection term   # p.90
  radix_shared_injection_values: precomputed_per_radix — different pre-computed injection values per radix, and a mapping of the binary round, guard and sticky bits onto digits 34 to 36 with padding, let one data path round both radices without adding delay on the critical path   # p.90, p.91
slots: none
parameters: rounded result selected from the compound adder carry-outs c0 and c1 and the injection carry-outs Cj and Ck, for all effective add cases and effective subtract cases with A > B; post rounding correction is a one digit (decimal) or one bit (binary) shift   # p.88, p.91
results: none
errors_and_checks: The paper proves that a second carry-out for RK is not possible on addition in homogeneous precision, in the eA = eB case (the result is exact, so no increment occurs) and in the eA > eB case (the unrounded result has at least one zero before the most significant bit, so the rounding carry stops there), which allows the addition and the injection rounding to be done in one step and still produce the correctly rounded result. It is also shown that rounding creates at most one additional digit (decimal) or bit (binary).   # p.91
conditions: For decimal, rounding only applies when B is shifted right, which implies A was fully normalized and B has at least one leading zero after alignment; for binary, B > A implies equal exponents, nothing was shifted into guard and sticky and no rounding is required (p.91).
evidence: Sections III.B, IV; Figures 5, 6, 7, 8; Table I.

### booth_recoded_parallel  (role: instantiates)
mechanism: The binary quad precision multiplier processes 18 bits of the multiplier mantissa in each cycle and generates 9 Booth-recoded partial products. The intermediate result is accumulated in redundant carry save format, retiring 18 bits of the sum and carry vectors per cycle. The AREN then adds the 226-bit wide carry and sum vectors, first on the low part and then on the high part while accounting for the carry from the low part. Multi-cycle operations such as quad precision multiply reuse the unit dataflow and loop in specific stages of the pipeline, to reduce the size of the multiplication hardware within the area and power budgets. The same compressor is reused by the decimal to binary convert.
choices:
  booth_radix: 4   # p.89 (18 multiplier bits per cycle yield 9 Booth-recoded partial products)
new_choices:
  multiplier_bits_per_cycle: 18 — the multiplier mantissa bits recoded, accumulated and retired per cycle when the partial-product hardware is reused across cycles instead of built at full width   # p.89
slots:
  reduction: csa_reduction_tree   # p.89
parameters: 9 Booth-recoded partial products per cycle; 226-bit sum and carry vectors; binary QP mantissa 113b; multiply cannot start a new operation every cycle   # p.88, p.89
results:
| metric | value | unit | technology / device | baseline | condition | page |
| Multiply latency | 23 | cycles | IBM 22 nm, 2016 | 55-97 cycles on zEC12 | quad precision, executed in the DQE | p.94 |
| Multiply throughput | 7.5 | CPI | IBM 22 nm, 2016 | 48-90 CPI on zEC12 | two DQEs in the processor | p.94 |
errors_and_checks: none
conditions: The looping implementation was chosen to satisfy area and power budgets rather than for latency (p.88).
evidence: Section II.G, Figure 2, Table II.

### sig_mul_then_round  (role: instantiates)
mechanism: Binary quad precision multiply is a multi-cycle operation through the DQE. The significand product is assimilated by the AREN compound adder, the result mantissa is then shifted appropriately in the shifter block, which also takes care of the corrections for subnormal operands and results, and the rounding takes place afterwards in the AREN by injection. Multi-cycle operations like decimal divide, decimal multiply and converts likewise end in a round operation passing through the AREN and the rounder.
choices: none
new_choices: none
slots:
  sig_mul: booth_recoded_parallel [booth_radix=4]   # p.89
parameters: binary QP significand 113b; assimilation, shift and rounding are separate passes through the shared dataflow   # p.89
results: none
errors_and_checks: none
conditions: none
evidence: Sections II.G, IV.

### digit_recurrence_sqrt_combined  (role: instantiates)
mechanism: Each of the two VFU pipelines has a standalone divide and square root engine that supports all binary and hexadecimal floating-point data types, single, double and quad precision. The underlying algorithm is SRT, generating 3 bits per cycle for divide and 2 bits per cycle for square root, on a quad precision mantissa of 113 bits plus some extra bits for rounding. A partially redundant number format was key to fitting one SRT step on such a wide mantissa into a single 5 GHz cycle. On receiving the operands the engine checks whether a mantissa is unnormalized, counts the leading zeros, fully normalizes the operands, initializes the SRT engine and runs a number of iterations based only on the operation and the precision.
choices: none
new_choices:
  residual_form: partially_redundant — the number format that lets one SRT step on a 113-bit mantissa close a 5 GHz cycle   # p.93
  result_bits_per_cycle: 3 for divide and 2 for square root   # p.93
slots: none
parameters: quad precision mantissa 113 bits plus extra rounding bits; one engine per VFU pipeline, two divide engines per processor; iteration count fixed by operation and precision   # p.93, p.94
results:
| metric | value | unit | technology / device | baseline | condition | page |
| Divide latency | 49 | cycles | IBM 22 nm, 2016 | ~165 cycles on zEC12 | quad precision, executed in the divide engine | p.94 |
| Divide throughput | 21 | CPI | IBM 22 nm, 2016 | ~158 CPI on zEC12 | two divide engines in the processor | p.94 |
| Sqrt latency | 66 | cycles | IBM 22 nm, 2016 | ~170 cycles on zEC12 | quad precision, executed in the divide engine | p.94 |
| Sqrt throughput | 24 | CPI | IBM 22 nm, 2016 | ~163 CPI on zEC12 | two divide engines in the processor | p.94 |
errors_and_checks: Subnormal binary and unnormalized hexadecimal numbers are supported in hardware by the leading zero count and the full normalization of the operands. Subnormal results may require fewer bits to be computed, and no early-out hardware was added because these cases are rare in commercial applications and would only increase the interface complexity.   # p.93
conditions: The engine is standalone, so the z13 can freely start new VFU instructions in the other engines, including the DQE, while a divide or square root is ongoing, and divide and square root execute in parallel with addition, subtraction and multiplication on the DQE (p.93, p.94).
evidence: Section V, Table II.

## new_families
### decimal_binary_radix_conversion  (domain: decimal, closest: parallel_decimal_multiplication, why_not: the mechanism converts a number between radix 10 and radix 2 rather than multiplying two decimal operands, and its per-iteration operand is three decimal digits rather than a partial-product matrix)
mechanism: The convert from decimal to binary is done in an iterative fashion, converting three digits at a time and adding them to the intermediate result multiplied by 1000. On the z13 the reduction and accumulation of the conversion terms reuse the binary multiplier structure: the compressor of the binary multiplier compresses the 3 new decimal digits with the 3 shifted terms of the sum and carry vectors that multiply the intermediate result by 1000. The rest of the algorithm is that of the z196 and zEC12 machines; the reuse of the binary multiplier structure is the change made on z13.
choices: digits_per_iteration: 1..3 by 1; reduction_hardware: enum['dedicated', 'reuse_binary_multiplier_compressor']
results: none
evidence: p.89 (Section II.F, Section II.G)

## space_gaps
* The fp adder families carry no `round` slot, so the injection rounder that this adder is built around cannot be recorded as the rounder of the adder   # p.88, p.90
* `compound_flagged_prefix.outputs` has no value covering sum, sum+1 and an inverted sum together, which is what H0, H1 and HC are   # p.90
* `bcd_direct_addition.correction_placement` holds one value, and this adder applies a presum +6 to the B operand together with a postsum -6 or +6 correction   # p.90
* No fp adder choice records one shifter, adder and rounder shared across the binary, hexadecimal and decimal radices, with the decimal 6-corrections suppressed for binary   # p.88, p.90
* No multiplier choice or slot records a final assimilation split over two passes of a shared adder, which is how the 226-bit sum and carry vectors are added in the AREN   # p.89

## open_questions
* The topology of the two regular binary carry trees inside the compound adder is not named   # p.90
* The internal structure of the LZA, of the normalizer's shifter and of the two shifter stages is not given beyond digit shift then bit shift   # p.88, p.89
* The SRT radix, the quotient digit set and the digit selection of the divide and square root engine are not stated, only 3 result bits per cycle for divide and 2 for square root   # p.93
* Which unit executes binary single and double precision add and subtract is not stated: the paper reports that quad precision BFP and HFP operations moved to the DQE and that single and double precision operands are padded on the DQE shifter, while two 64-bit binary floating point units remain in the VFU   # p.87, p.88, p.94
