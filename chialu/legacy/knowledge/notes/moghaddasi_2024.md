---
handle: moghaddasi_2024
citation: Moghaddasi, Jaberipur, Javaheri, Nam, "RNPE: An MSDF and Redundant Number System-Based DNN Accelerator Engine", IEEE Access, 2024
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_DOT_ACC]
formats: [int16, radix2_bsd16]
authority: incremental
pages_read: pp.96552–96564 / 13 pages
---

## summary
RNPE combines radix-2 redundant digits with most-significant-digit-first serial processing for DNN MACs. The engine emits one output digit per cycle, pipelines consecutive layers, and terminates computations through early ReLU/MaxPool decisions without reported accuracy loss. RTL synthesis uses TSMC 28 nm CMOS at 0.9 V.

## families
### generalized_signed_digit  (role: instantiates)
mechanism: RNPE represents each radix-2 digit with a Posibit and Negabit from the digit set {−1, 0, 1}. RDNS adders use carry-save addition with limited carry propagation, so their delay is independent of operand precision. Activations/outputs/intermediate data remain in RDNS, which avoids conversion to conventional representation. Weights remain binary 2’s complement. # pp.96553–96554, 96558
choices:
  radix: 2   # p.96553
  digit_encoding: Posibit/Negabit [outside domain]   # p.96553
  addition_scheme: limited_carry [outside domain]   # pp.96553–96554
new_choices:
  representation_scope: inputs_outputs_and_internal_data — selects whether RDNS is retained across unit boundaries   # pp.96554, 96558
slots:
  none
parameters: digit set {−1, 0, 1}; 16-BSD activations; 20-BSD accumulator residual   # pp.96553, 96556, 96559
results:
| metric | value | unit | technology / device | baseline | condition | page |
| operating latency | less than 49 | % | TSMC 28 nm CMOS, 2024 | bit-serial engine | STA cycle time | p.96561 |
| maximum performance | over 2 | x | TSMC 28 nm CMOS, 2024 | bit-serial engine | latency reduction alone | p.96561 |
errors_and_checks: Exact RDNS computation is reported with no DNN accuracy loss; no fault model or checking coverage is evaluated. # pp.96552, 96561
conditions: RDNS increases area by 25% and power by 26% against the bit-serial engine because Posibit/Negabit signal lines enlarge the arithmetic circuits. # p.96560
evidence: §II-B; Figures 1, 6, and 7; Table 4; §V-B.

### online_arithmetic_unit  (role: extends)
mechanism: Each cycle receives one MSDF BSD from every activation lane, forms digit-wise partial products, compresses them into Y[j], and updates R′[j] = 2R[j−1] + Y[j]. The accumulator emits O[j] while retaining a bounded residual. A Fitter maps the three leading residual digits to two digits, and a Limiter uses a sign detector to keep the residual in range despite redundant representations. # pp.96554, 96556–96559
choices:
  radix: 2   # p.96553
  residual_form: signed_digit   # pp.96556–96559
new_choices:
  residual_control: fitter_limiter_sign_detector — bounds the residual while selecting one real-time output digit per cycle   # pp.96557–96559
slots:
  none
parameters: 16-cycle loop; one BSD emitted per cycle; 16 output BSDs followed by a 20-BSD residual; 36 BSDs per iteration   # p.96559
results:
| metric | value | unit | technology / device | baseline | condition | page |
| response-time reduction | up to 97 | % | TSMC 28 nm CMOS, 2024 | traditional bit-parallel/bit-serial engines | image-classification DNN simulations | p.96552 |
| consequent-layer throughput improvement | up to 16 | x | TSMC 28 nm CMOS, 2024 | non-streamed layer execution | the next layer consumes digits before the producer terminates | pp.96560, 96562 |
errors_and_checks: Output is exact; the paper reports no accuracy loss and no arithmetic error bound beyond exact equivalence. # pp.96552, 96557
conditions: The next operation can start after receiving a limited number of leading digits, and computation can stop when the required precision or an activation-function condition is reached. # p.96554
evidence: §II-C; Algorithm 1; Example 1; Tables 2–3; Figures 7–8.

### bit_serial_dnn_datapath  (role: extends)
mechanism: RNPE is a serial/parallel DNN PE with 16 bit-parallel weight lanes and 16 BSD-serial activation lanes. R-PPG produces sixteen 16-BSD partial products, R-C compresses them to a 20-BSD partial sum, and R-AC accumulates while emitting an MSDF stream. R-ReLU terminates negative outputs, while R-MaxPool compares four PE streams and terminates losing computations. # pp.96556, 96558–96560
choices:
  digit_order: msdf   # pp.96554, 96556
  bits_per_cycle: 1   # pp.96556, 96559
  early_termination: true   # pp.96554, 96560
new_choices:
  operand_seriality: parallel_weights_serial_activations — identifies the mixed serial/parallel input organization   # pp.96555–96556
  pruning_function: ReLU_and_MaxPool — selects nonlinear functions that terminate MSDF computations   # pp.96559–96560
slots:
  none
parameters: 16 synapse lanes; 16-bit weights; 16-BSD activations; p = 16; l = 16; II = one activation digit per cycle   # pp.96556, 96558
results:
| metric | value | unit | technology / device | baseline | condition | page |
| area overhead | 25 | % | TSMC 28 nm CMOS, 2024 | bit-serial engine | synthesized RNPE | p.96560 |
| power overhead | 26 | % | TSMC 28 nm CMOS, 2024 | bit-serial engine | synthesized RNPE | p.96560 |
| computation reduction | 27 / 45 / 43 / 40 | % | TSMC 28 nm CMOS, 2024 | execution without pruning | LeNet5 / VGG16 / AlexNet / ResNet18 | p.96561 |
| performance improvement | 66 / 76 / 75 / 73 | % | TSMC 28 nm CMOS, 2024 | conventional engines | LeNet5 / VGG16 / AlexNet / ResNet18; pruning plus latency reduction | p.96561 |
| average PDP improvement | 14 | % | TSMC 28 nm CMOS, 2024 | conventional engines | image-classification DNN simulations | p.96552 |
| average EDP improvement | 53 | % | TSMC 28 nm CMOS, 2024 | conventional engines | image-classification DNN simulations | p.96552 |
| pruning improvement | 22.9 | % | TSMC 28 nm CMOS, 2024 | ComPreEND | average over VGG-16 and ResNet-18 | p.96562 |
errors_and_checks: Cycle-accurate LeNet5/VGG16/AlexNet/ResNet18 evaluation reports no accuracy loss; no approximate arithmetic or fault checker is used. # pp.96552, 96560–96562
conditions: RNPE supports dynamic precision adjustment, but the reported evaluation excludes that benefit because it is common to serial architectures. # p.96563 RNPE is not optimized for varying filter sizes or sparse inputs. # pp.96556, 96563
evidence: Algorithm 1; Figures 4–7 and 9–14; Tables 4–5; §§IV–VI.

### ling_prefix  (role: instantiates)
mechanism: The residual sign detector predicts carry without producing the addition result. The selected Ling-based circuit propagates Harry hi = ci ∨ ci−1 using generate/transfer signals, and the limiter uses the predicted sign to choose an equivalent bounded residual representation. # p.96558
choices:
new_choices:
  none
slots:
  none
parameters: sign input r4′r3′r2′r1′r0′   # p.96558
results:
| metric | value | unit | technology / device | baseline | condition | page |
errors_and_checks: none
conditions: The paper states that Harry propagation has lower overhead and delay than carry-lookahead addition, but it reports no numerical comparison. # p.96558
evidence: Equation (8); §III-C-d; Figure 8(c).

## new_families
none

## space_gaps
* `generalized_signed_digit.digit_encoding` lacks the Posibit/Negabit encoding used for radix-2 digits. # p.96553
* `bit_serial_dnn_datapath` lacks mixed bit-parallel-weight/BSD-serial-activation and serial-MSDF-output choices. # pp.96556, 96558–96560
* `online_arithmetic_unit` lacks a residual fitting/limiting mechanism for emitting one digit while retaining a fixed-width redundant residual. # pp.96557–96559
* `bit_serial_dnn_datapath` lacks slots for MSDF-aware ReLU and MaxPool pruning units. # pp.96559–96560

## open_questions
* The numerical cells of Tables 4–5 are absent from the supplied text extraction, so exact absolute area/power/frequency/latency values remain UNKNOWN.
* The narrative does not identify the precise PNPE/SNPE baseline associated with the reported 97% maximum response-time reduction.
