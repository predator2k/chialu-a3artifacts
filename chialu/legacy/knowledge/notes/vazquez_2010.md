---
handle: vazquez_2010
citation: Vazquez, Antelo, Montuschi, "Improved Design of High-Performance Parallel Decimal Multipliers", IEEE Transactions on Computers, 2010
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [bcd]
authority: incremental
pages_read: 679-693 / 15
---

## summary
The paper proposes combinational fixed-point parallel decimal multipliers using signed-digit radix-10 or radix-5 multiplier recoding and partial products encoded in (4221)/(5211) decimal codes (pp. 681-682). The paper also develops decimal p:2 carry-save reduction trees that use binary CSAs, digit recoders, and bit counters without BCD correction (pp. 685-689). Synthesized 16-digit designs reach minimum latencies of 2.30 ns for SD radix-10 and 2.28 ns for SD radix-5 in a 90 nm CMOS library (p. 690).

## families
### parallel_decimal_multiplication  (role: proposes)
mechanism: The SD radix-10 architecture recodes a d-digit BCD multiplier into d+1 digits from {-5,...,5}. Each recoded digit selects one of {0,X,2X,3X,4X,5X} through 5:1 muxes, and bit inversion plus a hot one produces negative multiples. Decimal p:2 CSA trees reduce the aligned (4221) partial products to S and H. A final conditional-speculative quaternary-tree decimal adder computes P=2H+S after recoding S to BCD excess-6 (pp. 681-684).
choices:
  multiplier_recoding: sd_radix10_m5_p5   # pp. 681-682
  internal_digit_code: bcd4221   # pp. 681-682
  pp_generation: precomputed_multiples_mux   # pp. 681-684
new_choices:
  reduction_optimization: area_optimized | delay_optimized — selects the p:2 CSA-tree area/delay organization   # pp. 688-690
slots:
  reduction_tree: csa_tree   # pp. 685-689
  final_adder: speculative_decimal_addition [outside domain]   # p. 682
parameters: unsigned d-digit BCD operands; evaluated at d=16 (64-bit); d+1 partial products; combinational; latency 1 cycle; II=1 cycle   # pp. 681, 685, 690, 692
results:
| metric | value | unit | technology / device | baseline | condition | page |
| delay range | 2.30-2.88 | ns | Faraday UMC 90 nm SP-RVT (Low k), 1 V, 25ºC | none | synthesized 16-digit SD radix-10 multiplier | p. 690 |
| area range | 44,500-32,400 | NAND2 gates | Faraday UMC 90 nm SP-RVT (Low k), 1 V, 25ºC | none | synthesized over the delay range from 2.30 ns to 2.88 ns | p. 690 |
| speedup | 1.15 | times | Faraday UMC 90 nm SP-RVT (Low k) | decimal multiplier in [9] | minimum-latency 16-digit implementation | p. 692 |
| area | 0.65 | times baseline area | Faraday UMC 90 nm SP-RVT (Low k) | decimal multiplier in [9] | minimum-latency 16-digit implementation | p. 692 |
errors_and_checks: exact unsigned fixed-point BCD product; no approximation or fault checking is reported   # pp. 680-682
conditions: The 3X carry-propagate addition constrains partial-product-generation latency (p. 684). The architecture is presented as the high-performance option with moderate area (p. 692).
evidence: §§3.1, 4.1, 4.3, 5.1-5.4, 6.2, 7.2; Figs. 1, 3, 5a, 7a, 14, 18; Tables 4 and 6.

### parallel_decimal_multiplication  (role: proposes)
mechanism: The SD radix-5 architecture decomposes each BCD multiplier digit as Yi=YiU·5+YiL, where YiU is in {0,1,2} and YiL is in {-2,-1,0,1,2}. The architecture generates 2d partial products using only {-2X,-X,X,2X}; fixed shifts create the factor-five upper products. Mixed (4221)/(5211) p:2 CSA trees reduce the partial products, followed by the same P=2H+S decimal assimilation stage (pp. 682-684).
choices:
  multiplier_recoding: radix4_radix5_split   # pp. 682-683
  internal_digit_code: bcd4221+bcd5211 [outside domain]   # pp. 682-683
  pp_generation: precomputed_multiples_mux   # pp. 682-684
new_choices:
  reduction_optimization: area_optimized | delay_optimized — selects the mixed-code p:2 CSA-tree organization   # pp. 688-690
slots:
  reduction_tree: csa_tree   # pp. 685, 688-690
  final_adder: speculative_decimal_addition [outside domain]   # p. 682
parameters: unsigned d-digit BCD operands; evaluated at d=16 (64-bit); 2d partial products; 32:2 worst-case digit-column reduction; combinational; latency 1 cycle; II=1 cycle   # pp. 682, 685, 690, 692
results:
| metric | value | unit | technology / device | baseline | condition | page |
| delay range | 2.28-2.88 | ns | Faraday UMC 90 nm SP-RVT (Low k), 1 V, 25ºC | none | synthesized 16-digit SD radix-5 multiplier | p. 690 |
| area range | 49,700-37,600 | NAND2 gates | Faraday UMC 90 nm SP-RVT (Low k), 1 V, 25ºC | none | synthesized over the delay range from 2.28 ns to 2.88 ns | p. 690 |
| speedup | 1.20 | times | Faraday UMC 90 nm SP-RVT (Low k) | decimal multiplier in [9] | minimum-latency 16-digit implementation | p. 692 |
| area | 0.70 | times baseline area | Faraday UMC 90 nm SP-RVT (Low k) | decimal multiplier in [9] | minimum-latency 16-digit implementation | p. 692 |
| speedup | about 7 | times | 90 nm CMOS standard-cell synthesis | sequential decimal multiplier in [13] | 16-digit multiplication | p. 692 |
| area | 3 | times baseline area | 90 nm CMOS standard-cell synthesis | sequential decimal multiplier in [13] | 16-digit multiplication | p. 692 |
errors_and_checks: exact unsigned fixed-point BCD product; no approximation or fault checking is reported   # pp. 680-682
conditions: The simple multiple set makes partial-product generation comparable in latency to binary Booth radix-4 (p. 683). The architecture gives higher performance than SD radix-10 at greater area for the minimum-delay point (pp. 690, 692).
evidence: §§3.2, 4.2-4.4, 5.1, 5.5, 6.2, 7.2; Figs. 2, 4, 5b, 7b, 16-18; Tables 4 and 6.

### decimal_multioperand_addition  (role: extends)
mechanism: The decimal p:2 trees represent digits in weight-sum-nine codes, principally (4221) and (5211). Conventional 4-bit binary 3:2 CSAs then produce valid decimal sum/carry digits without decimal correction. Digit recoders and wired shifts multiply carry operands by two. Rows of bit counters reduce 9, 8, or 7 digits into 4 or 3 digits, enabling area-optimized and delay-optimized reduction trees (pp. 685-689).
choices:
  reduction_style: decimal_compressors   # pp. 685-689
  compressor_arity: higher   # pp. 687-689
  correction_placement: none [outside domain]   # pp. 685-686
new_choices:
  internal_digit_code: {(4221), (5211), mixed_(4221)/(5211)} — selects the decimal code or mixed-code inputs used by the p:2 tree   # pp. 685-689
slots:
  reduction_tree: csa_tree   # pp. 685-689
parameters: p:2 trees; demonstrated 6:2, 16:2, 17:2, and 32:2 structures; counters include 9:4, 8:4, and 7:3 reductions   # pp. 687-689
results:
| metric | value | unit | technology / device | baseline | condition | page |
| delay reduction | roughly 5 | percent | UNKNOWN; static-CMOS logical-effort model | proposed area-optimized decimal 16:2 CSA | proposed delay-optimized decimal CSA | p. 691 |
| area increase | 10 | percent | UNKNOWN; static-CMOS logical-effort model | proposed area-optimized decimal 16:2 CSA | proposed delay-optimized decimal CSA | p. 691 |
| delay reduction | at least 45 | percent | UNKNOWN; static-CMOS logical-effort model | decimal tree adder in [8] | proposed decimal CSA | p. 691 |
| hardware reduction | about 10 | percent | UNKNOWN; static-CMOS logical-effort model | decimal tree adder in [8] | proposed decimal CSA | p. 691 |
errors_and_checks: exact decimal carry-save reduction; no fault checking is reported   # pp. 685-689
conditions: The (4221)/(5211) codes avoid BCD correction because every 4-bit vector represents a valid decimal digit (pp. 685-686). The proposed tree targets high-performance multioperand addition with moderate area (p. 691).
evidence: §§5.2-5.5 and 7.1; Figs. 8-17; Table 5.

## new_families
none

## space_gaps
* `parallel_decimal_multiplication.internal_digit_code` cannot express a mixed (4221)/(5211) reduction tree as one declared value (pp. 682, 685).
* `parallel_decimal_multiplication.final_adder` excludes decimal-adder families, although both architectures use a conditional-speculative decimal adder (p. 682).
* `decimal_multioperand_addition.correction_placement` lacks a `none` value for coded carry-save addition that requires no decimal correction (pp. 685-686).

## open_questions
* Page 685 calls the SD radix-5 upper partial products `(5221)` once, while the architecture and surrounding sections consistently call the code `(5211)` (pp. 682-686).
* The supplied rendering omits the numeric cells of Tables 4-6, so only values repeated in the surrounding prose are recorded (pp. 690-692).
