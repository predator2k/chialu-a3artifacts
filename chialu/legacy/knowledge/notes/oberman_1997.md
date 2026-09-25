---
handle: oberman_1997
citation: Oberman, Flynn, "Division Algorithms and Implementations", IEEE Transactions on Computers, 1997
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [fp32, fp64, IEEE_double_extended]
authority: survey
pages_read: 22 / 22
---

## summary
The paper classifies hardware division into digit-recurrence, functional-iteration, very-high-radix, table-lookup, and variable-latency classes (p.833). The comparison finds digit recurrence suitable for minimum-area implementations, functional iteration suitable for low latency with typical multipliers, and variable-latency methods promising for low average latency and area (pp.833, 851–853). The analysis covers floating-point division and notes that most conclusions also apply to square root (p.834).

## families
### srt_radix2  (role: analyzes)
mechanism: A subtractive recurrence selects one quotient digit from an estimate of the shifted partial remainder and divisor, forms the selected divisor multiple, and subtracts it from the shifted residual. A redundant quotient digit set permits selection without knowing the exact carry-save residual (pp.834–836).
choices:
  residual_form: twos_complement_cpa, carry_save   # p.836
new_choices:
  quotient_digit_set: nonredundant, minimally_redundant, maximally_redundant, over_redundant — allowed signed-digit redundancy controls selection and multiple-generation complexity   # p.835
slots:
  digit_select: qds_table   # pp.834, 836
parameters: normalized n-bit significands; n = 24 for IEEE single precision and n = 53 for IEEE double precision; one quotient digit per iteration in the basic recurrence   # p.834
results:
| metric | value | unit | technology / device | baseline | condition | page |
| circuit-style speedup | 1.5-1.7x | speedup | circuit study; 1997 | static CMOS gates | dual-rail domino, same circuit family | p.841 |
errors_and_checks: Correct rounding traditionally uses one extra guard digit and the final remainder; negative remainder may require restoration, and adding one ulp may require a full carry-propagate addition (p.841).
conditions: Carry-save residuals reduce recurrence delay but double residual-register storage, complicate quotient selection, and require final assimilation when a remainder is needed (p.836).
evidence: §§2.1–2.2, 2.4–2.5; Figs. 1–2.

### srt_high_radix  (role: compares)
mechanism: Higher radix is obtained through direct radix increase, cascaded low-radix stages, overlapped quotient selection, overlapped remainder computation, range reduction, or operand prescaling. Larger radix reduces iteration count but increases quotient-selection/divisor-multiple complexity and may increase cycle time (pp.834–841).
choices:
  radix: 4, 8, 16   # pp.835, 838–839
  digit_redundancy: minimal, intermediate, maximal   # pp.835, 840–841
  overlapped_stages: 1, 2, 3   # pp.837–839
new_choices:
  stage_composition: simple_staging, overlapped_quotient_selection, overlapped_remainder_computation, range_reduction — methods for composing low-radix stages   # pp.837–840
slots:
  digit_select: qds_table   # pp.836–840
parameters: radix-4 retires two bits/iteration; radix-16 retires four bits/iteration; UltraSPARC cascades three radix-2 stages into radix-8   # pp.835, 838
results:
| metric | value | unit | technology / device | baseline | condition | page |
| latency | 27 | cycles | UNKNOWN; 1997 | none | n = 53, radix 4 | p.852 |
| latency | 18 | cycles | UNKNOWN; 1997 | none | n = 53, radix 8 | p.852 |
| latency | 14 | cycles | UNKNOWN; 1997 | none | n = 53, radix 16 | p.852 |
| latency | 7 | cycles | UNKNOWN; 1997 | none | n = 53, radix 256 | p.852 |
| cycle-time reduction | nearly halved | cycle time | UNKNOWN; 1997 | standard radix-4 divider | duplicate remainder-computation hardware once | p.839 |
errors_and_checks: On-the-fly rounding maintains Qk, QMk, and QPk; final selection requires final-remainder sign and exact-zero detection (p.841).
conditions: Practical SRT dividers are described as limited to fewer than 10 quotient bits/cycle by cycle-time/area constraints (p.851).
evidence: §§2.2–2.5, 7; Figs. 3–6; Tables 1–2.

### newton_raphson  (role: compares)
mechanism: Newton-Raphson refines the reciprocal with Xi+1 = Xi(2 - bXi), using two dependent multiplications and a complement operation per iteration. A final multiplication by the dividend forms the quotient, and the reciprocal error decreases quadratically (p.842).
choices:
  iterations: 2, 3, 6 [outside domain]   # p.842
  dedicated_multiplier: false, true   # pp.841, 853
new_choices:
  complement_step: twos_complement, ones_complement — ones complement avoids full carry propagation with a one-ulp difference   # p.842
slots:
  seed: monolithic_rom   # pp.842, 847
  iter_mult: behavioral_star   # p.842
  final_round: back_multiply_remainder   # pp.843–844
parameters: 53-bit result requires six iterations from a one-bit seed, three from an eight-bit seed, or two from at least 14 bits; two dependent multiplications per iteration   # p.842
results:
| metric | value | unit | technology / device | baseline | condition | page |
| latency for tmul = 1/2/3 | 8/15/22 | cycles | UNKNOWN; 1997 | none | n = 53, initial approximation i = 8 | p.852 |
| latency for tmul = 1/2/3 | 6/11/16 | cycles | UNKNOWN; 1997 | none | n = 53, initial approximation i = 16 | p.852 |
errors_and_checks: Exact rounding may use more than twice-result precision followed by R = a - bQ′ and Q″ = Q′ + Rb, or may determine the final remainder by back multiplication/sign/zero detection (pp.843–844).
conditions: Dependent multiplications serialize each iteration; the iteration is self-correcting, and shared multiplier contention is reported as small in typical floating-point applications (pp.841–843).
evidence: §§3.1, 3.3, 7; Tables 1–2.

### goldschmidt  (role: compares)
mechanism: The series-expansion form multiplies numerator and denominator by a common correction factor so the denominator converges to one and the numerator converges quadratically to the quotient. Its two multiplications per iteration are independent and may execute concurrently in a pipelined multiplier (pp.842–843).
choices:
  truncated_intermediate_multiplies: true   # pp.843–844
new_choices:
  multiplier_schedule: serial_unpipelined, concurrent_pipelined — independent numerator/denominator products permit overlap   # p.843
slots:
  seed: monolithic_rom   # pp.842–843
  iter_mult: behavioral_star   # pp.842–843
  final_round: back_multiply_remainder   # pp.843–844
parameters: two multiplications and one twos-complement operation per iteration; early iterations may use reduced precision   # p.843
results:
| metric | value | unit | technology / device | baseline | condition | page |
| latency for tmul = 1/2/3 | 9/17/25 | cycles | UNKNOWN; 1997 | none | n = 53, i = 8, unpipelined | p.852 |
| latency for tmul = 1/2/3 | 7/13/19 | cycles | UNKNOWN; 1997 | none | n = 53, i = 16, unpipelined | p.852 |
| latency for tmul = 1/2/3 | 9/10/14 | cycles | UNKNOWN; 1997 | none | n = 53, i = 8, pipelined | p.852 |
| latency for tmul = 1/2/3 | 7/8/11 | cycles | UNKNOWN; 1997 | none | n = 53, i = 16, pipelined | p.852 |
errors_and_checks: Multiplication-rounding errors accumulate because independent operations are not self-correcting, so a wider multiplier is required; the IBM 360/91’s ten guard bits produced non-IEEE “somewhat round-to-nearest” results (pp.843–844).
conditions: The paper finds series expansion lowest-latency for reasonable area/multiplier latency, while Newton-Raphson can trade latency for throughput when multiple divisions occupy a pipelined multiplier (pp.852–853).
evidence: §§3.2–3.3, 7–8; Tables 1–2.

### prescaled_very_high_radix  (role: compares)
mechanism: Very-high-radix methods obtain an initial reciprocal approximation and use multiplication for divisor-multiple formation. The surveyed variants form quotient segments from accurate quotient approximations, a short reciprocal, or rounding of a prescaled carry-save residual (pp.844–847).
choices:
  bits_per_iteration: 17 [outside domain]   # pp.845–846
  prescaling_precision_bits: 19 [outside domain]   # p.845
  shared_scaling_multiplier: true, false   # pp.845–847
slots:
  prescaler: behavioral_star   # pp.845–847
  seed: monolithic_rom   # pp.844–846
parameters: “very high radix” means more than 10 quotient bits/iteration; Cyrix uses one 18 × 69 rectangular fused multiply/add and retires 17 bits/iteration; general round/prescale latency is ceil(n/b) + 4 cycles   # pp.844–846
results:
| metric | value | unit | technology / device | baseline | condition | page |
| latency | 15 | cycles | Cyrix 83D87; 1997 survey | none | double precision, six seed cycles | p.846 |
| latency | 10 | cycles | Cyrix 83D87; 1997 survey | none | larger table, one-cycle seed | p.846 |
| latency for tmul = 1/2/3 | 10/19/28 | cycles | UNKNOWN; 1997 | none | round/prescale, n = 53, i = 8, unpipelined | p.852 |
| latency for tmul = 1/2/3 | 7/13/19 | cycles | UNKNOWN; 1997 | none | round/prescale, n = 53, i = 16, unpipelined | p.852 |
| latency for tmul = 1/2/3 | 10/18/26 | cycles | UNKNOWN; 1997 | none | round/prescale, n = 53, i = 8, pipelined | p.852 |
| latency for tmul = 1/2/3 | 7/10/14 | cycles | UNKNOWN; 1997 | none | round/prescale, n = 53, i = 16, pipelined | p.852 |
errors_and_checks: Very-high-radix methods provide a true remainder and support postcorrection/rounding; prescaling both operands makes the remainder unusable without postscaling (pp.846, 851).
conditions: Accurate-quotient approximation can reach five cycles with a 736K-bit table and three multipliers, while the Cyrix short-reciprocal variant minimizes area with one rectangular fused unit (pp.845, 851–852).
evidence: §§4.1–4.3, 7; Tables 1–2.

### monolithic_rom  (role: analyzes)
mechanism: A normalized divisor’s leading bits index a ROM/PLA containing a midpoint reciprocal rounded and truncated to the requested output width. Table size grows exponentially with input precision (p.847).
choices:
  function: reciprocal   # p.847
new_choices: none
slots: none
parameters: k address bits, m stored output bits, 2^k m total bits; optional output guard bits g   # p.847
results:
| metric | value | unit | technology / device | baseline | condition | page |
| minimum precision | k + 0.415 | bits | UNKNOWN; 1997 | none | k-bits-in/k-bits-out table | p.847 |
| minimum precision | k + 0.678 | bits | UNKNOWN; 1997 | none | one output guard bit | p.847 |
| minimum precision | k + 0.830 | bits | UNKNOWN; 1997 | none | two output guard bits | p.847 |
| minimum precision | k + 0.912 | bits | UNKNOWN; 1997 | none | three output guard bits | p.847 |
errors_and_checks: The midpoint construction minimizes maximum relative error for piecewise-constant reciprocal tables (p.847).
conditions: ROM access is fast because it performs no arithmetic, but storage grows exponentially with each added input bit (p.847).
evidence: §5.1, equations (34)–(36).

### bipartite_rom  (role: analyzes)
mechanism: Separate tables produce positive/negative reciprocal portions in borrow-save form. The redundant output is recoded with the following multiplier, which avoids a separate multiply/accumulate operation (p.847).
choices:
  function: reciprocal   # p.847
new_choices: none
slots: none
parameters: conventional comparison spans four-to-16-bit reciprocal tables   # p.847
results:
| metric | value | unit | technology / device | baseline | condition | page |
| table-size reduction | two to four times | smaller | UNKNOWN; 1997 | conventional reciprocal table | four-to-nine-bit tables | p.847 |
| table-size reduction | four to more than 16 times | smaller | UNKNOWN; 1997 | conventional reciprocal table | 10-16-bit tables | p.847 |
errors_and_checks: The cited construction is faithful and integrates output rounding with multiplier recoding (p.847).
conditions: The method assumes the table output feeds a multiplier that accepts the redundant representation (p.847).
evidence: §5.1.

### self_timed_variable_latency  (role: compares)
mechanism: Variable-latency designs use self-timed cascaded SRT stages, quotient-bit skipping, speculative quotient selection with correction, clock gating, or reuse through caches. Completion time depends on operand behavior or cache reuse rather than a fixed iteration count (pp.848–851).
choices:
  mechanism: self_timed, speculation_rollback, early_termination, clock_gating   # pp.848–850
slots:
  digit_select: qds_table   # pp.848, 850
new_choices:
  cached_value: quotient, reciprocal — result reuse can terminate a computation after a cache hit   # pp.849–850
parameters: self-timed design uses five cascaded radix-2 stages; speculative examples retire up to four or six bits/cycle   # pp.848, 850
results:
| metric | value | unit | technology / device | baseline | condition | page |
| latency | 45 to 160 | ns | 1.2mm CMOS; 1991 | none | 54-b self-timed divider, operand-dependent | p.849 |
| latency | about seven | cycles | Hal SPARC64; 1995 | none | IEEE double precision | p.849 |
| quotient retirement | 2.4 | bits/cycle average | DEC Alpha 21164; 1995 | none | zero/one-string skipping | p.848 |
| delay per bit | 30 percent faster | percent | UNKNOWN; 1994 | fastest conventional radix-8 segmented divider | speculative radix-64 | p.850 |
| area | 44 percent more | percent | UNKNOWN; 1994 | conventional implementation | speculative radix-64 | p.850 |
| latency | 10 percent faster | percent | UNKNOWN; 1994 | conventional radix-8 divider | speculative radix-16 | p.850 |
| area | 25 percent reduction | percent | UNKNOWN; 1994 | conventional radix-8 divider | speculative radix-16 | p.850 |
| speedup | about two-times | speedup | UNKNOWN; 1997 | divider without reciprocal cache | cache about eight times an 8-bits-in/8-bits-out ROM | p.850 |
errors_and_checks: Incorrect quotient speculation requires at least one correction iteration; self-timing requires correct asynchronous clocking/circuit/test behavior (pp.850–851).
conditions: Division caches are inefficient when the base divider has high latency; reciprocal caches use smaller tags and obtain higher hit rates than quotient caches (pp.849–850).
evidence: §6, Figs. 7–9.

## new_families
### linear_reciprocal_seed  (domain: div: reciprocal seed tables, closest: poly_seed, why_not: the vocabulary restricts poly_seed to a minimax polynomial, while this mechanism stores segment coefficients and evaluates a general linear approximation)
mechanism: Two coefficient tables indexed by the leading divisor bits provide C0 and C1, and a multiply/add evaluates -C1b + C0. Modified forms replace the multiply/add with one multiplication and operand modification (pp.847–848).
choices: coefficient_tables: {one, two}; evaluation: {multiply_add, operand_modified_multiply}
results:
| metric | value | unit | technology / device | baseline | condition | page |
| guaranteed precision | 2k + 2 | bits | UNKNOWN; 1997 | none | m = 2k + 3 | p.847 |
| guaranteed precision | 2.5k | bits | UNKNOWN; 1997 | none | modified linear function | p.848 |
evidence: §5.2.

### partial_product_reciprocal_seed  (domain: div: reciprocal seed tables, closest: operand_modification_multiply, why_not: the seed is synthesized as generalized Boolean elements in a reused multiplier array rather than by multiplying a modified operand)
mechanism: A back-solved partial-product array sums directly to a reciprocal approximation and can reuse an existing floating-point multiplier (p.848).
choices: multiplier_array: {plain_53_row, booth_27_row}; reuse_existing_multiplier: Bool
results:
| metric | value | unit | technology / device | baseline | condition | page |
| minimum/average accuracy | 12.003/15.18 | correct bits | UNKNOWN; 1997 | none | 484 Boolean elements, 18 columns of 53-row array | p.848 |
| area | 39 times smaller | area | UNKNOWN; 1997 | equivalent 12-bit ROM | 484-element implementation | p.848 |
| minimum/average accuracy | 9.17/12.71 | correct bits | UNKNOWN; 1997 | none | 175 Boolean elements, Booth array | p.848 |
evidence: §5.3.

### division_result_cache  (domain: div: dividers / square root, closest: self_timed_variable_latency, why_not: latency reduction comes from memoizing prior results rather than changing recurrence timing)
mechanism: A quotient or reciprocal cache is accessed when division issues. A hit supplies the stored value and halts the divider; a miss permits normal execution and stores the completed value (pp.849–850).
choices: cached_value: {quotient, reciprocal}; associativity: {direct_mapped, fully_associative}
results:
| metric | value | unit | technology / device | baseline | condition | page |
| entry storage | approximately 160 | bits | UNKNOWN; 1997 | none | double-precision quotient cache | p.849 |
| entry storage | approximately 108 | bits | UNKNOWN; 1997 | none | reciprocal cache | p.849 |
evidence: §6.2, Figs. 8–9.

## space_gaps
* `srt_high_radix.radix` lacks 64 and 256, which the survey analyzes as staged/speculative or prospective SRT configurations (pp.839, 850, 852).
* `prescaled_very_high_radix.bits_per_iteration` stops at 16, while the Cyrix implementation retires 17 bits/iteration (pp.845–846).
* `prescaled_very_high_radix.prescaling_precision_bits` stops at 16, while the Cyrix short reciprocal is refined to 19 bits (p.845).
* SRT families lack explicit choices for quotient-digit-set bounds, partial-remainder encoding, stage overlap, and on-the-fly quotient conversion/rounding (pp.835–841).

## open_questions
* The paper groups result caches with variable-latency algorithms, but the merge pass must decide whether caching belongs inside divider microarchitecture or at the surrounding execution-unit level.
* Table 2 excludes rounding/normalization latency, so its cycle counts must not be treated as complete IEEE-operation latency (pp.851–852).
