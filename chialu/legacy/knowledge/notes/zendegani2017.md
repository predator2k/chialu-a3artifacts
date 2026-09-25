---
handle: zendegani2017
citation: R. Zendegani, M. Kamal, M. Bahadori, A. Afzali-Kusha, M. Pedram, "RoBA Multiplier: A Rounding-Based Approximate Multiplier for High-Speed yet Energy-Efficient Digital Signal Processing", IEEE Transactions on VLSI Systems, vol. 25, no. 2, pp. 393-401, 2017
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [uint8, int8, uint16, int16, uint24, int24, uint32, int32]
authority: incremental
pages_read: 9 / 9
---

## summary
The paper proposes RoBA, an approximate signed/unsigned multiplier that rounds each operand to its nearest power of two and omits the product of both rounding residuals. Three implementations provide unsigned operation, signed operation with exact negation, and signed operation with approximate negation. A 32-bit postlayout comparison and sharpening/smoothing experiments quantify hardware savings and accuracy.

## families
### operand_rounding  (role: proposes)
mechanism: RoBA rewrites multiplication as `(Ar − A)(Br − B) + ArB + BrA − ArBr` and omits `(Ar − A)(Br − B)`. The remaining products use shifts because `Ar` and `Br` are powers of two. Three barrel shifters generate `ArB`, `BrA`, and `ArBr`; an adder and simplified subtractor combine them. Signed implementations operate on absolute values and restore the output sign. S-RoBA performs exact two's-complement negation, while AS-RoBA omits the increment during negation. U-RoBA removes sign detection/restoration. # pp.2-4
choices:
  rounding: nearest_pow2   # pp.2-3
new_choices:
  sign_handling: {unsigned, exact_negation, approximate_negation} — selects U-RoBA, S-RoBA, or AS-RoBA hardware # p.4
  minus_one_bypass: Bool — detects an AS-RoBA operand of `−1` and returns the negated other operand to avoid the 100% maximum error # p.4
slots:
  none
parameters: generic `n`-bit operands; error-rate evaluation at 8, 16, 24, and 32 bits; hardware comparison at 32 bits; three `n`-input/`2n`-output barrel shifters; one `2n`-bit Kogge-Stone adder # pp.3-6
results:
| metric | value | unit | technology / device | baseline | condition | page |
| delay | about 22% lower | % | NanGate 45-nm (result year 2017) | DSM8 | 32-bit U-RoBA postlayout, 1.1 V | p.6 |
| delay | about 15% lower | % | NanGate 45-nm (result year 2017) | DRUM6 | 32-bit U-RoBA postlayout, 1.1 V | p.6 |
| energy | about 5% lower | % | NanGate 45-nm (result year 2017) | DSM8 | 32-bit U-RoBA postlayout, 1.1 V | p.6 |
| energy | about 13% lower | % | NanGate 45-nm (result year 2017) | DRUM6 | 32-bit U-RoBA postlayout, 1.1 V | p.6 |
| EDP | about 26% lower | % | NanGate 45-nm (result year 2017) | DSM8 | 32-bit U-RoBA postlayout, 1.1 V | p.6 |
| EDP | about 25% lower | % | NanGate 45-nm (result year 2017) | DRUM6 | 32-bit U-RoBA postlayout, 1.1 V | p.6 |
| power | about 18% higher | % | NanGate 45-nm (result year 2017) | DSM8 | 32-bit U-RoBA postlayout, 1.1 V | p.6 |
| area | about 57% higher | % | NanGate 45-nm (result year 2017) | DRUM6 | 32-bit U-RoBA postlayout, 1.1 V | p.6 |
| PDA | about 51% higher | % | NanGate 45-nm (result year 2017) | DRUM6 | 32-bit U-RoBA postlayout, 1.1 V | p.6 |
| delay | on average 3.4% larger | % | NanGate 45-nm (result year 2017) | Baugh-Wooley multiplier | 32-bit S-RoBA postlayout, 1.1 V | p.6 |
| power | about 47% lower | % | NanGate 45-nm (result year 2017) | Baugh-Wooley multiplier | 32-bit S-RoBA postlayout, 1.1 V | p.6 |
| area | about 32% lower | % | NanGate 45-nm (result year 2017) | Baugh-Wooley multiplier | 32-bit S-RoBA postlayout, 1.1 V | p.6 |
| energy | about 45% lower | % | NanGate 45-nm (result year 2017) | Baugh-Wooley multiplier | 32-bit S-RoBA postlayout, 1.1 V | p.6 |
| EDP | about 43% lower | % | NanGate 45-nm (result year 2017) | Baugh-Wooley multiplier | 32-bit S-RoBA postlayout, 1.1 V | p.6 |
| PDA | about 63% lower | % | NanGate 45-nm (result year 2017) | Baugh-Wooley multiplier | 32-bit S-RoBA postlayout, 1.1 V | p.6 |
| average sharpening PSNR | more than 43 | dB | UNKNOWN (result year 2017) | exact-multiplier output | positive coefficients, seven images | p.7 |
| average sharpening MSSIM | more than 0.99 | ratio | UNKNOWN (result year 2017) | exact-multiplier output | positive coefficients, seven images | p.7 |
| sharpening PSNR | more than 20 | dB | UNKNOWN (result year 2017) | exact-multiplier output | negative coefficients, all reported cases | p.7 |
| sharpening MSSIM | more than 0.91 | ratio | UNKNOWN (result year 2017) | exact-multiplier output | negative coefficients, all reported cases | p.7 |
| smoothing PSNR | higher than 40 | dB | UNKNOWN (result year 2017) | exact-multiplier output | seven images | p.8 |
| smoothing MSSIM | higher than 0.99 | ratio | UNKNOWN (result year 2017) | exact-multiplier output | seven images | p.8 |
errors_and_checks: U-RoBA and S-RoBA have relative error `(Ar−A)(Br−B)/(AB)` and maximum error `11.1̅%`; the result may exceed or fall below the exact result. Their output is exact when either operand's absolute value is a power of two. AS-RoBA adds negation error and reaches 100% error when an operand is `−1`. Almost all reported 32-bit RoBA approximate outputs have relative error below 10%. No fault checker is provided. # pp.3-5
conditions: RoBA targets error-resilient DSP applications. U-RoBA applies when inputs are positive. Signed inputs require absolute-value generation and final sign restoration, which increase hardware cost. AS-RoBA reduces negation delay by omitting incrementing, but its accuracy is lower when at least one input is negative. The shifter has the highest delay/power/area contribution in S-RoBA and AS-RoBA. DSM8 has higher accuracy in the reported comparisons, while U-RoBA has lower delay and energy. # pp.1,4-6
evidence: §III.A-C, Fig. 1, Tables I-V, §IV.A-B, Tables VI-IX, Figs. 2-3, pp.2-8

### parallel_prefix  (role: instantiates)
mechanism: A single `2n`-bit Kogge-Stone adder computes `Ar × B + Br × A` before the simplified subtraction of `Ar × Br`. # p.3
choices:
  topology: kogge_stone   # p.3
new_choices:
  none
slots:
  none
parameters: `2n`-bit adder # p.3
results: none
errors_and_checks: none
conditions: The paper does not report the Kogge-Stone adder separately from the complete RoBA multiplier. # pp.3,6
evidence: §III.B and Fig. 1, p.3

### barrel_mux_tree  (role: instantiates)
mechanism: Three barrel shifters calculate `Ar × Br`, `Ar × B`, and `Br × A`; the shift amounts derive from `log2Ar − 1` or `log2Br − 1`. # p.3
choices:
new_choices:
  none
slots:
  none
parameters: three shifters; `n`-bit inputs and `2n`-bit outputs; maximum unsigned shift amount `n−1` # pp.3-4
results: none
errors_and_checks: none
conditions: The shifter is the largest delay/power/area contributor in the reported S-RoBA and AS-RoBA breakdown. # p.6
evidence: §III.B, Fig. 1, and Table VII, pp.3-6

## new_families
none

## space_gaps
* `operand_rounding` lacks slots for the instantiated barrel shifters and Kogge-Stone summation adder. # p.3
* `operand_rounding.rounding` lacks the paper's tie rule: `3 × 2^(p−2)` rounds upward except that three rounds to two. # pp.2-3
* `operand_rounding` lacks a signed-negation choice distinguishing U-RoBA/S-RoBA/AS-RoBA. # p.4
* `operand_rounding` lacks the optional `−1` bypass that bounds AS-RoBA's worst case at added delay/power cost. # p.4

## open_questions
* The supplied text does not expose the numeric cells of Tables II-VII, so their absolute error-rate/power/delay/area/energy/EDP/PDA values cannot be recorded.
* The paper suggests the AS-RoBA `−1` bypass but does not state that the evaluated implementation includes it. # p.4
