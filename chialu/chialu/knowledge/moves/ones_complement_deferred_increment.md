---
id: ones_complement_deferred_increment
tier: word
applies_to: [adder, mul, fp]
preserves: bit_exact
check: tb
effect: area-, delay-
sources: [bewick1994, ercegovac_2004]
---
# Deferred +1 of a two's-complement negation

pattern: `-x = ~x + 1` computed fully before use

rewrite: use `~x` and inject the `+1` into the carry-in (or as an extra bit) of the adder or compressor that consumes it

when: negative Booth partial products (the correction bits enter the tree as constants), subtraction in FP significand paths, any negate-then-add
