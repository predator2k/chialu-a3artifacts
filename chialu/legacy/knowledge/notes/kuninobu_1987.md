---
handle: kuninobu_1987
citation: Kuninobu, Nishiyama, Edamatsu, Taniguchi, Takagi, "Design of High Speed MOS Multiplier and Divider Using Redundant Binary Representation", 8th IEEE Symposium on Computer Arithmetic, 1987
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [signed_int_n, int64]
authority: incremental
pages_read: 80-86 / 7 pages
---

## summary
The paper presents CMOS multiplier/divider designs whose internal arithmetic uses redundant binary digits {-1,0,1}. The multiplier combines adjacent radix-4 Booth groups to reduce the partial products from n/2 to n/4, while the divider keeps quotient selection and partial-remainder updates in redundant binary form (p.81-85).

## families
### generalized_signed_digit  (role: extends)
mechanism: Addition first determines intermediate carry ci and sum si satisfying xi+yi=2ci+si, then forms zi=si+ci-1 without another carry. The selection rule prevents si and ci-1 from having equal nonzero signs, so zi depends only on xi, yi and the two preceding digit pairs. Two-bit sign/absolute encodings simplify the CMOS cells for general redundant addition, redundant-plus-binary addition and binary subtraction (p.80-83).
choices:
  radix: 2   # p.81
  digit_encoding: sign_magnitude   # p.82
  addition_scheme: carry_free   # p.80
  final_conversion: cpa   # p.81
new_choices:
  none
slots:
  none
parameters: digit set {-1,0,1}; two addition steps; cell I general redundant addition; cell II redundant-plus-binary addition; cell III binary subtraction   # p.80-83
results:
| metric | value | unit | technology / device | baseline | condition | page |
| redundant adder cell I transistor count | 42 | transistors | CMOS, node UNKNOWN, 1987 | former cell [7], value UNKNOWN | general redundant plus redundant | p.82 |
| redundant adder cell I critical path | 5 | gates | CMOS, node UNKNOWN, 1987 | UNKNOWN | exclusive-nor counted as 1.5 gates | p.82 |
| redundant adder cell II transistor count | 22 | transistors | CMOS, node UNKNOWN, 1987 | cell I: 42 transistors | redundant plus binary | p.82 |
| redundant adder cell II critical path | 3 | gates | CMOS, node UNKNOWN, 1987 | cell I: 5 gates | redundant plus binary | p.82 |
| redundant adder cell III transistor count | 10 | transistors | CMOS, node UNKNOWN, 1987 | UNKNOWN | subtraction of two binary numbers | p.83 |
| redundant adder cell III critical path | 1.5 | gates | CMOS, node UNKNOWN, 1987 | UNKNOWN | subtraction of two binary numbers | p.83 |
errors_and_checks: none
conditions: Carry-propagation-free addition has time independent of word length, but each redundant digit uses two binary bits and external binary output requires a carry-lookahead conversion proportional to log n (p.80-81).
evidence: §II.A-B, Table I, Fig.2.1, §IV.A, Fig.4.1-4.3 (p.80-83)

### redundant_binary_multiplier  (role: proposes)
mechanism: The multiplier recodes a two's-complement multiplier with radix-4 Booth recoding, pairs adjacent even/odd recoded terms, and subtracts the paired binary multiples to form one {-1,0,1} partial product. This pairing produces about n/4 partial products. A tree of two-input/one-output redundant binary adders reduces the products before a carry-lookahead converter produces the binary result (p.81, p.83-84).
choices:
  rb_encoding: sign_magnitude_2bit   # p.82
  booth_radix: 4   # p.81
  rbnb_converter: cpa   # p.81
new_choices:
  adjacent_booth_grouping: paired_even_odd — two adjacent radix-4 recoded groups form one redundant partial product   # p.81
slots:
  final_converter: carry_lookahead   # p.81, p.83
parameters: n-bit×n-bit two's-complement; n/4 partial products; log2(n)-2 redundant-adder-tree levels; 64bitX64bit comparison   # p.81, p.83, p.85
results:
| metric | value | unit | technology / device | baseline | condition | page |
| critical logic path | 34 | gates | CMOS, node UNKNOWN, 1987 | Booth & Wallace: 38 gates | 64bitX64bit | p.85 |
| transistor count | 90k | transistors | CMOS, node UNKNOWN, 1987 | Booth & Wallace: 120k transistors | 64bitX64bit | p.85 |
| critical logic path ratio | 90% | of baseline | CMOS, node UNKNOWN, 1987 | Booth & Wallace | 64bitX64bit | p.85 |
| transistor count ratio | 75% | of baseline | CMOS, node UNKNOWN, 1987 | Booth & Wallace | 64bitX64bit | p.85 |
errors_and_checks: none
conditions: The reported advantage depends on n/4 partial products, simplified redundant cells and a regular tree layout; the comparison is limited to the paper's 64-bit circuit designs (p.85).
evidence: §III.A, §IV.B, Fig.4.4-4.5, Table III (p.81, p.83-85)

## new_families
### redundant_binary_divider  (domain: div: dividers / square root, closest: srt_radix2, why_not: the paper treats its fully redundant-binary recurrence as distinct from the SRT divider used as its baseline)
mechanism: A radix-2 shift-subtract/add recurrence represents every partial remainder with {-1,0,1} digits. Each quotient digit qj∈{-1,0,1} is selected from the sign of the three most significant digits of rR(j), and the next remainder is generated by a redundant binary add/subtract cell. An unrolled combinational array repeats quotient-selection/remainder cells for n steps and ends with redundant-to-binary conversion (p.82, p.84-85).
choices:
  radix: {2}   # p.82
  residual_representation: {redundant_binary_signed_digit}   # p.82
  quotient_digit_set: {m1_0_p1}   # p.82
  quotient_selection: {three_most_significant_digits}   # p.82
  implementation: {combinational_unrolled}   # p.84
results:
| metric | value | unit | technology / device | baseline | condition | page |
| critical logic path | 396 | gates | CMOS, node UNKNOWN, 1987 | SRT divider: 938 gates | 64bit+64bit | p.85 |
| transistor count | 110k | transistors | CMOS, node UNKNOWN, 1987 | SRT divider: 120k transistors | 64bit+64bit | p.85 |
| critical logic path ratio | about 42% | of baseline | CMOS, node UNKNOWN, 1987 | SRT divider | 64bit+64bit | p.85 |
| transistor count ratio | about 90% | of baseline | CMOS, node UNKNOWN, 1987 | SRT divider | 64bit+64bit | p.85 |
evidence: §III.B, §IV.C, Fig.4.6-4.8, Table IV (p.82, p.84-85)

## space_gaps
* `redundant_binary_multiplier` lacks a choice for adjacent Booth-group pairing, which reduces n/2 Booth partial products to n/4 redundant partial products (p.81).
* The divider vocabulary lacks the fully redundant-binary combinational recurrence that the paper distinguishes from its SRT baseline (p.80, p.82, p.85).

## open_questions
* The paper gives no CMOS technology node and does not identify the Table III/IV results as measured, simulated or estimated (p.85).
* The divider's final quotient precision and rounding behavior are not specified beyond redundant-to-binary conversion (p.82).
