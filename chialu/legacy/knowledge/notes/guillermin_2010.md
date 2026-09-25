---
handle: guillermin_2010
citation: Guillermin, "A High Speed Coprocessor for Elliptic Curve Scalar Multiplications over F_p", CHES (LNCS 6225), 2010
actual_citation: same
status: ok
kind: paper
unit_classes: [other]
formats: [Fp_160, Fp_192, Fp_256, Fp_384, Fp_512]
authority: incremental
pages_read: 48-64 / 17 pages
---

## summary
The paper extends the Cox-Rower RNS Montgomery architecture into an FPGA coprocessor for elliptic-curve scalar multiplication over general prime fields. Parallel pseudo-Mersenne residue channels execute modular multiply-accumulate operations through five-stage or six-stage pipelines. Implemented Stratix/Stratix II designs cover 160-bit through 512-bit curves and include final inversion/coordinate recovery/base conversions.

## families
### rns_montgomery_crypto  (role: extends)
mechanism: Two coprime RNS bases B and B̃ support Montgomery reduction through two Kawamura approximate base extensions. Parallel Rower modules execute acc = |x × y + acc|mi, while Cox logic supplies the approximate correction. Projective Montgomery-ladder formulas exploit AB + CD patterns to perform one addition and one doubling in 13 reductions per scalar bit. Sixteen GPRs per channel permit overlapping independent point-operation calculations. # pp.50-59
choices:
  channel_count_per_base: 5, 6, 8, 11, or 15   # pp.53,60
  channel_width: 34, 33, 33, 36, or 35   # pp.53,60
  base_extension: kawamura_approximate   # pp.51-52
new_choices:
  pipeline_depth: 5 or 6 — stages in each Rower modular multiply-accumulate pipeline   # pp.56-57
  gpr_per_channel: 16 — registers supporting overlapped point-operation schedules   # pp.58-59
slots:
  none
parameters: 160/192/256/384/512-bit curves; one Montgomery-ladder addition and doubling per scalar bit; 13 reductions per ladder step; 5/6/8/11/15 Rowers for the implemented 34/33/33/36/35-bit channels. # pp.52-53,59-60
results:
| metric | value | unit | technology / device | baseline | condition | page |
| latency | 0.57 | ms | 130 nm Altera Stratix EP1S20F484C5, 2010 | absolute | 160-bit complete [k]G | p.60 |
| area | 11431 | LE | 130 nm Altera Stratix EP1S20F484C5, 2010 | absolute | 160-bit | p.60 |
| DSP occupation | 74 | 9 × 9 multipliers | 130 nm Altera Stratix EP1S20F484C5, 2010 | absolute | 160-bit | p.60 |
| frequency | 92.6 | MHz | 130 nm Altera Stratix EP1S20F484C5, 2010 | absolute | 160-bit | p.60 |
| latency | 0.72 | ms | 130 nm Altera Stratix EP1S30F780C5, 2010 | absolute | 192-bit complete [k]G | p.60 |
| area | 12480 | LE | 130 nm Altera Stratix EP1S30F780C5, 2010 | absolute | 192-bit | p.60 |
| DSP occupation | 80 | 9 × 9 multipliers | 130 nm Altera Stratix EP1S30F780C5, 2010 | absolute | 192-bit | p.60 |
| frequency | 89.6 | MHz | 130 nm Altera Stratix EP1S30F780C5, 2010 | absolute | 192-bit | p.60 |
| latency | 1.17 | ms | 130 nm Altera Stratix EP1S60F780C5, 2010 | absolute | 256-bit complete [k]G | p.60 |
| area | 16200 | LE | 130 nm Altera Stratix EP1S60F780C5, 2010 | absolute | 256-bit | p.60 |
| DSP occupation | 125 | 9 × 9 multipliers | 130 nm Altera Stratix EP1S60F780C5, 2010 | absolute | 256-bit | p.60 |
| frequency | 90.7 | MHz | 130 nm Altera Stratix EP1S60F780C5, 2010 | absolute | 256-bit | p.60 |
| latency | 2.25 | ms | 130 nm Altera Stratix EP1S80F1020C5, 2010 | absolute | 384-bit complete [k]G | p.60 |
| area | 25279 | LE | 130 nm Altera Stratix EP1S80F1020C5, 2010 | absolute | 384-bit | p.60 |
| DSP occupation | 176 | 9 × 9 multipliers | 130 nm Altera Stratix EP1S80F1020C5, 2010 | absolute | 384-bit | p.60 |
| frequency | 90.0 | MHz | 130 nm Altera Stratix EP1S80F1020C5, 2010 | absolute | 384-bit | p.60 |
| latency | 4.03 | ms | 130 nm Altera Stratix EP1S80F1020C5, 2010 | absolute | 512-bit complete [k]G | p.60 |
| area | 48305 | LE | 130 nm Altera Stratix EP1S80F1020C5, 2010 | absolute | 512-bit | p.60 |
| DSP occupation | 176 | 9 × 9 multipliers | 130 nm Altera Stratix EP1S80F1020C5, 2010 | absolute | 512-bit | p.60 |
| frequency | 79.6 | MHz | 130 nm Altera Stratix EP1S80F1020C5, 2010 | absolute | 512-bit; some multipliers use LE blocks | p.60 |
| latency | 0.32 | ms | 90 nm Altera Stratix II EP2S30F484C3, 2010 | absolute | 160-bit complete [k]G | p.60 |
| area | 5896 | ALM | 90 nm Altera Stratix II EP2S30F484C3, 2010 | absolute | 160-bit | p.60 |
| DSP occupation | 74 | 9 × 9 multipliers | 90 nm Altera Stratix II EP2S30F484C3, 2010 | absolute | 160-bit | p.60 |
| frequency | 165.5 | MHz | 90 nm Altera Stratix II EP2S30F484C3, 2010 | absolute | 160-bit | p.60 |
| latency | 0.44 | ms | 90 nm Altera Stratix II EP2S30F484C3, 2010 | absolute | 192-bit complete [k]G | p.60 |
| area | 6203 | ALM | 90 nm Altera Stratix II EP2S30F484C3, 2010 | absolute | 192-bit | p.60 |
| DSP occupation | 92 | 9 × 9 multipliers | 90 nm Altera Stratix II EP2S30F484C3, 2010 | absolute | 192-bit | p.60 |
| frequency | 160.5 | MHz | 90 nm Altera Stratix II EP2S30F484C3, 2010 | absolute | 192-bit | p.60 |
| latency | 0.68 | ms | 90 nm Altera Stratix II EP2S30F484C3, 2010 | absolute | 256-bit complete [k]G | p.60 |
| area | 9177 | ALM | 90 nm Altera Stratix II EP2S30F484C3, 2010 | absolute | 256-bit | p.60 |
| DSP occupation | 96 | 9 × 9 multipliers | 90 nm Altera Stratix II EP2S30F484C3, 2010 | absolute | 256-bit | p.60 |
| frequency | 157.2 | MHz | 90 nm Altera Stratix II EP2S30F484C3, 2010 | absolute | 256-bit | p.60 |
| latency | 1.35 | ms | 90 nm Altera Stratix II EP2S60F484C3, 2010 | absolute | 384-bit complete [k]G | p.60 |
| area | 12958 | ALM | 90 nm Altera Stratix II EP2S60F484C3, 2010 | absolute | 384-bit | p.60 |
| DSP occupation | 177 | 9 × 9 multipliers | 90 nm Altera Stratix II EP2S60F484C3, 2010 | absolute | 384-bit | p.60 |
| frequency | 150.9 | MHz | 90 nm Altera Stratix II EP2S60F484C3, 2010 | absolute | 384-bit | p.60 |
| latency | 2.23 | ms | 90 nm Altera Stratix II EP2S60F484C3, 2010 | absolute | 512-bit complete [k]G | p.60 |
| area | 17017 | ALM | 90 nm Altera Stratix II EP2S60F484C3, 2010 | absolute | 512-bit | p.60 |
| DSP occupation | 244 | 9 × 9 multipliers | 90 nm Altera Stratix II EP2S60F484C3, 2010 | absolute | 512-bit | p.60 |
| frequency | 144.97 | MHz | 90 nm Altera Stratix II EP2S60F484C3, 2010 | absolute | 512-bit | p.60 |
errors_and_checks: RedMontg is exact modulo p for X < αp² when M > αp and M̃ > 2p, and it returns S < 2p. # p.51
conditions: The implementation supports general prime p rather than only pseudo-Mersenne field primes. # pp.60-62 The fixed-ROM results require a new bitstream to change curves; runtime curve/base changes require RAM or extra cycles/waits. # p.58 The Montgomery ladder has no dummy operation or data-dependent timing branch, while DPA resistance requires optional coordinate/scalar randomization. # p.59 The 512-bit Stratix implementation loses frequency because the device lacks enough DSP blocks. # pp.60-61
evidence: Algorithms 1 and 5; Figures 1-2; §§2.1-2.3, 3.1-3.5, 4.1-4.2; implementation table on p.60.

### rns_channel_arithmetic  (role: instantiates)
mechanism: Each independent channel uses mi = 2^r − εi. Algorithm 3 folds the high product portions through r × q and q × q multiplications, then performs modular additions. The ALU accepts |r1 × r2|mi and accumulation each cycle. FPGA DSP blocks implement the multipliers, while parallel candidate sums and a carry-controlled selection implement modular addition. # pp.53,55-57
choices:
  modulus_form: generic   # p.53
  channel_width_n: 17 to 36   # p.53
  multiplier_reduction: pseudo_mersenne_folding [outside domain]   # pp.55-56
new_choices:
  none
slots:
  modular_adder: none   # pp.56-57
parameters: mi = 2^r − εi; εi < 2^q; q < r/2; r = 17-36; q = 5-9; five-stage and six-stage alternatives. # pp.53,55-57
results:
| metric | value | unit | technology / device | baseline | condition | page |
| frequency | 110 | MHz | 90 nm Altera Stratix II, 2010 | absolute | five-stage pipeline | p.57 |
| frequency | 158 | MHz | 90 nm Altera Stratix II, 2010 | absolute | six-stage pipeline | p.57 |
| reported idle states | 95 | % | 90 nm Altera Stratix II, 2010 | absolute | five stages, five channels, 160-bit curve | p.57 |
| reported idle states | 90 | % | 90 nm Altera Stratix II, 2010 | absolute | six stages, five channels, 160-bit curve | p.57 |
errors_and_checks: none
conditions: The five-stage balance assumes modular addition is twice as fast as multiplication, while the six-stage balance assumes equal speeds. # p.56 Independent curve operations must overlap to occupy deeper pipelines, which can require more registers. # pp.56-59
evidence: Base-choice table on p.53; Algorithms 3-4; Figure 2; §§3.2-3.3.

### rns_reverse_converter  (role: proposes)
mechanism: The converter fixes channel m0 of B to 2^r, so the least radix word is x0. It repeatedly computes X ← (X − x0)/2^r over B̃ and applies Bext back to B to recover successive radix words. The existing Rower/main-bus datapath executes the conversion without added gates. # p.59
choices:
  algorithm: iterative_radix_extraction [outside domain]   # p.59
  implementation: adder_based   # p.59
new_choices:
  none
slots:
  none
parameters: radix word size r; m0 = 2^r; repeated extraction of X0 through Xn. # p.59
results:
| metric | value | unit | technology / device | baseline | condition | page |
| conversion time overhead | not more than 0.3 | % of total scalar multiplication time | UNKNOWN, 2010 | absolute | RNS-to-radix conversion | p.59 |
errors_and_checks: none
conditions: The conversion requires m0 = 2^r, computation over B̃ because 2^r is not coprime with M, and sequencer access to radix words/constants on the main bus. # p.59
evidence: §3.4, p.59.

## new_families
none

## space_gaps
* `rns_channel_arithmetic.multiplier_reduction` lacks the `pseudo_mersenne_folding` value used by Algorithm 3. # pp.55-56
* `rns_reverse_converter.algorithm` lacks the repeated `m0 = 2^r` radix-extraction method. # p.59
* `rns_montgomery_crypto` lacks pipeline-depth and per-channel-register choices needed to represent the five-stage/six-stage and 16-GPR tradeoff. # pp.56-59

## open_questions
* Page 57 calls 95% and 90% the percentage of “idle states,” while page 59 calls 90% the pipeline fill rate; the intended interpretation is ambiguous.
* The detailed table reports 5896 ALM for the 160-bit Stratix II implementation on p.60, while the comparison table reports 6203 ALM for that design on p.61.
