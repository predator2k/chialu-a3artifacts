---
handle: detrey_2005
citation: J. Detrey, F. de Dinechin, "Table-Based Polynomials for Fast Hardware Function Evaluation", IEEE International Conference on Application-Specific Systems, Architectures and Processors (ASAP), pp. 328-333, 2005
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_SFU]
formats: [fixed_point]
authority: incremental
pages_read: 6 / 6
---

## summary
The paper generalizes table-based piecewise-polynomial function evaluation to arbitrary degree using parallel monomials implemented by ROMs or power-and-multiply units. FPGA experiments compare degree-2/3/4 implementations of sin x and log2(1+x) for 12-32-bit input/output precision.

## families
### piecewise_poly  (role: extends)
mechanism: The input interval is split uniformly into subintervals selected by the α most significant input bits, and each subinterval receives a minimax polynomial. The developed polynomial form evaluates every term Tk(A,B) in parallel before a final summation. Individual terms use either a simple ROM or a power-and-multiply unit whose powering stage is table-based or an ad-hoc partial-product circuit. Per-term address/output widths are reduced under an explicit error budget, and midpoint symmetry reduces table inputs without additional error. # pp.329-331
choices:
  degree: 2, 3, or 4   # p.332
  basis: minimax_remez   # p.329
  rounding_contract: faithful   # pp.329,331-332
new_choices:
  term_realization: {simple_rom, power_and_multiply} — selects the implementation of each polynomial term   # pp.329-331
  powering_unit: {table_based, ad_hoc_partial_product} — selects how B^k is generated   # pp.330-331
  symmetry_exploitation: Bool — folds each subinterval around its midpoint using XOR gates   # pp.330-331
  per_term_precision_tuning: Bool — permits separate αk/βk/λk/μk precision parameters for each term   # pp.330-331
slots:
  evaluator: parallel_monomial   # pp.329,331
  segmenter: uniform_high_bit_decode   # p.329
parameters: wI and wO specify binary fractional input/output widths; experiments use wI=wO at 12, 16, 20, 24, 28, and 32 bits; degrees 2, 3, and 4 are implemented; α selects 2^α uniform subintervals; g guard bits are chosen by error analysis; implementations are combinational   # pp.329,331-333
results:
| metric | value | unit | technology / device | baseline | condition | page |
| approximation order judged optimal | 2 | order | Xilinx Virtex-II XC2V-1000-4 FPGA; 2005 | degrees 3/4 | precision up to 16 bits | p.333 |
| approximation order judged optimal | 3 | order | Xilinx Virtex-II XC2V-1000-4 FPGA; 2005 | degrees 2/4 | 24-bit precision | p.333 |
| operator area difference | 30 | % smaller | Xilinx Virtex-II XC2V-1000-4 FPGA; 2005 | the other of degree 3/4 | 32-bit precision; the prose does not identify which degree is smaller | p.333 |
errors_and_checks: The contract is faithful rounding with ε=maxX∈I|f(X)-f̃(X)|<2^-wO. The analysis requires εpoly+εmethod+εrt+εrf<εmax, where εmethod=εtab+εpow. Tables/multipliers retain g guard bits, and trial and error selects the smallest acceptable g. # pp.329,331-332
conditions: The method applies to elementary or compound functions satisfying basic continuity requirements. # p.328 The reported experiments cover sin x on [0,π/4) and log2(1+x) on [0,1). # p.332 The synthesis excludes the Virtex-II 18×18 hard multipliers to improve comparison with earlier work. # p.332 Degree 4 provides an area/speed tradeoff rather than a uniform improvement over degree 3 at 32-bit precision. # p.333 ASIC synthesis is not evaluated because its table/arithmetic metrics differ from FPGA metrics. # pp.329,333
evidence: §§2.2-2.4, §§3.1-3.3, §§4.1-4.4, §§5.1-5.4, Fig. 1, Fig. 2, §6, §7

## new_families
none

## space_gaps
* `piecewise_poly` lacks a term-realization choice or component slot for mixing simple ROM and power-and-multiply terms within one evaluator. # pp.329-331
* `piecewise_poly` lacks a choice for midpoint-symmetry folding of polynomial terms. # pp.330-331
* `piecewise_poly` lacks per-term address/power/output precision choices corresponding to αk, βk, λk, and μk. # pp.330-331

## open_questions
* Figure 2 provides curves rather than numeric tables, so exact slice counts and delays cannot be recovered from the document text.
* The document does not tabulate α, β, αk, βk, λk, μk, mk, mk:M, or g for each synthesized point.
* The conclusion does not identify which of degree 3 or degree 4 is 30% smaller at 32-bit precision; it states only that the other design is faster.
