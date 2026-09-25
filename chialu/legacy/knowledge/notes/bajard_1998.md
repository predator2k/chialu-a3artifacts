---
handle: bajard_1998
citation: Bajard, Didier, Kornerup, "An RNS Montgomery Modular Multiplication Algorithm", IEEE Transactions on Computers, 1998
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [RNS, MRS]
authority: incremental
pages_read: 6 (pp.234-239) / 6
---

## summary
The document proposes Montgomery modular multiplication using mixed-radix digits and two RNS bases for very large operands. The algorithm maps to a nearest-neighbor processor ring and supports time multiplexing when fewer processors than moduli are available. # pp.234-238

## families
### rns_montgomery_crypto  (role: proposes)
mechanism: The algorithm represents B, N, and R in a primary RNS base and an auxiliary RNS base, while A supplies mixed-radix digits. Each digit determines q_i so the intermediate value is divisible exactly by m_i; division removes one primary-base residue while the auxiliary residues preserve the result. A second application with the bases permuted recovers AB mod N. The implementation overlaps RNS-to-MRS conversion with modular operations on a nearest-neighbor processor ring. # pp.235-238
choices:
  channel_count_per_base: n [outside domain]   # p.235
  channel_width: 9 to 10 [outside domain]   # p.238
  base_extension: RNS-to-MRS conversion with an auxiliary RNS base [outside domain]   # pp.235-237
new_choices:
  processor_mapping: {ring_n_processors, time_multiplexed_p_processors} — selects the physical processor count and scheduling arrangement   # pp.236-238
  input_A_representation: {MRS, RNS_with_overlapped_conversion} — determines whether the triangular D-task conversion is required   # pp.235-237
  output_recovery: second_application_with_permuted_bases — converts ABM^-1 mod N into AB mod N   # p.235
slots:
  none
parameters: n moduli per base; p processors with p<n permitted and p dividing n for the regular mapping; k=n div p; moderately sized moduli suggested at 9 to 10 bits; n suggested to be in the order of 80 for cryptographic security requirements. # pp.236-238
results:
| metric | value | unit | technology / device | baseline | condition | page |
| algorithm time | O(n) | simple residue-operation times | UNKNOWN; year 1998 | none | O(n) processors | p.234 |
| latency | 4n - 1 | cycles | UNKNOWN; year 1998 | none | ring of n processors | p.236 |
| initiation interval | 3n | cycles | UNKNOWN; year 1998 | none | pipelined ring of n processors | p.236 |
| schedule time τ | 5kn/2 + 3n/2 - k - 1 | cycles | UNKNOWN; year 1998 | none | p processors, n mod p = 0, k = n div p | p.238 |
| processor utilization lower bound | 62.5 | % | UNKNOWN; year 1998 | none | asymptotic p=n | p.238 |
| processor utilization upper bound | 100 | % | UNKNOWN; year 1998 | none | p=1 | p.238 |
| single-processor time | O(n²) | simple residue-operation times | UNKNOWN; year 1998 | none | p=1 | p.238 |
errors_and_checks: Theorem 1 establishes R ≡ ABM^-1 mod N and R < 2N under its operand/modulus assumptions; no concurrent fault check is described. # p.236
conditions: The method targets repeated modular multiplication with very large operands and exploits parallel carry-free RNS arithmetic. # pp.234-235 The bases require pairwise relatively prime moduli, the auxiliary moduli must also be relatively prime to the primary moduli, and gcd(N,M)=1. # pp.234-236 The scheduling formula assumes p divides n, and constant task time assumes simple modular operations on moderately sized moduli, possibly implemented by table lookup. # p.238 The paper does not claim superiority over a similarly pipelined ordinary high-radix implementation because no comparison design was available, and it states that known high-radix simplifications do not apply. # p.238
evidence: Abstract; §§2-3; Theorem 1; §4, Algorithms 1-2, Figures 1-3, Tables 1-2; §5.

### rns_channel_arithmetic  (role: instantiates)
mechanism: Addition and multiplication are performed componentwise modulo each m_j. Exact division by m_i retains every residue except the residue modulo m_i and multiplies the retained residues by the corresponding modular inverse. Each ring processor stores constants/tables for one or more moduli and performs modular addition/multiplication locally. # pp.234-238
choices:
  modulus_form: generic   # pp.234-235
  channel_width_n: 9 to 10 [outside domain]   # p.238
new_choices:
  none
slots:
  modular_adder: UNKNOWN   # p.238
parameters: Pairwise relatively prime moduli; n channels; 9 to 10-bit moduli suggested; constants for m_j are assigned to processor j mod p when p<n. # pp.234,238
results:
| metric | value | unit | technology / device | baseline | condition | page |
| per-channel modular operation time | constant | simple residue-operation times | UNKNOWN; year 1998 | none | moderately sized moduli, possibly using table lookup | p.238 |
errors_and_checks: none
conditions: Comparison/division/modular multiplication are identified as difficult RNS operations; the proposed mixed-radix method addresses modular multiplication rather than general comparison or division. # pp.234-235
evidence: §2; §3.1; §4; §5.

## new_families
none

## space_gaps
* `rns_montgomery_crypto.base_extension` lacks a mixed-radix conversion with auxiliary-base residue preservation value. # pp.235-237
* `rns_montgomery_crypto.channel_width` excludes the suggested 9 to 10-bit moduli. # p.238
* `rns_montgomery_crypto.channel_count_per_base` ends at 64, while the document suggests n in the order of 80. # p.238
* `rns_montgomery_crypto` lacks choices for ring topology/time-multiplexed processor count and the permuted-base recovery pass. # pp.235-238

## open_questions
* The supplied text corrupts part of Theorem 1's bound on A and omits or garbles Algorithm 1, so the exact A bound and full recurrence cannot be transcribed safely. # pp.235-236
* The citation gives IEEE Transactions on Computers, 1998, while the document footer prints © 1997 IEEE; the publication venue/year requires bibliographic verification. # pp.234-239
* The numeric body of Table 2 is absent from the supplied extraction, so only the stated 62.5% and 100% utilization bounds are recorded. # p.238
