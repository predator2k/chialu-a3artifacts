---
handle: akkas_2011
citation: Akkas, Schulte, "A Decimal Floating-Point Fused Multiply-Add Unit with a Novel Decimal Leading-Zero Anticipator", IEEE ASAP, 2011
actual_citation: same
status: ok
kind: paper
unit_classes: [other]
formats: [decimal64]
authority: incremental
pages_read: 43-50 / 8
---

## summary
The paper proposes a decimal64 fused multiply-add unit that uses a parallel decimal multiplier, a Kogge-Stone decimal adder, simultaneous product/addend alignment, and one final IEEE 754-2008 rounding step (pp.43-46). A new decimal leading-zero anticipator predicts every zero-digit position in parallel with addition/subtraction (pp.46-49). A five-stage 65-nm implementation has a 1.07 ns pipeline delay and an area of 113,795 nm2 (p.49).

## families
### decimal_fma  (role: proposes)
mechanism: The unit decodes DPD operands to BCD, computes the 16-digit by 16-digit product, and aligns the 32-digit product and extended addend simultaneously with separate left/right decimal barrel shifters. A pre-corrected Kogge-Stone network performs 32-digit addition/subtraction. The decimal LZA operates in parallel with the addition, after which post-alignment, special-case handling, and one rounding step produce the decimal64 result (pp.44-46).
choices:
  structure: cascade   # pp.44-46
  internal_encoding: bcd   # p.44
new_choices:
  alignment_datapath: bidirectional_2P — both product and addend can be shifted left/right in a 2P-digit alignment unit   # pp.43-45
  rounding_modes: five_ieee_754_2008_modes — the final stage supports five rounding modes   # p.46
slots:
  multiplier_tree: parallel_decimal_multiplication   # p.44
parameters: decimal64; P=16 digits; 128-bit/32-digit internal product and adder; 1 to 10 pipeline stages   # pp.44,49
results:
| metric | value | unit | technology / device | baseline | condition | page |
| pipeline delay | 4.6 | ns | LSI gflxp 65-nm CMOS; 2011 | none | 1 stage, described as unpipelined | p.49 |
| area | 123,929 | nm2 | LSI gflxp 65-nm CMOS; 2011 | none | 1 stage | p.49 |
| pipeline delay | 2.3 | ns | LSI gflxp 65-nm CMOS; 2011 | none | 2 stages | p.49 |
| area | 116,942 | nm2 | LSI gflxp 65-nm CMOS; 2011 | none | 2 stages | p.49 |
| pipeline delay | 1.65 | ns | LSI gflxp 65-nm CMOS; 2011 | none | 3 stages | p.49 |
| area | 115,538 | nm2 | LSI gflxp 65-nm CMOS; 2011 | none | 3 stages | p.49 |
| pipeline delay | 1.25 | ns | LSI gflxp 65-nm CMOS; 2011 | none | 4 stages | p.49 |
| area | 120,585 | nm2 | LSI gflxp 65-nm CMOS; 2011 | none | 4 stages | p.49 |
| pipeline delay | 1.07 | ns | LSI gflxp 65-nm CMOS; 2011 | none | 5 stages | p.49 |
| area | 113,795 | nm2 | LSI gflxp 65-nm CMOS; 2011 | none | 5 stages | p.49 |
| pipeline delay | 0.94 | ns | LSI gflxp 65-nm CMOS; 2011 | none | 6 stages | p.49 |
| area | 126,509 | nm2 | LSI gflxp 65-nm CMOS; 2011 | none | 6 stages | p.49 |
| pipeline delay | 0.82 | ns | LSI gflxp 65-nm CMOS; 2011 | none | 7 stages | p.49 |
| area | 129,757 | nm2 | LSI gflxp 65-nm CMOS; 2011 | none | 7 stages | p.49 |
| pipeline delay | 0.74 | ns | LSI gflxp 65-nm CMOS; 2011 | none | 8 stages | p.49 |
| area | 125,802 | nm2 | LSI gflxp 65-nm CMOS; 2011 | none | 8 stages | p.49 |
| pipeline delay | 0.67 | ns | LSI gflxp 65-nm CMOS; 2011 | none | 9 stages | p.49 |
| area | 130,967 | nm2 | LSI gflxp 65-nm CMOS; 2011 | none | 9 stages | p.49 |
| pipeline delay | 0.61 | ns | LSI gflxp 65-nm CMOS; 2011 | none | 10 stages | p.49 |
| area | 137,709 | nm2 | LSI gflxp 65-nm CMOS; 2011 | none | 10 stages | p.49 |
| delay | 6.5 | ns | TSMC 90-nm CMOS; 2010 | previous DFP-FMA [11] | value reported from [11] | p.49 |
| area | 235,446 | nm2 | TSMC 90-nm CMOS; 2010 | previous DFP-FMA [11] | value reported from [11] | p.49 |
errors_and_checks: Basic/corner-case simulation produces correct DFP-FMA results; no quantitative coverage is reported   # p.49
conditions: The prior design uses a different 90-nm library, so the reported comparison is not technology-normalized. Auto-pipelining causes nonmonotonic area across pipeline depths because registers are inserted to meet delay constraints   # p.49
evidence: Fig. 1 and Algorithms 1-2 (pp.44-46); Tables II-III (p.49)

### parallel_decimal_multiplication  (role: instantiates)
mechanism: A previously published radix-10 parallel fixed-point multiplier multiplies two 16-digit BCD significands and produces a 128-bit result representing 32 decimal digits (p.44).
choices:
new_choices:
  none
slots:
  reduction_tree: UNKNOWN   # p.44
  final_adder: UNKNOWN   # p.44
parameters: 16 decimal digits by 16 decimal digits; 32-digit/128-bit product   # p.44
results:
| metric | value | unit | technology / device | baseline | condition | page |
| area | 82,252 | nm2 | LSI gflxp 65-nm CMOS; 2011 | none | component in five-stage DFP-FMA | p.49 |
| total-area share | 72.3 | % | LSI gflxp 65-nm CMOS; 2011 | total area 113,795 nm2 | component in five-stage DFP-FMA | p.49 |
errors_and_checks: none
conditions: The paper refers to [17] for the multiplier architecture and does not restate its recoding/internal digit code/reduction structure   # pp.44,50
evidence: Section III and Fig. 1 (p.44); Table III (p.49)

### bcd_direct_addition  (role: instantiates)
mechanism: Addition/subtraction uses pre-correction, a Kogge-Stone carry network, and post-correction. Addition adds 6 to every digit of the first operand. Subtraction inverts each bit of the second operand to form the digitwise fifteen's complement. Each pre-corrected digit result lies in [6,25], so sums above 15 generate decimal carries (p.45).
choices:
  digit_code: bcd8421   # p.44
  correction_placement: presum_plus6   # p.45
  carry_scheme: full_lookahead   # p.45
new_choices:
  subtraction_pre_correction: fifteens_complement — each subtrahend digit is bitwise inverted before addition   # p.45
slots:
  digit_adder: parallel_prefix [topology=kogge_stone]   # p.45
parameters: 32 decimal digits; 128-bit operands   # pp.44-45
results:
| metric | value | unit | technology / device | baseline | condition | page |
| delay | 1.07 | ns | LSI gflxp 65-nm CMOS; 2011 | none | K-S adder constrained to 1.07 ns | p.48 |
| area | 7,556 | nm2 | LSI gflxp 65-nm CMOS; 2011 | none | K-S adder constrained to 1.07 ns | p.48 |
| minimum delay | 0.65 | ns | LSI gflxp 65-nm CMOS; 2011 | none | K-S adder minimum-delay synthesis | p.48 |
| area at minimum delay | 17,464 | nm2 | LSI gflxp 65-nm CMOS; 2011 | none | K-S adder minimum-delay synthesis | p.48 |
errors_and_checks: none
conditions: The reported K-S adder includes pre-correction, K-S network, and post-correction   # p.49
evidence: Section III-B (p.45); Table I (p.48)

### decimal_encoding_codec  (role: instantiates)
mechanism: Operand Decode extracts decimal64 fields, accepts DPD significands, and converts each decimal digit to four-bit BCD before multiplication/alignment/addition. Operand Encode converts the final result for the decimal64 output (p.44).
choices:
  significand_encoding: dpd   # p.44
  codec_placement: inside_operation   # p.44
new_choices:
  none
slots:
  none
parameters: three 64-bit decimal64 inputs; one 64-bit result   # p.44
results:
| metric | value | unit | technology / device | baseline | condition | page |
| decode area | 1,524 | nm2 | LSI gflxp 65-nm CMOS; 2011 | total area 113,795 nm2 | five-stage DFP-FMA | p.49 |
| encode area | 396 | nm2 | LSI gflxp 65-nm CMOS; 2011 | total area 113,795 nm2 | five-stage DFP-FMA | p.49 |
errors_and_checks: none
conditions: The internal arithmetic uses BCD rather than DPD   # p.44
evidence: Fig. 1 and Section III (p.44); Table III (p.49)

## new_families
### decimal_leading_zero_anticipator  (domain: decimal: decimal misc, closest: lzd_cell_tree, why_not: This mechanism predicts decimal sum/difference zero digits from pre-corrected operands before the result exists, rather than detecting zeros in an existing binary word.)
mechanism: Thirty-two four-bit adders form per-digit five-bit results. Addition derives ten/nine/carry-sure vectors; subtraction derives same/one-bigger/borrow-sure vectors. Two Kogge-Stone-type networks compute carries or borrows for the three effective-operation/sign cases. Two 32-bit expected vectors predict zero digits, and the sum sign selects the correct vector. A binary LZD counts zeros in the upper 16 predicted bits while decimal addition proceeds (pp.46-49).
choices: prediction_cases: {addition, subtraction_positive_sum, subtraction_negative_sum}; prefix_network_count: 2; zero_prediction: exact
results:
| metric | value | unit | technology / device | baseline | condition | page |
| delay | 1.07 | ns | LSI gflxp 65-nm CMOS; 2011 | none | Decimal LZA + 16-bit LZD constrained to 1.07 ns | p.48 |
| area | 2,907 | nm2 | LSI gflxp 65-nm CMOS; 2011 | none | Decimal LZA + 16-bit LZD constrained to 1.07 ns | p.48 |
| minimum delay | 0.65 | ns | LSI gflxp 65-nm CMOS; 2011 | none | Decimal LZA + 16-bit LZD minimum-delay synthesis | p.48 |
| area at minimum delay | 7,568 | nm2 | LSI gflxp 65-nm CMOS; 2011 | none | Decimal LZA + 16-bit LZD minimum-delay synthesis | p.48 |
| total-area share | 5.0 | % | LSI gflxp 65-nm CMOS; 2011 | total area 113,795 nm2 | integrated five-stage DFP-FMA | p.49 |
errors_and_checks: Every zero-digit position is predicted exactly. Software testing checks all possible cases for four-digit operands; no false predictions are reported   # pp.43,49
conditions: The LZA consumes shifted/pre-corrected operands and the effective operation. The final selection also waits for the sum sign through a 2-to-1 multiplexer   # pp.46-49
evidence: Figs. 3-8 and Eqs. 2-5 (pp.46-48); Tables I and III (pp.48-49)

## space_gaps
* `decimal_fma` lacks a significand-adder slot for the instantiated `bcd_direct_addition` family   # pp.44-45
* `decimal_fma` lacks a leading-zero-anticipator slot for `decimal_leading_zero_anticipator`   # pp.46-49
* `decimal_leading_zero_anticipator` is absent from the decimal vocabulary despite exact digit-level anticipation being the paper's principal new mechanism   # pp.43,46-49

## open_questions
* The paper does not restate enough of multiplier [17] to determine `multiplier_recoding`, `internal_digit_code`, `pp_generation`, or either multiplier slot   # pp.44,50
* The Kogge-Stone networks' valency/fanout/node implementation are not reported   # pp.45,47-49
