---
handle: montalvo_1998
citation: Montalvo, Parhi, Guyot, "New Svoboda-Tung Division", IEEE Transactions on Computers, 1998
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [binary, fp64]
authority: landmark
pages_read: 1014-1020 / 7
---

## summary
The paper develops New Svoboda-Tung division, which recodes the two most significant residual digits before selecting the quotient digit and supports power-of-two radices b ≥ 2. # p.1014, p.1015
The paper characterizes b²/4 variants per radix and identifies the minimally redundant radix-4 “mr” algorithm as the preferred radix-4 variant under its implementation criteria. # p.1016, p.1018

## families
### svoboda_tung  (role: proposes)
mechanism: NST uses the recurrence R^(j+1) = bR^j − q_(j+1)Y with a redundant signed-digit residual D<b.α> and a nonredundant divisor. The two most significant residual digits r1^j r2^j are conditionally recoded into r1a^j r2a^j while preserving br1a^j + r2a^j = br1^j + r2^j. The quotient digit is q_(j+1) = r1a^j. Both operands are multiplied by K so that Y = KYstd lies in [1, 1 + δ). # p.1015, p.1016
choices:
  radix: powers of 2, b ≥ 2 [outside domain]   # p.1014, p.1016
  msd_recoding: two_digit_recode   # p.1015
new_choices:
  residual_digit_set: D<b.α>, b/2 ≤ α ≤ b − 1 — the redundant digit set used for the residual   # p.1015
  recoding_threshold: β, b − α − 1 ≤ β < α — the largest opposite-sign second digit left without recoding   # p.1016
  divisor_range: 1 ≤ Y < 1 + δ, δ = (α − β)/(bα) — the valid range after prescaling   # p.1016, p.1017
  algorithm_variant: MRMR | MROR | MRmr | mr | intermediate — named α/β design points   # p.1017
slots:
  prescaler: UNKNOWN   # p.1016
parameters: General count N_nst,b = b²/4; radix-4 variants are MRMR (α=3, β=0, δ=1/4), MROR (α=3, β=1, δ=1/6), MRmr (α=3, β=2, δ=1/12), and mr (α=2, β=1, δ=1/8). Their prescaling latencies are 3/3/3/2 cycles, and their quotient-selection inputs are 8/6/8/6 residual bits. The analytical fp64 comparison uses W=53, W/2 recurrence cycles, and ignores quotient-conversion cycles. # p.1016, p.1017, p.1018, p.1019
results:
| metric | value | unit | technology / device | baseline | condition | page |
| computation time | 891.75 | unit delays | UNKNOWN; result 1998 | MROR: 1,057.50 unit delays | mr, W=53 analytical gate-delay model | p.1019 |
| speedup | 1.19 | speedup | UNKNOWN; result 1998 | prescaled NST MROR | mr, W=53 | p.1019 |
| speedup | 1.44 | speedup | UNKNOWN; result 1998 | prescaled regular radix-4 | mr | p.1019 |
| speedup | 1.38 | speedup | UNKNOWN; result 1998 | prescaled over-redundant radix-4 (i) | mr | p.1019 |
| speedup | 1.31 | speedup | UNKNOWN; result 1998 | prescaled over-redundant radix-4 (ii) | mr | p.1019 |
| speedup | 1.36 | speedup | UNKNOWN; result 1998 | regular radix-4 | mr | p.1019 |
| speedup | 1.54 | speedup | UNKNOWN; result 1998 | SRT regular radix-2 (i) | mr | p.1019 |
| speedup | 1.77 | speedup | UNKNOWN; result 1998 | SRT regular radix-2 (ii) | mr | p.1019 |
| speedup | 1.45 | speedup | UNKNOWN; result 1998 | prescaled NST radix-2 | mr | p.1019 |
| area requirement | W CFA + W FAC + muxes | formula | UNKNOWN; result 1998 | none | mr; latches/quotient-selection logic excluded | p.1019 |
| area requirement | 2W CFA + W FAC + muxes | formula | UNKNOWN; result 1998 | mr | MROR; latches/quotient-selection logic excluded | p.1019 |
| computation time | 30 | ns | 1 µm CMOS, 2 metal; result 1995 | MROR: 32 ns | mr, 8 bits, combinational standard-cell layout | p.1019 |
| area | 3.2 | mm² | 1 µm CMOS, 2 metal; result 1995 | MROR: 3.3 mm² | mr, 8 bits, combinational standard-cell layout | p.1019 |
| computation time | 56 | ns | 1 µm CMOS, 2 metal; result 1995 | MROR: 58 ns | mr, 16 bits, combinational standard-cell layout | p.1019 |
| area | 9.6 | mm² | 1 µm CMOS, 2 metal; result 1995 | MROR: 10.3 mm² | mr, 16 bits, combinational standard-cell layout | p.1019 |
| computation time | 110 | ns | 1 µm CMOS, 2 metal; result 1995 | MROR: 117 ns | mr, 32 bits, combinational standard-cell layout | p.1019 |
| area | 35.2 | mm² | 1 µm CMOS, 2 metal; result 1995 | MROR: 39.5 mm² | mr, 32 bits, combinational standard-cell layout | p.1019 |
errors_and_checks: The quotient is correct and the recurrence satisfies the arithmetic condition, but prescaling changes the final residual to KR rather than R. No fault-detection mechanism is reported. # p.1016
conditions: NST requires both IEEE-range operands to be prescaled by the same K and requires the scaled divisor in nonredundant form. # p.1016 The design is unsuitable when an unscaled final residual is required. # p.1014, p.1016 The mr variant is favored for radix 4 because it avoids non-power-of-two divisor multiples, uses two prescaling cycles, and observes six residual bits. # p.1018 The physical comparisons cover only W ≤ 32 and do not use IEEE-standard precisions. # p.1019
evidence: §3, Fig. 1, Tables 1-2, §4, Tables 3-4, and §5; p.1015-p.1020

## new_families
none

## space_gaps
* svoboda_tung needs a residual-digit-set/redundancy choice because α changes the adder complexity, divisor multiples, and residual encoding. # p.1017, p.1018
* svoboda_tung needs a recoding-threshold choice because β changes quotient-selection complexity and the prescaling range. # p.1016, p.1018
* svoboda_tung needs a prescaling-range choice because δ controls the number of divisor bits and constant decomposition used by the prescaler. # p.1017, p.1018
* svoboda_tung.radix should include radix 2 and power-of-two radices above 16. # p.1014, p.1017

## open_questions
* The paper does not instantiate a specific prescaler family; it refers to previously published prescaling techniques. # p.1016
* The quantitative timing model omits the redundant-to-binary quotient-conversion cycles. # p.1018, p.1019
* The paper states that radix-2 implementations are slightly smaller than mr but does not provide matched physical-layout area values for them. # p.1020
