---
id: power_of_two_test
tier: bit
applies_to: [shift, fp]
preserves: bit_exact
check: tb
effect: area-, delay-
sources: [seander_bithacks]
---
# Power-of-two test without a popcount

pattern: `popcount(v) == 1`

rewrite: `(v & (v - 1)) == 0 && v != 0` — one decrementer, an AND row, and a zero detect

when: normalization checks, exact-power detection in log/exp units, alignment tests
