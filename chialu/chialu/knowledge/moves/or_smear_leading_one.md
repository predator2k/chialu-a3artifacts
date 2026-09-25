---
id: or_smear_leading_one
tier: bit
applies_to: [shift, fp]
preserves: bit_exact
check: tb
effect: delay-
sources: [seander_bithacks]
---
# Leading-one by prefix OR smear

pattern: priority encoder / leading-zero detector as a chain

rewrite: `s = v | v>>1 | v>>2 | v>>4 | ...` (log2 W stages) turns the word into a thermometer code; the leading-one mask is `s ^ (s >> 1)`, the count follows by a small popcount or encoder

when: leading-zero count in FP normalization when a log-depth structure beats the lzd tree at the width in hand; round-up-to-power-of-two
