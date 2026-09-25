---
handle: harris_1997
citation: Harris, Oberman, Horowitz, "SRT Division Architectures and Implementations", 13th IEEE Symposium on Computer Arithmetic, 1997
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [fp32, fp64]
authority: survey
pages_read: 18-25 / 8
---

## summary
The paper compares radix-2/radix-4 SRT divider architectures, overlap schemes, and static CMOS/dual-rail domino implementations for floating-point significands. The results show modest performance differences among reasonable architectures but a 1.5-1.7 times speedup from dual-rail domino over comparable static designs. # p.24-25

## families
### srt_radix2  (role: compares)
mechanism: Each iteration selects a quotient digit from {-1,0,1} using approximations of the shifted partial remainder and divisor, then forms the next partial remainder with a carry-save subtraction. Cascaded radix-2 stages increase the quotient bits retired per cycle; quotient selection, remainder formation, both operations, or only the critical high-order remainder bits can be overlapped. # p.19-22
choices:
  residual_form: carry_save  # p.19-20
  quotient_prediction: true  # p.20-21
new_choices:
  overlap_scheme: {none, quotient_selection, remainder_formation, quotient_and_remainder, hybrid} — identifies which consecutive-stage operations are computed speculatively # p.20-22
  circuit_style: {static_cmos_standard_cell, skew_tolerant_dual_rail_domino} — selects the compared circuit implementation # p.22-25
  quotient_digit_set: {-1,0,1} — fixes the radix-2 signed-digit set # p.19
slots:
  digit_select: qds_table  # p.19-20
parameters: n=24 for single precision; n=53 for double precision; b=1 bit per radix-2 stage; overlap s=2 or s=3 in the recommended examples; latency k=n/b iterations before cascading # p.19, p.22, p.25
results:
| metric | value | unit | technology / device | baseline | condition | page |
| speed | 1.7 | times as fast | 1 µm (drawn) HP-CMOS26B, 1997 | static hybrid overlapped radix-2 | dual-rail domino hybrid overlapped radix-2 | p.24 |
| area | 1.6 | times as much area | 1 µm (drawn) HP-CMOS26B, 1997 | static hybrid overlapped radix-2 | dual-rail domino hybrid overlapped radix-2 | p.24 |
| delay per bit | 4-5 | FO4 | 1 µm (drawn) HP-CMOS26B, 1997 | none | reasonable architectures, including hybrid radix-2 s=2 and quotient-selection-overlapped radix-2 s=3 | p.25 |
| core cost | approximately 3M | λ2 per bit/cycle | 1 µm (drawn) HP-CMOS26B, 1997 | none | reasonable architectures | p.25 |
| core cost | 6000 | transistors per bit/cycle | 1 µm (drawn) HP-CMOS26B, 1997 | none | reasonable architectures | p.25 |
errors_and_checks: No error/fault metrics are reported; the analysis computes an n-bit quotient, while measured core area excludes normalization/rounding/exponent handling. # p.19, p.23-24
conditions: Overlap beyond s=3 is limited by exponential growth in quotient-selection blocks. Hybrid overlap has the lowest analyzed latency and fewer speculative CSAs than full remainder overlap, but other quotient-selection-overlapped designs remain within one CSA/buffer delay. # p.22
evidence: §2.1-2.4, Figs. 1-7, Tables 1-2, Fig. 8, §4-5, p.18-25

### srt_high_radix  (role: analyzes)
mechanism: Practical higher-radix dividers cascade radix-2 or radix-4 stages because quotient-selection delay/area and divisor-multiple generation limit realistic individual stages to radix 2 or 4. Radix-4 uses minimally or maximally redundant signed-digit sets and a carry-save partial remainder; overlapping consecutive low-radix stages produces more quotient bits per cycle. # p.18-22
choices:
  radix: 4  # p.19
  digit_redundancy: minimal  # p.19
  digit_redundancy: maximal  # p.19
  overlapped_stages: 2  # p.20-22
  overlapped_stages: 3  # p.22, p.25
new_choices:
  base_stage_radix: {2,4} — identifies the low-radix stage used to construct the effective higher-radix divider # p.18-22
  overlap_scheme: {none, quotient_selection, remainder_formation, quotient_and_remainder, hybrid} — identifies the speculative overlap organization # p.20-22
  circuit_style: {static_cmos_standard_cell, skew_tolerant_dual_rail_domino} — selects the compared circuit implementation # p.22-25
slots:
  digit_select: qds_table  # p.19, p.22-24
parameters: radix-4 minimally redundant digit set {-2,-1,0,1,2}; radix-4 maximally redundant digit set {-3,-2,-1,0,1,2,3}; practical overlap s=2 or possibly s=3 # p.19, p.22
results:
| metric | value | unit | technology / device | baseline | condition | page |
| quotient-selection speed | 20% | faster | UNKNOWN, UNKNOWN | minimally redundant radix-4 | maximally redundant radix-4 quotient selection, reported from [10] | p.19 |
| quotient-selection area | 50% | smaller | UNKNOWN, UNKNOWN | minimally redundant radix-4 | maximally redundant radix-4 quotient selection, reported from [10] | p.19 |
| speed | 1.5 | times as fast | 1 µm (drawn) HP-CMOS26B, 1997 | fastest static design | fastest domino design | p.24 |
| circuit-style speedup | 1.5-1.7 | times | 1 µm (drawn) HP-CMOS26B, 1997 | similar static CMOS architecture | dual-rail domino | p.25 |
| delay per bit | 4-5 | FO4 | 1 µm (drawn) HP-CMOS26B, 1997 | none | reasonable architectures, including hybrid maximally redundant radix-4 s=2 | p.25 |
errors_and_checks: No error/fault metrics are reported; maximally redundant radix-4 requires precomputation of the 3x divisor multiple, whose setup latency is excluded from Design E delay. # p.19, p.24
conditions: Quotient-selection table delay grows linearly with radix and area grows quadratically, while radix-8 and higher require impractical divisor multiples. Radix-4 domino quotient selection also pays a larger monotonic 1-hot PLA area cost. # p.19, p.22-25
evidence: §2.2-2.4, Tables 1-2, §3-5, Fig. 8, Tables 3-4, p.19-25

## new_families
none

## space_gaps
* `srt_radix2` lacks an overlap-scheme choice for none/quotient-selection/remainder-formation/combined/hybrid organizations. # p.20-22
* `srt_radix2` and `srt_high_radix` lack a circuit-style choice for static CMOS versus skew-tolerant dual-rail domino. # p.22-25
* `srt_high_radix` lacks a base-stage-radix choice for higher-radix dividers composed from radix-2/radix-4 stages. # p.18-22

## open_questions
* Table 3 values are not legible in the supplied document text, so the exact architecture/radix assignments for Designs A-E must not be inferred.
* The static-design process technology/year underlying the normalized comparisons is not stated independently of the HP-CMOS26B comparison basis.
