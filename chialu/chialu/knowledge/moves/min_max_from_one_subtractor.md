---
id: min_max_from_one_subtractor
tier: word
applies_to: [adder, alu]
preserves: bit_exact
check: tb
effect: area-
sources: [seander_bithacks]
---
# Min and max from one difference

pattern: two comparators, or a comparator plus two muxes

rewrite: `lt` from one subtraction (compare_via_subtract_sign), then `min = lt ? a : b`, `max = lt ? b : a` — one subtractor and two mux rows; branch-free form `min = b ^ ((a ^ b) & {W{lt}})` when the mux maps worse than AND/XOR

when: min/max ops in an ALU, clamping, sorting cells
