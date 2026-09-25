---
handle: albericio_2017
citation: Albericio, Delmas, Judd, Sharify, O'Leary, Genov, Moshovos, "Bit-Pragmatic Deep Neural Network Computing", IEEE/ACM International Symposium on Microarchitecture (MICRO-50), 2017
actual_citation: Jorge Albericio, Patrick Judd, Alberto Delmás, Sayeh Sharify, Andreas Moshovos, "Bit-Pragmatic Deep Neural Network Computing", arXiv:1610.06920v1, 2016
status: ok
kind: paper
unit_classes: [VEC_DOT_ACC]
formats: [fixed16, int8]
authority: landmark
pages_read: 13 / 13
---

## summary
Pragmatic processes only the non-zero bits of DNN neurons by converting each neuron into an explicit list of power-of-two offsets and combining one offset per cycle with bit-parallel synapses. A 16×16 array of Pragmatic Inner Product units preserves DaDianNao's worst-case term throughput while data-dependent execution, two-stage shifting, and per-column synchronization improve average performance and energy efficiency.

## families
### bit_serial_dnn_datapath  (role: extends)
mechanism: Neurons are converted on-the-fly from positional fixed-point or quantized storage into oneffsets identifying their non-zero powers of two. Each cycle, a PIP shifts each 16-bit synapse by one corresponding oneffset, reduces 16 shifted synapses through an adder tree, and accumulates the result. A 16×16 PIP tile processes 256 neuron oneffsets against 256 synapses across 16 windows, producing 4K terms per cycle. Neuron lanes finish according to their essential-bit counts and synchronize at pallet or column granularity. # p.5–p.8
choices:
  digit_order: msdf   # p.7–p.8
  bits_per_cycle: 1   # p.5
  precision_source: per_value   # p.5–p.7
  early_termination: true   # p.5–p.7
new_choices:
  essential_bit_representation: oneffset_list — each neuron is represented by `(pow, eon)` entries for its non-zero powers of two   # p.5
  lane_synchronization: pallet | per_column — lanes wait at a pallet boundary or independently by PIP column   # p.6, p.8
  first_stage_shift_control_bits: 0 | 1 | 2 | 3 | 4 — `L` limits the first-stage shift range before a shared second-stage shift   # p.7–p.10
  synapse_set_registers: 1 | 4 | 16 — SSRs buffer recently read synapse sets for independently advancing columns   # p.8, p.11
  software_precision_trimming: enabled | disabled — per-layer metadata controls prefix/suffix bits cleared before neuron storage   # p.9, p.11
slots: none
parameters: 16-bit fixed-point neurons/synapses; 8-bit quantized evaluation; 16×16 PIPs per tile; 256 oneffset generators; 4K terms/cycle; 16 tiles; oneffset `pow` width 4 bits plus `eon`; `L=0..4`; 1/4/16 SSR variants   # p.5–p.12
results:
| metric | value | unit | technology / device | baseline | condition | page |
| average essential-bit content | 12.7 | % | N/A / 2016 | 16-bit fixed-length representation | maximum across evaluated networks, all neurons | p.3 |
| average essential-bit content | 38.4 | % | N/A / 2016 | 8-bit quantized representation | maximum across evaluated networks, all neurons | p.3 |
| processed terms | 10 | % | N/A / 2016 | DaDianNao terms | ideal PRA-fp16 average | p.3 |
| processed terms | 8 | % | N/A / 2016 | DaDianNao terms | ideal PRA-red average with software precision | p.3 |
| average performance | 2.59 | × | TSMC 65nm / 2016 | DaDianNao | PRAsingle, convolutional layers | p.10 |
| average performance | 1.85 | × | TSMC 65nm / 2016 | DaDianNao | Stripes, convolutional layers | p.10 |
| performance difference | within 0.2 | % | TSMC 65nm / 2016 | PRAsingle | PRA2b and PRA3b | p.10 |
| chip area | 122 | mm² | TSMC 65nm / 2016 | 90 mm² DaDianNao | PRA2b, pallet synchronization | p.10 |
| chip power | 38.2 | W | TSMC 65nm / 2016 | 18.8 W DaDianNao | PRA2b, pallet synchronization | p.10 |
| average performance | 3.1 | × | TSMC 65nm / 2016 | DaDianNao | PRA2b with one SSR and column synchronization | p.11 |
| ideal average performance | 3.45 | × | TSMC 65nm / 2016 | DaDianNao | PRA2b with unlimited SSRs | p.11 |
| chip area | 122 | mm² | TSMC 65nm / 2016 | 90 mm² DaDianNao | PRA2b with one SSR | p.11 |
| chip power | 38.8 | W | TSMC 65nm / 2016 | 18.8 W DaDianNao | PRA2b with one SSR | p.11 |
| energy efficiency improvement | 28 | % | TSMC 65nm / 2016 | DaDianNao | PRA2b | p.11 |
| energy efficiency improvement | 48 | % | TSMC 65nm / 2016 | DaDianNao | PRA2b with one SSR | p.11 |
| performance benefit | 19 | % | TSMC 65nm / 2016 | same PRA without software guidance | average contribution from per-layer precision metadata | p.11 |
| average performance | nearly 3.5 | × | TSMC 65nm / 2016 | 8-bit quantized DaDianNao | PRA2b with one SSR | p.12 |
errors_and_checks: Products are exact for the stored neuron representation; the architecture is not presented as approximate arithmetic and provides no fault checker. Software-guided trimming uses profiled per-layer precision intended to maintain network accuracy, but no numerical accuracy-loss bound is reported. # p.1, p.9
conditions: Results cover convolutional layers, which account for more than 92% of DaDianNao execution time; other layers are unaffected. Performance depends on essential-bit counts, lane synchronization, NM fetch time, and whether oneffset differences fit the `2^L` first-stage shift range. Pallet processing starts after `max(NMC, PC)` cycles, so NM access can cause stalls when `NMC > PC`. Area and energy for 8-bit implementations are left for future work. # p.1, p.6–p.8, p.9, p.12
evidence: §II and Table I; §III and Fig. 4; §V-A–§V-F and Figs. 5–8; §VI-A–§VI-F, Tables III–V, and Figs. 9–12.

## new_families
none

## space_gaps
* `bit_serial_dnn_datapath.precision_source` cannot express Pragmatic's combination of per-value essential-bit execution with optional per-layer precision trimming. # p.5, p.9
* `bit_serial_dnn_datapath` lacks choices for sparse oneffset encoding, lane-synchronization granularity, two-stage shift width, and synapse-set buffering. # p.5–p.11
* `pairwise_tree.mul` cannot be filled by `bit_serial_dnn_datapath`, although Pragmatic's PIPs feed shifted essential-bit terms into per-filter adder trees. # p.5–p.7

## open_questions
* Table IV reports PRA2b with one SSR at `2.06×` DaDianNao power, while the adjacent prose states `2.19×`. # p.11
* The abstract's “additional 0.7% area” for improved synchronization does not identify whether the percentage is relative to DaDianNao or the pallet-synchronized Pragmatic configuration. # p.1
* The document reports no absolute clock frequency or latency in time units.
