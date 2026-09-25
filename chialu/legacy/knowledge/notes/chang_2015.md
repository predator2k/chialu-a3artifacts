---
handle: chang_2015
citation: Chang, Molahosseini, Zarandi, Tay, "Residue Number Systems: A New Paradigm to Datapath Optimization for Low-Power and High-Performance Digital Signal Processing Applications", IEEE Circuits and Systems Magazine, 2015
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU, VEC_DOT_ACC, other]
formats: [integer, residue]
authority: survey
pages_read: 26-44 / 19 pages
---

## summary
The paper surveys RNS datapaths whose pairwise-coprime modulus channels perform independent modular arithmetic without inter-channel carry propagation. The paper analyzes conversion/inter-modular overheads, DSP/cryptographic applications, RRNS fault tolerance, and implementation results across ASIC/FPGA/GPU platforms.

## families
### rns_channel_arithmetic  (role: analyzes)
mechanism: An integer is represented by residues over N pairwise relatively prime moduli, with dynamic range M equal to their product. Addition/subtraction/multiplication execute independently in smaller modulus channels, and carry outputs do not propagate between channels. Arbitrary moduli provide flexible/balanced channel widths, while 2^n and 2^n±1 moduli provide arithmetic identities that simplify operators/converters. # p.29
choices:
  modulus_form: generic / pow2_minus_1 / pow2 / pow2_plus_1   # p.29
new_choices:
  moduli_set_balance: balanced / relaxed — Whether channel word lengths are comparable or relaxed to enlarge the special-moduli search space.   # p.32
slots:
  modular_adder: end_around_carry   # pp.39-40
parameters: N pairwise relatively prime moduli; M = product of all moduli; channel widths determined by the selected moduli.   # p.29
results:
| metric | value | unit | technology / device | baseline | condition | page |
| normalized delay-variation saving | up to 58% | % | UNKNOWN / 2013 | equivalent TCS implementation | three-moduli {2^8, 2^10-1, 2^12+1}, four-tap FIR | p.39 |
| timing yield | up to 100% | % | UNKNOWN / 2013 | equivalent TCS implementation | three-moduli {2^8, 2^10-1, 2^12+1}, four-tap FIR | p.39 |
errors_and_checks: Errors remain localized to their modulus channels; a faulty channel can be removed if the surviving information moduli retain sufficient dynamic range.   # p.36
conditions: RNS favors workloads dominated by addition/subtraction/multiplication. Sign detection/magnitude comparison/overflow detection/division/scaling require inter-modular computation and cannot use the same independent-channel parallelism.   # p.29
evidence: §II.B, Fig. 1, Fig. 2, §IV, pp.29-31, 39-40

### rns_reverse_converter  (role: analyzes)
mechanism: The reverse converter reconstructs a weighted integer from all residue channels. Implementations use CRT, Mixed Radix Conversion, or hybrids; arbitrary moduli generally require lookup tables, while special moduli permit simplification into bit selection/reshuffling/modular carry-save addition/vector-merged modular addition. # pp.29, 32
choices:
  algorithm: crt / mixed_radix   # pp.31-32
  implementation: rom / adder_based   # p.32
new_choices:
  algorithm: hybrid_crt_mixed_radix — Combines CRT and Mixed Radix Conversion in one reverse converter.   # p.32
slots: none
parameters: Inputs are N residues; output dynamic range is M; converter size depends on moduli count/values.   # pp.29, 32
results: none
errors_and_checks: none
conditions: The reverse converter is the most complex main RNS component. ROM-based converters for arbitrary moduli are difficult to pipeline and consume area/time, while special-moduli identities simplify conversion.   # pp.29, 32
evidence: Fig. 1, Eq. (1), §II.B-C, pp.29-32

### rns_scaling_comparison  (role: analyzes)
mechanism: Sign detection determines whether a reconstructed value lies in the lower or upper half of M. Magnitude comparison can perform modular subtraction followed by sign detection. Scaling/overflow handling and comparison require information from multiple residues rather than independent channel operations. # pp.29, 31
choices:
  operation: scale / sign_detect / compare   # pp.29, 31
new_choices: none
slots: none
parameters: Scaling is especially efficient when its factor is one modulus of a special moduli set.   # p.31
results: none
errors_and_checks: Overflow produces an incorrect residue representation when a result exceeds the dynamic range.   # pp.30-31
conditions: Scaling can avoid overflow with some loss of output precision; sign/comparison/scaling remain non-trivial inter-modular operations.   # pp.29, 31
evidence: §II.B, Fig. 2, pp.29-31

### rns_dsp_datapath  (role: compares)
mechanism: FIR/IIR/transform datapaths convert inputs to residues, execute convolutions independently in parallel modulus channels, and reverse-convert the final residues. Short local channels support voltage/frequency scaling, path relaxation, reduced glitching, and technology mapping by channel. # pp.31-33, 39
choices:
  kernel: fir / iir / fft   # pp.32-33
new_choices: none
slots: none
parameters: Reported examples include 16-/120-/256-tap FIR filters, 4-/8-tap DWT filters, and 19-29-bit outputs.   # pp.32-33, 40
results:
| metric | value | unit | technology / device | baseline | condition | page |
| area-delay-product gain | 1.35-1.71 | ratio | 0.7 μm CMOS / 2004 | TCS transpose FIR stage | 16-tap filter, M from 20 to 40 bits | p.32 |
| energy per cycle | 844 | pJ per cycle | ASIC / 2012 | TCS: 1196 pJ per cycle | 120-tap fully parallel FIR at 20 MHz | p.32 |
| energy per cycle | 225 | pJ per cycle | ASIC / 2012 | TCS: 364 pJ per cycle | clock-gated serial/parallel FIR | p.32 |
| speed improvement | 59% / 46% / 76% / 131% | % | Chip Express 0.35 μm CX3003 CMOS / 2003 | corresponding TCS DWT | 21-/23-/27-/29-bit outputs | p.33 |
| area | 112332 | nm² | 32 nm CMOS / 2013 | UNKNOWN | Gaussian smoothing/Sobel detector | p.33 |
| power | 30.23 | mW | 32 nm CMOS / 2013 | UNKNOWN | 1.05V, 250 MHz | p.33 |
| resource-utilization saving | 40% | % | Xilinx FPGA / 2012 | TCS implementation | 256-tap FIR, moduli {64,31,29,23,19,17,13} | p.40 |
| power saving | more than 50% | % | embedded RISC processor / 2009 | regular TCS | various DSP kernels | p.40 |
errors_and_checks: DSP arithmetic remains exact within M unless overflow/scaling or deliberately overscaled voltage introduces errors.   # pp.30-31, 33
conditions: Conversion overhead must be hidden/amortized across substantial residue-domain computation. Changing dynamic range at runtime costs at least about a reverse conversion, which disadvantages workloads with disparate or abrupt precision requirements.   # pp.28, 41
evidence: Fig. 3, §III.A, §IV-V, pp.31-33, 39-41

### rns_montgomery_crypto  (role: analyzes)
mechanism: RNS partitions large modular multiplications into smaller parallel residue-channel operations. RSA can remain entirely in the residue domain when communicating parties share RNS parameters, while ECC uses RNS Montgomery multiplication to accelerate point multiplication. # pp.37-38
choices:
  base_extension: mixed_radix   # pp.37, 44
new_choices: none
slots: none
parameters: Large-key RSA/ECC modular multiplication/exponentiation; exact channel count/width is UNKNOWN.   # p.37
results:
| metric | value | unit | technology / device | baseline | condition | page |
| area | less than half | baseline area | UNKNOWN / 2009 | previous ECC design efforts | RNS Montgomery point multiplier | p.37 |
| throughput improvement | up to 122% | % | GPU / 2012 | non-RNS partitioning | elliptic-curve point multiplication | p.40 |
errors_and_checks: Base randomization can protect RNS-based RSA against side-channel attacks without overhead relative to the unprotected regular implementation.   # p.38
conditions: RNS is advantageous for large modular multiplications; full-RNS RSA avoids forward/reverse conversions only when both parties agree on RNS parameters.   # p.37
evidence: §III.E, §IV, pp.37-40

### rns_redundant  (role: analyzes)
mechanism: RRNS adds redundant moduli beyond the information-moduli dynamic range. Reverse conversion into the illegitimate range signals residue errors; independent channels localize errors, and erroneous channels can be excluded when the remaining information range suffices. # pp.29-31
choices:
  correction: true   # p.30
new_choices:
  decoding: legitimate_range / iterative_channel_exclusion / maximum_likelihood — Methods used to detect, locate, or disambiguate residue errors.   # pp.30, 36-37
slots: none
parameters: With r redundant moduli, RRNS detects up to r residue-digit errors and corrects up to floor(r/2); one illustrated set is {3,4,5,7}.   # pp.30-31
results:
| metric | value | unit | technology / device | baseline | condition | page |
| fault missing rate | zero | rate | UNKNOWN / 2013 | traditional SEU mitigation | single-event upsets in FIR filters | p.37 |
| code rate | 0.33 | ratio | UNKNOWN / 2000 | other RRNS codes | RRNS (9,3), three information/six redundant 8-bit residues | p.37 |
errors_and_checks: Detection/correction bounds are r and floor(r/2) residue-digit errors, respectively; arithmetic faults remain channel-local.   # p.30
conditions: Correction requires sufficient redundant moduli/dynamic range. RRNS can protect arithmetic, storage, communication, and residue-domain DSP operations.   # pp.30, 35-37
evidence: Fig. 2, Fig. 7, §II.B, §III.C-D, pp.29-31, 35-37

### reduced_precision  (role: instantiates)
mechanism: Reduced precision redundancy mitigates voltage-overscaling timing errors in an RNS FIR filter with less hardware than full duplication. # p.33
choices: none
new_choices: none
slots: none
parameters: 0.25 μm, 2.5 V CMOS FIR case study; replica width is UNKNOWN.   # p.33
results:
| metric | value | unit | technology / device | baseline | condition | page |
| energy saving | 62% more | % | 0.25 μm, 2.5 V CMOS / 2013 | conventional TCS filter | voltage-overscaled RNS-RPR FIR | p.33 |
errors_and_checks: Signal-to-noise-ratio degradation is less than 2 dB.   # p.33
conditions: The result applies to an error-tolerable voltage-overscaled FIR system.   # p.33
evidence: §III.A, p.33

## new_families
### rns_forward_converter  (domain: redundant: residue number systems, closest: rns_reverse_converter, why_not: Forward conversion is a distinct integer-to-residue operation rather than residue reconstruction.)
mechanism: A forward converter computes each input residue independently, commonly with multi-operand modular adders using the periodicity of 2^j mod m. Memoryless designs distribute input-bit subsets across modular additions/constant multiplications and avoid exponential ROM growth. # pp.29, 31
choices: modulus_class: {arbitrary, restricted_2n_plusminus_k, special_power_of_two}; implementation: {rom, memoryless_moma, carry_save}; moduli_selection: {fixed, heuristic_range_driven}
results: none
evidence: Fig. 1, §II.B-C, pp.29, 31

## space_gaps
* `rns_channel_arithmetic` needs moduli-set/cardinality/balance choices because performance and converter cost depend strongly on the selected set.   # pp.29, 32
* RNS datapath families need explicit forward-converter/reverse-converter slots because transcoding overhead determines whether channel parallelism produces a system benefit.   # pp.28-29, 31
* `rns_redundant` needs a decoding-method choice for legitimate-range/iterative-exclusion/maximum-likelihood decoders.   # pp.30, 36-37

## open_questions
* The survey aggregates results from cited implementations, so unspecified technology/device details must remain UNKNOWN.
* The paper does not fix one preferred moduli set, reverse-conversion algorithm, or modular operator architecture across applications.
