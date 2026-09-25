---
handle: richards_1955#s08
parent: richards_1955
citation: Richards, "Arithmetic Operations in Digital Computers", Van Nostrand, 1955
chapter: COUNTING, BINARY AND DECIMAL
pdf_pages: 204-219
status: ok
kind: book_chapter
unit_classes: [other]
formats: [binary, decimal, 8,4,2,1, 5,4,2,1, 2,4,2,1]
authority: textbook
pages_read: 16 / 16
---

## summary
The chapter classifies binary counters by their carry/storage organization and describes direct, chained, grouped, half-adder, and serial-delay implementations. # p.205-p.209
The chapter also classifies decimal counters made from binary elements, one-hot ring counters, and carry arrangements for native decimal digit counters. # p.210-p.219

## families
### prefix_and_incrementer  (role: taxonomizes)
mechanism: A binary count is incremented when an input pulse toggles the lowest-order storage element and toggles each higher element whose lower-order conditions generate a carry. Carry may ripple through digit counters, pass through a chain of “and” switches, be generated directly from all lower-order 1 states, or combine direct generation within groups with chained propagation between groups. Half adders can combine the stored bit and incoming pulse, while dynamic storage or an n-digit delay line can hold the count serially.
choices:
  structure: ripple_and_chain   # p.205-p.208
  topology: UNKNOWN   # p.205
  dual_direction: UNKNOWN   # p.205
new_choices:
  carry_arrangement: {digit_counter_ripple, simultaneous_all_lower_and, serial_and_chain, grouped_hybrid} — selects how higher-order toggle pulses are formed   # p.205-p.207
  storage_implementation: {bistable_digit_counters, half_adder_static_storage, half_adder_dynamic_storage, recirculating_n_digit_delay_line} — selects the state-holding organization   # p.207-p.209
  hardware_organization: {one_stage_per_bit, bit_serial_reuse} — distinguishes parallel digit stages from one reused half adder and delay line   # p.207-p.209
slots:
  none
parameters: n orders; grouped example uses two groups of 3 digit counters; serial storage uses an n-digit delay line   # p.207, p.209
results:
| metric | value | unit | technology / device | baseline | condition | page |
| carry path through grouped counter | 3 | “and” switches | abstract | direct all-lower “and” switching | sixth digit counter in Fig. 7-4 | p.207 |
| maximum switch input count | 3 | input lines per “and” switch | abstract | direct all-lower “and” switching | Fig. 7-4 | p.207 |
| binary count range | zero to fifteen | input-pulse count | abstract | four-order binary counter | before wraparound | p.209 |
| wraparound output | sixteenth pulse | input pulse | abstract | four-order binary counter | output from highest order | p.209 |
errors_and_checks: none
conditions: The digit-counter ripple arrangement accepts input pulses at the speed of the lowest-order digit counter, but the displayed total may settle slowly after a long carry. # p.205 The simultaneous all-lower “and” arrangement substantially eliminates carry lag, but its switching requirement becomes very great for many orders. # p.205-p.206 The serial “and” chain reduces switching equipment at a moderate cost in carry speed. # p.206 The grouped arrangement bounds both the demonstrated carry-chain length and switch input count at three. # p.207 Dynamic half-adder storage requires pulse amplification/reshaping/retiming and synchronized pulse phases. # p.208-p.209 The n-digit delay-line arrangement requires input pulses to coincide with arrival of the lowest-order digit. # p.209
evidence: Binary Counting; Figs. 7-1 through 7-7

## taxonomy
Counting
  Binary Counting
    binary digit-counter arrangements
      first variation: successive digit-counter carry -> prefix_and_incrementer [structure=ripple_and_chain]   # p.205
      second variation: simultaneous input gated by all lower-order 1 states -> prefix_and_incrementer   # p.205-p.206
      third variation: input pulse chained through “and” switches -> prefix_and_incrementer [structure=ripple_and_chain]   # p.206
      compromise between direct and chained carry -> prefix_and_incrementer   # p.207
      combinations including the first variation -> prefix_and_incrementer   # p.207
    counters employing half adders
      half adders with separate static storage devices -> prefix_and_incrementer [structure=ripple_and_chain]   # p.207-p.208
      half adders with per-order dynamic delay storage -> prefix_and_incrementer [structure=ripple_and_chain]   # p.208-p.209
      one half adder with an n-digit recirculating delay line -> prefix_and_incrementer [hardware_organization=bit_serial_reuse]   # p.209
  Decimal Digit Counters Formed with Binary Elements
    feedback connections -> binary_encoded_modulo_counter   # p.210-p.212
    pulse advancing
      add six after the 8,4,2,1 state 1001 -> binary_encoded_modulo_counter   # p.213
      advance after decimal 8 with a non-8,4,2,1 representation for 9 -> binary_encoded_modulo_counter   # p.213
      add 3 twice with 5,4,2,1 code -> binary_encoded_modulo_counter   # p.213
      advance at decimal 4 with self-complementing 2,4,2,1 code -> binary_encoded_modulo_counter   # p.213
    pulse blocking -> binary_encoded_modulo_counter   # p.215
    parallel connections
      5-counter in parallel with 2-counter -> binary_encoded_modulo_counter   # p.215-p.216
  Ring Counters
    delayed turn-off followed by turn-on -> one_hot_ring_counter   # p.216-p.217
    input directed through “and” switches -> one_hot_ring_counter   # p.216-p.218
    simultaneous turn-off and turn-on -> one_hot_ring_counter   # p.218
    turn-on followed by backward turn-off -> one_hot_ring_counter   # p.218
    alternate stages driven by binary-counter output phases -> one_hot_ring_counter   # p.218-p.219
  Decimal Counters
    successive digit rollover carry -> multi_digit_radix_counter   # p.219
    direct all-lower-digit-9 carry -> multi_digit_radix_counter   # p.219
    chained carry gating -> multi_digit_radix_counter   # p.219
    grouped direct/chained carry -> multi_digit_radix_counter   # p.219
  Counter Components Having More than Two Stable States
    charge-collecting condenser counter -> unmapped   # p.219
    gaseous counter tube -> unmapped   # p.219
    mechanical counter wheel -> unmapped   # p.219

## primary_sources
none

## new_families
### binary_encoded_modulo_counter  (domain: decimal: decimal misc, closest: prefix_and_incrementer, why_not: The modulus is imposed on binary storage by feedback/advancing/blocking/parallel composition rather than by a binary incrementer alone.)
mechanism: Four binary elements provide sixteen possible states, of which six are nullified to form a decimal digit counter. Feedback inserts extra pulses, pulse advancing applies selected input pulses to higher orders, pulse blocking suppresses selected carries, and parallel counters produce an output at the least common multiple of their individual periods.
choices:
  modulus_mechanism: {feedback_connections, pulse_advancing, pulse_blocking, parallel_connections}   # p.210-p.216
  digit_code: {8,4,2,1, 5,4,2,1, 2,4,2,1, nonstandard_nine_state}   # p.213-p.215
  feedback_connections: Int[1..3:1]   # p.210-p.212
  complement_control: Bool   # p.213
results:
| metric | value | unit | technology / device | baseline | condition | page |
| feedback count | N = 2^(n1+n2+n3) - 2^(n1+n3) | input pulses per output pulse | abstract | three binary counter groups | one feedback around the n2 group | p.210 |
| interlocked-feedback count | N = 2^(n1+n2+n3) - 2^n1 - 2^n3 | input pulses per output pulse | abstract | three binary counter groups | Fig. 7-8(d) | p.212 |
| decimal storage cost | 4 | binary counters | abstract | decimal digit counter | all described binary-element decimal arrangements | p.216 |
| parallel-counter period | least common multiple | input pulses per output pulse | abstract | individual counter periods | counters driven in parallel | p.216 |
| decimal parallel composition | least common multiple of 5 and 2 = 10 | input pulses per output pulse | abstract | separate 5-counter and 2-counter | Fig. 7-12 | p.216 |
| relative counting speed | Fig. 7-9(a) greater than Fig. 7-9(b) | qualitative | abstract | alternative feedback counter | lowest-order counter receives no feedback pulse | p.212 |
evidence: Decimal Digit Counters Formed with Binary Elements; Figs. 7-8 through 7-12; p.209-p.216

### one_hot_ring_counter  (domain: shift: bit counting, closest: prefix_and_incrementer, why_not: State advances spatially through one-hot bistable stages rather than through a positional carry/increment network.)
mechanism: A ring contains a series of bistable devices with usually one device on. Each counted pulse moves the on state to the next device. Variants sequence turn-off and turn-on differently, steer pulses with “and” switches, or use alternating outputs from a binary digit counter to drive alternate stages without delay units.
choices:
  closure: {closed, externally_restarted}   # p.216
  pulse_steering: {per_stage_input, and_switch_directed, alternating_phase_driver}   # p.216-p.219
  state_transition: {off_then_on, simultaneous_off_on, on_then_previous_off}   # p.216-p.218
results:
| metric | value | unit | technology / device | baseline | condition | page |
| active state count | 1 | bistable device on | abstract | ring stages | usual ring encoding | p.216 |
| delay units | 0 | delay units | abstract | ordinary ring variants | binary digit counter drives alternate stages | p.218-p.219 |
| closed-ring stage constraint | even number | stages | abstract | direct ring drive | alternating binary-counter outputs | p.219 |
evidence: Ring Counters; Figs. 7-13 and 7-14; p.216-p.219

### multi_digit_radix_counter  (domain: decimal: decimal misc, closest: prefix_and_incrementer, why_not: The carry condition tests radix-minus-one digit states rather than a prefix of binary 1 bits.)
mechanism: A digit counter rolls from radix-minus-one to zero and emits a pulse to the next digit. Decimal counters can reuse the binary chapter’s successive, direct, chained, and grouped carry arrangements when each decimal digit counter supplies a rollover pulse or a static indication of 9.
choices:
  radix: Int[2..16:1]   # p.204, p.209, p.219
  carry_arrangement: {successive_rollover, simultaneous_all_lower_terminal, serial_gate_chain, grouped_hybrid}   # p.219
  carry_signal_timing: {arriving_at_zero, leaving_nine}   # p.219
results:
| metric | value | unit | technology / device | baseline | condition | page |
| carry timing speed | leaving 9 is “a bit faster” | qualitative | abstract | arriving at 0 | successive decimal carry | p.219 |
evidence: chapter introduction; Decimal Counters; p.204, p.219

## space_gaps
* prefix_and_incrementer lacks direct unbounded-fan-in lower-bit gating, grouped direct/chained carry, dynamic per-bit storage, and bit-serial half-adder reuse choices. # p.205-p.209
* The vocabulary lacks binary-encoded modulo counters based on feedback/pulse advancing/pulse blocking/parallel-period composition. # p.210-p.216
* The vocabulary lacks one-hot ring counters and their state-transition sequencing choices. # p.216-p.219
* The vocabulary lacks radix-general digit counters whose carry predicate is the terminal digit state. # p.204, p.219

## open_questions
* The chapter does not quantify component delays or maximum pulse rates for the binary carry arrangements. # p.205-p.207
* The chapter does not specify a named prefix topology for simultaneous all-lower-bit carry generation. # p.205-p.206
* The chapter omits implementation details for amplification/reshaping/retiming in dynamic half-adder storage. # p.209
* The chapter gives no common functional analysis for counter components having more than two stable states. # p.219
