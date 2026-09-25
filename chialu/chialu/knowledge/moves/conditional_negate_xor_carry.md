---
id: conditional_negate_xor_carry
tier: word
applies_to: [adder, alu, mul, fp]
preserves: bit_exact
check: tb
effect: area-, delay-
sources: [seander_bithacks, bewick1994]
---
# Conditional negate as XOR plus carry-in

pattern: `r = f ? -v : v` written with a negator and a mux

rewrite: `m = {W{f}}; r = (v ^ m) + f` — complement under the flag and add the flag as carry-in; when the value feeds an adder anyway, fold the `+f` into that adder's carry-in and keep only the XOR row

when: Booth negative partial products (complement plus a correction bit that joins the tree), effective subtraction in FP significand paths, two's-complement sign handling
