---
handle: macsorley1961
citation: O. L. MacSorley, "High-Speed Arithmetic in Binary Computers", Proceedings of the IRE, vol. 49, no. 1, pp. 67-91, 1961
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [binary_integer, binary_floating_point]
authority: survey
pages_read: 67-91 / 25
---

## summary
The report describes and compares high-speed binary addition/multiplication/division methods using logical-level delay and logical-unit count. It covers fixed/variable-time adders, recoded sequential multiplication, carry-save multiplication, and variable-shift division with several divisor multiples. # pp.67-91

## families
### ripple_carry  (role: analyzes)
mechanism: Full-adder stages connect each carry output directly to the next stage. The worst-case addition path is two logical levels per bit. # p.68
choices:
  carry_polarity_alternation: UNKNOWN
new_choices:
  none
slots:
  full_adder_cell: UNKNOWN   # p.68
parameters: 50-bit and 100-bit adders   # pp.68-70
results:
| metric | value | unit | technology / device | baseline | condition | page |
| delay | 100 | logical levels | technology UNKNOWN; year 1961 | none | 50-bit adder | p.70 |
| logical units | 400 | logical units | technology UNKNOWN; year 1961 | none | 50-bit adder | p.70 |
| delay | 200 | logical levels | technology UNKNOWN; year 1961 | none | 100-bit adder | p.70 |
| logical units | 800 | logical units | technology UNKNOWN; year 1961 | none | 100-bit adder | p.70 |
errors_and_checks: none
conditions: The worst case assumes a carry generated in the first stage and propagated through every intervening stage. # p.68
evidence: §Binary Adders, Fixed Time; Fig. 1; Table II, pp.68-70

### carry_lookahead  (role: compares)
mechanism: Generated/transmitted carries are expanded into AND/OR expressions. Five bits form a group, five groups form a section, and look-ahead can operate within groups/between groups/between sections. # pp.68-70
choices:
  group_size: 5   # p.68
  levels: 3   # p.69
  intergroup_carry: lookahead   # p.69
  block_sizing: uniform   # p.69
new_choices:
  none
slots:
  none
parameters: 5-bit groups; 25-bit sections; 50-bit and 100-bit adders   # pp.68-70
results:
| metric | value | unit | technology / device | baseline | condition | page |
| delay | 12 | logical levels | technology UNKNOWN; year 1961 | 100 logical levels for ripple carry | 50-bit full look-ahead | p.70 |
| logical units | 636 | logical units | technology UNKNOWN; year 1961 | 400 logical units for ripple carry | 50-bit full look-ahead | p.70 |
| delay | 14 | logical levels | technology UNKNOWN; year 1961 | 200 logical levels for ripple carry | 100-bit full look-ahead | p.70 |
| logical units | 1294 | logical units | technology UNKNOWN; year 1961 | 800 logical units for ripple carry | 100-bit full look-ahead | p.70 |
errors_and_checks: none
conditions: Circuit input-count limitations bound the number of stages connected at each look-ahead level. # p.68
evidence: Figs. 2-3; Tables I-II, pp.68-70

### carry_skip  (role: instantiates)
mechanism: A carry-bypass circuit inside each five-bit group accelerates a ripple connection between groups. # p.70
choices:
  block_width: 5   # p.70
  block_sizing: uniform   # p.70
  skip_levels: 1   # p.70
  skip_gate: and_or_bypass   # p.70
new_choices:
  none
slots:
  block_adder: ripple_carry   # p.70
parameters: 50-bit and 100-bit adders   # p.70
results:
| metric | value | unit | technology / device | baseline | condition | page |
| delay | 36 | logical levels | technology UNKNOWN; year 1961 | 100 logical levels for ripple carry | 50-bit adder | p.70 |
| logical units | 410 | logical units | technology UNKNOWN; year 1961 | 400 logical units for ripple carry | 50-bit adder | p.70 |
| delay | 52 | logical levels | technology UNKNOWN; year 1961 | 200 logical levels for ripple carry | 100-bit adder | p.70 |
| logical units | 820 | logical units | technology UNKNOWN; year 1961 | 800 logical units for ripple carry | 100-bit adder | p.70 |
errors_and_checks: none
conditions: The paper identifies percentage speed improvement per unit cost as the bypass method's principal merit. # p.70
evidence: modification 3 and Table II, p.70

### speculative_variable_latency  (role: instantiates)
mechanism: Separate carry/no-carry signals ripple through every position. Completion occurs when exactly one signal is asserted at each position, so operation waits for actual carry completion. # p.71
choices:
  detection: completion_sensing   # p.71
  recovery: await_completion   # p.71
new_choices:
  completion_encoding: separate_carry_no_carry — completion is recognized from mutually exclusive C/N signals at every bit.   # p.71
slots:
  base_adder: ripple_carry   # pp.70-71
parameters: 100-bit example; average longest carry no greater than log2 N   # pp.70-71
results:
| metric | value | unit | technology / device | baseline | condition | page |
| average longest carry | 5.6 | bit positions | technology UNKNOWN; year 1961 | none | random 50-bit additions | p.70 |
| average longest carry | 6.6 | bit positions | technology UNKNOWN; year 1961 | none | random 100-bit additions | p.70 |
| logical units | approximately 1280 | logical units | technology UNKNOWN; year 1961 | 1294 logical units for full look-ahead | 100-bit completion-recognition adder | p.71 |
errors_and_checks: Completion logic must avoid transient false completion; some recognition equipment may also serve checking circuitry. # pp.70-71
conditions: Inputs must arrive simultaneously/remain unchanged, and inputs must be cleared or forced before the next operation. These restrictions may nullify the average-time advantage. # p.71
evidence: §Binary Adders, Variable Time; Fig. 4, pp.70-71

### sequential_shift_add  (role: extends)
mechanism: Multiplier runs are recoded into multiplicand additions/subtractions. Variable shifting crosses runs of equal bits, while uniform two-bit/three-bit grouping performs one operation per group using shifted multiples. # pp.71-75
choices:
  bits_per_cycle: 2 [one compared value]   # pp.73-74
  bits_per_cycle: 3 [one compared value]   # p.74
  accumulator_form: carry_propagate   # p.75
  string_skipping: true   # pp.71-73
new_choices:
  shift_schedule: {variable_run_length, uniform_2_bit, uniform_3_bit} — multiplier scanning may skip runs or use fixed groups.   # pp.71-75
slots:
  step_adder: carry_lookahead [group_size=5]   # p.75
parameters: shifted multiples 1/2/4 for two-bit groups and 1/2/4/6/8 for three-bit groups   # pp.73-74
results:
| metric | value | unit | technology / device | baseline | condition | page |
| average shift per addition | 3.0 | bit positions | technology UNKNOWN; year 1961 | none | infinite shifter | p.73 |
| average shift per addition | 2.9 | bit positions | technology UNKNOWN; year 1961 | none | shifter limit 6 | p.73 |
errors_and_checks: exact arithmetic; none
conditions: Uniform shifts give a predictable cycle count and support cascaded carry-save adders. Three-bit grouping requires generation/storage of six times the multiplicand. # pp.73-76
evidence: §§Multiplication Using Variable Length Shift/Uniform Shifts; Tables III-IV, pp.71-75

### carry_save_datapath  (role: extends)
mechanism: Each 3:2 adder stores sum and shifted carry separately, delaying carry propagation until a terminal CPA. Three serial carry-save adders accept four decoded multiplier groups before the final CPA. # pp.75-77
choices:
  compressor: 3_2   # pp.75-76
  assimilation_point: end_of_chain   # p.76
  accumulator_redundant: true   # p.76
new_choices:
  none
slots:
  assimilator: UNKNOWN   # p.76
parameters: three serial CSAs; eight multiplier bits per cycle; 16-bit example   # pp.76-78
results:
| metric | value | unit | technology / device | baseline | condition | page |
| original CSA size | 75 | full adder units | technology UNKNOWN; year 1961 | none | three 25-position CSAs | p.79 |
| reduced CSA size | 45 plus three modified | units | technology UNKNOWN; year 1961 | 75 full adder units | terminated low/high positions | p.79 |
| saving | 27 | units | technology UNKNOWN; year 1961 | original CSA arrangement | component-reduced design | p.79 |
errors_and_checks: exact arithmetic; none
conditions: Fixed multiplier grouping is preferred when several adders are cascaded because multiple variable shifters lengthen/complicate decoding. # p.76
evidence: §§Multiplication Using Carry-Save Adders/Component Reduction; Figs. 6-8, pp.75-80

## new_families
### variable_shift_nonrestoring_division  (domain: dividers / square root, closest: restoring_nonrestoring, why_not: The vocabulary family is fixed-iteration, while this method shifts across determined quotient runs and has data-dependent cycle counts.)
mechanism: The divider adds a true/complement divisor to a true/complement partial dividend, decodes leading equal bits, and shifts across quotient zeros or ones until another addition is needed. Variants select 1/2/1/2 or 3/4/1/3/2 divisor multiples through coded selection, optimum selection, or parallel trial additions. # pp.80-90
choices: shift_policy: {zeros_only, zeros_and_ones}; divisor_multiple_set: {1, half_one_two, three_quarters_one_three_halves}; selection: {coded_single_adder, double_adder, optimum}; shifter_limit: {4, 6, 8, none}
results:
| metric | value | unit | technology / device | baseline | condition | page |
| average bits per cycle | 2.54 | bits/cycle | technology UNKNOWN; year 1961 | none | one-times divisor; five-bit divisor | p.84 |
| average bits per cycle | 2.74 | bits/cycle | technology UNKNOWN; year 1961 | 2.82 double-adder | half/one/two coded selection | p.86 |
| average bits per cycle | 3.57 | bits/cycle | technology UNKNOWN; year 1961 | 3.51 double-adder | 3/4/1/3/2 optimum selection | p.88 |
| methods 1-8, unlimited shifter | 1.86/2.66/2.86/2.94/3.59/3.77/3.75/3.82 | bits per shift cycle | technology UNKNOWN; year 1961 | method 1 | Table VII method order | p.91 |
| methods 1-8, shifter limit 4 | 1.76/2.39/2.53/2.61/2.98/3.07/3.08/3.03 | bits per shift cycle | technology UNKNOWN; year 1961 | method 1 | Table VII method order | p.91 |
evidence: §§Binary Division/Comparative Evaluation; Figs. 9-16; Tables V-VII, pp.80-91

## space_gaps
* `sequential_shift_add` lacks a choice for add/subtract multiplier recoding and variable versus uniform shift scheduling. # pp.71-75
* The divider vocabulary lacks data-dependent shifting across quotient-bit runs and trial selection among divisor multiples. # pp.80-91
* `carry_save_datapath` lacks structural choices for serial CSA count and component-reducing termination of unused high/low positions. # pp.76-80

## open_questions
* The paper describes logical blocks rather than a fabrication technology, so every technology field remains `UNKNOWN`.
* The terminal CPA topology in the carry-save multiplication example is not fixed. # pp.76-80
