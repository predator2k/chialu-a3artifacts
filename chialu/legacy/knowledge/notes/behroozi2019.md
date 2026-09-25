---
handle: behroozi2019
citation: S. Behroozi, J. Li, J. Melchert, Y. Kim, "SAADI: A Scalable Accuracy Approximate Divider for Dynamic Energy-Quality Scaling", 24th Asia and South Pacific Design Automation Conference (ASP-DAC), pp. 481-486, 2019
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [unsigned_int32_dividend, unsigned_int16_divisor]
authority: incremental
pages_read: 6 / 6
---

## summary
SAADI performs approximate division by multiplying the normalized dividend by an incremental Taylor-series approximation of the divisor reciprocal. A runtime-selected iteration count trades latency/energy for accuracy, while a design-time normalized width sets the available accuracy range and hardware cost. For n = 8, average accuracy ranges from 92.50% to 99.01% over one to seven cycles.

## families
### approximate_functional  (role: proposes)
mechanism: SAADI normalizes A and B to n-bit a and b, forms |x| = 1-b, and accumulates R̃_t(b) = 1+|x|+|x|²+...+|x|ᵗ. One shared n-bit multiplier generates successive powers with n-bit truncation and finally multiplies a by R̃_t(b); a barrel shifter denormalizes the quotient. The application terminates the recurrence at t to control accuracy/latency/energy. A power-of-two divisor bypasses the recurrence with a shift. # p.2-p.3
choices:
  method: iterative_quasi_convergence   # p.2-p.3
  bias_correction: false   # p.3-p.4
  runtime_quality_scaling: true   # p.1-p.3
new_choices:
  normalized_width_n: Int[4..16:4] — design-time width of normalized operands, multiplier, and reciprocal datapath evaluated in the paper   # p.3-p.5
  reciprocal_order_t: Int[1..n-1:1] — runtime Taylor-series order and total multiplier-cycle latency   # p.2-p.4
slots:
  none
parameters: 32-bit dividend/16-bit divisor; n = 4, 8, 12, or 16 bits; effective t = 1 to n-1 except n = 4 saturation at t = 2; latency = t cycles; one n-bit normalizer/multiplier/barrel shifter, one (n+1)-bit accumulator, and one log2 n-bit adder. # p.3-p.5
results:
| metric | value | unit | technology / device | baseline | condition | page |
| area | 1,199 | µm2 | NanGate 45 nm CMOS / 2019 | none | n = 4 bit | p.5 |
| area | 1,963 | µm2 | NanGate 45 nm CMOS / 2019 | none | n = 8 bit | p.5 |
| area | 3,068 | µm2 | NanGate 45 nm CMOS / 2019 | none | n = 12 bit | p.5 |
| area | 4,872 | µm2 | NanGate 45 nm CMOS / 2019 | none | n = 16 bit | p.5 |
| delay | 1.07 | ns | NanGate 45 nm CMOS / 2019 | none | n = 4 bit | p.5 |
| delay | 1.13 | ns | NanGate 45 nm CMOS / 2019 | none | n = 8 bit | p.5 |
| delay | 1.43 | ns | NanGate 45 nm CMOS / 2019 | none | n = 12 bit | p.5 |
| delay | 1.60 | ns | NanGate 45 nm CMOS / 2019 | none | n = 16 bit | p.5 |
| power | 0.31 | mW | NanGate 45 nm CMOS / 2019 | none | n = 4 bit | p.5 |
| power | 0.59 | mW | NanGate 45 nm CMOS / 2019 | none | n = 8 bit | p.5 |
| power | 1.09 | mW | NanGate 45 nm CMOS / 2019 | none | n = 12 bit | p.5 |
| power | 1.94 | mW | NanGate 45 nm CMOS / 2019 | none | n = 16 bit | p.5 |
| energy per cycle | 0.33 | pJ | NanGate 45 nm CMOS / 2019 | none | n = 4 bit | p.5 |
| energy per cycle | 0.66 | pJ | NanGate 45 nm CMOS / 2019 | none | n = 8 bit | p.5 |
| energy per cycle | 1.56 | pJ | NanGate 45 nm CMOS / 2019 | none | n = 12 bit | p.5 |
| energy per cycle | 3.11 | pJ | NanGate 45 nm CMOS / 2019 | none | n = 16 bit | p.5 |
| minimum accuracy | 85.37 | % | NanGate 45 nm CMOS / 2019 | exact quotient | n = 4 bit | p.5 |
| maximum accuracy | 88.68 | % | NanGate 45 nm CMOS / 2019 | exact quotient | n = 4 bit | p.5 |
| minimum accuracy | 92.50 | % | NanGate 45 nm CMOS / 2019 | exact quotient | n = 8 bit | p.5 |
| maximum accuracy | 99.01 | % | NanGate 45 nm CMOS / 2019 | exact quotient | n = 8 bit | p.5 |
| minimum accuracy | 93.02 | % | NanGate 45 nm CMOS / 2019 | exact quotient | n = 12 bit | p.5 |
| maximum accuracy | 99.93 | % | NanGate 45 nm CMOS / 2019 | exact quotient | n = 12 bit | p.5 |
| minimum accuracy | 93.06 | % | NanGate 45 nm CMOS / 2019 | exact quotient | n = 16 bit | p.5 |
| maximum accuracy | 99.99 | % | NanGate 45 nm CMOS / 2019 | exact quotient | n = 16 bit | p.5 |
| energy per operation | 0.66 | pJ | NanGate 45 nm CMOS / 2019 | 88% target | n = 4 bit, t = 2 | p.5 |
| energy per operation | 4.01 | pJ | NanGate 45 nm CMOS / 2019 | 99% target | n = 8 bit, t = 6 | p.5 |
| energy per operation | 6.26 | pJ | NanGate 45 nm CMOS / 2019 | 99% target | n = 12 bit, t = 4 | p.5 |
| energy per operation | 9.35 | pJ | NanGate 45 nm CMOS / 2019 | 99% target | n = 16 bit, t = 3 | p.5 |
| energy per operation | 10.96 | pJ | NanGate 45 nm CMOS / 2019 | 99.9% target | n = 12 bit, t = 7 | p.5 |
| energy per operation | 18.70 | pJ | NanGate 45 nm CMOS / 2019 | 99.9% target | n = 16 bit, t = 6 | p.5 |
| energy reduction | 57 | % | NanGate 45 nm CMOS / 2019 | n = 16 bit at 99% accuracy | n = 8 bit, six cycles | p.5 |
| MAE | 11.32 | % | NanGate 45 nm CMOS / 2019 | exact quotient | n = 4 bit, maximum accuracy, 2 cycles | p.6 |
| MAE | 14.63 | % | NanGate 45 nm CMOS / 2019 | exact quotient | n = 4 bit, minimum accuracy, 1 cycle | p.6 |
| MAE | 0.99 | % | NanGate 45 nm CMOS / 2019 | exact quotient | n = 8 bit, maximum accuracy, 7 cycles | p.6 |
| MAE | 7.50 | % | NanGate 45 nm CMOS / 2019 | exact quotient | n = 8 bit, minimum accuracy, 1 cycle | p.6 |
| MAE | 0.07 | % | NanGate 45 nm CMOS / 2019 | exact quotient | n = 12 bit, maximum accuracy, 11 cycles | p.6 |
| MAE | 6.98 | % | NanGate 45 nm CMOS / 2019 | exact quotient | n = 12 bit, minimum accuracy, 1 cycle | p.6 |
| MAE | 0.006 | % | NanGate 45 nm CMOS / 2019 | exact quotient | n = 16 bit, maximum accuracy, 15 cycles | p.6 |
| MAE | 6.94 | % | NanGate 45 nm CMOS / 2019 | exact quotient | n = 16 bit, minimum accuracy, 1 cycle | p.6 |
| total delay | 7.91 | ns | NanGate 45 nm CMOS / 2019 | none | n = 8 bit, maximum accuracy | p.6 |
| total energy | 4.67 | pJ | NanGate 45 nm CMOS / 2019 | none | n = 8 bit, maximum accuracy | p.6 |
| total delay | 15.73 | ns | NanGate 45 nm CMOS / 2019 | none | n = 12 bit, maximum accuracy | p.6 |
| total energy | 17.22 | pJ | NanGate 45 nm CMOS / 2019 | none | n = 12 bit, maximum accuracy | p.6 |
| total delay | 24.00 | ns | NanGate 45 nm CMOS / 2019 | none | n = 16 bit, maximum accuracy | p.6 |
| total energy | 46.76 | pJ | NanGate 45 nm CMOS / 2019 | none | n = 16 bit, maximum accuracy | p.6 |
errors_and_checks: Error is (Q̃−Q)/Q, and MAE is evaluated over one million uniformly distributed dividend/divisor pairs. Finite series order and datapath truncation predominantly under-approximate the quotient, so errors are negatively biased. No fault-detection mechanism is provided. # p.3-p.4, p.6
conditions: Each multiplication by |x| ≤ 0.5 removes at least one significant bit, so t beyond n−1 increases latency without improving accuracy. Wider n improves maximum accuracy but increases area/energy. The evaluation assumes 2K/K division with the upper K dividend bits below the divisor to prevent overflow, although SAADI is not restricted to that width ratio. # p.4-p.5
evidence: §3.1-§3.3; Figures 1-5; Tables 1-2; §4.1-§4.3. # p.2-p.6

## new_families
none

## space_gaps
* `approximate_functional.method` needs an `incremental_taylor_reciprocal` value to distinguish SAADI's power-series recurrence from generic `iterative_quasi_convergence`. # p.2-p.3
* `approximate_functional` lacks a slot for the shared multiplier used for reciprocal powers and final quotient multiplication; the multiplier microarchitecture is not disclosed. # p.3
* `approximate_functional` lacks design-time normalized width and runtime iteration-count choices, which jointly define SAADI's accuracy/energy range. # p.3-p.6

## open_questions
* The paper specifies a single-cycle n-bit multiplier but does not identify its multiplier family. # p.3, p.5
* The paper does not identify the microarchitectures of the accumulator adder, exponent-difference adder, normalizer, or barrel shifter. # p.3
