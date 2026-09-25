---
id: swap_by_xor
tier: bit
applies_to: [shift, fp]
preserves: bit_exact
check: tb
effect: area-
sources: [seander_bithacks]
---
# Operand swap without a temporary

pattern: two muxes selecting `(a, b)` or `(b, a)` by a flag

rewrite: `t = (a ^ b) & {W{swap}}; a' = a ^ t; b' = b ^ t` — one XOR row shared by both outputs when the muxes map worse than XOR/AND

when: FP operand swap after the exponent-difference sign; sorting cells; usually a wash against mux cells, worth trying when `a ^ b` exists already
