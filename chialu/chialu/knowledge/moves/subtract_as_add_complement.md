---
id: subtract_as_add_complement
tier: word
applies_to: [adder, alu]
preserves: bit_exact
check: tb
effect: area-
sources: [richards_1955, zimmermann1997]
---
# One adder for add and subtract

pattern: separate adder and subtractor selected by a mux, or `op ? a - b : a + b`

rewrite: `b2 = b ^ {W{sub}}; r = a + b2 + sub` — one XOR row and the carry-in turn the adder into a subtractor

when: ALUs with add/sub/compare, FP significand add/sub, any unit that instantiates both operators
