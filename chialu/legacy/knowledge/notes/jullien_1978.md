---
handle: jullien_1978
citation: Jullien, "Residue Number Scaling and Other Operations Using ROM Arrays", IEEE Transactions on Computers, 1978
actual_citation: same
status: ok
kind: paper
unit_classes: [other]
formats: [signed_int16, signed_int18, fixed_point_residue]
authority: landmark
pages_read: 325-336 / 12
---

## summary
The paper implements residue addition/subtraction/multiplication/scaling with high-density ROM lookup arrays and develops exact-division and scaled-metric-vector-estimate scaling algorithms. # p.325,p.336
The paper applies the architecture to a scaled multiplier and a second-order recursive digital filter. # p.334-p.336

## families
### rns_scaling_comparison  (role: proposes)
mechanism: The scaling factor K is a product of S moduli. The exact algorithm iteratively divides using multiplicative inverses, performs partial mixed-radix conversion, and extends the result into the removed moduli. The estimate algorithm sums scaled Chinese-remainder metric vectors for the retained residues and uses mixed-radix base extension for the remaining residues. Parallel two-input ROM computations reduce the operation to at most N lookup cycles. # p.327-p.334
choices:
  operation: scale   # p.327
  method: rom_mrc (exact-division algorithm); crt_fraction_estimate (scaled-metric-vector algorithm)   # p.328,p.330-p.332
  exactness: exact (exact-division algorithm); approximate_with_correction (estimate algorithm)   # p.328,p.331-p.332
new_choices:
  rounding: round_down | round_off — selects truncation or addition of a fixed half-scale quantity before scaling   # p.327,p.332
slots: none
parameters: N moduli; S scaled-out moduli; K=product of the first S moduli; N=6/S=3 example; latency ne=N+n1-S for estimates and no=N for the original algorithm   # p.327-p.334
results:
| metric | value | unit | technology / device | baseline | condition | page |
| lookup-table count | 18 | 8K ROM packages | 8K semiconductor ROM; node UNKNOWN; 1978 | original requirement of N additions, N multiplications, and S linear equations | N=6, S=3 estimate scaling | p.334 |
| scaling latency | at most N | look-up cycles | 8K semiconductor ROM; node UNKNOWN; 1978 | original requirement of N additions, N multiplications, and S linear equations | sufficient parallel hardware | p.334 |
| scaling package count | 34 | ROM packages | 8K semiconductor ROM; node UNKNOWN; 1978 | UNKNOWN | N=8, S=4, 18-bit multiplier application | p.334 |
| scaling latency | 7 | look-up cycles | 8K semiconductor ROM; node UNKNOWN; 1978 | UNKNOWN | N=8, S=4, 18-bit multiplier application | p.334 |
| complete multiplier package count | 42 | 8K ROM's | 8K semiconductor ROM; node UNKNOWN; 1978 | UNKNOWN | 18 x 18 bit signed multiplication scaled to 18-bit output | p.334,p.336 |
| complete multiplier latency | 8 | look-up cycles | 8K semiconductor ROM; node UNKNOWN; 1978 | UNKNOWN | 18 x 18 bit signed multiplication scaled to 18-bit output | p.334,p.336 |
errors_and_checks: The estimate error satisfies |ε|<(S+1)/2 for retained-residue computation. Estimate scaling is less accurate than exact division, and fixed scaling can lose all precision when an unscaled result is of order M/K. # p.332,p.334,p.336
conditions: K must be a product of moduli for fast access to the scaling remainder. Estimate-based base extension alone is unsuitable for high-speed processing. The estimate realization uses no more cycles and fewer lookup tables than the original algorithm, with equality for limited S cases. # p.327-p.328,p.332-p.334
evidence: §III, (4), (6), (10), (17)-(20), (26), (28)-(31), Figs. 3-7, §IV.A, §VI, p.327-p.336

### rns_channel_arithmetic  (role: instantiates)
mechanism: Each residue channel uses a ROM addressed by two residues to return the modular addition/subtraction/multiplication result. Moduli no larger than 32 keep each residue within 5 bits, so two-input tables use 10 address bits and 5 output bits. Fixed operations in a chain can be folded into one lookup table. # p.326-p.327
choices:
  modulus_form: generic   # p.326-p.327
  channel_width_n: 5   # p.327
  multiplier_reduction: rom   # p.326-p.327
new_choices:
  operation_realization: rom_lookup | boolean_logic — selects stored modular outcomes or implemented Boolean functions   # p.326
slots: none
parameters: maximum modulus 32; maximum residue width 5 bits; two-input address width 10 bits; 5 output bits used from an 8-bit ROM word   # p.326-p.327
results:
| metric | value | unit | technology / device | baseline | condition | page |
| package count | 7 | 8K ROM's | Intersil IM53S08/18 example; node UNKNOWN; 1978 | 32 LSI IC's and 29 MSI IC's, excluding control circuitry | 16 x 16 bit signed multiplication in 32-bit precision | p.327 |
| propagation delay | 55 | ns | Intersil IM53S08/18 example; node UNKNOWN; 1978 | about 115 ns for 4 bit x 4 bit multipliers and lookahead adders | 16 x 16 bit signed multiplication | p.327 |
errors_and_checks: Binary operations within the residue channels introduce no roundoff error; errors occur during scaling. # p.335
conditions: Addition/subtraction/multiplication are independent across equal-modulus residue pairs. General-purpose use remains limited by scaling/division/sign/magnitude operations. # p.326
evidence: §II.B, Tables I-II, Fig. 1, p.326-p.327

### rns_reverse_converter  (role: instantiates)
mechanism: Residue-to-binary conversion first produces mixed-radix digits. A ROM connected to each mixed-radix digit generates a binary contribution, and the contributions are summed; limited-width cases can combine the sum within a lookup table. # p.335
choices:
  algorithm: mixed_radix   # p.335
  implementation: rom   # p.335
new_choices: none
slots: none
parameters: 8-bit limited-precision example; two mixed-radix digits; moduli 15 and 17; ROM organization 512 x 8 bits   # p.335
results:
| metric | value | unit | technology / device | baseline | condition | page |
| table count | one | 4K look-up table | semiconductor ROM; node UNKNOWN; 1978 | UNKNOWN | 8-bit conversion using moduli 15 and 17 | p.335 |
errors_and_checks: none
conditions: Residue-to-binary conversion is more difficult than binary-to-residue conversion. Reduced-base conversion can be performed through the scaling process. # p.335
evidence: §V.B, p.335

### rns_dsp_datapath  (role: instantiates)
mechanism: A second-order recursive filter performs five multiplications and four additions in residue channels, then shares one scaling operation at the central node. Fixed coefficients and adjacent operations are combined in ROM tables. Latching each lookup-cycle result permits pipelined operation and multiplexing of filter sections. # p.334-p.336
choices:
  kernel: iir   # p.334-p.335
  scaling_placement: per_block   # p.334-p.336
new_choices: none
slots: none
parameters: second-order canonic section; W=12 data bits; C=9 coefficient bits; N=5; S=2; M=1.16 x 2^24; scaling factor 1.76 x 2^9; typical ROM cycle time 90 ns   # p.334-p.335
results:
| metric | value | unit | technology / device | baseline | condition | page |
| package count | 34 | 8K ROM packages | Intersil IM53S08/18 example; node UNKNOWN; 1978 | UNKNOWN | 9-bit coefficient word and 12-bit data word | p.334,p.336 |
| latency | 7 | look-up cycles | 8K semiconductor ROM; node UNKNOWN; 1978 | UNKNOWN | one second-order section | p.334,p.336 |
| input data rate | over 11 | MHz | 90 ns ROM cycle; node UNKNOWN; 1978 | UNKNOWN | pipelined multiplexed section | p.335 |
| package count | 68 | IC's | 90 ns ROM cycle; node UNKNOWN; 1978 | UNKNOWN | two sections in tandem | p.335 |
| input data rate | over 22 | MHz | 90 ns ROM cycle; node UNKNOWN; 1978 | UNKNOWN | two sections in tandem | p.335 |
errors_and_checks: Arithmetic before scaling uses extended precision without roundoff. Scaling injects one noise source at the central node; under uniform/zero-mean/uncorrelated-noise assumptions, the residue-to-standard output-noise variance ratio is σr²/σs²=F/(3+2F). # p.335
conditions: The architecture is suitable when addition/multiplication substantially outnumber scaling/sign/magnitude operations. Normalizing/scaling factors must satisfy coefficient/data worst-case bounds and prevent overflow. # p.326,p.334-p.335
evidence: §IV.B, Fig. 8, §VI, p.334-p.336

## new_families
### binary_to_rns_converter  (domain: redundant: residue number systems, closest: rns_reverse_converter, why_not: rns_reverse_converter covers the opposite conversion direction)
mechanism: Each binary input chunk addresses one ROM per modulus to produce its residue contribution. A single chunk converts in one lookup cycle; wider binary words are partitioned into smaller chunks whose residue contributions are summed. For two's-complement input, the chunk containing the sign bit is treated as signed and the other chunks as unsigned. # p.335
choices: binary_partition: {single_rom, split_and_residue_sum}; signed_input: Bool
results:
| metric | value | unit | technology / device | baseline | condition | page |
| package count | N | 8K ROM's | semiconductor ROM; node UNKNOWN; 1978 | UNKNOWN | 10-bit binary input, residues below 32 | p.335 |
| latency | one | look-up cycle | semiconductor ROM; node UNKNOWN; 1978 | UNKNOWN | 10-bit binary input | p.335 |
| package count | 3N | ROM's | 8K semiconductor ROM; node UNKNOWN; 1978 | UNKNOWN | 20-bit input split into two equal parts | p.335 |
| latency | two | look-up cycles | 8K semiconductor ROM; node UNKNOWN; 1978 | UNKNOWN | 20-bit input split into two equal parts | p.335 |
evidence: §V.A, p.335

## space_gaps
* rns_channel_arithmetic lacks an `operation_realization` choice for ROM lookup versus Boolean/modular arithmetic logic. # p.326
* The `modular_adder` slot cannot represent a ROM lookup-table channel implementation. # p.326-p.327

## open_questions
* The paper does not quantify the final output-error distribution of scaled-metric-vector estimation beyond intermediate bounds and qualitative comparison with exact division.
* The paper does not identify a semiconductor process node for any ROM implementation.
