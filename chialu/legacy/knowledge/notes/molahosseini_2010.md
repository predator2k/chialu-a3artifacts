---
handle: molahosseini_2010
citation: Molahosseini, Navi, Dadkhah, Kavehei, Timarchi, "Efficient Reverse Converter Designs for the New 4-Moduli Sets Based on New CRTs", IEEE Transactions on Circuits and Systems I, 2010
actual_citation: Amir Sabbagh Molahosseini, Keivan Navi, Chitra Dadkhah, Omid Kavehei, and Somayeh Timarchi, "Efficient Reverse Converter Designs for the New 4-Moduli Sets {2^n−1, 2^n, 2^n+1, 2^(2n+1)−1} and {2^n−1, 2^n+1, 2^(2n), 2^(2n)+1} Based on New CRTs", IEEE Transactions on Circuits and Systems—I: Regular Papers, 2010
status: ok
kind: paper
unit_classes: [other]
formats: [rns]
authority: incremental
pages_read: 823–835 / 13
---

## summary
The paper proposes two four-moduli RNS sets and exact adder-based reverse converters for translating their residues into weighted binary numbers. New CRT-II serves the 5n+1-bit set, while New CRT-I serves the 6n-bit set; both architectures omit ROMs and multipliers and support pipelining. # pp.823–834

## families
### rns_reverse_converter  (role: proposes)
mechanism: The first converter applies New CRT-II to {2^n−1, 2^n, 2^n+1, 2^(2n+1)−1}; bit routing/complementation prepares operands, end-around-carry adders evaluate modular sums, and a binary subtracter and concatenation recover the weighted number. The second converter applies New CRT-I to {2^n−1, 2^n+1, 2^(2n), 2^(2n)+1}; algebraic simplification reduces six summands to five, so its main hardware is one five-operand modular adder. # pp.824–830
choices:
  algorithm: new_crt_ii for {2^n−1, 2^n, 2^n+1, 2^(2n+1)−1}; new_crt_i for {2^n−1, 2^n+1, 2^(2n), 2^(2n)+1}   # pp.824–830
  moduli_count: 4   # pp.823–830
  implementation: adder_based   # pp.824, 827–830
new_choices:
  moduli_set: {{2^n−1, 2^n, 2^n+1, 2^(2n+1)−1}, {2^n−1, 2^n+1, 2^(2n), 2^(2n)+1}} — identifies the channel moduli for which the conversion equations and hardware are derived   # pp.823–830
  dynamic_range_bits: {5n+1, 6n} — identifies the weighted dynamic range of the corresponding moduli set   # pp.823, 830
slots:
  none
parameters: Four residues; parameter n; 5n+1-bit and 6n-bit dynamic ranges; worked examples use n=2 and recover 1319 and 2684; layout examples use n=8. # pp.823, 827, 830, 832–833
results:
| metric | value | unit | technology / device | baseline | condition | page |
| post-layout area | lower | qualitative | TSMC 65 nm / 2010 | converter of [24] | New CRT-II converter; Cadence implementation at 0.9 V and 50 MHZ; numeric Table IV cells are absent from the supplied text extraction | pp.831–832 |
| post-layout delay | lower | qualitative | TSMC 65 nm / 2010 | converter of [24] | New CRT-II converter; Cadence implementation at 0.9 V and 50 MHZ; numeric Table IV cells are absent from the supplied text extraction | pp.831–832 |
| post-layout area | lower | qualitative | TSMC 65 nm / 2010 | converter of [25] | New CRT-I converter; Cadence implementation at 0.9 V and 50 MHZ; numeric Table IV cells are absent from the supplied text extraction | pp.831–833 |
| post-layout delay | lower | qualitative | TSMC 65 nm / 2010 | converter of [25] | New CRT-I converter; Cadence implementation at 0.9 V and 50 MHZ; numeric Table IV cells are absent from the supplied text extraction | pp.831–833 |
errors_and_checks: The conversion equations recover the exact weighted number within the moduli-set dynamic range; the paper reports no approximation error, fault model, detection coverage, false alarms, or alias rate. # pp.824–830
conditions: The first moduli set targets fast internal RNS arithmetic, while the second is conversion-friendly. # p.823 A CPA with end-around carry is assumed to have twice the delay and the same hardware complexity as a regular CPA. # pp.827–828 Area/delay comparisons use VHDL simulation with ISE v10.1 and Cadence implementation in TSMC 65 nm at 0.9 V and 50 MHZ with ten area-optimization iterations. # p.831 Fair converter comparison requires similar dynamic range and comparable internal RNS arithmetic speed. # pp.831–833 Both proposed converters are memoryless, adder-based, and efficiently pipelineable. # p.834
evidence: Section III, Theorems 1–4, Properties 1–2, Figs. 1–2, and Tables I–II establish the algorithms and architectures. Section IV, Tables III–VI, and Figs. 3–9 provide analytical and implementation comparisons. # pp.824–833

## new_families
none

## space_gaps
* `rns_reverse_converter` lacks a `modular_adder` or equivalent component slot for the end-around-carry CPAs and carry-save modular adders that dominate both proposed architectures. # pp.827–830
* `rns_reverse_converter` lacks choices for the exact moduli set and its dynamic range, although the paper treats both as central determinants of converter cost and internal arithmetic speed. # pp.823–824, 830–833

## open_questions
* The numeric area/delay values in Tables I–V are not present in the supplied text extraction, so the qualitative comparisons cannot be supplemented with printed values.
* Several restrictions on comparison designs' permitted values of n are missing from the supplied extraction and must not be reconstructed. # p.831
