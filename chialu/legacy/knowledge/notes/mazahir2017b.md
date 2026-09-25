---
handle: mazahir2017b
citation: S. Mazahir, O. Hasan, R. Hafiz, M. Shafique, "Probabilistic Error Analysis of Approximate Recursive Multipliers", IEEE Transactions on Computers, vol. 66, no. 11, pp. 1982-1990, 2017
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [unsigned_int, signed_int, Q0.12]
authority: incremental
pages_read: 1982-1990 / 9
---

## summary
The paper derives error probability and error Probability Mass Function (PMF) models for arbitrary-width recursive approximate multipliers assembled from smaller approximate multiplier blocks. The models support general input distributions and extensions to hybrid/signed multipliers, squarers, constant multipliers, and approximate adder trees. Validation against exhaustive/Monte-Carlo simulation and image blending shows exact agreement for some compatible designs and close estimates for others. # pp.1982-1990

## families
### error_analysis_quality  (role: proposes)
mechanism: The analysis derives an arbitrary-width multiplier’s error probability from the error behavior of its M × M building block and the input PMFs. Inclusion-exclusion combines the conditions under which operand blocks belong to the error-triggering set Q. Algorithm 1 enumerates factor conditions and weighted partial-product errors to compute an exact PMF for single-error-value blocks satisfying the architectural assumptions. Conditional error PMFs and convolution estimate designs with multiple block-error values. # pp.1984-1986
choices:
  metric: {er, med, nmed, mse [outside domain], psnr [outside domain]}   # pp.1987-1989
  model: analytical_pmf   # pp.1985-1986
  composition_across_blocks: true   # pp.1984-1986
new_choices:
  input_distribution: {uniform, geometric, Gaussian, arbitrary_PMF} — input statistics used by the error analysis   # pp.1985,1987-1989
  block_error_model: {single_error_value, conditional_error_PMF} — whether an M × M block has one or multiple nonzero error values   # p.1986
slots:
  none
parameters: N × N multiplier; M × M building blocks; N = kM; evaluated M = 2 and M = 4; exhaustive simulation for small widths and Monte-Carlo simulation for larger widths   # pp.1983,1985,1987
results:
| metric | value | unit | technology / device | baseline | condition | page |
| ER analysis/MC; MED analysis/MC | 0.6757/0.6611; 2.33 × 10^5/2.37 × 10^5 | UNKNOWN | UNKNOWN / 2017 | MC simulation | Kulkarni 12 × 12, uniform | p.1988 |
| ER analysis/MC; MED analysis/MC | 0.5365/0.5381; 1.71 × 10^4/1.70 × 10^4 | UNKNOWN | UNKNOWN / 2017 | MC simulation | Kulkarni 12 × 12, geometric p = 0.001 | p.1988 |
| ER analysis/MC; MED analysis/MC | 0.3924/0.3929; 647.6/643.7 | UNKNOWN | UNKNOWN / 2017 | MC simulation | Kulkarni 12 × 12, geometric p = 0.005 | p.1988 |
| ER analysis/MC; MED analysis/MC | 0.6121/0.6077; 2.05 × 10^4/1.99 × 10^4 | UNKNOWN | UNKNOWN / 2017 | MC simulation | Kulkarni 12 × 12, Gaussian m = 2040, s = 295.6 | p.1988 |
| ER analysis/MC; MED analysis/MC | 0.8789/0.8472; 1806/1601 | UNKNOWN | UNKNOWN / 2017 | MC simulation | Shafique 8 × 8, uniform | p.1988 |
| ER analysis/MC; MED analysis/MC | 0.8374/0.8111; 1149.5/1097 | UNKNOWN | UNKNOWN / 2017 | MC simulation | Shafique 8 × 8, geometric p = 0.008 | p.1988 |
| ER analysis/MC; MED analysis/MC | 0.9159/0.8975; 2682/2713 | UNKNOWN | UNKNOWN / 2017 | MC simulation | Shafique 8 × 8, Gaussian m = 126, s = 37 | p.1988 |
| ER analysis/MC; MED analysis/MC | 0.4673/0.4647; 1806/1810 | UNKNOWN | UNKNOWN / 2017 | MC simulation | ApproxMul4 8 × 8, uniform | p.1988 |
| ER analysis/MC; MED analysis/MC | 0.3462/0.3462; 464/471 | UNKNOWN | UNKNOWN / 2017 | MC simulation | ApproxMul4 8 × 8, geometric p = 0.008 | p.1988 |
| ER analysis/MC; MED analysis/MC | 0.3915/0.3882; 174/172 | UNKNOWN | UNKNOWN / 2017 | MC simulation | ApproxMul4 8 × 8, Gaussian m = 126, s = 37 | p.1988 |
| ER analysis/MC; MED analysis/MC | 0.8098/0.8101; 2.39 × 10^8/2.41 × 8 | UNKNOWN | UNKNOWN / 2017 | MC simulation | ApproxMul5/3 16 × 16, uniform | p.1988 |
| ER analysis/MC; MED analysis/MC | 0.6960/0.7001; 6.45 × 10^6/6.41 × 10^6 | UNKNOWN | UNKNOWN / 2017 | MC simulation | ApproxMul5/3 16 × 16, geometric p = 0.0001 | p.1988 |
| ER analysis/MC; MED analysis/MC | 0.7693/0.7645; 2.08 × 10^7/2.10 × 10^7 | UNKNOWN | UNKNOWN / 2017 | MC simulation | ApproxMul5/3 16 × 16, Gaussian m = 32760, s = 4729 | p.1988 |
| ER analysis/MC; MED analysis/MC | 0.052/0.052; 1.19 × 10^6/1.24 × 10^6 | UNKNOWN | UNKNOWN / 2017 | MC simulation | HAC1/Lin 16 × 16, uniform | p.1988 |
| ER analysis/MC; MED analysis/MC | 0.0276/0.0268; 4.69 × 10^3/4.78 × 10^3 | UNKNOWN | UNKNOWN / 2017 | MC simulation | HAC1/Lin 16 × 16, geometric p = 0.0001 | p.1988 |
| ER analysis/MC; MED analysis/MC | 0.0310/0.0306; 4.67 × 10^3/4.81 × 10^3 | UNKNOWN | UNKNOWN / 2017 | MC simulation | HAC1/Lin 16 × 16, Gaussian m = 32760, s = 4729 | p.1988 |
| ER analysis/MC; MED analysis/MC | 0.052/0.0519; 2.38 × 10^6/2.36 × 10^6 | UNKNOWN | UNKNOWN / 2017 | MC simulation | HAC2 16 × 16, uniform | p.1988 |
| ER analysis/MC; MED analysis/MC | 0.0276/0.0279; 9.38 × 10^3/9.31 × 10^3 | UNKNOWN | UNKNOWN / 2017 | MC simulation | HAC2 16 × 16, geometric p = 0.0001 | p.1988 |
| ER analysis/MC; MED analysis/MC | 0.7385/0.7710; 863/882 | UNKNOWN | UNKNOWN / 2017 | MC simulation | MAC1 8 × 8, uniform | p.1988 |
| ER analysis/MC; MED analysis/MC | 0.8399/0.8631; 1038/1201 | UNKNOWN | UNKNOWN / 2017 | MC simulation | MAC1 8 × 8, geometric p = 0.008 | p.1988 |
| ER analysis/MC; MED analysis/MC | 0.7385/0.7575; 863/879 | UNKNOWN | UNKNOWN / 2017 | MC simulation | MAC2 8 × 8, uniform | p.1988 |
| ER analysis/MC; MED analysis/MC | 0.8399/0.8528; 1037/1100 | UNKNOWN | UNKNOWN / 2017 | MC simulation | MAC2 8 × 8, geometric p = 0.008 | p.1988 |
| ER analysis/MC; MED analysis/MC | 0.7385/0.7575; 863/886 | UNKNOWN | UNKNOWN / 2017 | MC simulation | Momeni 8 × 8, uniform | p.1988 |
| ER analysis/MC; MED analysis/MC | 0.8399/0.8585; 1037/1047 | UNKNOWN | UNKNOWN / 2017 | MC simulation | Momeni 8 × 8, geometric p = 0.008 | p.1988 |
| ER analysis/MC; MED analysis/MC | 0.6982/0.7059; 447.8/459 | UNKNOWN | UNKNOWN / 2017 | MC simulation | Momeni 8 × 8, Gaussian m = 126, s = 37 | p.1988 |
| ER; MED; Avg. NED; MSE; PSNR, analysis/image | 0.676/0.577; 1.38/1.81; 6.3/8.7; 1.51/1.67; 28.2/27.8 | UNKNOWN; × 10^-2; × 10^-2; × 10^-3; dB | UNKNOWN / 2017 | image result | Kulkarni 8 × 8, Q0.12 image blending | p.1989 |
| ER; MED; Avg. NED; MSE; PSNR, analysis/image | 0.935/0.840; 2.08/2.16; 18.75/18.91; 1.38/1.35; 28.6/28.7 | UNKNOWN; × 10^-2; × 10^-2; × 10^-3; dB | UNKNOWN / 2017 | image result | Shafique 8 × 8, Q0.12 image blending | p.1989 |
| ER; MED; Avg. NED; MSE; PSNR, analysis/image | 0.031/0.005; 0.028/0.013; 0.40/0.18; 0.016/0.006; 48.06/52.58 | UNKNOWN; × 10^-2; × 10^-2; × 10^-3; dB | UNKNOWN / 2017 | image result | Lin 8 × 8, Q0.12 image blending | p.1989 |
| ER; MED; Avg. NED; MSE; PSNR, analysis/image | 0.897/1; 1.33/1.03; 35.78/29.98; 0.419/0.366; 33.7/34.36 | UNKNOWN; × 10^-2; × 10^-2; × 10^-3; dB | UNKNOWN / 2017 | image result | Momeni 8 × 8, Q0.12 image blending | p.1989 |
errors_and_checks: Algorithm 1 gives an exact PMF when the Section 4.1 assumptions hold and the building block has one possible error value. Other designs receive an estimated PMF; convolution neglects partial-product dependence, and infrequent error values may receive zero estimated probability. # pp.1986,1988
conditions: Inputs A/B are independent; all partial products use identical approximate multiplier blocks; and block-error occurrence is symmetric in the two operands. Nonuniform-input analysis approximates block-membership events as independent. Kulkarni/Lin satisfy the model exactly, while Shafique/Momeni only approximately satisfy it. # pp.1984-1985,1988
evidence: §§3-4; Algorithm 1; Table 1; Figs. 7-10; Table 2

### pp_perforation  (role: analyzes)
mechanism: An N × N multiplier is recursively constructed from M × M approximate multiplier units. Every operand block is multiplied by every block of the other operand, producing (N/M)^2 approximate partial products. Precise additions combine the partial products, so the partial-product errors add and the precise tree structure does not affect error statistics. Evaluated units include approximate 2 × 2 multipliers and 4 × 4 units built with approximate 4:2 compressors. # pp.1983,1987
choices:
  perforated_rows: 0   # p.1983
  cell: {kulkarni_2x2_inaccurate, Shafique_2x2 [outside domain], Rehman_ApproxMul3_ApproxMul4_ApproxMul5 [outside domain]}   # pp.1984,1987
new_choices:
  building_block_width: {2, 4} — width M of the approximate multiplier used to generate block partial products   # pp.1983,1987
  partial_product_accumulation: {precise, hybrid_approximate_tree} — accuracy of the adders/compressors combining block products   # pp.1983,1986
slots:
  cpa: UNKNOWN   # p.1983
parameters: N × N; N = 2^kM or general N = kM; M = 2 or 4 in evaluation; precise/approximate blocks may be mixed by position   # pp.1983,1985-1986
results:
| metric | value | unit | technology / device | baseline | condition | page |
| architecture coverage | eleven | multipliers | UNKNOWN / 2017 | exhaustive or MC simulation | evaluated recursive designs | pp.1987-1988 |
errors_and_checks: Approximation error is characterized by ER and an error PMF; exactness depends on whether the building-block truth table satisfies the set-Q model. # pp.1984,1986
conditions: More-significant partial products may use precise blocks to reduce ER and maximum error. Signed multiplication reuses approximate unsigned blocks where the signed/unsigned partial-product logic agrees and uses precise or specially designed blocks elsewhere. # pp.1986,1989
evidence: Figs. 1-6 and 10; §§2-5

### approximate_compressor_tree  (role: analyzes)
mechanism: A 4 × 4 approximate multiplier building block uses an approximate 4:2 compressor and then serves as a partial-product generator in a larger recursive multiplier. A broader hybrid may combine approximate block products with approximate full adders or compressors in a Wallace tree. The two error PMFs may be convolved because the paper treats block-generation and tree approximations as independent. # pp.1983,1986-1987
choices:
  compressor: {momeni_d1_d2, Lin_4_2 [outside domain], HAC1 [outside domain], HAC2 [outside domain], MAC1 [outside domain], MAC2 [outside domain]}   # pp.1987-1988
new_choices:
  none
slots:
  cpa: UNKNOWN   # pp.1983,1986
parameters: 4 × 4 building blocks; evaluated larger widths 8 × 8, 12 × 12, and 16 × 16   # pp.1987-1988
results:
| metric | value | unit | technology / device | baseline | condition | page |
| base error probability rM | 1/256 | UNKNOWN | UNKNOWN / 2017 | truth table | Lin, M = 4 | p.1988 |
| base error probability rM | 100/256 | UNKNOWN | UNKNOWN / 2017 | truth table | Momeni, M = 4 | p.1988 |
errors_and_checks: The convolution-based PMF is approximate because it ignores dependence among partial products. # pp.1986,1988
conditions: The extension requires the bit distributions presented to approximate full adders to be derived from the M × M block truth table and the operand distributions. # p.1986
evidence: Fig. 6; §4.6.1; Table 1; Figs. 8-9

## new_families
none

## space_gaps
* `pp_perforation` lacks a `building_block_width` choice covering the document’s recursive 2 × 2 and 4 × 4 approximate partial-product generators. # pp.1983,1987
* `pp_perforation` lacks a choice distinguishing precise partial-product accumulation from a hybrid approximate Wallace/compressor tree. # pp.1983,1986
* `error_analysis_quality.metric` lacks MSE and PSNR, which the application evaluation reports alongside ER/MED/NED. # p.1989
* `error_analysis_quality` lacks choices for input distribution and single-value versus conditional-PMF building-block error models. # pp.1985-1986

## open_questions
* Table 1 prints the ApproxMul5/3 uniform MC MED as `2.41 × 8` in the supplied document text; the missing exponent must not be inferred. # p.1988
* The paper does not identify the precise-adder family used to accumulate approximate partial products. # p.1983
