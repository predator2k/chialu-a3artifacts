---
handle: wahba_2017
citation: Wahba, Fahmy, "Area Efficient and Fast Combined Binary/Decimal Floating Point Fused Multiply Add Unit", IEEE Transactions on Computers, 2017
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [binary64, decimal64]
authority: incremental
pages_read: 14 / 14
---

## summary
The document proposes one IEEE-compliant 64-bit FMA datapath that performs binary/decimal addition, multiplication, subtraction, FMA, and fused multiply-subtract. The design shares a column-wise multiplier reduction tree and a carry-free redundant final adder, overlaps leading-zero anticipation with addition, and overlaps rounding with redundant-to-nonredundant conversion. Synthesis reports 4.25 ns delay, 195 000 µm2 area, and 112 mW power in TSMC65nmLP.

## families
### decimal_fma  (role: proposes)
mechanism: The combined binary/decimal FMA shares the multiplier and final adder between both formats. Binary mode uses SD radix-4 recoding, while decimal mode uses SD radix-5 recoding and BCD-8421 partial products. Column-wise reduction produces vectors that are combined with the aligned addend by a binary or decimal 4:2 CSA. A digit-set [−6,6] redundant adder performs the final addition. Leading-zero anticipation runs in parallel with that addition, and rounding runs in parallel with redundant-to-binary/decimal conversion. The unit performs one final IEEE rounding.
choices:
  structure: merged_tree   # pp.7-8
  internal_encoding: redundant_decimal   # pp.8-10
  binary_decimal_combined: true   # p.5
new_choices:
  multiplier_reduction: column_wise_mixed_binary_bcd — each four-bit column is reduced independently before optional binary-to-decimal conversion   # p.6
  normalization_count_encoding: base_3_binary_mode — the binary LZD emits a base-3 shift count for redundant digits carrying three binary bits   # pp.9,11
  rounding_timing: parallel_with_redundant_conversion — two conversions assume borrow-in 0/1 and the rounding decision selects the result   # pp.11-12
slots:
  multiplier_tree: parallel_decimal_multiplication [multiplier_recoding=sd_radix5 [outside domain], internal_digit_code=bcd8421]   # pp.5-6
parameters: 64-bit binary/decimal floating point; binary operating width 2p+1=107 bits; decimal operating width 3p+1 digits; optional 7 pipeline stages at 22 FO4 each   # pp.7-8,12
results:
| metric | value | unit | technology / device | baseline | condition | page |
| delay | 4.25 | ns | TSMC65nmLP / 2017 | none | combined binary/decimal combinational unit, typical process/temperature, 1.2V | p.12 |
| area | 195 000 | µm2 | TSMC65nmLP / 2017 | none | combined binary/decimal unit | p.12 |
| power | 112 | mW | TSMC65nmLP / 2017 | none | combined binary/decimal unit | p.12 |
| binary-mode delay | 3.4 | ns | TSMC65nmLP / 2017 | none | unchanged combined unit operated in binary mode | p.12 |
| delay improvement | 6% | percent | TSMC65nmLP / 2017 | fastest published stand-alone decimal FMA | decimal mode; normalized comparison | p.13 |
| area reduction | 23% | percent | TSMC65nmLP / 2017 | authors' separate binary-only and decimal-only units together | combined unit | p.13 |
| pipeline depth | 7 | stages | TSMC65nmLP / 2017 | none | 22 FO4 per stage, including 3 FO4 for latching | p.12 |
errors_and_checks: The decimal multiplier/adder/FMA passed more than 1.1 million directed vectors; binary multiplication/addition/FMA used a separate generated vector set, whose size is not reported, and discovered bugs were fixed. The claimed contract is IEEE-754 compliance with five standard rounding directions plus two extra directions.   # p.12
conditions: Resource sharing reduces area because the multiplier and adder dominate the unit. The seven-stage FMA has greater addition latency than a typical four-stage floating-point adder. IBM Power6 is about 30% faster than the combined unit in binary mode after the authors' technology/delay normalization.   # pp.5,12-13
evidence: Fig. 1; §§3.1-3.3, 4.1-4.5, 5.1-5.2; Figs. 3, 6, 8-9; Table 4, pp.5-13

### parallel_decimal_multiplication  (role: extends)
mechanism: Each decimal multiplier digit is recoded as Bi=5×BiU+BiL, with BiU in {0,1,2} and BiL in {−2,−1,0,1,2}. The digits select {0,±A,±2A,5A,10A} in BCD-8421. Each four-bit column is reduced independently by a binary CSA tree and carry-lookahead adder; decimal mode then converts the column sum into units/tens/hundreds digits. The shared hardware treats each four-bit binary group as one column.
choices:
  multiplier_recoding: sd_radix5 [outside domain]   # p.5
  internal_digit_code: bcd8421   # pp.5-6
  pp_generation: precomputed_multiples_mux   # pp.5-6
new_choices:
  reduction_style: column_wise_binary_then_bcd — independent binary column reduction followed by binary-to-decimal conversion   # p.6
slots:
  reduction_tree: csa_tree   # p.6
parameters: 32 four-bit columns; 32 decimal partial products; 28 binary partial products; longest column has 32 digits and a maximum decimal sum of 288   # p.6
results:
| metric | value | unit | technology / device | baseline | condition | page |
| multiplier area share | 43% | percent of total area | TSMC65nmLP / 2017 | combined FMA total | synthesized combined unit | p.12 |
| multiplier delay share | 36% | percent of total delay | TSMC65nmLP / 2017 | combined FMA total | synthesized combined unit | p.12 |
errors_and_checks: none
conditions: Column-wise reduction is described as easier to share between binary and decimal than a conventional CSA reduction tree. Decimal conversion adds a stage after each binary column sum.   # p.6
evidence: §§3.1.1-3.1.3; Figs. 2-3, pp.5-6

### generalized_signed_digit  (role: extends)
mechanism: Binary values are grouped as radix-8 digits, while decimal values remain radix-10 digits. Both modes convert into two’s-complement redundant digits from [−6,6]. The adder estimates an output transfer digit in parallel with a four-bit digit addition, then adds a correction digit containing the radix adjustment and input transfer. Each digit therefore completes without carry propagation. Final conversion uses a look-ahead borrow tree.
choices:
  radix: 10 [outside domain]   # p.10
  redundancy: intermediate   # p.10
  digit_encoding: twos_complement   # p.10
  addition_scheme: carry_free   # pp.10-11
  final_conversion: cpa   # p.11
new_choices:
  shared_radices: {8, 10} — one redundant digit system supports octal-grouped binary and decimal arithmetic   # p.10
slots:
  none
parameters: digit set [−6,6]; four-bit digit adder; eight-input transfer-estimation circuit   # p.10
results:
| metric | value | unit | technology / device | baseline | condition | page |
| redundant-section area share | 28% | percent of total area | TSMC65nmLP / 2017 | combined FMA total | addition/normalization/rounding section | p.12 |
| redundant-section delay share | 41% | percent of total delay | TSMC65nmLP / 2017 | combined FMA total | addition/normalization/rounding section | p.12 |
errors_and_checks: none
conditions: The [−6,6] representation removes carry propagation from final addition, but conversion back to binary/decimal requires borrow propagation through a look-ahead tree.   # pp.10-11
evidence: §§4.2, 4.4; Figs. 7-8, pp.10-11

## new_families
### rounding_while_redundant  (domain: fp: floating-point rounding, closest: decimal_fma, why_not: existing round-slot families do not describe speculative borrow conversion and location-dependent redundant rounding)
mechanism: Rounding signals are generated for every possible rounding location before fine normalization. Binary mode evaluates three locations, and decimal mode evaluates two because its LZA may be wrong by one digit. Redundant-to-nonredundant conversion is duplicated under assumed borrow-ins of 0 and 1. The completed rounding decision selects the correct conversion, removing rounding carry propagation from the critical path.
choices: rounding_locations: {binary_three, decimal_two}; conversion_candidates: Int[2..2:1]; rounding_modes: {five_ieee, five_ieee_plus_two}
results:
| metric | value | unit | technology / device | baseline | condition | page |
| rounding critical-path delay | 0 | added delay | TSMC65nmLP / 2017 | rounding after conversion | rounding overlaps duplicate conversion | pp.11-12 |
evidence: §§4.3-4.5; Fig. 8, pp.11-12

## space_gaps
* `parallel_decimal_multiplication.multiplier_recoding` lacks the document's `sd_radix5` value.   # p.5
* `generalized_signed_digit.radix` lacks radix 10 and cannot express one implementation shared across radices 8/10.   # p.10
* `decimal_fma` lacks choices for column-wise mixed binary/BCD reduction, base-3 LZA output, and rounding while redundant.   # pp.6,9-12
* `decimal_fma.slot final_adder` is absent, while the document makes the shared [−6,6] redundant adder a principal architectural component.   # pp.10,13

## open_questions
* Table 4 reports technology-normalized delay/area ratios, but the document does not give enough scaling detail to reconstruct every normalized comparison.   # p.13
* The binary verification vector count and achieved coverage are not reported.   # p.12
