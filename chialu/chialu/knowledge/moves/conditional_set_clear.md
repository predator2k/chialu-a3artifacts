---
id: conditional_set_clear
tier: bit
applies_to: [shift, alu]
preserves: bit_exact
check: tb
effect: area-
sources: [seander_bithacks]
---
# Conditional set or clear of masked bits

pattern: `w = f ? (w | m) : (w & ~m)`

rewrite: `w = w ^ ((-f ^ w) & m)` (branch-free); in RTL this is one AND-XOR row driven by the replicated flag

when: flag/status assembly, sticky/guard bit handling, mask-driven lane enables
