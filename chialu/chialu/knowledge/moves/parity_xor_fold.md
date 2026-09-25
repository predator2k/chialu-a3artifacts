---
id: parity_xor_fold
tier: bit
applies_to: [checker, shift]
preserves: bit_exact
check: tb
effect: delay-
sources: [seander_bithacks]
---
# Parity by log-depth XOR folding

pattern: a linear XOR chain over W bits

rewrite: `v ^= v >> W/2; v ^= v >> W/4; ...; p = v[0]` — a balanced XOR tree of depth log2 W

when: parity prediction and parity checkers, two-rail comparators; the folded form is what synthesis should reach, the chain is what a `for` loop with `^=` often gives it
