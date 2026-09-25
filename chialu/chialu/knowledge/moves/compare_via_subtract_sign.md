---
id: compare_via_subtract_sign
tier: word
applies_to: [adder, alu]
preserves: bit_exact
check: tb
effect: area-
sources: [zimmermann1997, seander_bithacks]
---
# Compare as the sign of a difference

pattern: separate magnitude comparators for lt/eq/gt next to an adder/subtractor

rewrite: compute `d = a - b` once (the ALU's subtractor); `lt = d[W] ^ overflow` for signed (or the borrow-out for unsigned), `eq = ~|d[W-1:0]`, `gt = ~lt & ~eq`

when: ALU compare/min/max ops, saturation detection, sort/min/max networks; keep a dedicated prefix comparator only when the compare is on the critical path and the subtractor is not
