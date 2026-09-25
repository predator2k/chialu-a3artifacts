---
handle: takagi_1985
citation: Takagi, Yasuura, Yajima, "High-Speed VLSI Multiplication Algorithm with a Redundant Binary Addition Tree", IEEE Transactions on Computers, 1985
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [unsigned_binary_integer, twos_complement_binary_integer]
authority: landmark
pages_read: 789-796 / 8
---

## summary
The document proposes an integer multiplier that reduces redundant-binary partial products through a binary tree of carry-propagation-free adders and converts the final result with a CLA. The multiplier has O(log n) depth/O(n2) gates and supports unsigned/2's-complement operands. (pp.789-794)

## families
### redundant_binary_multiplier  (role: proposes)
mechanism: The multiplier converts operands to radix-2 redundant binary digits in {−1, 0, 1}, generates partial products, and reduces pairs through log2 n levels of redundant binary adders. Each adder has constant depth because its two-step digit addition examines only a bounded set of neighboring digits. A redundant-binary/binary converter implemented as a modified CLA produces the conventional binary result. Extended Booth recoding reduces the partial-product count from n to n/2. (pp.790-794)
choices:
  rb_encoding: plus_minus_pair   # p.794
  booth_radix: 4   # p.793
  rbnb_converter: cpa   # pp.791-793
new_choices:
  none
slots:
  final_converter: carry_lookahead   # pp.791-793
parameters: n-bit unsigned or 2's-complement operands; n partial products without recoding; n/2 partial products with radix-4 modified-SD recoding; log2 n reduction levels; combinational circuit; n assumed to be a power of 2 for exposition, although n may be any positive integer.   # pp.790, 792-794
results:
| metric | value | unit | technology / device | baseline | condition | page |
| depth | 21 | computation elements | four-input NOR/OR gates; ECL considered; node/device UNKNOWN; 1985 | standard array 29; Wallace tree 22 | n=8 | p.794 |
| depth | 27 | computation elements | four-input NOR/OR gates; ECL considered; node/device UNKNOWN; 1985 | standard array 61; Wallace tree 28 | n=16 | p.794 |
| depth | 31 | computation elements | four-input NOR/OR gates; ECL considered; node/device UNKNOWN; 1985 | standard array 125; Wallace tree 30 | n=32 | p.794 |
| depth | 37 | computation elements | four-input NOR/OR gates; ECL considered; node/device UNKNOWN; 1985 | standard array 253; Wallace tree 34 | n=64 | p.794 |
| depth | 41 | computation elements | four-input NOR/OR gates; ECL considered; node/device UNKNOWN; 1985 | standard array 509; Wallace tree 40 | n=128 | p.794 |
| gate count | 550 | gates | four-input NOR/OR gates; ECL considered; node/device UNKNOWN; 1985 | standard array 528; Wallace tree 815 | n=8 | p.794 |
| gate count | 2213 | gates | four-input NOR/OR gates; ECL considered; node/device UNKNOWN; 1985 | standard array 2336; Wallace tree 2939 | n=16 | p.794 |
| gate count | 8796 | gates | four-input NOR/OR gates; ECL considered; node/device UNKNOWN; 1985 | standard array 9792; Wallace tree 9965 | n=32 | p.794 |
| gate count | 34388 | gates | four-input NOR/OR gates; ECL considered; node/device UNKNOWN; 1985 | standard array 40064; Wallace tree 37423 | n=64 | p.794 |
| gate count | 135324 | gates | four-input NOR/OR gates; ECL considered; node/device UNKNOWN; 1985 | standard array 162048; Wallace tree 142335 | n=128 | p.794 |
| relative speed | about four times faster | UNKNOWN | four-input NOR/OR gates; ECL considered; node/device UNKNOWN; 1985 | 32-bit standard array multiplier | depth used as computation-time measure | pp.790, 794 |
| relative speed | about seven times faster | UNKNOWN | four-input NOR/OR gates; ECL considered; node/device UNKNOWN; 1985 | 64-bit standard array multiplier | depth used as computation-time measure | pp.790, 794 |
| depth complexity | O(log n) | UNKNOWN | bounded-fan-in combinational model; node/device UNKNOWN; 1985 | array multiplier O(n); Wallace tree O(log n) | wires assumed to have no delay | pp.790, 793 |
| gate-count complexity | O(n2) | computation elements | bounded-fan-in combinational model; node/device UNKNOWN; 1985 | array multiplier O(n2); Wallace tree O(n2) | n-bit multiplier | pp.792-793 |
| chip-area complexity | O(n2 log n) | UNKNOWN | VLSI layout model; node/device UNKNOWN; 1985 | array multiplier O(n2); Wallace tree O(n2 log n) | bounded element/wire area and bounded wire overlap | pp.790, 793 |
errors_and_checks: The multiplication is exact; no approximation/error-detection contract or fault model is reported.   # pp.789-795
conditions: The design matches Wallace-tree asymptotic depth and has a more regular/simpler cellular layout, while its chip-area order exceeds the array multiplier's O(n2). The speed advantage over an array multiplier increases for longer operands. The evaluation assumes constant gate delay, bounded fan-in, unrestricted fan-out, and zero wire delay.   # pp.790, 793-795
evidence: Sections III-B/III-C, Section IV, Section V-A/V-B, Figs. 3-5, Tables II-III (pp.791-795)

### generalized_signed_digit  (role: instantiates)
mechanism: Each radix-2 digit belongs to {−1, 0, 1}. Addition first produces an intermediate carry/sum pair and then adds the lower-position carry without generating another carry. Each output digit depends on six local operand digits, so parallel addition has constant depth independent of operand length. Negation changes the signs of all nonzero digits in parallel. (pp.790-791)
choices:
  radix: 2   # p.790
  addition_scheme: carry_free   # pp.790-791
  final_conversion: cpa   # p.791
new_choices:
  none
slots:
  none
parameters: digit set {−1, 0, 1}; two addition steps; six input digits determine each result digit; redundant digit encoded by x+ and x− as 00/10/01 for 0/1/−1.   # pp.790-791, 794
results:
| metric | value | unit | technology / device | baseline | condition | page |
| adder depth | constant independent of n | computation elements | abstract combinational circuit; node/device UNKNOWN; 1985 | conventional carry-propagating addition | n-digit redundant-binary addition | p.791 |
| adder gate count | proportional to n | computation elements | abstract combinational circuit; node/device UNKNOWN; 1985 | UNKNOWN | n-digit redundant-binary addition | p.791 |
errors_and_checks: The representation and addition are exact; no fault checks are reported.   # pp.790-791
conditions: Redundancy permits carry-propagation-free addition, but conversion back to conventional binary requires time proportional to log2 n through a CLA.   # pp.790-791
evidence: Section III-A/III-B/III-C, Table I, Fig. 1, Fig. 5 (pp.790-791, 794-795)

## new_families
none

## space_gaps
* The `booth_recoded_parallel` reduction slot lacks `redundant_binary_multiplier`, although the document applies radix-4 Booth recoding directly before a redundant-binary addition tree. (pp.793-794)
* The `generalized_signed_digit.digit_encoding` domain lacks the document's x+/x− encoding, which assigns 00/10/01 to 0/1/−1. (p.794)

## open_questions
* The paper reports that a 16-bit multiplier was implemented elsewhere, but it gives no fabrication process/device or measured silicon area/delay/power for that chip. (pp.790, 795)
* The exposition assumes n is a power of 2 and does not specify the exact tree organization for other positive values of n. (p.790)
