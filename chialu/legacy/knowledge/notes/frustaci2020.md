---
handle: frustaci2020
citation: F. Frustaci, S. Perri, P. Corsonello, M. Alioto, "Approximate Multipliers with Dynamic Truncation for Energy Reduction via Graceful Quality Degradation", IEEE Transactions on Circuits and Systems II, vol. 67, no. 12, pp. 3427-3431, 2020
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [uint8, int8, int12, uint16, int16]
authority: incremental
pages_read: 1-5 / 5
---

## summary
The paper proposes runtime-configurable truncation of multiplier partial-product columns using an incremental low-overhead mapping and an optional approximate mean-error correction in the partial-product-generation stage (pp.2-4). Wallace/Dadda multiplier and DCT results show scalable energy/quality with less overhead than conventional dynamic truncation and dual-quality compressors (pp.3-5).

## families
### truncated_fixed_width  (role: compares)
mechanism: Static truncation removes the partial products and compressor columns required to compute NT result LSBs. Separate hardware versions implement each NT value, so output quality is fixed at design time (pp.1-2).
choices:
  correction: none   # pp.1-2
  target: multiplier   # pp.1-2
new_choices:
  none
slots:
  kept_tree: csa_reduction_tree   # p.2
parameters: unsigned Wallace multipliers; 8×8 with NT=0,5,6,7,8; 16×16 with NT=0,10,12,14,16   # pp.2-4
results:
| metric | value | unit | technology / device | baseline | condition | page |
| delay | 507/587/659/698/777 | ps | 28-nm FDSOI 1V / 2020 | none | 8×8 static; NT=8/7/6/5/0 | p.4 |
| energy | 85/113/142/166/214 | fJ | 28-nm FDSOI 1V / 2020 | none | 8×8 static; NT=8/7/6/5/0 | p.4 |
| area | 77/100/129/148/190 | um2 | 28-nm FDSOI 1V / 2020 | none | 8×8 static; NT=8/7/6/5/0 | p.4 |
| delay | 1007/1104/1197/1274/1539 | ps | 28-nm FDSOI 1V / 2020 | none | 16×16 static; NT=16/14/12/10/0 | p.4 |
| energy | 478/624/737/833/1040 | fJ | 28-nm FDSOI 1V / 2020 | none | 16×16 static; NT=16/14/12/10/0 | p.4 |
| area | 500/591/664/727/827 | um2 | 28-nm FDSOI 1V / 2020 | none | 16×16 static; NT=16/14/12/10/0 | p.4 |
errors_and_checks: MED/MRED/error rate are evaluated; static truncation has the same error values as uncorrected dynamic truncation at equal NT (p.4).
conditions: Static truncation gives the lowest area/energy/delay, but it cannot change precision at runtime (p.3).
evidence: §II; Fig. 1a; Fig. 2; Table I (pp.1-4)

### ripple_carry  (role: instantiates)
mechanism: Every evaluated Wallace multiplier uses a ripple-carry adder as its final carry-propagate adder to favor low energy (p.2).
choices:
new_choices:
  none
slots:
  none
parameters: final CPA for 8×8 and 16×16 multipliers   # p.2
results:
| metric | value | unit | technology / device | baseline | condition | page |
| none | UNKNOWN | UNKNOWN | UNKNOWN / 2020 | none | RCA is not characterized separately | p.2 |
errors_and_checks: none
conditions: The RCA choice is held constant across compared multipliers (p.2).
evidence: §III-B and Fig. 1 (p.2)

## new_families
### dynamic_column_truncation_multiplier  (domain: approx: approximate multipliers, closest: truncated_fixed_width, why_not: `truncated_fixed_width` fixes discarded columns at design time, whereas this mechanism varies NT at runtime and remaps the reduction tree to control switching overhead.)
mechanism: Control signals gate partial products in the first kmax columns according to runtime NT. The proposed mapping starts from the NT=kmax static tree, adds compressors incrementally for higher precision, labels/sorts gated sum/carry bits, and groups equal-label bits to reduce active compressors and switching. Optional AND-OR gates inject an NT-dependent approximate mean-error offset directly in the PPG stage (pp.2-4).
choices:
  truncation_control: {runtime_column_gating} — NT selects truncated LSB columns at runtime   # pp.1-2
  pp_mapping: {incremental_low_overhead} — compressors are added from the maximally truncated tree   # p.2
  correction: {none, incremental_approximate_mean_offset} — configurable correction is injected in the PPG stage   # p.4
  reduction_tree: {wallace, dadda_4_2} — both tree structures are evaluated   # pp.2,4-5
  signedness: {unsigned, signed} — correction constants are reported for both forms   # p.4
  final_cpa: {ripple_carry} — all evaluated Wallace designs use an RCA   # p.2
results:
| metric | value | unit | technology / device | baseline | condition | page |
| delay | 564/674/725/766/830 | ps | 28-nm FDSOI 1V / 2020 | none | 8×8 uncorrected; NT=8/7/6/5/0 | p.4 |
| energy | 96/128/154/178/213 | fJ | 28-nm FDSOI 1V / 2020 | none | 8×8 uncorrected; NT=8/7/6/5/0 | p.4 |
| area | 203 | um2 | 28-nm FDSOI 1V / 2020 | none | 8×8 uncorrected; all NT | p.4 |
| MED | 452/192/80/32/0 | none | 28-nm FDSOI 1V / 2020 | exact product | 8×8 uncorrected; NT=8/7/6/5/0 | p.4 |
| delay | 640/710/725/770/831 | ps | 28-nm FDSOI 1V / 2020 | none | 8×8 corrected; NT=8/7/6/5/0 | p.4 |
| energy | 108/135/161/183/213 | fJ | 28-nm FDSOI 1V / 2020 | none | 8×8 corrected; NT=8/7/6/5/0 | p.4 |
| MED | 202/97/44/19/0 | none | 28-nm FDSOI 1V / 2020 | exact product | 8×8 corrected; NT=8/7/6/5/0 | p.4 |
| delay | 1011/1154/1269/1346/1570 | ps | 28-nm FDSOI 1V / 2020 | none | 16×16 uncorrected; NT=16/14/12/10/0 | p.4 |
| energy | 504/635/749/840/1060 | fJ | 28-nm FDSOI 1V / 2020 | none | 16×16 uncorrected; NT=16/14/12/10/0 | p.4 |
| area | 873 | um2 | 28-nm FDSOI 1V / 2020 | none | 16×16 uncorrected; all NT | p.4 |
| MED | 2.4E+5/5.4E+4/1.1E+4/2308/0 | none | 28-nm FDSOI 1V / 2020 | exact product | 16×16 uncorrected; NT=16/14/12/10/0 | p.4 |
| delay | 1120/1176/1289/1367/1570 | ps | 28-nm FDSOI 1V / 2020 | none | 16×16 corrected; NT=16/14/12/10/0 | p.4 |
| energy | 522/642/752/856/1060 | fJ | 28-nm FDSOI 1V / 2020 | none | 16×16 corrected; NT=16/14/12/10/0 | p.4 |
| MED | 7.6E+4/1.8E+4/4136/993/0 | none | 28-nm FDSOI 1V / 2020 | exact product | 16×16 corrected; NT=16/14/12/10/0 | p.4 |
| MED reduction | 11× | none | 28-nm FDSOI 1V / 2020 | conventional dynamic truncation [12] | 16×16 corrected, NT=10, iso-energy | p.4 |
| energy reduction | 26.2% | none | 28-nm FDSOI 1V / 2020 | conventional dynamic truncation [12] | 16×16 corrected, NT=16, iso-quality | p.4 |
| energy reduction | 33% | none | 28-nm FDSOI 1V / 2020 | dual-quality 4:2 compressors [13] | 8×8 Dadda tree, iso-quality | pp.4-5 |
| energy reduction | 12%/26% | none | 28-nm FDSOI 1V / 2020 | [12]/[13] | 2,000-frame DCT video sequence | p.5 |
evidence: Fig. 1c; §III-A/B; Fig. 2; Tables I-II; Fig. 3; §V and Fig. 4 (pp.2-5)

## space_gaps
* The approximate-multiplier vocabulary lacks runtime-selectable truncation of LSB partial-product columns with reduction-tree remapping; `truncated_fixed_width` covers only design-time truncation (pp.1-3).
* The proposed family needs a `final_cpa` slot because the evaluated designs explicitly use `ripple_carry`, while other final adders remain possible but untested (p.2).
* The correction domain needs an `incremental_approximate_mean_offset` value because the injected constant changes with NT and is neither one fixed constant nor input-data-dependent (p.4).

## open_questions
* The paper states that the method applies beyond Wallace/Dadda trees, but it does not establish results for other reduction-tree structures (pp.4-5).
* The paper does not report the implementation cost or control source of the external runtime policy that selects NT in the DCT case study (p.5).
