---
id: sign_from_msb
tier: bit
applies_to: [adder, shift, fp]
preserves: bit_exact
check: tb
effect: area-, delay-
sources: [seander_bithacks]
---
# Sign as the top bit

pattern: a comparator `x < 0` or `x >= 0` on a two's-complement word

rewrite: read the sign bit directly: `sign = x[W-1]`; for `x <= 0` use `x[W-1] | ~|x`

when: always for two's complement; synthesis usually finds it, but a comparator written against a constant in a wider context (`$signed(x) < 0` with mixed widths) can survive as a subtractor
