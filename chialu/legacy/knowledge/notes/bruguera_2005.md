---
handle: bruguera_2005
citation: J. D. Bruguera, T. Lang, "Floating-Point Fused Multiply-Add: Reduced Latency for Floating-Point Addition", ARITH-17, pp. 42-51, 2005
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [fp64]
authority: incremental
pages_read: 10 / 10
---

## summary
The paper proposes a double-precision fused multiply-add architecture that lets floating-point addition bypass the multiplier stages. A CLOSE/FAR double datapath keeps full alignment and full normalization off the same critical path, while normalization before addition enables combined addition and rounding with a dual adder. The resulting addition latency is 2 cycles in a 3-stage unit or 3 cycles in a 5-stage unit. # p.1, p.4, p.9

## families
### reduced_latency_fma  (role: proposes)
mechanism: The unit moves addend alignment after multiplication so a pure addition enters after the multiplier. CLOSE and FAR datapaths separate cases requiring full normalization from cases requiring full alignment. Both paths normalize carry-save operands before the final addition. A 53-bit dual adder computes the sum and sum+1, and the round/guard/carry/sticky information selects the result. LZA operation overlaps the normalization shift, and exponent/shift processing overlaps multiplication or alignment. # p.2, p.4-p.7
choices:
  rounding_position: fused_with_cpa_dual_sum   # p.2, p.3
  normalize_before_add: true   # p.2, p.4, p.7
  add_skip_for_pure_addition: true   # p.2, p.5
new_choices:
  datapath_organization: close_far_double_datapath — CLOSE handles cancellation cases with bounded alignment/full normalization; FAR handles the remaining cases with full alignment/bounded normalization.   # p.4, p.6-p.7
slots:
  align: full_align   # p.4, p.6
  lza: lza   # p.3, p.5, p.7
  cpa: UNKNOWN [53-bit dual adder; topology unspecified]   # p.3, p.5
  round: compound_adder_select   # p.2, p.3, p.5
  multiplier: booth_recoded_parallel [booth_radix=UNKNOWN]   # p.5
parameters: IEEE double precision; 53-bit dual adder; 106-bit product inputs; CLOSE alignment up to 3 bits; FAR alignment up to 53 bits for E×F or 106 bits for D; 3-stage, 4-stage, or 5-stage pipelines; II UNKNOWN.   # p.2-p.3, p.6, p.9
results:
| metric | value | unit | technology / device | baseline | condition | page |
| latency | 2 | cycles | UNKNOWN; year 2005 | 3 cycles | fp-add in 3-stage proposed MAF | p.9 |
| latency | 3 | cycles | UNKNOWN; year 2005 | 5 cycles | fp-add in 5-stage proposed MAF | p.9 |
| latency | 2 | cycles | UNKNOWN; year 2005 | UNKNOWN | fp-add in 4-stage proposed MAF | p.9 |
| normalized delay | 0.9 | basic-MAF delay | UNKNOWN; year 2005 | basic MAF = 1 | proposed MAF/fp-multiply | p.9 |
| normalized delay | 0.6 | basic-MAF delay | UNKNOWN; year 2005 | basic MAF = 1 | fp-add in proposed MAF | p.9 |
| normalized delay | 0.8 | basic-MAF delay | UNKNOWN; year 2005 | basic MAF = 1 | single-datapath MAF with normalization before addition | p.9 |
| estimated delay | 175 | t_inv4 | UNKNOWN; year 2005 | none | basic single-datapath MAF | p.9 |
| estimated delay | 145 | t_inv4 | UNKNOWN; year 2005 | none | single-datapath MAF with normalization before addition | p.9 |
| alignment/normalization delay increment | 14 | t_inv4 | UNKNOWN; year 2005 | single-datapath MAF with normalization before addition | proposed double datapath | p.8 |
| MAF delay increase | around 10% | percent | UNKNOWN; year 2005 | single-datapath MAF with normalization before addition | proposed MAF | p.9 |
| fp-add delay reduction | around 40% | percent | UNKNOWN; year 2005 | basic MAF | proposed MAF | p.9 |
| fp-add delay reduction | around 30% | percent | UNKNOWN; year 2005 | single-datapath MAF with normalization before addition | proposed MAF | p.9 |
errors_and_checks: D+(E×F) is computed with no intermediate rounding and one final rounding; no numerical-error bound or checker is reported. Special and denormalized numbers are not discussed.   # p.1-p.2
conditions: The architecture targets IEEE double precision. Full alignment and full normalization must remain mutually exclusive so only one full-length shift lies on a path. Addition/multiplication/MAF pipeline collisions require an issue policy because the operations enter and leave different stages. The delay figures are estimates based on t_inv4 assumptions rather than measurements in a reported technology. Special and denormalized numbers are outside the description.   # p.2, p.4, p.8-p.9
evidence: Abstract; §1; Figures 1-3; §3; equations (1)-(6); Table 1; §4.4; §5.   # p.1-p.9

## new_families
none

## space_gaps
* reduced_latency_fma lacks a choice for the CLOSE/FAR double-datapath organization that separates full alignment from full normalization.   # p.4, p.7
* reduced_latency_fma lacks a choice for overlapping exponent/shift-count generation with multiplication or shifting.   # p.6
* The align slot cannot express the mixed bounded-alignment/full-alignment paths used by one FMA architecture.   # p.4, p.6

## open_questions
* The final dual-adder topology is unspecified, so the cpa slot must remain UNKNOWN.
* The multiplier recoding radix and reduction-tree details are unspecified.
* The implementation technology/device, area, power, cycle time, and initiation interval are not reported.
* Special-number and denormalized-number handling is not described.
