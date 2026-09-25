---
handle: kawamura_2000
citation: Kawamura, Koike, Sano, Shimbo, "Cox-Rower Architecture for Fast Parallel Montgomery Multiplication", EUROCRYPT (LNCS 1807), 2000
actual_citation: same
status: ok
kind: paper
unit_classes: [other]
formats: [int1024, RNS, radix_2^32]
authority: landmark
pages_read: 523–538 / 16
---

## summary
The paper proposes an RNS Montgomery multiplication algorithm whose two base extensions use an approximate reduction factor computed by addition alone (pp.528–531). The Cox-Rower Architecture executes residue-channel modular multiply-accumulates in parallel and provides radix-to-RNS/RNS-to-radix conversion for a standard RSA interface (pp.531–534).

## families
### rns_montgomery_crypto  (role: proposes)
mechanism: Two relatively prime RNS bases a and b represent operands across independent channels. Montgomery reduction uses B as R, extends t from b to a with α=0, computes w in base a, and extends w back to a∪b with α>0. The recursive base extension accumulates truncated q-bit estimates of ξi/2^r in the Cox unit while n Rower modular multiplier-accumulators compute the residue outputs in parallel (pp.526–532).
choices:
  channel_count_per_base: 33   # p.534
  channel_width: 32   # p.534
  base_extension: kawamura_approximate   # pp.528–531
new_choices:
  none
slots:
  none
parameters: N is 1024 bit; r=32; n=33; q=7; α=1/2; Cox unit is a 7 bit adder; each Rower is a single-precision modular multiplier-and-accumulator (pp.531, 534).
results:
| metric | value | unit | technology / device | baseline | condition | page |
| operations per MM, BE | 2n(n + 2) | mod-mul | UNKNOWN; 2000 | none | algorithm MM | p.535 |
| operations per MM, others | 5n | mod-mul | UNKNOWN; 2000 | none | algorithm MM | p.535 |
| MM calls per EXP | 3nr/2 + 2 | – | UNKNOWN; 2000 | none | binary exponentiation | p.535 |
| exponentiation throughput | 890 | kbit/sec | 0.35 – 0.18 µm CMOS; 2000 | none | 1024-bit full exponentiation, r=32, n=33, f=100MHz | p.534 |
| exponentiation throughput | 1.1 | Mbps | 0.35 – 0.18 µm CMOS; 2000 | binary exponentiation at 890 kbit/sec | 4-bit window method, approximately 4 kByte RAM increase | p.534 |
| total RAM | 1k | Byte | UNKNOWN; 2000 | none | binary exponentiation, r=32, n=33 | p.535 |
| total ROM | 32k | Byte | UNKNOWN; 2000 | none | binary exponentiation, r=32, n=33 | p.535 |
| RAM per Rower unit | 32 | Byte | UNKNOWN; 2000 | none | binary exponentiation, r=32, n=33 | p.535 |
| ROM per Rower unit | 970 | Byte | UNKNOWN; 2000 | none | binary exponentiation, r=32, n=33 | p.535 |
errors_and_checks: The α=0 extension returns t or t+B; either result preserves the required Montgomery congruence. The α>0 extension is error-free under Theorem 3. No fault-detection mechanism is reported (pp.530–531, 537–538).
conditions: Theorem 3 requires gcd(N,B)=1, gcd(A,B)=1, 0≤∆≤α<1, 4N/(1−∆)≤B, and 2N/(1−α)≤A (pp.530–531). The output satisfies w≡xyB^−1 (mod N) and w<2N for x,y<2N, which permits repeated multiplication for exponentiation (p.530). The reported performance is a rough estimate rather than a VLSI measurement (pp.534–535).
evidence: §§2.3–5.2; Figs.1–5; Tables 1–2; Theorems 1–3; Appendices A–C.

### rns_channel_arithmetic  (role: instantiates)
mechanism: Each Rower independently performs modular addition/multiplication for one residue element. The Cox unit broadcasts one-bit reduction-factor decisions while the Rower units evaluate cj=(cj−1+fjgj+dj) mod mi. The selected moduli are pairwise relatively prime and close to 2^32 (pp.525, 529, 531, 534).
choices:
  modulus_form: generic   # pp.525, 534
  channel_width_n: 32   # p.534
new_choices:
  none
slots:
  none
parameters: n=33 Rower units; each unit is a 32-bit modular multiplier-and-accumulator; two bases a and b are used (pp.531, 534).
results: none
errors_and_checks: none
conditions: Base elements must be pairwise relatively prime, and gcd(A,B)=1 is required (pp.525, 530). The parameter search found bases with ε<2^−22 for n=33 (p.534).
evidence: §§2.1, 3.3, 4.1, 5.1; Figs.2 and 4.

### rns_reverse_converter  (role: extends)
mechanism: The RNS-to-radix conversion expands the CRT-derived expression x=ΣξiAi−kA into radix-2^r rows. Rower units accumulate the rows in parallel, preserve carries during the n summation steps, and then propagate carries from Rower 1 through Rower n. The same hardware performs a final subtraction when the Montgomery result exceeds N (p.533).
choices:
  algorithm: crt   # p.533
  moduli_count: 33   # p.534
  implementation: adder_based   # pp.531–533
new_choices:
  none
slots:
  none
parameters: radix 2^r; r=32 and n=33 in the evaluated configuration; n summation steps, n carry-propagation steps, and n final-correction steps (pp.533–534).
results:
| metric | value | unit | technology / device | baseline | condition | page |
| RNS-to-radix operations | 2n² + n | mod-mul | UNKNOWN; 2000 | none | algorithm EXP | p.535 |
| final-correction operations | n² | subtraction | UNKNOWN; 2000 | none | algorithm EXP | p.535 |
| summation latency | n | steps | UNKNOWN; 2000 | none | n Rower units | p.533 |
| carry-propagation latency | n | steps | UNKNOWN; 2000 | none | after summation | p.533 |
| final-correction latency | n | steps | UNKNOWN; 2000 | none | result larger than N | p.533 |
errors_and_checks: The conversion is error-free when Theorem 1 conditions hold; no fault checker is reported (pp.530, 533).
conditions: Theorem 1 requires 0≤n(εm+δm)≤α<1 and 0≤x<(1−α)M (p.530). A final correction is required because a Montgomery result may exceed N (p.533).
evidence: §4.3; Eq.12; Fig.4; Table 1.

## new_families
### radix_to_rns_converter  (domain: redundant: residue number systems, closest: rns_reverse_converter, why_not: rns_reverse_converter only covers residue-to-binary conversion)
mechanism: A radix-2^r operand x=(x(n−1),…,x(0)) is converted by computing x[mi]=Σx(j)(2^rj[mi]) mod mi independently for every residue channel. Constants 2^rj[mi] are precomputed, so n parallel Rower units finish the conversion in n steps (pp.533–534).
choices: radix_digit_width_bits: Int[1..64:1]; residue_channels: Int[1..64:1]; constants: {precomputed}; channel_execution: {parallel}
results:
| metric | value | unit | technology / device | baseline | condition | page |
| conversion latency | n | steps | UNKNOWN; 2000 | none | n units operating in parallel | p.533 |
| radix-to-RNS operations | n² | mod-mul | UNKNOWN; 2000 | none | algorithm EXP | p.535 |
evidence: §4.4; Eq.1-derived conversion formula; Table 1.

## space_gaps
none

## open_questions
* The exact ai and bi moduli are not listed; the paper reports only that a computer search found suitable bases with ε<2^−22 (p.534).
* The performance remains a rough estimate because a VLSI design and detailed performance evaluation remain future work (p.535).
* The paper does not state whether the performance estimate assumes the relaxed modular reduction y≡x (mod mi), y<2^r described in the conclusion (p.535).
