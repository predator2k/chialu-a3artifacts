---
handle: camus2016
citation: V. Camus, J. Schlachter, C. Enz, "A Low-Power Carry Cut-Back Approximate Adder with Fixed-Point Implementation and Floating-Point Precision", 53rd Design Automation Conference (DAC), 2016
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [uint32_fixed_point]
authority: incremental
pages_read: 6 / 6
---

## summary
The document proposes the Carry Cut-Back approximate adder, which monitors high-significance carry stages and cuts propagation at lower-significance positions to bound relative error while shortening effective critical paths. The 32-bit implementations trade configurable floating-point-like precision for energy/area/delay savings in an industrial 65 nm technology.

## families
### segmented_carry_speculative  (role: proposes)
mechanism: A conventional fixed-point carry chain is divided by cut-back modules containing PROP monitoring, an optional short SPEC carry speculator, and a multiplexer or monotonic straight-cut gate. PROP detects a carry sequence that could activate a long path, so a lower-significance stage substitutes a guessed carry. The apparent feedback uses operand-derived local propagate/generate signals and is not recursive. All modules use the same guess direction to prevent errors from accumulating in the same direction.   # pp.2-4
choices:
  prediction_window: SPEC widths {0, 1, 2, 3, 4}; 1 and 3 [outside domain]   # pp.5-6
  carry_in_scheme: carry_cut_back   # p.2
  correction: none   # pp.2-3
new_choices:
  propagate_monitor_width: configurable PROP bit-width — controls detection/error rate and contributes to maximum error   # p.4
  cutback_count: one or more modules — trades critical-path length against overhead/error rate   # pp.2,4
  cutback_position: configurable ADD1 width — sets the significance and maximum magnitude of a cut error   # p.4
  carry_guess_direction: fixed 0 or fixed 1 — all modules must use the same direction   # pp.3-4
  straight_cut_gate: OR-cut or SPEC-plus-multiplexer — selects direct substitution or short-chain speculation   # pp.2-3
slots:
  none
parameters: 32-bit adders; 0.8 GHz and 3.3 GHz; regular tuple `(number of cut-backs, ADD1, PROP, ADD3, SPEC)`; evaluated CCB tuples `(7,1,1,2,0)`, `(3,4,1,2,0)`, `(2,5,1,3,0)`, `(4,4,1,0,0)`, `(2,8,1,0,0)`, and `(1,10,1,-,0)`   # pp.5-6
results:
| metric | value | unit | technology / device | baseline | condition | page |
| REMAX | 35 | % | industrial 65 nm; 2016 | exact adder: 0 % | `(7,1,1,2,0)`, 32-bit, 3.3 GHz | p.6 |
| energy | 22 | fJ | industrial 65 nm; 2016 | exact adder: 47 fJ | `(7,1,1,2,0)`, REMAX 35 % | p.6 |
| area | 472 | µm2 | industrial 65 nm; 2016 | exact adder: 910 µm2 | `(7,1,1,2,0)`, REMAX 35 % | p.6 |
| PDAP | 102 | UNKNOWN | industrial 65 nm; 2016 | exact adder: 424 | `(7,1,1,2,0)`, REMAX 35 % | p.6 |
| REMAX | 6 | % | industrial 65 nm; 2016 | exact adder: 0 % | `(3,4,1,2,0)`, 32-bit, 3.3 GHz | p.6 |
| energy | 35 | fJ | industrial 65 nm; 2016 | exact adder: 47 fJ | `(3,4,1,2,0)`, REMAX 6 % | p.6 |
| area | 643 | µm2 | industrial 65 nm; 2016 | exact adder: 910 µm2 | `(3,4,1,2,0)`, REMAX 6 % | p.6 |
| PDAP | 223 | UNKNOWN | industrial 65 nm; 2016 | exact adder: 424 | `(3,4,1,2,0)`, REMAX 6 % | p.6 |
| REMAX | 3 | % | industrial 65 nm; 2016 | exact adder: 0 % | `(2,5,1,3,0)`, 32-bit, 3.3 GHz | p.6 |
| energy | 38 | fJ | industrial 65 nm; 2016 | exact adder: 47 fJ | `(2,5,1,3,0)`, REMAX 3 % | p.6 |
| area | 749 | µm2 | industrial 65 nm; 2016 | exact adder: 910 µm2 | `(2,5,1,3,0)`, REMAX 3 % | p.6 |
| PDAP | 287 | UNKNOWN | industrial 65 nm; 2016 | exact adder: 424 | `(2,5,1,3,0)`, REMAX 3 % | p.6 |
| REMAX | 6 | % | industrial 65 nm; 2016 | exact adder: 0 % | `(4,4,1,0,0)`, 32-bit, 0.8 GHz | p.6 |
| energy | 41 | fJ | industrial 65 nm; 2016 | exact adder: 79 fJ | `(4,4,1,0,0)`, REMAX 6 % | p.6 |
| area | 253 | µm2 | industrial 65 nm; 2016 | exact adder: 401 µm2 | `(4,4,1,0,0)`, REMAX 6 % | p.6 |
| PDAP | 103 | UNKNOWN | industrial 65 nm; 2016 | exact adder: 316 | `(4,4,1,0,0)`, REMAX 6 % | p.6 |
| REMAX | 0.4 | % | industrial 65 nm; 2016 | exact adder: 0 % | `(2,8,1,0,0)`, 32-bit, 0.8 GHz | p.6 |
| energy | 62 | fJ | industrial 65 nm; 2016 | exact adder: 79 fJ | `(2,8,1,0,0)`, REMAX 0.4 % | p.6 |
| area | 334 | µm2 | industrial 65 nm; 2016 | exact adder: 401 µm2 | `(2,8,1,0,0)`, REMAX 0.4 % | p.6 |
| PDAP | 216 | UNKNOWN | industrial 65 nm; 2016 | exact adder: 316 | `(2,8,1,0,0)`, REMAX 0.4 % | p.6 |
| REMAX | 0.1 | % | industrial 65 nm; 2016 | exact adder: 0 % | `(1,10,1,-,0)`, 32-bit, 0.8 GHz | p.6 |
| energy | 68 | fJ | industrial 65 nm; 2016 | exact adder: 79 fJ | `(1,10,1,-,0)`, REMAX 0.1 % | p.6 |
| area | 362 | µm2 | industrial 65 nm; 2016 | exact adder: 401 µm2 | `(1,10,1,-,0)`, REMAX 0.1 % | p.6 |
| PDAP | 246 | UNKNOWN | industrial 65 nm; 2016 | exact adder: 316 | `(1,10,1,-,0)`, REMAX 0.1 % | p.6 |
| energy saving | 14 | % | industrial 65 nm; 2016 | exact adder at 3.3 GHz | 32-bit, REMAX 2 % | p.5 |
| PDAP reduction | 27 | % | industrial 65 nm; 2016 | exact adder at 3.3 GHz | 32-bit, REMAX 2 % | p.5 |
| energy saving | 44 | % | industrial 65 nm; 2016 | exact adder at 0.8 GHz | 32-bit, REMAX 2 % | p.5 |
| PDAP reduction | 62 | % | industrial 65 nm; 2016 | exact adder at 0.8 GHz | 32-bit, REMAX 2 % | p.5 |
| PDAP improvement | up to 30 | % | industrial 65 nm; 2016 | ISA | compared implementations | p.6 |
| PDAP improvement | up to 45 | % | industrial 65 nm; 2016 | modified ETBA | compared implementations | p.6 |
errors_and_checks: `RE=(Sapprox-Sexact)/Sexact`; `REMAX` defines minimum precision, while `RERMS` estimates SNR-related error. A wrong carry guess has 50 % binary probability after PROP/SPEC propagation conditions hold. A consistently directed cut produces absolute error `2^m`; opposite-direction cuts can produce `2^(p+1)-2^m`, so mixed guess directions are prohibited. `REMAX` uses five million logarithmically uniform unsigned inputs, and `RERMS` uses five million uniformly distributed unsigned inputs; no fault checker is provided.   # pp.3-5
conditions: Manual STA constraints must exclude the full carry chain as a false path. High-speed implementations need more cut-back modules, which increases overhead; low-speed implementations obtain larger savings. Wider PROP/SPEC/ADD1 fields improve precision but eventually constrain delay. At very low precision under the 3.3 GHz constraint, ISA is more efficient; CCB gains relative efficiency as required accuracy increases. The claimed floating-point precision is a bounded relative-error property rather than an implemented floating-point adder.   # pp.4-6
evidence: Fig. 1 and §3.1 p.2; Figs. 2-5, equations (1)-(7), and §§3.2-3.4 pp.3-4; Figs. 6-7 and §4.1-4.2 p.5; Tables 1-2 and §4.3 p.6

## new_families
none

## space_gaps
* `segmented_carry_speculative` lacks independent choices for PROP width/cutback count/cut position/carry-guess direction, which determine the CCB timing/error trade-off.   # p.4
* `prediction_window` excludes the odd SPEC widths 1 and 3 that appear in evaluated CCB implementations.   # pp.5-6
* `segmented_carry_speculative` lacks a direct-cut-gate choice distinguishing OR-cut from SPEC-plus-multiplexer speculation.   # pp.2-3

## open_questions
* The underlying conventional ADD-block adder family is not identified.
* Tables 1 and 2 do not print a unit for PDAP.
* The industrial 65 nm process and standard-cell library are not identified.
