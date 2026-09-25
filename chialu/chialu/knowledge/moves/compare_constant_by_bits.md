---
id: compare_constant_by_bits
tier: bit
applies_to: [alu, shift]
preserves: bit_exact
check: tb
effect: area-, delay-
sources: [seander_bithacks]
---
# Compare against a constant by bit tests

pattern: a full magnitude comparator against a literal

rewrite: `x >= 2^k` is `|x[W-1:k]`; `x < 2^k` its complement; `x == 2^k-1` is `&x[k-1:0] & ~|x[W-1:k]`; general constants reduce to a few such tests

when: range checks, overflow detection against fixed bounds, exponent range tests
