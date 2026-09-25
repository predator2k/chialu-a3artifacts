---
handle: kadric_2016
citation: E. Kadric, P. Gurniak, A. DeHon, "Accurate Parallel Floating-Point Accumulation", IEEE Transactions on Computers, vol. 65, no. 11, pp. 3224-3238, 2016
actual_citation: E. Kadric, P. Gurniak, and A. DeHon, "Accurate Parallel Floating-Point Accumulation", IEEE Symposium on Computer Arithmetic (ARITH 2013), 2013
status: ok
kind: paper
unit_classes: [VEC_DOT_ACC]
formats: [fp64]
authority: incremental
pages_read: 13 / 13
---

## summary
The document proposes an iterative parallel tree reduction that preserves each floating-point addition residue and returns the correctly rounded sum in O(log N) depth. A residue sum bound supplies conservative termination detection, while a Big Tie procedure guarantees termination. A Virtex 6 implementation consumes a tunable m summands per cycle using pipelined residue-preserving IEEE-754 double-precision adders.

## families
### streaming_accurate_accumulator  (role: proposes)
mechanism: Each FPAR tree node emits a rounded sum and the exactly representable discarded residue. The first reduction pass sums the inputs, and later passes reduce residues and add their sums into St. The algorithm computes rsb from the nonzero-residue count and maximum residue exponent, then terminates when adding or subtracting rsb cannot change the rounded result. A Big Tie procedure removes the tying bit and continues until the remaining residue sign is determined.
choices:
  approach: tree_reduce_with_refinement   # p.5
  in_loop_normalization: true   # p.3
new_choices:
  termination_detection: residue_sum_bound — stops when round(St + Rt + rsb) = round(St + Rt − rsb)   # p.6
  tie_resolution: big_tie_iteration — subtracts a bit after St's LSB and iterates until the residue sign is fixed   # p.7
  input_parallelism: tunable_m — instantiates additional FPAR tree levels to consume m summands per cycle   # p.12
slots:
  cpa: UNKNOWN
parameters: N summands; simulations use N = 2^12; two TSBs for the common two-pass case; m summands/cycle; latency 3N/m; O(N) work; O(log N) reduction depth   # pp.9-12
results:
| metric | value | unit | technology / device | baseline | condition | page |
| average iterations, σ | 2, 0 | iterations | UNKNOWN | none | Data 1-3, exponential and uniform distributions, δ = 10/100/1000/2000 | p.10 |
| average iterations, σ | 3, 0 | iterations | UNKNOWN | none | Data 4, exponential distribution, δ = 100, κ → ∞ | p.10 |
| average iterations, σ | 20, 0.17 | iterations | UNKNOWN | none | Data 4, exponential distribution, δ = 1000, κ → ∞ | p.10 |
| average iterations, σ | 39, 0.045 | iterations | UNKNOWN | none | Data 4, exponential distribution, δ = 2000, κ → ∞ | p.10 |
| FLOP count | 3 | FLOPs/summand | UNKNOWN | Leuprecht and Oberaigner tree: 14; iFastSum: 12 | two iterations in almost all cases | p.10 |
| TSB area | 2410 | LUTs plus Block RAMs | Virtex 6 FPGA | FPAR | N = 2^12 inputs | p.11 |
| TSB area overhead | 7% | more area | Virtex 6 FPGA | FPAR | N = 2^12 inputs | p.11 |
| TSB frequency | 250 | MHz | Virtex 6 FPGA | FPAR | critical path 3.967 ns | p.11 |
| mn area | 53 | LUTs | Virtex 6 FPGA | none | maxexp/nzcnt update block | p.12 |
| mn critical path | 2.378 | ns | Virtex 6 FPGA | none | maxexp/nzcnt update block | p.12 |
| conv area | 682 | LUTs | Virtex 6 FPGA | none | four pipeline stages | p.12 |
| conv critical path | 3.937 | ns | Virtex 6 FPGA | none | four pipeline stages | p.12 |
| full design area | 5648 | LUTs | Virtex 6 FPGA | two TSB modules | one value consumed per cycle | p.12 |
| full design area overhead | 17% | more area | Virtex 6 FPGA | two TSB modules | one value consumed per cycle | p.12 |
| full design critical path | 3.986 | ns | Virtex 6 FPGA | none | one value consumed per cycle | p.12 |
errors_and_checks: The result is the correctly rounded exact sum under IEEE-754 round-to-nearest, ties-to-even; Theorems 1 and 2 prove termination. The conservative rsb bound may cause extra iterations but cannot permit an incorrect early termination. No Big Tie occurred in the reported datasets.   # pp.6-10
conditions: Two passes suffice in most reported cases, while exponentially distributed zero-sum data with κ → ∞ requires up to 39 average iterations.   # pp.9-10
evidence: Fig. 2 and Secs. IV-V define the reduction/refinement algorithm; Table I and Fig. 4 define termination; Theorems 1-2 prove termination; Table II reports convergence; Table III and Fig. 6 report work and hardware.

### single_path  (role: extends)
mechanism: The seven-stage IEEE-754 double-precision FPA compares operands, aligns the smaller mantissa, performs a 54-bit addition, detects the leading one, rounds/normalizes, and handles zero/denormal/infinity cases. The FPAR retains alignment residue bits, couples sum rounding with residue correction, then detects, normalizes, and emits the residue without increasing the pipeline depth or reducing frequency.
choices:
  pipeline_depth: 7   # p.3
new_choices:
  residue_preserving_output: true — emits r = (a + b) − IEEE754Round(a + b) with the rounded sum   # pp.2-5
slots:
  sig_adder: UNKNOWN
  round: UNKNOWN
  exp: UNKNOWN
  subnormal: full_hardware   # p.3
  align: full_align   # p.3
  norm: single_barrel   # p.3
parameters: IEEE-754 double precision; 64-bit input; 53-bit significand; seven pipeline stages; II = 1   # pp.3-5
results:
| metric | value | unit | technology / device | baseline | condition | page |
| FPA area | 1517 | LUTs | Virtex 6 FPGA | none | post-place-and-route | p.4 |
| FPA frequency | 250 | MHz | Virtex 6 FPGA | none | critical path 3.996 ns | p.4 |
| FPAR area | 2252 | LUTs | Virtex 6 FPGA | FPA: 1517 LUTs | seven stages | p.5 |
| FPAR area overhead | 48% | more area | Virtex 6 FPGA | standard FPA | same frequency and pipeline depth | p.5 |
| FPAR frequency | 250 | MHz | Virtex 6 FPGA | FPA: 250 MHz | critical path 3.999 ns | p.5 |
| latency improvement | 5x | latency improvement | Virtex 6 FPGA | five sequential instructions in Knuth's algorithm | FPAR operation | p.5 |
| total work reduction | 75% | total work reduction | Virtex 6 FPGA | Knuth implementation using 6x FPA area | FPAR uses 1.5x FPA area | p.5 |
errors_and_checks: The FPAR returns the IEEE-754 rounded sum and an exactly representable floating-point residue satisfying r = (a + b) − s.   # p.2
conditions: Residue generation preserves the FPA's seven-stage pipeline and 250 MHz frequency because added computations execute in parallel with existing stages.   # pp.4-5
evidence: Eqs. 1-2 define the residue contract; Fig. 1 and Sec. III describe the FPA/FPAR pipeline; Sec. III-C reports the comparison with software FPAR construction.

## new_families
none

## space_gaps
* streaming_accurate_accumulator needs a reduction-node slot that can name a residue-preserving floating-point adder rather than only a final binary CPA.   # pp.5,11-12
* single_path needs a residue-output choice because the FPAR preserves the exact rounding residue without changing pipeline depth.   # pp.2-5
* streaming_accurate_accumulator needs variable iteration/termination choices because the design usually takes two passes but proves termination through unbounded refinement and Big Tie handling.   # pp.6-10

## open_questions
* The hardware feedback path for failed convergence and the Big Tie mechanism are not implemented in the reported full design; the document says higher-level software can handle them.   # p.12
* The accurate dot-product extension requires a full-width multiplier that encodes each product as two fp64 values, but no multiplier microarchitecture or implementation result is provided.   # p.13
