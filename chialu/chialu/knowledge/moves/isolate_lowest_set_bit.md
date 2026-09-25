---
id: isolate_lowest_set_bit
tier: bit
applies_to: [shift]
preserves: bit_exact
check: tb
effect: area-, delay-
sources: [seander_bithacks]
---
# Lowest set bit by two's complement

pattern: priority encoder scanning from the LSB

rewrite: `low = v & -v` (equivalently `v & (~v + 1)`): one incrementer and an AND row isolate the lowest set bit, then a small encoder finds its index

when: trailing-zero count, first-free-slot selection, sticky-bit position
