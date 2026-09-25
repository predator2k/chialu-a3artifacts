---
handle: tyagi1993
citation: A. Tyagi, "A Reduced-Area Scheme for Carry-Select Adders", IEEE Transactions on Computers, vol. 42, no. 10, pp. 1163-1170, 1993.
actual_citation: Akhilesh Tyagi, "A Reduced Area Scheme for Carry-Select Adders (preliminary version)", venue UNKNOWN, 1990
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [binary_integer]
authority: incremental
pages_read: pp.255-258 / 4 pages
---

## summary
The document replaces the carry-select adder's second carry-chain copy with one additional OR-derived carry per bit position. The document also proposes select-prefix adders, which use parallel-prefix blocks connected by a carry-select chain to span area/time points between carry-select and pure parallel-prefix adders.

## families
### carry_select  (role: extends)
mechanism: Each block evaluates carries for a zero block carry-in and computes the one-carry-in result from the identity \(c_i^1=c_i^0\lor P_i\). An AND gate extends the block propagate at each bit, while NOR-based logic selects each carry using the preceding block's carry-out. The scheme avoids duplicating the complete carry-evaluation block.   # pp.255-256
choices:
  block_sizing: square_root_ramp   # pp.255,257
  duplication: or_gate_derived_second_carry [outside domain]   # p.256
  select_source: rippled_block_carries   # p.256
new_choices:
  none
slots:
  block_adder: ripple_carry   # pp.255-256
parameters: n-bit adder divided into k stages; common stage sizes 1, 2, ..., √n; implemented widths n = 4, 8, 16, 32, 64   # pp.255,258
results:
| metric | value | unit | technology / device | baseline | condition | page |
| gate count | 37% larger | percent | UNKNOWN; 1990 | carry-skip adder | elementary-gate accounting; XOR counted as two gates | p.257 |
| delay | about 30% faster | percent | UNKNOWN; 1990 | carry-skip adder | arithmetic-progression block sizing | p.257 |
| area | 115735 | X2 units | UNKNOWN; 1990 | carry-ripple adder: 66880 X2 units | n = 4; module-generator layout | p.258 |
| area | 286572 | X2 units | UNKNOWN; 1990 | carry-ripple adder: 151280 X2 units | n = 8; module-generator layout | p.258 |
| area | 682878 | X2 units | UNKNOWN; 1990 | carry-ripple adder: 309008 X2 units | n = 16; module-generator layout | p.258 |
| area | 1605552 | X2 units | UNKNOWN; 1990 | carry-ripple adder: 838656 X2 units | n = 32; module-generator layout | p.258 |
| area | 4764342 | X2 units | UNKNOWN; 1990 | carry-ripple adder: 2321824 X2 units | n = 64; module-generator layout | p.258 |
| delay | 4.0 | nano-second units | UNKNOWN; 1990 | carry-ripple adder: 5.5 nano-second units | n = 4 | p.258 |
| delay | 7.0 | nano-second units | UNKNOWN; 1990 | carry-ripple adder: 13.0 nano-second units | n = 8 | p.258 |
| delay | 11.5 | nano-second units | UNKNOWN; 1990 | carry-ripple adder: 27.5 nano-second units | n = 16 | p.258 |
| delay | 22.5 | nano-second units | UNKNOWN; 1990 | carry-ripple adder: 57.5 nano-second units | n = 32 | p.258 |
| delay | 44.5 | nano-second units | UNKNOWN; 1990 | carry-ripple adder: 119.5 nano-second units | n = 64 | p.258 |
| area overhead | between 60% and 80% | percent | UNKNOWN; 1990 | carry-ripple adder | module-generator layouts for n = 4, 8, 16, 32, 64 | p.258 |
errors_and_checks: none
conditions: The reduced-area carry-select scheme targets medium-speed addition and trades about 37% more gates than carry-skip for about 30% less delay. The measured layouts retain 60%-80% more area than carry-ripple adders.   # pp.257-258
evidence: §2; Figs. 1-2; §2.1; Tables 1-2; §4, pp.255-258

## new_families
### select_prefix  (domain: adder, closest: carry_select, why_not: the carry-select family does not admit parallel-prefix blocks in its block_adder slot or represent a serial selection chain over independently evaluated prefix blocks)
mechanism: Parallel-prefix carry-evaluation blocks feed a serial carry-select chain. Adjacent block sizes are delay-matched because a j-bit prefix block evaluates in \(4\log j\) elementary-gate delays, its alternate carry needs one OR-gate delay, and selection needs \(2T\). Doubling the next block size adds two prefix levels, which matches the preceding selection delay. Equal blocks of size \(n^\epsilon\), for \(1/2\leq\epsilon\leq1\), define a family between square-root-time carry-select and logarithmic-time parallel-prefix designs.   # p.257
choices: block_adder: {parallel_prefix}; block_size_exponent: Real[1/2..1]; block_sizing: {delay_matched_doubling, equal_power_sized}; select_chain: {serial}
results:
| metric | value | unit | technology / device | baseline | condition | page |
| area | 2n log n - 3n | composition nodes | UNKNOWN; 1990 | Brent-Kung parallel-prefix adder: 2n log n composition nodes | full select-prefix construction | p.257 |
| worst-case time | [4 log n - 1]T | elementary-gate delay | UNKNOWN; 1990 | Brent-Kung parallel-prefix adder: 4 log n T | full select-prefix construction | p.257 |
| area | εn log n | composition-node area | UNKNOWN; 1990 | none | equal prefix blocks of size n^ε; 1/2 ≤ ε ≤ 1 | p.257 |
| time | n^(1-ε) | asymptotic time | UNKNOWN; 1990 | none | equal prefix blocks of size n^ε; 1/2 ≤ ε ≤ 1 | p.257 |
evidence: §3 and Lemmas 2-3, p.257

## space_gaps
* The carry_select duplication domain lacks `or_gate_derived_second_carry`, where \(c_i^1=c_i^0\lor P_i\) replaces the second carry-chain copy.   # p.256
* The carry_select block_adder slot lacks `parallel_prefix`, which the select-prefix construction uses inside each selection block.   # p.257
* The carry_select block_sizing domain lacks delay-matched prefix-block growth, including adjacent block sizes j and 2j.   # p.257

## open_questions
* The document does not identify its conference or proceedings venue; only the 1990 IEEE copyright line is visible.
* The overview's printed/OCR percentage for the reduced area advantage over carry-skip is unclear, so that percentage is not extracted.   # p.255
