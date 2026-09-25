---
handle: file_rupley2012#s01
parent: file_rupley2012
citation: Jeff Rupley, AMD Fellow, Chief Architect / Jaguar Core, “JAGUAR” AMD’s Next Generation Low Power x86 Core, August 28, 2012
chapter: “JAGUAR” AMD’s Next Generation Low Power x86 Core
pdf_pages: 0-19
status: out_of_scope
kind: slides
unit_classes: [BINARY_ALU, VEC_SFU]
formats: [AMD64 x86, SSE1-SSSE3, SSE4A, SSE4.1, SSE4.2, AVX, FP16 conversion, single precision, double precision]
authority: slides
pages_read: 20 / 20
---

## summary
The slides describe the AMD Jaguar core, including its integer/FP execution resources, 128b native FP hardware, 256b AVX double pumping, and a new hardware divider. The slides do not disclose the arithmetic recurrences, encodings, topologies, component choices, or comparative arithmetic-unit costs needed to assign a vocabulary family.

## families
none

## taxonomy
none

## primary_sources
none

## new_families
none

## space_gaps
* none

## open_questions
* The new hardware divider is identified as leveraged from Llano, but its divider family, radix, recurrence, latency, and component structure are unspecified.   # p.7
* The integer Mul/Div blocks are shown without multiplier/divider mechanisms or performance parameters.   # p.5
* The 128b native FP hardware performs 4 SP multiplies plus 4 SP adds or 1 DP multiply plus 2 DP adds, but the slides do not state whether the operations are fused or identify their arithmetic families.   # p.8
* The 256b AVX implementation double-pumps 128b hardware, but its cycle schedule and arithmetic-unit organization are unspecified.   # p.8
* The new zero optimizations are named without their detection, gating, or bypass mechanisms.   # p.8
