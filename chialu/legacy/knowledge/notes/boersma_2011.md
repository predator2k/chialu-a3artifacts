---
handle: boersma_2011
citation: M. Boersma, M. Kroener, C. Layer, P. Leber, S. M. Mueller, K. Schelm, "The POWER7 Binary Floating-Point Unit", ARITH-20, 2011
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU, VEC_DOT_ACC]
formats: [fp32, fp64]
authority: incremental
pages_read: 87-91 / 5
---

## summary
The POWER7 floating-point unit is a 5.5-cycle fused multiply-add design, compliant with IEEE 754-2008, that merges the scalar and vector FPUs of previous PowerPC designs into one unit executing the scalar single and double precision set, the VMX single precision vector set and the new VSX vector and scalar set. Four 64-bit instances per core replace the POWER6 scalar and vector FPUs, each measuring 0.26mm2 in 45nm CMOS SOI at a 4.14GHz chip frequency. A rebiased two's complement internal exponent, rounding information precomputed in the normalizer and the leading-zero anticipator, and a three-stack buffer-free floorplan shorten the POWER6 pipeline by roughly one stage.

## families

### classic_fma  (role: instantiates)
mechanism: The FMA A*C+B takes its operands from the operand latches in parallel through the aligner and the Booth multiplier into the adder, with multiplier and aligner in the first two stages, two stages for the addition, one stage to normalize and one stage for rounding and packing. The adder also handles rounding and saturation for integer results, which are muxed into the final pack step after the exit point for 5.5-cycle forwarding. The normalizer and leading-zero anticipator compress the shifted-out bits in parallel with the shifting to precompute sticky bits and carry-out for different target precisions, reduce the leading ones to speed the carry propagation of a potential rounding increment, and precompute exponent wraps for overflow and underflow.
choices: none
new_choices:
  internal_exponent_rebiasing: target_emin_biased_twos_complement — the 13-bit intermediate exponent is rebiased with the minimum exponent eminT of the target precision (eminSP = -126, eminDP = -1022) in a 13-bit biased two's complement format instead of the conventional constant bias13b = 4095, so underflow is the sign bit of the exponent and the 13-bit comparators disappear   # p.90
  forwarded_result_format: rounded_internal_representation — the fully rounded result is available after 5.5 cycles in an internal representation with special value flags, forwarded to the local and remote FPU and muxed directly into the operand latches, where POWER6 forwarded unrounded results and needed a fix-up inside the multiplier   # p.89
  rounding_target_precision: instruction_selected_sp_or_dp — all scalar arithmetic FP operations come in two flavours, rounding either to SP or to DP precision on 64-bit operands   # p.88
slots:
  align: full_align   # p.89 (Fig. 3), p.90
  lza: lza   # p.89 (Fig. 3, "Adder & LZA"), p.90 ("a leading zero anticipator operating on the trailing 110 bits of the sum")
  multiplier: booth_recoded_parallel   # p.89 ("33 partial products in the Booth multiplier")
parameters: 53 x 53-bit DP significand multiply; 33 partial products when the 64-bit FX multiply shared the multiplier, 6 more than a conventional 53 x 53-bit DP multiplier needs; 160-bit wide sum into normalizer and rounder; LZA over the trailing 110 bits of the sum; 13-bit internal exponent; six pipeline stages EX1-EX6; product exponent ep = ea + ec with sum exponent es = eb, ep+57 or ep+3; four FPU instances per core on two execution pipes   # p.89, p.90
results:
| metric | value | unit | technology / device | baseline | condition | page |
| area, single 64-bit FPU instance | 0.26 | mm2 | 45nm CMOS SOI, 2011 | POWER6 64-bit FPU scaled into 45nm: 0.46mm2 | one instance, four per core | p.87 |
| area, POWER6 units scaled into 45nm | about 2.5 | mm2 | 45nm (scaled), 2011 | — | two 64-bit scalar FPUs, a vector FPU of four 32-bit instances, a vector FX multiplier | p.87 |
| area ratio, single instance | 1.8 | x smaller | 45nm CMOS SOI, 2011 | POWER6 64-bit FPU | per instance | p.87 |
| total FPU area ratio | 2.5 | x smaller | 45nm CMOS SOI, 2011 | POWER6 total FPU area | increased functionality and two times higher DP throughput | p.87 |
| area reduction from pipeline streamlining and reduced frequency | 1.8 | factor | 45nm CMOS SOI, 2011 | POWER6 | component of the 2.5 factor | p.91 |
| area reduction (abstract wording) | 2 | factor | 45nm CMOS SOI, 2011 | POWER6, beyond the normal technology shrink | abstract | p.87 |
| chip frequency supported | 4.14 | GHz | 45nm CMOS SOI, 2011 | — | — | p.87 |
| FMA latency to fully rounded result | 5.5 | cycles | 45nm CMOS SOI, 2011 | POWER6: 6-cycle back-to-back only by forwarding unrounded results within an instance, 8 cycles for a fully rounded result | half a cycle left for distribution to local and remote FPU | p.87, p.89 |
| back-to-back FP latency | 6 | cycles | 45nm CMOS SOI, 2011 | POWER6 remote forwarding: one extra cycle | FP result usable by the FPUs | p.89 |
| FX result forwarding latency | 7 | cycles | 45nm CMOS SOI, 2011 | FP result at 6 cycles | integer results muxed in after the 5.5-cycle exit point | p.89 |
errors_and_checks: fully compliant with the IEEE 754-2008 standard (p.87). The normalization shift amount is limited to nsha = min(LZC, Es) and underflow is detected when LZC > es - emin, which the rebiasing turns into an inspection of the exponent's sign bit; overflow is detected by comparing er against emax (p.90). No fault model and no concurrent error detection are reported.
conditions: The out-of-order core requires symmetric forwarding latencies for local and remote FPU and a 6-cycle back-to-back latency, with flush conditions kept to a minimum, which forces the fully rounded result at 5.5 cycles (p.89). The 64-bit FX multiplication was moved back to the scalar FXU to cut partial products and multiplier delay, leaving the short vector FX multiplies on the FPU (p.89). In this high frequency design a signal can barely cross an FPU on default wire using M1 to M5, so the three-stack U-shaped floorplan places multiplier and aligner between operand latches and adder, and adder output, normalizer and rounder buffer-free in a third stack, with exponent, control and divide logic outside the main data flow (p.90, p.91).
evidence: Abstract; Sec. I; Sec. III; Sec. IV-A; Sec. IV-B; Sec. V; Sec. VI; Figs. 2, 3, 4, 5.

### multi_precision_simd_fma  (role: instantiates)
mechanism: One 64-bit FPU instance executes scalar SP, scalar DP and vector DP operations, and the operands of scalar SP arithmetic instructions are 64-bit DP register file data whose intermediate result is rounded to SP with a single rounding error and then converted back to 64-bit DP. The normalizer and the leading-zero anticipator precompute sticky bits and carry-out information for the different target precisions. Vector width comes from instances rather than from lanes inside one datapath: one FPU serves scalar code, two serve vector DP, and all four serve vector SP.
choices:
  lane_split: 1x64   # p.89 — each instance is one 64-bit datapath
  shared_rounder: true   # p.88, p.89 — one rounder per instance serves the SP and DP target precisions
new_choices:
  simd_element_source: fpu_instance_per_element — 4-way SIMD SP and 2-way SIMD DP take one 64-bit FPU instance per element instead of splitting one datapath into narrower lanes   # p.89
slots:
  align: full_align   # p.89
  lza: lza   # p.89
parameters: 128-bit wide VSR with 64 entries combining 32 64-bit FPR and 32 128-bit VR; 2-way SIMD DP and 4-way SIMD SP elements in 64-bit and 32-bit IEEE-754 memory format; four 64-bit FPUs per core   # p.88, p.89
results:
| metric | value | unit | technology / device | baseline | condition | page |
| area reduction from merging the vector and scalar FPUs | 1.35 | factor | 45nm CMOS SOI, 2011 | POWER6 separate vector and scalar FPUs | component of the 2.5 factor total FPU area reduction | p.91 |
| architected register space | 2 | x | 45nm CMOS SOI, 2011 | previous designs | VSX scalar and vector instructions access all 64 VSR | p.88 |
errors_and_checks: The scalar SP arithmetic intermediate result carries a single rounding error before conversion to 64-bit DP (p.88). Heterogeneous precision arithmetic is the support required by IEEE 754-2008 (p.88).
conditions: Programs that combine SP scalar and vector register data need explicit conversions between 64-bit scalar SP and 32-bit vector SP format, because scalar FP data are stored in 64-bit DP format in the register file whatever their precision (p.88).
evidence: Sec. II-A; Sec. II-B; Sec. III; Figs. 1, 3.

### replicated_lanes  (role: instantiates)
mechanism: The VSU comprises four DP FPUs, a vector FXU and a 128-bit wide permute unit, all assigned to two execution pipes. Pipe 1 also executes permute instructions, using one or two FPUs; pipe 0 also executes vector FX and vector SP instructions. A packing circuit at the end of the pipeline reformats the data from the internal FPU format to the architected register file format, muxes in the integer results and potential constants, and the result is distributed by a forwarding network to all subunits of the VSU, including the FPUs and the register file.
choices: none
new_choices: none
slots: none
parameters: four 64-bit FPU instances, one vector FXU, one 128-bit wide permute unit, two execution pipes   # p.89
results:
| metric | value | unit | technology / device | baseline | condition | page |
| FX result forwarding latency | 7 | cycles | 45nm CMOS SOI, 2011 | FP result at 6 cycles | FX results produced by the FPU | p.89 |
errors_and_checks: none
conditions: The vector FX units perform vector FX arithmetic, data permutations and bit manipulations, so the permute unit is a separate 128-bit unit rather than a mode of the FPUs (p.88, p.89).
evidence: Sec. II; Sec. III; Fig. 3.

### shift_round_convert  (role: instantiates)
mechanism: A scalar SP load converts 32-bit SP memory data into 64-bit DP format before the register file write, and a scalar SP store converts the 64-bit DP register data back to 32-bit SP. For SP numbers in the normal SP range the conversion pads the fraction with 29 trailing zeros and rebiases the exponent by E' = E - biasSP + biasDP = E - 127 + 1023 = E + 896, the bias difference applied by inserting three copies of the inverse of the most significant exponent bit. For SP subnormal numbers the exponent is rebiased to 381_16, the fraction is normalized and the exponent is adjusted by the normalization shift amount. The adder handles rounding and saturation for the integer results.
choices: none
new_choices:
  subnormal_operand_representation: architected_pattern_plus_dirty_flag — the register file holds the exact architected bit pattern and each register carries a dirty flag, zero for vector data in architected format (type-1) and for scalar DP data matching the architected pattern (type-2), one for scalar DP data not matching it (type-3), where the flag replaces the implied bit; the earlier implementation kept SP subnormals in a 65-bit intermediate format including the implied integer bit, with the exponent rebiased to 381_16 and the fraction padded with 29 trailing zeros   # p.88
slots: none
parameters: 32-bit SP memory format, 64-bit DP register format, 29 trailing zero fraction pad, bias difference 896_10 = 380_16, subnormal exponent 381_16, 65-bit intermediate format of the earlier scheme, three data types   # p.88
results: none
errors_and_checks: Normalizing SP subnormals at conversion would otherwise require an additional normalization stage on the FPU execution pipeline and on the load datapath (p.88). When type-3 data are accessed by another unit, used as a vector SP operand or as an FX operand, a flush request is triggered, the hypervisor executes normalizing vector-DP-moves on every register file entry to convert type-3 data into architected format, and the instruction causing the flush request is reissued (p.88).
conditions: The register file must store the exact architected bit pattern because scalar DP data are now also accessed by vector FX and vector SP instructions, which the earlier 65-bit intermediate format does not allow (p.88). A valid flag per second doubleword lets a scalar write update only half the register file and still keeps undefined data from being observed by other instructions or programs (p.88).
evidence: Sec. II-A; Sec. II-B; Sec. II-C; Fig. 1.

## new_families
none

## space_gaps
* `classic_fma` has no `exp` slot for `exponent_path`, although the exponent path computes the shift amounts for the mantissa datapath, the overflow and underflow conditions and the result exponent, and carries this document's two most critical paths (p.90).
* No FMA family carries a choice for the internal exponent representation, so the biased two's complement format rebiased with the target precision's eminT, which removes several 13-bit comparators, has nowhere to land (p.90).
* `classic_fma` has no `subnormal_representation` choice, while the fp adder families do; POWER7 settles it as the architected pattern plus a dirty flag against the 65-bit pseudo-normalized intermediate format of the earlier design (p.88).
* No choice records whether the forwarded result is rounded or unrounded, which is the property POWER7 changes from POWER6 and the reason for the 5.5-cycle target (p.89).
* No choice records that sticky bits, carry-out, leading-one reduction and exponent wraps are precomputed in the normalizer and LZA for several target precisions, which the document names as the key to a half-cycle rounder (p.89, p.91).

## open_questions
* The Booth radix is not stated; the document gives only 33 partial products for the shared 64-bit FX multiply and "6 more than needed for a conventional 53 x 53-bit DP multiplier" (p.89).
* Fig. 3 shows an "Incrementer" stage at EX4 beside "Adder & LZA", and Sec. IV-A gives er = en + cout for the exponent, so it is not settled whether the rounding uses `increment_adder` or `compound_adder_select`, nor which family fills the `cpa`, `round` and `norm_shifter` slots (p.89, p.90).
* Whether FP add and FP multiply execute on the FMA datapath (`subsume_fp_add`) is not stated (p.87).
* The abstract reports "a factor of 2 area reduction over the POWER6 design", while Sec. I and Sec. VI report 2.5 for the total FPU area and 1.8 for a single instance (p.87, p.91).
* Divide logic is named only as a block placed outside the main data flow in the floorplan; no division algorithm, latency or family is given (p.91).
* The alignment width is not given directly; the exponent cases ep + 57 > eb > ep + 3 and the 160-bit wide sum are the only figures the document supplies (p.90).
