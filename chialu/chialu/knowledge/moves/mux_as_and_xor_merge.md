---
id: mux_as_and_xor_merge
tier: bit
applies_to: [adder, alu, shift]
preserves: bit_exact
check: tb
effect: area-
sources: [seander_bithacks]
---
# Bit merge by mask instead of a mux

pattern: per-bit 2:1 mux `r = m ? b : a` on wide words

rewrite: `r = a ^ ((a ^ b) & m)` — three gates per bit, and the `a ^ b` term is often already present (e.g. as the propagate signal of an adder)

when: when the XOR of the two sources already exists in the datapath; otherwise a mux cell is usually smaller
