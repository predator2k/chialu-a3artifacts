---
id: abs_by_sign_mask
tier: word
applies_to: [adder, alu, fp]
preserves: bit_exact
check: tb
effect: area-, delay-
sources: [seander_bithacks, richards_1955]
---
# Absolute value without a mux

pattern: `abs = x[W-1] ? -x : x` (a negator plus a full-width mux)

rewrite: `m = {W{x[W-1]}}; abs = (x ^ m) - m` — the XOR row conditionally complements, the subtraction of the mask is a +1 carry-in when negative, so one adder with carry-in replaces negator plus mux

when: sign-magnitude conversions, unsigned-core multipliers/dividers fed by signed operands, absolute-difference units
