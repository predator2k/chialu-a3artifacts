---
handle: avizienis_gilley_1971
citation: A. Avizienis, G. C. Gilley, F. P. Mathur, D. A. Rennels, J. A. Rohr, D. K. Rubin, "The STAR (Self-Testing And Repairing) Computer: An Investigation of the Theory and Practice of Fault-Tolerant Computer Design", IEEE Transactions on Computers, vol. C-20, no. 11, 1971
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU, other]
formats: [int28]
authority: landmark
pages_read: 1312-1321 / 10
---

## summary
The document describes the operating STAR computer, which combines coded words, concurrent checking, rollback, powered replication, and unpowered standby replacement. The arithmetic datapath uses modulo-15 inverse-residue check bytes so arithmetic processing does not require complete duplication. The document also reports modeled permanent-failure reliability for STAR configurations with two or three spares.

## families
### residue  (role: instantiates)
mechanism: Each 28-bit numeric operand is transmitted with a 4-bit check byte, and a bus checker casts out 15 concurrently with word transmission. A zero residue, represented by 1111, denotes a valid 32-bit coded word; every other computed residue causes a fault indication. Addresses use the same residue code. # p.1315
choices:
  modulus: 15   # p.1315
  comparison_point: data_bus [outside domain]   # pp.1315-1317
  generator_style: modular_ripple   # p.1315
new_choices:
  checked_word_classes: operands_addresses — The same residue algorithm checks numeric operands and instruction addresses.   # p.1315
slots:
  comparator: UNKNOWN   # p.1315
parameters: 28-bit binary number; 4-bit check byte; 32-bit coded word   # p.1315
results: none
errors_and_checks: A computed zero residue indicates a correct codeword, while every nonzero residue indicates a fault; undetected-error probability and fault coverage are not reported.   # p.1315
conditions: Modulo 15 is selected for a byte-organized computer with four-bit bytes; the separable code permits two's-complement arithmetic and facilitates multiple-precision/floating-point arithmetic.   # p.1315
evidence: §II-D, Fig. 4, Fig. 5, pp.1315-1316

### inverse_residue  (role: instantiates)
mechanism: The check channel carries c(b) = 15 - |b|15, which makes the complete 32-bit operand word a multiple of 15. The checker computes the residue of the entire coded word rather than comparing separately generated arithmetic results. # p.1315
choices:
  modulus: 15   # p.1315
  inverse_on: check_channel   # p.1315
new_choices:
  check_location: data_bus — Checking occurs concurrently while a word is transmitted.   # p.1315
slots:
  comparator: UNKNOWN   # p.1315
parameters: b is 28 bits; c(b) is 4 bits   # p.1315
results: none
errors_and_checks: The paper specifies valid/nonvalid residue behavior but does not quantify alias rate or coverage for particular faults.   # p.1315
conditions: The residue code replaces the initially used AN code because it is separable and better accommodates two's-complement, multiple-precision, and floating-point arithmetic.   # p.1315
evidence: §II-D, Fig. 4(b), p.1315

### end_around_carry  (role: instantiates)
mechanism: A four-bit end-around-carry adder performs casting out 15 for concurrent checking of coded words on the bus. The document does not specify its prefix topology or internal recirculation organization. # p.1315
choices:
  modulus: mod_2n_minus_1   # p.1315
new_choices:
  none
slots:
  none
parameters: n=4   # p.1315
results: none
errors_and_checks: none
conditions: The adder serves the modulo-15 checker rather than the main arithmetic result path.   # p.1315
evidence: §II-D, Fig. 5, p.1315

### duplication  (role: instantiates)
mechanism: Two LOP copies compare their outputs through disagree status messages, critical RWM storage can be duplicated or triplicated, and three powered TARP copies use a 2-out-of-(n+3) threshold vote with standby replacements. The TARP attempts state rollback before replacing a disagreeing member. # pp.1316-1317
choices:
  replication: 2 (LOP/RWM) and 3 (TARP)   # pp.1316-1317
  comparison_point: per_cycle   # pp.1316-1317
  temporal_stagger: false   # pp.1316-1317
new_choices:
  standby_spares: n, with n=2 in the present TARP design — Unpowered units replace failed active replicas.   # p.1317
slots:
  comparator: UNKNOWN   # pp.1316-1317
parameters: three powered TARPs; n=2 standby TARPs; 2-out-of-(n+3) vote   # p.1317
results: none
errors_and_checks: A disagreement triggers recovery; quantitative detection coverage and false-alarm behavior are not reported.   # p.1317
conditions: Complete processor/memory duplex operation is optional, while only the LOP and critical RWM are normally duplexed.   # p.1316
evidence: §II-E through §II-G, pp.1315-1317

## new_families
### standby_replacement_recovery  (domain: checker, closest: duplication, why_not: duplication does not represent dormant spares, rollback, fault classification, and power-switched replacement)
mechanism: Concurrent word/status checking stops normal computation when an error is detected. Recovery resets powered units and resumes at a stored rollback address. Repeated indications attributed to one unit cause that unit to be powered off and an unpowered spare to be activated. Transient effects are removed by repetition, while permanent faults are removed by unit replacement. # pp.1313, 1317
choices: spare_count: Int[1..3:1]; spare_power_state: {powered, unpowered}; recovery_sequence: {rollback, replacement, rollback_then_replacement}; replacement_switching: {power_switching, information_line_switching}
results:
| metric | value | unit | technology / device | baseline | condition | page |
| reliability | 0.9999998 | UNKNOWN | MM'69 technology assumptions; 1971 | MM'69 0.928; simplex 0.82 | 4368 h; S=3; K=∞ | p.1318 |
| reliability | 0.99997 | UNKNOWN | MM'69 technology assumptions; 1971 | MM'69 0.928; simplex 0.82 | 4368 h; S=2; K=∞ | p.1318 |
| reliability | 0.999995 | UNKNOWN | MM'69 technology assumptions; 1971 | MM'69 0.928; simplex 0.82 | 4368 h; S=3; K=1 | p.1318 |
| reliability | 0.99982 | UNKNOWN | MM'69 technology assumptions; 1971 | MM'69 0.928; simplex 0.82 | 4368 h; S=2; K=1 | p.1318 |
| reliability | 0.997 | UNKNOWN | MM'69 technology assumptions; 1971 | MM'69 0.475; simplex 0.14 | 43 680 h; S=3; K=∞ | p.1318 |
| reliability | 0.97 | UNKNOWN | MM'69 technology assumptions; 1971 | MM'69 0.475; simplex 0.14 | 43 680 h; S=2; K=∞ | p.1318 |
| reliability | 0.966 | UNKNOWN | MM'69 technology assumptions; 1971 | MM'69 0.475; simplex 0.14 | 43 680 h; S=3; K=1 | p.1318 |
| reliability | 0.87 | UNKNOWN | MM'69 technology assumptions; 1971 | MM'69 0.475; simplex 0.14 | 43 680 h; S=2; K=1 | p.1318 |
| reliability | 0.96 | UNKNOWN | MM'69 technology assumptions; 1971 | MM'69 0.225; simplex 0.019 | 87 360 h; S=3; K=∞ | p.1318 |
| reliability | 0.79 | UNKNOWN | MM'69 technology assumptions; 1971 | MM'69 0.225; simplex 0.019 | 87 360 h; S=2; K=∞ | p.1318 |
| reliability | 0.71 | UNKNOWN | MM'69 technology assumptions; 1971 | MM'69 0.225; simplex 0.019 | 87 360 h; S=3; K=1 | p.1318 |
| reliability | 0.45 | UNKNOWN | MM'69 technology assumptions; 1971 | MM'69 0.225; simplex 0.019 | 87 360 h; S=2; K=1 | p.1318 |
| mission duration | 12.5 | years | MM'69 technology assumptions; 1971 | MM'69 0.7 years; simplex 0.3 years | reliability 0.9; S=3; K=∞ | p.1318 |
| mission duration | 7.5 | years | MM'69 technology assumptions; 1971 | MM'69 0.7 years; simplex 0.3 years | reliability 0.9; S=2; K=∞ | p.1318 |
| mission duration | 6.7 | years | MM'69 technology assumptions; 1971 | MM'69 0.7 years; simplex 0.3 years | reliability 0.9; S=3; K=1 | p.1318 |
| mission duration | 4.5 | years | MM'69 technology assumptions; 1971 | MM'69 0.7 years; simplex 0.3 years | reliability 0.9; S=2; K=1 | p.1318 |
| mission duration | 16.0 | years | MM'69 technology assumptions; 1971 | MM'69 1.5 years; simplex 0.6 years | reliability 0.8; S=3; K=∞ | p.1318 |
| mission duration | 9.7 | years | MM'69 technology assumptions; 1971 | MM'69 1.5 years; simplex 0.6 years | reliability 0.8; S=2; K=∞ | p.1318 |
| mission duration | 8.5 | years | MM'69 technology assumptions; 1971 | MM'69 1.5 years; simplex 0.6 years | reliability 0.8; S=3; K=1 | p.1318 |
| mission duration | 6.0 | years | MM'69 technology assumptions; 1971 | MM'69 1.5 years; simplex 0.6 years | reliability 0.8; S=2; K=1 | p.1318 |
| mission duration | 18.5 | years | MM'69 technology assumptions; 1971 | MM'69 2.4 years; simplex 0.9 years | reliability 0.7; S=3; K=∞ | p.1318 |
| mission duration | 11.7 | years | MM'69 technology assumptions; 1971 | MM'69 2.4 years; simplex 0.9 years | reliability 0.7; S=2; K=∞ | p.1318 |
| mission duration | 10.0 | years | MM'69 technology assumptions; 1971 | MM'69 2.4 years; simplex 0.9 years | reliability 0.7; S=3; K=1 | p.1318 |
| mission duration | 7.0 | years | MM'69 technology assumptions; 1971 | MM'69 2.4 years; simplex 0.9 years | reliability 0.7; S=2; K=1 | p.1318 |
| mission duration | 20.5 | years | MM'69 technology assumptions; 1971 | MM'69 3.5 years; simplex 1.3 years | reliability 0.6; S=3; K=∞ | p.1318 |
| mission duration | 13.5 | years | MM'69 technology assumptions; 1971 | MM'69 3.5 years; simplex 1.3 years | reliability 0.6; S=2; K=∞ | p.1318 |
| mission duration | 11.3 | years | MM'69 technology assumptions; 1971 | MM'69 3.5 years; simplex 1.3 years | reliability 0.6; S=3; K=1 | p.1318 |
| mission duration | 8.3 | years | MM'69 technology assumptions; 1971 | MM'69 3.5 years; simplex 1.3 years | reliability 0.6; S=2; K=1 | p.1318 |
evidence: §II-A, §II-G, §III, Fig. 7, Tables I-II, pp.1313, 1317-1318

## space_gaps
* The residue vocabulary lacks a slot for an end-around-carry residue generator/checker, which is the actual modulo-15 checking circuit. # p.1315
* The checker vocabulary lacks concurrent control-error monitoring based on predicted unit activity/status messages encoded as 1-out-of-2. # pp.1315-1317
* The duplication vocabulary lacks dormant-spare count/power-state and replacement-policy choices. # pp.1313, 1317

## open_questions
* The paper does not quantify modulo-15 alias rate, checker fault coverage, or false-alarm behavior.
* The bus checker circuit does not establish a vocabulary-compatible comparator family.
* The reliability results are modeled rather than measured, and absolute component failure rates are not established.
