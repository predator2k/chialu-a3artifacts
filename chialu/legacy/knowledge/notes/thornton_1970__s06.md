---
handle: thornton_1970#s06
parent: thornton_1970
citation: J. E. Thornton, "Design of a Computer: The Control Data 6600", Scott, Foresman and Co., 1970
chapter: CENTRAL PROCESSOR FUNCTIONAL UNITS
pdf_pages: 35-64
status: ok
kind: book_chapter
unit_classes: [BINARY_ALU]
formats: [60-bit one's-complement fixed point, 60-bit one's-complement floating point, 18-bit one's-complement fixed point]
authority: textbook
pages_read: 30 / 30
---

## summary
The chapter defines the Control Data 6600 fixed-add, floating-add, shift, multiply, divide, population-count, and increment datapaths. It settles their recurrences, widths, parallel structures, execution times, and machine-specific rounding behavior. It classifies multiplication by parallel subdivision/carry-save/radix and shifting by fixed-column parallel networks.   # p.35-p.62

## families
### carry_lookahead  (role: instantiates)
mechanism: The Fixed Add Unit forms borrow-generation and borrow-pass terms simultaneously. Three-bit groups feed intermediate twelve-bit groups, which combine across 60 bits before local sum completion. The floating Add Unit uses a related 98-bit parallel borrow network with successive groupings of two, three, three, and six. The shared 18-bit Increment network uses the same general addition method.   # p.39-p.40, p.49-p.51, p.62
choices:
  group_size: 3   # p.40
  levels: 3   # p.40
  intergroup_carry: lookahead   # p.40
  block_sizing: UNKNOWN   # p.40
new_choices:
  arithmetic_signal: borrow_generate_pass — the networks propagate borrow rather than carry terms   # p.39-p.40
slots: none
parameters: 60-bit fixed adder; 98-bit floating adder; 18-bit shared Increment adder   # p.40, p.49-p.51, p.62
results:
| metric | value | unit | technology / device | baseline | condition | page |
| longest fixed-add path | 16 | inversions | abstract | shortest path | excluding input flip-flop | p.40 |
| shortest fixed-add path | 5 | inversions | abstract | longest path | excluding input flip-flop | p.40 |
| fixed-add network modules | 20 FA + 5 FB + 1 FC + 4 FD + 20 FE | modules | abstract | none | 60-bit network | p.40 |
errors_and_checks: The fixed unit tests positive/negative zero, sign, floating range, and indefinite encodings when partnered with the Branch Unit.   # p.41
conditions: Stable input registers allow paths of unequal length to settle before sampling.   # p.40

### end_around_carry  (role: defines)
mechanism: One's-complement addition returns the most-significant carry to the least-significant position. The subtractive form closes the borrow network by making the final borrow equal to the initial borrow. Exponent comparison also uses the existence of an end-around borrow to select the larger exponent or successful divisor subtraction.   # p.39, p.48-p.49, p.58-p.59
choices:
  modulus: mod_2n_minus_1   # p.39
  recirculation: cyclic_prefix_level   # p.39
  topology: UNKNOWN   # p.39-p.40
new_choices: none
slots: none
parameters: 60-bit fixed addition; 12-bit exponent subtraction; 48-bit divide subtraction   # p.39, p.48, p.59
results:
| metric | value | unit | technology / device | baseline | condition | page |
| serial end-around cost | another pass through the adder | pass | abstract | ordinary serial addition | one's-complement bit-serial adder | p.39 |
errors_and_checks: Positive and negative zero are both recognized as zero by branch testing.   # p.41
conditions: End-around borrow is available sooner than the sign in the 48-bit divide subtractors.   # p.59

### barrel_mux_tree  (role: instantiates)
mechanism: Six logic columns correspond to the six shift-count bits. Each column passes the word unchanged or displaces it by that bit's weight. The same unit supports left circular shifts and right end-off shifts with sign extension. Two columns are packaged per module set.   # p.43-p.44
choices:
  stage_radix: 2   # p.43
  select_encoding: binary   # p.43
  direction_handling: mirrored_datapath   # p.44
  stage_order: small_shift_first   # p.44
  sticky_collect: false   # p.43-p.45
new_choices: none
slots: none
parameters: 60-bit word; six shift-count bits; shifts from one to 60 places   # p.43-p.44
results:
| metric | value | unit | technology / device | baseline | condition | page |
| shift-network latency | 1 | minor cycle | Control Data 6600, 1970 | variable-cycle serial shift | any supported left/right shift | p.44 |
| shift-network size | 60 | modules | Control Data 6600, 1970 | none | controls excluded | p.44 |
| gate fan-in | 3 | inputs | abstract | none | shift-network OR element | p.44 |
| gate fan-out | 3 | loads | abstract | none | each shift column | p.44 |
errors_and_checks: none
conditions: The parallel network makes execution time independent of shift distance.   # p.43-p.44

### single_path  (role: instantiates)
mechanism: The floating Add Unit compares exponents, selects the smaller coefficient, aligns it in a seven-stage right-shift network, adds a 98-bit signed coefficient path, selects the upper or lower half, and applies overflow correction. Rounded and unrounded single precision and unrounded double precision share this datapath.   # p.45, p.48-p.51
choices:
  pipeline_depth: UNKNOWN   # p.45
  post_round_renorm: true   # p.47, p.49-p.51
new_choices:
  precision_result_selection: upper_or_lower_half — single and double instructions select different halves of the double-length result   # p.47
slots:
  sig_adder: carry_lookahead [group_size=3]   # p.49-p.51
  round: injection   # p.49
  exp: exponent_path   # p.48-p.49
  subnormal: flush_to_zero_mode   # p.46-p.48
  align: full_align   # p.49-p.50
  norm: single_barrel   # p.47, p.51
parameters: 48-bit coefficient; 11-bit exponent; 98-bit adder; 96-bit shift output plus two sign bits   # p.45, p.49
results:
| metric | value | unit | technology / device | baseline | condition | page |
| execution time | 400 | nanoseconds | Control Data 6600, 1970 | none | includes result-register transfer | p.45 |
| right-shift depth | 7 | inverters | abstract | none | seven-bit shift count | p.49 |
errors_and_checks: Exponent overflow produces infinity; underflow produces a zero exponent; prescribed infinity/indefinite operand combinations follow Table V.   # p.46-p.48
conditions: The dedicated unit handles only floating addition/subtraction, which removes unrelated functions from its datapath.   # p.46

### iterative_reuse  (role: instantiates)
mechanism: The multiplier divides the multiplier into two 24-bit halves. Each half repeatedly traverses three carry-save layers, processes six multiplier bits per step, and deposits shifted product bits in holding registers. Four iterations produce the two unmerged partial products before a final parallel merge.   # p.53-p.56
choices:
  instantiated_fraction: half   # p.53
  iteration_pipeline_overlap: true   # p.51
new_choices:
  bits_per_iteration_per_half: 6 — three layers process two multiplier bits each   # p.53
slots:
  partial_tree: csa_reduction_tree   # p.53-p.56
parameters: two 24-bit halves; three carry-save layers; four iterations; 48-bit operands; 72-bit half-product registers   # p.53-p.55
results:
| metric | value | unit | technology / device | baseline | condition | page |
| carry-save work per cycle | 3 | additions per 100 nanoseconds | Control Data 6600, 1970 | one conventional parallel addition | one minor cycle | p.54 |
| first result latency | 1000 | nanoseconds | Control Data 6600, 1970 | Add Unit at 400 nanoseconds | one Multiply Unit | p.51 |
| overlapped second-half cost | 100 | nanoseconds | Control Data 6600, 1970 | first half at 1000 nanoseconds | two Multiply Units and distinct result registers | p.51 |
errors_and_checks: Carries remain represented by pseudo-sum/pseudo-carry until the final merge.   # p.53-p.56
conditions: Reuse reduces hardware while retaining two-way half-product parallelism.   # p.51-p.53

### carry_save_datapath  (role: defines)
mechanism: A three-input/two-output adder produces pseudo-sum and pseudo-carry. The pseudo-carry stores the unpropagated part of the carry equation, so each layer propagates carry only one position. Pseudo-sum/pseudo-carry feed later layers until a conventional carry network assimilates the result.   # p.53-p.56
choices:
  compressor: 3_2   # p.53
  assimilation_point: end_of_chain   # p.53, p.55-p.56
  accumulator_redundant: true   # p.53-p.55
new_choices: none
slots:
  assimilator: carry_lookahead   # p.55-p.56
parameters: three cascaded carry-save networks; maximum five inverters per network and fifteen across three networks   # p.54
results:
| metric | value | unit | technology / device | baseline | condition | page |
| single-network depth | 5 | inverters | abstract | none | longest path | p.54 |
| three-network depth | 15 | inverters | abstract | none | includes register by clear-set technique | p.54 |
| final carry propagation | approximately 1 | minor cycle | Control Data 6600, 1970 | none | product merge | p.55 |
errors_and_checks: The pseudo-sum and pseudo-carry terms are mutually exclusive, so a stored carry cannot exceed one.   # p.54
conditions: Carry-save is effective for repetitive additions because full propagation occurs only at completion.   # p.52-p.54

### sig_mul_then_round  (role: instantiates)
mechanism: The floating multiplier forms a 96-bit coefficient product, calculates upper/lower exponents in parallel, merges saved carries, optionally normalizes by one left shift, and selects an upper or lower result. Rounding presets one-quarter relative to the upper integer product into the merge network.   # p.51, p.56-p.57
choices: none
new_choices:
  rounding_bias: slightly_toward_zero [outside domain] — preset rounding is approximate rather than nearest-even   # p.57
slots:
  sig_mul: iterative_reuse   # p.53-p.56
  round: injection   # p.56-p.57
  exp: exponent_path   # p.56
  subnormal: flush_to_zero_mode   # p.56
parameters: 48-bit significands; 96-bit product; single/double precision outputs   # p.51, p.56
results:
| metric | value | unit | technology / device | baseline | condition | page |
| execution time | 1000 | nanoseconds | Control Data 6600, 1970 | floating Add Unit at 400 nanoseconds | includes result transfer | p.51 |
| normalization displacement | 1 | bit | abstract | none | both operands normalized | p.51 |
errors_and_checks: Preset rounding rounds half of shifted products and one quarter of unshifted products upward, which biases results slightly toward zero.   # p.57
conditions: Double precision is favored for unnormalized arithmetic; normalized operands need at most a one-bit correction.   # p.51

### restoring_nonrestoring  (role: extends)
mechanism: Three parallel subtractors try the divisor, twice the divisor, and three times the divisor against the partial dividend. End-around-borrow signals select the largest successful subtraction and emit two quotient bits. The selected residual shifts left two places before the next iteration.   # p.57-p.59
choices:
  style: nonperforming   # p.58-p.59
  bits_per_cycle: 2   # p.58
  shift_over_zeros: false   # p.58
new_choices:
  parallel_trial_multiples: 3 — each iteration tries 1X/2X/3X simultaneously   # p.58
slots:
  residual_adder: carry_lookahead   # p.58-p.59
parameters: 48-bit coefficients; three subtract networks; 25 subtractions and 24 shifts   # p.58-p.59
results:
| metric | value | unit | technology / device | baseline | condition | page |
| division latency | 2900 | nanoseconds | Control Data 6600, 1970 | none | floating division | p.57 |
| subtraction latency | 1 | minor cycle | Control Data 6600, 1970 | none | borrow must reach selection logic | p.59 |
errors_and_checks: The unit corrects only a single-bit quotient overflow and assumes normalized arithmetic or software protection against larger divide overflow.   # p.58-p.59
conditions: End-around-borrow shortens quotient selection relative to waiting for the residual sign.   # p.59

### sig_div_then_round  (role: instantiates)
mechanism: The floating Divide Unit wraps the two-bit recurrence with exponent subtraction, a 60-octal exponent reduction, optional one-bit overflow correction, sign restoration, and preset rounding. The preset one-third dividend value produces a final rounding contribution ranging from one-third to two-thirds for normalized divisors.   # p.59
choices: none
new_choices:
  rounding_bias: slightly_toward_zero [outside domain] — overflow-shift cases bias preset rounding toward zero   # p.59
slots:
  sig_div: restoring_nonrestoring [bits_per_cycle=2]   # p.58-p.59
  round: injection   # p.59
  exp: exponent_path   # p.59
  subnormal: UNKNOWN   # p.57-p.59
parameters: 48-bit coefficient; 25 subtraction steps; preset round value one-third of the integer dividend   # p.59
results:
| metric | value | unit | technology / device | baseline | condition | page |
| execution time | 2900 | nanoseconds | Control Data 6600, 1970 | population count at 800 nanoseconds | floating division | p.57 |
errors_and_checks: Rounding adds no execution time but is biased slightly toward zero in right-shift cases.   # p.59
conditions: The unit assumes normalized arithmetic or program protection against divide overflow.   # p.58

### popcount_counter_tree  (role: instantiates)
mechanism: Fifteen first-column circuits convert the sixty input bits in four-bit groups into three-bit counts. A tree then adds the fifteen quantities two at a time through four add cycles.   # p.59-p.61
choices:
  counter_primitive: lut_rom [outside domain]   # p.59, p.61
  tree_shape: balanced_tree   # p.59-p.60
  lane_taps: false   # p.59-p.60
new_choices:
  first_stage_counter: 4_to_3 — each four-bit group becomes a three-bit count   # p.59
slots:
  final_adder: carry_lookahead   # p.59-p.60
parameters: 60 input bits; fifteen three-bit first-stage values; four summing cycles   # p.59-p.60
results:
| metric | value | unit | technology / device | baseline | condition | page |
| execution time | 800 | nanoseconds | Control Data 6600, 1970 | divide at 2900 nanoseconds | count ones in a 60-bit word | p.57, p.59 |
errors_and_checks: none
conditions: The Population Count shares the Divide Unit rather than using a separate functional unit.   # p.57-p.59

## taxonomy
Central Processor functional units   # p.35-p.36
  Boolean Unit -> unmapped   # p.35-p.38
  Shift Unit   # p.42-p.45
    left circular/right end-off shift -> barrel_mux_tree   # p.43-p.44
    normalize leading-bit search -> lzd_cell_tree   # p.44-p.45
    pack/unpack/mask -> unmapped   # p.43-p.45
  Fixed Add Unit   # p.38-p.41
    additive one's-complement adder -> end_around_carry   # p.39
    subtractive parallel borrow network -> carry_lookahead   # p.39-p.40
  Add Unit   # p.45-p.51
    rounded single precision -> single_path   # p.45, p.49
    unrounded single precision -> single_path   # p.45
    unrounded double precision -> single_path   # p.45, p.47
  Multiply Units   # p.51-p.57
    simple add and shift -> sequential_shift_add   # p.52
    separated multiplier halves -> iterative_reuse   # p.52-p.53
    carry-save addition -> carry_save_datapath   # p.52-p.56
    multiple multiplier bits per step -> iterative_reuse   # p.52-p.53
    floating product and rounding -> sig_mul_then_round   # p.51, p.56-p.57
  Divide Unit   # p.57-p.59
    successive subtraction and shift -> restoring_nonrestoring   # p.57-p.59
    floating wrapper and rounding -> sig_div_then_round   # p.59
    Population Count -> popcount_counter_tree   # p.59-p.61
  Increment Units -> carry_lookahead   # p.59-p.62
  Branch Unit -> unmapped   # p.62-p.64
  ECS Coupler-Controller -> unmapped   # p.64

## primary_sources
none

## new_families
none

## space_gaps
* `carry_lookahead` lacks a value for the chapter's mixed two/three/six-term borrow-group hierarchy.   # p.49-p.51
* `sig_mul_then_round` and `sig_div_then_round` lack a choice for deliberately biased preset rounding.   # p.57, p.59
* `prefix_and_incrementer` does not describe the chapter's Increment Units, which perform arbitrary 18-bit addition/subtraction through a shared parallel adder.   # p.59-p.62
* `popcount_counter_tree.counter_primitive` lacks the chapter's custom 4-to-3 first-stage counter.   # p.59, p.61

## open_questions
* The chapter calls the Divide Unit a successive-subtraction design but does not label it restoring, nonperforming, or nonrestoring. The `nonperforming` mapping follows its selection of only successful trial subtractions and should be reviewed.   # p.57-p.59
* The chapter does not name the fixed/floating parallel borrow topology, so no named prefix topology can be assigned.   # p.39-p.40, p.49-p.51
