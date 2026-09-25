---
id: mod_pow2_by_mask
tier: bit
applies_to: [adder, div, shift]
preserves: bit_exact
check: tb
effect: area-, delay-
sources: [seander_bithacks]
---
# Modulo 2^s by masking

pattern: `v % (1 << s)` written with a remainder operator

rewrite: `v & ((1 << s) - 1)` — the low s bits

when: any modulus that is a power of two; also the quotient `v >> s`
