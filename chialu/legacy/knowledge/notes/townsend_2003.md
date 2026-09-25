---
handle: townsend_2003
citation: W. J. Townsend, J. A. Abraham, E. E. Swartzlander, "Quadruple Time Redundancy Adders", Proc. 16th IEEE Symposium on Computer Arithmetic (ARITH-16), pp. 250-256, 2003
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [int8, int16, int32, int64]
authority: incremental
pages_read: 7 / 7
---

## summary
Quadruple Time Redundancy uses three quarter-width ripple-carry adders over four iterations with majority voting to provide concurrent error correction. The gate-level comparison covers non-redundant, TMR, TSTMR, and QTR adders from 8 to 64 bits. QTR reduces hardware complexity relative to TSTMR while increasing delay.

## families
### time_redundancy  (role: extends)
mechanism: QTR divides both operands into quarters and multiplexes each quarter into three replicated ceil(n/4)-bit adders. Each module performs four additions, a majority voter masks a faulty result, and a 1-bit register carries state between sections. A 2:1 multiplexer selects the external carry for the first quarter or the registered carry for later quarters. # p.253
choices:
  transform: split_duplicate_quarters [outside domain]   # p.253
  iterations: 4   # p.253
  correction: true   # p.253
new_choices:
  partition_count: 4 — number of operand sections processed over time   # p.253
  hardware_replication: 3 — number of quarter-width adder modules   # p.253
  voting: majority_voter — combines the three module outputs for fault masking   # p.253
slots:
  comparator: none
parameters: 8-, 16-, 32-, and 64-bit operands; three ceil(n/4)-bit RCAs; four iterations; one 1-bit carry register; 4:1 operand multiplexers; 2:1 carry multiplexer   # pp.253-254
results:
| metric | value | unit | technology / device | baseline | condition | page |
| hardware complexity, QTR | 115 (160%) | gates | technology/device UNKNOWN; 2003 | Non-Redundant 72 (100%) | 8 bit | p.254 |
| hardware complexity, QTR | 207 (144%) | gates | technology/device UNKNOWN; 2003 | Non-Redundant 144 (100%) | 16 bit | p.254 |
| hardware complexity, QTR | 391 (136%) | gates | technology/device UNKNOWN; 2003 | Non-Redundant 288 (100%) | 32 bit | p.254 |
| hardware complexity, QTR | 759 (132%) | gates | technology/device UNKNOWN; 2003 | Non-Redundant 576 (100%) | 64 bit | p.254 |
| hardware complexity, TSTMR | 155 (215%) | gates | technology/device UNKNOWN; 2003 | Non-Redundant 72 (100%) | 8 bit | p.254 |
| hardware complexity, TSTMR | 287 (199%) | gates | technology/device UNKNOWN; 2003 | Non-Redundant 144 (100%) | 16 bit | p.254 |
| hardware complexity, TSTMR | 507 (176%) | gates | technology/device UNKNOWN; 2003 | Non-Redundant 288 (100%) | 32 bit | p.254 |
| hardware complexity, TSTMR | 991 (172%) | gates | technology/device UNKNOWN; 2003 | Non-Redundant 576 (100%) | 64 bit | p.254 |
| delay, QTR | 60 (300%) | units | technology/device UNKNOWN; 2003 | Non-Redundant 20 (100%) | 8 bit | p.255 |
| delay, QTR | 76 (211%) | units | technology/device UNKNOWN; 2003 | Non-Redundant 36 (100%) | 16 bit | p.255 |
| delay, QTR | 108 (159%) | units | technology/device UNKNOWN; 2003 | Non-Redundant 68 (100%) | 32 bit | p.255 |
| delay, QTR | 172 (130%) | units | technology/device UNKNOWN; 2003 | Non-Redundant 132 (100%) | 64 bit | p.255 |
| delay, TSTMR | 51 (255%) | units | technology/device UNKNOWN; 2003 | Non-Redundant 20 (100%) | 8 bit | p.255 |
| delay, TSTMR | 69 (192%) | units | technology/device UNKNOWN; 2003 | Non-Redundant 36 (100%) | 16 bit | p.255 |
| delay, TSTMR | 99 (146%) | units | technology/device UNKNOWN; 2003 | Non-Redundant 68 (100%) | 32 bit | p.255 |
| delay, TSTMR | 165 (125%) | units | technology/device UNKNOWN; 2003 | Non-Redundant 132 (100%) | 64 bit | p.255 |
| complexity × delay squared, QTR | 1438% | percent of Non-Redundant | technology/device UNKNOWN; 2003 | Non-Redundant 100% | 8 bit | p.255 |
| complexity × delay squared, QTR | 641% | percent of Non-Redundant | technology/device UNKNOWN; 2003 | Non-Redundant 100% | 16 bit | p.255 |
| complexity × delay squared, QTR | 342% | percent of Non-Redundant | technology/device UNKNOWN; 2003 | Non-Redundant 100% | 32 bit | p.255 |
| complexity × delay squared, QTR | 224% | percent of Non-Redundant | technology/device UNKNOWN; 2003 | Non-Redundant 100% | 64 bit | p.255 |
| complexity × delay squared, TSTMR | 1400% | percent of Non-Redundant | technology/device UNKNOWN; 2003 | Non-Redundant 100% | 8 bit | p.255 |
| complexity × delay squared, TSTMR | 732% | percent of Non-Redundant | technology/device UNKNOWN; 2003 | Non-Redundant 100% | 16 bit | p.255 |
| complexity × delay squared, TSTMR | 373% | percent of Non-Redundant | technology/device UNKNOWN; 2003 | Non-Redundant 100% | 32 bit | p.255 |
| complexity × delay squared, TSTMR | 269% | percent of Non-Redundant | technology/device UNKNOWN; 2003 | Non-Redundant 100% | 64 bit | p.255 |
errors_and_checks: Majority voting provides concurrent error correction through fault masking; the paper does not quantify the fault model, coverage, alias rate, or false-alarm behavior.   # pp.253-256
conditions: QTR avoids the padding required by three-way partitioning for common adder widths divisible by four; double-precision floating point is identified as an exception. QTR is slower than TSTMR, but the delay difference falls to 5% at 64 bits. QTR has the lowest complexity-times-delay-squared result among the error-correcting designs at 32 and 64 bits.   # pp.253,255-256
evidence: §4; Fig. 3; Tables 1-3; Equations (1)-(4), pp.253-255

### duplication  (role: compares)
mechanism: TMR operates three full-width adders in parallel and applies a majority voter to their outputs. The implementation uses five-gate voters for each output bit. # pp.252,254
choices:
  replication: 3   # p.252
  temporal_stagger: false   # p.252
new_choices:
  voting: majority_voter — corrects one disagreeing module output   # p.252
slots:
  comparator: none
parameters: three n-bit RCAs; one voter per output bit; 8-, 16-, 32-, and 64-bit implementations   # pp.252,254
results:
| metric | value | unit | technology / device | baseline | condition | page |
| hardware complexity | 261 (363%) | gates | technology/device UNKNOWN; 2003 | Non-Redundant 72 (100%) | 8 bit | p.254 |
| hardware complexity | 517 (359%) | gates | technology/device UNKNOWN; 2003 | Non-Redundant 144 (100%) | 16 bit | p.254 |
| hardware complexity | 1029 (357%) | gates | technology/device UNKNOWN; 2003 | Non-Redundant 288 (100%) | 32 bit | p.254 |
| hardware complexity | 2053 (356%) | gates | technology/device UNKNOWN; 2003 | Non-Redundant 576 (100%) | 64 bit | p.254 |
| delay | 23 (115%) | units | technology/device UNKNOWN; 2003 | Non-Redundant 20 (100%) | 8 bit | p.255 |
| delay | 39 (108%) | units | technology/device UNKNOWN; 2003 | Non-Redundant 36 (100%) | 16 bit | p.255 |
| delay | 71 (104%) | units | technology/device UNKNOWN; 2003 | Non-Redundant 68 (100%) | 32 bit | p.255 |
| delay | 135 (102%) | units | technology/device UNKNOWN; 2003 | Non-Redundant 132 (100%) | 64 bit | p.255 |
| complexity × delay squared | 479% | percent of Non-Redundant | technology/device UNKNOWN; 2003 | Non-Redundant 100% | 8 bit | p.255 |
| complexity × delay squared | 421% | percent of Non-Redundant | technology/device UNKNOWN; 2003 | Non-Redundant 100% | 16 bit | p.255 |
| complexity × delay squared | 390% | percent of Non-Redundant | technology/device UNKNOWN; 2003 | Non-Redundant 100% | 32 bit | p.255 |
| complexity × delay squared | 373% | percent of Non-Redundant | technology/device UNKNOWN; 2003 | Non-Redundant 100% | 64 bit | p.255 |
errors_and_checks: TMR corrects errors by majority voting; quantitative coverage and the assumed number/type of faults are not stated.   # p.252
conditions: TMR adds only voter delay but has high hardware overhead. TMR has the lowest complexity-times-delay-squared value among the error-correcting designs at 8 and 16 bits.   # pp.252,255
evidence: §3; Fig. 1; Tables 1-3, pp.252,254-255

### ripple_carry  (role: instantiates)
mechanism: Every compared design uses a ripple-carry adder constructed from nine-gate full-adder cells. The gate-level model restricts cells to 2-input AND gates, 2-input OR gates, and inverters, with every gate assigned one delay unit. # pp.253-254
choices:
  full_adder_cell: nine_gate_full_adder [outside domain]   # p.254
new_choices:
  none
slots:
  none
parameters: n-bit complexity 9n gates; n-bit delay 2n + 4 units; widths 8, 16, 32, and 64 bits   # pp.254-255
results:
| metric | value | unit | technology / device | baseline | condition | page |
| hardware complexity | 72 (100%) | gates | technology/device UNKNOWN; 2003 | self | 8 bit | p.254 |
| hardware complexity | 144 (100%) | gates | technology/device UNKNOWN; 2003 | self | 16 bit | p.254 |
| hardware complexity | 288 (100%) | gates | technology/device UNKNOWN; 2003 | self | 32 bit | p.254 |
| hardware complexity | 576 (100%) | gates | technology/device UNKNOWN; 2003 | self | 64 bit | p.254 |
| delay | 20 (100%) | units | technology/device UNKNOWN; 2003 | self | 8 bit | p.255 |
| delay | 36 (100%) | units | technology/device UNKNOWN; 2003 | self | 16 bit | p.255 |
| delay | 68 (100%) | units | technology/device UNKNOWN; 2003 | self | 32 bit | p.255 |
| delay | 132 (100%) | units | technology/device UNKNOWN; 2003 | self | 64 bit | p.255 |
errors_and_checks: none
conditions: The RCA is the non-redundant baseline and the functional module used by all redundant implementations. Results assume uniform one-unit gate delay rather than a specified fabrication technology.   # pp.253-255
evidence: §5; Tables 1-2; Equations (1)-(4), pp.253-255

## new_families
none

## space_gaps
* time_redundancy lacks `split_duplicate_quarters`, which QTR uses instead of the declared half-width transform.   # p.253
* time_redundancy lacks choices for partition count and parallel module replication, which distinguish QTR from TSTMR.   # pp.252-253
* time_redundancy and duplication lack a majority-voter slot; `two_rail_tree` does not describe the voter used here.   # pp.252-254
* time_redundancy lacks a base-adder slot for the quarter-width ripple-carry modules.   # pp.253-254
* ripple_carry lacks the nine-gate full-adder cell used by every evaluated implementation.   # p.254

## open_questions
* The document does not state the fault multiplicity, fault duration, or circuit locations covered by QTR.
* The document does not report fabrication technology, physical area, power, or measured timing.
* The document does not quantify QTR detection coverage, correction coverage, or false-alarm behavior.
