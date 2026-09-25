---
id: round_up_pow2_smear
tier: bit
applies_to: [shift, fp]
preserves: bit_exact
check: tb
effect: area-
sources: [seander_bithacks]
---
# Round up to a power of two by smearing

pattern: a leading-one detector plus a decoder

rewrite: `v = v - 1; v |= v >> 1; v |= v >> 2; ...; v = v + 1` — OR smear then increment

when: buffer/size rounding, exponent alignment in fixed-to-float
