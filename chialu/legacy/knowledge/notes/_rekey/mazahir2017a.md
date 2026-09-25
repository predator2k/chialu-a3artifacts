---
handle: mazahir2017a
citation: S. Mazahir, O. Hasan, R. Hafiz, M. Shafique, J. Henkel, "Probabilistic Error Modeling for Approximate Adders", IEEE Transactions on Computers, vol. 66, no. 3, pp. 515-530, 2017
actual_citation: S. Mazahir, O. Hasan, R. Hafiz, M. Shafique, "Probabilistic Error Analysis of Approximate Recursive Multipliers", IEEE Transactions on Computers, 2017
status: mismatch
kind: paper
unit_classes: [BINARY_ALU]
formats: [unsigned_int, signed_int, Q0.12]
authority: incremental
pages_read: 8 / 8
---

## summary
The document presents probabilistic error-rate and error-PMF analysis for recursive approximate multipliers assembled from smaller approximate multiplier blocks. The analysis supports arbitrary widths/input distributions and extensions for signed multiplication, squaring, constant multiplication, and hybrid precise/approximate structures. Validation compares analytical results with exhaustive or Monte-Carlo simulation for eleven multiplier designs.

## families
### error_analysis_quality  (role: proposes)
mechanism: The method derives the building-block error probability ρM and conditional error PMF from an M × M truth table. Inclusion-exclusion then computes the probability that at least one M-bit component of each operand satisfies the error condition Θ. Algorithm 1 enumerates mutually exclusive operand-component conditions and weighted partial-product errors to obtain the product-error PMF. Input PMFs supply component probabilities for nonuniform operands, while convolution estimates combined errors when partial-product errors are interdependent. # pp.3–5
choices:
  metric: er   # pp.3–4
  model: analytical_pmf   # pp.4–5
  composition_across_blocks: true   # pp.4–5
new_choices:
  input_distribution: uniform | arbitrary_PMF — selects closed-form or PMF-derived component probabilities   # pp.4–5
  error_value_method: exact_enumeration | convolution_estimate — distinguishes Algorithm 1 Case I from Case II   # p.5
slots:
  none
parameters: arbitrary N × N multiplier; M × M blocks; N=2^kM or N=kM; evaluated M=2 and M=4; 8×8, 12×12, and 16×16 examples   # pp.2–7
results:
| metric | value | unit | technology / device | baseline | condition | page |
| ER / MED | 0.6757 / 2.33 × 10^5 | dimensionless / product distance | UNKNOWN; year UNKNOWN | MC: 0.6611 / 2.37 × 10^5 | Kulkarni 12×12, uniform | p.6 |
| ER / MED | 0.5365 / 1.71 × 10^4 | dimensionless / product distance | UNKNOWN; year UNKNOWN | MC: 0.5381 / 1.70 × 10^4 | Kulkarni 12×12, geometric p=0.001 | p.6 |
| ER / MED | 0.3924 / 647.6 | dimensionless / product distance | UNKNOWN; year UNKNOWN | MC: 0.3929 / 643.7 | Kulkarni 12×12, geometric p=0.005 | p.6 |
| ER / MED | 0.6121 / 2.05 × 10^4 | dimensionless / product distance | UNKNOWN; year UNKNOWN | MC: 0.6077 / 1.99 × 10^4 | Kulkarni 12×12, Gaussian μ=2040, σ=295.6 | p.6 |
| ER / MED | 0.8789 / 1806 | dimensionless / product distance | UNKNOWN; year UNKNOWN | MC: 0.8472 / 1601 | Shafique 8×8, uniform | p.6 |
| ER / MED | 0.8374 / 1149.5 | dimensionless / product distance | UNKNOWN; year UNKNOWN | MC: 0.8111 / 1097 | Shafique 8×8, geometric p=0.008 | p.6 |
| ER / MED | 0.9159 / 2682 | dimensionless / product distance | UNKNOWN; year UNKNOWN | MC: 0.8975 / 2713 | Shafique 8×8, Gaussian μ=126, σ=37 | p.6 |
| ER / MED | 0.4673 / 1806 | dimensionless / product distance | UNKNOWN; year UNKNOWN | MC: 0.4647 / 1810 | ApproxMul4 8×8, uniform | p.6 |
| ER / MED | 0.3462 / 464 | dimensionless / product distance | UNKNOWN; year UNKNOWN | MC: 0.3462 / 471 | ApproxMul4 8×8, geometric p=0.008 | p.6 |
| ER / MED | 0.3915 / 174 | dimensionless / product distance | UNKNOWN; year UNKNOWN | MC: 0.3882 / 172 | ApproxMul4 8×8, Gaussian μ=126, σ=37 | p.6 |
| ER / MED | 0.8098 / 2.39 × 10^8 | dimensionless / product distance | UNKNOWN; year UNKNOWN | MC: 0.8101 / 2.41 × 10^8 | ApproxMul5/3 16×16, uniform | p.6 |
| ER / MED | 0.6960 / 6.45 × 10^6 | dimensionless / product distance | UNKNOWN; year UNKNOWN | MC: 0.7001 / 6.41 × 10^6 | ApproxMul5/3 16×16, geometric p=0.0001 | p.6 |
| ER / MED | 0.7693 / 2.08 × 10^7 | dimensionless / product distance | UNKNOWN; year UNKNOWN | MC: 0.7645 / 2.10 × 10^7 | ApproxMul5/3 16×16, Gaussian μ=32760, σ=4729 | p.6 |
| ER / MED | 0.052 / 1.19 × 10^6 | dimensionless / product distance | UNKNOWN; year UNKNOWN | MC: 0.052 / 1.24 × 10^6 | HAC1/Lin 16×16, uniform | p.6 |
| ER / MED | 0.0276 / 4.69 × 10^3 | dimensionless / product distance | UNKNOWN; year UNKNOWN | MC: 0.0268 / 4.78 × 10^3 | HAC1/Lin 16×16, geometric p=0.0001 | p.6 |
| ER / MED | 0.0310 / 4.67 × 10^3 | dimensionless / product distance | UNKNOWN; year UNKNOWN | MC: 0.0306 / 4.81 × 10^3 | HAC1/Lin 16×16, Gaussian μ=32760, σ=4729 | p.6 |
| ER / MED | 0.052 / 2.38 × 10^6 | dimensionless / product distance | UNKNOWN; year UNKNOWN | MC: 0.0519 / 2.36 × 10^6 | HAC2 16×16, uniform | p.6 |
| ER / MED | 0.7385 / 863 | dimensionless / product distance | UNKNOWN; year UNKNOWN | MC: 0.7710 / 882 | MAC1 8×8, uniform | p.6 |
| ER / MED | 0.7385 / 863 | dimensionless / product distance | UNKNOWN; year UNKNOWN | MC: 0.7575 / 879 | MAC2 8×8, uniform | p.6 |
| ER / MED | 0.7385 / 863 | dimensionless / product distance | UNKNOWN; year UNKNOWN | MC: 0.7575 / 886 | Momeni 8×8, uniform | p.6 |
| ER / MED | 0.6982 / 447.8 | dimensionless / product distance | UNKNOWN; year UNKNOWN | MC: 0.7059 / 459 | Momeni 8×8, Gaussian μ=126, σ=37 | p.6 |
errors_and_checks: ER is Pr[A∗B ≠ A×B]; MED is derived from the error PMF. Algorithm 1 gives an exact PMF when the Section 4.1 assumptions and single building-block error value hold; otherwise it estimates the PMF. Cancellation probability κ is taken as 0 for the studied designs.   # pp.2–7
conditions: A and B are independent; component blocks are identical; block error occurrence is symmetric in both inputs; partial-product addition is precise. The Θ abstraction is exact for Kulkarni/Rehman/Lin designs and approximate for Shafique/Momeni designs. Nonuniform component events are approximated as independent, and convolution ignores partial-product interdependence.   # pp.2–7
evidence: §§4.1–4.6, Algorithm 1, Table 1, Figs. 7–10

### pp_perforation  (role: analyzes)
mechanism: An N × N product is partitioned into M-bit operand components. Every component pair is multiplied by an M × M approximate block, shifted by its component position, and accumulated with precise adders. Evaluated blocks include approximate 2 × 2 multipliers and 4 × 4 multipliers containing approximate 4:2 compressors. Hybrid variants replace selected high-significance blocks with precise multipliers, and signed variants retain approximate blocks only where signed/unsigned partial-product logic matches.   # pp.2,5–7
choices:
  cell: kulkarni_2x2_inaccurate   # pp.2,6
new_choices:
  building_block_width: {2, 4} — width M of each recursively tiled approximate multiplier   # pp.2,6
  accumulation_accuracy: {precise, approximate_hybrid} — whether the partial-product tree also contains approximate adders/compressors   # pp.2,5
  block_precision_map: {all_approximate, mixed_precise_approximate} — selects precise blocks by partial-product significance or signed logic   # pp.5,7
slots:
  none
parameters: N=2^kM or N=kM; M=2 or 4 in validation; arbitrary N in the analysis   # pp.2–6
results:
| metric | value | unit | technology / device | baseline | condition | page |
| building-block ER / error value | 1/16 / 2 | probability / product value | UNKNOWN; year UNKNOWN | exact truth table | Kulkarni 2×2 | p.6 |
| building-block ER / error value | 3/16 / 1 | probability / product value | UNKNOWN; year UNKNOWN | exact truth table | Shafique 2×2 | p.6 |
| building-block ER / error value | 1/256 / 16 | probability / product value | UNKNOWN; year UNKNOWN | exact truth table | Lin 4×4 | p.6 |
| building-block ER / error value | 100/256 / ±8 | probability / product value | UNKNOWN; year UNKNOWN | exact truth table | Momeni 4×4 | p.6 |
errors_and_checks: Approximation error is characterized by ER, error magnitude, MED, and the complete PMF; no hardware checker is proposed.   # pp.3–8
conditions: The direct analysis targets Type A recursive multipliers with approximate partial products and precise accumulation. Hybrid approximate accumulation requires convolution with a separate adder-tree error PMF.   # pp.2,5
evidence: Figs. 1–6, §§2–3, §4.6, §5.1

## new_families
none

## space_gaps
* error_analysis_quality.metric lacks PMF/MSE/average NED/PSNR values used to characterize multiplier and application error.   # pp.4–5,8
* pp_perforation lacks building-block width/recursive tiling choices for structures assembled from M × M approximate products.   # pp.2–4
* pp_perforation lacks a reduction-tree slot that distinguishes precise accumulation from hybrid approximate-adder/compressor accumulation.   # pp.2,5

## open_questions
* The accepted manuscript does not state final volume/issue/page metadata for the actual article.
* The merge pass must not treat the Θ model or PMF as exact for Shafique/Momeni designs, because the document reports approximation from neglected error cases/interdependencies.   # pp.3,7
