---
handle: file_webb2007#s01
parent: file_webb2007
citation: Charles Webb, IBM z6 – The Next-Generation Mainframe Microprocessor, © 2007 IBM Corporation
chapter: IBM z6 – The Next-Generation Mainframe Microprocessor
pdf_pages: 0-13
status: ok
kind: slides
unit_classes: [other]
formats: [fixed-point, binary floating point, hexadecimal floating point, decimal floating point, BCD decimal]
authority: slides
pages_read: 14 / 14
---

## summary
The slides instantiate a 36-digit/144-bit decimal floating-point accelerator that converts DPD operands to BCD, computes conditional digit sums, and converts the result back to DPD. The slides also establish residue checking as one part of chip-wide error detection and describe checkpoint/retry/core-sparing recovery. The slides do not classify arithmetic-unit alternatives or report isolated arithmetic latency/area comparisons.

## families
### bcd_direct_addition  (role: instantiates)
mechanism: The decimal dataflow expands DPD operands to BCD and computes four conditional candidates for every digit: A+B+7, A+B+6, A+B+1, and A+B. Per-digit increment stages feed ADD registers before the result is compressed from BCD to DPD.
choices:
  digit_code: bcd8421   # p.9
  correction_placement: presum_plus6   # p.9
  carry_scheme: UNKNOWN   # p.9
new_choices:
  candidate_sums: {A+B+7, A+B+6, A+B+1, A+B} — the four conditional results computed for every digit   # p.9
slots:
  digit_adder: conditional_sum [base_block_width=UNKNOWN, mux_style=UNKNOWN, selection_radix=UNKNOWN]   # p.9
parameters: 144 bits or 36 digits wide   # p.9
results:
| metric | value | unit | technology / device | baseline | condition | page |
| internal datapath width | 144 | bits | IBM 65nm SOI, 2007 | none | decimal floating-point accelerator; also stated as 36 digits | p.9 |
errors_and_checks: The accelerator avoids rounding and other problems caused by binary/decimal conversions; no numerical error bound is reported.   # p.9
conditions: The dataflow supports decimal floating-point and legacy BCD operations mapped onto the DFU.   # p.9
evidence: Decimal Floating Point Accelerator diagrams and annotations, p.9.

### decimal_fp_addition  (role: instantiates)
mechanism: The decimal floating-point accelerator expands DPD operands into BCD, applies a digit-wide conditional-sum dataflow, and compresses the BCD result back into DPD. The slides identify ADD registers but do not specify alignment, normalization, or exception handling.
choices:
  alignment: UNKNOWN   # p.9
  rounding: UNKNOWN   # p.9
  leading_zero_anticipation: UNKNOWN   # p.9
  format: UNKNOWN   # p.9
new_choices:
  none
slots:
  significand_adder: bcd_direct_addition [digit_code=bcd8421, correction_placement=presum_plus6, carry_scheme=UNKNOWN]   # p.9
parameters: 144 bits or 36 digits wide   # p.9
results:
| metric | value | unit | technology / device | baseline | condition | page |
| internal datapath width | 36 | digits | IBM 65nm SOI, 2007 | none | decimal floating-point accelerator | p.9 |
errors_and_checks: The accelerator is presented as avoiding binary/decimal conversion rounding problems; IEEE rounding details are not reported.   # p.9
conditions: The IBM z6 provides full hardware support for decimal floating point.   # p.2
evidence: IBM z6 Architecture, p.2; Decimal Floating Point Accelerator, p.9.

### decimal_encoding_codec  (role: instantiates)
mechanism: DPD operands are expanded to BCD before decimal arithmetic, and the BCD result is compressed back to DPD after the ADD registers.
choices:
  significand_encoding: dpd   # p.9
  codec_placement: inside_operation   # p.9
new_choices:
  none
slots:
  none
parameters: 144 bits or 36 digits wide   # p.9
results:
| metric | value | unit | technology / device | baseline | condition | page |
| codec datapath width | 144 | bits | IBM 65nm SOI, 2007 | none | DPD-to-BCD and BCD-to-DPD conversion around the decimal dataflow | p.9 |
errors_and_checks: The slides state that decimal floating point avoids problems associated with binary/decimal conversions, but no codec error bound is reported.   # p.9
conditions: The codec surrounds the IBM z6 decimal floating-point dataflow.   # p.9
evidence: Decimal Floating Point Accelerator diagrams, p.9.

### commercial_decimal_fpu  (role: instantiates)
mechanism: The IBM z6 contains a hardware decimal floating-point unit co-developed with POWER6. The DFU shares architecture operations/semantics and dataflow elements with POWER6, maps mainframe legacy BCD operations onto the unit, and contains DPD/BCD conversion, conditional digit sums, increment stages, and multiple creation.
choices:
  implementation: hardware_dfu   # p.9
  datapath_width_digits: 36   # p.9
  shared_with_binary_fpu: UNKNOWN   # p.9
new_choices:
  none
slots:
  significand_adder: bcd_direct_addition [digit_code=bcd8421, correction_placement=presum_plus6, carry_scheme=UNKNOWN]   # p.9
  multiplier: UNKNOWN   # p.9
  divider: UNKNOWN   # p.9
parameters: 144 bits or 36 digits wide; multiple creator for 2X and 5X; two rotate cycles   # p.9
results:
| metric | value | unit | technology / device | baseline | condition | page |
| internal datapath width | 36 | digits | IBM 65nm SOI, 2007 | none | IBM z6 DFU | p.9 |
errors_and_checks: The slides report no arithmetic error bound or rounding proof.   # p.9
conditions: The DFU implements decimal floating point in hardware and absorbs mainframe legacy BCD operations.   # p.2, p.9
evidence: IBM z6 Architecture, p.2; Decimal Floating Point Accelerator, p.9.

### residue  (role: instantiates)
mechanism: Residue checking is used with parity checking on data, address, and execution flow as part of fine-grained redundancy and checking throughout the IBM z6.
choices:
  modulus: UNKNOWN   # p.11
  granularity: UNKNOWN   # p.11
  comparison_point: UNKNOWN   # p.11
  generator_style: UNKNOWN   # p.11
  ops_per_checker: UNKNOWN   # p.11
new_choices:
  protected_flow: {data, address, execution} — the flows covered by parity or residue checking   # p.11
slots:
  comparator: UNKNOWN   # p.11
parameters: over 20,000 error checkers in the chip across all checker types   # p.11
results:
| metric | value | unit | technology / device | baseline | condition | page |
| chip error-checker count | over 20,000 | checkers | IBM z6, IBM 65nm SOI, 2007 | none | includes functional, parity, state, residue, ECC, and other checking | p.11 |
errors_and_checks: Parity or residue protects data/address/execution flow; the slides do not report the modulus, aliasing rate, fault model, or isolated residue coverage.   # p.11
conditions: Residue is one part of a broader scheme that also uses ECC, parity, functional checks, state checks, checkpoint retry, core sparing, and machine-check recovery.   # p.11
evidence: Industry-Leading Error Detection and Recovery, p.11.

## taxonomy
IBM z6 error detection and recovery   # p.11
  detection
    ECC on 2nd- and 3rd-level caches/store buffers/R-Unit state array -> unmapped   # p.11
    parity on other arrays/register files -> unmapped   # p.11
    parity or residue on data/address/execution flow -> residue   # p.11
    functional/parity/state checking on control logic -> unmapped   # p.11
  recovery
    precise core retry from buffered architected state -> unmapped   # p.11
    dynamic transparent core sparing for a hard core error -> unmapped   # p.11
    precise software recovery through machine check architecture -> unmapped   # p.11

## primary_sources
none

## new_families
### checkpoint_retry_recovery  (domain: checker: concurrent error detection, closest: duplication, why_not: The mechanism restores buffered architected state or changes cores rather than comparing concurrently replicated arithmetic results.)
mechanism: The R-Unit buffers the processor’s full architected state with ECC. A detected hardware fault can trigger precise core retry for almost all hardware errors. A hard core error can trigger dynamic transparent core sparing, while the machine-check architecture provides precise software recovery for an unrecoverable failure.
choices: checkpoint_state: {full_architected_state}; retry: {precise_core_retry}; hard_error_recovery: {core_sparing}; unrecoverable_recovery: {machine_check_software}
results:
| metric | value | unit | technology / device | baseline | condition | page |
| recoverable fault coverage | almost all | hardware errors | IBM z6, IBM 65nm SOI, 2007 | none | precise core retry using R-Unit checkpoint state | p.11 |
evidence: p.11

## space_gaps
* The checker vocabulary lacks general ECC/parity/state-checking families for the protections listed alongside residue checking.   # p.11
* The decimal vocabulary lacks a component slot for the DFU multiple creator, which produces 2X and 5X through two rotate cycles.   # p.9
* The decimal-adder vocabulary does not directly encode the four per-digit candidates A+B+7/A+B+6/A+B+1/A+B.   # p.9

## open_questions
* The slides do not identify which conditional candidates implement decimal correction, rounding increment, or both.   # p.9
* The slides do not identify the decimal floating-point format despite reporting a 36-digit internal datapath.   # p.9
* The slides do not specify the residue modulus, generator, comparison point, comparator, or coverage.   # p.11
* The slides do not identify the decimal multiplier/divider mechanisms inside the DFU.   # p.9
