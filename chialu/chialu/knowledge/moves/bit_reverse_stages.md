---
id: bit_reverse_stages
tier: bit
applies_to: [shift]
preserves: bit_exact
check: tb
effect: area-
sources: [seander_bithacks]
---
# Bit reversal by log-depth swaps

pattern: a full crossbar or a loop of single-bit moves

rewrite: swap adjacent bits, then pairs, nibbles, bytes, halves (log2 W stages of masked shift-swap), or, in RTL, a pure wiring permutation when the reversal is static

when: FFT/bit-reversed addressing, reflected codes, mirrored shifters; a static reversal is free wiring and should never be logic
