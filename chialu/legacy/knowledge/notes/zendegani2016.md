---
handle: zendegani2016
citation: R. Zendegani, M. Kamal, A. Fayyazi, A. Afzali-Kusha, S. Safari, M. Pedram, "SEERAD: A High Speed yet Energy-Efficient Rounding-Based Approximate Divider", Design, Automation and Test in Europe (DATE), pp. 1481-1484, 2016
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [int32, uint32]
authority: incremental
pages_read: 4 / 4
---

## summary
SEERAD approximates A/B by rounding B to Br = 2^(K+L)/D and computing D×A with shifts/addition followed by a K+L-bit right shift. Four design-time accuracy levels trade error for delay/power/area, and 32-bit implementations are compared with three combinational SRT dividers.

## families
### approximate_functional  (role: proposes)
mechanism: SEERAD finds Bf = 2^K from the divisor’s leading one, classifies B using following bits, selects constants D and L, and approximates A/B as D×A/(2^L×Bf). D×A is formed from shifted copies of |A| and an adder. A barrel shifter divides by 2^(K+L), and sign-detection/sign-setting blocks support 2’s-complement inputs. More divisor groups select more D values, which reduces error while increasing hardware and delay.
choices:
  method: divisor_round_pow2_lut   # p.1481-p.1483
  runtime_quality_scaling: false   # p.1481
new_choices:
  accuracy_level: Int[1..4:1] — selects the implemented accuracy/hardware point   # p.1482
  divisor_group_count: {1, 2, 4, 8} — partitions B using bits following its leading one   # p.1482
  rounding_tuple: per_group_(L,D) — fixes the rounded-divisor form 2^(K+L)/D   # p.1482
slots:
  none
parameters: n-bit 2’s-complement inputs; evaluated at 32 bits signed/unsigned; levels 1/2/3/4 use 1/2/4/8 groups, L=3/4/5/7, and 2/2/2/3 shift units; D sets are {5}, {12,9}, {28,24,20,17}, and {120,108,97,88,82,76,70,66}; Multiply/Adder outputs are 2n bits and the final output is 2n+L bits   # p.1482-p.1483
results:
| metric | value | unit | technology / device | baseline | condition | page |
| maximum error | 37.5% | % | UNKNOWN / 2016 | exact division | level 1 | p.1483 |
| maximum error | 25.0% | % | UNKNOWN / 2016 | exact division | level 2 | p.1483 |
| maximum error | 12.5% | % | UNKNOWN / 2016 | exact division | level 3 | p.1483 |
| maximum error | 6.25% | % | UNKNOWN / 2016 | exact division | level 4 | p.1483 |
| MRE | 16.55% | % | UNKNOWN / 2016 | exact division | level 1, 8 bits | p.1483 |
| MRE | 16.25% | % | UNKNOWN / 2016 | exact division | level 1, 16 bits | p.1483 |
| MRE | 16.25% | % | UNKNOWN / 2016 | exact division | level 1, 32 bits | p.1483 |
| MRE | 9.15% | % | UNKNOWN / 2016 | exact division | level 2, 8 bits | p.1483 |
| MRE | 8.77% | % | UNKNOWN / 2016 | exact division | level 2, 16 bits | p.1483 |
| MRE | 8.77% | % | UNKNOWN / 2016 | exact division | level 2, 32 bits | p.1483 |
| MRE | 4.66% | % | UNKNOWN / 2016 | exact division | level 3, 8 bits | p.1483 |
| MRE | 4.55% | % | UNKNOWN / 2016 | exact division | level 3, 16 bits | p.1483 |
| MRE | 4.55% | % | UNKNOWN / 2016 | exact division | level 3, 32 bits | p.1483 |
| MRE | 2.42% | % | UNKNOWN / 2016 | exact division | level 4, 8 bits | p.1483 |
| MRE | 2.20% | % | UNKNOWN / 2016 | exact division | level 4, 16 bits | p.1483 |
| MRE | 2.20% | % | UNKNOWN / 2016 | exact division | level 4, 32 bits | p.1483 |
| delay | 0.61 | ns | 45 nm / 2016 | none | unsigned level 1 | p.1484 |
| power | 0.64 | mw | 45 nm / 2016 | none | unsigned level 1 | p.1484 |
| area | 1343 | μm2 | 45 nm / 2016 | none | unsigned level 1 | p.1484 |
| energy | 0.39 | pJ | 45 nm / 2016 | none | unsigned level 1 | p.1484 |
| EDP | 0.24 | ns × pJ | 45 nm / 2016 | none | unsigned level 1 | p.1484 |
| PDA | 524 | mW×ns×μm2 | 45 nm / 2016 | none | unsigned level 1 | p.1484 |
| delay | 0.7 | ns | 45 nm / 2016 | none | unsigned level 2 | p.1484 |
| power | 1.18 | mw | 45 nm / 2016 | none | unsigned level 2 | p.1484 |
| area | 2445 | μm2 | 45 nm / 2016 | none | unsigned level 2 | p.1484 |
| energy | 0.83 | pJ | 45 nm / 2016 | none | unsigned level 2 | p.1484 |
| EDP | 0.58 | ns × pJ | 45 nm / 2016 | none | unsigned level 2 | p.1484 |
| PDA | 2020 | mW×ns×μm2 | 45 nm / 2016 | none | unsigned level 2 | p.1484 |
| delay | 0.8 | ns | 45 nm / 2016 | none | unsigned level 3 | p.1484 |
| power | 2.117 | mw | 45 nm / 2016 | none | unsigned level 3 | p.1484 |
| area | 4378 | μm2 | 45 nm / 2016 | none | unsigned level 3 | p.1484 |
| energy | 1.69 | pJ | 45 nm / 2016 | none | unsigned level 3 | p.1484 |
| EDP | 1.35 | ns × pJ | 45 nm / 2016 | none | unsigned level 3 | p.1484 |
| PDA | 7415 | mW×ns×μm2 | 45 nm / 2016 | none | unsigned level 3 | p.1484 |
| delay | 1.07 | ns | 45 nm / 2016 | none | unsigned level 4 | p.1484 |
| power | 7.53 | mw | 45 nm / 2016 | none | unsigned level 4 | p.1484 |
| area | 12451 | μm2 | 45 nm / 2016 | none | unsigned level 4 | p.1484 |
| energy | 8.06 | pJ | 45 nm / 2016 | none | unsigned level 4 | p.1484 |
| EDP | 8.62 | ns × pJ | 45 nm / 2016 | none | unsigned level 4 | p.1484 |
| PDA | 100319 | mW×ns×μm2 | 45 nm / 2016 | none | unsigned level 4 | p.1484 |
| delay | 0.76 | ns | 45 nm / 2016 | none | signed level 1 | p.1484 |
| power | 0.99 | mw | 45 nm / 2016 | none | signed level 1 | p.1484 |
| area | 1537 | μm2 | 45 nm / 2016 | none | signed level 1 | p.1484 |
| energy | 0.75 | pJ | 45 nm / 2016 | none | signed level 1 | p.1484 |
| EDP | 0.57 | ns × pJ | 45 nm / 2016 | none | signed level 1 | p.1484 |
| PDA | 1156 | mW×ns×μm2 | 45 nm / 2016 | none | signed level 1 | p.1484 |
| delay | 0.87 | ns | 45 nm / 2016 | none | signed level 2 | p.1484 |
| power | 1.69 | mw | 45 nm / 2016 | none | signed level 2 | p.1484 |
| area | 2684 | μm2 | 45 nm / 2016 | none | signed level 2 | p.1484 |
| energy | 1.47 | pJ | 45 nm / 2016 | none | signed level 2 | p.1484 |
| EDP | 1.28 | ns × pJ | 45 nm / 2016 | none | signed level 2 | p.1484 |
| PDA | 3946 | mW×ns×μm2 | 45 nm / 2016 | none | signed level 2 | p.1484 |
| delay | 0.92 | ns | 45 nm / 2016 | none | signed level 3 | p.1484 |
| power | 3.27 | mw | 45 nm / 2016 | none | signed level 3 | p.1484 |
| area | 4868 | μm2 | 45 nm / 2016 | none | signed level 3 | p.1484 |
| energy | 3.01 | pJ | 45 nm / 2016 | none | signed level 3 | p.1484 |
| EDP | 2.77 | ns × pJ | 45 nm / 2016 | none | signed level 3 | p.1484 |
| PDA | 14645 | mW×ns×μm2 | 45 nm / 2016 | none | signed level 3 | p.1484 |
| delay | 1.27 | ns | 45 nm / 2016 | none | signed level 4 | p.1484 |
| power | 9.72 | mw | 45 nm / 2016 | none | signed level 4 | p.1484 |
| area | 12840 | μm2 | 45 nm / 2016 | none | signed level 4 | p.1484 |
| energy | 12.34 | pJ | 45 nm / 2016 | none | signed level 4 | p.1484 |
| EDP | 15.68 | ns × pJ | 45 nm / 2016 | none | signed level 4 | p.1484 |
| PDA | 158502 | mW×ns×μm2 | 45 nm / 2016 | none | signed level 4 | p.1484 |
| delay | 19.61 | ns | 45 nm / 2016 | none | SRT Radix-2 | p.1484 |
| power | 60.88 | mw | 45 nm / 2016 | none | SRT Radix-2 | p.1484 |
| area | 28691 | μm2 | 45 nm / 2016 | none | SRT Radix-2 | p.1484 |
| energy | 1193.86 | pJ | 45 nm / 2016 | none | SRT Radix-2 | p.1484 |
| EDP | 23411.53 | ns × pJ | 45 nm / 2016 | none | SRT Radix-2 | p.1484 |
| PDA | 34252945 | mW×ns×μm2 | 45 nm / 2016 | none | SRT Radix-2 | p.1484 |
| delay | 11.3 | ns | 45 nm / 2016 | none | SRT Radix-2 CS | p.1484 |
| power | 31.07 | mw | 45 nm / 2016 | none | SRT Radix-2 CS | p.1484 |
| area | 15863 | μm2 | 45 nm / 2016 | none | SRT Radix-2 CS | p.1484 |
| energy | 351.09 | pJ | 45 nm / 2016 | none | SRT Radix-2 CS | p.1484 |
| EDP | 3967.33 | ns × pJ | 45 nm / 2016 | none | SRT Radix-2 CS | p.1484 |
| PDA | 5569357 | mW×ns×μm2 | 45 nm / 2016 | none | SRT Radix-2 CS | p.1484 |
| delay | 17.63 | ns | 45 nm / 2016 | none | SRT Radix-4 | p.1484 |
| power | 54.47 | mw | 45 nm / 2016 | none | SRT Radix-4 | p.1484 |
| area | 25051 | μm2 | 45 nm / 2016 | none | SRT Radix-4 | p.1484 |
| energy | 960.31 | pJ | 45 nm / 2016 | none | SRT Radix-4 | p.1484 |
| EDP | 16930.20 | ns × pJ | 45 nm / 2016 | none | SRT Radix-4 | p.1484 |
| PDA | 24056628 | mW×ns×μm2 | 45 nm / 2016 | none | SRT Radix-4 | p.1484 |
| delay reduction | 14 | times smaller | 45 nm / 2016 | SRT Radix-2 CS | SEERAD average | p.1484 |
| energy reduction | 300 | times smaller | 45 nm / 2016 | SRT Radix-2 CS | SEERAD average | p.1484 |
| delay reduction | 50% | % | 45 nm / 2016 | exact Wallace-tree multiplier | unsigned SEERAD average | p.1483 |
| power reduction | 81% | % | 45 nm / 2016 | exact Wallace-tree multiplier | unsigned SEERAD average | p.1483 |
| area reduction | 0.58% | % | 45 nm / 2016 | exact Wallace-tree multiplier | unsigned SEERAD average | p.1483 |
| PSNR maximum | 76 | DB | UNKNOWN / 2016 | exact division | Football, level 1 | p.1484 |
| PSNR minimum | 66 | DB | UNKNOWN / 2016 | exact division | Football, level 1 | p.1484 |
| PSNR average | 75 | DB | UNKNOWN / 2016 | exact division | Football, level 1 | p.1484 |
| PSNR maximum | 81 | DB | UNKNOWN / 2016 | exact division | Football, level 2 | p.1484 |
| PSNR minimum | 69 | DB | UNKNOWN / 2016 | exact division | Football, level 2 | p.1484 |
| PSNR average | 79 | DB | UNKNOWN / 2016 | exact division | Football, level 2 | p.1484 |
| PSNR maximum | 86 | DB | UNKNOWN / 2016 | exact division | Football, level 3 | p.1484 |
| PSNR minimum | 75 | DB | UNKNOWN / 2016 | exact division | Football, level 3 | p.1484 |
| PSNR average | 85 | DB | UNKNOWN / 2016 | exact division | Football, level 3 | p.1484 |
| PSNR maximum | 92 | DB | UNKNOWN / 2016 | exact division | Football, level 4 | p.1484 |
| PSNR minimum | 81 | DB | UNKNOWN / 2016 | exact division | Football, level 4 | p.1484 |
| PSNR average | 91 | DB | UNKNOWN / 2016 | exact division | Football, level 4 | p.1484 |
| PSNR maximum | 73 | DB | UNKNOWN / 2016 | exact division | Miss America, level 1 | p.1484 |
| PSNR minimum | 73 | DB | UNKNOWN / 2016 | exact division | Miss America, level 1 | p.1484 |
| PSNR average | 72 | DB | UNKNOWN / 2016 | exact division | Miss America, level 1 | p.1484 |
| PSNR maximum | 76 | DB | UNKNOWN / 2016 | exact division | Miss America, level 2 | p.1484 |
| PSNR minimum | 76 | DB | UNKNOWN / 2016 | exact division | Miss America, level 2 | p.1484 |
| PSNR average | 76 | DB | UNKNOWN / 2016 | exact division | Miss America, level 2 | p.1484 |
| PSNR maximum | 82 | DB | UNKNOWN / 2016 | exact division | Miss America, level 3 | p.1484 |
| PSNR minimum | 82 | DB | UNKNOWN / 2016 | exact division | Miss America, level 3 | p.1484 |
| PSNR average | 82 | DB | UNKNOWN / 2016 | exact division | Miss America, level 3 | p.1484 |
| PSNR maximum | 88 | DB | UNKNOWN / 2016 | exact division | Miss America, level 4 | p.1484 |
| PSNR minimum | 88 | DB | UNKNOWN / 2016 | exact division | Miss America, level 4 | p.1484 |
| PSNR average | 88 | DB | UNKNOWN / 2016 | exact division | Miss America, level 4 | p.1484 |
| PSNR maximum | 66 | DB | UNKNOWN / 2016 | exact division | Bus, level 1 | p.1484 |
| PSNR minimum | 56 | DB | UNKNOWN / 2016 | exact division | Bus, level 1 | p.1484 |
| PSNR average | 62 | DB | UNKNOWN / 2016 | exact division | Bus, level 1 | p.1484 |
| PSNR maximum | 70 | DB | UNKNOWN / 2016 | exact division | Bus, level 2 | p.1484 |
| PSNR minimum | 59 | DB | UNKNOWN / 2016 | exact division | Bus, level 2 | p.1484 |
| PSNR average | 66 | DB | UNKNOWN / 2016 | exact division | Bus, level 2 | p.1484 |
| PSNR maximum | 77 | DB | UNKNOWN / 2016 | exact division | Bus, level 3 | p.1484 |
| PSNR minimum | 65 | DB | UNKNOWN / 2016 | exact division | Bus, level 3 | p.1484 |
| PSNR average | 72 | DB | UNKNOWN / 2016 | exact division | Bus, level 3 | p.1484 |
| PSNR maximum | 82 | DB | UNKNOWN / 2016 | exact division | Bus, level 4 | p.1484 |
| PSNR minimum | 71 | DB | UNKNOWN / 2016 | exact division | Bus, level 4 | p.1484 |
| PSNR average | 78 | DB | UNKNOWN / 2016 | exact division | Bus, level 4 | p.1484 |
errors_and_checks: Relative error is 1-(A/B approximate)/(A/B exact), and its maximum is 1-Dmax/2^L. Table II reports maximum error from 37.5% to 6.25% and MRE from 16.55% to 2.20%; no checker or recovery mechanism is reported.   # p.1483
conditions: SEERAD targets error-resilient DSP applications. Tuples found for 8-bit inputs are reused above 8 bits for simpler hardware with slightly larger inaccuracy. Higher accuracy requires more groups/hardware/delay. Unsigned implementations omit Sign Detector and Sign Set. All hardware comparisons use combinational 32-bit circuits synthesized with Synopsys Design Compiler and the Nangate 45nm library.   # p.1481-p.1484
evidence: §II.A-C, Table I, Figures 1-3, Table II, §III.A-B, Figures 4, Tables III-IV, pp.1482-1484

## new_families
### constant_shift_add_multiplier  (domain: mul: integer multipliers, closest: sequential_shift_add, why_not: D×A is a combinational constant multiplication from parallel shifted copies rather than a reused iterative adder)
mechanism: The selected per-group constant D is expressed with coefficients ai in {-1,0,1}. Two shift units form D×|A| at accuracy levels 1-3, while three shift units serve level 4. An unspecified adder sums the shifted outputs into a 2n-bit result.
choices: shift_terms: Int[2..3:1]; constant_selection: {per_divisor_group}
results: none
evidence: §II.A-B, Table I, Figure 2, pp.1482-1483

## space_gaps
* approximate_functional lacks component slots for the rounding/index logic, constant shift-add multiplier, and quotient barrel shifter used by SEERAD.   # p.1482-p.1483
* approximate_functional lacks a design-time accuracy-level/group-count choice; runtime_quality_scaling does not represent the four synthesized structures.   # p.1481-p.1482

## open_questions
* The adder architecture and barrel-shifter radix/stage organization are unspecified.
* Table IV prints Miss America level-1 maximum/minimum/average PSNR as 73/73/72 DB, so the average is below the printed minimum.
