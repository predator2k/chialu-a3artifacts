---
handle: zimmermann1997#s03
parent: zimmermann1997
citation: zimmermann1997 — Binary Adder Architectures for Cell-Based VLSI and their Synthesis
chapter: Basic Conditions and Implications
pdf_pages: 9-19
status: ok
kind: thesis_chapter
unit_classes: [BINARY_ALU]
formats: [fixed-point binary, unsigned, two's complement, one's complement, sign magnitude, carry-save, delayed-carry, signed-digit, residue]
authority: thesis
pages_read: 11 / 11
---

## summary
The chapter defines carry-save, delayed-carry, signed-digit, residue, and conventional binary representations and explains their implications for addition structures. It establishes that carry-save and signed-digit adders avoid carry propagation but normally require a carry-propagate conversion before conventional processing. It also selects unit-gate area/delay/power models for abstract comparisons of combinational cell-based adders.

## families
### ripple_carry  (role: analyzes)
mechanism: The ripple-carry adder is identified as the simplest carry-propagate architecture. A self-timed realization benefits from its short average carry-propagation length because completion follows the actual carry path.
choices:
  full_adder_cell: UNKNOWN   # p.12
  carry_polarity_alternation: UNKNOWN   # p.12
new_choices:
  timing_style: self_timed — completion signals indicate when combinational evaluation has finished   # p.12
slots:
  none
parameters: operand width n   # p.12
results:
| metric | value | unit | technology / device | baseline | condition | page |
| average carry-propagation length | log₂ n | bit positions | abstract | worst-case word-length-dependent propagation | self-timed realization | p.12 |
errors_and_checks: Self-timed combinational circuits require completion signals, which are not trivial to generate.   # p.12
conditions: The ripple-carry architecture takes the greatest advantage of self-timed implementation because its average carry-propagation length is short.   # p.12
evidence: Sections 2.1.5 and 2.1.6.

### carry_save_datapath  (role: defines)
mechanism: Carry-save represents the result of adding three numbers without carry propagation. The representation contains two numbers, one holding the carry bits and one holding the sum bits, so the carries remain available for later propagation. Carry-save adders support fast multioperand addition but normally require a carry-propagate adder to produce an irredundant integer result.
choices:
  compressor: 3_2   # p.12
  assimilation_point: end_of_chain   # p.13
  accumulator_redundant: true   # p.12
new_choices:
  none
slots:
  assimilator: UNKNOWN   # p.13
parameters: three input numbers reduced to two output numbers   # p.12
results:
| metric | value | unit | technology / device | baseline | condition | page |
| carry-propagation path | absent | structural property | abstract | carry-propagate addition | redundant carry-save result retained | p.13 |
| further optimization potential | minimal | qualitative | abstract | UNKNOWN | simple carry-save structure | p.13 |
| gate equivalent | 1 2-input NAND-gate = 4 MOSFETs | gate equivalent | abstract | unit-gate model | generic cell-based circuit estimation | p.16 |
| basic monotonic 2-input gate area | 1 | unit gate | abstract | AND/OR/NAND/NOR | unit-gate area model | p.17 |
| XOR/XNOR area | 2 | unit gates | abstract | basic monotonic 2-input gate | unit-gate area model | p.17 |
| basic 2-input gate delay | 1 | gate delay | abstract | AND/OR/NAND/NOR | unit-gate delay model | p.18 |
| XOR/XNOR delay | 2 | gate delays | abstract | basic 2-input gate | unit-gate delay model | p.18 |
| assumed average input transition activity | 50% | input transitions | abstract | random data-path inputs | each input toggles each second clock cycle | p.19 |
| average power dissipation | approximately proportional to circuit size | proportionality | abstract | constant input switching activity | arithmetic units | p.19 |
errors_and_checks: none
conditions: Carry-save addition is important for multioperand circuits and is fast because no carry-propagation path exists.   # p.12, p.13
conditions: Carry-save results usually require conversion by a carry-propagate adder before further processing.   # p.13
conditions: The unit-gate model provides abstract area/delay/power comparisons before technology mapping and physical layout, but it cannot model detailed circuit/layout effects accurately.   # p.16, p.19
evidence: Sections 2.1.3, 2.1.6, 2.5.1, 2.5.2, 2.5.3, and 2.5.5.

### generalized_signed_digit  (role: defines)
mechanism: Signed-digit arithmetic uses the redundant digit set {-1, 0, 1}. Signed-digit adders avoid carry-propagation paths and produce redundant results that normally require conversion to an irredundant integer representation.
choices:
  radix: 2   # p.12
  redundancy: UNKNOWN   # p.12
  digit_encoding: UNKNOWN   # p.12
  addition_scheme: carry_free   # p.13
  final_conversion: cpa   # p.13
new_choices:
  none
slots:
  none
parameters: digit set {-1, 0, 1}   # p.12
results:
| metric | value | unit | technology / device | baseline | condition | page |
| carry-propagation path | absent | structural property | abstract | carry-propagate addition | redundant signed-digit result retained | p.13 |
| further optimization potential | minimal | qualitative | abstract | UNKNOWN | simple redundant-adder structure | p.13 |
errors_and_checks: none
conditions: Signed-digit results normally require conversion by a carry-propagate adder before further processing.   # p.13
evidence: Sections 2.1.3 and 2.1.6.

### rns_channel_arithmetic  (role: analyzes)
mechanism: A residue number system uses a set of different residues rather than one fixed radix. Each digit has a different radix, so arithmetic operations can be computed independently and in parallel on the digits using normal or modular integer arithmetic.
choices:
  modulus_form: UNKNOWN   # p.12
  channel_width_n: UNKNOWN   # p.12
  pow2_plus_1_encoding: UNKNOWN   # p.12
  multiplier_reduction: UNKNOWN   # p.12
new_choices:
  none
slots:
  modular_adder: UNKNOWN   # p.12
parameters: residue set and digit count UNKNOWN   # p.12
results:
| metric | value | unit | technology / device | baseline | condition | page |
| channel execution | independent and parallel | qualitative | abstract | conventional fixed-radix arithmetic | arithmetic performed per residue digit | p.12 |
errors_and_checks: none
conditions: Residue arithmetic provides considerable speed-up, but conversion to and from conventional number systems is very expensive.   # p.12
conditions: Individual residue operations still rely mainly on normal or modular additions.   # p.12
evidence: Section 2.1.3.

## taxonomy
Number representations   # p.11, p.12
  Binary number systems   # p.11
    Unsigned numbers -> unmapped   # p.11
    Two's complement -> unmapped   # p.11
    One's complement -> unmapped   # p.11
    Sign magnitude -> unmapped   # p.11
  Redundant number systems   # p.12
    Carry-save -> carry_save_datapath   # p.12
    Delayed-carry or half-adder form -> unmapped   # p.12
    Signed-digit -> generalized_signed_digit   # p.12
  Residue number systems -> rns_channel_arithmetic   # p.12
Adder circuit realization   # p.12
  Sequential circuits   # p.12
    Bit-serial adders -> unmapped   # p.12
    Pipelined adders -> unmapped   # p.12
  Combinational circuits   # p.12
    Carry-propagate adders -> unmapped   # p.12
    Carry-save adders -> carry_save_datapath   # p.12, p.13
Circuit-estimation models   # p.17, p.18
  Area models   # p.17
    Unit-gate area model -> unmapped   # p.17
    Fan-in area model -> unmapped   # p.17
    Gate-equivalents and other detailed models -> unmapped   # p.17
  Delay models   # p.18
    Unit-gate delay model -> unmapped   # p.18
    Fan-in delay model -> unmapped   # p.18
    Fan-out delay model -> unmapped   # p.18
    Transistor-level and complex-gate models -> unmapped   # p.18

## primary_sources
none

## new_families
none

## space_gaps
* The delayed-carry or half-adder representation for adding two numbers has no vocabulary family.   # p.12
* The vocabulary has no cross-family unit-gate area/delay/power model for recording the abstract comparison framework adopted by the chapter.   # p.17, p.18, p.19
* The carry_save_datapath assimilator slot cannot express an unspecified generic carry-propagate adder without selecting a concrete family.   # p.13

## open_questions
* The chapter does not specify which carry-propagate architecture converts carry-save or signed-digit results.   # p.13
* The chapter does not specify the residue moduli, channel widths, or modular-adder architecture.   # p.12
* The chapter does not settle a vocabulary encoding or redundancy class for the signed-digit set {-1, 0, 1}.   # p.12
