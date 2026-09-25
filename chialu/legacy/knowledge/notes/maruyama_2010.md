---
handle: maruyama_2010
citation: T. Maruyama, T. Yoshida, R. Kan, I. Yamazaki, S. Yamamura, N. Takahashi, et al., "Sparc64 VIIIfx: A New-Generation Octocore Processor for Petascale Computing", IEEE Micro, vol. 30, no. 2, pp. 30-40, 2010.
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU, VEC_SFU, VEC_DOT_ACC]
formats: [fp32, fp64]
authority: landmark
pages_read: 30-40 / 11
---

## summary
The document describes the 45-nm, eight-core Sparc64 VIIIfx processor, whose cores each contain two integer ALUs and four floating-point FMA execution units. HPC-ACE adds two-way fp32/fp64 SIMD, reciprocal-approximation instructions for division/square root, and an FMA-like instruction for piecewise minimax sine/cosine evaluation. Parity/residue protection and hardware instruction retry protect the ALUs.

## families
### classic_fma  (role: instantiates)
mechanism: Each core contains four floating-point FMA execution units and executes up to four double-precision FMA operations per cycle. HPC-ACE SIMD instructions operate on paired basic/extended floating-point registers, and one SIMD FMA instruction executes two multiply operations and two add operations. The floating-point register file remains flat for SIMD and non-SIMD access. # pp.30, 34-35
choices:
new_choices:
  simd_width: two fp32 or two fp64 operations per instruction — SIMD basic/extended register pairs supply two lanes. # pp.34-35
slots:
  none
parameters: four FMA execution units per core; up to four fp64 FMA operations per cycle per core; two-way fp32/fp64 SIMD; eight cores; up to 2 GHz. # pp.30-31, 34
results:
| metric | value | unit | technology / device | baseline | condition | page |
| peak chip performance | 128 | gigaflops | 45-nm CMOS / Sparc64 VIIIfx (2010) | none | eight cores at up to 2 GHz | p.31 |
| FMA throughput | up to 4 | double-precision FMA operations per cycle per core | 45-nm CMOS / Sparc64 VIIIfx (2010) | none | four FMA execution units per core | p.30 |
| chip power | as little as 58 | watts | 45-nm CMOS / Sparc64 VIIIfx (2010) | none | average process, Tj of 30° C, water cooling and fine-grained clock gating | p.37 |
| performance per watt | six-fold improvement | relative | 45-nm CMOS / Sparc64 VIIIfx (2010) | previous-generation Sparc64 processors | processor-level result | pp.30, 39 |
errors_and_checks: The document does not state FMA rounding accuracy or exception behavior. ALUs are parity or residue protected, and detected single-bit errors can invoke instruction retry. # pp.38-39
conditions: SIMD execution requires paired basic/extended floating-point registers, although SIMD and non-SIMD instructions can access the flat floating-point register set. # pp.34-35
evidence: execution-unit description on pp.30-32; SIMD description on pp.34-35; performance/power results in Figures 7-9 on pp.37-38.

### piecewise_poly  (role: instantiates)
mechanism: The ftrimadd instruction evaluates piecewise minimax approximations of sine and cosine. Each instruction multiplies the preceding partial result by the square of the input operand and adds a coefficient supplied by hardware, which forms a chained polynomial recurrence. # p.36
choices:
  basis: minimax [outside domain] # p.36
new_choices:
  coefficient_source: hardware_provided — hardware supplies the coefficient added by each ftrimadd instruction. # p.36
slots:
  evaluator: fma_based # p.36
parameters: piecewise evaluation; polynomial degree is not fixed by the instruction description; the evaluated performance suite includes a ninth-degree polynomial benchmark. # pp.36-37
results:
| metric | value | unit | technology / device | baseline | condition | page |
| sine benchmark speedup | 6.8 | times faster | 45-nm CMOS / Sparc64 VIIIfx (2010) | Sparc64 VII core at 2.5 GHz | Sparc64 VIIIfx at 2 GHz with SIMD instructions | pp.36-37 |
| ninth-degree polynomial benchmark speedup | 1.4 | times faster | 45-nm CMOS / Sparc64 VIIIfx (2010) | Sparc64 VII core at 2.5 GHz | Sparc64 VIIIfx at 2 GHz with SIMD instructions | p.37 |
errors_and_checks: The approximation error, coefficient precision, rounding contract, and supported argument range are not reported. # p.36
conditions: The instruction supports floating-point trigonometric functions through software-visible piecewise evaluation rather than a complete single-instruction sine/cosine result. # p.36
evidence: “Other enhancements” on p.36 and Figure 7 on p.37.

### residue  (role: instantiates)
mechanism: Arithmetic logic units are protected by parity or residue checking. The document does not describe the residue modulus, generator, comparison point, or checker sharing. # pp.38-39
choices:
new_choices:
  none
slots:
  none
parameters: UNKNOWN # pp.38-39
results:
| metric | value | unit | technology / device | baseline | condition | page |
| ALU fault coverage | single-bit errors | detectable and correctable through retry | 45-nm CMOS / Sparc64 VIIIfx (2010) | none | ALUs use parity or residue detection; instruction retry supplies recovery | pp.38-39 |
errors_and_checks: The chip detects single-bit errors in registers or ALUs and retries the affected instruction. The document reports no alias rate, false-alarm rate, or checker-specific coverage percentage. # pp.38-39
conditions: Residue is one of two stated ALU protection methods, so the document does not establish which ALUs use residue rather than parity. # p.38
evidence: RAS discussion and Figures 10-11 on pp.38-39.

## new_families
### reciprocal_approximation_instruction  (domain: sfu: elementary-function units, closest: newton_raphson, why_not: The document exposes reciprocal approximations for divide and square root but does not state a Newton-Raphson iteration, seed, or other listed mechanism.)
mechanism: HPC-ACE replaces low-throughput floating-point divide and square-root use with instructions that produce reciprocal approximations. Software uses the approximations to implement divide and square-root computations, but the document does not state the approximation algorithm or accuracy. # p.35
choices: function: {divide_reciprocal, square_root_reciprocal, both}; implementation_method: UNKNOWN; accuracy_contract: UNKNOWN
results:
| metric | value | unit | technology / device | baseline | condition | page |
| divide/square-root execution throughput | more than four times | previous-generation throughput | 45-nm CMOS / Sparc64 VIIIfx (2010) | Sparc64 VII | reciprocal-approximation instructions replace divide/square-root instructions in SIMD-oriented code | p.35 |
| divide benchmark speedup | 4.3 | times faster | 45-nm CMOS / Sparc64 VIIIfx (2010) | Sparc64 VII core at 2.5 GHz | Sparc64 VIIIfx at 2 GHz with SIMD instructions | pp.36-37 |
evidence: SIMD instruction discussion on p.35 and Figure 7 on p.37.

### instruction_retry_recovery  (domain: checker: concurrent error detection, closest: time_redundancy, why_not: Recovery is triggered by an independently detected error and repeats an untransformed instruction until success or a threshold, rather than using a fixed transformed recomputation.)
mechanism: Detection cancels all in-flight instructions before commit. Hardware then executes the faulting instruction alone and resumes normal execution if that instruction commits without error. Failed retries repeat until success or a threshold, after which hardware interrupts software. Successful recovery is invisible to software. # pp.38-39
choices: trigger: {detected_error}; retry_execution: {single_step_alone}; retry_limit: {threshold}; failure_action: {software_interrupt}
results:
| metric | value | unit | technology / device | baseline | condition | page |
| corrected fault class | any single-bit error | registers or ALUs | 45-nm CMOS / Sparc64 VIIIfx (2010) | none | the error is detected and a retry succeeds before the retry threshold | pp.38-39 |
evidence: “Hardware instruction retry” and Figure 10 on pp.38-39.

## space_gaps
* `multi_precision_simd_fma.lane_split` lacks `2x64`, although HPC-ACE defines two-way double-precision SIMD FMA; the document does not establish whether one datapath is physically split. # pp.34-35
* The vocabulary lacks an accuracy-unspecified reciprocal/reciprocal-square-root approximation instruction family for commercial processors. # p.35
* The checker vocabulary lacks detected-error-triggered instruction retry with repeated single-step execution and a retry threshold. # pp.38-39

## open_questions
* The FMA datapath topology, pipeline depth, multiplier family, carry-propagate adder, and rounding mechanism are not reported.
* The reciprocal-approximation algorithm, output precision, error bound, and software refinement sequence are not reported.
* The ftrimadd polynomial degree/segments/coefficient widths/range-reduction method and approximation error are not reported.
* The ALU residue modulus, generator style, comparison point, protected-operation set, and alias rate are not reported.
