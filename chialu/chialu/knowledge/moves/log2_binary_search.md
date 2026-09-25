---
id: log2_binary_search
tier: bit
applies_to: [shift, sfu, fp]
preserves: bit_exact
check: tb
effect: delay-
sources: [seander_bithacks]
---
# Integer log2 by binary search

pattern: linear scan for the most significant set bit

rewrite: `if (|v[W-1:W/2]) {r[k]=1; v = v >> W/2}` repeated log2 W times: each stage tests the upper half, shifts, and sets one result bit — a fixed log-depth structure

when: leading-zero count, exponent extraction in int-to-float conversion, log2 range reduction
