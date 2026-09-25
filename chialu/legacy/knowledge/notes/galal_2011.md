---
handle: galal_2011
citation: S. Galal, M. Horowitz, "Energy-Efficient Floating-Point Unit Design", IEEE Transactions on Computers, vol. 60, no. 7, 2011
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_DOT_ACC]
formats: [fp32, fp64]
authority: incremental
pages_read: 913-922 / 10
---

## summary
The paper presents a method for generating a power/throughput versus area/throughput trade-off curve for floating-point multiply-add units, and uses it to pick the throughput-optimal design under area, power and power-density constraints. Two multiply-add units are synthesized, placed and routed in 90 nm and 45 nm standard cells over a sweep of supply voltage, threshold voltage, clock period and pipeline depth: the fused multiply-add (FMA) and the cascade multiply-add (CMA). The study reports the resulting energy/op and GFlops/mm2 points, the cost of IEEE compliance, the register-file overhead, and how the curve shifts from 180 nm to 16 nm.

## families
### classic_fma  (role: instantiates)
mechanism: The FMA computes A + B x C by aligning the addend significand SA in parallel with the multiplication of SB and SC, which removes the conventional alignment step from the critical path. Because the addend exponent may be smaller or larger than the sum of the multiplicand exponents, SA can be shifted from all the way to the left of the multiplier result to all the way to the right, giving a 72-bit shifting operation for single precision. The adder and normalize stages are therefore around 72 bits wide for single precision. The design carries no speculative hardware for improving latency, so no energy is spent on precomputed results that are discarded.
choices: none
new_choices:
  pipeline_depth: 1..8 — number of pipeline stages, swept as a first-class optimization knob; even the lowest energy designs still use three or four stages, and 45 nm FMAs sit at three to six cycles   # p.916, p.920
  ieee_compliance: enum['truncation_only_no_denormals', 'all_rounding_modes_and_denormals'] — whether the unit implements the IEEE rounding modes and denormals   # p.914, p.917
slots:
  align: full_align   # p.914
parameters: single and double precision; ~72-bit shifter, adder and normalize datapath for single precision (p.914); 90 nm standard cells at Vdd 1-1.2 V and 45 nm standard cells at 0.8-1 V (p.916); pipeline depth, clock period, supply voltage and threshold voltage swept, circuit sizing set indirectly by frequency and pipeline depth (p.916); 10-cycle latency at the 3.2 GFlops single-precision point (p.917); three to six cycles at 45 nm (p.920).
results:
| metric | value | unit | technology / device | baseline | condition | page |
| throughput density | 27 | GFlops/mm2 | 90 nm CMOS (2011) | none | single precision, 1 W/mm2, FPUs only, no register or memory | p.913 |
| throughput density | 7.5 | GFlops/mm2 | 90 nm CMOS (2011) | none | double precision, 1 W/mm2 | p.913 |
| energy per Flop | 10 to 100 | pJ | 90 nm (2011) | none | single precision, efficient frontier of Fig. 3 | p.916 |
| area for 1 GFlops | 0.035 to 0.15 | mm2 | 90 nm (2011) | none | single precision, efficient frontier of Fig. 3 | p.916 |
| latency | ~60 | FO4 | UNKNOWN (2011) | none | single precision, cited for the Cell Processor FMA | p.914 |
| area efficiency eps_A | 0.036 | mm2/GFlops | 90 nm (2011) | none | single precision, 3.2 GFlops throughput | p.917 |
| power efficiency eps_P | 0.046 | W/GFlops | 90 nm (2011) | none | single precision, 3.2 GFlops throughput | p.917 |
| latency | 10 | cycles | 90 nm (2011) | cascade design at 12 cycles | same 3.2 GFlops single-precision point | p.917 |
| IEEE compliance overhead | 5 to 10 | percent | 90 nm (2011) | unit without denormals and with truncation rounding only | over the range of power densities | p.917 |
| double- over single-precision resources | ~3 | x | 90 nm (2011) | single-precision FMA | multiplier trees grow quadratically, rest of datapath linearly | p.917 |
| multiplier share of area and power | 31 to 45 | percent | 90 nm (2011) | single-precision design at 31 percent | double-precision design at 45 percent | p.917 |
| optimal design throughput | 1.67 | GFlops | 90 nm (2011) | none | Amax = 2 cm2, Pmax = 60 W, Dmax = 50 W/cm2 | p.917 |
| optimal design area | 0.09 | mm2 | 90 nm (2011) | none | same constraints, eps_A = 0.054 mm2/GFlops | p.917 |
| optimal design power | 27 | mW | 90 nm (2011) | none | same constraints, eps_P = 0.016 W/GFlops | p.917 |
| aggregate throughput | 3.7 | TFlops | 90 nm (2011) | none | 2,222 FPUs at 60 W and 2 cm2 | p.917 |
| scaling gain 90 nm to 45 nm | 7 | x | 45 nm (2011) | 90 nm design at the same power density | 1 W/mm2, steep part of the curve | p.918 |
| scaling gain 90 nm to 45 nm | 3.5 | x | 45 nm (2011) | 90 nm design at the same power density | 0.1 W/mm2, flatter part of the curve | p.918 |
| scaling gain 180 nm to 90 nm | 8 | x | 90 nm (2011) | 180 nm design | classic Dennard scaling, Matlab model with predictive transistor models | p.919 |
| scaling gain 45 nm to 22 nm | 2.7 | x | 22 nm projected (2011) | 45 nm 1 W/mm2 design | gate speed constant, start from 0.5 W/mm2 at 45 nm, ~1.5x area | p.919 |
| scaling gain 45 nm to 22 nm | 4 | x | 22 nm projected (2011) | 45 nm 1 W/mm2 design | gate speed scales, start from 0.25 W/mm2 at 45 nm, ~2x area | p.919 |
| scaling gain 45 nm to 22 nm | 3 | x | 22 nm projected (2011) | 45 nm 1 W/mm2 design | double precision, Fig. 10 estimated curves | p.919 |
| throughput density | ~40 | GFlops/mm2 | 45 nm (2011) | none | double precision at 1 W/mm2 | p.921 |
| energy per Flop | ~25 | pJ | 45 nm (2011) | none | double precision | p.921 |
| register file size | 512 and 1,024 | bytes | 45 nm (2011) | none | single and double precision, latencies of three to six cycles, 16 registers per thread | p.920 |
| register file energy and area overhead | ~25 | percent | 45 nm (2011) | FMA datapath alone | single precision | p.921 |
| register file energy and area overhead | ~20 | percent | 45 nm (2011) | FMA datapath alone | double precision | p.921 |
| area overhead with register file | under 30 | percent | 45 nm (2011) | FMA datapath alone | constant power density | p.921 |
| throughput loss from register file | under 50 | percent | 45 nm (2011) | FMA datapath alone | high compute intensity | p.913 |
| DRAM energy per double-precision word fetch | ~1 | nJ | GDDR5 (2010 datasheet) | none | high-performance graphics DRAM | p.921 |
| arithmetic intensity break-even | over 40 | Flops per double word load | 45 nm (2011) | none | memory not dominating the system | p.921 |
errors_and_checks: No ulp bound, error rate or fault model is reported. The designs explored first leave out IEEE denormals and support only truncation rounding, as done in many multimedia designs, and an IEEE-compliant implementation supporting all rounding modes and denormals is also built (p.914, p.917). Multiply-add instructions are stated to offer better accuracy than separate adders and multipliers (p.914).
conditions: The FMA has the shortest latency of any multiply-add design, and lower latency is a free feature at equal energy and area efficiency, which is why the rest of the study uses it (p.914, p.917). Proposed innovations that shorten FMA latency further carry large area and power overheads that are inappropriate when optimizing FLOPs/mm2 or FLOPs/W (p.914). Parallel alignment costs a very large variable shifter and a wide intermediate datapath (p.914). Deeply pipelined high-voltage high-frequency designs maximize ops/s/mm2 and shallow-pipelined low-frequency low-voltage designs maximize ops/s/W, while mixtures such as high Vdd with shallow pipelines were never efficient (p.916). Throughput requires as many interleaved threads as the pipeline depth (p.920). Below 32 nm and between 0.1 and 1 W/mm2, low-power technologies with higher EOT and longer Leff become the optimal technologies (p.920).
evidence: Sections 2.1, 3.1, 3.2, 3.3, 4, 5, 6; Figs. 1, 3, 4, 5, 6, 9, 10, 11, 12; Tables 1 and 2 (captions only in the extracted text).

### bridge_fma  (role: compares)
mechanism: The cascade multiply-add performs the multiply first and then aligns the operands for the FP adder. The partial products coming from the multipliers are combined using an adder before being fed to the aligner. The aligner swaps its two inputs based on which significand has the smaller exponent and then shifts it to align the numbers. The aligned results are added and normalized. The datapath width for the aligner, adder and normalizer is around 48 bits for single precision. The forwarding path for a dependent accumulate operation is shorter than the forwarding path through the multiplier, and shorter than the corresponding path in the FMA design.
choices:
  composition_style: cascade_mul_then_add   # p.914, p.915
new_choices:
  pipeline_depth: 1..12 — stages swept by the same flow; the cascade reaches the shared 3.2 GFlops point at 12 cycles   # p.917
slots:
  align: full_align   # p.915
parameters: single precision; ~48-bit aligner, adder and normalizer datapath (p.915); 12-cycle latency at the 3.2 GFlops point (p.917).
results:
| metric | value | unit | technology / device | baseline | condition | page |
| aligner/adder/normalizer datapath width | ~48 | bits | 90 nm (2011) | ~72 bits for the FMA | single precision | p.914, p.915 |
| area efficiency eps_A | 0.036 | mm2/GFlops | 90 nm (2011) | same value for the FMA | single precision, 3.2 GFlops throughput | p.917 |
| power efficiency eps_P | 0.046 | W/GFlops | 90 nm (2011) | same value for the FMA | single precision, 3.2 GFlops throughput | p.917 |
| latency | 12 | cycles | 90 nm (2011) | 10 cycles for the FMA | single precision, 3.2 GFlops throughput | p.917 |
errors_and_checks: none reported for the cascade design beyond the shared statement that the initial designs omit IEEE denormals and support only truncation rounding (p.917).
conditions: Some recent designs prefer the cascade over the FMA, especially in embedded graphics applications (p.915). The narrower datapath may make it better for throughput applications, at a longer overall latency (p.914). The shorter dependent-accumulate forwarding path can make the total latency of a dot product shorter than in an FMA design, which is stated as an argument in favor of the cascade for such calculations (p.915). Both designs have very similar power-area trade-offs, so the cascade is dropped from the rest of the study because its latency is longer at equal efficiency (p.917).
evidence: Sections 2.2, 3.2; Figs. 2 and 5.

## new_families
none

## space_gaps
* A support level for IEEE denormals and the rounding-mode set is missing from `classic_fma` and `bridge_fma`, although the document measures its cost at 5-10 percent; `tensor_core_mixed_precision_mac` has `subnormal_support` and `fp8_training_datapath` has `flush_subnormals`, so the choice exists elsewhere in the same section.   # p.914, p.917
* No family in the `dot` section carries a pipeline-depth or cycle-latency choice, although the document treats pipeline depth as a first-order microarchitectural parameter that sets both the energy/op and the thread count needed for full throughput.   # p.916, p.920
* The `bridge_fma` value `cascade_mul_then_add` covers a natively cascaded multiplier-then-adder unit, while the family's description frames the mechanism as a retrofit that bridges existing separate units; the two are different design intents under one value.   # p.914, p.915

## open_questions
* Tables 1 and 2 and the data inside Figs. 3 to 12 are images in the extracted text, so the per-point frontier data (the 90 nm and 45 nm scaling summary, and the 45 nm double-precision FMA design parameters with register file) is not available from this document text.
* The multiplier slot family is not identified: the document says only "multiplier trees" whose area and power grow quadratically with operand size (p.917), without naming a recoding or reduction scheme.
* Whether the IEEE-compliant unit shown in Fig. 5 is the fused or the cascade design is not stated (p.917).
* The adder, normalizer, leading-zero and rounding structures inside either unit are shown only in the Fig. 1 and Fig. 2 block diagrams, which the extracted text does not carry, so their families stay unassigned.
