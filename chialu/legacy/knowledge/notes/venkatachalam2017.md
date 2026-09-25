---
handle: venkatachalam2017
citation: S. Venkatachalam, S.-B. Ko, "Design of Power and Area Efficient Approximate Multipliers", IEEE Transactions on VLSI Systems, vol. 25, no. 5, pp. 1782-1786, 2017
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [uint16]
authority: incremental
pages_read: 5 / 5
---

## summary
The paper proposes probability-guided alteration and approximate reduction of partial products for 16-bit multipliers. Two variants trade accuracy for area/power by approximating either all columns or the 15 least significant columns. # p.1, p.3

## families
### approximate_compressor_tree  (role: proposes)
mechanism: Paired partial products am,n and an,m are replaced by propagate pm,n = am,n + an,m and generate gm,n = am,n · an,m terms with probabilities 7/16 and 1/16. Generate terms are reduced in groups of at most four using OR gates. The remaining matrix is reduced with proposed approximate half-adders/full-adders/4-2 compressors whose local arithmetic error difference is limited to one, followed by a ripple-carry vector merge adder. # p.2–3
choices:
  approximate_columns: {all, 15 least significant} [outside domain]   # p.3
  compressor: venkatachalam_pp_alter   # p.2–3
new_choices:
  partial_product_transform: propagate_generate_pairing — paired partial products become pm,n and gm,n before reduction   # p.2
  generate_reduction_group_limit: 4 — at most four generate signals are combined by each OR gate   # p.2
  approximate_cell_set: {half_adder, full_adder, 4_2_compressor} — cell types used to reduce non-generate terms   # p.2–3
slots:
  cpa: ripple_carry   # p.3
parameters: 16-bit multipliers; Multiplier1 approximates all columns; Multiplier2 approximates the 15 least significant columns; Verilog implementation; the 8-bit illustrative matrix uses two reduction stages   # p.3
results:
| metric | value | unit | technology / device | baseline | condition | page |
| power savings | 72% | power savings | TSMC 65 nm standard cell library / 2017 | exact 16-bit Dadda multiplier | Multiplier1 | p.1 |
| power savings | 38% | power savings | TSMC 65 nm standard cell library / 2017 | exact 16-bit Dadda multiplier | Multiplier2 | p.1 |
| area savings | 32% | area savings | TSMC 65 nm standard cell library / 2017 | exact 16-bit Dadda multiplier | Multiplier2 | p.4 |
| APP savings | 87% | APP savings | TSMC 65 nm standard cell library / 2017 | exact 16-bit Dadda multiplier | Multiplier1 | p.4–5 |
| APP savings | 58% | APP savings | TSMC 65 nm standard cell library / 2017 | exact 16-bit Dadda multiplier | Multiplier2 | p.4–5 |
| MRE | 7.6% | mean relative error | TSMC 65 nm standard cell library / 2017 | exact multiplication | Multiplier1 | p.1 |
| MRE | 0.02% | mean relative error | TSMC 65 nm standard cell library / 2017 | exact multiplication | Multiplier2 | p.1 |
| NED reduction | 64% lower | normalized error distance | TSMC 65 nm standard cell library / 2017 | ACM1 | Multiplier1 | p.3 |
| MRE reduction | three orders of magnitude lower | mean relative error | TSMC 65 nm standard cell library / 2017 | ACM1 | Multiplier1 | p.3 |
| MRE reduction | one order lower | mean relative error | TSMC 65 nm standard cell library / 2017 | ACM2 | Multiplier2 | p.4 |
| MRE reduction | two orders lower | mean relative error | TSMC 65 nm standard cell library / 2017 | UDM | Multiplier2 | p.4 |
| MRE reduction | 73% lower | mean relative error | TSMC 65 nm standard cell library / 2017 | PPP | Multiplier2 | p.4 |
| MRE reduction | 62% lower | mean relative error | TSMC 65 nm standard cell library / 2017 | SSM | Multiplier2 | p.4 |
| NED difference | 10% higher | normalized error distance | TSMC 65 nm standard cell library / 2017 | ACM2 | Multiplier2 | p.4 |
errors_and_checks: Each proposed approximate half-adder/full-adder/4-2-compressor maintains an absolute local output difference of one for erroneous cases. Exhaustive MATLAB analysis reports ED/NED/MRE for the 16-bit designs; no runtime error detection or correction is provided. # p.2–3
conditions: The design targets error-tolerant multimedia/data-mining applications. Multiplier1 targets higher power savings with greater error tolerance, while Multiplier2 targets moderate savings and lower MRE. Multiplier2 has low MRE at larger products because exact units remain in the most significant portion. The technique can be applied to signed and Booth multipliers except at sign-extension bits. # p.1, p.4
evidence: §II and Fig. 1 define the altered partial products; Tables I–IV and Fig. 2 define the probability-guided reduction/cells; §II-C defines the variants; §III and Tables V–VII report implementation/error comparisons; §IV and Figs. 4–5 report the image-processing evaluation. # p.2–4

## new_families
none

## space_gaps
* approximate_columns does not represent the paper's `all columns` variant or its odd-valued `15 least significant columns` variant. # p.3
* approximate_compressor_tree lacks choices for propagate/generate partial-product alteration, OR-group size, and approximate half-adder/full-adder participation. # p.2–3

## open_questions
* The supplied document text does not expose the numeric cells of Tables V and VI, so their absolute area/delay/power/PDP/APP/NED/MRE values remain UNKNOWN.
* The paper states that the method applies to signed/Booth multiplication except for sign-extension bits, but the reported 16-bit synthesis results do not identify a signed implementation. # p.1, p.3
