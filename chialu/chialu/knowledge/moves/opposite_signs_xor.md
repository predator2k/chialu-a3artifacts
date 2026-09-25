---
id: opposite_signs_xor
tier: bit
applies_to: [adder, fp]
preserves: bit_exact
check: tb
effect: area-
sources: [seander_bithacks]
---
# Opposite signs by XOR

pattern: `(x < 0) != (y < 0)` or `(x ^ y) < 0`

rewrite: `x[W-1] ^ y[W-1]`

when: sign tests on two operands before an effective add/sub decision (FP effective-operation, saturation direction)
