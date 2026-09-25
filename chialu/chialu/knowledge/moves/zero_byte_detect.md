---
id: zero_byte_detect
tier: word
applies_to: [shift, alu]
preserves: bit_exact
check: tb
effect: area-, delay-
sources: [seander_bithacks]
---
# Zero sub-word detection in parallel

pattern: per-lane zero detectors and an OR

rewrite: `~(((v & 0x7F7F...) + 0x7F7F...) | v | 0x7F7F...)` marks each zero byte in its top bit with one adder row; the lane mask then drives the SIMD zero/flag logic

when: sub-word SIMD flag generation, string/byte units; a plain OR-reduce per lane is smaller when only a global zero flag is needed
