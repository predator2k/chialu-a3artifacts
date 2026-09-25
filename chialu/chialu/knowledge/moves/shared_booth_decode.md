---
id: shared_booth_decode
tier: structural
applies_to: [mul]
preserves: bit_exact
check: tb
effect: area-
sources: [bewick1994]
---
# One Booth decoder per row, shared selects

pattern: per-bit Booth logic replicated across the multiplicand width

rewrite: decode each 3-bit group once into (neg, one, two) selects and fan them out; the per-bit cell reduces to a 2:1 select plus a conditional XOR

when: Booth-recoded multipliers of any radix
