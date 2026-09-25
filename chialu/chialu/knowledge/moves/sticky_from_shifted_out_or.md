---
id: sticky_from_shifted_out_or
tier: bit
applies_to: [fp]
preserves: bit_exact
check: tb
effect: delay-
sources: [bewick1994, muller_2018]
---
# Sticky bit without a wide OR after the shifter

pattern: OR of the bits shifted out, taken after the alignment shift

rewrite: compute the sticky from the shift amount and the operand directly: a mask of the low `sh` bits ANDed with the operand, OR-reduced, in parallel with the shifter (or the trailing-zero count compared with the shift amount)

when: FP alignment and normalization rounding paths where the sticky OR sits on the critical path
