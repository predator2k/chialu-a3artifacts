---
handle: sullivan_2018
citation: M. B. Sullivan, S. K. S. Hari, B. Zimmer, T. Tsai, S. W. Keckler, "SwapCodes: Error Codes for Hardware-Software Cooperative GPU Pipeline Error Detection", Proc. MICRO-51, pp. 762-774, 2018
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [int32, int64, fp32, fp64]
authority: incremental
pages_read: 762-774 / 13
---

## summary
SwapCodes combines intra-thread instruction duplication with register-file ECC so pipeline errors are checked implicitly on register reads without explicit comparison instructions or shadow registers (pp.762, 765). Swap-Predict adds selective check-bit predictors for common arithmetic operations, achieving 15% mean slowdown while detecting more than 99.3% of injected pipeline errors with a residue code (pp.762-763, 770).

## families
### duplication  (role: compares)
mechanism: The software baseline executes each arithmetic instruction twice, keeps original and shadow register spaces, and inserts equivalence checks before control-flow/memory/non-duplication-eligible instructions. SwapCodes retains instruction duplication but pairs original data with shadow-generated check-bits in one register, so the register-file decoder performs the comparison implicitly. (pp.764-765, 768)
choices:
  replication: 2   # p.765
new_choices:
  comparison_trigger: before_control_flow_memory_or_ineligible_instruction — The software baseline inserts checks at these boundaries.   # p.768
slots:
  comparator: none
parameters: intra-thread instruction pairs; 32-thread GPU warps; no added SwapCodes pipeline stage assumed   # pp.763, 768
results:
| metric | value | unit | technology / device | baseline | condition | page |
| mean slowdown | 49% | percent | NVIDIA Tesla P100; year UNKNOWN | un-duplicated program | software intra-thread duplication | p.770 |
| worst-case slowdown | 99% | percent | NVIDIA Tesla P100; year UNKNOWN | un-duplicated program | software intra-thread duplication; b+tree | p.770 |
| mean dynamic instruction bloat | 91% | percent | NVIDIA Tesla P100; year UNKNOWN | un-duplicated program | software intra-thread duplication | p.770 |
| mean slowdown | 113% | percent | NVIDIA Tesla P100; year UNKNOWN | un-duplicated program | inter-thread duplication | p.772 |
| maximum slowdown | 241% | percent | NVIDIA Tesla P100; year UNKNOWN | un-duplicated program | inter-thread duplication | p.772 |
errors_and_checks: Software-enforced duplication has 0% SDC risk under the paper's metric because original/shadow results are explicitly compared.   # p.769
conditions: Intra-thread duplication is programmer-transparent but increases register usage, arithmetic operations, and checking instructions. Inter-thread duplication fails for some thread-count/intra-warp-communication cases.   # pp.762, 764, 771
evidence: Table I; Figures 2, 3, 12, 13, and 15; Sections II-C, III-A, IV-C, and V (pp.764-765, 770-772)

### residue  (role: instantiates)
mechanism: Swap-Predict uses low-cost residues with modulus A = 2^a-1. Residue addition uses an a-bit end-around-carry adder, while multiplication/MAD uses modular partial products, a carry-save multi-operand modular-adder tree, and an end-around-carry adder. Mixed-width MAD derives the full 64-bit addend residue from two 32-bit residues and recodes the result into separate 32-bit register codewords. (pp.767-768)
choices:
  modulus: 3   # pp.767, 769
  modulus: 127 [outside domain]   # pp.767, 769-770
  granularity: endpoint   # pp.767-768
  generator_style: csa_tree   # p.767
new_choices:
  checking_point: register_read — The existing register-file decoder checks the swapped codeword whenever a register is read.   # pp.762, 765
slots:
  comparator: none
parameters: Mod-3 uses 2 check-bits; Mod-127 uses 7 check-bits; evaluated MAD has 32-bit multiplicands, a 64-bit addend, and a 64-bit output split into 32-bit codewords   # pp.767-769
results:
| metric | value | unit | technology / device | baseline | condition | page |
| SDC risk | < 5% | probability | 16nm industrial library; year UNKNOWN | 100% unprotected SDC risk | Mod-3 across injected arithmetic-unit errors | p.769 |
| pipeline error-rate reduction | > 20x | ratio | 16nm industrial library; year UNKNOWN | unprotected pipeline | Mod-3 | p.769 |
| worst-case 95% CI SDC risk | 0.7% | probability | 16nm industrial library; year UNKNOWN | 100% unprotected SDC risk | Mod-127 | p.770 |
| Add predictor area overhead | 5.91% | percent | 16nm industrial library; year UNKNOWN | 32-bit Add datapath | Mod-3; 42 NAND2 | p.771 |
| MAD predictor area overhead | 0.98% | percent | 16nm industrial library; year UNKNOWN | 32+64-bit MAD datapath | Mod-3; 98 NAND2 | p.771 |
| MAD predictor area overhead | 5.87% | percent | 16nm industrial library; year UNKNOWN | 32+64-bit MAD datapath | Mod-127; 584 NAND2 | p.771 |
errors_and_checks: Mod-127 detects more than 99.3% of injected pipeline errors. Mod-3 leaves less than 5% SDC risk. Coverage depends on the underlying code, and errors beyond its detection strength can alias to valid codewords.   # pp.763, 769-770
conditions: Low-cost residue prediction supports modular add/multiply directly. Mixed 32/64-bit MAD requires addend-residue reconstruction and output recoding.   # pp.767-768
evidence: Figures 8-11; Tables III-IV; Sections III-C, IV-B, and IV-D (pp.767-771)

### end_around_carry  (role: instantiates)
mechanism: Low-cost residue generators and predictors use end-around-carry adders for modulo 2^a-1 arithmetic. The implementation can add an extra level to a parallel-prefix adder to re-propagate carry-out internally. (p.767)
choices:
  modulus: mod_2n_minus_1   # p.767
  recirculation: cyclic_prefix_level   # p.767
new_choices:
  none
slots:
  none
parameters: width a bits; examples use a=2 for Mod-3 and a=7 for Mod-127   # pp.767, 769
results:
| metric | value | unit | technology / device | baseline | condition | page |
| predictor clock target | 2GHz | clock | 16nm industrial library; year UNKNOWN | UNKNOWN | two-stage multiply-add prediction pipeline | p.769 |
errors_and_checks: none
conditions: The construction applies to low-cost residue moduli A = 2^a-1.   # p.767
evidence: Section III-C and Figure 9 (pp.767-768)

## new_families
### swapped_codeword_duplication  (domain: checker: concurrent error detection, closest: duplication, why_not: duplication lacks split data/check-bit production, implicit register-read checking, and selective check-bit prediction)
mechanism: Each instruction executes as an original/shadow pair. The original writes data, while the shadow overwrites only the register ECC check-bits, producing a codeword whose data/check-bits come from independent computations. A single pipeline error therefore cannot corrupt both portions. Register-file ECC checks the pair on reads. Swap-ECC always duplicates eligible arithmetic; Swap-Predict bypasses duplication when a separate predictor generates trustworthy check-bits. SEC-DED-DP/SEC-DP distinguish storage errors from compute errors to prevent compute-error miscorrection. (pp.765-767)
choices: organization: {swap_ecc, swap_predict}; storage_correction: {SEC-DED-DP, SEC-DP, detection_only}; predicted_operations: {moves, fixed_point_add_sub, fixed_point_multiply_mad}   # pp.765-768
results:
| metric | value | unit | technology / device | baseline | condition | page |
| mean slowdown | 21% | percent | NVIDIA Tesla P100; year UNKNOWN | un-duplicated program | Swap-ECC | p.770 |
| mean slowdown | 16% | percent | NVIDIA Tesla P100; year UNKNOWN | un-duplicated program | Swap-Predict Pre AddSub | p.770 |
| mean slowdown | 15% | percent | NVIDIA Tesla P100; year UNKNOWN | un-duplicated program | Swap-Predict Pre MAD | p.770 |
| worst-case slowdown | 74% | percent | NVIDIA Tesla P100; year UNKNOWN | un-duplicated program | Swap-Predict; lavaMD | p.770 |
| dynamic instruction bloat | 33% | percent | NVIDIA Tesla P100; year UNKNOWN | un-duplicated program | Swap-Predict Pre MAD | p.770 |
| worst-case energy increase | 11% | percent | NVIDIA Tesla P100; year UNKNOWN | unprotected execution | Swap-ECC on SNAP | p.771 |
evidence: Figures 2-9 and 12-14; Tables II-IV; Sections III-IV (pp.765-771)

## space_gaps
* `residue.modulus` lacks 127, which the paper evaluates as a 7-bit low-cost residue code.   # pp.767, 769-770
* `residue.comparison_point` lacks `register_read`, which is the implicit checking point used by SwapCodes.   # pp.762, 765
* The checker vocabulary lacks a slot for arithmetic check-bit predictors that generate residue/ECC bits independently of the protected datapath.   # pp.767-768

## open_questions
* Figure 11 does not print exact per-operation SDC-risk values, so only the textual worst-case bounds are extractable.   # pp.769-770
* The paper does not report a year for the measured P100 runs or synthesized 16nm results.
