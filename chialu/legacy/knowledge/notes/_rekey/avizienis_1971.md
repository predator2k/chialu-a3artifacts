---
handle: avizienis_1971
citation: A. Avizienis, "Arithmetic Error Codes: Cost and Effectiveness Studies for Application in Digital System Design", IEEE Transactions on Computers, vol. C-20, no. 11, pp. 1322-1331, 1971
actual_citation: A. Avizienis, G. C. Gilley, F. P. Mathur, D. A. Rennels, J. A. Rohr, and D. K. Rubin, "The STAR (Self-Testing And Repairing) Computer: An Investigation of the Theory and Practice of Fault-Tolerant Computer Design", IEEE Transactions on Computers, vol. C-20, no. 11, 1971
status: mismatch
kind: paper
unit_classes: [BINARY_ALU, other]
formats: [int28, residue_mod15]
authority: landmark
pages_read: 10 / 10
---

## summary
The document describes the STAR computer, which combines coded words, concurrent checking, duplication/triplication, rollback, and powered-off replacement units for fault tolerance (p.1312-1313). Its arithmetic datapath uses 28-bit operands with four-bit inverse modulo-15 check bytes and checks every bus transmission with an end-around-carry residue circuit (p.1315).

## families
### residue  (role: instantiates)
mechanism: Every 28-bit numeric operand b carries a four-bit check byte c(b), making the complete 32-bit word a multiple of 15. A bus checker casts out 15s concurrently with byte-serial word transmission. The checker uses a four-bit end-around-carry adder. Addresses use the same residue code, while instruction op-code/step-code/condition-code bytes use 2-out-of-4 encoding (p.1315).
choices:
  modulus: 15   # p.1315
  granularity: endpoint   # p.1315
  comparison_point: bus_transmission [outside domain]   # p.1315
  generator_style: modular_ripple   # p.1315
new_choices:
  zero_representation: 1111 — binary representation used for a zero modulo-15 residue   # p.1315
slots:
  comparator: none
parameters: 32-bit coded word; 28-bit binary operand; 4-bit check byte; 4-bit byte-serial bus   # p.1314-1315
results:
| metric | value | unit | technology / device | baseline | condition | page |
| check-field width | 4 | bits | UNKNOWN / 1971 | 28-bit data field | 32-bit numeric operand word | p.1315 |
errors_and_checks: A zero residue, represented by 1111, indicates a correct word; every other residue value indicates a fault. Undetected-error/alias rates are not reported (p.1315).
conditions: The modulo-15 code is selected for a byte-organized computer with four-bit bytes (p.1315). The separable residue code permits two's-complement arithmetic and facilitates multiple-precision/floating-point arithmetic (p.1315). Logic operations do not preserve the arithmetic code, so the logic processor removes the code before an operation and re-encodes the result (p.1316).
evidence: §II.D, Fig. 4, Fig. 5, pp.1315-1316

### inverse_residue  (role: instantiates)
mechanism: The check channel carries c(b) = 15 - |b|15, where |b|15 is the modulo-15 residue of the data field. Appending c(b) makes the complete operand word congruent to zero modulo 15, so one residue calculation checks the data/check pair (p.1315).
choices:
  modulus: 15   # p.1315
  inverse_on: check_channel   # p.1315
new_choices:
  none
slots:
  comparator: none
parameters: c(b) = 15 - |b|15; 28 data bits plus 4 check bits   # p.1315
results:
| metric | value | unit | technology / device | baseline | condition | page |
| coded-word width | 32 | bits | UNKNOWN / 1971 | 28-bit uncoded operand | inverse modulo-15 check byte appended | p.1315 |
errors_and_checks: The document specifies code validity by a zero whole-word residue but does not quantify fault coverage or alias rate (p.1315).
conditions: The inverse residue is applied to numeric operands and 16-bit instruction addresses; operation-code bytes retain 2-out-of-4 encoding in STAR (p.1315).
evidence: §II.D and Fig. 4, p.1315

### duplication  (role: instantiates)
mechanism: Two logic-processor copies drive an OR-connected bus and compare the bus word with each internally held output, producing a disagree message on mismatch. Three powered TARP copies operate with standby spares; a 2-out-of-(n+3) threshold vote identifies disagreement and triggers rollback or replacement (p.1316-1317).
choices:
  replication: 2 and 3 [outside domain]   # p.1316-1317
  comparison_point: per_cycle   # p.1314, p.1316
  temporal_stagger: false   # p.1316-1317
new_choices:
  standby_spares: 2 — powered-off replicas available to replace a failed TARP in the present design   # p.1317
  decision_rule: 2-out-of-(n+3) threshold vote — voting rule for three powered TARPs plus n spares   # p.1317
slots:
  comparator: none
parameters: 2 LOP copies; 3 powered TARP copies; n=2 standby TARPs; optional duplex processor/memory operation   # p.1316-1317
results:
| metric | value | unit | technology / device | baseline | condition | page |
| predicted 10-year reliability | 0.96 | probability | MM'69 technology / 1971 | MM'69 computer: 0.225 | S=3, K=∞ upper bound | p.1318 |
| predicted 10-year reliability | 0.79 | probability | MM'69 technology / 1971 | MM'69 computer: 0.225 | S=2, K=∞ upper bound | p.1318 |
| predicted 10-year reliability | 0.71 | probability | MM'69 technology / 1971 | MM'69 computer: 0.225 | S=3, K=1 lower bound | p.1318 |
| predicted 10-year reliability | 0.45 | probability | MM'69 technology / 1971 | MM'69 computer: 0.225 | S=2, K=1 lower bound | p.1318 |
errors_and_checks: The design targets transient/permanent/random/catastrophic faults. The paper does not report measured detection coverage or false-alarm rates (p.1313).
conditions: Reliability predictions concern permanent failures and assume CF=1/3, STF=8/7, and MM'69 components/packaging (p.1317-1318). Coding protects arithmetic processing, while duplication covers logic that does not preserve arithmetic codes (p.1315-1317).
evidence: §II.E-G, §III, Fig. 7, Table I, pp.1315-1318

## new_families
### standby_replacement_recovery  (domain: checker, closest: duplication, why_not: duplication models concurrent replicas and comparison, while STAR also uses dormant spares, rollback, fault localization, and power-switched replacement)
mechanism: Coded words and status monitors detect faults during execution. TARP stops the machine, resets powered units, and resumes from a stored rollback address. Repeated indications assigned to one unit cause that unit to be powered off and a spare to be powered on. Unpowered spares remain bus-connected through isolation circuits but produce only zero outputs (p.1313, p.1317).
choices: spare_count: Int[1..3:1]; spare_state: {powered, dormant_unpowered}; transient_recovery: {program_rollback}; permanent_recovery: {power_switched_replacement}; replacement_threshold: Int[1..UNKNOWN:1]
results:
| metric | value | unit | technology / device | baseline | condition | page |
| mission duration at reliability 0.9 | 12.5 | years | MM'69 technology / 1971 | MM'69 computer: 0.7 years | S=3, K=∞ upper bound | p.1318 |
| mission duration at reliability 0.9 | 4.5 | years | MM'69 technology / 1971 | MM'69 computer: 0.7 years | S=2, K=1 lower bound | p.1318 |
evidence: §I, §II.A, §II.G, §III, Table II, pp.1312-1318

## space_gaps
* residue.comparison_point lacks bus_transmission, although STAR checks every coded word during bus transmission (p.1315).
* inverse_residue lacks a generator/checker-style choice for the four-bit end-around-carry circuit (p.1315).
* duplication lacks standby-spare count and threshold-voting choices used by the TARP array (p.1317).
* time_redundancy.transform lacks untransformed program rollback/retry after transient faults (p.1313, p.1317).

## open_questions
* The paper does not quantify which fault patterns alias under the modulo-15 code.
* The paper does not identify the semiconductor process or technology node.
* The paper does not specify the number of repeated fault indications required before replacement; the threshold is configurable in the experimental TARP (p.1317).
